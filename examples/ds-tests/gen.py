#!/usr/bin/env python3
"""
Bateria de testes geométricos do design system — VIGAS.

Não são produtos: são corpos de prova. Cada um isola uma pergunta
sobre as vigas e responde com uma montagem que o compilador valida
e o CGAL confere.

  t1-cubo-vigas      cubo só de vigas retas (caixa), cavilhas nos cantos
  t2-cubo-liftarm    o mesmo cubo com vigas de ponta redonda e machos
                     integrais — sem cavilha solta
  t3-cubo-curvas     cubo de cantos arredondados: anéis de BEND + vigas
  t4-portico         pórticos curvos (poste → curva → travessa → curva
                     → poste) sobre o anel, unidos por cumeeiras
  t5-inclinadas      dobras e inclinações: rampas 3-4-5 e 5-12-13,
                     diagonal no plano 6-8-10, diagonal 3D 2-3-6 e
                     um "S" de vigas com duas curvas

    python3 examples/ds-tests/gen.py
    for t in t1 t2 t3 t4 t5; do make assemble NAME=ds-tests/$t...; done

Eixos: x, y no chão, z para cima. 1 célula = 8 mm.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "impl", "python"))

from fusionbrick.irgen import BK, BL, GR, OR, WH  # noqa: E402
from fusionbrick.irgen import Build as _Build  # noqa: E402


class Build(_Build):
    def write(self):
        return super().write(os.path.join(HERE, self.name))


# ============================================================
# T1 / T2 — cubo só de vigas
# ============================================================
def cube(name, N):
    """
    Esqueleto de cubo N×N×N, vigas retas de topo. As vigas X de baixo
    e de cima são donas dos cantos; as vigas Y entram entre elas; os
    postes Z ficam entre os dois anéis. 12 arestas, 12 vigas.
    """
    b = Build(name, f"Corpo de prova: cubo {N}×{N}×{N} células só de vigas retas, de topo, "
              "unidas por cavilhas", view_angle=35)
    for zi, z in (("inf", 0), ("sup", N - 1)):
        g = f"anel-{zi}"
        b.brick(g, f"x0-{zi}", (0, 0, z), (N, 1, 1), BK)
        b.brick(g, f"x1-{zi}", (0, N - 1, z), (N, 1, 1), BK)
        b.brick(g, f"y0-{zi}", (0, 1, z), (1, N - 2, 1), OR)
        b.brick(g, f"y1-{zi}", (N - 1, 1, z), (1, N - 2, 1), OR)
        if zi == "inf":
            for i, (x, y) in enumerate([(0, 0), (N - 1, 0), (0, N - 1), (N - 1, N - 1)]):
                b.brick("postes", f"poste{i}", (x, y, 1), (1, 1, N - 2), GR)
    b.notes = {"anel-inf": "4 vigas no chão", "postes": "4 postes nos cantos",
               "anel-sup": "4 vigas no topo fecham o cubo"}
    b.write()


def cube_lift(name, N):
    """
    Cubo à moda Technic: vigas de ponta redonda (furos em Z) em
    camadas alternadas X / Y, cruzando-se nos cantos — as arestas
    verticais nascem da sobreposição, e cada canto leva uma cavilha
    em Z por camada. Nenhuma viga encosta de topo.
    """
    b = Build(name, f"Corpo de prova: cubo {N}×{N}×{N} de vigas de ponta redonda empilhadas em camadas "
              "alternadas X/Y, cavilhas verticais nos cantos", view_angle=35)
    for z in range(N):
        g = "camadas-x" if z % 2 == 0 else "camadas-y"
        if z % 2 == 0:
            b.brick(g, f"x0-{z}", (0, 0, z), (N, 1, 1), BK, rounded="z", corner_r=4.0)
            b.brick(g, f"x1-{z}", (0, N - 1, z), (N, 1, 1), BK, rounded="z", corner_r=4.0)
        else:
            b.brick(g, f"y0-{z}", (0, 0, z), (1, N, 1), OR, rounded="z", corner_r=4.0)
            b.brick(g, f"y1-{z}", (N - 1, 0, z), (1, N, 1), OR, rounded="z", corner_r=4.0)
    b.notes = {"camadas-x": "camadas pares: vigas em X", "camadas-y": "camadas ímpares: vigas em Y"}
    b.write()


# ============================================================
# T3 — cubo de cantos arredondados (anéis de curvas)
# ============================================================
def ring(b, g, z, N, color_beam, color_bend, tag):
    """Anel quadrado N×N no plano z: 4 vigas retas + 4 BENDs k=1."""
    L = N - 4
    b.brick(g, f"vb-{tag}", (2, 0, z), (L, 1, 1), color_beam)
    b.brick(g, f"vd-{tag}", (N - 1, 2, z), (1, L, 1), color_beam)
    b.brick(g, f"vt-{tag}", (2, N - 1, z), (L, 1, 1), color_beam)
    b.brick(g, f"ve-{tag}", (0, 2, z), (1, L, 1), color_beam)
    b.curve(g, f"cBD-{tag}", (N - 2, 0, z), (1, 0, 0), (0, 1, 0), color=color_bend)
    b.curve(g, f"cTD-{tag}", (N - 1, N - 2, z), (0, 1, 0), (-1, 0, 0), color=color_bend)
    b.curve(g, f"cTE-{tag}", (1, N - 1, z), (-1, 0, 0), (0, -1, 0), color=color_bend)
    b.curve(g, f"cBE-{tag}", (0, 1, z), (0, -1, 0), (1, 0, 0), color=color_bend)


def cube_curvas(N=10):
    b = Build("t3-cubo-curvas", f"Corpo de prova: cubo {N}×{N}×{N} de cantos arredondados — dois anéis "
              "de vigas + BEND 90° (R = 1,5 célula) e 8 postes", view_angle=35)
    ring(b, "anel-inf", 0, N, BK, OR, "i")
    L = N - 4
    posts = [(2, 0), (N - 3, 0), (N - 1, 2), (N - 1, N - 3), (N - 3, N - 1), (2, N - 1), (0, N - 3), (0, 2)]
    for i, (x, y) in enumerate(posts):
        b.brick("postes", f"poste{i}", (x, y, 1), (1, 1, N - 2), GR)
    ring(b, "anel-sup", N - 1, N, BK, OR, "s")
    b.notes = {"anel-inf": "anel de baixo: 4 vigas + 4 curvas", "postes": "8 postes nas pontas das vigas",
               "anel-sup": "anel de cima fecha o cubo"}
    b.write()


# ============================================================
# T4 — pórticos curvos
# ============================================================
def portico(N=10, H=6):
    b = Build("t4-portico", "Corpo de prova: anel de base com curvas + dois pórticos curvos "
              "(poste, curva, travessa, curva, poste) unidos por cumeeiras", view_angle=35)
    ring(b, "base", 0, N, BK, OR, "b")
    for tag, y in (("f", 0), ("t", N - 1)):
        g = f"portico-{tag}"
        # postes nas células x=2 e x=N-3 da viga de base
        b.brick(g, f"pe-{tag}", (2, y, 1), (1, 1, H - 1), GR)
        b.brick(g, f"pd-{tag}", (N - 3, y, 1), (1, 1, H - 1), GR)
        # curva esquerda: sobe (+Z) e vira para +X
        b.curve(g, f"ce-{tag}", (2, y, H), (0, 0, 1), (1, 0, 0), color=OR)
        # travessa entre as curvas
        b.brick(g, f"tr-{tag}", (4, y, H + 1), (N - 8, 1, 1), BK)
        # curva direita: segue +X e desce (−Z)
        b.curve(g, f"cd-{tag}", (N - 4, y, H + 1), (1, 0, 0), (0, 0, -1), color=OR)
    for i, x in enumerate(range(4, N - 4)):
        b.brick("cumeeira", f"cum{i}", (x, 1, H + 1), (1, N - 2, 1), WH)
    b.notes = {"base": "anel de base", "portico-f": "pórtico da frente",
               "portico-t": "pórtico de trás", "cumeeira": "vigas Y ligam as duas travessas"}
    b.write()


# ============================================================
# T5 — dobras e inclinações
# ============================================================
def inclinadas():
    b = Build("t5-inclinadas", "Corpo de prova: vigas inclinadas por ternos pitagóricos (3-4-5, "
              "5-12-13, 6-8-10 no plano, 2-3-6 em 3D) e vigas dobradas por BEND (S e grampo 180°)",
              view_angle=215)
    # Chassi de prova: duas longarinas X e quatro travessas Y
    b.brick("base", "long0", (0, 0, 0), (24, 1, 1), BK)
    b.brick("base", "long1", (0, 10, 0), (24, 1, 1), BK)
    for i, x in enumerate((0, 8, 16, 23)):
        b.brick("base", f"trav{i}", (x, 1, 0), (1, 9, 1), GR)

    # (a) Rampa 4-3 (~37°) sobre long0. O braço do NÓ precisa estar a
    # ≥127° da viga, então as pontas apoiam DE LADO (±X), não por baixo.
    b.brick("rampa", "r-pe", (1, 0, 1), (1, 1, 1), GR)
    b.node("rampa", "r0", (2, 0, 1), [(-1, 0, 0), (4, 0, 3)])
    b.node("rampa", "r1", (6, 0, 4), [(-4, 0, -3), (1, 0, 0)])
    b.strut_between("rampa", "r-diag", "r0", "r1", color=OR, style="beam")
    b.brick("rampa", "r-poste", (7, 0, 1), (1, 1, 4), GR)

    # (b) Rampa suave 12-5 (~23°) sobre long1
    b.brick("suave", "s-pe", (1, 10, 1), (1, 1, 1), GR)
    b.node("suave", "s0", (2, 10, 1), [(-1, 0, 0), (12, 0, 5)])
    b.node("suave", "s1", (14, 10, 6), [(-12, 0, -5), (1, 0, 0)])
    b.strut_between("suave", "s-diag", "s0", "s1", color=BL, style="beam")
    b.brick("suave", "s-poste", (15, 10, 1), (1, 1, 6), GR)

    # (c) Diagonal NO PLANO 6-8: contraventa o chassi, braços nas laterais
    b.node("plano", "p0", (9, 1, 0), [(0, -1, 0), (6, 8, 0)])
    b.node("plano", "p1", (15, 9, 0), [(-6, -8, 0), (0, 1, 0)])
    b.strut_between("plano", "p-diag", "p0", "p1", color=WH, style="beam")

    # (d) Diagonal 3D 2-3-6 (comprimento 7): nó de baixo apoia por baixo,
    # nó de cima pendura numa viga-teto
    b.brick("3d", "d-apoio0", (17, 2, 0), (6, 1, 1), BK)
    b.brick("3d", "d-apoio1", (17, 8, 0), (6, 1, 1), BK)
    b.node("3d", "d0", (17, 2, 1), [(0, 0, -1), (2, 3, 6)])
    b.node("3d", "d1", (19, 5, 7), [(-2, -3, -6), (0, 0, 1)])
    b.strut_between("3d", "d-diag", "d0", "d1", color=OR, style="beam")
    b.brick("3d", "d-teto", (19, 5, 8), (1, 4, 1), BK)
    b.brick("3d", "d-poste", (19, 8, 1), (1, 1, 7), GR)

    # (e) Viga dobrada em "S" com dois curvas, em pé no plano XZ
    b.brick("dobra", "S-poste", (9, 0, 1), (1, 1, 2), GR)
    b.curve("dobra", "S-c1", (9, 0, 3), (0, 0, 1), (1, 0, 0), color=OR)
    b.brick("dobra", "S-meio", (11, 0, 4), (2, 1, 1), BK)
    b.curve("dobra", "S-c2", (13, 0, 4), (1, 0, 0), (0, 0, 1), color=OR)
    b.brick("dobra", "S-topo", (14, 0, 6), (1, 1, 1), GR)
    b.brick("dobra", "S-alto", (14, 0, 7), (6, 1, 1), BK)
    b.brick("dobra", "S-poste2", (19, 0, 1), (1, 1, 6), GR)

    # (f) Grampo (U de 180°) deitado, preso na travessa
    b.brick("grampo", "U-a", (16, 4, 1), (5, 1, 1), BK)
    b.curve("grampo", "U-c", (21, 4, 1), (1, 0, 0), (0, 1, 0), radius=2, angle=180, color=OR)
    b.brick("grampo", "U-b", (16, 7, 1), (5, 1, 1), BK)

    b.notes = {"base": "chassi de prova", "rampa": "3-4-5", "suave": "5-12-13", "plano": "6-8-10 no chão",
               "3d": "2-3-6 nos dois planos", "dobra": "S com duas curvas", "grampo": "retorno 180°"}
    b.write()


if __name__ == "__main__":
    cube("t1-cubo-vigas", 8)
    cube_lift("t2-cubo-liftarm", 8)
    cube_curvas()
    portico()
    inclinadas()
