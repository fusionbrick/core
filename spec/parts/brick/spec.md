# BRICK — especificação

O bloco universal. Ocupa células do grid e é sempre **ortogonal**.

Absorve o que antes eram cinco peças: ATOM, PLATE, viga, quina e vértice. Todas eram o mesmo objeto — um bloco de `n` células com furos e machos em faces diferentes.

| | |
| --- | --- |
| Cotas | [`contracts.toml`](contracts.toml) — **fonte única**, verificada por `make spec-check` |
| Premissas | [`../../constitution.md`](../../constitution.md) |
| Compatibilidade | [`../../rules.md`](../../rules.md) |
| Implementações | [`plan.md`](plan.md) · status em [`tasks.md`](tasks.md) |
| Constitution Check | [`checklist.md`](checklist.md) |

> Nenhum número deste arquivo é digitado à mão. Se um valor aqui divergir de `contracts.toml`, o contrato manda.

---

## Requisitos

**REQ-001** — O BRICK MUST ocupar um volume de `cells_x × cells_y × cells_z` células, com cada aresta valendo `grid`.

**REQ-002** — Cada **eixo** MUST ser `bored` (furo passante no centro de cada célula) ou `solid`. O furo, quando existe, MUST atravessar a peça inteira — não há furo cego.

**REQ-003** — Cada **face** MUST ter acabamento `recess`, `pin` ou `plain`, independente das demais. O padrão é `auto`, que resolve para `recess` com o eixo `bored` e `plain` com o eixo `solid`.

**REQ-004** — Eixo e face MUST ser camadas separadas. Tratar "furo" como propriedade de face abriria a face oposta à revelia dela, porque o furo é passante.

**REQ-005** — Uma face `recess` MUST exigir o eixo correspondente `bored`. Rebaixo sem furo é bolso cego: aceita o colar de um macho que não tem o que agarrar. `recess` **declarado** num eixo `solid` é erro no core e no OpenSCAD; `auto` nunca cai nesse caso.

**REQ-006** — Uma célula 1×1 toda fêmea MUST aceitar macho nas 6 faces simultaneamente, sem que um invada o espaço do outro (constituição § 5).

**REQ-007** — Material de acabamento fora do volume de grid MUST andar na escala fina, nunca deslocando furo (Lei do Grid). O BRICK **não** expõe `skin`: quem precisa é o [DOCK](../dock.md), que hospeda dispositivo de dimensão arbitrária.

**REQ-008** — Com `thickness > 0` o BRICK MUST virar **laje**: extensão em Z livre do grid, sem furo de borda.

**REQ-009** — O recurso central, quando presente, MUST eliminar os furos de grid que alcança — e com eles o rebaixo e o macho daquela face.

---

## Geometria

Bloco de `cells_x × cells_y × cells_z` células. Nada fora disso — acabamento fora do grid é assunto do DOCK.

Posições ao longo de um eixo: `grid/2 + i·grid`. Com grid de 8mm: **4, 12, 20…**

### O que ele vira

| Antes | Configuração |
| --- | --- |
| ATOM | `1×1×1`, eixos `bored`, faces `recess` |
| PLATE `n×m` | `n×m×1` |
| Viga de `n` células | `1×1×n`, eixo longo `bored`, laterais `solid` |
| CORNER | `1×1×n` com duas faces adjacentes `pin` |
| VERTEX | `1×1×1`, eixos `solid`, três faces `pin` |
| União 90° / 180° / 6 vias | `1×1×1` com as faces correspondentes `pin` |

**Toda união ortogonal é um BRICK.** Só ângulo não-ortogonal precisa de [NODE](../node.md) — as portas de uma união a 90° caem exatamente nos centros de face da célula.

### O que sobra quando tudo é vazado

Com os três eixos `bored`, os furos se cruzam no centro e sobra a **gaiola das 12 arestas**, de seção `edge_bar`. É o caso extremo: se a célula sobrevive assim, qualquer configuração sobrevive.

### Economia de material

`solid` nos eixos sem uso e `plain` nas faces sem encaixe é o comportamento **recomendado**, não exceção. Nada se perde — não havia encaixe ali.

---

## Parâmetros

| Parâmetro | Padrão | Faixa |
| --- | --- | --- |
| `cells_x` · `cells_y` · `cells_z` | `1` | inteiro ≥ 1 |
| `thickness` | `0` | `0` = usa `cells_z`; `> 0` = laje |
| `axis_x` · `axis_y` · `axis_z` | `bored` | `bored` / `solid` |
| `face_xn` … `face_zp` | `auto` | `auto` / `recess` / `pin` / `plain` |
| `round_axis` | `none` | `none` / `x` / `y` / `z` — arestas paralelas ao eixo viram cilindro (viga — `beam` na montagem) |
| `corner_r` | `0` | raio; `grid/2` numa peça de 1 célula = ponta redonda cheia. Acima de `grid/2` o canto come os furos das quinas |
| `pin_cells` | `all` | `all` / `edge` — machos só no perímetro da face / `inner` — machos só nas células planas quando há `round_axis` (a ponta curva não sustenta o colar; REQ-010 continua valendo para `all`) |
| `center` | `none` | `none` / `hole` / `pin` |
| `center_size` | — | diâmetro |

Presets: `all_recess`, `beam`, `corner_90` — os que têm uso real. Preset sem usuário é dívida.

---

## Laje — espessura fora do grid

Uma célula tem `grid` de altura porque esse é o mínimo para abrigar um furo de **borda**. Chão e parede não têm furo de borda, então não precisam pagar por ele.

O que limita a espessura é o **PIN**, não a `wall`. Ele tem duas cotas independentes: `collar_depth` (assenta no rebaixo) e `shaft_len` (entra no furo).

Os patamares estão em `contracts.toml` (`slab_*`). Com os valores atuais:

| Espessura | Contrato | O que habilita |
| --- | --- | --- |
| `1.0mm` | `slab_floor_1` | fêmea de um lado — abaixo disso não há encosto |
| **`2.0mm`** | `slab_min_1` = `grid/4` | fêmea de um lado, haste rasante no verso — **pele/parede** |
| `2.0mm` | `slab_floor_2` | fêmea dos dois lados: os rebaixos se encontram, o macho atravessa |
| `3.0mm` | `slab_min_2` | fêmea dos dois lados, um furo por vez |
| **`4.0mm`** | `grid/2` | **chão/base** — duas lajes empilhadas fecham uma célula |
| `4.5mm` | `slab_both` | mesmo furo servindo os dois lados ao mesmo tempo |
| `7.2mm` | `edge_bore_min` | mínimo para ter furo de **borda** |

`grid/2` é a recomendação porque **duas lajes empilhadas fecham uma célula**: a espessura compõe com o grid em vez de brigar com ele. A `grid/4` fecha exato porque `slab_min_1 = pin_len`.

**Consequência:** laje não tem furo de borda, logo **não é viga**. Toda carga entra pela face.

### Campo de furos, não de machos

Um campo de machos é base de Lego, e é a escolha errada:

- **Macho é permanente, furo é opcional.** Um campo de machos compromete toda posição para sempre; furo + [PIN](../pin.md) dá os dois estados.
- **A base precisa assentar plana** — não apoia na mesa nem empilha com outra laje se tiver saliência.
- **Rompe a simetria do sistema.** Toda peça é fêmea, todo macho é peça solta.

---

## Variantes persistidas

Uma configuração que se repete vira **arquivo**, não peça nova — ganha preview, STL e linha de catálogo automáticos sem inflar o catálogo. Variante não ganha pasta de spec; só peça ganha.

O mecanismo é `include`, **não** `use`:

| | O que importa | Serve? |
| --- | --- | --- |
| `use <brick.scad>` | só o módulo, parâmetros congelados no padrão | **não** |
| `include <brick.scad>` | o arquivo inteiro; a reatribuição vence e os derivados recomputam | sim |

Como `include` também executa o topo de `brick.scad`, a variante **não** chama `brick()` — quem desenha é o render do próprio BRICK. Uma chamada extra renderizaria duas vezes.

⚠️ **Ordem importa.** Reatribuição só pode usar literal ou variável declarada **antes** do `include`. Ao reatribuir uma variável do arquivo base, o OpenSCAD avalia no ponto da declaração original — variável nova declarada depois ainda não existe lá, e sai `WARNING: Ignoring unknown variable` com o valor errado, em silêncio.

### HUB — `impl/openscad/hub.scad`

BRICK `3×3×3` com `center = "hole"` de `Ø10`. É o que era o ATOM: o nome mudou porque "átomo" prometia unidade indivisível, e a unidade do sistema é a célula.

Bloco `24 × 24 × 24mm`; **4 de 9** furos de grid sobrevivem na face Z. Os do meio de cada aresta não: o macro alcança `9.4mm` do centro e eles estão a `8mm`. Isso é REQ-009 agindo, não configuração do HUB.

> O recurso central atravessa **só o eixo Z**. O ATOM tinha o macro nas seis faces — reproduzir exige `center_axes`, não implementado.

### PLATE — `impl/openscad/plate.scad`

Chão e parede: campo de furos no passo do grid, costas planas. `sided` decide a espessura, porque ela é consequência:

| `sided` | Espessura | Uso |
| --- | --- | --- |
| `2` | `grid/2` = `4mm` | chão/base, fêmea nas duas faces |
| `1` | `grid/4` = `2mm` | pele/parede, fêmea só em cima |

Eixos X e Y são `solid` — furo de borda exige `edge_bore_min` e a laje não tem.

---

## Critérios de aceite

Verificados por `make spec-check`:

- **AC-001** Todo derivado de `contracts.toml` avalia para o `value` declarado
- **AC-002** `corner_sliver == wall` e `web_between_holes == 2·wall` — os invariantes caem de graça da derivação
- **AC-003** O core Python produz os mesmos números do contrato
- **AC-004** Os echos do OpenSCAD produzem os mesmos números do contrato
- **AC-005** `make vars` produz os mesmos números do contrato
- **AC-006** As validações `fatal` do contrato passam com os valores atuais

Verificados por `assert` na implementação:

- **AC-007** `recess` numa face exige o eixo correspondente `bored` (REQ-005)
- **AC-008** Face Z sem furo não recebe `recess` nem `pin` (REQ-009)
- **AC-009** Laje: `thickness` acima do piso conforme o número de faces Z fêmeas, eixos X/Y `solid` abaixo de `edge_bore_min` (REQ-008)
- **AC-011** Recurso central respeita a folga de **montagem**, não só a de material

Verificados manualmente, sem automação hoje:

- **AC-012** Encaixe simultâneo nas 6 faces de uma célula 1×1 (REQ-006) — medido por interseção de sólidos, não coberto por teste automático
- **AC-013** Press-fit real em peça impressa — `tolerance` nunca foi calibrada contra impressão
