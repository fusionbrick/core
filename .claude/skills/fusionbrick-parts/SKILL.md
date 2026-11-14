---
name: fusionbrick-parts
description: Use ao dimensionar, parametrizar, gerar ou variar peças FusionBrick em OpenSCAD — tamanho (cells/skin/spacer/arm_len), eixo vs. face, border_radius, presets, geração de STL/PNG com -D, e variantes persistidas via include. Triggers - "qual parâmetro muda o tamanho", "viga mais comprida", "eixo maior", "gerar variante", "peça não encaixa", "cells", "spacer", "skin", "bored", "recess", "border_radius", "make preview/build com parâmetro".
---

# FusionBrick — peças e parâmetros

Como dimensionar e gerar peças do sistema. Para sintaxe OpenSCAD genérica
(minkowski, customizer, CLI, colorschemes) use a skill **`openscad`** — esta
aqui cobre só o que é específico do FusionBrick.

## Nomes: duas camadas, uma ponte

Esta skill trata dos **parâmetros das peças no OpenSCAD** (`-D`), que mantêm os nomes do contrato. A montagem (`assembly.toml`, skill `fusionbrick-assembly`) usa o vocabulário público. É a mesma coisa com outra palavra:

| Na montagem (IR) | Aqui, no OpenSCAD |
| --- | --- |
| `stud` (pino impresso) · `socket` (encaixe) · `flat` (liso) | `pin` · `recess` · `plain` — os dois valem em qualquer `-D` |
| faces `front` `back` `left` `right` `top` `bottom` | `face_xp` `face_xn` `face_yp` `face_yn` `face_zp` `face_zn` |
| `size` · `holes` · `rounded` · `studs_on` | `cells_x/y/z` · `axis_x/y/z` (`bored`/`solid`) · `round_axis` · `pin_cells` |
| `beam`, `plate`, `cover` (variantes do bloco) | `brick.scad` com os parâmetros acima |
| `curve` com `radius` | `curve.scad` com `k = radius − 1` |
| cavilha | PIN de duas pontas: `pin.scad` com `ends = 2` |

"Macho" e "fêmea" nos comentários dos `.scad` são o pino e o encaixe. Tabela completa: `spec/assembly.md` § Nomes.

## Fonte de verdade — leia antes de decidir cotas

**Nunca assuma um valor de cabeça. Nunca copie um número deste arquivo para
código sem confirmar na fonte.** Os parâmetros mudam; esta skill aponta onde
eles vivem, não os congela.

| Pergunta | Onde está a resposta |
| --- | --- |
| Parâmetros globais do sistema | `spec/params.md` |
| Regras de compatibilidade, Grid Law, interfaces | `spec/rules.md` |
| Premissas do sistema | `spec/constitution.md` |
| **Cotas de uma peça convertida** | `spec/parts/<peça>/contracts.toml` — **fonte única**, verificada |
| Requisitos e critérios de aceite | `spec/parts/<peça>/spec.md` |
| **Contrato vs implementação bate?** | `make spec-check` |
| Intenção/geometria/limites de uma peça | `spec/parts/<peça>.md` |
| **Valor efetivo em uso** | `impl/openscad/<peça>.scad` (bloco de parâmetros no topo) |
| Config do pipeline e primitivos injetados | `hack/automations/variables.mk` |
| Config local da máquina | `.env` na raiz (ver `.env.example`) |
| **Config efetiva agora** | `make vars` |
| Receitas de render/export | `hack/automations/openscad.mk` |

Quando `spec/` e `impl/` divergirem, isso é um bug — reporte, não escolha em
silêncio. Para peça convertida, `make spec-check` detecta sozinho: ele confere
`contracts.toml` contra o core Python, os echos do OpenSCAD e o `make vars`.

Rode-o **antes e depois** de mexer em cota.

### Descobrir os parâmetros de uma peça

```bash
# Bloco de parâmetros com os ranges do Customizer
sed -n '1,120p' impl/openscad/pin.scad

# Só as linhas de parâmetro
grep -nE '^[a-z_]+ *= *[^;]+; *//' impl/openscad/pin.scad

# Assinatura dos módulos (o que aceita argumento vs. só global)
grep -nE '^module ' impl/openscad/pin.scad
```

### Confirmar a geometria REAL (não a esperada)

O `.scad` diz a intenção; o STL diz o que saiu. Divergiram várias vezes —
sempre meça quando for posicionar peça em assembly:

```bash
openscad -o /tmp/probe.stl --export-format binstl \
  -D 'cells_z=3' impl/openscad/brick.scad 2>&1 | grep ECHO
```

Todas as peças ecoam dimensões e checks de compatibilidade no final. **Leia os
echos** — eles respondem "isto ainda encaixa?" sem você ter que deduzir.

---

## Como cada peça muda de tamanho

Não existe parâmetro único de comprimento. Cada peça tem o seu, e algumas não
têm nenhum — o tamanho é derivado da interface.

| Peça | Parâmetro(s) de tamanho | Passo |
| --- | --- | --- |
| `brick` | `cells_x/y/z` | múltiplos de `grid` (8mm) |
| `brick` | `skin_x/y/z` | múltiplos da escala fina (2.5mm) |
| `brick` | `thickness` | **contínuo** — laje: fixa o Z em mm, fora do grid |
| `pin` | `spacer` | **contínuo** |
| `pin` | `size` | Ø do furo receptor (escala do macho) |
| `node` | `arm_len` | **contínuo** (0 = `grid/2`) |
| `dock` | `cells_x/y/z` + `skin_x/y/z` | grid + escala fina |

Consequência prática: para comprimento **arbitrário** só `pin` (`spacer`) e
`node` (`arm_len`). Blocos são travados no grid — é o Grid Law, não limitação.
O que passa disso é **pele** (`skin_*`), que não é comprimento de viga: é
material fora do volume de grid, e não move furo nenhum.

### Alongar um PIN (cavilha longa, eixo, afastador)

`spacer` insere comprimento **entre as duas pontas**, preservando o engate:

```bash
openscad -D 'spacer=8' -o eixo.stl --export-format binstl impl/openscad/pin.scad
```

Ressalvas:

- **`spacer` alonga o vão, não o engate.** `pin_len` é **contrato do sistema**
  (**declarado**, teto `grid/2 − pin_d/2`), não parâmetro da peça: macho mais
  longo entra fundo demais e colide com o perpendicular da célula receptora,
  quebrando o encaixe simultâneo. Mais comprimento = mais momento fletor com o
  mesmo engate.
- **`size` é o Ø do furo RECEPTOR, não do pino.** `pin_d` e `collar_d` saem
  dele com a folga descontada. Um macho para o furo do grid e um para o recurso
  central são a mesma peça com `size` diferente.

### Eixo vs. face no BRICK

O par que mais causa erro. São coisas separadas de propósito:

| | Escopo | Valores |
| --- | --- | --- |
| `axis_x/y/z` | o **furo passante**, por eixo | `bored` / `solid` |
| `face_xn` … `face_zp` | o **acabamento**, por face | `recess` / `pin` / `plain` |

Fundir os dois acoplaria faces opostas. `recess` numa face **exige** o eixo
correspondente `bored` (há `assert`). Presets cobrem os casos comuns:
`all_recess`, `all_pin`, `beam`, `corner_90`, `vertex_3`.

Isso decide quem é macho e quem é fêmea numa junção — o parâmetro mais
importante para montagem, e o mais fácil de esquecer.

---

## Encaixe — o que o teste de colisão NÃO pega

**Ausência de colisão não é encaixe.** Duas peças a 3mm uma da outra não
colidem e não conectam. Ao montar assembly, valide pino↔furo:

1. **Features ficam no CENTRO de cada célula, uma por célula por face.** Num
   bloco com pele zero, as posições ao longo de um eixo são
   `grid/2 + i·grid` — 4, 12, 20… Um `1×1×5` tem 5 posições por face lateral,
   não 2. Com `skin_*` tudo desloca: `skin + grid/2 + i·grid`.
2. **Peça encaixada tem a face ENCOSTADA na face da outra.** A distância entre
   centros é a soma das meias-seções, não meia-seção + folga a olho. O PIN
   some inteiro dentro dos dois rebaixos.
3. **A junção só existe se a posição cair num centro de célula real**, com a
   face macho apontando para a fêmea. Posição fora da malha não conecta —
   nada avisa, só não encaixa.
4. **Recurso central mata furos.** `alive()` filtra por distância: onde o
   macro alcança, não há furo, nem rebaixo, nem macho naquela face Z. Conte
   pelo echo `furos vivos`, não pelo `cells_x × cells_y`.
5. **Laje não tem furo de borda.** Com `thickness` abaixo de 7.2mm os eixos
   X/Y têm de ser `solid` (há `assert`) — não dá para pinar na lateral de um
   chão ou parede. Laje é face, nunca viga.

Confirme as cotas em `spec/rules.md` / `spec/parts/brick.md`, e os valores nos
echos do `.scad` — não neste texto.

---

## border_radius / border_style

Presente em quase toda peça: `border_radius` (0 = arestas vivas) e
`border_style` (`round` = esfera, `chamfer` = octaedro 45°), aplicados via
minkowski. Defaults variam por peça — confira no `.scad`.

- **`make preview` injeta um raio para os renders de documentação**; os
  defaults do `.scad` ficam como estão. Ver `openscad.mk`.
- **Minkowski com raio > 0 deixa o render MUITO mais lento.** Para iteração
  rápida use 0; suba só no export final.
- O raio é limitado pela seção (`safe_radius`) — pedir mais que metade da
  seção não estoura, satura.

---

## Gerar variantes

`-D` sobrepõe **qualquer** variável declarada no arquivo — inclusive as que
não são argumento de módulo.

```bash
# STL de uma variante
openscad -o out.stl --export-format binstl \
  -D 'cells_z=5' -D 'preset="beam"' -D 'border_radius=0.6' \
  impl/openscad/brick.scad

# PNG (precisa de --preview: color() é ignorado em --render)
openscad -o out.png --preview --colorscheme=Monotone \
  --projection=o --camera=0,0,0,54.7,0,45,500 --autocenter --viewall \
  -D 'spacer=8' impl/openscad/pin.scad
```

### Wireframe — exige `--render`, não `--preview`

`--view=wireframe` **falha em silêncio** com `--preview`. O comando roda,
não emite erro e devolve a imagem **sólida**. O export PNG usa Preview
(F5/OpenCSG) por padrão, e esse modo ignora as opções de view.

```bash
# ERRADO — devolve sólido, sem avisar
openscad --preview --view=wireframe -o out.png a.scad

# CERTO
openscad --render --view=wireframe --projection=o \
  --camera=0,0,0,54.7,0,45,500 --autocenter --viewall \
  --export-format png --imgsize=1100,800 -o out.png a.scad
```

Alvos prontos no Makefile: `make preview-wireframe` e
`make assembly-wireframe` — os dois já forçam `--render`.

Contrapartida: `--render` avalia a geometria inteira (CGAL) e é **bem mais
lento** que o preview. Em assembly grande, conte minutos. E `color()` é
ignorado nesse modo, então o wireframe sai monocromático.

Outras opções de `--view`: `axes`, `crosshairs`, `edges`, `scales`. O
`edges` funciona com `--preview` e só contorna as arestas — útil e barato,
mas não é wireframe.

Strings precisam de aspas **dentro** do `-D`: `-D 'preset="full_holes"'`.

### `make` aceita parâmetro?

Sim. **Toda** variável ajustável está em `hack/automations/variables.mk` —
`openscad.mk` só tem receitas. Principais:

| Variável | Para quê |
| --- | --- |
| `HOLE_D` `WALL` `COLLAR_W` `COLLAR_DEPTH` `TOLERANCE` `GAP` | os primitivos do sistema, injetados em **toda** chamada via `SYSTEM_D` |
| `FN` | facetas do círculo — baixe para iterar rápido |
| `PART` | roda **uma** peça (ou lista) em vez de varrer o diretório |
| `EXTRA_D` | repassa `-D` arbitrário; tem a última palavra |
| `IMPL_DIR` / `IMG_DIR` / `STL_DIR` | diretórios de entrada e saída |
| `PART_COLOR` / `BORDER_RADIUS` / `BORDER_STYLE` | cotas cabeadas nos alvos |

```bash
make vars                                  # config efetiva + derivados
make build PART=brick
make build PART=brick EXTRA_D='-D cells_z=5'
make build TOLERANCE=0.15                  # calibrar encaixe p/ a impressora
make preview IMPL_DIR=experiments/x IMG_DIR=experiments/x/img
```

**Antes de gerar qualquer coisa, rode `make vars`.** Ele mostra a config
efetiva *e* os derivados (`grid`, `recess_d`, `pin_d`, `pin_len`), então
responde "que sistema vou gerar?" sem abrir arquivo.

Precedência (menor → maior): default do `.scad` < `variables.mk` < `.env` na
raiz < variável de linha < `EXTRA_D`. O `.env` é gitignored e lido como
makefile — `CHAVE=valor`, sem aspas, sem `export`. Ver `.env.example`.

**Não existe `GRID` ajustável.** É derivado (`hole_d + 2·(wall + collar_w)`).
Se alguém pedir "muda o grid para 10", o caminho é mexer em `HOLE_D`/`WALL`,
não inventar a variável.

**Testar `-D` sem destruir o catálogo**: os alvos escrevem em `renders/`.
Redirecione com `STL_DIR=`/`IMG_DIR=` ao experimentar, senão o `make build`
sobrescreve o STL versionado da peça com a sua variante.

**Pegadinha das strings — falha quase silenciosa.** O `$(EXTRA_D)` é expandido
dentro da receita, e o shell da receita consome as aspas. String sem escape
chega ao openscad como variável indefinida:

```bash
# ERRADO — vira -D preset=full_holes, sem aspas
make build PART=pin EXTRA_D='-D preset="full_holes"'
#   WARNING: Ignoring unknown variable 'full_holes'   ← e usa o default

# CERTO — o \" sobrevive até o openscad
make build PART=brick EXTRA_D='-D preset=\"beam\"'
```

**Pegadinha do `$fn` — escape duplo.** O `$` é significativo para o make *e*
para o shell. `EXTRA_D='-D $fn=64'` vira `-D n=64` (o make come `$f`);
`'-D $$fn=64'` vira `-D =64` (o shell expande `$fn`, que é vazio). Nenhum dos
dois avisa.

```bash
make build FN=16                     # use isto
make build EXTRA_D='-D \$$fn=16'     # só se não houver alternativa
```

O WARNING é a única pista, e passa fácil no meio do log de render. Números não
têm esse problema (`-D cells=5` funciona direto).

Sem `PART`, os alvos **iteram sobre todas as peças** do `IMPL_DIR`, então um
`EXTRA_D` global se aplica a peças que ignoram a variável — inofensivo, mas é
por isso que `PART` existe.

**Para uma variante virar peça de primeira classe** (preview + STL
automáticos, versionada), crie um `.scad` fino — o wildcard a inclui sozinha.
Padrão existente: `impl/openscad/hub.scad`.

Use **`include`**, não `use`:

```openscad
include <brick.scad>

cells_x = 3;
cells_y = 3;
cells_z = 3;
center      = "hole";
center_size = 10;
// SEM chamada de render: quem desenha é o topo de brick.scad,
// já executando com estes valores.
```

`include` cola o arquivo inteiro; a reatribuição posterior **vence** (último
valor ganha) e os derivados recomputam — `grid`, `total_x`, tudo. O módulo
enxerga os valores novos:

```
$ openscad -o /dev/null hub.scad
ECHO: "Bloco       24 × 24 × 24mm (3×3×3 células + pele 0/0/0)"
```

Como `include` também executa o topo do arquivo base, a variante **não** chama
o módulo — isso renderizaria duas vezes.

**Armadilha da ordem — falha silenciosa.** Uma reatribuição só pode usar
literais ou variáveis que já existam ANTES do `include`. Ao reatribuir uma
variável do arquivo base, o OpenSCAD avalia a atribuição vencedora no ponto da
declaração **original** — dentro do arquivo incluído. Variável nova declarada
depois do include ainda não existe lá:

```openscad
include <brick.scad>
sided     = 2;
thickness = sided == 2 ? 4 : 2;   // vira 2, nao 4
```
```
WARNING: thickness was assigned on line 71 but was overwritten
WARNING: Ignoring unknown variable 'sided'
```

Exit 0, peça gerada com o valor errado. A correção é declarar a variável nova
**antes** do `include` (ver `impl/openscad/plate.scad`).

**Pegadinha do `use <>` — falha silenciosa**: ele importa **módulos, não
variáveis globais**, com os parâmetros congelados no default do arquivo de
origem. Passar um parâmetro que não está na assinatura do módulo **não gera
erro**: o OpenSCAD emite um WARNING e **ignora o valor**.

```
$ openscad -o out.stl t-spacer.scad     # com `brick(cells_x = 3)`
WARNING: variable cells_x not specified as parameter in file t-spacer.scad, line 2
--- exit: 0
```

Exit 0, STL gerado, valor ignorado — você recebe a peça default achando que a
configurou. Só dá para variar por argumento o que o `module` declara:

```bash
grep -nE '^module ' impl/openscad/brick.scad
```

`use <>` continua certo para **assembly**, onde se quer instanciar a peça
várias vezes com o default. Para reconfigurar, é `include`.

---

## Ao mudar qualquer coisa

Regra do projeto: **mudança propaga para `spec/`, `impl/`, docs, automações e
READMEs**. Uma cota alterada só no `.scad` deixa a spec mentindo.

Checklist:

1. `spec/params.md` ou `spec/parts/<peça>.md` — a regra
2. `impl/openscad/<peça>.scad` — o valor + echo de compatibilidade
3. `README.md` — se a peça é listada
4. `hack/automations/openscad.mk` — se virou parâmetro de build
5. `make preview` / `make build` — regenerar artefatos afetados
6. Peças que **compartilham** o parâmetro (interface de face/borda é comum a
   várias) — senão os furos deixam de alinhar
