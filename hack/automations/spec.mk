SHELL := /bin/bash

# Configuração inteira em variables.mk — aqui só receitas.
include $(dir $(lastword $(MAKEFILE_LIST)))variables.mk

# ============================================================
# spec.mk — spec-driven development
# ============================================================
# `spec/parts/<peça>/contracts.toml` é a FONTE ÚNICA das cotas.
# `spec-check` confere contra o core Python, os echos do OpenSCAD
# e o `make vars`.
#
# Existe porque as fórmulas de derivação estavam escritas à mão em
# quatro lugares e divergiram sem ninguém notar. Divergência entre
# contrato e implementação é BUG, não escolha.
#
# PASSO A PASSO: spec/README.md
# ============================================================

.PHONY: spec-check spec-docs spec-status spec-help

spec-help:
	@echo "  make spec-check              confere contrato vs implementações"
	@echo "  make spec-check PART=brick   uma peça só"
	@echo "  make spec-docs               regenera as tabelas de spec/params.md a partir do contrato"
	@echo "  make spec-status             quais peças estão convertidas"

# Peças com pasta spec-driven (têm contracts.toml)
SPEC_PARTS = $(notdir $(patsubst %/contracts.toml,%,$(wildcard spec/parts/*/contracts.toml)))
SPEC_SELECTED = $(if $(PART),$(PART),$(SPEC_PARTS))

spec-docs:
	@$(FUSION_PYTHON) hack/scripts/spec_docs.py

spec-check:
	@$(FUSION_PYTHON) hack/scripts/spec_check.py $(SPEC_SELECTED)
	@$(FUSION_PYTHON) hack/scripts/spec_docs.py --check
	@echo "-> spec/parts/{$(shell echo '$(SPEC_SELECTED)' | tr ' ' ',')}/contracts.toml"

spec-status:
	@echo "  convertidas (spec-driven):"
	@for p in $(SPEC_PARTS); do echo "    $$p  spec/parts/$$p/"; done
	@echo "  ainda em arquivo único:"
	@for f in $(wildcard spec/parts/*.md); do \
	  echo "    $$(basename $$f .md)  $$f"; done
	@echo
	@echo "  constituição: spec/constitution.md"
	@echo "  formato:      spec/README.md"
