"""
Métricas de QUALIDADE e de FÍSICA — não de validade.

`stats`   o quanto a montagem parece um kit técnico e quanto custa
          (resolução, cavilhas, reuso, mesa, pinos livres)
`physics` massa, centro de massa, tombamento e base de peças altas —
          estimativa de ordem de grandeza a partir dos STLs gerados
"""

from __future__ import annotations

import math
import os
import struct

PLA_G_MM3 = 1.24e-3
FILL = 0.55            # fração sólida típica de peça pequena FDM (paredes + ~20% infill)
MOCK_G_CM3 = 0.6       # densidade média de eletrônica sem `mass` declarada
BED_MM = 220


# ------------------------------------------------------------
# stats
# ------------------------------------------------------------
def _hints(s: dict, dowel_step: int) -> list:
    """Cada regra: (condição, texto). Tabela, não cascata de ifs."""
    printed, dowels, unique = s["printed"], s["dowels"], s["unique_stl"]
    more_step = "suba dowel_every" if dowel_step > 1 else "use dowel_every = 3"
    rules = [
        (s["parts_per_100mm"] < 15,
         f"baixa resolução ({s['parts_per_100mm']:.0f} peças/100mm; kit técnico fica em 15–40): "
         "aumente a escala ou quebre blocos grandes em vigas"),
        (printed and dowels / printed > 0.55,
         f"{dowels}/{printed} das peças impressas são cavilhas: {more_step}, "
         "pinos impressos (studs) onde não há ponta redonda, ou contatos mais curtos"),
        (unique and printed > 10 and printed / unique < 2.0,
         f"reuso baixo ({printed / max(unique, 1):.1f} cópias por STL): padronize comprimentos "
         "(ex.: 4, 8, 12) e use simetria"),
        (s["longest_mm"] > BED_MM,
         f"peça de {s['longest_mm']:.0f}mm passa da mesa típica ({BED_MM}mm): divida em duas"),
        (s["free_pins"] > 20,
         f"{s['free_pins']} pinos livres: use faces auto (cavilha só no contato) "
         "ou studs_on = \"edge\" nas placas"),
    ]
    return [text for cond, text in rules if cond]


def _envelope(parts):
    if not parts:
        return [0, 0, 0]
    lo = [min(q.origin[i] for q in parts) for i in range(3)]
    hi = [max(q.origin[i] + q.size[i] for q in parts) for i in range(3)]
    return [round(hi[i] - lo[i], 1) for i in range(3)]


def stats(asm) -> dict:
    rows = asm.bom()
    solid = [q for q in asm.parts.values() if q.printed and q.size[0]]
    # BEAM tem caixa folgada (diagonal); os nós das pontas já marcam o volume
    dims = _envelope([q for q in solid if q.type != "strut"] or solid)
    structural = [q for q in solid if q.structural]
    used = {(pid, j.pos) for j in asm.joints for pid in (j.a, j.b)}
    s = {
        "dims_mm": dims,
        "structural": len(structural),
        "printed": sum(r["count"] for r in rows),
        "unique_stl": len(rows),
        "dowels": sum(r["count"] for r in rows if r["key"] == "dowel"),
        "mocks": len(asm.of("component")),
        "free_pins": sum(1 for pid, pts in asm.ports.items() for pt in pts
                         if pt.kind == "pin" and (pid, pt.pos) not in used),
        "parts_per_100mm": round(len(structural) / max(max(dims) / 100.0, 0.01), 1),
        "longest_mm": max((max(q.size) for q in structural if q.type == "brick"), default=0),
    }
    s["hints"] = _hints(s, asm.dowel_step)
    return s


def stats_report(asm) -> str:
    s = stats(asm)
    d = s["dims_mm"]
    lines = [f"{asm.name}: {d[0]:g} × {d[1]:g} × {d[2]:g} mm",
             f"  estruturais {s['structural']} · impressas {s['printed']} "
             f"(cavilhas {s['dowels']}) · STLs únicos {s['unique_stl']} · componentes {s['mocks']} · "
             f"pinos livres {s['free_pins']}",
             f"  resolução {s['parts_per_100mm']} peças/100mm · maior peça {s['longest_mm']:g}mm"]
    return "\n".join(lines + ([f"  dica: {h}" for h in s["hints"]] or ["  sem alertas de qualidade"]))


# ------------------------------------------------------------
# physics
# ------------------------------------------------------------
def stl_volume(path: str) -> float:
    """Volume de um STL binário (soma dos tetraedros assinados)."""
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    vol = 0.0
    for i in range(n):
        v = struct.unpack("<9f", data[96 + 50 * i: 132 + 50 * i])
        a, b, c = v[0:3], v[3:6], v[6:9]
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(vol)


def _component_mass(m) -> float:
    if m.mass is not None:
        return float(m.mass)
    shape = 0.785 if m.shape == "cyl" else 1.0
    return m.size[0] * m.size[1] * m.size[2] / 1000.0 * MOCK_G_CM3 * shape


def _masses(asm, parts_dir: str):
    """[(massa g, centro mm, id)] e quantas peças ficaram sem STL."""
    vols, items, missing = {}, [], 0

    def volume(key):
        path = os.path.join(parts_dir, key + ".stl")
        if key not in vols:
            vols[key] = stl_volume(path) if os.path.exists(path) else None
        return vols[key]

    for q in asm.parts.values():
        if q.type == "component":
            if q.collides:
                items.append((_component_mass(q), q.mass_center(), q.id))
        elif q.placed:
            v = volume(q.config(asm)[0])
            if v is None:
                missing += 1
            else:
                items.append((v * PLA_G_MM3 * FILL, q.mass_center(), q.id))
    v = volume("dowel")
    if v:
        items += [(v * PLA_G_MM3, tuple(j.pos), "cavilha") for j in asm.joints if j.kind == "dowel"]
    return items, missing


def _tall_parts(asm, items, ground: float):
    """Peças altas e finas apoiadas por baixo (mastro, antena): massa em cima × base."""
    g = asm.p.grid
    out = []
    for q in asm.of("brick"):
        if not (q.size[2] >= 6 * g and max(q.size[0], q.size[1]) <= 2 * g and q.origin[2] > ground + 4 * g):
            continue
        base, z0 = _base_joints(asm, q)
        cx, cy = q.origin[0] + q.size[0] / 2, q.origin[1] + q.size[1] / 2
        above = [(m, c) for m, c, _ in items
                 if c[2] > q.origin[2] and abs(c[0] - cx) < 3 * g and abs(c[1] - cy) < 4 * g]
        if not base or not above:
            continue
        mass = sum(m for m, _ in above)
        if mass < 20:                              # poste de arco: nada pesado em cima
            continue
        arm = sum(m * c[2] for m, c in above) / mass - z0
        span = max((math.dist(a.pos, b.pos) for a in base for b in base), default=0.0)
        out.append({"id": q.id, "mass_g": mass, "arm_mm": arm, "joints": len(base), "span_mm": span,
                    "moment_nmm": mass / 1000 * 9.81 * 0.5 * arm})
    return out


def _base_joints(asm, q):
    """Juntas que seguram `q` por baixo; se ele apoia num pé mais largo, as do pé."""
    g = asm.p.grid
    z0 = q.origin[2]
    base = [j for j in asm.joints if q.id in (j.a, j.b) and abs(j.pos[2] - z0) < 1e-6]
    for fid in {j.b if j.a == q.id else j.a for j in base}:
        foot = asm.parts.get(fid)
        wider = foot is not None and foot.type == "brick" and foot.size[2] <= 2 * g \
            and foot.size[0] * foot.size[1] > q.size[0] * q.size[1]
        if wider:
            under = [j for j in asm.joints if fid in (j.a, j.b) and abs(j.pos[2] - foot.origin[2]) < 1e-6]
            if under:
                return under, foot.origin[2]
    return base, z0


def physics(asm, parts_dir: str) -> dict:
    items, missing = _masses(asm, parts_dir)
    total = sum(m for m, _, _ in items) or 1e-9
    com = [sum(m * c[i] for m, c, _ in items) / total for i in range(3)]
    out = {"mass_g": total, "com_mm": com, "missing": missing, "wheels": False}
    wheels = [w for w in asm.of("wheel") if w.placed]
    if not wheels:
        return out
    ground = min(w.origin[2] for w in wheels)
    xs = [w.origin[0] + w.size[0] / 2 for w in wheels]
    ys = [w.origin[1] + w.size[1] / 2 for w in wheels]
    h = com[2] - ground
    half_track, half_base = (max(ys) - min(ys)) / 2, (max(xs) - min(xs)) / 2
    off_x, off_y = com[0] - (max(xs) + min(xs)) / 2, com[1] - (max(ys) + min(ys)) / 2
    body = [q for q in asm.parts.values() if q.printed and q.placed]
    length = max(q.hi[0] for q in body) - min(q.lo[0] for q in body)
    wheel_d = wheels[0].diameter_cells * asm.p.grid
    out.update({
        "wheels": True, "com_height_mm": h, "com_offset_mm": (off_x, off_y),
        "tip_lateral_deg": math.degrees(math.atan2(half_track - abs(off_y), h)),
        "tip_long_deg": math.degrees(math.atan2(half_base - abs(off_x), h)),
        "track_mm": 2 * half_track, "wheelbase_mm": 2 * half_base,
        "wheel_d_mm": wheel_d, "wheel_ratio": wheel_d / length,
        "tall": _tall_parts(asm, items, ground),
    })
    return out


def physics_report(asm, parts_dir: str) -> str:
    ph = physics(asm, parts_dir)
    miss = f" ({ph['missing']} peça(s) sem STL — rode build)" if ph["missing"] else ""
    lines = [f"{asm.name}: massa estimada {ph['mass_g']:.0f} g{miss}"]
    if not ph["wheels"]:
        c = ph["com_mm"]
        return lines[0] + f"\n  centro de massa {c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f} mm (sem rodas: sem tombamento)"
    ox, oy = ph["com_offset_mm"]
    lines += [
        f"  centro de massa a {ph['com_height_mm']:.0f} mm do chão · desvio x {ox:+.0f} mm, y {oy:+.0f} mm",
        f"  tombamento: lateral {ph['tip_lateral_deg']:.0f}° · longitudinal {ph['tip_long_deg']:.0f}°"
        "  (rover: ≥ 45° lateral; < 35° é veto)",
        f"  bitola {ph['track_mm']:.0f} mm · entre-eixos {ph['wheelbase_mm']:.0f} mm · "
        f"roda Ø{ph['wheel_d_mm']:.0f} = {ph['wheel_ratio']:.2f} do comprimento",
    ]
    lines += [f"  {t['id']}: {t['mass_g']:.0f} g a {t['arm_mm']:.0f} mm da base · momento a 0,5 g = "
              f"{t['moment_nmm']:.0f} N·mm · {t['joints']} junta(s) na base, afastadas {t['span_mm']:.0f} mm"
              for t in ph["tall"]]
    return "\n".join(lines)


# ------------------------------------------------------------
# review — a ficha de qualidade (portões medidos do conselho)
# ------------------------------------------------------------
def _print_colors(asm) -> int:
    """Cores distintas da estrutura impressa — pneus ficam de fora (material próprio)."""
    return len({tuple(round(c, 2) for c in (q.color or q.default_color or (0, 0, 0))[:3])
                for q in asm.parts.values() if q.structural and q.placed})


def _collide_verdict(base_dir: str) -> str:
    path = os.path.join(base_dir, "collide.txt")
    if not os.path.exists(path):
        return "não rodou"
    with open(path) as f:
        return f.read().strip().splitlines()[-1].split("—")[-1].strip()


def gates(asm, parts_dir: str) -> list:
    """[(perfil, portão, valor medido, alvo, passou)] — o que o conselho exige antes de opinar."""
    s, codes = stats(asm), [f.code for f in asm.findings if f.severity != "info"]
    ph = physics(asm, parts_dir)
    undocumented = [g.get("id", "?") for g in asm.groups if not g.get("note")]
    share = s["dowels"] / s["printed"] if s["printed"] else 0
    reuse = s["printed"] / s["unique_stl"] if s["unique_stl"] else 0
    collide = _collide_verdict(asm.base_dir)
    rows = [
        ("Maker", "erros de encaixe", sum(f.severity == "error" for f in asm.findings), "0", asm.ok),
        ("Maker", "peças que não entram num movimento (ASM-012)", codes.count("ASM-012"), "0",
         "ASM-012" not in codes),
        ("Maker", "maior peça", f"{s['longest_mm']:g} mm", f"≤ {BED_MM} mm", s["longest_mm"] <= BED_MM),
        ("Maker", "pinos sem uso", s["free_pins"], "0", s["free_pins"] == 0),
        ("Maker", "cavilhas / peças impressas", f"{share:.0%}", "≤ 55%", share <= 0.55),
        ("Maker", "passos de montagem sem nota", len(undocumented), "0", not undocumented),
        ("Engenheiro", "colisão exata (fb_collide)", collide, "ZERO COLISÃO", collide == "ZERO COLISÃO"),
        ("Engenheiro", "cópias por STL único", f"{reuse:.1f}", "≥ 2", reuse >= 2 or s["printed"] <= 10),
        ("Designer", "resolução", f"{s['parts_per_100mm']} peças/100mm", "15–40",
         15 <= s["parts_per_100mm"] <= 40),
        ("Designer", "cores da estrutura", _print_colors(asm), "≤ 3", _print_colors(asm) <= 3),
    ]
    if ph["wheels"]:
        off = max(abs(v) for v in ph["com_offset_mm"])
        rows += [
            ("Engenheiro", "tombamento lateral", f"{ph['tip_lateral_deg']:.0f}°", "≥ 45°",
             ph["tip_lateral_deg"] >= 45),
            ("Engenheiro", "centro de massa fora do centro das rodas", f"{off:.0f} mm", "≤ 10 mm", off <= 10),
            ("Engenheiro", "arrasta no chão (ASM-010)", codes.count("ASM-010"), "0", "ASM-010" not in codes),
            ("Designer", "roda / comprimento", f"{ph['wheel_ratio']:.2f}", "0,20–0,45",
             0.20 <= ph["wheel_ratio"] <= 0.45),
        ]
    rows += [("Engenheiro", f"base de {t['id']}", f"{t['joints']} juntas a {t['span_mm']:.0f} mm",
              "≥ 4 juntas, ≥ 24 mm", t["joints"] >= 4 and t["span_mm"] >= 24) for t in ph.get("tall", [])]
    return rows


def review_report(asm, parts_dir: str) -> str:
    rows = gates(asm, parts_dir)
    failed = [r for r in rows if not r[4]]
    L = [f"{asm.name} — ficha de qualidade ({len(rows) - len(failed)}/{len(rows)} portões)", ""]
    for who in ("Maker", "Engenheiro", "Designer"):
        L += [f"  {'ok   ' if ok else 'FALHA'} {who:10} {name}: {value}  (alvo {target})"
              for w, name, value, target, ok in rows if w == who]
    L += ["", "APTO para o conselho opinar" if not failed else
          f"NÃO APTO: {len(failed)} portão(ões) medido(s) falham — conserte antes de discutir gosto"]
    return "\n".join(L)
