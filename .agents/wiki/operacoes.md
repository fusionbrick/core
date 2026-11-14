# Operações

Não há serviço para subir: "operar" este repositório significa **gerar artefatos** (PNG, GIF, MP4, STL) a partir dos `.scad` e imprimir as peças. Toda a operação passa pelo `Makefile` da raiz.

## Dependências

| Ferramenta | Evidência | Usada por |
| --- | --- | --- |
| `openscad` | `.tool-versions` fixa `openscad 2021.01`; variável `OPENSCAD` em `hack/automations/openscad.mk` | todos os targets |
| `magick` (ImageMagick 7) | variável `MAGICK` em `openscad.mk` | `preview`, `preview-animated`, `assembly-animated` — **não fixada** em nenhum manifest |
| `ffmpeg` | `.tool-versions` fixa `ffmpeg 8.1.2`; variável `FFMPEG` em `openscad.mk` | apenas `assembly-video` |

O `README.md` documenta a instalação via asdf (`asdf plugin add openscad https://github.com/gabrielelana/asdf-openscad` seguido de `asdf install`) ou download direto do OpenSCAD. Para a impressão em si, o `README.md` declara os requisitos de hardware/material: impressora FDM com PLA ou PETG.

Não existem variáveis de ambiente próprias do projeto, arquivos `.env` ou credenciais: a configuração é feita passando variáveis do Make na linha de comando.

## Roteamento dos targets

```text
Makefile  →  hack/automations/core.mk  →  hack/automations/openscad.mk
```

O `Makefile` da raiz apenas calcula `ROOT_DIR` e inclui `core.mk`. `core.mk` inclui `openscad.mk` (por isso os targets ficam disponíveis sem prefixo) e define a regra `openscad-%`, que reinvoca o make com `-f hack/automations/openscad.mk` no alvo correspondente. Ou seja, `make preview` e `make openscad-preview` executam a mesma receita; o segundo formato é o namespace explícito para o dia em que outra implementação for adicionada.

O trabalho é descoberto por wildcard: `PARTS` vem de `impl/openscad/*.scad` e `ASSEMBLIES` de `examples/*/assembly.scad`. Nenhum target precisa ser editado ao adicionar peça ou montagem.

## Targets

| Comando | O que faz | Saída |
| --- | --- | --- |
| `make preview` | Renderiza cada peça em PNG isométrico (`--preview`, `--colorscheme=Monotone`, `800,600`) injetando `part_color`, e usa `magick` para amostrar o pixel `[0,0]` e tornar o fundo transparente com `-fuzz 2%` | `renders/img/<peça>.png` |
| `make preview-animated` | `ANIM_FRAMES` renders girando o azimute (`ISO_AZIM + i*360/ANIM_FRAMES`), cada frame com fundo removido, montados em GIF com `-loop 0 -dispose Background` | `renders/img/<peça>.gif` |
| `make build` | Exporta STL binário de cada peça, injetando `border_radius`/`border_style` | `renders/stl/<peça>.stl` |
| `make assembly` | Para cada montagem, dois renders isométricos em `1200,900`: normal e com `-D explode=12` | `examples/<nome>/assembly.png` e `assembly-exploded.png` |
| `make assembly-animated` | Boomerang de explode/recolhe (loop perfeito) montado em GIF | `examples/<nome>/assembly.gif` |
| `make assembly-video` | Mesmos frames do boomerang codificados em H.264 (`format=yuv420p`, `+faststart`) | `examples/<nome>/assembly.mp4` |
| `make openscad-preview`, `make openscad-build` | Aliases explícitos das receitas acima | idem |

Comportamento a conhecer: `preview`, `preview-animated`, `assembly` e as receitas de animação imprimem `SKIP <alvo> (render failed)` e seguem para o próximo item quando o OpenSCAD falha; a receita `build` não tem essa guarda, então uma peça que não renderiza deixa um STL ausente ou incompleto sem interromper o laço.

## Variáveis de configuração

Todas são sobrescritas na linha de comando (`make preview PART_COLOR="[0.8, 0.2, 0.1]"`). Defaults em `hack/automations/openscad.mk`:

| Variável | Default | Efeito |
| --- | --- | --- |
| `PART_COLOR` | `[0.35, 0.38, 0.42]` | cor injetada por `-D part_color` no preview (RGB 0.0–1.0) |
| `COLORSCHEME` | `Monotone` | esquema de cores do OpenSCAD nos previews de peça |
| `IMGSIZE` / `ASM_IMGSIZE` | `800,600` / `1200,900` | resolução de peças / montagens |
| `ISO_ELEV`, `ISO_AZIM` | `54.7`, `45` | ângulo isométrico; compõem `ISO_CAMERA` com `--projection=o --autocenter --viewall` |
| `ANIM_FRAMES`, `ANIM_DELAY` | `36`, `15` | frames por volta e delay (1/100 s) do GIF de peça |
| `BORDER_RADIUS`, `BORDER_STYLE` | `0`, `round` | acabamento de aresta injetado **só** no `build`; `> 0` usa `minkowski()` e deixa o render bem mais lento |
| `ASM_ANIM_FRAMES`, `ASM_ANIM_DELAY` | `72`, `5` | frames do loop e delay da animação de montagem |
| `ASM_ANIM_EXPLODE` | `12` | afastamento máximo em mm no boomerang |
| `ASM_ANIM_SPIN` | `0` | graus de giro no loop; `0` mantém a câmera isométrica fixa e anima só o explode |
| `ASM_ANIM_SPEED` | `1` | multiplicador de velocidade: divide o delay do GIF (mínimo 1) e multiplica o fps do MP4 |
| `ASM_VIDEO_FPS` | `30` | frame rate base do MP4 |
| `STL_DIR`, `IMG_DIR`, `IMPL_DIR` | `renders/stl`, `renders/img`, `impl/openscad` | diretórios de origem e destino |

`IMG_W`, `IMG_H`, `GRAD_TOP` e `GRAD_BOT` também estão definidas, mas nenhuma receita as usa.

## Como a animação de montagem é construída

`assembly-animated` e `assembly-video` compartilham o `define ASM_RENDER_FRAMES`, que renderiza os frames uma única vez de forma idêntica para os dois formatos. Para cada frame `i`:

- `frac = (1 − cos(2π·i/n)) / 2` e `explode = frac × ASM_ANIM_EXPLODE` — a montagem abre e fecha suavemente, e como a função fecha o ciclo em `n` frames o loop é perfeito;
- `rot = ISO_AZIM + i × ASM_ANIM_SPIN / n` — com o default `ASM_ANIM_SPIN = 0` a câmera não gira.

Os cálculos em ponto flutuante são feitos com `awk` sob `LC_NUMERIC=C` para não depender do locale da máquina. Os frames vão para um `mktemp -d` e são removidos ao final; só o GIF ou o MP4 sobrevivem.

## Fluxo manual no OpenSCAD

O caminho sem Make, descrito no `README.md`: abrir o `.scad` da peça, ajustar os parâmetros no painel do customizer (as faixas `// [min:step:max]` de cada declaração alimentam esse painel), `F6` para render completo e `File → Export → Export as STL`.

Atenção a duas armadilhas de preview: `color()` só tem efeito em `--preview`/`F5`, não em render completo; e `intersection()` entre módulos — base do teste de colisão — só é calculado no render completo, nunca no preview (ver [Testes](testes.md)).

## Artefatos versionados

`renders/img/` e `renders/stl/` guardam os resultados de `preview`, `preview-animated` e `build` para 9 das 11 peças — as 8 com spec em `spec/parts/` mais `link-oneside`, faltando `track` e `wheel`; `examples/<nome>/` guarda os stills e a animação de cada montagem, e `examples/u-channel/assembly.mp4` é o único MP4 versionado. Como esses arquivos binários entram no histórico, regenerar tudo produz diffs grandes — vale regerar apenas o que a mudança afeta.

## Observabilidade

Não há framework de log nem métricas: o retorno é o stdout/stderr do processo. As receitas imprimem progresso (`STL <peça>`, `ANIMATE <peça>`, `ASSEMBLY <dir>`, `VIDEO ASSEMBLY <dir>`, `-> <arquivo>`) e cada `.scad` imprime, via `echo`, dimensões calculadas e verificações de compatibilidade. Note que `preview-animated` e o render de frames de montagem usam `2>/dev/null`, o que **descarta** essas mensagens; para lê-las, use `make preview` ou execute o OpenSCAD diretamente sobre o arquivo.
