"""
Geometria mínima do compilador — stdlib pura, sem CAD.

Vetores, a rotação `along` (a mesma do node.scad), as 24 rotações do
cubo, caixa orientada (OBB) com teste de eixo separador, e os ternos
pitagóricos que dão comprimento de grid a uma diagonal.
"""

from __future__ import annotations

import math
import itertools
from typing import List, Optional, Sequence, Tuple

Vec = Tuple[float, float, float]


# ------------------------------------------------------------
# Álgebra mínima
# ------------------------------------------------------------
def norm(v) -> float:
    return math.sqrt(sum(c * c for c in v))


def unit(v) -> Vec:
    n = norm(v)
    return tuple(c / n for c in v)


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a, b) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


def matvec(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def along(u) -> List[List[float]]:
    """
    Rotação que leva +Z em `u` — MESMA conta do `along()` do
    node.scad (eixo = Z × u, ângulo = acos(u.z)). Precisa ser a
    mesma: é ela que alinha a seção quadrada da viga com a do braço.
    """
    u = unit(u)
    ax = (-u[1], u[0], 0.0)
    if norm(ax) < 1e-9:
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]] if u[2] > 0 else [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    k = unit(ax)
    a = math.acos(max(-1.0, min(1.0, u[2])))
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    x, y, z = k
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def line_key(pos, d) -> tuple:
    """Identifica a RETA (direção sem sinal + ponto) de uma junção."""
    d = unit(d)
    for c in d:
        if abs(c) > 1e-9:
            if c < 0:
                d = mul(d, -1)
            break
    perp = sub(pos, mul(d, dot(pos, d)))
    return tuple(round(c, 3) for c in d) + tuple(round(c, 2) for c in perp)


# ------------------------------------------------------------
# Caixa orientada (OBB) e teste de eixo separador
# ------------------------------------------------------------
class Box:
    """Caixa orientada: centro, 3 eixos unitários, meias-medidas."""

    def __init__(self, center, axes, half, owner: str, kind: str):
        self.c, self.ax, self.h = tuple(center), [tuple(a) for a in axes], tuple(half)
        self.owner, self.kind = owner, kind

    @classmethod
    def aabb(cls, lo, hi, owner, kind):
        c = tuple((lo[i] + hi[i]) / 2 for i in range(3))
        h = tuple((hi[i] - lo[i]) / 2 for i in range(3))
        return cls(c, [(1, 0, 0), (0, 1, 0), (0, 0, 1)], h, owner, kind)

    def radius_on(self, axis) -> float:
        return sum(self.h[i] * abs(dot(self.ax[i], axis)) for i in range(3))


def overlap_depth(A: Box, B: Box) -> float:
    """
    Menor penetração entre duas caixas orientadas (SAT, 15 eixos).
    ≤ 0 = separadas ou só encostadas.
    """
    axes = list(A.ax) + list(B.ax)
    for a in A.ax:
        for b in B.ax:
            c = cross(a, b)
            if norm(c) > 1e-6:
                axes.append(unit(c))
    t = sub(B.c, A.c)
    best = float("inf")
    for ax in axes:
        d = A.radius_on(ax) + B.radius_on(ax) - abs(dot(t, ax))
        if d < best:
            best = d
        if best <= 0:
            return best
    return best


def is_ortho(d) -> Optional[int]:
    u = unit(d)
    for i in range(3):
        if abs(abs(u[i]) - 1) < 1e-9:
            return i
    return None


def pyth_len(d: Sequence[int]) -> Optional[int]:
    """Comprimento inteiro do vetor inteiro `d`, ou None."""
    L = math.sqrt(sum(c * c for c in d))
    return int(round(L)) if abs(L - round(L)) < 1e-9 else None


# ------------------------------------------------------------
# Rotações do cubo — para canonizar peças repetidas
# ------------------------------------------------------------
def _det(m) -> int:
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _rotations():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = [[0] * 3 for _ in range(3)]
            for i in range(3):
                m[i][perm[i]] = signs[i]
            if _det(m) == 1:
                out.append(tuple(tuple(r) for r in m))
    return out


ROTATIONS = _rotations()
IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def frame_z_to(axis: int, sign: int):
    """Rotação que leva +Z da peça para sign·e_axis, mexendo o mínimo nos outros eixos."""
    want = [sign if i == axis else 0 for i in range(3)]
    cands = [r for r in ROTATIONS if [r[i][2] for i in range(3)] == want]
    cands.sort(key=lambda r: -sum(r[i][i] for i in range(3)))
    return cands[0]


def box_corners(bx: "Box"):
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                off = (sx * bx.h[0], sy * bx.h[1], sz * bx.h[2])
                yield tuple(bx.c[i] + sum(bx.ax[j][i] * off[j] for j in range(3)) for i in range(3))
