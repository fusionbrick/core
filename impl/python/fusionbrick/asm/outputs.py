"""
Saídas do compilador: lista de peças, passo a passo, relatório e o
assembly.scad (que só posiciona STLs — nenhuma geometria é desenhada
aqui, exceto os componentes).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List

from .. import geom as G
from ..brick import FACES
from . import names
from .model import r4

PALETTE = [
    [0.93, 0.93, 0.90], [0.20, 0.42, 0.72], [0.88, 0.40, 0.20],
    [0.30, 0.62, 0.40], [0.95, 0.75, 0.20], [0.55, 0.40, 0.70],
]
COLOR_PIN = [0.95, 0.62, 0.15]
COLOR_AXLE = [0.70, 0.71, 0.73]
PRIMITIVES = ("hole_d", "wall", "collar_w", "collar_depth", "tolerance", "gap", "pin_len")


# ------------------------------------------------------------
# BOM
# ------------------------------------------------------------
def _axle_key(width: int) -> str:
    return "axle" if width == 1 else f"axle-w{width}"


def bom(asm) -> List[dict]:
    rows: Dict[str, dict] = {}

    def add(key, scad, prm, pid=None, n=1):
        row = rows.setdefault(key, {"key": key, "scad": scad, "params": prm, "count": 0, "ids": []})
        row["count"] += n
        if pid:
            row["ids"].append(pid)

    for part in asm.parts.values():
        if part.printed and (part.placed or part.type == "wheel"):
            add(*part.config(asm), pid=part.id)
    n_dowel = sum(1 for j in asm.joints if j.kind == "dowel")
    if n_dowel:
        add("dowel", "pin.scad", {"ends": 2}, n=n_dowel)
    widths = [j.width for j in asm.joints if j.kind == "axle"]
    for w in sorted(set(widths)):
        add(_axle_key(w), "axle.scad", {} if w == 1 else {"width_cells": w}, n=widths.count(w))
    return list(rows.values())


def bom_md(asm) -> str:
    rows = bom(asm)
    L = [f"# {asm.name} — lista de peças", "", asm.intent, "",
         "| Qtd | Peça | Configuração | Usada em |", "| --- | --- | --- | --- |"]
    for row in rows:
        prm = ", ".join(f"{k}={v}" for k, v in row["params"].items())
        L.append(f"| {row['count']} | `{row['key']}.stl` | {row['scad']} {prm} | "
                 f"{', '.join(row['ids']) or '—'} |")
    L += ["", f"Total: {sum(r['count'] for r in rows)} peças impressas."]
    comps = asm.of("component")
    if comps:
        L += ["", "## Componentes — não imprimir", "",
              "Volumes reservados para componentes reais; entram na checagem de colisão.", "",
              "| Componente | Medidas (mm) |", "| --- | --- |"]
        seen: Dict[tuple, int] = {}
        for q in comps:
            seen[(q.label, tuple(q.msize))] = seen.get((q.label, tuple(q.msize)), 0) + 1
        for (lbl, sz), n in seen.items():
            L.append(f"| {lbl}{f' ×{n}' if n > 1 else ''} | {' × '.join(f'{v:g}' for v in sz)} |")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------
# Passos
# ------------------------------------------------------------
def steps(asm):
    """(passos, peça → índice do passo, componente → índice do passo)."""
    order: Dict[str, int] = {}
    component_order: Dict[str, int] = {}
    out = []

    def new_step(sid, note=""):
        out.append({"id": sid, "note": note, "parts": [], "dowels": 0, "axles": 0})
        return len(out) - 1

    for gi, g in enumerate(asm.groups):
        k = new_step(g.get("id", f"passo-{gi + 1}"), g.get("note", ""))
        for pid in g.get("parts", []):
            part = asm.parts.get(pid)
            if part is None or pid in order:
                continue
            if part.type == "component":
                component_order[pid] = k
            else:
                order[pid] = k
                out[k]["parts"].append(pid)
    for label, wanted in (("estrutura", lambda q: q.structural), ("rodas", lambda q: q.type == "wheel")):
        rest = [q.id for q in asm.parts.values() if q.id not in order and wanted(q)]
        if rest:
            k = new_step(label)
            out[k]["parts"] = rest
            order.update({pid: k for pid in rest})
    for j in asm.joints:
        if j.kind in ("dowel", "axle"):
            out[max(order.get(j.a, 0), order.get(j.b, 0))][j.kind + "s"] += 1
    return out, order, component_order


def steps_md(asm) -> str:
    L = [f"# {asm.name} — passo a passo", ""]
    for i, st in enumerate(steps(asm)[0], 1):
        L.append(f"{i}. **{st['id']}** — {', '.join(st['parts'])}")
        if st["note"]:
            L.append(f"    {st['note']}")
        extra = []
        if st["dowels"]:
            extra.append(f"{st['dowels']} cavilha(s) nos encontros socket × socket")
        if st["axles"]:
            extra.append(f"{st['axles']} eixo(s): a roda primeiro no eixo, depois o eixo na peça")
        if extra:
            L.append("    " + "; ".join(extra) + ".")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------
# Relatórios
# ------------------------------------------------------------
def summary(asm) -> str:
    n = {t: len(asm.of(t)) for t in ("brick", "wheel", "node", "strut", "curve", "component")}
    extra = "".join(f" · {n[t]} {lbl}" for t, lbl in
                    (("node", "nós"), ("strut", "vigas"), ("curve", "curvas"), ("component", "componentes")) if n[t])
    cnt = {k: sum(1 for j in asm.joints if j.kind == k) for k in ("integral", "dowel", "axle")}
    head = (f"{'ok   ' if asm.ok else 'FALHA'} {asm.name}: {n['brick']} blocos · {n['wheel']} rodas{extra} · "
            f"{cnt['integral']} encaixes por pino · {cnt['dowel']} cavilhas · {cnt['axle']} eixos")
    rank = {"error": 0, "warn": 1, "info": 2}
    return "\n".join([head] + [f.line() for f in sorted(asm.findings, key=lambda f: rank[f.severity])])


JOINT_NAMES = {"integral": "pino", "dowel": "cavilha", "axle": "eixo"}


def ports_report(asm, pid: str) -> str:
    part = asm.parts.get(pid)
    if part is None or pid not in asm.ports:
        return f"{pid}: sem portas (não existe ou não foi posicionada)"
    used = {}
    for j in asm.joints:
        for x, y in ((j.a, j.b), (j.b, j.a)):
            used[(x, j.pos)] = f"{JOINT_NAMES.get(j.kind, j.kind)} com {y}"
    lines = [f"{pid}:"]
    labels = list(dict.fromkeys(pt.label for pt in asm.ports[pid]))
    for lbl in (FACES if part.type == "brick" else labels):
        pts = [pt for pt in asm.ports[pid] if pt.label == lbl]
        if not pts:
            continue
        lines.append(f"  {names.face(lbl)}  ({', '.join(sorted({names.kind(pt.kind) for pt in pts}))})")
        for pt in pts:
            st = used.get((pid, pt.pos), "livre" if pt.kind != "plain" else "—")
            lines.append(f"    {asm.cell_of(pt.pos, pt.axis):>14}  {names.kind(pt.kind):6}  {st}")
    return "\n".join(lines)


# ------------------------------------------------------------
# assembly.scad
# ------------------------------------------------------------
def _matrix(R, t) -> list:
    return [[round(R[i][0], 6), round(R[i][1], 6), round(R[i][2], 6), r4(t[i])] for i in range(3)] \
        + [[0, 0, 0, 1]]


def _exploder(asm, order, component_order):
    """
    Vista explodida: cada passo sobe um nível, e as peças de borda se
    afastam do centro no plano — para as junções ficarem à vista.
    """
    bricks = asm.of("brick")
    lo = [min(q.lo[i] for q in bricks) for i in range(3)] if bricks else [0, 0, 0]
    hi = [max(q.hi[i] for q in bricks) for i in range(3)] if bricks else [0, 0, 0]
    mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
    span = [max(hi[i] - lo[i], 1e-9) for i in range(3)]

    def one(pid):
        q = asm.parts[pid]
        e = [0.0, 0.0, float(order.get(pid, component_order.get(pid, 0)))]
        if q.type == "brick":
            for i in (0, 1):
                c = (q.lo[i] + q.hi[i]) / 2 - mid[i]
                if abs(c) > 0.3 * span[i] and q.size[i] < 0.5 * span[i]:
                    e[i] = 0.7 if c > 0 else -0.7
        return e

    def off(*pids):
        es = [one(pid) for pid in pids]
        return [sum(e[i] for e in es) / len(es) for i in range(3)] if len(es) > 1 else es[0]

    return off


def _component_body(part) -> str:
    if part.shape == "cable":
        d = part.msize[0]
        return "{ " + " ".join(
            f"hull() {{ translate({[r4(v) for v in a]}) sphere(d = {d:g}, $fn = 12); "
            f"translate({[r4(v) for v in b]}) sphere(d = {d:g}, $fn = 12); }}"
            for a, b in zip(part.points, part.points[1:])) + " }"
    if part.shape == "text":
        h, _, dep = part.msize
        rz = part.maxis if part.maxis not in "xyz" else 0
        return (f"translate({[r4(v) for v in part.origin]}) rotate([0, 0, {rz}]) "
                f"linear_extrude({dep:g}) text(\"{part.text}\", size = {h:g}, halign = \"center\", "
                f"valign = \"center\", font = \"Liberation Sans:style=Bold\");")
    if part.shape == "cyl":
        d, _, length = part.msize
        rot = {"x": "[0, 90, 0]", "y": "[-90, 0, 0]", "z": "[0, 0, 0]"}[part.maxis]
        ctr = [part.origin[i] + part.size[i] / 2 for i in range(3)]
        return (f"translate({[r4(v) for v in ctr]}) rotate({rot}) "
                f"cylinder(d = {d:g}, h = {length:g}, center = true, $fn = 32);")
    return f"translate({[r4(v) for v in part.origin]}) cube({[r4(v) for v in part.size]});"


def _connector_line(asm, j, off, parts_dir) -> str:
    if j.kind == "dowel":
        R = G.along(j.dir) if j.axis < 0 else G.frame_z_to(j.axis, 1)
        return (f"    place(\"{parts_dir}/dowel.stl\", {_matrix(R, j.pos)}, "
                f"{COLOR_PIN}, {off(j.a, j.b)});")
    e = off(j.b)
    e = [e[i] + (1.2 * j.sign if i == j.axis else 0) for i in range(3)]
    return (f"    place(\"{parts_dir}/{_axle_key(j.width)}.stl\", "
            f"{_matrix(G.frame_z_to(j.axis, j.sign), j.pos)}, {COLOR_AXLE}, {e});")


HEADER = """// ============================================================
// ASSEMBLY — {name}
// {intent}
// ============================================================
// GERADO por fusionbrick.assembly a partir de assembly.toml.
// Não edite: mude o assembly.toml e rode `make assemble`.
// Cada import é um STL de configuração ÚNICA em parts/.
// ============================================================

/* [Montagem] */
explode = 0; // [0:1:40]
show_pins = true;

module place(file, m, c, e) {{
    translate(e * explode) multmatrix(m) color(c) import(file, convexity = 6);
}}
"""


def scad(asm, parts_dir: str = "parts") -> str:
    st, order, component_order = steps(asm)
    off = _exploder(asm, order, component_order)
    group_color = {pid: PALETTE[i % len(PALETTE)] for i, s in enumerate(st) for pid in s["parts"]}
    L = HEADER.format(name=asm.name, intent=asm.intent).split("\n")
    solid = [q for q in asm.parts.values() if q.printed and q.placed]
    for part in sorted(solid, key=lambda q: {"brick": 0, "wheel": 1}.get(q.type, 2)):
        key = part.config(asm)[0]
        c = part.color or part.default_color or group_color.get(part.id, PALETTE[0])
        e = off(*part.explode_with())
        if part.type == "wheel":                   # a roda se afasta mais que o eixo
            e = [e[i] + (2.2 * part.sign if i == part.axis else 0) for i in range(3)]
        L.append(f"place(\"{parts_dir}/{key}.stl\", {_matrix(*part.matrix(asm))}, "
                 f"{list(c)}, {e});  // {part.id}")
    L += ["", "show_components = true;", "if (show_components) {"]
    for part in asm.of("component"):
        c = list(part.color or part.default_color)
        if len(c) == 3:
            c.append(0.45)
        note = f"componente {part.id}" + ("" if part.shape == "text" else f": {part.label}")
        L.append(f"    translate({off(part.id)} * explode) color({c}) {_component_body(part)}  // {note}")
    L += ["}", "", "if (show_pins) {"]
    L += [_connector_line(asm, j, off, parts_dir) for j in asm.joints if j.kind in ("dowel", "axle")]
    L.append("}")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------
# Render das peças (OpenSCAD)
# ------------------------------------------------------------
def _scad_value(v) -> str:
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_scad_value(x) for x in v) + "]"
    return f"{v:g}"


def scad_args(params: dict, p, fn: int) -> List[str]:
    out = []
    for k in PRIMITIVES:
        out += ["-D", f"{k}={getattr(p, k):g}"]
    out += ["-D", f"$fn={fn}"]
    for k, v in params.items():
        out += ["-D", f"{k}={_scad_value(v)}"]
    return out


def render_jobs(asm, scad_dir: str, out_dir: str, fn: int = 48):
    """(stl, carimbo, assinatura, comando) de cada STL que ainda falta gerar."""
    jobs = []
    for row in bom(asm):
        src = os.path.join(scad_dir, row["scad"])
        with open(src, "rb") as f:
            src_h = hashlib.sha1(f.read()).hexdigest()[:8]
        stl = os.path.join(out_dir, row["key"] + ".stl")
        stamp = stl + ".src"
        sig = f"{src_h} {fn} {json.dumps(row['params'], sort_keys=True)} {asm.p}"
        if os.path.exists(stl) and os.path.exists(stamp) and open(stamp).read() == sig:
            continue
        cmd = ["openscad", "--export-format", "binstl", "-o", stl] + scad_args(row["params"], asm.p, fn) + [src]
        jobs.append((stl, stamp, sig, cmd))
    return jobs
