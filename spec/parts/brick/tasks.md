# BRICK — tasks

Formato do [GitHub Spec Kit](https://github.com/github/spec-kit): `T### [P] descrição`.
`[P]` = paralelizável (arquivos distintos, sem dependência).

Requisitos em [`spec.md`](spec.md) · Lacunas em [`plan.md`](plan.md)

---

## Concluído

- [x] **T001** Contrato em `spec/parts/brick/contracts.toml`
- [x] **T002** `make spec-check` conferindo contrato vs core Python, OpenSCAD e make
- [x] **T003** Geometria OpenSCAD completa — `impl/openscad/brick.scad`
- [x] **T004** Core Python: primitivos, derivados, invariantes — `impl/python/fusionbrick/params.py`
- [x] **T005** Validações do core — `impl/python/fusionbrick/rules.py`
- [x] **T006** Descrição de geometria sem CAD — `impl/python/fusionbrick/brick.py`
- [x] **T007** 19 testes do core — `impl/python/tests/test_core.py`
- [x] **T008** Variantes HUB e PLATE via `include`
- [x] **T009** Add-in do Fusion gerando a célula `1×1×1` com User Parameters
- [x] **T010** Premissa 5 da constituição corrigida (`pin_len` declarado, não derivado)
- [x] **T011** `params.scad` compartilhado — 28 declarações de primitivo viraram 7
- [x] **T012** Poda do BRICK pelo conselho — 22 → 15 parâmetros, geometria idêntica

## Pendente

### Fusion 360

- [ ] **T020** Células múltiplas (`cells_x/y/z`) no diálogo e na geometria
- [ ] **T021** `[P]` Eixos `bored`/`solid` e faces `recess`/`pin`/`plain`
- [ ] **T022** `[P]` Modo laje (`thickness`)
- [ ] **T023** Recurso central
- [ ] **T024** `executePreview` — desenhar enquanto o usuário digita

### Geometria

- [ ] **T030** `center_axes` — recurso central nos 3 eixos, para reproduzir o ATOM

### Verificação

- [ ] **T040** Automatizar AC-012 (encaixe simultâneo nas 6 faces) como teste de interseção
- [ ] **T041** `[P]` Calibrar `tolerance` contra impressão real — AC-013
- [ ] **T042** Gerar `variables.mk` e `params.py` a partir do contrato, tornando a divergência impossível
