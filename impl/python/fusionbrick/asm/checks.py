"""
As regras ASM-### de spec/assembly.md — uma função por regra.

Cada regra lê a montagem já posicionada e com as juntas resolvidas, e
registra achados com `asm.err / warn / info`. `RULES` é a ordem em que
rodam; `routes` roda antes das juntas porque reserva portas para fio.
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict

from .. import geom as G
from ..brick import AXES
from .model import EPS, rvec


# ------------------------------------------------------------
# ASM-007 — rotas de fio
# ------------------------------------------------------------
def _cells_between(c0, c1, a):
    step = 1 if c1[a] > c0[a] else -1
    return [tuple(c0[i] if i != a else v for i in range(3)) for v in range(c0[a], c1[a] + step, step)], step


def _route_leg(asm, rid, c0, c1, owner):
    diff = [i for i in range(3) if c0[i] != c1[i]]
    if len(diff) != 1:
        return asm.err("ASM-007", f"rota {rid}: trecho {list(c0)}→{list(c1)} não é reto")
    a, g = diff[0], asm.p.grid
    cells, step = _cells_between(c0, c1, a)
    prev = None
    for cell in cells:
        b = owner(cell)
        if b is None:
            asm.err("ASM-007", f"rota {rid}: célula {list(cell)} fora de peça")
        else:
            if b.axes[a] != "bored":
                asm.err("ASM-007", f"rota {rid}: {b.id} tem eixo {AXES[a]} sólido em {list(cell)}",
                        f"fure o eixo {AXES[a]} de {b.id}")
            if prev is not None and prev.id != b.id:        # fronteira entre peças: porta aberta
                pos = [(cell[i] + 0.5) * g for i in range(3)]
                pos[a] = (cell[a] if step > 0 else cell[a] + 1) * g
                asm.open_ports.add((rvec(pos), a))
        prev = b


def routes(asm):
    g = asm.p.grid
    solid = [b for b in asm.of("brick") if not b.slab]

    def owner(cell):
        c = [(cell[i] + 0.5) * g for i in range(3)]
        return next((b for b in solid if all(b.lo[i] < c[i] < b.hi[i] for i in range(3))), None)

    for rt in asm.routes:
        rid = rt.get("id", "rota")
        path = [tuple(int(v) for v in c) for c in rt.get("path", [])]
        if len(path) < 2:
            asm.err("ASM-007", f"rota {rid}: precisa de 2+ pontos")
        for c0, c1 in zip(path, path[1:]):
            _route_leg(asm, rid, c0, c1, owner)


# ------------------------------------------------------------
# ASM-002 — duas peças não ocupam o mesmo volume
# ------------------------------------------------------------
def collisions(asm):
    for part in asm.parts.values():
        if part.placed and hasattr(part, "check"):
            part.check(asm)
    boxes = [bx for part in asm.parts.values() if part.collides for bx in part.boxes()]
    for A, B in itertools.combinations(boxes, 2):
        pa, pb = asm.parts[A.owner], asm.parts[B.owner]
        if pa is pb or pa.ignores(pb, asm) or pb.ignores(pa, asm):
            continue
        d = G.overlap_depth(A, B)
        if d > 0.05:
            mock = "component" in (pa.type, pb.type)
            asm.err("ASM-002", f"{A.owner} e {B.owner} se interpenetram ({d:.1f}mm)",
                    "o volume reservado não cabe aí: mova o componente ou abra espaço" if mock
                    else "desloque uma das peças ou reduza size")


def _wheel_hits_box(w, b) -> bool:
    a = w.axis
    if min(w.hi[a], b.hi[a]) - max(w.lo[a], b.lo[a]) <= EPS:
        return False
    d2 = sum(max(b.lo[q] - w.center[q], 0, w.center[q] - b.hi[q]) ** 2 for q in range(3) if q != a)
    return math.sqrt(d2) < w.radius - EPS


def _wheels_touch(w1, w2) -> bool:
    a = w1.axis
    if a != w2.axis or min(w1.hi[a], w2.hi[a]) - max(w1.lo[a], w2.lo[a]) <= EPS:
        return False
    perp = [i for i in range(3) if i != a]
    return math.dist([w1.center[i] for i in perp], [w2.center[i] for i in perp]) < w1.radius + w2.radius - EPS


def wheel_clearance(asm):
    """Roda é cilindro, não caixa: teste próprio, mais o vão livre do chão (ASM-010)."""
    wheels = [w for w in asm.of("wheel") if w.placed]
    solids = [q for q in asm.of("brick", "node", "component") if q.collides]
    for w in wheels:
        for b in solids:
            if _wheel_hits_box(w, b):
                asm.err("ASM-002", f"roda {w.id} invade {b.id}",
                        "afaste a roda (mais células na peça) ou use roda menor")
    for w1, w2 in itertools.combinations(wheels, 2):
        if _wheels_touch(w1, w2):
            asm.err("ASM-002", f"rodas {w1.id} e {w2.id} se tocam", "afaste os eixos ou use rodas menores")
    if wheels and solids:
        ground, low = min(w.lo[2] for w in wheels), min(b.lo[2] for b in solids)
        if low < ground - EPS:
            asm.warn("ASM-010", f"a estrutura desce {ground - low:g}mm abaixo das rodas — arrasta no chão")
        else:
            asm.info("ASM-010", f"vão livre do chão: {low - ground:g}mm")


# ------------------------------------------------------------
# ASM-006 — dois pinos no mesmo furo precisam caber
# ------------------------------------------------------------
def _bore_entries(asm):
    """(peça, eixo, posição no plano) → lados por onde entra um pino."""
    entries = defaultdict(set)

    def enter(pid, j, side=None):
        part = asm.parts[pid]
        if part.type != "brick":
            return
        if side is None:
            side = 1 if abs(j.pos[j.axis] - part.hi[j.axis]) < EPS else -1
        entries[(pid, j.axis, tuple(j.pos[i] for i in range(3) if i != j.axis))].add(side)

    for j in asm.joints:
        if j.axis < 0:
            continue
        if j.kind == "integral":
            enter(j.b, j)
        elif j.kind == "dowel":
            enter(j.a, j)
            enter(j.b, j)
        else:
            enter(j.b, j, j.sign)
    return entries


def shared_bores(asm):
    need = 2 * asm.p.pin_len + asm.p.gap
    bad = defaultdict(list)
    for (pid, axis, perp), sides in _bore_entries(asm).items():
        part = asm.parts[pid]
        if len(sides) == 2 and need > part.size[axis] + EPS:
            pos = list(perp)
            pos.insert(axis, part.lo[axis])
            bad[(pid, axis)].append(asm.cell_of(pos, axis))
    for (pid, axis), cells in bad.items():
        shown = " ".join(cells[:4]) + (f" … (+{len(cells) - 4})" if len(cells) > 4 else "")
        asm.err("ASM-006", f"{pid}: {len(cells)} furo(s) {AXES[axis]} com pino dos dois lados pedem "
                f"{need:g}mm e a peça tem {asm.parts[pid].size[axis]:g}mm — {shown}",
                "use laje mais grossa (≥ slab_both) ou desloque um dos encaixes")


# ------------------------------------------------------------
# ASM-005 — uma peça só
# ------------------------------------------------------------
def connectivity(asm):
    parent = {pid: pid for pid, q in asm.parts.items() if q.type != "component"}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for j in asm.joints:
        parent[find(j.a)] = find(j.b)
    comps = defaultdict(list)
    for pid in parent:
        comps[find(pid)].append(pid)
    if len(comps) > 1:
        groups = sorted(comps.values(), key=len, reverse=True)
        asm.err("ASM-005", f"{len(comps)} blocos soltos; separados do principal: "
                + " | ".join(", ".join(sorted(g)) for g in groups[1:]),
                "contato sem junção não conta: precisa de stud × socket, ou socket × socket (cavilha)")


# ------------------------------------------------------------
# ASM-004 — nenhuma peça gira em torno de uma linha
# ------------------------------------------------------------
def _slender(part) -> bool:
    return part.type == "strut" or (part.type == "brick" and sorted(part.cells)[:2] == [1, 1])


def rigidity(asm):
    parts = [q for q in asm.parts.values() if q.structural and q.placed]
    if len(parts) < 2:
        return
    held = {q.id: [] for q in parts}
    for j in asm.joints:
        if j.kind != "axle":                       # eixo de roda gira: não trava ninguém
            for pid in (j.a, j.b):
                if pid in held:
                    held[pid].append(j)
    for pid, js in held.items():
        if not js or pid in asm.hinges or len({j.line() for j in js}) > 1:
            continue
        spots = {tuple(round(c, 2) for c in j.pos) for j in js}
        if _slender(asm.parts[pid]) and len(spots) >= 2:
            asm.info("ASM-004", f"{pid}: membro de treliça — preso pelas duas pontas, "
                     "só gira sobre o próprio eixo")
        else:
            asm.err("ASM-004", f"{pid}: todas as junções estão numa mesma linha "
                    f"({len(js)} junção(ões)) — a peça gira em torno dela",
                    "junte por outra face ou por uma segunda célula, "
                    "ou declare em hinges se girar é a intenção")


# ------------------------------------------------------------
# ASM-012 — cada peça entra com um movimento só
# ------------------------------------------------------------
def _units(asm):
    """peça → unidade de montagem (a própria peça, ou o grupo com sub = true)."""
    unit = {pid: pid for pid in asm.parts}
    for g in asm.groups:
        if g.get("sub"):
            for pid in g.get("parts", []):
                unit[pid] = "grupo " + g.get("id", "?")
    return unit


def _move(j, mover, anchor, as_unit: bool):
    """(eixo, sentido) em que `mover` anda para fechar a junta j."""
    if as_unit:                                    # subconjunto: sentido pelo lado da peça que já está lá
        c = anchor.origin[j.axis] + anchor.size[j.axis] / 2
        return j.axis, -1 if j.pos[j.axis] > c else 1
    c = mover.origin[j.axis] + mover.size[j.axis] / 2
    return j.axis, 1 if j.pos[j.axis] > c else -1


def insertion(asm):
    """
    Na ordem de montagem, as juntas de cada peça com as que já estão no
    lugar precisam estar no mesmo eixo E no mesmo sentido. Dois eixos, ou
    os dois sentidos (peça entre duas já montadas), não montam à mão.
    Só juntas do grid entram: diagonais e eixos de roda ficam de fora.
    """
    when = {pid: i for i, pid in enumerate(asm.assembly_order())}
    unit = _units(asm)
    first = {}
    for pid, i in when.items():
        first[unit[pid]] = min(first.get(unit[pid], i), i)
    moves = defaultdict(set)
    for j in asm.joints:
        if j.kind == "axle" or not j.grid:
            continue
        pa, pb = asm.parts[j.a], asm.parts[j.b]
        ua, ub = unit[pa.id], unit[pb.id]
        if ua != ub:                               # entre unidades: anda a que vem depois
            mover, anchor = (pa, pb) if first[ua] > first[ub] else (pb, pa)
        else:                                      # dentro da unidade: peça a peça
            mover, anchor = (pa, pb) if when[pa.id] > when[pb.id] else (pb, pa)
        key = unit[mover.id] if ua != ub else mover.id
        moves[key].add(_move(j, mover, anchor, key != mover.id))
    for pid, mv in moves.items():
        if len(mv) > 1:
            desc = ", ".join(f"{'+' if s > 0 else '−'}{'xyz'[a]}" for a, s in sorted(mv))
            asm.warn("ASM-012", f"{pid}: precisaria entrar em {desc} ao mesmo tempo — não monta à mão",
                     "troque a ordem nos groups, monte um subconjunto antes (sub = true no grupo), "
                     "ou deixe flat as faces que travam o segundo movimento")


# ------------------------------------------------------------
# ASM-011 — pinos sem uso
# ------------------------------------------------------------
def free_studs(asm):
    bricks = asm.of("brick")
    used = {(j.a, j.pos) for j in asm.joints if j.kind == "integral"}
    floor = min((b.lo[2] for b in bricks), default=0)
    free = 0
    for b in bricks:
        for pt in asm.ports[b.id]:
            if pt.kind == "pin" and (b.id, pt.pos) not in used:
                free += 1
                if pt.face == "zn" and abs(pt.pos[2] - floor) < EPS:
                    asm.warn("ASM-011", f"{b.id}: pino exposto na base em {asm.cell_of(pt.pos, 2)} "
                             "— a peça não assenta plana")
    if free:
        asm.info("ASM-011", f"{free} pino(s) livre(s), prontos para receber peças")


RULES = [collisions, wheel_clearance, shared_bores, connectivity, rigidity, insertion, free_studs]
