#!/usr/bin/env python3
"""
Gera examples/rover-x6/assembly.toml — Rover X6.

Rover de exploração de 6 rodas, sucessor do buggy-vt3. Pedido:
carroceria mais aberta, com mais vigas e curvas, base de blocos
maiores, "menos quadradão", sem teto, mastro com cabeça.

  · base: 3 blocos 12×12×2 entre duas laterais de liftarm — machos
    integrais nos lados (sem cavilha) e entre os blocos;
  · deck branco de 2 placas sobre a base;
  · quadro inferior de cantos curvos (BEND) no perímetro do deck;
  · quadro superior MAIS ESTREITO e mais curto, sobre 4 postes —
    a silhueta afunila, como um rover, em vez de caixa;
  · mastro redondo 2×2 com cabeça de câmeras; braço robótico na
    frente (diagonal 4-3); antena de alto ganho atrás;
  · bicos arredondados na frente e atrás, 6 rodas off-road Ø80.

    python3 examples/rover-x6/gen.py && make assemble NAME=rover-x6
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "impl", "python"))
from fusionbrick.irgen import LIFT_X, OR, WH, Build  # noqa: E402

GF = [0.20, 0.21, 0.23]       # grafite
W = 14                        # largura (y 0..13)
L = 36                        # comprimento do casco (x 0..35)
AXLES = (4, 18, 32)           # rodas Ø88 nas pontas do corpo, a cada 14 células
YS = -3                       # plano da suspensão: 2 células para fora do corpo (bitola larga)
AZ = 2                        # nível do eixo
BZ = 8                        # o corpo fica ERGUIDO sobre as pernas
DECK = BZ + 2                 # nível do deck
RING = BZ + 3                 # quadro inferior
UP = BZ + 7                   # quadro superior

b = Build("rover-x6", "Rover de exploração 6×6: base de blocos grandes, carroceria aberta de vigas e curvas "
          "que afunila para cima, mastro com cabeça de câmeras, braço robótico, antena, rodas off-road; "
          "grafite, branco e laranja", view_angle=145, dowel_every=5)
b.header = """ROVER X6 — vista lateral (X-Z), x = TRÁS → FRENTE

z=21..22                      ▐cabeça▌ ◉◉ câmeras, LiDAR
z=15..18     ╭arco╮            ┃     ┃            ╭arco╮
z=15       ╭─────── quadro superior (y 2..11) ───────╮           ● mão
z=11..14   ┃poste           mastro              poste┃        ╱ braço 4-3
z=11     ╭──────────── quadro inferior (perímetro) ──────────────●╮
z=10     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ deck branco (4 placas) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
z=8..9 ╭ ███ bloco ███ ███ bloco ███ ███ bloco ███ ╮  (laterais de liftarm nos lados)
z=3..8          ●╲_____ perna 5-12-13       ┃coluna      perna ____╱●
z=2      [cubo]═══════ bogie ════════════════┃════════ bogie ═══[cubo]
        ( roda )                          ( roda )                ( roda )
x:    -2    4                                18                      32  35  40
"""

# ============================================================
# BASE — laterais de viga + 3 blocos grandes
# ============================================================
# Ordem de montagem (ASM-012): lateral esquerda montada à parte →
# blocos entram em +y... na lateral → lateral direita entra por cima
# dos pinos dos blocos. As emendas das laterais e os lados x dos
# blocos ficam SEM encaixe: cada peça entra com um movimento só.
for z, cut in ((0, 12), (1, 24)):
    for k, (x0, x1) in enumerate(((0, cut), (cut, L))):
        faces = {"top": "stud"} if z == 0 else {}
        faces["front" if k == 0 else "back"] = "flat"
        kw = dict(studs_on="inner") if z == 0 else {}
        b.brick("lateral_e", f"lat{z}{'ab'[k]}_e", (x0, 0, BZ + z), (x1 - x0, 1, 1), GF, **LIFT_X,
                faces=faces, **kw)
b.sub("lateral_e", "Lateral esquerda: 2 camadas de liftarm, machos da de baixo na de cima.")

# Blocos: 12×12×2, pinos nos dois lados (entram nas laterais). Os lados
# x ficam lisos: os blocos se amarram pelas laterais e pelo deck.
for k, x in enumerate((0, 12, 24)):
    b.brick("blocos", f"bloco{k}", (x, 1, BZ), (12, W - 2, 2), GF, holes="xz",
            faces={"right": "stud", "left": "stud", "back": "flat", "front": "flat"})

# Bicos arredondados: cada bico (curva + travessa + curva) é montado à
# parte e entra de frente nas pontas das laterais.
b.curve("bico_f", "bico_f_e", (L, 0, BZ), (1, 0, 0), (0, 1, 0), color=OR)
b.brick("bico_f", "bico_f", (L + 1, 2, BZ), (1, W - 4, 1), GF, holes="xyz", rounded="x")
b.brick("bico_t", "bico_t", (-2, 2, BZ), (1, W - 4, 1), GF, holes="xyz", rounded="x")
b.curve("bico_t", "bico_t_e", (-2, 1, BZ), (0, -1, 0), (1, 0, 0), color=OR)

# ============================================================
# SUSPENSÃO ROCKER-BOGIE (visual) — 3 pernas por lado
# ============================================================
# Roda do meio: coluna vertical do eixo (z=AZ) até o corpo (z=BZ),
# encostada na lateral do corpo. Bogies: vigas no nível do eixo, da
# coluna até um cubo de 2 células onde a roda da ponta encaixa.
# Pernas: diagonais 5-12-13 (22,6°) que saem DE LADO da coluna e
# chegam DE LADO no cubo (braços ±X, a 157° da diagonal — lei 6).
XM = AXLES[1]
# Ombro: sai da lateral do corpo até o plano da suspensão (bitola +32 mm)
b.brick("ombro_e", "ombro_e", (XM, YS + 1, BZ), (1, -YS - 1, 2), GF, holes="xyz")
b.brick("susp_e", "coluna_e", (XM, YS, AZ), (1, 1, BZ - AZ + 1), GF, holes="xyz", rounded="y")
for tag, xw, sgn in (("t", AXLES[0], -1), ("f", AXLES[2], 1)):
    x0, x1 = sorted((XM + sgn, xw - sgn))
    b.brick("susp_e", f"bogie_{tag}_e", (x0, YS, AZ), (x1 - x0 + 1, 1, 1), GF, **LIFT_X)
    b.brick("susp_e", f"cubo_{tag}_e", (xw, YS, AZ), (1, 1, 2), GF, holes="xyz")
    b.strut("susp_e", f"perna_{tag}_e", (XM + sgn, YS, BZ), (xw - sgn, YS, AZ + 1),
            from_arm=[-sgn, 0, 0], to_arm=[sgn, 0, 0], color=OR)
b.sub("susp_e", "Suspensão esquerda montada à parte (coluna, bogies, cubos, pernas); entra no ombro.")

# ============================================================
# RODAS — 3 por lado, off-road Ø88, raios em Y; motores N20 (componentes)
# ============================================================
for tag, ax in zip("tmf", AXLES):
    host = "coluna_e" if tag == "m" else f"cubo_{tag}_e"
    b.wheel("rodas", f"roda_{tag}_e", (ax, YS - 1, AZ), f"{host}.right", diameter=11, width=4,
            tread="offroad", spokes=6, spoke_style="y", color=[0.10, 0.10, 0.11])

# lado direito: laterais, bicos, ombro, suspensão e rodas espelhados
b.mirror_y(W)
# o espelho entra no mesmo grupo; separa por lado (subconjuntos distintos)
for g in ("lateral_e", "ombro_e", "susp_e"):
    gd = g[:-2] + "_d"
    b.groups[gd] = [i for i in b.groups[g] if i.endswith("_d") or "_d-" in i]
    b.groups[g] = [i for i in b.groups[g] if i not in b.groups[gd]]
    if g in getattr(b, "subs", set()):
        b.sub(gd, b.notes.get(g, "").replace("esquerda", "direita"))
for g in ("bico_f", "bico_t"):
    b.sub(g, "Bico montado à parte (curva + travessa + curva); entra nas pontas das laterais.")

# ============================================================
# DECK — 4 placas brancas, cantos redondos, pinos em toda a base
# ============================================================
for k, x in enumerate((0, 9, 18, 27)):          # 4 placas iguais: 1 STL, render rápido
    b.brick("deck", f"deck{k}", (x, 0, DECK), (9, W, 1), WH, holes="z", rounded="z", corner_r=4.0,
            faces={"bottom": "stud"})

# ============================================================
# CARROCERIA — quadro inferior no perímetro, quadro superior
# estreito sobre postes (afunila), tudo aberto
# ============================================================
# quadro inferior: pinos para baixo nas células planas (encaixe integral no deck)
b.ring("q_inf", "q_inf", 0, 0, RING, L, W, beam_color=GF, curve_color=OR, holes="xyz", rounded="y",
       faces={"bottom": "stud"}, studs_on="inner", split="flat")
# ordem de fechamento: começa depois de cada emenda lisa (ASM-012)
b.groups["q_inf"] = ["q_inf-s1", "q_inf-cSE", "q_inf-l", "q_inf-cNE", "q_inf-n1",
                     "q_inf-n0", "q_inf-cNO", "q_inf-o", "q_inf-cSO", "q_inf-s0"]
b.sub("q_inf", "Quadro inferior montado à parte; desce sobre o deck (machos para baixo).")
UX0, UNX = 6, 22                 # quadro superior: x 6..27
UY0, UNY = 2, W - 4              # y 2..11 — 2 células para dentro de cada lado
for x in (UX0 + 2, 13, 22, UX0 + UNX - 3):
    for y in (UY0, UY0 + UNY - 1):
        b.brick("postes", f"poste_x{x}_y{y}", (x, y, RING), (1, 1, UP - RING), WH,
                holes="xyz", rounded="y")
# vigas longas em 2 metades com emenda lisa: cada metade apoia em 2
# postes, e o anel fecha sem exigir um segundo movimento (ASM-012)
b.ring("q_sup", "q_sup", UX0, UY0, UP, UNX, UNY, beam_color=GF, curve_color=OR, holes="xyz", rounded="y",
       max_cells=9, split="flat")
b.groups["q_sup"] = ["q_sup-s1", "q_sup-cSE", "q_sup-l", "q_sup-cNE", "q_sup-n1",
                     "q_sup-n0", "q_sup-cNO", "q_sup-o", "q_sup-cSO", "q_sup-s0"]
b.sub("q_sup", "Quadro superior montado à parte; desce sobre os postes.")

# Dois arcos abertos sobre a eletrônica, apoiados no quadro superior
# (longe do mastro em x=17..18 e da cabeça)
for k, x in enumerate((10, 24)):
    b.arch(f"arco{k}", f"arco{k}", x, UY0, UY0 + UNY - 1, UP + 1, UP + 4, color=GF, curve_color=OR,
           holes="xyz", rounded="y")
    b.sub(f"arco{k}", "Arco montado à parte; desce sobre o quadro superior.")

# ============================================================
# MASTRO E CABEÇA
# ============================================================
# Pé 4×4: espalha a base do mastro (juntas a 34 mm, não a 11 mm). Os
# pinos de cima só saem nas 4 células planas do meio — sob o mastro.
b.brick("mastro", "pe_mastro", (16, 5, RING), (4, 4, 1), GF, holes="z", rounded="z", corner_r=4.0,
        faces={"top": "stud"}, studs_on="inner")
b.brick("mastro", "mastro", (17, 6, RING + 1), (2, 2, 10), WH, holes="z", rounded="z", corner_r=4.0)
# Cabeça maior e no acento: lê como rosto (dois olhos grandes)
b.brick("mastro", "cabeca", (16, 3, RING + 11), (3, 8, 2), OR, holes="xyz", rounded="x", corner_r=4.0)

# ============================================================
# BRAÇO ROBÓTICO — base sobre o quadro da frente, diagonal 4-3
# ============================================================
b.brick("braco", "braco_base", (L - 2, 6, RING + 1), (2, 2, 1), GF, holes="xz")
b.strut("braco", "braco", (L, 6, RING + 1), (L + 4, 6, RING + 4), from_arm=[-1, 0, 0],
        to_arm=[1, 0, 0], color=OR)
b.brick("braco", "punho", (L + 5, 6, RING + 4), (1, 1, 1), GF, holes="xyz")
b.hinges.append("punho")

# ============================================================
# BERÇO DA BATERIA — embaixo do corpo (centro de massa 7 células abaixo)
# ============================================================
# 4 pendurais nos blocos e uma bandeja; tudo entra de baixo para cima.
# A bateria sai deslizando para a frente, entre os pendurais.
for x in (13, 23):
    for y in (3, W - 4):
        b.brick("berco", f"pendural_x{x}_y{y}", (x, y, 4), (1, 1, BZ - 4), GF, holes="xyz", rounded="y")
b.brick("berco", "bandeja", (13, 3, 3), (11, W - 6, 1), WH, holes="z", rounded="z", corner_r=4.0)

# Base do Pi: laje adaptadora (a furação do Pi não cai no grid — DOCK
# fica para depois)
b.brick("eletronica", "base_pi", (5, 3, RING), (10, 7, 1), GF, thickness=4.0, holes="z", rounded="z",
        corner_r=4.0, faces={"bottom": "stud"})

# ============================================================
# ANTENA — haste 2×1 atrás do quadro superior
# ============================================================
b.brick("antena", "antena_haste", (2, 9, RING), (2, 1, 5), WH, holes="xz", rounded="y")

# ============================================================
# MOCKS — eletrônica e sensores
# ============================================================
G = 8.0
b.component("mocks", "pi4", (5.35, 3.2, RING + 0.5), (85.0, 56.0, 17.0), "Raspberry Pi 4", [0.10, 0.45, 0.25, 0.95], mass=46)
b.component("mocks", "bateria", (14.2, 4.2, 4.0), (67.0, 42.0, 28.0), "bateria 2S", [0.15, 0.15, 0.17, 0.95], mass=110)
b.component("mocks", "bat_tampa", (14.2 + 67 / G, 4.2, 4.0), (10.0, 42.0, 28.0), "bateria (terminal)",
       [0.90, 0.45, 0.10, 0.95], mass=10)
b.component("mocks", "lente_e", (19.0, 4.125, RING + 11.125), (14.0, 14.0, 6.0), "câmera estéreo E",
       [0.02, 0.02, 0.03, 1.0], shape="cyl", axis="x", mass=8)
b.component("mocks", "lente_d", (19.0, 8.125, RING + 11.125), (14.0, 14.0, 6.0), "câmera estéreo D",
       [0.02, 0.02, 0.03, 1.0], shape="cyl", axis="x", mass=8)
# LiDAR no nariz do deck: no alto do mastro ele virava uma cartola
# preta escondendo a cabeça (Designer) e subia o centro de massa
b.component("mocks", "lidar", (28.6, 4.59, RING), (38.6, 38.6, 33.5), "LiDAR LD06", [0.08, 0.08, 0.09, 1.0],
       shape="cyl", axis="z", mass=42)
b.component("mocks", "prato", (1.37, 6.5, RING + 1.5), (48.0, 48.0, 5.0), "antena de alto ganho",
       [0.92, 0.92, 0.90, 1.0], shape="cyl", axis="x", mass=25)
for k, y in enumerate((3.5, 9.0)):
    b.component("mocks", f"hazcam{k}", (L + 2, y, BZ + 0.25), (6.0, 6.0, 5.0), "hazcam", [0.02, 0.02, 0.03, 1.0],
           shape="cyl", axis="x", mass=4)
b.component("mocks", "garra", (L + 6, 6.1, RING + 4.1), (10.0, 6.0, 6.0), "garra", [0.75, 0.75, 0.78, 1.0], mass=15)
for k, (col, dy) in enumerate(zip(([0.85, 0.12, 0.10, 1.0], [0.12, 0.35, 0.85, 1.0]), (0.0, 0.3))):
    b.component("mocks", f"fio{k}", (0, 0, 0), (2.2, 2.2, 2.2), "fio", col, shape="cable",
           points=[[18.4 + dy, 6.6, RING + 11.0], [18.4 + dy, 8.2, RING + 10.0], [18.4 + dy, 8.2, RING + 2.4],
                   [17.0, 9.2 + dy, RING + 1.4], [13.0, 9.2 + dy, RING + 2.6]])
# motores N20 (12 × 10 × 34 mm, eixo em Y) por dentro de cada roda
for tag, ax in zip("tmf", AXLES):
    b.component("mocks", f"motor_{tag}_e", (ax + 0.25, YS + 1, AZ + 0.2), (12.0, 34.0, 10.0), "motor N20",
           [0.75, 0.75, 0.78, 1.0], mass=12)
    b.component("mocks", f"motor_{tag}_d", (ax + 0.25, W - YS - 1 - 34 / G, AZ + 0.2), (12.0, 34.0, 10.0),
           "motor N20", [0.75, 0.75, 0.78, 1.0], mass=12)
    for side, y_out, y_in in (("e", YS + 1 + 34 / G, -0.4), ("d", W - YS - 1 - 34 / G, W + 0.4)):
        b.component("mocks", f"fio_motor_{tag}_{side}", (0, 0, 0), (2.0, 2.0, 2.0), "fio", [0.85, 0.12, 0.10, 1.0],
               shape="cable", points=[[ax + 1.0, y_out, AZ + 0.8], [ax + 1.0, y_in, AZ + 0.8],
                                      [ax + 1.0, y_in, DECK + 1.2],
                                      [ax + 1.0, 1.3 if side == "e" else W - 1.3, RING + 0.3],
                                      [22.5, 1.3 if side == "e" else W - 1.3, RING + 0.3],
                                      [23.5, 5.0 if side == "e" else 8.2, RING + 0.6]])
# driver dos 6 motores (2 × TB6612 numa placa) no deck, no lugar da bateria
b.component("mocks", "driver", (21.6, 4.6, RING), (40.0, 30.0, 12.0), "driver de motor", [0.12, 0.30, 0.60, 0.95],
       mass=20)
b.component("mocks", "fio_bat", (0, 0, 0), (2.4, 2.4, 2.4), "fio", [0.10, 0.10, 0.10, 1.0], shape="cable",
       points=[[24.0, 6.0, 5.6], [24.6, 6.0, 7.6], [24.6, 6.0, DECK + 1.2], [24.0, 6.0, RING + 0.6]])
for k, y in enumerate((5.5, 7.5)):
    b.component("mocks", f"farol{k}", (L + 2, y, BZ + 0.3), (6.0, 6.0, 3.0), "farol", [1.0, 0.95, 0.75, 1.0],
           shape="cyl", axis="x", mass=2)
b.component("mocks", "letreiro", (24.0, 1.0, RING + 0.4), (9.0, 0.0, 0.6), "letreiro X6",
       [0.95, 0.47, 0.10, 1.0], shape="text", text="X6", axis="0")

b.notes.update({
    "suspensao": "Coluna do meio, bogies no nível do eixo, cubos das rodas da ponta e pernas 5-12-13, dos dois lados.",
    "rodas": "6 rodas off-road: a do meio na coluna, as outras nos cubos das pernas.",
    "deck": "4 placas brancas iguais; machos em toda a base.",
    "mastro": "Mastro redondo 2×2 no centro do deck; cabeça de câmeras por cima.",
    "braco": "Base sobre o quadro da frente, diagonal 4-3, punho giratório.",
    "antena": "Haste traseira da antena de alto ganho.",
    "mocks": "Pi, bateria, motores, driver, câmeras, LiDAR, antena, hazcams, faróis, garra, fios — não imprimem.",
    "blocos": "Blocos entram na lateral esquerda (machos dos lados).",
    "deck": "4 placas brancas iguais; machos em toda a base.",
    "postes": "8 postes sobre o deck.",
    "berco": "De baixo para cima: pendurais nos blocos, bandeja nos pendurais.",
    "eletronica": "Laje adaptadora do Pi sobre o deck.",
    "rodas": "6 rodas off-road Ø88: a do meio na coluna, as outras nos cubos.",
    "ombro_e": "Ombro esquerdo: sai da lateral até o plano da suspensão.",
    "ombro_d": "Ombro direito.",
})
# ordem de montagem
ORDER = ["lateral_e", "blocos", "lateral_d", "bico_f", "bico_t", "deck", "berco", "ombro_e", "ombro_d",
         "susp_e", "susp_d", "rodas", "q_inf", "postes", "q_sup", "arco0", "arco1", "mastro", "eletronica",
         "braco", "antena", "mocks"]
assert set(ORDER) == set(b.groups), set(b.groups) ^ set(ORDER)
b.groups = {g: b.groups[g] for g in ORDER}
b.write(__file__)
