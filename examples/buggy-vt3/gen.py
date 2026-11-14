#!/usr/bin/env python3
"""
Gera examples/buggy-vt3/assembly.toml — Buggy V-T Mk3.

O vt2 refeito com a skill v2. O que mudou e por quê (stats do vt2):

  · gaiola de TUBO: dois arcos (poste → BEND → travessa → BEND →
    poste) unidos por trilhos, em vez de quadro reto com canto vivo;
  · colunas A 6-8-10 que nascem de lado no arco dianteiro (regra do
    braço ≥127°), não de um nó solto no canto do teto;
  · teto do tamanho da gaiola (12 células de largura, não 16);
  · para-choques de BEND: bico arredondado na frente e atrás;
  · laterais com 2 segmentos por camada, emendas desencontradas:
    menos pares de contato → menos cavilhas (vt2: 144 só aí);
  · travessas com machos integrais nas pontas (sem cavilha);
  · piso e decks com faces auto: cavilha só onde encostam — o vt2
    tinha 658 machos impressos sem encaixar em nada.

    python3 examples/buggy-vt3/gen.py && make assemble NAME=buggy-vt3
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "impl", "python"))
from fusionbrick.irgen import BK, GR, OR, TN, Build, LIFT_X, LIFT_Z  # noqa: E402

W = 16            # largura em células (y 0..15)
L = 34            # comprimento da lateral (x 0..33)
TOP = 5           # nível dos decks
ROOF = 14         # nível das travessas do teto
HOOPS = {"t": 1, "f": 21}   # x dos arcos traseiro e dianteiro
AXLES = (6, 27)

b = Build("buggy-vt3", "Buggy off-road 4×4 da imagem de referência, Mk3: gaiola de tubo com arcos curvos, "
          "colunas A diagonais, teto bege do tamanho da gaiola, laterais de liftarm laranja, para-choques "
          "arredondados, bateria, câmera e LEDs, rodas balão", view_angle=125, dowel_every=5)
b.header = """BUGGY V-T Mk3 — vista lateral (X-Z), x = TRÁS → FRENTE

z=15        ▄▄▄▄▄▄▄▄▄ teto bege (laje, machos só no perímetro) ▄▄▄▄
z=13..14   ╭─arco t─╮─────── trilhos y=2 e y=13 ───────╭─arco f─╮
z=6..12    ┃ poste  ┃                                  ┃ poste ●╲ nó (22,11)
           ┃        ┃      [bateria]                   ┃        ╲ coluna A 6-8-10
z=5     ▓▓▓▓ deck traseiro ▓▓▓▓                 ▓▓▓ deck dianteiro ●(30,5) ▌cam
z=0..4 ╭═══ laterais: 5 camadas de liftarm, 2 segmentos cada ═══════════╮
z=0    ╰ bico (BEND)            ( roda Ø112 )        ( roda Ø112 )  bico ╯
x:    -2 0 1      6        13       21  22     27  30   33 35

Arcos no plano Y-Z (vista de frente):   ╭──────────╮  z=14, travessa y=2..13
                                        ┃          ┃  postes y=0 e y=15
"""

# ============================================================
# CHASSI — laterais em camadas de viga, 2 segmentos por camada
# ============================================================
ROWS = {0: 17, 1: 11, 2: 14, 3: 21, 4: 8}      # onde fica a emenda em cada camada
axle_beam = {}
for z, cut in ROWS.items():
    for k, (x0, x1) in enumerate(((0, cut), (cut, L))):
        pid = f"lat{z}{'ab'[k]}_e"
        # Camadas 0–3 levam MACHOS em cima, só nas células planas
        # (pin_cells = "inner"): o empilhamento vira encaixe integral.
        stack = dict(faces={"top": "stud"}, studs_on="inner") if z < 4 else {}
        b.brick("chassi", pid, (x0, 0, z), (x1 - x0, 1, 1), OR, **LIFT_X, **stack)
        if z == 2:
            for ax in AXLES:
                if x0 <= ax < x1:
                    axle_beam[ax] = pid[:-2]

# Travessas: vigas retas com MACHOS nas pontas (encaixe integral nas
# laterais). Ponta redonda não aceita pino, então estas não têm round.
for x in (1, 9, 17, 25, 32):
    b.brick("chassi", f"trav0_x{x}", (x, 1, 0), (1, W - 2, 1), OR, holes="xyz",
            faces={"right": "stud", "left": "stud"})
for x in (1, 12, 25, 32):
    b.brick("chassi", f"trav4_x{x}", (x, 1, 4), (1, W - 2, 1), OR, holes="xyz",
            faces={"right": "stud", "left": "stud"})

# Piso: 4 placas iguais; faces auto → cavilha só sobre as travessas
for k, x in enumerate((1, 9, 17, 25)):
    b.brick("chassi", f"piso{k}", (x, 1, 1), (8, W - 2, 1), OR, thickness=4.0, holes="z",
            rounded="z", corner_r=2.0)

# Decks
b.brick("chassi", "deck_t_e", (0, 0, TOP), (14, 8, 1), OR, holes="z", rounded="z", corner_r=4.0)
b.brick("chassi", "deck_f", (24, 1, TOP), (10, W - 2, 1), OR, holes="z", rounded="z", corner_r=4.0)

# Frente e traseira: vigas de face (furos à vista), camadas 1–4
for z in (1, 2, 3, 4):
    stack = dict(faces={"top": "stud"}, studs_on="inner") if z < 4 else {}
    b.brick("chassi", f"frente{z}", (L, 0, z), (1, W, 1), OR, holes="xyz", rounded="x", **stack)
    b.brick("chassi", f"tras{z}", (-1, 0, z), (1, W, 1), OR, holes="xyz", rounded="x", **stack)

# Bicos: para-choques arredondados na camada do chão, curvas k=1 nos cantos
# frente: lateral_e → curva → travessa em x=35 → curva → lateral_d
b.curve("chassi", "bico_f_e", (L, 0, 0), (1, 0, 0), (0, 1, 0), color=BK)
b.brick("chassi", "bico_f", (L + 1, 2, 0), (1, W - 4, 1), BK, holes="xyz", rounded="x")
# traseira: espelho em X (as curvas _d saem do mirror_y)
b.brick("chassi", "bico_t", (-2, 2, 0), (1, W - 4, 1), BK, holes="xyz", rounded="x")
b.curve("chassi", "bico_t_e", (-2, 1, 0), (0, -1, 0), (1, 0, 0), color=BK)

# ============================================================
# GAIOLA — dois arcos de tubo, trilhos, colunas A
# ============================================================
for tag, x in HOOPS.items():
    z0 = TOP + 1 if x < 14 else TOP          # arco traseiro apoia no deck; dianteiro na lateral
    g = "gaiola"
    b.brick(g, f"arco_{tag}_poste_e", (x, 0, z0), (1, 1, ROOF - 1 - z0), BK, **LIFT_Z)
    b.curve(g, f"arco_{tag}_c_e", (x, 0, ROOF - 1), (0, 0, 1), (0, 1, 0), color=BK)
    b.brick(g, f"arco_{tag}_trav", (x, 2, ROOF), (1, W - 4, 1), BK, holes="xyz", rounded="x")
    # o lado _d (curva e poste) sai do mirror_y
for y in (2, W - 3):
    b.brick("gaiola", f"trilho_y{y}", (HOOPS["t"] + 1, y, ROOF), (HOOPS["f"] - HOOPS["t"] - 1, 1, 1),
            BK, **LIFT_X)

# Coluna A: de um pé sobre a lateral dianteira até o TOPO do poste do
# arco dianteiro, encostando DE LADO nele (braço −X, a 143° da diagonal).
b.brick("gaiola", "pe_coluna_e", (30, 0, TOP), (1, 1, 1), BK)
b.strut("gaiola", "coluna_a_e", (30, 0, TOP + 1), (HOOPS["f"] + 1, 0, ROOF - 2),
        from_arm=[0, 0, -1], to_arm=[-1, 0, 0], color=BK)

# Teto: do tamanho da gaiola, pinos só no perímetro (sobre arcos e trilhos)
b.brick("teto", "teto", (HOOPS["t"], 2, ROOF + 1), (HOOPS["f"] - HOOPS["t"] + 1, W - 4, 1), TN,
        thickness=4.0, holes="none", rounded="z", corner_r=4.0, faces={"bottom": "stud"}, studs_on="edge")

# ============================================================
# FRENTE — suporte da câmera e dos LEDs
# ============================================================
b.brick("frente", "suporte_cam", (33, 6, TOP + 1), (1, 4, 4), BK, holes="xz", faces={"bottom": "stud"})
b.brick("frente", "suporte_led_e", (33, 2, TOP + 1), (1, 2, 2), BK, holes="xz", faces={"bottom": "stud"})

# ============================================================
# BATERIA — base e presilhas cinzas
# ============================================================
b.brick("bateria", "base_bat", (2, 4, TOP + 1), (12, 8, 1), GR, thickness=4.0, holes="z",
        rounded="z", corner_r=4.0, faces={"bottom": "stud"})
for x in (2, 13):
    b.brick("bateria", f"presilha_x{x}", (x, 5, TOP + 1.5), (1, 6, 3), GR, holes="z", faces={"bottom": "stud"})

# ============================================================
# RODAS — balão Ø112, 5 células, aro de 5 raios em Y
# ============================================================
for tag, ax in (("t", AXLES[0]), ("f", AXLES[1])):
    b.wheel("rodas", f"roda_{tag}_e", (ax, -1, 2), f"{axle_beam[ax]}_e.right", diameter=14, width=5,
            tread="balloon", spokes=5, spoke_style="y")

# ============================================================
# Simetria: tudo que é _e ganha o par _d (laterais, postes, colunas,
# suporte de LED, rodas)
# ============================================================
b.mirror_y(W)

# ============================================================
# ELETRÔNICA — componentes
# ============================================================
G = 8.0
b.component("eletronica", "bateria", (3.05, 5.4, 6.5), (54.0, 42.0, 28.0), "bateria (corpo)",
       [0.12, 0.12, 0.13, 0.95])
b.component("eletronica", "bateria_tampa", (3.05 + 54 / G, 5.4, 6.5), (23.5, 42.0, 28.0), "bateria (tampa)",
       [0.80, 0.50, 0.22, 0.95])
for k, yy in enumerate((6.6, 9.0)):
    b.component("eletronica", f"terminal{k}", (11.7, yy, 10.0), (6.0, 6.0, 4.0), "terminal",
           [0.75, 0.75, 0.78, 1.0], shape="cyl", axis="z")
b.component("eletronica", "esp32cam", (34.0, 6.3, 6.5), (4.5, 27.0, 40.0), "ESP32-CAM", [0.08, 0.30, 0.20, 0.95])
b.component("eletronica", "camera_mod", (34.56, 7.25, 9.1), (2.0, 12.0, 12.0), "módulo da câmera",
       [0.06, 0.06, 0.06, 1.0])
b.component("eletronica", "lente", (34.81, 7.94, 9.8), (8.0, 8.0, 5.0), "lente", [0.02, 0.02, 0.03, 1.0],
       shape="cyl", axis="x")
for s, y0 in (("e", 2), ("d", 12)):
    for k, (yy, zz, col, lbl) in enumerate((
            (y0 + 0.15, 7.15, [0.96, 0.96, 1.0, 0.9], "LED branco"),
            (y0 + 1.05, 7.15, [0.96, 0.96, 1.0, 0.9], "LED branco"),
            (y0 + 0.15, 6.25, [1.0, 0.78, 0.08, 0.9], "LED âmbar"),
            (y0 + 1.05, 6.25, [1.0, 0.78, 0.08, 0.9], "LED âmbar"))):
        b.component("eletronica", f"led_{s}{k}", (34.0, yy, zz), (5.5, 5.5, 7.0), lbl, col, shape="cyl", axis="x")
# faróis na travessa do arco dianteiro, por cima do teto
for s, yy in (("e", 2.3), ("d", W - 3.8)):
    b.component("eletronica", f"farol_{s}", (HOOPS["f"] - 0.5, yy, ROOF + 1.5), (12.0, 12.0, 10.0),
           "farol (corpo)", [0.06, 0.06, 0.07, 1.0], shape="cyl", axis="x")
    b.component("eletronica", f"farol_lente_{s}", (HOOPS["f"] + 0.75, yy + 0.19, ROOF + 1.69), (9.0, 9.0, 1.5),
           "farol (lente)", [0.97, 0.97, 1.0, 0.95], shape="cyl", axis="x")
b.component("eletronica", "letreiro", (9.0, 8.0, ROOF + 1.5), (11.0, 0.0, 0.6), "letreiro V-T",
       [0.25, 0.22, 0.18, 1.0], shape="text", text="V-T", axis="90")
# fios da câmera até a bateria, por DENTRO do poste do arco (y ≥ 1.4)
for k, (col, dy) in enumerate(zip(([0.85, 0.12, 0.10, 1.0], [0.12, 0.35, 0.85, 1.0],
                                   [0.10, 0.65, 0.35, 1.0]), (0.0, 0.3, 0.6))):
    b.component("eletronica", f"fio{k}", (0, 0, 0), (2.2, 2.2, 2.2), "fio", col, shape="cable",
           points=[[33.9, 7.4 + dy, 9.6], [31.5, 4.5 + dy, 6.35], [24.5, 1.5 + dy, 6.35],
                   [23.6, 1.5 + dy, 5.35], [15.0, 1.5 + dy, 5.35], [14.2, 1.5 + dy, 6.35],
                   [13.0, 3.2 + dy, 6.6], [12.4, 6.6 + dy * 2, 10.6]])

b.notes = {
    "chassi": "Laterais em 5 camadas de liftarm (2 segmentos, emendas desencontradas), travessas com machos, "
              "piso em 4 placas, decks, vigas de face e bicos arredondados.",
    "rodas": "Roda no eixo, eixo no rebaixo da camada do meio da lateral.",
    "bateria": "Base cinza sobre o deck traseiro, presilhas nas pontas.",
    "gaiola": "Arcos traseiro e dianteiro (poste, curva, travessa, curva, poste), trilhos do teto e colunas A.",
    "teto": "Laje bege sobre arcos e trilhos, machos só no perímetro.",
    "frente": "Suportes da câmera e dos LEDs sobre o deck dianteiro.",
    "eletronica": "Mocks: reservam espaço, não são impressos.",
}
# ordem de montagem
b.groups = {g: b.groups[g] for g in ("chassi", "rodas", "bateria", "gaiola", "teto", "frente", "eletronica")}
b.write(__file__)
