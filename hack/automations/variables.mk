# ============================================================
# variables.mk — superfície única de configuração
# ============================================================
# Toda variável ajustável do pipeline mora aqui. `openscad.mk`
# fica só com as receitas.
#
# PRECEDÊNCIA (menor → maior):
#
#   1. default no .scad          hole_d = 4.0;
#   2. default deste arquivo     HOLE_D ?= 4.0
#   3. .env na raiz do projeto   HOLE_D=5.0
#   4. variável na linha         make build HOLE_D=5.0
#   5. EXTRA_D                   make build EXTRA_D='-D hole_d=5.0'
#
# 3 vence 2 porque os defaults usam `?=` e o .env é lido antes.
# 4 vence 3 porque variável de linha de comando ganha de
# qualquer atribuição em arquivo, é regra do make.
# 5 vence 4 porque o openscad aplica o ÚLTIMO -D de mesmo nome,
# e EXTRA_D entra depois de SYSTEM_D em toda receita.
# ============================================================

ifndef FB_VARIABLES_MK
FB_VARIABLES_MK := 1

VARS_DIR  := $(dir $(lastword $(MAKEFILE_LIST)))
REPO_ROOT := $(abspath $(VARS_DIR)../..)

# Opcional: ausente não é erro. Formato `CHAVE=valor`, um por
# linha, `#` comenta. Sem `export`, sem aspas — o make trata o
# arquivo como makefile, então aspas viram parte do valor.
-include $(REPO_ROOT)/.env

# ------------------------------------------------------------
# Primitivos do sistema
# ------------------------------------------------------------
# Os seis valores dos quais TODA cota do sistema deriva. Mudar
# um aqui muda o sistema inteiro de forma coerente, porque as
# peças recalculam grid, rebaixo, pino e colar a partir deles.
#
# Não existe GRID: ele é DERIVADO (hole_d + 2×(wall+collar_w)).
# Expor grid como ajustável permitiria pedir um grid que não
# fecha com o próprio furo. Ver spec/constitution.md.
HOLE_D       ?= 4.0
WALL         ?= 1.6
COLLAR_W     ?= 0.4
COLLAR_DEPTH ?= 1.0
TOLERANCE    ?= 0.2

# Folga mínima REAL entre dois machos que se aproximam. Vale para
# o caso coaxial (dois pinos no mesmo furo passante), onde a
# aproximação é axial.
GAP          ?= 0.5

# Protrusão do macho por ponta. Declarada, não derivada de GAP:
# machos PERPENDICULARES se aproximam na diagonal, então descontar
# GAP do eixo cobrava √2 a mais. Teto geométrico = grid/2 −
# pin_d/2 = 2.1; as peças têm assert.
PIN_LEN      ?= 2.0

# Facetas do círculo. Baixe para 16–24 ao iterar: o render cai
# para uma fração do tempo.
FN           ?= 48

# Repassado a TODA invocação do openscad, antes de EXTRA_D.
# `strip` protege contra espaço sobrando no .env (`X=1 ` viraria
# o valor "1 " e quebraria o -D).
#
# O `$$fn` vai com barra invertida, não entre aspas simples: as
# aspas fecham cedo quando este valor é interpolado dentro de
# outra string, e aí o shell expande $$fn para vazio.
SYSTEM_D ?= \
	-D hole_d=$(strip $(HOLE_D)) \
	-D wall=$(strip $(WALL)) \
	-D collar_w=$(strip $(COLLAR_W)) \
	-D collar_depth=$(strip $(COLLAR_DEPTH)) \
	-D tolerance=$(strip $(TOLERANCE)) \
	-D gap=$(strip $(GAP)) \
	-D pin_len=$(strip $(PIN_LEN)) \
	-D \$$fn=$(strip $(FN))

# ------------------------------------------------------------
# Ferramentas
# ------------------------------------------------------------
OPENSCAD ?= openscad
MAGICK   ?= magick
FFMPEG   ?= ffmpeg

# ------------------------------------------------------------
# Caminhos
# ------------------------------------------------------------
IMPL_DIR    ?= impl/openscad
RENDERS_DIR ?= renders
STL_DIR     ?= $(RENDERS_DIR)/stl
IMG_DIR     ?= $(RENDERS_DIR)/img

# Lista dinâmica: acrescentar um .scad basta.
# `params.scad` é biblioteca compartilhada, não peça — o wildcard
# a pegaria e geraria params.stl/params.png sem sentido.
PARTS       ?= $(filter-out params,$(basename $(notdir $(wildcard $(IMPL_DIR)/*.scad))))
ASSEMBLIES  ?= $(wildcard examples/*/assembly.scad)

# Filtra uma peça (ou lista) em vez de varrer o diretório:
#   make build PART=brick
#   make preview PART="brick pin"
PART        ?=
SELECTED    ?= $(if $(PART),$(PART),$(PARTS))

# Parâmetros arbitrários repassados ao openscad, com a última
# palavra sobre tudo. Strings precisam de aspas internas:
#   make build PART=brick EXTRA_D='-D cells_z=5 -D preset=\"beam\"'
EXTRA_D     ?=

# ------------------------------------------------------------
# Render de peça
# ------------------------------------------------------------
IMGSIZE     ?= 800,600
IMG_W       ?= 800
IMG_H       ?= 600
# Cornfield | Metallic | Sunset | Starnight | BeforeDawn | Nature |
# DeepOcean | Solarized | Tomorrow | Tomorrow Night | Monotone
# https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Preferences#Color_Schemes
COLORSCHEME ?= Monotone
GRAD_TOP    ?= rgb(208,208,208)
GRAD_BOT    ?= rgb(82, 82, 82)
PART_COLOR  ?= [0.35, 0.38, 0.42]

# Câmera isométrica: projeção ortográfica + rotação 54.7°/45°
ISO_ELEV    ?= 54.7
ISO_AZIM    ?= 45
ISO_CAMERA  ?= --projection=o --camera=0,0,0,$(ISO_ELEV),0,$(ISO_AZIM),500 --autocenter --viewall

# Acabamento das arestas no export STL — 0 mantém o default de
# cada .scad. Minkowski com radius > 0 deixa o render bem lento.
BORDER_RADIUS ?= 0
BORDER_STYLE  ?= round

# Opções de visualização: axes | crosshairs | edges | scales |
# wireframe (lista separada por vírgula).
#
# ⚠️  wireframe SÓ funciona com --render (F6). O export PNG usa
# --preview (F5/OpenCSG) por padrão, que ignora a flag em
# silêncio: roda sem erro e devolve a imagem sólida. Por isso os
# alvos *-wireframe forçam --render.
VIEW ?=

# ------------------------------------------------------------
# Animação de peça
# ------------------------------------------------------------
# Frames por volta completa e delay entre frames (1/100s)
ANIM_FRAMES ?= 36
ANIM_DELAY  ?= 15

# ------------------------------------------------------------
# Render e animação de assembly
# ------------------------------------------------------------
ASM_IMGSIZE      ?= 1200,900
ASM_ANIM_FRAMES  ?= 72
ASM_ANIM_DELAY   ?= 5
ASM_ANIM_EXPLODE ?= 12
# Graus de giro total no loop — 0 mantém a câmera fixa no ângulo
# isométrico e anima só o explode/recolhe
ASM_ANIM_SPIN    ?= 0
# Multiplicador de velocidade — 2 = 2x mais rápido, 0.5 = metade
ASM_ANIM_SPEED   ?= 1
# Frame rate do MP4 — com ASM_ANIM_FRAMES define a duração do loop
ASM_VIDEO_FPS    ?= 30

# ------------------------------------------------------------
# Fusion 360
# ------------------------------------------------------------
FUSION_ADDIN_NAME ?= FusionBrick
FUSION_ADDIN_SRC  ?= impl/fusion360/$(FUSION_ADDIN_NAME)
FUSION_PY_CORE    ?= impl/python
FUSION_PYTHON     ?= python3

# Onde o Fusion procura add-ins. VAZIO = autodetecta — a Autodesk
# renomeou a pasta ("Autodesk Fusion 360" -> "Autodesk Fusion") ao
# longo das versões, e o caminho tem ESPAÇOS, então a resolução é
# feita no shell da receita, não com $(wildcard).
# Preencha para forçar um caminho.
FUSION_ADDINS_DIR ?=

# Saída do empacotamento para distribuição
FUSION_DIST_DIR   ?= dist/fusion360

# ------------------------------------------------------------
# Diagnóstico
# ------------------------------------------------------------
.PHONY: vars
vars:
	@echo "config efetiva  (.env: $(if $(wildcard $(REPO_ROOT)/.env),$(REPO_ROOT)/.env,ausente))"
	@echo
	@echo "  PRIMITIVOS"
	@printf '    %-14s %s\n' hole_d $(HOLE_D) wall $(WALL) collar_w $(COLLAR_W) \
		collar_depth $(COLLAR_DEPTH) tolerance $(TOLERANCE) gap $(GAP) pin_len $(PIN_LEN) '$$fn' $(FN)
	@echo
	@echo "  DERIVADOS (calculados pelo .scad, não ajustáveis)"
	@LC_NUMERIC=C awk -v h=$(HOLE_D) -v w=$(WALL) -v c=$(COLLAR_W) \
		-v cd=$(COLLAR_DEPTH) -v t=$(TOLERANCE) -v g=$(GAP) -v pl=$(PIN_LEN) 'BEGIN { \
		printf "    %-14s %s\n", "grid",     h + 2*(w+c); \
		printf "    %-14s %s\n", "recess_d", h + 2*c; \
		printf "    %-14s %s\n", "pin_d",    h - t; \
		printf "    %-14s %s\n", "collar_d", h + 2*c - t; \
		printf "    %-14s %s%s\n", "pin_len_max", h/2 + w + c - (h-t)/2, \
			(pl > h/2 + w + c - (h-t)/2) ? "   <-- pin_len ACIMA DO TETO" : ""; \
		printf "    %-14s %s\n", "lasca na quina", w; \
		printf "    %-14s %s\n", "alma entre furos", 2*w; }'
	@echo
	@echo "  PEÇAS      $(SELECTED)"
	@echo "  FUSION     add-in $(FUSION_ADDIN_SRC) | core $(FUSION_PY_CORE)"
	@echo "  SYSTEM_D   $(SYSTEM_D)"

endif
