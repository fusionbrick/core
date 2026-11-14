# FusionBrick — wiki do repositório

FusionBrick é um **sistema de design mecânico paramétrico** para impressão 3D FDM: um conjunto pequeno de peças que encaixam por press-fit em qualquer face, sem parafusos e sem ferramentas. O repositório não contém aplicação executável — ele contém a **especificação do sistema**, a **implementação em OpenSCAD** de cada peça, as **montagens de exemplo** e a **automação Make** que transforma tudo isso em imagens, GIFs, MP4 e STLs.

O contrato do sistema está em [`../../spec/design-system.md`](../../spec/design-system.md) (premissas), [`../../spec/params.md`](../../spec/params.md) (parâmetros globais) e [`../../spec/rules.md`](../../spec/rules.md) (Lei do Grid e interfaces). A tradução desse contrato em geometria está em `../../impl/openscad/` — um arquivo `.scad` por peça.

## Em uma passada: como o sistema funciona

- **Grid de 20 mm.** `cell_size = 20` é o passo de tudo (`../../spec/params.md`). Nenhuma junção pode alterá-lo.
- **Duas interfaces que não competem.** Face (furo `Ø10` + rebaixo `Ø14 × 2`) para LINK, empilhamento e módulos; borda (furo `Ø3 × 4` nas extremidades das células) para junções estruturais. Montar uma junção nunca consome furo de face — ver [Peças e interfaces](pecas.md).
- **Tolerância só no conector.** `tolerance = 0.2` é subtraída do pino/flange, nunca da peça receptora: `pin_d = 9.8`, `flange_d = 13.8`, pino de borda `Ø2.8`.
- **Passagem de fio por padrão.** Todo conector nasce com canal axial (`canal_d = 6` no LINK, `3` no CORNER); fechar é opt-in.
- **Spec-first.** Divergência entre `spec/` e `impl/` é bug da implementação — ver as divergências reais já detectadas em [Arquitetura](arquitetura.md#divergências-entre-documentação-e-código).

## Primeiros passos

Requisitos verificáveis no repositório: `openscad 2021.01` e `ffmpeg 8.1.2` estão fixados em `.tool-versions`; `magick` (ImageMagick 7) é exigido pelas receitas de `hack/automations/openscad.mk` mas não é fixado em nenhum manifest.

```bash
asdf install                 # instala as versões de .tool-versions
make preview                 # renders/img/<peça>.png para cada impl/openscad/*.scad
make build                   # renders/stl/<peça>.stl para cada impl/openscad/*.scad
make assembly                # examples/*/assembly.png e assembly-exploded.png
```

Para inspecionar ou alterar uma peça, abra o `.scad` correspondente no OpenSCAD: os parâmetros estão no topo do arquivo com faixas de customizer (ex.: `atom_size = 20; // [5:1:100]`), e cada arquivo termina em `echo(...)` que imprime dimensões e verificações de compatibilidade no console. O detalhe de cada comando, variável e artefato está em [Operações](operacoes.md); a estratégia de validação (não há framework de testes) está em [Testes](testes.md).

## Navegação

- [Arquitetura](arquitetura.md) — separação spec/impl, pipeline Make, convenções dos arquivos `.scad`, sistemas de coordenadas e divergências conhecidas.
- [Peças e interfaces](pecas.md) — catálogo das 11 peças de `impl/openscad/`, o que cada uma resolve, as duas interfaces de encaixe e as regras de compatibilidade.
- [Operações](operacoes.md) — dependências, targets e variáveis do `Makefile`, pipeline de render, artefatos gerados.
- [Testes](testes.md) — asserções por `echo`, teste de colisão por `intersection()`, validação visual e limites dessa abordagem.

## Onde cada coisa vive

| Caminho | Conteúdo |
| --- | --- |
| `../../spec/` | Contrato independente de ferramenta: premissas, parâmetros globais, regras e uma spec por peça em `spec/parts/`. |
| `../../impl/openscad/` | Implementação OpenSCAD: um arquivo por peça, parametrizado e com asserções em `echo`. |
| `../../hack/automations/` | `core.mk` (roteamento `openscad-%`) e `openscad.mk` (toda a lógica de render/export). |
| `../../examples/` | Montagens programáticas (`assembly.scad`) que usam `use <>` das peças e servem de teste de encaixe. |
| `../../renders/` | Artefatos versionados: `img/` (PNG/GIF) e `stl/`. |
| `../../.claude/skills/fusionbrick-builder/SKILL.md` | Instruções de agente para construir novas montagens sobre as peças existentes. |
