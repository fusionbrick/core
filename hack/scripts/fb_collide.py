#!/usr/bin/env python3
"""
fb_collide — verificação INDEPENDENTE do compilador de montagem.

Lê o assembly.scad gerado, acha os pares de peças cujas caixas se
sobrepõem e calcula a interseção EXATA (CGAL) de cada par a partir
dos STLs reais — com machos, cavilhas e eixos. O compilador decide
por regra; isto confere a geometria. Volume ≠ 0 é colisão.

  fb_collide.py examples/<nome>/assembly.scad [-j N] [--only <trecho do id>]

Lento (CGAL): use como teste de regressão, não a cada montagem.
"""

import concurrent.futures as cf
import os
import re
import struct
import subprocess
import sys
import tempfile

# Volume abaixo disto é ruído de malha (arestas tangentes), não colisão:
# 0.5 mm³ ≈ um cubo de 0,8 mm de lado.
TOL = 0.5

LINE = re.compile(r'place\("([^"]+)", (\[\[.*?\]\]), \[[^\]]*\], \[[^\]]*\]\);(?:\s*//\s*(\S+))?')


def read_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:5] == b"solid" and (b"facet" in data[:400] or b"endsolid" in data[:400]):
        pts = re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data)
        return [tuple(float(v) for v in p) for p in pts]
    n = struct.unpack("<I", data[80:84])[0]
    out = []
    for i in range(n):
        vals = struct.unpack("<12f", data[84 + 50 * i: 84 + 50 * i + 48])
        out += [vals[3:6], vals[6:9], vals[9:12]]
    return out


def volume(path):
    pts = read_stl(path)
    vol = 0.0
    for i in range(0, len(pts) - 2, 3):
        a, b, c = pts[i], pts[i + 1], pts[i + 2]
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(vol)


def bbox(pts, m):
    tp = [[sum(m[i][j] * p[j] for j in range(3)) + m[i][3] for i in range(3)] for p in pts]
    return [min(p[i] for p in tp) for i in range(3)], [max(p[i] for p in tp) for i in range(3)]


def _arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def placed_parts(scad, base):
    """[(nome, stl, matriz, lo, hi)] de cada place() do assembly.scad."""
    items, cache = [], {}
    for k, mt in enumerate(LINE.finditer(open(scad).read())):
        f, m, name = mt.group(1), eval(mt.group(2)), mt.group(3) or f"conector{k}"
        if f not in cache:
            cache[f] = read_stl(os.path.join(base, f))
        items.append((name, f, m) + bbox(cache[f], m))
    return items


def neighbour_pairs(items, only=None):
    """Pares cujas caixas se sobrepõem — os únicos que podem colidir."""
    def touch(a, b):
        return all(min(a[4][q], b[4][q]) - max(a[3][q], b[3][q]) > 1e-4 for q in range(3))

    def wanted(a, b):
        return not only or only in a[0] or only in b[0]

    return [(a, b) for i, a in enumerate(items) for b in items[i + 1:] if wanted(a, b) and touch(a, b)]


def main():
    scad = sys.argv[1]
    jobs = int(_arg("-j", os.cpu_count() or 2))
    only = _arg("--only")
    base = os.path.dirname(os.path.abspath(scad))
    items = placed_parts(scad, base)
    pairs = neighbour_pairs(items, only)
    print(f"{len(items)} peças posicionadas, {len(pairs)} pares com caixas sobrepostas")

    def run(a, b, nudge):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "x.scad")
            with open(src, "w") as fh:
                fh.write("intersection() {\n")
                for k, (_, f, m, _, _) in enumerate((a, b)):
                    t = f"translate({list(nudge)}) " if k and nudge else ""
                    fh.write(f'  {t}multmatrix({m}) import("{os.path.join(base, f)}", convexity=6);\n')
                fh.write("}\n")
            out = os.path.join(td, "x.stl")
            r = subprocess.run(["openscad", "-o", out, src], capture_output=True, text=True)
            if "CGAL error" in r.stderr or "assertion violation" in r.stderr:
                return None                      # CGAL quebrou: o STL sai lixo
            if "Current top level object is empty" in r.stderr or not os.path.exists(out):
                return 0.0
            return volume(out)

    def manifold(a, b):
        """Plano B robusto (manifold3d), quando instalado."""
        try:
            import numpy as np
            import trimesh
            import manifold3d as m3
        except ImportError:
            return None
        solids = []
        for _, f, m, _, _ in (a, b):
            t = trimesh.load(os.path.join(base, f), process=True)
            t.apply_transform(np.array(m, dtype=float))
            mesh = m3.Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32),
                           tri_verts=np.asarray(t.faces, dtype=np.uint32))
            solid = m3.Manifold(mesh)
            if solid.status() != m3.Error.NoError:
                return None
            solids.append(solid)
        return float((solids[0] ^ solids[1]).volume())

    def test(pair):
        # O CGAL do OpenSCAD 2021 às vezes falha em faces quase
        # coplanares (nó × viga diagonal). Falha NÃO é colisão: tenta de
        # novo com um empurrão de micrômetros; se insistir, marca "?".
        a, b = pair
        for nudge in (None, (0.002, 0.001, 0.0015), (-0.0015, 0.002, -0.001)):
            v = run(a, b, nudge)
            if v is not None:
                return a[0], b[0], v
        return a[0], b[0], manifold(a, b)

    worst = 0.0
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        unknown = 0
        for na, nb, v in ex.map(test, pairs):
            if v is None:
                unknown += 1
                print(f"  ?       {na} × {nb}: CGAL falhou e manifold3d indisponível — confira à mão")
                continue
            worst = max(worst, v)
            flag = "COLISÃO" if v > TOL else "ok"
            print(f"  {flag:7} {na} × {nb}: {v:.4f} mm³")
    verdict = "HÁ COLISÃO" if worst > TOL else ("INDETERMINADO" if unknown else "ZERO COLISÃO")
    line = f"pior interseção: {worst:.4f} mm³ — {verdict}"
    print("\n" + line)
    if not only:                                   # o veredito completo fica ao lado da montagem
        with open(os.path.join(base, "collide.txt"), "w") as fh:
            fh.write(f"{len(pairs)} pares de peças vizinhas\n{line}\n")
    return 0 if verdict == "ZERO COLISÃO" else 1


if __name__ == "__main__":
    sys.exit(main())
