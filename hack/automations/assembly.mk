SHELL := /bin/bash

# Configuração inteira em variables.mk — aqui só receitas.
include $(dir $(lastword $(MAKEFILE_LIST)))variables.mk

# ============================================================
# assembly.mk — montagem a partir de assembly.toml
# ============================================================
# A montagem é DESCRITA em examples/<nome>/assembly.toml (peças em
# células) e COMPILADA: o compilador insere as cavilhas, aplica as
# regras ASM-### e gera assembly.scad, BOM, passos e STLs.
#
# Regras: spec/assembly.md · Skill: .claude/skills/fusionbrick-assembly/
# ============================================================

.PHONY: assemble assemble-check assemble-stats assemble-review assemble-all assemble-test assemble-collide assemble-help

ASM_TOMLS = $(wildcard examples/*/assembly.toml)
ASM_FN   ?= $(FN)

assemble-help:
	@echo "  make assemble NAME=<x>        check + STLs + .scad + BOM + passos + PNGs"
	@echo "  make assemble-check NAME=<x>  só valida (milissegundos)"
	@echo "  make assemble-stats NAME=<x>  qualidade: resolução, cavilhas, reuso, maior peça"
	@echo "  make assemble-review NAME=<x> ficha de qualidade: todos os portões medidos do conselho"
	@echo "  make assemble-all             todas as examples/*/assembly.toml"
	@echo "  make assemble-test            testes do compilador"
	@echo "  make assemble-collide NAME=<x> interseção EXATA (CGAL) par a par — lento"

_need_name:
	@if [ -z "$(NAME)" ]; then echo "use: make $(MAKECMDGOALS) NAME=<pasta em examples/>"; \
	  echo "  disponíveis: $(notdir $(patsubst %/,%,$(dir $(ASM_TOMLS))))"; exit 2; fi

assemble: _need_name
	@$(FUSION_PYTHON) hack/scripts/fb_assemble.py build examples/$(NAME)/assembly.toml --png --fn $(ASM_FN)

assemble-check: _need_name
	@$(FUSION_PYTHON) hack/scripts/fb_assemble.py check examples/$(NAME)/assembly.toml

assemble-stats: _need_name
	@$(FUSION_PYTHON) hack/scripts/fb_assemble.py stats examples/$(NAME)/assembly.toml

assemble-review: _need_name
	@$(FUSION_PYTHON) hack/scripts/fb_assemble.py review examples/$(NAME)/assembly.toml

assemble-all:
	@for f in $(ASM_TOMLS); do \
	  $(FUSION_PYTHON) hack/scripts/fb_assemble.py build $$f --png --fn $(ASM_FN) || exit 1; done

assemble-test:
	@cd impl/python && $(FUSION_PYTHON) -m unittest tests.test_assembly tests.test_irgen -v

# Verificação INDEPENDENTE: interseção CGAL de cada par vizinho a
# partir dos STLs reais. O compilador decide por regra; isto confere
# a geometria. Rode depois de `make assemble`.
assemble-collide: _need_name
	@$(FUSION_PYTHON) hack/scripts/fb_collide.py examples/$(NAME)/assembly.scad
