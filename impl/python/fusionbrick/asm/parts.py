"""
Os tipos de peça da IR. Cada classe responde às quatro perguntas de
`model.Part` (resolve, ports, boxes, config) e mais nada no compilador
ramifica por tipo.

    brick      bloco, viga, placa, tampa — vive no grid e não gira
    node       cubo de 1 célula com portas por direção (pontas da diagonal)
    strut      diagonal: viga entre dois nós, comprimento pitagórico
    curve      viga curva de 90°/180°
    wheel      roda num eixo, encostada na face de um BRICK
    component  volume de componente real — não imprime

As peças chegam aqui nos nomes INTERNOS (`names.normalize`): `cells`,
`axes`, `round`, `pin_cells`, faces `xn…zp`, `pin/recess/plain`. São os
mesmos dos parâmetros do OpenSCAD. As mensagens falam os nomes públicos.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import List

from .. import geom as G
from ..brick import AXES, FACES, FACE_AXIS, FACE_NORMAL, BrickSpec
from . import names
from .model import EPS, IRError, Joint, Part, Port, rvec

KINDS = ("auto", "recess", "pin", "plain")
FACE_SIGN = {"xn": -1, "xp": 1, "yn": -1, "yp": 1, "zn": -1, "zp": 1}


def face_name(axis: int, sign: int) -> str:
    return AXES[axis] + ("p" if sign > 0 else "n")


def _short_hash(obj) -> str:
    return hashlib.sha1(json.dumps(obj).encode()).hexdigest()[:6]


def _axes_from(v):
    if v is None:
        v = "xyz"
    if isinstance(v, dict):
        return tuple(v.get(a, "bored") for a in AXES)
    if not isinstance(v, str):
        raise IRError(f"holes inválido: {v!r}")
    s = "" if v in ("", "none") else v.lower()
    if any(ch not in "xyz" for ch in s):
        raise IRError(f"holes = {v!r}: use letras de x/y/z (ex.: \"xz\") ou \"none\"")
    return tuple("bored" if a in s else "solid" for a in AXES)


def _faces_from(v) -> List[str]:
    if v is None:
        return ["auto"] * 6
    if isinstance(v, str):
        v = {"default": v}
    unknown = set(v) - set(FACES) - {"default"}
    if unknown:
        raise IRError(f"faces com chave desconhecida: {sorted(unknown)}")
    out = [v.get(f, v.get("default", "auto")) for f in FACES]
    for f, k in zip(FACES, out):
        if k not in KINDS:
            raise IRError(f"face {names.face(f)} = {names.kind(k)!r}: use auto, socket, stud ou flat")
    return out


def _port_kinds(pid, value, n, default):
    kinds = [value] * n if isinstance(value, str) else list(value if value is not None else [default] * n)
    if len(kinds) != n:
        raise IRError(f"{pid}: uma entrada de ports por porta ({n})")
    for k in kinds:
        if k not in ("pin", "recess", "plain"):
            raise IRError(f"{pid}: porta '{k}' inválida (use stud, socket ou flat)")
    return kinds


# ============================================================
# BRICK
# ============================================================
class Brick(Part):
    type = "brick"
    order = 0
    default_color = None

    def parse(self, rp, g):
        cells = tuple(int(c) for c in rp.get("cells", (1, 1, 1)))
        if len(cells) != 3 or min(cells) < 1:
            raise IRError(f"{self.id}: size precisa de 3 inteiros ≥ 1")
        self.cells = cells
        self.thickness = float(rp.get("thickness", 0))
        self.axes = _axes_from(rp.get("axes"))
        self.faces = _faces_from(rp.get("faces"))
        self.round_axis = rp.get("round", "none")
        if self.round_axis not in ("none", "x", "y", "z"):
            raise IRError(f"{self.id}: rounded = {self.round_axis!r}: use none/x/y/z")
        self.corner_r = float(rp.get("corner_r", g / 2 if self.round_axis != "none" else 0))
        self.pin_cells = rp.get("pin_cells", "all")
        if self.pin_cells not in ("all", "edge", "inner"):
            raise IRError(f"{self.id}: studs_on = {self.pin_cells!r}: use all/edge/inner")
        sz = [c * g for c in cells]
        if self.slab:
            sz[2] = self.thickness
        self.size = tuple(sz)
        self._canon = None

    @property
    def slab(self) -> bool:
        return self.thickness > 0

    def spec(self, p) -> BrickSpec:
        return BrickSpec(cells=self.cells, axes=self.axes, faces=list(self.faces), p=p)

    # --- validação da própria peça --------------------------------
    def resolve(self, asm):
        self.placed = True
        x, y, z = self.at
        if abs(x - round(x)) > EPS or abs(y - round(y)) > EPS:
            asm.err("ASM-001", f"{self.id}: at X/Y precisa ser inteiro (é {self.at})",
                    "o grid é sagrado: furo fora do centro de célula não encaixa")
        if abs(z * 2 - round(z * 2)) > EPS:
            asm.err("ASM-001", f"{self.id}: at Z precisa ser múltiplo de 0.5 célula (é {z})")
        sp = self.spec(asm.p)
        self._check_round_pins(asm, sp)
        for e in sp.errors():
            asm.err("REQ-005", f"{self.id}: {e}", "deixe a face em auto, ou fure esse eixo (holes)")
        if self.slab:
            self._check_slab(asm, sp)

    def _round_radius(self) -> float:
        ra = "xyz".index(self.round_axis)
        return min(self.corner_r, min(self.size[i] for i in range(3) if i != ra) / 2)

    def rounded(self, p, q: int) -> bool:
        """A ponta no eixo q é curva demais para sustentar o colar de um macho?"""
        if self.round_axis == "none" or "xyz".index(self.round_axis) == q:
            return False
        return self._round_radius() > p.grid / 2 - p.collar_d / 2 + 1e-6

    def _check_round_pins(self, asm, sp):
        if self.round_axis == "none" or self.pin_cells == "inner":
            return
        ra, r_eff = "xyz".index(self.round_axis), self._round_radius()
        safe = asm.p.grid / 2 - asm.p.collar_d / 2
        for fi, f in enumerate(FACES):
            if sp.face(fi) == "pin" and FACE_AXIS[f] != ra and r_eff > safe + 1e-6:
                asm.err("REQ-010", f"{self.id}: pino (stud) em {names.face(f)} sobre aresta arredondada "
                        f"(raio {r_eff:g} > {safe:g})",
                        "ponta redonda junta por cavilha: deixe a face em auto, "
                        "ou use studs_on = \"inner\" (pinos só nas células planas)")

    def _check_slab(self, asm, sp):
        p = asm.p
        if self.thickness < p.edge_bore_min:
            for a in (0, 1):
                if self.axes[a] == "bored":
                    asm.err("REQ-008", f"{self.id}: laje de {self.thickness:g}mm não comporta "
                            f"furo no eixo {AXES[a]} (mínimo {p.edge_bore_min:g})",
                            f"use holes sem '{AXES[a]}'")
        zr = (sp.face(4) == "recess") + (sp.face(5) == "recess")
        floor = zr * p.collar_depth
        if zr and self.thickness <= floor:
            asm.err("REQ-008", f"{self.id}: laje de {self.thickness:g}mm fina demais para "
                    f"{zr} face(s) com encaixe (socket) (piso {floor:g})")

    # --- portas ---------------------------------------------------
    def _centers(self, p, q: int) -> List[float]:
        if q == 2 and self.slab:
            return [self.origin[2] + self.thickness / 2]
        return [self.origin[q] + p.inset + k * p.grid for k in range(self.cells[q])]

    def _pin_here(self, p, perp, iu, nu, iv, nv) -> bool:
        """pin_cells decide em quais células da face o macho existe."""
        edge_u, edge_v = iu in (0, nu - 1), iv in (0, nv - 1)
        if self.pin_cells == "edge":
            return edge_u or edge_v
        if self.pin_cells == "inner":
            return not ((self.rounded(p, perp[0]) and edge_u) or (self.rounded(p, perp[1]) and edge_v))
        return True

    def ports(self, asm) -> List[Port]:
        p, sp, out = asm.p, self.spec(asm.p), []
        for fi, f in enumerate(FACES):
            a, s, kind = FACE_AXIS[f], FACE_SIGN[f], sp.face(fi)
            plane = self.origin[a] + (self.size[a] if s > 0 else 0.0)
            perp = [i for i in range(3) if i != a]
            us, vs = self._centers(p, perp[0]), self._centers(p, perp[1])
            for iu, u in enumerate(us):
                for iv, v in enumerate(vs):
                    k = kind
                    if kind == "pin" and not self._pin_here(p, perp, iu, len(us), iv, len(vs)):
                        k = "plain"
                    pos = [0.0, 0.0, 0.0]
                    pos[a], pos[perp[0]], pos[perp[1]] = plane, u, v
                    out.append(Port(self.id, rvec(pos), FACE_NORMAL[f], k, f))
        return out

    # --- STL canônico ----------------------------------------------
    def _oriented(self, R, sp):
        """Assinatura da peça vista no referencial girado por R."""
        perm = [next(k for k in range(3) if R[i][k]) for i in range(3)]
        cc, ca, cf = [0] * 3, [""] * 3, {}
        for i, j in enumerate(perm):
            cc[j], ca[j] = self.cells[i], self.axes[i]
            for u in (1, -1):
                cf[face_name(j, u)] = sp.face(FACES.index(face_name(i, u * R[i][j])))
        ra = "none" if self.round_axis == "none" else "xyz"[perm["xyz".index(self.round_axis)]]
        return (tuple(cc), tuple(ca), tuple(cf[f] for f in FACES), self.thickness, ra,
                self.corner_r, self.pin_cells)

    def canonical(self, p):
        """
        (assinatura, rotação): a orientação de IMPRESSÃO — maior dimensão
        em X, menor em Z, de preferência sem macho na face de baixo.
        Peças que são a mesma peça girada caem na mesma assinatura.
        """
        if self._canon is None:
            sp = self.spec(p)
            cands = [R for R in G.ROTATIONS if not self.slab or abs(R[2][2]) == 1]
            sigs = [(self._oriented(R, sp), R) for R in cands]
            self._canon = min(sigs, key=lambda sr: (tuple(-c for c in sr[0][0]), sr[0][2][4] == "pin", sr[0]))
        return self._canon

    def config(self, asm):
        sig, _ = self.canonical(asm.p)
        cc, ca, cf, th, ra, cr, pc = sig
        prm = {"cells_x": cc[0], "cells_y": cc[1], "cells_z": cc[2],
               "axis_x": ca[0], "axis_y": ca[1], "axis_z": ca[2]}
        if ra != "none":
            prm.update({"round_axis": ra, "corner_r": cr})
        if pc != "all":
            prm["pin_cells"] = pc
        for f, k in zip(FACES, cf):
            prm[f"face_{f}"] = k
        if th:
            prm["thickness"] = th
        plain = ra == "none" and pc == "all"
        dims = f"{cc[0]}x{cc[1]}x{cc[2]}" if not th else f"{cc[0]}x{cc[1]}-t{th:g}"
        return f"brick-{dims}-{_short_hash(sig[:4] if plain else sig)}", "brick.scad", prm

    def matrix(self, asm):
        sig, R = self.canonical(asm.p)
        g = asm.p.grid
        csz = [c * g for c in sig[0]]
        if self.slab:
            csz[2] = self.thickness
        m = [sum(min(0, R[i][j] * csz[j]) for j in range(3)) for i in range(3)]
        return R, [self.origin[i] - m[i] for i in range(3)]


# ============================================================
# NODE + BEAM — forma livre por ternos pitagóricos
# ============================================================
class Node(Part):
    type = "node"
    order = 1

    def parse(self, rp, g):
        self.dirs = [tuple(int(c) for c in d) for d in rp.get("dirs", [])]
        if len(self.dirs) < 2:
            raise IRError(f"{self.id}: node precisa de 2+ direções em dirs")
        self.port_kinds = _port_kinds(self.id, rp.get("ports"), len(self.dirs), "pin")
        self.fillet = rp.get("fillet")
        self.size = (g, g, g)
        self.center = tuple(self.origin[i] + g / 2 for i in range(3))

    def resolve(self, asm):
        g = asm.p.grid
        self.placed = True
        self.on_grid(asm, "node ocupa uma célula")
        if self.fillet is not None and self.fillet > g / 4 + 1e-9:
            asm.err("ASM-002", f"{self.id}: fillet {self.fillet:g} > {g / 4:g} — o cubo do nó sai da "
                    "própria célula e invade as peças vizinhas", f"use fillet ≤ {g / 4:g} (padrão)")
        units = [G.unit(d) for d in self.dirs]
        for i, u in enumerate(units):
            if any(G.dot(u, v) > 0.9999 for v in units[:i]):
                asm.err("ASM-008", f"{self.id}: duas portas na mesma direção {list(self.dirs[i])}")

    def ports(self, asm):
        g = asm.p.grid
        return [Port(self.id, rvec(G.add(self.center, G.mul(G.unit(d), g / 2))), G.unit(d), k, str(list(d)))
                for d, k in zip(self.dirs, self.port_kinds)]

    def config(self, asm):
        prm = {"dirs": [list(d) for d in self.dirs], "ports": list(self.port_kinds)}
        if self.fillet is not None:
            prm["fillet"] = float(self.fillet)
        return f"node-{len(self.dirs)}p-{_short_hash(prm)}", "node.scad", prm

    def matrix(self, asm):
        return G.IDENTITY, self.center

    def arm_box(self, d, g) -> G.Box:
        """Meio braço da porta `d` — o volume que pode invadir uma viga vizinha."""
        du = G.unit(d)
        Al = G.along(du)
        axes = [(Al[0][0], Al[1][0], Al[2][0]), (Al[0][1], Al[1][1], Al[2][1]), du]
        return G.Box(G.add(self.center, G.mul(du, g / 4)), axes, (g / 2, g / 2, g / 4), self.id, "arm")


class Strut(Part):
    type = "strut"
    order = 2

    def parse(self, rp, g):
        self.style = rp.get("style", "box")
        if self.style not in ("box", "beam"):
            raise IRError(f"{self.id}: style = {self.style!r}: use beam (furada, pontas redondas) ou box")
        self.frm, self.to = rp.get("from"), rp.get("to")
        if not self.frm or not self.to:
            raise IRError(f"{self.id}: strut precisa de from e to (duas células, ou dois nós)")
        self.cells = (0, 1, 1)

    def _span(self, asm):
        """(nó A, nó B, Δ em células, comprimento) ou None com o erro já registrado."""
        A, B = asm.parts.get(self.frm), asm.parts.get(self.to)
        if not isinstance(A, Node) or not isinstance(B, Node):
            asm.err("ASM-008", f"{self.id}: from/to precisam ser nós ({self.frm} → {self.to})")
            return None
        delta = tuple(int(round(B.at[i] - A.at[i])) for i in range(3))
        L = G.pyth_len(delta)
        if L is None:
            asm.err("ASM-008", f"{self.id}: {A.id}→{B.id} vale {G.norm(delta):.3f} células — não é inteiro",
                    "a diagonal precisa fechar no grid: use 3-4-5, 5-12-13, 6-8-10, ou alinhe a um eixo")
            return None
        if L < 2:
            asm.err("ASM-008", f"{self.id}: nós vizinhos demais para caber viga ({L} célula)")
            return None
        u = G.unit(delta)
        for node, want, need in ((A, u, delta), (B, G.mul(u, -1), [-c for c in delta])):
            if not any(G.dot(G.unit(d), want) > 0.9999 for d in node.dirs):
                asm.err("ASM-008", f"{self.id}: {node.id} não tem porta apontando para a viga "
                        f"(precisa de dirs com {list(need)})")
                return None
        return A, B, u, L

    def resolve(self, asm):
        span = self._span(asm)
        if span is None:
            return
        g = asm.p.grid
        A, _, u, L = span
        n = L - 1                                    # cada nó avança grid/2
        Al = G.along(u)
        ex, ey = (Al[0][0], Al[1][0], Al[2][0]), (Al[0][1], Al[1][1], Al[2][1])
        cols = [u, ey, G.mul(ex, -1)]                # local: comprimento em X
        self.R = [[cols[j][i] for j in range(3)] for i in range(3)]
        self.start = G.add(A.center, G.mul(u, g / 2))
        self.end = G.add(self.start, G.mul(u, n * g))
        self.t = G.sub(self.start, G.matvec(self.R, (0, g / 2, g / 2)))
        self.u, self.cells = u, (n, 1, 1)
        self.box = G.Box(G.add(self.start, G.mul(u, n * g / 2)), cols, (n * g / 2, g / 2, g / 2),
                         self.id, "strut")
        lo = [min(self.start[i], self.end[i]) - g for i in range(3)]
        self.origin = tuple(lo)
        self.size = tuple(abs(self.end[i] - self.start[i]) + 2 * g for i in range(3))
        self.placed = True

    def ports(self, asm):
        if not self.placed:
            return []
        return [Port(self.id, rvec(self.start), G.mul(self.u, -1), "recess", "início"),
                Port(self.id, rvec(self.end), self.u, "recess", "fim")]

    def boxes(self):
        return [self.box] if self.placed else []

    def ignores(self, other, asm):
        return other.id in (self.frm, self.to)

    def check(self, asm):
        """A ponta da viga entra na célula do nó: um braço perto da diagonal a invade."""
        g = asm.p.grid
        for nid, toward in ((self.frm, self.u), (self.to, G.mul(self.u, -1))):
            node = asm.parts[nid]
            for d in node.dirs:
                if G.dot(G.unit(d), toward) > 0.9999:
                    continue
                dep = G.overlap_depth(node.arm_box(d, g), self.box)
                if dep > 0.05:
                    asm.err("ASM-008", f"{nid}: o braço {list(d)} invade a ponta de {self.id} ({dep:.1f}mm)",
                            "braço a menos de ~127° da diagonal colide com a viga; "
                            "tire essa porta e apoie a peça em outro lugar")

    def config(self, asm):
        n = self.cells[0]
        prm = {"cells_x": n, "cells_y": 1, "cells_z": 1,
               "axis_x": "bored", "axis_y": "bored", "axis_z": "bored"}
        if self.style == "beam":                  # pontas redondas no plano da diagonal
            prm.update({"round_axis": "y", "corner_r": asm.p.grid / 2})
            return f"strut-{n}", "brick.scad", prm
        return f"strut-{n}-box", "brick.scad", prm

    def matrix(self, asm):
        return self.R, self.t

    def explode_with(self):
        return (self.frm, self.to)

    def mass_center(self):
        return tuple((self.start[i] + self.end[i]) / 2 for i in range(3))


# ============================================================
# BEND — viga curva
# ============================================================
class Curve(Part):
    type = "curve"
    order = 3

    def parse(self, rp, g):
        self.dir = tuple(int(c) for c in rp.get("dir", (0, 1, 0)))
        self.turn = tuple(int(c) for c in rp.get("turn", (-1, 0, 0)))
        self.k, self.angle = int(rp.get("k", 1)), int(rp.get("angle", 90))
        self.port_kinds = _port_kinds(self.id, rp.get("ports"), 2, "recess")
        if self.angle not in (90, 180):
            raise IRError(f"{self.id}: curve só fecha no grid a 90° ou 180° (é {self.angle})")
        if self.k < 0:
            raise IRError(f"{self.id}: radius ≥ 1")
        if any(sum(abs(c) for c in d) != 1 for d in (self.dir, self.turn)):
            raise IRError(f"{self.id}: dir/turn precisam ser eixos (ex. [0,1,0])")
        if G.dot(self.dir, self.turn) != 0:
            raise IRError(f"{self.id}: turn precisa ser perpendicular a dir")
        self.size = (g, g, g)

    def resolve(self, asm):
        """
        Referencial do curve.scad: arco no plano XY, centro na origem,
        porta A em (R,0,0) olhando −Y. No mundo: X = −turn, Y = dir.
        """
        g = asm.p.grid
        self.on_grid(asm, "curve começa numa célula")
        d, t = tuple(map(float, self.dir)), tuple(map(float, self.turn))
        self.radius = (self.k + 0.5) * g
        cell = tuple(self.origin[i] + g / 2 for i in range(3))
        self.pa = G.sub(cell, G.mul(d, g / 2))
        self.C = G.add(self.pa, G.mul(t, self.radius))
        xl, yl = G.mul(t, -1), d
        zl = G.cross(xl, yl)
        self.R = [[xl[i], yl[i], zl[i]] for i in range(3)]
        if self.angle == 90:
            self.pb, self.db = G.add(self.C, G.mul(d, self.radius)), t
        else:
            self.pb, self.db = G.add(self.C, G.mul(t, self.radius)), G.mul(d, -1)
        self._chain = self._arc_boxes(g, zl)
        corners = [c for bx in self._chain for c in G.box_corners(bx)]
        lo = [min(q[i] for q in corners) for i in range(3)]
        hi = [max(q[i] for q in corners) for i in range(3)]
        self.origin, self.size = tuple(lo), tuple(hi[i] - lo[i] for i in range(3))
        self.placed = True

    def _arc_boxes(self, g, zl):
        """O arco como corrente de caixas tangentes — o miolo da curva fica livre."""
        nseg = 6 * (self.angle // 90) * (1 + self.k)
        half = self.radius * math.radians(self.angle / nseg) / 2 * 0.98
        out = []
        for s in range(nseg):
            a = math.radians((s + 0.5) * self.angle / nseg)
            rad = G.matvec(self.R, (math.cos(a), math.sin(a), 0))
            tan = G.matvec(self.R, (-math.sin(a), math.cos(a), 0))
            out.append(G.Box(G.add(self.C, G.mul(rad, self.radius)), [rad, tan, zl],
                             (g / 2 - 0.1, half, g / 2), self.id, "curve"))
        return out

    def ports(self, asm):
        ka, kb = self.port_kinds
        return [Port(self.id, rvec(self.pa), G.mul(tuple(map(float, self.dir)), -1), ka, "A"),
                Port(self.id, rvec(self.pb), self.db, kb, "B")]

    def boxes(self):
        return self._chain if self.placed else []

    def ignores(self, other, asm):
        return frozenset((self.id, other.id)) in asm.joined      # faces encostadas no encaixe

    def config(self, asm):
        ka, kb = self.port_kinds
        prm = {"k": self.k, "angle": self.angle, "port_a": ka, "port_b": kb}
        code = {"pin": "st", "recess": "so", "plain": "fl"}
        return f"curve-r{self.k + 1}-a{self.angle}-{code[ka]}{code[kb]}", "curve.scad", prm

    def matrix(self, asm):
        return self.R, self.C


# ============================================================
# WHEEL — depende das portas do BRICK onde encosta
# ============================================================
class Wheel(Part):
    type = "wheel"
    order = 5
    stage = 2
    structural = False
    default_color = [0.16, 0.16, 0.18]

    def parse(self, rp, g):
        on = rp.get("on", "")
        if "." not in on:
            raise IRError(f"{self.id}: roda precisa de on = \"<peça>.<face>\"")
        self.on, self.on_face = on.split(".", 1)
        if self.on_face not in FACES:
            raise IRError(f"{self.id}: face '{self.on_face}' inválida (use {', '.join(names.FACES)})")
        self.diameter_cells = int(rp.get("cells", 4))
        self.width_cells = int(rp.get("width", 1))
        self.tread = rp.get("tread", "street")
        self.spokes = int(rp.get("spokes", 0))
        self.spoke_style = rp.get("spoke_style", "straight")

    def resolve(self, asm):
        g = asm.p.grid
        host = asm.parts.get(self.on)
        if not isinstance(host, Brick):
            return asm.err("ASM-010", f"{self.id}: on = '{self.on}' não é um BRICK da montagem")
        f = self.on_face
        a, s = FACE_AXIS[f], FACE_SIGN[f]
        cell_lo = [self.at[i] * g for i in range(3)]
        plane = host.hi[a] if s > 0 else host.lo[a]
        expected = plane if s > 0 else plane - self.width_cells * g
        if s < 0 and abs(cell_lo[a] - (plane - g)) < EPS:
            expected = plane - g                     # `at` na célula encostada
        if abs(cell_lo[a] - expected) > EPS:
            return asm.err("ASM-010", f"{self.id}: at {list(self.at)} não encosta em {host.id}.{names.face(f)}",
                           f"a coordenada {AXES[a]} da roda deve ser {expected / g:g}")
        pos = [cell_lo[i] + g / 2 for i in range(3)]
        pos[a] = plane
        pos = rvec(pos)
        port = next((pt for pt in asm.ports[host.id] if pt.face == f and pt.pos == pos), None)
        if port is None:
            return asm.err("ASM-010", f"{self.id}: nenhuma porta de {host.id}.{names.face(f)} no centro da "
                           f"célula {list(self.at)}")
        if port.kind != "recess":
            asm.err("ASM-010", f"{self.id}: o eixo da roda exige um encaixe (socket); "
                    f"{host.id}.{names.face(f)} é {names.kind(port.kind)} ali",
                    f"fure {host.id} no eixo {AXES[a]} (holes) ou declare a face {names.face(f)} = socket")
        r, W = self.diameter_cells * g / 2, self.width_cells * g
        self.origin = tuple(pos[i] - (r if i != a else (0 if s > 0 else W)) for i in range(3))
        self.size = tuple(W if i == a else 2 * r for i in range(3))
        self.axis, self.sign, self.center, self.radius = a, s, pos, r
        self.placed = True
        asm.joints.append(Joint("axle", self.id, host.id, a, pos, FACE_NORMAL[f], sign=s,
                                width=self.width_cells))

    def ignores(self, other, asm):
        return other.type in ("brick", "node", "component", "wheel")   # roda × caixa: teste por cilindro

    def config(self, asm):
        prm = {"wheel_cells": self.diameter_cells, "width_cells": self.width_cells,
               "tread": self.tread, "spokes": self.spokes}
        lugs = {"offroad": (14, 2.75), "balloon": (16, 2)}.get(self.tread)
        if lugs:
            prm["tread_count"] = max(lugs[0], int(self.diameter_cells * lugs[1]))
        key = f"wheel-d{self.diameter_cells}"
        if (self.width_cells, self.tread, self.spokes) != (1, "street", 0):
            key += f"-w{self.width_cells}-{self.tread}-s{self.spokes}"
        if self.spoke_style != "straight":
            prm["spoke_style"] = self.spoke_style
            key += f"-{self.spoke_style}"
        return key, "wheel.scad", prm

    def matrix(self, asm):
        return G.frame_z_to(self.axis, self.sign), self.center

    def explode_with(self):
        return (self.on,)


# ============================================================
# MOCK — volume de um componente real
# ============================================================
class Component(Part):
    type = "component"
    order = 4
    structural = False
    printed = False
    default_color = [0.55, 0.75, 0.95, 0.45]
    SHAPES = ("box", "cyl", "cable", "text")

    def parse(self, rp, g):
        self.msize = tuple(float(c) for c in rp.get("size", (g, g, g)))
        self.shape = rp.get("shape", "box")
        if self.shape not in self.SHAPES:
            raise IRError(f"{self.id}: shape = {self.shape!r}: use {', '.join(self.SHAPES)}")
        self.maxis = rp.get("axis", "z")
        self.label = rp.get("label", self.id)
        self.mass = rp.get("mass")                   # g; None = estimar pelo volume
        self.text = rp.get("text", "")
        self.points = None
        self.collides = self.shape in ("box", "cyl")  # cabo é flexível, texto é decalque
        self.size = self.msize
        if self.shape == "cable":
            self._parse_cable(rp, g)
        elif self.shape == "cyl":                    # size = [Ø, Ø, comprimento] no eixo `axis`
            d, _, length = self.msize
            self.size = tuple(length if a == self.maxis else d for a in "xyz")

    def _parse_cable(self, rp, g):
        self.points = [tuple(float(c) * g for c in q) for q in rp.get("points", [])]
        if len(self.points) < 2:
            raise IRError(f"{self.id}: cabo precisa de 2+ pontos")
        lo = [min(q[i] for q in self.points) for i in range(3)]
        hi = [max(q[i] for q in self.points) for i in range(3)]
        self.origin, self.size = tuple(lo), tuple(hi[i] - lo[i] for i in range(3))

    def boxes(self):
        return super().boxes() if self.collides else []


TYPES = {c.type: c for c in (Brick, Node, Strut, Curve, Wheel, Component)}
