"""
irgen — gerar a IR de montagem (assembly.toml) por código.

Acima de ~40 peças, ou com simetria, escrever o TOML à mão vira fonte
de erro de coordenada. Um `gen.py` ao lado do `assembly.toml` usa
este módulo; o compilador continua lendo só o TOML gerado.

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "impl", "python"))
    from fusionbrick.irgen import Build, BK, OR

    b = Build("meu-rover", "rover 4×4 com deck", view_angle=125, dowel_every=3)
    b.beam("chassi", "long_e", (0, 0, 0), (24, 1, 1), BK)
    b.mirror_y(16)            # copia tudo o que tem sufixo _e para _d
    b.write(__file__)         # grava assembly.toml ao lado do gen.py

Tudo em células (1 célula = grid = 8 mm). Eixos: x, y no chão, z para
cima; a frente é +X (faces front/back/left/right/top/bottom). Nenhuma
função aqui calcula encaixe — isso é do compilador.

O TOML sai sempre nos nomes públicos (`asm/names.py`), mesmo que o
gen.py ainda use um nome antigo (liftarm, mock, cells, faces xn…).
"""

from __future__ import annotations

import copy
import os
import re

from .asm import names

# Paleta curta e com função. Use 2–3 cores por modelo, não mais.
BK = [0.11, 0.11, 0.12]   # estrutura escura
GR = [0.62, 0.63, 0.66]   # postes / suporte
WH = [0.90, 0.90, 0.88]   # carenagem clara
OR = [0.97, 0.47, 0.10]   # acento
BL = [0.20, 0.45, 0.85]   # acento frio
TN = [0.83, 0.73, 0.56]   # bege (teto, tampa)

# Receitas de BRICK com cara de viga: furado nos 3 eixos e arredondado
# no eixo dos furos que ficam à vista. (Para 1×1×n, prefira `b.beam`.)
LIFT_X = dict(holes="xyz", rounded="y")   # viga ao longo de X, furos em Y à vista
LIFT_Y = dict(holes="xyz", rounded="x")   # viga ao longo de Y, furos em X à vista
LIFT_Z = dict(holes="xyz", rounded="y")   # poste vertical, furos em Y à vista
FLAT = dict(rounded="z", corner_r=4.0)    # placa/viga deitada, cantos redondos em planta


def fmt(v):
    """Valor Python → literal TOML de uma linha."""
    if isinstance(v, str):
        return '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {fmt(x)}" for k, x in v.items()) + " }"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, float):
        return f"{v:g}" if v != int(v) else f"{v:.1f}"
    return str(v)


# ------------------------------------------------------------
# Espelho em Y — uma regra por campo da IR
# ------------------------------------------------------------
_SWAP = {"yn": "yp", "yp": "yn", "left": "right", "right": "left"}


def _flip_y(v):
    return [v[0], -v[1], v[2]]


def _y_extent(q) -> float:
    """Quantas células a peça ocupa em Y (bloco = size, componente = mm/grid, resto = 1)."""
    t = names.type_of(q)
    if t in names.BRICKS:
        return (q.get("size") or q["cells"])[1]
    if t == "component" and ("size_mm" in q or "size" in q):
        return (q.get("size_mm") or q["size"])[1] / 8.0
    return 1


_MIRROR = {
    "faces": lambda v, w: {_SWAP.get(k, k): x for k, x in v.items()},
    "pins": lambda v, w: [_SWAP.get(f, f) for f in v],
    "plain": lambda v, w: [_SWAP.get(f, f) for f in v],
    "flat": lambda v, w: [_SWAP.get(f, f) for f in v],
    "studs": lambda v, w: v if isinstance(v, str) else [_SWAP.get(f, f) for f in v],
    "from_arm": lambda v, w: _flip_y(v),
    "to_arm": lambda v, w: _flip_y(v),
    "dirs": lambda v, w: [_flip_y(d) for d in v],
    "dir": lambda v, w: _flip_y(v),
    "turn": lambda v, w: _flip_y(v),
    "points": lambda v, w: [[q[0], w - q[1], q[2]] for q in v],
}


def _mirrored(p: dict, width: int, rename) -> dict:
    q = copy.deepcopy(p)
    q["id"] = rename(p["id"])
    for key in ("from", "to"):
        if isinstance(q.get(key), str):                 # diagonal entre dois nós: ids
            q[key] = rename(q[key])
        elif key in q:                                  # diagonal por células
            q[key] = [q[key][0], width - q[key][1] - 1, q[key][2]]
    if "on" in q:
        pid, face = q["on"].rsplit(".", 1)
        q["on"] = f"{rename(pid)}.{_SWAP.get(face, face)}"
    if "at" in q and "points" not in q:
        y = width - q["at"][1] - _y_extent(q)
        q["at"][1] = int(y) if float(y).is_integer() else y
    for key, rule in _MIRROR.items():
        if key in q:
            q[key] = rule(q[key], width)
    return q


class Build:
    """Acumula peças e grupos; `write()` gera o assembly.toml."""

    def __init__(self, name: str, intent: str, **meta):
        self.name, self.intent, self.meta = name, intent, meta
        self.parts: list[dict] = []
        self.groups: dict[str, list[str]] = {}
        self.notes: dict[str, str] = {}
        self.hinges: list[str] = []
        self.header = ""            # esboço ASCII / comentário de topo

    # ---------- primitivas da IR ----------
    def add(self, group: str, **kw) -> dict:
        if any(p["id"] == kw["id"] for p in self.parts):
            raise ValueError(f"id repetido: {kw['id']}")
        self.parts.append(kw)
        self.groups.setdefault(group, []).append(kw["id"])
        return kw

    def brick(self, group, id, at, size, color=None, **kw):
        """Bloco: `at` = canto mínimo; `size` em células, no referencial do MUNDO (não gira)."""
        d = dict(id=id, type=kw.pop("type", "brick"), at=list(at), size=list(size))
        if color:
            d["color"] = color
        return self.add(group, **d, **kw)

    def beam(self, group, id, at, size, color=None, **kw):
        """Viga 1×1×n com furos à vista e pontas redondas. `studs="top"` empilha sem cavilha."""
        return self.brick(group, id, at, size, color, type="beam", **kw)

    def plate(self, group, id, at, nx, ny, color=None, **kw):
        """Placa de 4 mm furada em Z. `studs="bottom"` encaixa por pinos no que está embaixo."""
        return self.brick(group, id, at, (nx, ny, 1), color, type="plate", **kw)

    def cover(self, group, id, at, nx, ny, color=None, **kw):
        """Tampa lisa de 4 mm, pinos para baixo só no perímetro."""
        return self.brick(group, id, at, (nx, ny, 1), color, type="cover", **kw)

    def curve(self, group, id, at, dir, turn, radius=2, angle=90, color=OR, k=None, **kw):
        """
        Curva: `at` = 1ª célula do arco; a entrada fica na face de trás (−dir).
        `radius` = células que a curva ocupa de lado (1, 2 ou 3).
        """
        if k is not None:                       # nome antigo: k = radius − 1
            radius = k + 1
        return self.add(group, id=id, type="curve", at=list(at), dir=list(dir), turn=list(turn),
                        radius=radius, angle=angle, color=color, **kw)

    def strut(self, group, id, a, b, color=BK, from_arm=None, to_arm=None, base_dir=None, top_dir=None, **kw):
        """
        Diagonal entre as células `a` e `b` (o vetor precisa fechar no
        grid: 3-4-5, 5-12-13…). Os nós das pontas são criados sozinhos,
        com os ids `<id>-n0`, `<id>-n1` e a viga `<id>-v`.
        `from_arm` / `to_arm`: o braço de cada nó que prende no resto.
        Padrão: o eixo dominante da diagonal, para trás dela. REGRA: o
        braço fica a ≥127° da diagonal — nunca a 90°.
        """
        d = {"id": id, "type": "strut", "from": list(a), "to": list(b), "color": color}
        for key, v in (("from_arm", from_arm or base_dir), ("to_arm", to_arm or top_dir)):
            if v is not None:
                d[key] = list(v)
        return self.add(group, **d, **kw)

    def node(self, group, id, at, dirs, color=BK, **kw):
        """Nó solto (uso avançado: nó com 3+ portas). Para uma diagonal comum, use `strut`."""
        return self.add(group, id=id, type="node", at=list(at), dirs=[list(d) for d in dirs],
                        color=color, **kw)

    def strut_between(self, group, id, node_a, node_b, color=BK, style="beam", **kw):
        """Diagonal entre dois nós que já existem (ids)."""
        return self.add(group, id=id, type="strut", **{"from": node_a}, to=node_b, color=color,
                        style=style, **kw)

    def wheel(self, group, id, at, on, diameter=4, color=BK, cells=None, **kw):
        """Roda: `on` = "<peça>.<face>", `diameter` em células."""
        return self.add(group, id=id, type="wheel", at=list(at), on=on,
                        diameter=cells if cells is not None else diameter, color=color, **kw)

    def component(self, group, id, at, size_mm, label="", color=None, **kw):
        """Componente comprado pronto: `at` em células, `size_mm` na medida real."""
        d = dict(id=id, type="component", at=list(at), size_mm=list(size_mm))
        if label:
            d["label"] = label
        if color:
            d["color"] = color
        return self.add(group, **d, **kw)

    # nomes de antes da revisão — continuam funcionando
    liftarm, tile, mock = beam, cover, component

    def bend(self, group, id, at, dir, turn, k=1, angle=90, color=OR, **kw):
        return self.curve(group, id, at, dir, turn, k=k, angle=angle, color=color, **kw)

    # ---------- macros validadas (ver reference/patterns.md) ----------
    def ring(self, group, prefix, x0, y0, z, nx, ny, beam_color=BK, curve_color=OR, radius=2, max_cells=26,
             split="dowel", k=None, bend_color=None, **beam_kw):
        """
        Quadro retangular de cantos curvos no plano z: 4 vigas + 4 curvas.
        Ocupa nx × ny células a partir de (x0, y0). Precisa de
        nx, ny ≥ 2·radius + 1 para sobrar viga reta entre as curvas.
        Vigas retas maiores que `max_cells` (26 = 208 mm) saem em partes.
        Emenda: `split="dowel"` (cavilha de topo — anel solto) ou
        `split="flat"` (sem encaixe — quando o anel apoia num deck e cada
        parte já entra por outra face; evita o 2º movimento do ASM-012).
        """
        if k is not None:
            radius = k + 1
        curve_color = bend_color or curve_color
        k = radius - 1
        c = radius                              # células que cada curva ocupa por lado
        Lx, Ly = nx - 2 * c, ny - 2 * c
        if Lx < 1 or Ly < 1:
            raise ValueError("ring pequeno demais para a curva escolhida")
        X1, Y1 = x0 + nx - 1, y0 + ny - 1

        def run(tag, at, n, axis):
            # viga reta, dividida em partes iguais se passar de max_cells
            # (mesa de impressão): as partes se juntam por cavilha.
            parts = -(-n // max_cells)
            sizes = [n // parts + (1 if i < n % parts else 0) for i in range(parts)]
            off = 0
            neg, pos_f = ("back", "front") if axis == 0 else ("right", "left")
            for i, m in enumerate(sizes):
                pos = list(at)
                pos[axis] += off
                cells = [1, 1, 1]
                cells[axis] = m
                kw = dict(beam_kw)
                if parts > 1 and split in ("flat", "plain"):
                    # emenda SEM encaixe: a peça já entra por outra face
                    # (machos para baixo, curvas nas pontas); uma cavilha
                    # de topo aqui exigiria um segundo movimento (ASM-012)
                    ends = ([neg] if i > 0 else []) + ([pos_f] if i < parts - 1 else [])
                    kw["flat"] = list(kw.get("flat", kw.pop("plain", []))) + ends
                self.brick(group, f"{prefix}-{tag}" + (str(i) if parts > 1 else ""), pos, cells,
                           beam_color, **kw)
                off += m

        run("s", (x0 + c, y0, z), Lx, 0)
        run("l", (X1, y0 + c, z), Ly, 1)
        run("n", (x0 + c, Y1, z), Lx, 0)
        run("o", (x0, y0 + c, z), Ly, 1)
        self.curve(group, f"{prefix}-cSE", (X1 - k, y0, z), (1, 0, 0), (0, 1, 0), radius=radius, color=curve_color)
        self.curve(group, f"{prefix}-cNE", (X1, Y1 - k, z), (0, 1, 0), (-1, 0, 0), radius=radius, color=curve_color)
        self.curve(group, f"{prefix}-cNO", (x0 + k, Y1, z), (-1, 0, 0), (0, -1, 0), radius=radius, color=curve_color)
        self.curve(group, f"{prefix}-cSO", (x0, y0 + k, z), (0, -1, 0), (1, 0, 0), radius=radius, color=curve_color)

    def sub(self, group: str, note: str = ""):
        """Marca o grupo como subconjunto montado à parte (ASM-012)."""
        self.subs = getattr(self, "subs", set()) | {group}
        if note:
            self.notes[group] = note

    def arch(self, group, prefix, x, y0, y1, z0, top, color=BK, curve_color=OR, bend_color=None, **beam_kw):
        """
        Arco aberto no plano Y-Z (santantônio): poste em y0 e em y1 de
        z0 até top−2, curva de raio 2 em cada canto, travessa em z = top.
        A travessa ocupa y0+2 … y1−2 (y1 − y0 − 3 células).
        """
        if y1 - y0 < 4:
            raise ValueError("arco estreito demais (y1 − y0 ≥ 4)")
        h = top - 1 - z0
        curve_color = bend_color or curve_color
        self.brick(group, f"{prefix}-pe", (x, y0, z0), (1, 1, h), color, **beam_kw)
        self.curve(group, f"{prefix}-ce", (x, y0, top - 1), (0, 0, 1), (0, 1, 0), color=curve_color)
        self.brick(group, f"{prefix}-tr", (x, y0 + 2, top), (1, y1 - y0 - 3, 1), color, **beam_kw)
        self.curve(group, f"{prefix}-cd", (x, y1 - 1, top), (0, 1, 0), (0, 0, -1), color=curve_color)
        self.brick(group, f"{prefix}-pd", (x, y1, z0), (1, 1, h), color, **beam_kw)

    # ---------- simetria ----------
    def mirror_y(self, width: int, src: str = "_e", dst: str = "_d", split_groups: bool = False):
        """
        Duplica toda peça cujo id tem `src` no fim ou antes de um "-"
        (`long_e`, `r_e-n0`), espelhada em Y num corpo de `width` células.
        Troca left↔right e o sinal de Y nas direções; ids referidos acompanham.
        `split_groups`: a cópia de um grupo `x_e` vai para o grupo `x_d`
        (subconjuntos por lado, com a mesma nota e o mesmo `sub`).
        """
        tag = re.compile(re.escape(src) + r"(?=$|-)")
        new = []
        for p in self.parts:
            if tag.search(p["id"]):
                group = next(g for g, ids in self.groups.items() if p["id"] in ids)
                new.append((group, _mirrored(p, width, lambda i: tag.sub(dst, i))))
        for group, q in new:
            target = tag.sub(dst, group) if split_groups else group
            self.add(target, **q)
            if target != group:
                if group in self.notes:
                    self.notes.setdefault(target, self.notes[group])
                if group in getattr(self, "subs", set()):
                    self.subs.add(target)

    # ---------- saída ----------
    def toml(self) -> str:
        out = [f"# GERADO por gen.py — edite o gerador, não este arquivo.\n"]
        if self.header:
            out.append("\n".join("# " + l if l else "#" for l in self.header.strip("\n").splitlines()) + "\n")
        out.append(f'\n[assembly]\nname = "{self.name}"\n')
        for k, v in self.meta.items():
            out.append(f"{names.META_OUT.get(k, k)} = {fmt(v)}\n")
        out.append(f"intent = {fmt(self.intent)}\n\nparts = [\n")
        for p in self.parts:
            out.append("  { " + ", ".join(f"{k} = {fmt(v)}" for k, v in names.publicize(p).items()) + " },\n")
        out.append("]\n\ngroups = [\n")
        for g, ids in self.groups.items():
            sub = ", sub = true" if g in getattr(self, "subs", set()) else ""
            out.append(f"  {{ id = {fmt(g)}, parts = {fmt(ids)}, note = {fmt(self.notes.get(g, ''))}{sub} }},\n")
        out.append("]\n")
        if self.hinges:
            out.append(f"\nhinges = {fmt(self.hinges)}\n")
        return "".join(out)

    def write(self, where: str) -> str:
        """`where` = __file__ do gen.py (grava ao lado) ou uma pasta."""
        if where.endswith(".py"):
            d = os.path.dirname(os.path.abspath(where))
        else:
            d = where
            os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "assembly.toml")
        with open(path, "w") as f:
            f.write(self.toml())
        print(f"  {self.name}: {len(self.parts)} peças → {path}")
        return path
