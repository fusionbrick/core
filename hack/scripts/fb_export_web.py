#!/usr/bin/env python3
"""
fb_export_web — exporta uma montagem compilada para a web (three.js).

    python3 hack/scripts/fb_export_web.py examples/rover-orion/assembly.toml \\
        ../studio/apps/landing/public/assembly

Gera dois arquivos em <saída>/:

    <nome>.json   a montagem NA ORDEM DOS PASSOS: cada peça, cavilha, eixo e
                  componente com a matriz do assembly.scad (mm, Z para cima),
                  o passo, a cor e de onde chega (`from`, vetor unitário)
    <nome>.bin    as malhas únicas, simplificadas e compactadas
                  (posições int16 quantizadas + índices), num arquivo só

Nada aqui recalcula encaixe: posições, juntas e ordem vêm do compilador.
As malhas são só para TELA (simplificadas); para imprimir, use parts/*.stl.

Precisa de: pip install trimesh fast-simplification
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "impl", "python"))

from fusionbrick import asm as A            # noqa: E402
from fusionbrick import geom as G           # noqa: E402
from fusionbrick.asm import outputs as O    # noqa: E402

AXES = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
COLOR_DOWEL = [0.98, 0.72, 0.16]
COLOR_AXLE = [0.55, 0.56, 0.6]

# Orçamento de triângulos por malha: o bastante para ler furos e curvas
# no tamanho em que a montagem aparece, sem pesar o download.
KEEP, MIN_FACES, MAX_FACES = 0.4, 500, 22000
FULL = ("wheel", "axle", "dowel")        # peças redondas pequenas: a simplificação aparece


def rows(R, t):
    return [[round(float(R[i][j]), 6) for j in range(3)] + [round(float(t[i]), 4)] for i in range(3)]


def simplify(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    n = len(m.faces)
    target = int(min(n, max(MIN_FACES, min(n * KEEP, MAX_FACES))))
    if target < n and not os.path.basename(path).startswith(FULL):
        m = m.simplify_quadric_decimation(face_count=target)
    return np.asarray(m.vertices, dtype=np.float64), np.asarray(m.faces, dtype=np.uint32)


def pack(meshes, parts_dir, bin_path):
    """Posições int16 (quantizadas na caixa da malha) + índices u16/u32, alinhados em 4 bytes."""
    table, blob = {}, bytearray()
    for key in sorted(meshes):
        v, f = simplify(os.path.join(parts_dir, f"{key}.stl"))
        lo, hi = v.min(axis=0), v.max(axis=0)
        span = np.where(hi - lo > 1e-9, hi - lo, 1.0)
        q = np.round((v - lo) / span * 65535 - 32768).astype("<i2")
        wide = len(v) > 65535
        idx = f.astype("<u4" if wide else "<u2")
        entry = {"nv": len(v), "nt": len(f), "wide": wide,
                 "lo": [round(float(x), 4) for x in lo], "span": [round(float(x), 4) for x in span]}
        for name, arr in (("pos", q), ("idx", idx)):
            while len(blob) % 4:
                blob.append(0)
            entry[name] = len(blob)
            blob += arr.tobytes()
        table[key] = entry
    with open(bin_path, "wb") as fh:
        fh.write(blob)
    return table


def own_direction(asm, part, step_of):
    """Para onde a peça se afasta das que já estão montadas (juntas do grid com passos anteriores)."""
    dirs = set()
    for j in asm.joints:
        if part.id not in (j.a, j.b) or j.axis < 0 or j.kind == "axle":
            continue
        other = j.b if j.a == part.id else j.a
        if other in step_of and step_of[other] < step_of[part.id]:
            c = part.mass_center()
            dirs.add((j.axis, 1 if c[j.axis] >= j.pos[j.axis] else -1))
    return dirs


def unit_vec(axis, sign):
    return [sign * a for a in AXES[axis]]


def component(part, g):
    c = list(part.color or part.default_color)[:3]
    base = {"id": part.id, "kind": "component", "shape": part.shape, "label": part.label,
            "color": [round(x, 3) for x in c]}
    if part.shape == "cable":
        return {**base, "d": part.msize[0], "points": [[round(v, 3) for v in p] for p in part.points]}
    if part.shape == "text":
        return None                                  # letreiro: fica para o render do OpenSCAD
    if part.shape == "cyl":
        d, _, length = part.msize
        ctr = [part.origin[i] + part.size[i] / 2 for i in range(3)]
        return {**base, "d": d, "h": length, "axis": part.maxis, "at": [round(v, 3) for v in ctr]}
    return {**base, "at": [round(part.origin[i] + part.size[i] / 2, 3) for i in range(3)],
            "size": [round(v, 3) for v in part.size]}


def export(toml_path, out_dir):
    asm = A.load(toml_path).compile()
    if not asm.ok:
        sys.exit("montagem com erro — rode `fb_assemble.py check` primeiro")
    parts_dir = os.path.join(os.path.dirname(toml_path), "parts")
    steps, order, comp_order = O.steps(asm)
    solid = [q for q in asm.parts.values() if q.printed and q.placed and q.id in order]
    lo = [min(q.lo[i] for q in solid) for i in range(3)]
    hi = [max(q.hi[i] for q in solid) for i in range(3)]
    subs = {i for i, g in enumerate(asm.groups) if g.get("sub")}

    # direção de cada passo: o voto das juntas das suas peças com o que já está montado
    own = {q.id: own_direction(asm, q, order) for q in solid}
    step_dir = {}
    for k in range(len(steps)):
        votes = {}
        for q in solid:
            if order[q.id] == k:
                for d in own[q.id]:
                    votes[d] = votes.get(d, 0) + 1
        if votes:
            step_dir[k] = unit_vec(*max(votes, key=votes.get))

    def came_from(q):
        """Um passo = um movimento: todas as peças do passo chegam do mesmo lado. Roda: pelo eixo."""
        if q.type == "wheel":
            return unit_vec(q.axis, q.sign)
        return step_dir.get(order[q.id], [0, 0, 1])     # sem voto (1º passo): pousa de cima

    items, meshes = [], set()
    direction = {}
    for q in sorted(solid, key=lambda q: (order[q.id], q.type == "wheel")):
        key = q.config(asm)[0]
        meshes.add(key)
        direction[q.id] = came_from(q)
        items.append({"id": q.id, "kind": q.type, "mesh": key, "m": rows(*q.matrix(asm)),
                      "from": direction[q.id], "step": order[q.id],
                      "color": [round(c, 3) for c in (q.color or q.default_color or [0.6, 0.6, 0.6])][:3]})
    for j in asm.joints:
        if j.kind == "dowel" and j.a in order and j.b in order:
            later = j.a if order[j.a] >= order[j.b] else j.b
            R = G.along(j.dir) if j.axis < 0 else G.frame_z_to(j.axis, 1)
            meshes.add("dowel")
            items.append({"id": f"cavilha-{len(items)}", "kind": "dowel", "mesh": "dowel",
                          "m": rows(R, j.pos), "from": direction[later], "step": order[later],
                          "color": COLOR_DOWEL})
        elif j.kind == "axle" and j.a in order:
            key = O._axle_key(j.width)
            meshes.add(key)
            items.append({"id": f"eixo-{j.a}", "kind": "axle", "mesh": key,
                          "m": rows(G.frame_z_to(j.axis, j.sign), j.pos), "from": direction[j.a],
                          "step": order[j.a], "color": COLOR_AXLE})
    for part in asm.of("component"):
        c = component(part, asm.p.grid)
        if c:
            items.append({**c, "step": comp_order.get(part.id, len(steps) - 1), "from": [0, 0, 1]})
    items.sort(key=lambda it: it["step"])

    os.makedirs(out_dir, exist_ok=True)
    table = pack(meshes, parts_dir, os.path.join(out_dir, f"{asm.name}.bin"))
    st = asm.stats()
    printed = [it for it in items if it["kind"] != "component"]
    doc = {
        "name": asm.name, "intent": asm.intent, "grid": asm.p.grid,
        "bounds": {"lo": [round(v, 3) for v in lo], "hi": [round(v, 3) for v in hi]},
        "steps": [{"id": s["id"], "note": s["note"], "sub": i in subs,
                   "count": sum(1 for it in items if it["step"] == i)} for i, s in enumerate(steps)],
        "stats": {"printed": len(printed),
                  "structural": sum(1 for it in printed if it["kind"] not in ("dowel", "axle")),
                  "dowels": sum(1 for it in printed if it["kind"] == "dowel"),
                  "components": len(items) - len(printed),
                  "unique_stl": st.get("unique_stl", len(meshes)),
                  "size_mm": [round(hi[i] - lo[i], 1) for i in range(3)]},
        "meshes": table,
        "items": items,
    }
    path = os.path.join(out_dir, f"{asm.name}.json")
    with open(path, "w") as f:
        json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
    tris = sum(m["nt"] for m in table.values())
    drawn = sum(table[it["mesh"]]["nt"] for it in printed)
    print(f"{path}: {len(printed)} impressas + {len(items) - len(printed)} componentes em {len(steps)} passos")
    print(f"  {len(table)} malhas · {tris} triângulos únicos · {drawn} desenhados · "
          f".bin {os.path.getsize(os.path.join(out_dir, asm.name + '.bin')) / 1e6:.2f} MB · "
          f".json {os.path.getsize(path) / 1e3:.0f} kB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    export(sys.argv[1], sys.argv[2])
