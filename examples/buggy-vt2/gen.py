#!/usr/bin/env python3
"""
Gera examples/buggy-vt2/assembly.toml — Buggy V-T Mk2.

Versão em ALTA RESOLUÇÃO do buggy da imagem de referência: escala
~1.8× (272 × 208mm, rodas Ø112), construído como um kit técnico —
dezenas de vigas de ponta redonda (liftarm) unidas por cavilhas, em
vez de poucos blocos grandes.

Por que um gerador: são ~70 peças com simetria esquerda/direita.
Gerar a IR por código elimina erro de digitação em coordenada; o
assembly.toml gerado continua sendo a fonte que o compilador lê.

    python3 examples/buggy-vt2/gen.py && make assemble NAME=buggy-vt2

Eixos: x = trás → frente · y = esquerda → direita · z = cima.
1 célula = 8mm.
"""

import os

OR = [0.97, 0.47, 0.10]      # laranja
BK = [0.11, 0.11, 0.12]      # preto da gaiola
TN = [0.83, 0.73, 0.56]      # bege do teto
GR = [0.62, 0.63, 0.66]      # cinza do suporte

W = 16                        # largura do corpo em células (y 0..15)
SIDES = {"e": 0, "d": W - 1}  # esquerda, direita

parts, groups = [], {}


def fmt(v):
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {fmt(x)}" for k, x in v.items()) + " }"
    if isinstance(v, float):
        return f"{v:g}" if v != int(v) else f"{v:.1f}"
    return str(v)


def add(group, **kw):
    parts.append(kw)
    groups.setdefault(group, []).append(kw["id"])


def brick(group, id, at, size, color, **kw):
    add(group, id=id, type="brick", at=list(at), size=list(size), color=color, **kw)


def mock(id, at, size, label, color, **kw):
    add("eletronica", id=id, type="component", at=list(at), size_mm=list(size), label=label, color=color, **kw)


# ============================================================
# CHASSI — laterais em camadas de vigas (furos à vista em Y)
# ============================================================
# Emendas desencontradas entre camadas, como alvenaria: nenhuma
# emenda fica sobre outra, então as cavilhas verticais travam tudo.
ROWS = {
    0: [(0, 17), (17, 34)],
    1: [(0, 12), (12, 24), (24, 34)],
    2: [(0, 14), (14, 22), (22, 34)],     # eixos das rodas em x=6 e x=27
    3: [(0, 10), (10, 20), (20, 34)],
    4: [(0, 14), (14, 24), (24, 34)],     # topo da lateral, de ponta a ponta
}
TOP = 5                                   # nível dos decks
LIFT_Y = dict(holes="xyz", rounded="y")      # viga ao longo de X
LIFT_X = dict(holes="xyz", rounded="x")      # viga ao longo de Y
LIFT_V = dict(holes="xyz", rounded="y")      # poste vertical, furos em Y

axle_beam = {}
for s, y in SIDES.items():
    for z, segs in ROWS.items():
        for k, (x0, x1) in enumerate(segs):
            pid = f"lat{z}{'abc'[k]}_{s}"
            brick("chassi", pid, (x0, y, z), (x1 - x0, 1, 1), OR, **LIFT_Y)
            if z == 2:
                for ax in (6, 27):
                    if x0 <= ax < x1:
                        axle_beam[(s, ax)] = pid

# Travessas (viga ao longo de Y), cavilhadas nas faces internas
for x in (1, 9, 17, 25, 32):
    brick("chassi", f"trav0_x{x}", (x, 1, 0), (1, W - 2, 1), OR, **LIFT_X)
for x in (1, 12, 25, 32):
    brick("chassi", f"trav4_x{x}", (x, 1, 4), (1, W - 2, 1), OR, **LIFT_X)

# Piso: 4 placas IGUAIS de 8×14, cada uma sobre uma travessa — mais
# resolução, e um STL só para as quatro (mesma configuração)
for k, x in enumerate((1, 9, 17, 25)):
    brick("chassi", f"piso{k}", (x, 1, 1), (8, W - 2, 1), OR, thickness=4.0, holes="z",
          rounded="z", corner_r=2.0, faces={"bottom": "stud"})

# Decks: traseiro (sob a bateria e os postes) e dianteiro (câmera)
brick("chassi", "deck_t_e", (0, 0, TOP), (14, 8, 1), OR, holes="z", rounded="z", corner_r=4.0,
      faces={"bottom": "stud"})
brick("chassi", "deck_t_d", (0, 8, TOP), (14, 8, 1), OR, holes="z", rounded="z", corner_r=4.0,
      faces={"bottom": "stud"})
brick("chassi", "deck_f", (24, 1, TOP), (10, W - 2, 1), OR, holes="z", rounded="z", corner_r=4.0,
      faces={"bottom": "stud"})

# Frente: duas vigas de face (furos à vista na frente) + para-choque
for z in (1, 2, 3, 4):
    brick("chassi", f"frente{z}", (34, 0, z), (1, W, 1), OR, **LIFT_X)
brick("chassi", "parachoque_f", (34, 0, 0), (2, W, 1), OR, holes="xz", rounded="z", corner_r=4.0)
# Traseira: idem
for z in (1, 2, 3, 4):
    brick("chassi", f"tras{z}", (-1, 0, z), (1, W, 1), OR, **LIFT_X)
brick("chassi", "parachoque_t", (-2, 0, 0), (2, W, 1), OR, holes="xz", rounded="z", corner_r=4.0)

# ============================================================
# GAIOLA — vigas pretos, colunas A em diagonal 9-12-15
# ============================================================
ROOF = 14
for s, y in SIDES.items():
    for x in (0, 9):
        brick("gaiola", f"poste_x{x}_{s}", (x, y, TOP + 1), (1, 1, ROOF - TOP - 1), BK, **LIFT_V)
    brick("gaiola", f"trilho_{s}", (1, y, ROOF), (17, 1, 1), BK, **LIFT_Y)
    # Nó alto na ponta do trilho; nó baixo no topo da lateral dianteira.
    # Vetor (12, 0, -9): módulo 15 → viga de 14 células, 36.9°.
    add("gaiola", id=f"no_alto_{s}", type="node", at=[18, y, ROOF],
        dirs=[[-1, 0, 0], [4, 0, -3]], color=BK)
    add("gaiola", id=f"no_baixo_{s}", type="node", at=[30, y, TOP],
        dirs=[[0, 0, -1], [-4, 0, 3]], color=BK)
    add("gaiola", id=f"coluna_a_{s}", type="strut", **{"from": f"no_baixo_{s}"},
        to=f"no_alto_{s}", style="beam", color=BK)
brick("gaiola", "teto_tras", (0, 0, ROOF), (1, W, 1), BK, **LIFT_X)
brick("gaiola", "teto_frente", (17, 1, ROOF), (1, W - 2, 1), BK, **LIFT_X)
# Teto liso: sem furos, pinos só no perímetro (sobre o quadro)
brick("teto", "teto", (0, 0, ROOF + 1), (18, W, 1), TN, thickness=4.0, holes="none",
      rounded="z", corner_r=4.0, faces={"bottom": "stud"}, studs_on="edge")

# ============================================================
# FRENTE — suporte da câmera e dos LEDs (pretos)
# ============================================================
brick("frente", "suporte_cam", (33, 6, TOP + 1), (1, 4, 4), BK, holes="xz", faces={"bottom": "stud"})
for s, y0 in (("e", 2), ("d", 12)):
    brick("frente", f"suporte_led_{s}", (33, y0, TOP + 1), (1, 2, 2), BK, holes="xz",
          faces={"bottom": "stud"})

# ============================================================
# BATERIA — base e presilhas cinzas
# ============================================================
brick("bateria", "base_bat", (2, 4, TOP + 1), (12, 8, 1), GR, thickness=4.0, holes="z",
      rounded="z", corner_r=4.0, faces={"bottom": "stud"})
for x in (2, 13):
    brick("bateria", f"presilha_x{x}", (x, 5, TOP + 1.5), (1, 6, 3), GR, holes="z", faces={"bottom": "stud"})

# ============================================================
# RODAS — balão Ø112, 5 células de largura, aro de 5 raios em Y
# ============================================================
for s, y in SIDES.items():
    side_face = "right" if s == "e" else "left"
    wy = -1 if s == "e" else W
    for tag, ax in (("t", 6), ("f", 27)):
        add("rodas", id=f"roda_{tag}{s}", type="wheel", at=[ax, wy, 2],
            on=f"{axle_beam[(s, ax)]}.{side_face}", diameter=14, width=5,
            tread="balloon", spokes=5, spoke_style="y")

# ============================================================
# ELETRÔNICA — componentes (não imprimem; reservam espaço)
# ============================================================
G = 8.0
# bateria: pack ~78 × 42 × 28 com terminal à frente, bicolor
mock("bateria", (3.05, 5.4, 6.5), (54.0, 42.0, 28.0), "bateria (corpo)", [0.12, 0.12, 0.13, 0.95])
mock("bateria_tampa", (3.05 + 54 / G, 5.4, 6.5), (23.5, 42.0, 28.0), "bateria (tampa)",
     [0.80, 0.50, 0.22, 0.95])
for k, yy in enumerate((6.6, 9.0)):
    mock(f"terminal{k}", (11.7, yy, 10.0), (6.0, 6.0, 4.0), "terminal", [0.75, 0.75, 0.78, 1.0],
         shape="cyl", axis="z")
# placa de câmera em pé, colada no suporte
mock("esp32cam", (34.0, 6.3, 6.5), (4.5, 27.0, 40.0), "ESP32-CAM", [0.08, 0.30, 0.20, 0.95])
mock("camera_mod", (34.56, 7.25, 9.1), (2.0, 12.0, 12.0), "módulo da câmera", [0.06, 0.06, 0.06, 1.0])
mock("lente", (34.81, 7.94, 9.8), (8.0, 8.0, 5.0), "lente", [0.02, 0.02, 0.03, 1.0],
     shape="cyl", axis="x")
# LEDs: dois brancos em cima, dois âmbar embaixo, em cada suporte
for s, y0 in (("e", 2), ("d", 12)):
    for k, (yy, zz, col, lbl) in enumerate((
            (y0 + 0.15, 7.15, [0.96, 0.96, 1.0, 0.9], "LED branco"),
            (y0 + 1.05, 7.15, [0.96, 0.96, 1.0, 0.9], "LED branco"),
            (y0 + 0.15, 6.25, [1.0, 0.78, 0.08, 0.9], "LED âmbar"),
            (y0 + 1.05, 6.25, [1.0, 0.78, 0.08, 0.9], "LED âmbar"))):
        mock(f"led_{s}{k}", (34.0, yy, zz), (5.5, 5.5, 7.0), lbl, col, shape="cyl", axis="x")
# faróis do teto: corpo preto + lente
for s, yy in (("e", 0.3), ("d", W - 1.8)):
    mock(f"farol_{s}", (15.4, yy, ROOF + 1.5), (12.0, 12.0, 10.0), "farol (corpo)",
         [0.06, 0.06, 0.07, 1.0], shape="cyl", axis="x")
    mock(f"farol_lente_{s}", (16.65, yy + 0.19, ROOF + 1.69), (9.0, 9.0, 1.5), "farol (lente)",
         [0.97, 0.97, 1.0, 0.95], shape="cyl", axis="x")
# letreiro V-T no teto
mock("letreiro", (8.0, 8.0, ROOF + 1.5), (11.0, 0.0, 0.6), "letreiro V-T", [0.25, 0.22, 0.18, 1.0],
     shape="text", text="V-T", axis="90")   # axis = giro em Z: lê de frente
# fios: da câmera, pela lateral esquerda, até a bateria
for k, (col, dy) in enumerate((([0.85, 0.12, 0.10, 1.0]), ([0.12, 0.35, 0.85, 1.0]),
                                ([0.10, 0.65, 0.35, 1.0])) and
                               zip(([0.85, 0.12, 0.10, 1.0], [0.12, 0.35, 0.85, 1.0],
                                    [0.10, 0.65, 0.35, 1.0]), (0.0, 0.3, 0.6))):
    mock(f"fio{k}", (0, 0, 0), (2.2, 2.2, 2.2), "fio", col, shape="cable",
         points=[[33.9, 7.4 + dy, 9.6], [31.5, 4.5 + dy, 6.35], [24.5, 0.6 + dy, 6.35],
                 [23.6, 0.6 + dy, 5.35], [15.0, 0.6 + dy, 5.35], [14.2, 0.6 + dy, 6.35],
                 [13.0, 3.2 + dy, 6.6], [12.4, 6.6 + dy * 2, 10.6]])

# ============================================================
# Saída
# ============================================================
ORDER = ["chassi", "rodas", "bateria", "gaiola", "teto", "frente", "eletronica"]
NOTES = {
    "chassi": "Laterais em 4 camadas de liftarms com emendas desencontradas; travessas, piso, decks e para-choques. Tudo por cavilha.",
    "rodas": "Roda no eixo, eixo no rebaixo da camada do meio da lateral.",
    "bateria": "Base cinza sobre o deck traseiro, presilhas nas pontas.",
    "gaiola": "Postes nos decks, quadro do teto, colunas A em diagonal 9-12-15 entre os nós.",
    "teto": "Laje bege sobre o quadro, cavilhas em todo o perímetro.",
    "frente": "Suporte da câmera e suportes dos LEDs sobre o deck dianteiro.",
    "eletronica": "Mocks: reservam espaço, não são impressos.",
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assembly.toml")
with open(out, "w") as f:
    f.write("""# ============================================================
# BUGGY V-T Mk2 — GERADO por gen.py (edite o gerador, não este arquivo)
# ============================================================
# Buggy off-road 4×4 da imagem de referência em alta resolução:
# 288 × 208mm, rodas balão Ø112, ~90 peças estilo kit técnico.
#
# Vista lateral (X-Z), x = TRÁS → FRENTE:
#
#   z=14  ╭──────── teto bege (laje 4mm) ────────╮◉ farol
#   z=13  ├─teto_tras──trilho───────────teto_frente●  nó alto (x=18)
#         ┃poste        ┃poste                      ╲  coluna A
#         ┃             ┃     [bateria]               ╲  9-12-15
#   z=4   ▓▓▓ deck traseiro ▓▓▓        ▓▓ deck dianteiro ●▓ (x=30) ▌cam
#   z=3   ═══ lateral ═══                   ═══ lateral ═══
#   z=0..2  ═══ laterais em camadas · piso · travessas ═══ ▀▀ para-choque
#          ( roda Ø112 )                ( roda Ø112 )
#   x:  -2 0      6        9    14  18      24  27  30  34 36
# ============================================================

""")
    f.write('[assembly]\nname   = "buggy-vt2"\ndowel_every = 3\nview_angle = 125\n')
    f.write('intent = "Buggy off-road 4×4 da imagem de referência em alta resolução: laterais em camadas de liftarms laranja, gaiola preta com colunas A diagonais, teto bege com faróis, bateria em suporte cinza, câmera e LEDs na frente, rodas balão"\n\n')
    f.write("parts = [\n")
    for p in parts:
        f.write("  { " + ", ".join(f"{k} = {fmt(v)}" for k, v in p.items()) + " },\n")
    f.write("]\n\ngroups = [\n")
    for g in ORDER:
        f.write(f'  {{ id = "{g}", parts = {fmt(groups.get(g, []))}, note = "{NOTES[g]}" }},\n')
    f.write("]\n")
print(f"{len(parts)} peças → {os.path.relpath(out)}")
