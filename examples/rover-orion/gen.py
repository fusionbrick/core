#!/usr/bin/env python3
"""
Gera examples/rover-orion/assembly.toml — Rover Orion.

UMA IDEIA: um rover de exploração de seis rodas cuja cabine aberta sobe
numa linha só, do nariz ao mastro — o perfil é a assinatura.

Feito com o sistema simplificado: variantes (`liftarm`, `plate`),
`studs` em vez de cavilha, e macros de `irgen`.

  base        2 blocos 16×12×2 entre laterais de liftarm (machos integrais)
  suspensão   rocker-bogie visual: ombro, coluna, bogies, pernas 5-12-13
  cabine      aro no perímetro do deck + 3 arcos: baixo no nariz, altos
              atrás; duas longarinas 5-12-13 descem do arco alto ao do nariz
  teto        dois trilhos sobre os arcos altos (bagageiro); o LiDAR fica no nariz
  mastro      pé 4×4, mastro redondo, cabeça de câmeras (o rosto)

    python3 examples/rover-orion/gen.py && make assemble NAME=rover-orion
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "impl", "python"))
from fusionbrick.irgen import OR, WH, Build  # noqa: E402

GF = [0.20, 0.21, 0.23]       # grafite: estrutura
TIRE = [0.10, 0.10, 0.11]
W, L = 14, 32                 # corpo: y 0..13, x 0..31
YS = -3                       # plano da suspensão (2 células fora do corpo)
AXLES = (2, 16, 30)
AZ, BZ = 2, 8                 # eixo das rodas · base do corpo
DECK, RING = BZ + 2, BZ + 3
X_REAR, X_PEAK, X_NOSE = 3, 11, 25     # os três arcos
TOP_HIGH, TOP_NOSE = RING + 8, RING + 3

b = Build("rover-orion", "Rover de exploração 6×6: cabine aberta que sobe numa linha só do nariz ao mastro, "
          "suspensão rocker-bogie, mastro com cabeça de câmeras, braço de coleta e LiDAR no nariz",
          view_angle=145, dowel_every=5)
b.header = """ROVER ORION — vista lateral (X-Z), x = TRÁS → FRENTE

z=22..23                         ▐cabeça▌ ◉◉
z=20       ═══════ trilhos            ┃
z=19     ╭─arco─────────arco─╮●       ┃ mastro
z=14..18 ┃                   ┃  ╲ longarina 5-12-13
z=12..13 ┃                   ┃     ╲___●╭─arco─╮          ● garra
z=11   ╭────────────── aro no perímetro do deck ─────────●╱ braço 4-3
z=10   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ deck branco (4 placas) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓
z=8..9 ╭ ██████ bloco ██████ ██████ bloco ██████ ╮
z=3..8        ●╲____ perna        ┃coluna       perna ____╱●
z=2    [cubo]═══════ bogie ═══════┃═══════ bogie ═══════[cubo]
      ( roda )                 ( roda )                 ( roda )
x:   -2   2      4            13   16            27     30 31   36
"""

# ============================================================
# BASE — laterais de viga, 2 blocos grandes, bicos curvos
# ============================================================
# Lateral esquerda montada à parte; os blocos entram nela pelos pinos
# do lado; a lateral direita entra nos pinos do outro lado.
for z, cut in ((0, 12), (1, 20)):
    for k, (x0, x1) in enumerate(((0, cut), (cut, L))):
        b.beam("lateral_e", f"lat{z}{'ab'[k]}_e", (x0, 0, BZ + z), (x1 - x0, 1, 1), GF,
                  flat=["front" if k == 0 else "back"], **({"studs": "up"} if z == 0 else {}))
b.sub("lateral_e", "Lateral esquerda: 2 camadas de liftarm, os machos da de baixo na de cima.")
for k, x in enumerate((0, 16)):
    b.brick("blocos", f"bloco{k}", (x, 1, BZ), (16, W - 2, 2), GF, holes="xz",
            studs=["right", "left"], flat=["back", "front"])

b.curve("bico_f", "bico_f_e", (L, 0, BZ), (1, 0, 0), (0, 1, 0))
b.beam("bico_f", "bico_f", (L + 1, 2, BZ), (1, W - 4, 1), GF)
b.beam("bico_t", "bico_t", (-2, 2, BZ), (1, W - 4, 1), GF)
b.curve("bico_t", "bico_t_e", (-2, 1, BZ), (0, -1, 0), (1, 0, 0))

# ============================================================
# SUSPENSÃO rocker-bogie (visual) e RODAS — lado esquerdo
# ============================================================
XM = AXLES[1]
b.brick("ombro_e", "ombro_e", (XM, YS + 1, BZ), (1, -YS - 1, 2), GF)
b.beam("susp_e", "coluna_e", (XM, YS, AZ), (1, 1, BZ - AZ + 1), GF)
for tag, xw, sgn in (("t", AXLES[0], -1), ("f", AXLES[2], 1)):
    x0, x1 = sorted((XM + sgn, xw - sgn))
    b.beam("susp_e", f"bogie_{tag}_e", (x0, YS, AZ), (x1 - x0 + 1, 1, 1), GF)
    b.brick("susp_e", f"cubo_{tag}_e", (xw, YS, AZ), (1, 1, 2), GF)
    b.strut("susp_e", f"perna_{tag}_e", (XM + sgn, YS, BZ), (xw - sgn, YS, AZ + 1),
            from_arm=[-sgn, 0, 0], to_arm=[sgn, 0, 0], color=OR)
b.sub("susp_e", "Suspensão esquerda montada à parte (coluna, bogies, cubos, pernas); entra no ombro.")
b.notes["ombro_e"] = "Ombro esquerdo: da lateral do corpo até o plano da suspensão."
for tag, ax in zip("tmf", AXLES):
    host = "coluna_e" if tag == "m" else f"cubo_{tag}_e"
    b.wheel("rodas", f"roda_{tag}_e", (ax, YS - 1, AZ), f"{host}.right", diameter=11, width=4,
            tread="offroad", spokes=6, spoke_style="y", color=TIRE)

b.mirror_y(W, split_groups=True)        # laterais, bicos, ombro, suspensão e rodas do lado direito
for g in ("bico_f", "bico_t"):
    b.sub(g, "Bico montado à parte (curva, travessa, curva); entra nas pontas das laterais.")

# ============================================================
# DECK e BERÇO DA BATERIA
# ============================================================
for k in range(4):
    # deck de 1 célula de altura (não laje): recebe pinos por cima E por baixo
    b.brick("deck", f"deck{k}", (8 * k, 0, DECK), (8, W, 1), WH, holes="z", rounded="z", corner_r=4.0,
            studs="bottom")
for x in (11, 21):
    for y in (3, W - 4):
        b.beam("berco", f"pendural_x{x}_y{y}", (x, y, 4), (1, 1, BZ - 4), GF)
b.plate("berco", "bandeja", (11, 3, 3.5), 11, W - 6, WH)

# ============================================================
# CABINE ABERTA — aro, três arcos, longarinas, trilhos
# ============================================================
b.ring("aro", "aro", 0, 0, RING, L, W, beam_color=GF, curve_color=OR, type="beam",
       studs="bottom", split="flat")
b.groups["aro"] = ["aro-s1", "aro-cSE", "aro-l", "aro-cNE", "aro-n1",
                   "aro-n0", "aro-cNO", "aro-o", "aro-cSO", "aro-s0"]     # fecha depois da emenda lisa
b.sub("aro", "Aro montado à parte; desce sobre o deck (machos para baixo).")

for name, x, top in (("arco_t", X_REAR, TOP_HIGH), ("arco_m", X_PEAK, TOP_HIGH), ("arco_f", X_NOSE, TOP_NOSE)):
    b.arch(name, name, x, 0, W - 1, RING + 1, top, color=GF, curve_color=OR, type="beam")
    b.sub(name, "Arco montado à parte; desce sobre o aro.")

# Trilhos do teto: apoiam POR CIMA nos dois arcos altos (um movimento só)
for y in (3, W - 4):
    b.beam("teto", f"trilho_y{y}", (X_REAR, y, TOP_HIGH + 1), (X_PEAK - X_REAR + 1, 1, 1), GF)

# Longarinas: do arco alto ao arco do nariz, 5-12-13 (22,6°). Os braços
# saem de lado das travessas (±X), a 157° da diagonal.
for y in (3, W - 4):
    b.strut("longarinas", f"longarina_y{y}", (X_PEAK + 1, y, TOP_HIGH), (X_NOSE - 1, y, TOP_NOSE),
            from_arm=[-1, 0, 0], to_arm=[1, 0, 0], color=OR)

# ============================================================
# MASTRO, BRAÇO, ANTENA
# ============================================================
b.brick("mastro", "pe_mastro", (16, 5, RING), (4, 4, 1), GF, holes="z", rounded="z", corner_r=4.0,
        studs="top", studs_on="inner")
b.brick("mastro", "mastro", (17, 6, RING + 1), (2, 2, 10), WH, holes="z", rounded="z", corner_r=4.0)
b.brick("mastro", "cabeca", (16, 3, RING + 11), (3, 8, 2), OR, rounded="x", corner_r=4.0)

b.plate("eletronica", "base_pi", (5, 3, RING), 10, 7, GF, studs="bottom")
# braço no ombro direito do nariz (o centro fica para o LiDAR)
YA = W - 4
b.brick("braco", "braco_base", (L - 2, YA, RING + 1), (2, 2, 1), GF, holes="xz")
b.strut("braco", "braco", (L, YA, RING + 1), (L + 4, YA, RING + 4), from_arm=[-1, 0, 0],
        to_arm=[1, 0, 0], color=OR)
b.brick("braco", "punho", (L + 5, YA, RING + 4), (1, 1, 1), GF)
b.hinges.append("punho")
b.brick("antena", "antena_haste", (1, 9, RING), (2, 1, 5), WH, holes="xz", rounded="y", flat=["back"])

# ============================================================
# MOCKS — eletrônica com medida e massa reais
# ============================================================
G = 8.0
DARK, LENS, STEEL = [0.15, 0.15, 0.17, 0.95], [0.02, 0.02, 0.03, 1.0], [0.75, 0.75, 0.78, 1.0]
b.component("mocks", "pi4", (5.35, 3.2, RING + 0.5), (85.0, 56.0, 17.0), "Raspberry Pi 4",
       [0.10, 0.45, 0.25, 0.95], mass=46)
b.component("mocks", "driver", (20.0, 4.6, RING), (40.0, 30.0, 12.0), "driver de motor",
       [0.12, 0.30, 0.60, 0.95], mass=20)
b.component("mocks", "bateria", (12.2, 4.2, 4.0), (67.0, 42.0, 28.0), "bateria 2S", DARK, mass=110)
b.component("mocks", "bat_tampa", (12.2 + 67 / G, 4.2, 4.0), (10.0, 42.0, 28.0), "bateria (terminal)",
       [0.90, 0.45, 0.10, 0.95], mass=10)
# LiDAR no nariz, à frente do arco baixo: vê o caminho e não disputa o topo com a cabeça
b.component("mocks", "lidar", (26.09, 4.09, RING), (38.6, 38.6, 33.5), "LiDAR LD06",
       [0.08, 0.08, 0.09, 1.0], shape="cyl", axis="z", mass=42)
for s, y in (("e", 4.125), ("d", 8.125)):
    b.component("mocks", f"lente_{s}", (19.0, y, RING + 11.125), (14.0, 14.0, 6.0), "câmera estéreo", LENS,
           shape="cyl", axis="x", mass=8)
b.component("mocks", "prato", (0.3, 6.5, RING + 1.5), (48.0, 48.0, 5.0), "antena de alto ganho",
       [0.92, 0.92, 0.90, 1.0], shape="cyl", axis="x", mass=25)
for k, y in enumerate((3.5, 9.0)):
    b.component("mocks", f"hazcam{k}", (L + 2, y, BZ + 0.25), (6.0, 6.0, 5.0), "hazcam", LENS,
           shape="cyl", axis="x", mass=4)
for k, y in enumerate((5.5, 7.5)):
    b.component("mocks", f"farol{k}", (L + 2, y, BZ + 0.3), (6.0, 6.0, 3.0), "farol", [1.0, 0.95, 0.75, 1.0],
           shape="cyl", axis="x", mass=2)
b.component("mocks", "garra", (L + 6, YA + 0.1, RING + 4.1), (10.0, 6.0, 6.0), "garra", STEEL, mass=15)

# motores N20 por dentro de cada roda, com o fio subindo pela lateral
# e correndo pela borda do deck até o driver
for tag, ax in zip("tmf", AXLES):
    for s, y_motor, y_edge, y_run in (("e", YS + 1, -0.4, 1.3), ("d", W - YS - 1 - 34 / G, W + 0.4, W - 1.3)):
        b.component("mocks", f"motor_{tag}_{s}", (ax + 0.25, y_motor, AZ + 0.2), (12.0, 34.0, 10.0), "motor N20",
               STEEL, mass=12)
        y_out = y_motor + 34 / G if s == "e" else y_motor
        b.component("mocks", f"fio_motor_{tag}_{s}", (0, 0, 0), (2.0, 2.0, 2.0), "fio", [0.85, 0.12, 0.10, 1.0],
               shape="cable", points=[[ax + 1.0, y_out, AZ + 0.8], [ax + 1.0, y_edge, AZ + 0.8],
                                      [ax + 1.0, y_edge, DECK + 1.2], [ax + 1.0, y_run, RING + 0.3],
                                      [21.0, y_run, RING + 0.3], [22.0, 5.0 if s == "e" else 8.2, RING + 0.6]])
b.component("mocks", "fio_bat", (0, 0, 0), (2.4, 2.4, 2.4), "fio", [0.10, 0.10, 0.10, 1.0], shape="cable",
       points=[[21.0, 6.0, 5.6], [22.0, 6.0, 7.6], [22.0, 6.0, DECK + 1.2], [22.0, 6.0, RING + 0.6]])
for k, (col, dy) in enumerate(zip(([0.85, 0.12, 0.10, 1.0], [0.12, 0.35, 0.85, 1.0]), (0.0, 0.3))):
    b.component("mocks", f"fio_cam{k}", (0, 0, 0), (2.2, 2.2, 2.2), "fio", col, shape="cable",
           points=[[18.4 + dy, 6.6, RING + 11.0], [18.4 + dy, 8.2, RING + 10.0], [18.4 + dy, 8.2, RING + 2.4],
                   [17.0, 9.4 + dy, RING + 1.4], [13.0, 9.4 + dy, RING + 2.6]])
b.component("mocks", "letreiro", (21.0, 11.2, RING + 0.02), (8.0, 0.0, 0.6), "letreiro ORION",
       [0.95, 0.47, 0.10, 1.0], shape="text", text="ORION", axis="180")

b.notes.update({
    "blocos": "Dois blocos 16×12×2 entram na lateral esquerda pelos machos do lado.",
    "deck": "4 placas brancas iguais; machos em toda a base.",
    "berco": "De baixo para cima: 4 pendurais nos blocos, bandeja nos pendurais. A bateria sai pela frente.",
    "rodas": "6 rodas off-road Ø88: a do meio na coluna, as outras nos cubos dos bogies.",
    "teto": "Dois trilhos por cima dos arcos altos: bagageiro e proteção.",
    "longarinas": "Do arco alto ao arco do nariz: a linha do perfil.",
    "mastro": "Pé 4×4 sobre o deck, mastro redondo, cabeça de câmeras.",
    "eletronica": "Laje adaptadora do Pi sobre o deck.",
    "braco": "Base sobre o aro da frente, diagonal 4-3, punho giratório.",
    "antena": "Haste traseira da antena de alto ganho.",
    "mocks": "Pi, driver, bateria, 6 motores, LiDAR, câmeras, antena, hazcams, faróis, garra, fios — não imprimem.",
})
ORDER = ["lateral_e", "blocos", "lateral_d", "bico_f", "bico_t", "deck", "berco", "ombro_e", "ombro_d",
         "susp_e", "susp_d", "rodas", "aro", "arco_t", "arco_m", "arco_f", "teto", "longarinas", "mastro",
         "eletronica", "braco", "antena", "mocks"]
assert set(ORDER) == set(b.groups), set(b.groups) ^ set(ORDER)
b.groups = {g: b.groups[g] for g in ORDER}
b.write(__file__)
