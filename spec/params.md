# Parâmetros — Referência

As cotas do sistema têm **uma** fonte: [`parts/brick/contracts.toml`](parts/brick/contracts.toml), conferida por `make spec-check` contra o core Python, o OpenSCAD e o `make vars`. As tabelas abaixo são **geradas** dela (`make spec-docs`); o porquê de cada premissa está em [constitution.md](constitution.md).

---

<!-- GERADO por hack/scripts/spec_docs.py a partir de spec/parts/brick/contracts.toml — não edite -->

## Primitivos

| Primitivo | Valor | Papel |
| --- | --- | --- |
| `hole_d` | `4mm` | furo passante — a interface mecânica |
| `wall` | `1.6mm` | parede interna mínima (4 perímetros de 0,4) |
| `collar_w` | `0.4mm` | degrau radial entre furo e rebaixo (1 bico) |
| `collar_depth` | `1mm` | profundidade axial do rebaixo (5 camadas de 0,2) |
| `tolerance` | `0.2mm` | folga de press-fit, sempre do macho |
| `gap` | `0.5mm` | folga mínima entre dois machos que se aproximam |
| `pin_len` | `2mm` | protrusão do macho — **declarado**, com teto `pin_len_max` (constitution.md § 5) |

## Derivados

Nenhum é escolhido à mão: mudar um primitivo recalcula todos.

| Derivado | Fórmula | Valor | Nota |
| --- | --- | --- | --- |
| `grid` | `hole_d + 2·(wall + collar_w)` | `8mm` | O grid é DERIVADO. Declará-lo permitiria pedir um que não fecha com o próprio furo. |
| `recess_d` | `hole_d + 2·collar_w` | `4.8mm` |  |
| `pin_d` | `hole_d − tolerance` | `3.8mm` |  |
| `collar_d` | `recess_d − tolerance` | `4.6mm` |  |
| `inset` | `grid/2` | `4mm` | Do canto da célula ao centro do furo. É o que faz a aresta do braço de um canto encostar exatamente na quina. |
| `pin_len_max` | `grid/2 − pin_d/2` | `2.1mm` | Teto do macho: duas hastes perpendiculares se tocam aqui. |
| `passage_max` | `grid/2 − hole_d/2` | `2mm` | Tangência com a passagem transversal. Acima disso o macho come a seção livre do furo perpendicular — é por isso que pin_len de produção é 2.0 e não 2.1. |
| `edge_bore_min` | `hole_d + 2·wall` | `7.2mm` | Espessura mínima para caber um furo de BORDA. Laje fina não tem. |
| `shaft_len` | `pin_len − collar_depth` | `1mm` | Haste além do colar. Ela ALINHA; quem retém é o colar. |
| `slab_floor_1` | `collar_depth` | `1mm` | Fêmea de UM lado: abaixo disso não sobra encosto para o colar. |
| `slab_floor_2` | `2·collar_depth` | `2mm` | Fêmea dos DOIS lados: os rebaixos se encontram e o macho atravessa. |
| `slab_min_1` | `pin_len` | `2mm` | Fêmea de um lado, haste inteira dentro. = grid/4 — a laje de pele. |
| `slab_min_2` | `2·collar_depth + (pin_len − collar_depth)` | `3mm` | Fêmea dos dois lados, um furo servindo um lado por vez. |
| `slab_both` | `2·pin_len + gap` | `4.5mm` | Mesmo furo servindo os dois lados ao mesmo tempo, com folga. |

## Invariantes

Caem de graça da derivação; se um quebrar, o grid não fecha.

| Invariante | Fórmula | Igual a | Valor | Nota |
| --- | --- | --- | --- | --- |
| `corner_sliver` | `inset − recess_d/2` | `wall` | `1.6mm` | Lasca na quina da célula. |
| `web_between_holes` | `grid − recess_d` | `2·wall` | `3.2mm` | Alma entre dois rebaixos vizinhos. |
| `edge_bar` | `(grid − hole_d)/2` | — | `2mm` | Seção da gaiola de 12 arestas, com os três eixos vazados. Caso extremo do sistema. |

## Validações

`fatal` não gera a peça; `warn` gera e avisa.

| id | Severidade | Regra | Se falhar |
| --- | --- | --- | --- |
| `recess_vs_edge_bar` | fatal | `hole_d · sqrt(2) > recess_d` | rebaixo morde a barra da aresta |
| `pin_len_max` | fatal | `pin_len <= pin_len_max` | macho encosta no perpendicular da célula receptora |
| `pin_len_vs_collar` | fatal | `pin_len > collar_depth` | colar mais fundo que a protrusão: a haste não sai do colar |
| `pin_len_positive` | fatal | `pin_len > 0` | macho sem comprimento |
| `pin_vs_passage` | warn | `pin_len <= passage_max` | macho invade a passagem transversal |
| `invariant_corner` | warn | `corner_sliver == wall` | lasca na quina divergiu da parede |
| `invariant_web` | warn | `web_between_holes == 2·wall` | alma entre furos divergiu de 2×parede |

<!-- fim do bloco gerado -->

## Escala fina

`2.5mm` — passo da **pele** (material fora do volume de grid) e de qualquer cota que não seja múltiplo de célula.

---

## Configuração por peça

Não fazem parte do contrato: escolhem a variante.

| Parâmetro | Tipo | Padrão | Aplica a |
| --- | --- | --- | --- |
| `cells_x` · `cells_y` · `cells_z` | inteiro ≥ 1 | `1` | toda peça |
| `skin_x` · `skin_y` · `skin_z` | múltiplo de `2.5` | `0` | peças com conteúdo fora do grid |
| `axis_x` · `axis_y` · `axis_z` | `bored` / `solid` | `bored` | toda peça |
| `face_*` (6) | `recess` / `pin` / `plain` | `recess` | toda peça |
| `len` | livre | — | vigas |
| `angle` | `15°` a `180°` | `90` | curvas |
| `inner_r` | ≥ 0 | `0` | curvas |
| `spacer` | ≥ 0 | `0` | conectores de face |
| `center` | `none` / `hole` / `pin` | `none` | blocos |
| `center_size` | diâmetro | — | blocos com `center` |
| `border_radius` | `0` a `grid/2` | `0` | toda peça |
| `border_style` | `round` / `chamfer` | `round` | toda peça |

---

## Limites por peça

As validações numéricas do sistema estão no bloco gerado acima. Estas dependem da configuração de cada peça:

| Regra | Onde |
| --- | --- |
| `face == recess` ⟹ eixo `bored` (REQ-005) | `brick.scad`, `brick.py`, compilador |
| folga de montagem do recurso central | `brick.scad` |
| laje: espessura mínima por face fêmea (REQ-008) | `brick.scad`, compilador |
| macho fora de ponta arredondada (REQ-010) | `brick.scad`, compilador |

---

## O que muda e o que não muda com o grid

Ao alterar `hole_d` ou `wall`, o `grid` e todos os derivados acompanham. Estes **não** acompanham, porque são do processo de fabricação:

| Fixo | Valor | Amarrado a |
| --- | --- | --- |
| `collar_w` | `0.4mm` | largura de 1 filete (bico de `0.4`) |
| `collar_depth` | `1.0mm` | 5 camadas de `0.2` |
| `tolerance` | `0.2mm` | precisão da impressora |
| `gap` | `0.5mm` | folga de montagem entre machos |
| escala fina | `2.5mm` | convenção do sistema |

Trocar de bico ou de altura de camada é o que justifica mexer nesses quatro — não o tamanho da peça.

---

> **Peças convertidas para spec-driven** têm as cotas em `spec/parts/<peça>/contracts.toml`, que é a fonte única e é verificada por `make spec-check`. Este arquivo continua valendo como referência **entre** peças. Ver [README.md](README.md).
