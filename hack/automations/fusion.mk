SHELL := /bin/bash

# Configuração inteira em variables.mk — aqui só receitas.
include $(dir $(lastword $(MAKEFILE_LIST)))variables.mk

# ============================================================
# fusion.mk — add-in do Fusion 360
# ============================================================
# Desenvolvimento usa SYMLINK, não cópia: você edita no repo e o
# Fusion carrega a versão nova ao dar Stop → Run no add-in.
#
# Copiar quebraria o import do core. O add-in acha `impl/python/`
# subindo dois níveis a partir da própria pasta; fora do repo esse
# caminho não existe. Para distribuir existe `fusion-vendor`, que
# empacota o core DENTRO da pasta do add-in.
#
# PASSO A PASSO DE DESENVOLVIMENTO: fusion.md (nesta pasta)
# ============================================================

# Resolve a pasta de add-ins no shell — o caminho tem espaços e o
# nome mudou entre versões do Fusion.
define FUSION_RESOLVE
dir="$(FUSION_ADDINS_DIR)"; \
if [ -z "$$dir" ]; then \
  for c in "$$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns" \
           "$$HOME/Library/Application Support/Autodesk/Autodesk Fusion/API/AddIns" \
           "$$APPDATA/Autodesk/Autodesk Fusion 360/API/AddIns" \
           "$$APPDATA/Autodesk/Autodesk Fusion/API/AddIns"; do \
    if [ -d "$$c" ]; then dir="$$c"; break; fi; \
  done; \
fi; \
link="$$dir/$(FUSION_ADDIN_NAME)"; \
src="$(CURDIR)/$(FUSION_ADDIN_SRC)";
endef

.PHONY: fusion-status fusion-link fusion-unlink fusion-test fusion-check fusion-vendor fusion-help

fusion-help:
	@echo "  make fusion-status   estado da instalação"
	@echo "  make fusion-link     symlink do add-in (desenvolvimento)"
	@echo "  make fusion-unlink   remove o symlink"
	@echo "  make fusion-test     testes do core Python"
	@echo "  make fusion-check    sintaxe do add-in + manifest"
	@echo "  make fusion-vendor   empacota para distribuição"

fusion-status:
	@$(FUSION_RESOLVE) \
	if [ -z "$$dir" ]; then \
	  echo "  pasta de add-ins : NÃO ENCONTRADA"; \
	  echo "  o Fusion está instalado? Defina FUSION_ADDINS_DIR para forçar."; \
	  exit 0; \
	fi; \
	echo "  pasta de add-ins : $$dir"; \
	echo "  fonte no repo    : $$src"; \
	if [ -L "$$link" ]; then \
	  t=$$(readlink "$$link"); \
	  if [ "$$t" = "$$src" ]; then echo "  instalação       : SYMLINK ok -> $$t"; \
	  else echo "  instalação       : symlink para OUTRO lugar -> $$t"; fi; \
	elif [ -d "$$link" ]; then \
	  echo "  instalação       : DIRETÓRIO REAL (cópia) — o import do core não funciona daí"; \
	elif [ -e "$$link" ]; then \
	  echo "  instalação       : existe mas não é pasta nem link"; \
	else \
	  echo "  instalação       : ausente — rode 'make fusion-link'"; \
	fi

fusion-link:
	@$(FUSION_RESOLVE) \
	if [ -z "$$dir" ]; then \
	  echo "ERRO: pasta de add-ins do Fusion não encontrada."; \
	  echo "      Defina FUSION_ADDINS_DIR=/caminho para forçar."; exit 1; \
	fi; \
	if [ ! -d "$$src" ]; then echo "ERRO: fonte não existe: $$src"; exit 1; fi; \
	if [ -L "$$link" ]; then \
	  rm "$$link"; \
	elif [ -e "$$link" ]; then \
	  echo "ERRO: já existe algo que NÃO é symlink em:"; \
	  echo "      $$link"; \
	  echo "      Não vou apagar — mova ou remova à mão antes."; exit 1; \
	fi; \
	ln -s "$$src" "$$link"; \
	echo "LINK $(FUSION_ADDIN_NAME)"; \
	echo "  -> $$link"; \
	echo "  Fusion: Tools → Add-Ins → $(FUSION_ADDIN_NAME) → Run"

# Só remove SYMLINK. Nunca apaga diretório real — se alguém copiou
# o add-in à mão, apagar aqui destruiria trabalho.
fusion-unlink:
	@$(FUSION_RESOLVE) \
	if [ -L "$$link" ]; then rm "$$link"; echo "UNLINK $$link"; \
	elif [ -d "$$link" ]; then \
	  echo "AVISO: $$link é diretório real, não symlink. Não removi."; \
	else echo "nada a remover em $$link"; fi

fusion-test:
	@cd $(FUSION_PY_CORE) && $(FUSION_PYTHON) -m unittest discover -s tests -v
	@echo "-> $(FUSION_PY_CORE)/tests"

# A API `adsk` só existe dentro do Fusion, então não dá para
# importar o add-in aqui. O que dá para verificar sem o Fusion é
# sintaxe e o JSON do manifest — pega erro de digitação antes de
# abrir o programa.
fusion-check:
	@$(FUSION_PYTHON) hack/scripts/fusion_check.py $(FUSION_ADDIN_SRC)
	@$(FUSION_PYTHON) hack/scripts/fusion_api_check.py $(FUSION_ADDIN_SRC)
	@$(FUSION_RESOLVE) \
	$(FUSION_PYTHON) hack/scripts/fusion_core_resolve.py "$$link"
	@echo "-> $(FUSION_ADDIN_SRC)"

# Empacota para distribuição: o core vai DENTRO da pasta do add-in,
# então funciona copiado, sem depender do repo.
fusion-vendor:
	@rm -rf $(FUSION_DIST_DIR)/$(FUSION_ADDIN_NAME)
	@mkdir -p $(FUSION_DIST_DIR)/$(FUSION_ADDIN_NAME)
	@cp $(FUSION_ADDIN_SRC)/*.py $(FUSION_ADDIN_SRC)/*.manifest \
	    $(FUSION_DIST_DIR)/$(FUSION_ADDIN_NAME)/
	@cp -R $(FUSION_PY_CORE)/fusionbrick $(FUSION_DIST_DIR)/$(FUSION_ADDIN_NAME)/
	@find $(FUSION_DIST_DIR) -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "VENDOR $(FUSION_ADDIN_NAME)  (core embutido)"
	@echo "-> $(FUSION_DIST_DIR)/$(FUSION_ADDIN_NAME)"
