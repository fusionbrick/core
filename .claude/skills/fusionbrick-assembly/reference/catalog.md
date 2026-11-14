# Catálogo da IR

Tudo em **células** (1 célula = `grid` = 8 mm), exceto onde diz mm. Eixos: x, y no chão, z para cima; **a frente é +X**. Faces: `front` (+X) · `back` (−X) · `left` (+Y) · `right` (−Y) · `top` (+Z) · `bottom` (−Z). Encaixes: `stud` (pino impresso) · `socket` (encaixe) · `flat` (liso). Schema completo para tool use: `python3 hack/scripts/fb_assemble.py schema`.

## `[assembly]`

| Campo | Padrão | Para quê |
| --- | --- | --- |
| `name` | — | nome da pasta em `examples/` |
| `intent` | — | o pedido em uma frase (vai para BOM e passos) |
| `dowel_every` | 1 | num contato longo entre faces `socket`, uma cavilha a cada N furos. Com vigas: 3 |
| `view_angle` | 35 | giro em Z da vista principal e da explodida. Frente em +X: 125 ou 215 |

## `brick` — bloco

A peça-base. Viga, placa e tampa são blocos com padrões (seção seguinte).

```toml
{ id = "lat_e", type = "brick", at = [0, 0, 1], size = [16, 1, 1], holes = "xyz", rounded = "y", color = [0.97, 0.47, 0.10] }
```

| Campo | Padrão | Notas |
| --- | --- | --- |
| `at` | — | canto mínimo; X/Y inteiros, Z múltiplo de 0.5 |
| `size` | `[1,1,1]` | células em x, y, z, no referencial do mundo (o bloco não gira) |
| `holes` | `"xyz"` | direções com furo passante; `"none"` = maciço. Furo sem função polui: tire o que não encaixa, a não ser que o visual técnico seja a intenção |
| `faces` | `auto` em todas | `auto` = `socket` onde há furo, `flat` onde não há. Declare só `stud` e `flat` deliberados: `faces = { bottom = "stud" }`. `socket` numa direção sem furo = erro REQ-005 |
| `studs` | — | atalho: `"top"` / `"bottom"`, ou uma lista de faces (`["left", "right"]`) que levam pino |
| `flat` | — | atalho: lista de faces que ficam lisas (`["back"]`) |
| `thickness` | 0 | mm; > 0 vira chapa (4.0 típico). Tudo acima fica em `z + 0.5` |
| `rounded` | `"none"` | arredonda as pontas em torno deste eixo. `rounded = "y"` numa peça ao longo de X = furos Y à vista e pontas redondas. Ponta redonda **não leva pino** (REQ-010) |
| `corner_r` | 4 com `rounded`, senão 0 | mm, ≤ 4 (= grid/2). Acima disso corta os furos do canto |
| `studs_on` | `"all"` | onde ficam os pinos de uma face: `"edge"` = só no perímetro (tampa sobre quadro) · `"inner"` = só nas células planas de uma peça arredondada (viga empilhada sem cavilha) |
| `color` | paleta | `[r, g, b]` 0–1 |

Receitas (`fusionbrick.irgen`), para bloco com cara de viga mais grosso que 1×1: `LIFT_X` ao longo de X · `LIFT_Y` ao longo de Y · `LIFT_Z` poste · `FLAT` cantos redondos em planta.

## `beam` · `plate` · `cover` — variantes do bloco

Fonte: `impl/python/fusionbrick/asm/variants.py`. Variante = bloco com padrões; o que a peça escreve vence.

```toml
{ id = "lat",   type = "beam",  at = [0, 0, 1], size = [12, 1, 1], studs = "top" },
{ id = "deck",  type = "plate", at = [0, 0, 2], size = [12, 8, 1], studs = "bottom" },
{ id = "tampa", type = "cover", at = [0, 0, 4], size = [12, 8, 1] },
```

| `type` | É | Padrões | Exige |
| --- | --- | --- | --- |
| `beam` | viga furada de pontas redondas | `holes = "xyz"`, `rounded` = eixo que deixa os furos à vista (viga em X ou Z → `"y"`; em Y → `"x"`) | seção 1×1 |
| `plate` | chapa de 4 mm furada | `thickness = 4`, `holes = "z"`, `rounded = "z"`, `corner_r = 4` | — |
| `cover` | tampa lisa de 4 mm | `thickness = 4`, `holes = "none"`, `rounded = "z"`, `faces.bottom = "stud"`, `studs_on = "edge"` | um quadro embaixo do perímetro |

| Atalho (qualquer bloco) | Equivale a |
| --- | --- |
| `studs = "top"` / `"bottom"` | `faces.top` / `faces.bottom` `= "stud"` (+ `studs_on = "inner"` se a peça é arredondada) |
| `studs = ["left", "right"]` | essas faces `= "stud"` |
| `flat = ["back"]` | essas faces `= "flat"` |

## `curve` — curva

```toml
{ id = "c1", type = "curve", at = [12, 0, 0], dir = [1, 0, 0], turn = [0, 1, 0], radius = 2, angle = 90 }
```

| Campo | Padrão | Notas |
| --- | --- | --- |
| `at` | — | **1ª célula do arco**: a célula logo depois da última célula da viga que chega |
| `dir` | `[0,1,0]` | avanço na entrada (um eixo). A entrada fica na face de trás de `at` (−dir) |
| `turn` | `[-1,0,0]` | para onde a curva vira, ⊥ `dir` |
| `radius` | 2 | células que a curva ocupa de lado: 1 → 1×1 (R4) · 2 → 2×2 (R12) · 3 → 3×3 (R20) |
| `angle` | 90 | 90 ou 180 |
| `ports` | `"socket"` | ou `"stud"`/`"flat"`, ou `[entrada, saída]` |

**Onde sai a outra ponta** (com `r = radius`, em células):

- 90°: a peça seguinte tem o canto mínimo em `at + (r−1)·dir + r·turn` e corre ao longo de `turn`. Ex.: `at=[12,0,0] dir=+X turn=+Y radius=2` → a viga seguinte começa em `[13, 2, 0]` e corre em +Y (com `radius=1`: `[12, 1, 0]`).
- 180°: volta na direção `−dir`, deslocada `2r−1` células em `turn`. Ex.: `at=[21,4,1] dir=+X turn=+Y radius=2` → a viga de volta termina em `x=20`, `y=7`.

Na dúvida, use a macro `ring()` de `irgen` ou copie um padrão de `patterns.md`. Furos ao longo do arco são visuais; nada encaixa no miolo.

## `strut` — diagonal

```toml
{ id = "rampa", type = "strut", from = [2, 0, 1], to = [6, 0, 4] }
```

Uma linha: as duas células das pontas. O compilador cria os nós `rampa-n0` (em `from`), `rampa-n1` (em `to`) e a viga `rampa-v`; nos `groups` você escreve só `rampa`.

| Campo | Padrão | Notas |
| --- | --- | --- |
| `from`, `to` | — | células dos dois nós. O vetor `to − from` precisa fechar no grid (lista abaixo) |
| `from_arm`, `to_arm` | o eixo dominante, para trás da diagonal | o braço de cada nó que prende no resto. Para `(4,0,3)`: `from_arm = [-1,0,0]`, `to_arm = [1,0,0]` |
| `style` | `"beam"` | viga furada de pontas redondas; `"box"` = caixa lisa |
| `fillet` | — | mm, ≤ 2 (grid/4): arredonda o nó. Mais que isso transborda a célula (ASM-002) |

Comprimento da viga = `|Δ| − 1` células. Vetores que fecham: (3,4)→5 · (6,8)→10 · (5,12)→13 · (9,12)→15 · (8,15)→17 · 3D (1,2,2)→3 · (2,3,6)→7 · (4,4,7)→9.

**Regra do braço**: o braço fica a ≥127° da diagonal (cos ≤ −0,6). Para a diagonal (4,0,3): braço `[-1,0,0]` (143°) ok, `[0,0,-1]` (127°) no limite, `[0,0,1]` ou `[1,0,0]` colidem. O que prende o nó é **uma peça encostada no braço**: ponha um bloco na célula para onde o braço aponta.

**Uso avançado — nó com 3+ portas.** Declare os nós à mão e ligue por id:

```toml
{ id = "n0", type = "node", at = [2, 0, 1], dirs = [[-1, 0, 0], [4, 0, 3], [0, 1, 0]] },
{ id = "n1", type = "node", at = [6, 0, 4], dirs = [[-4, 0, -3], [1, 0, 0]] },
{ id = "v",  type = "strut", from = "n0", to = "n1" },
```

`node.dirs` = uma direção inteira por porta (a diagonal pode ser reduzida: `[4,0,3]` vale para `[8,0,6]`); `node.ports` = `"stud"` (padrão) ou lista.

## `wheel` — roda

```toml
{ id = "roda_fe", type = "wheel", at = [27, -1, 2], on = "lat2c_e.right", diameter = 14, width = 5, tread = "balloon", spokes = 5, spoke_style = "y" }
```

| Campo | Padrão | Notas |
| --- | --- | --- |
| `at` | — | célula do cubo, encostada na face |
| `on` | — | `<peça>.<face>`, ex. `"lateral.right"`; ali a face precisa ter encaixe (`socket`) |
| `diameter` | 4 | em células (3 → Ø24 … 14 → Ø112) |
| `width` | 1 | 1–6 células; o eixo acompanha |
| `tread` | `street` | `offroad` (garras), `balloon` (pneu gordo) |
| `spokes` / `spoke_style` | 0 / `straight` | `y` = raio em Y, visual de roda de liga |

O eixo (AXLE) é gerado sozinho. O compilador informa o vão livre (ASM-010) e acusa roda que bate em peça.

## `component` — o que se compra pronto (não imprime)

```toml
{ id = "bat", type = "component", at = [3, 2, 1], size_mm = [48.5, 26.5, 17.5], label = "9V", color = [0.2, 0.2, 0.25] }
```

| `shape` | `size_mm` | Colide? |
| --- | --- | --- |
| `box` (padrão) | `[x, y, z]` | sim |
| `cyl` | `[Ø, Ø, comprimento]` no eixo `axis` | sim |
| `cable` | `[Ø, …]` + `points = [[x,y,z], …]` em células | não |
| `text` | altura da letra + `text = "…"` | não |

`mass` (g) em todo componente que pesa: o `physics` usa para centro de massa e tombamento; sem ela estima por 0,6 g/cm³ (erra feio em bateria e LiDAR).

Medidas úteis (mm · g): 9V 48,5×26,5×17,5 · 45 · 18650 Ø18×65 · 47 · LiPo 2S 2200 ~67×42×28 · 110 · Raspberry Pi 4 85×56×17 · 46 · Pi Zero 65×30×5 · 9 · Arduino Uno 68,6×53,4×15 · 25 · ESP32-CAM 40×27×12 · 10 · motor 130 Ø20×25 · 18 · N20 com caixa 12×10×34 · 12 · TT 70×22×18 · 30 · servo SG90 23×12,2×29 · 9 · HC-SR04 45×20×15 · 9 · LiDAR LD06 38,6×38,6×33,5 · 42 · RPLidar A1 97×70×55 · 170 · câmera Pi 25×24×9 · 3 · TB6612 20×20×3 · 2.

## Grupos, rotas, dobradiças

- `groups = [{ id, parts, note, sub? }]` — **ordem de montagem** e passos do `steps.md`. A ordem é checada (ASM-012): cada peça entra nas anteriores por um movimento só. `sub = true` = subconjunto montado à parte que entra como um corpo (lateral de 2 camadas, anel fechado, arco, suspensão). Componentes entram no grupo em que são colocados. Um `strut` entra pelo próprio id.
- `routes = [{ id, path = [[x,y,z], …] }]` — passagem de fio por furos contíguos (ASM-007).
- `hinges = ["mastro"]` — peças com uma junção só, girando de propósito.
