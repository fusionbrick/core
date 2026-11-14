# Padrões validados

Cada padrão é um trecho de IR que passa no `check` (e, onde indicado, na colisão exata do CGAL). Componha em vez de começar do zero. Coordenadas relativas: some o seu `at`.

| Padrão | Para | Fonte |
| --- | --- | --- |
| Chassi de longarinas + piso | base de veículo, grade de fixação | rover-tub |
| Caixa aberta | caçamba, case | rover-tub |
| Laterais de viga em alvenaria | lateral técnica em alta resolução | buggy-vt2 |
| Quadro de vigas de topo | cubo, moldura, gaiola reta | ds-tests/t1 |
| Cubo Technic empilhado | estrutura sem cavilha de topo | ds-tests/t2 |
| Anel de cantos curvos | moldura arredondada, para-choque, teto | ds-tests/t3 |
| Pórtico curvo | santantônio, arco de gaiola | ds-tests/t4 |
| Rampa (diagonal com apoio lateral) | coluna A, braço, rampa | ds-tests/t5 |
| Diagonal no plano / 3D | contraventamento, mastro inclinado | ds-tests/t5 |
| S e grampo de curva | tubo dobrado, alça, para-choque em U | ds-tests/t5 |
| Teto liso | tampa, capô | buggy-vt2 |
| Rover aberto afunilado | base de blocos + quadros curvos + arcos + mastro | rover-x6 |
| Suspensão rocker-bogie | corpo erguido sobre pernas, 6 rodas | rover-x6 |

## Chassi de longarinas + piso

Duas longarinas com pinos para dentro, piso entre elas. O piso, todo furado, vira grade de fixação para eletrônica. Rodas entram no eixo `y` das longarinas.

```toml
{ id = "longarina_e", type = "brick", at = [0, 0, 0], size = [12, 1, 1], holes = "xyz", studs = ["left"] },
{ id = "longarina_d", type = "brick", at = [0, 6, 0], size = [12, 1, 1], holes = "xyz", studs = ["right"] },
{ id = "piso",        type = "brick", at = [0, 1, 0], size = [12, 5, 1], holes = "xyz" },
```

## Caixa aberta (paredes sobre base)

Laterais com `studs = "bottom"` sobre as longarinas; frente e traseira travam nas laterais (`right`/`left`) **e** no piso (`bottom`). Três faces de junção = rígida.

```toml
{ id = "lateral_e", type = "brick", at = [0, 0, 1], size = [12, 1, 2], holes = "yz", studs = "bottom" },
{ id = "lateral_d", type = "brick", at = [0, 6, 1], size = [12, 1, 2], holes = "yz", studs = "bottom" },
{ id = "frente",    type = "brick", at = [0, 1, 1], size = [1, 5, 2], holes = "yz", studs = ["bottom", "right", "left"] },
```

## Para-choque

Com pinos (`studs = ["front"]`) quando as pontas das longarinas e do piso têm eixo `x` furado. Sem pinos expostos: todo `socket`, e o compilador põe cavilhas nos encontros.

## Pórtico / santantônio

Colunas de **2 células de base** (uma `1×1` giraria) com pinos em cima e embaixo; travessa por cima.

```toml
{ id = "coluna_e", type = "brick", at = [10, 0, 3], size = [2, 1, 3], holes = "yz", studs = ["bottom", "top"] },
{ id = "coluna_d", type = "brick", at = [10, 6, 3], size = [2, 1, 3], holes = "yz", studs = ["bottom", "top"] },
{ id = "travessa", type = "brick", at = [10, 0, 6], size = [2, 7, 1], holes = "yz" },
```

## Deck em placa

Chão leve sobre longarinas com `studs = "top"`. Peças acima em `z = 1.5`, e **nunca sobre a mesma coluna de furos das longarinas** (ASM-006).

```toml
{ id = "deck", type = "plate", at = [0, 0, 1], size = [14, 7, 1] },
```

## Torre + cabeça

Torre com pinos nas duas pontas; cabeça maior por cima, recebendo. Bom para sensores (ultrassom, câmera) na frente de um rover.

## Mastro giratório

Peça `1×1` com uma junção só, declarada em `hinges`. É o mesmo padrão de qualquer torreta.

## Rodas

| Diâmetro | `diameter` | Espaçamento mínimo entre eixos | Vão livre (eixo em z=0.5) |
| --- | --- | --- | --- |
| Ø24 | 3 | 3 células + 1 | 8mm |
| Ø32 | 4 | 4 células + 1 | 12mm |

Rodas da frente e de trás no mesmo lado: a distância entre `at` precisa passar do diâmetro em células, senão ASM-002.

## Gaiola com colunas A (diagonal)

Postes `1×1×n` nas laterais, quadro do teto (travessas + trilhos), e a coluna A como diagonal. Do `buggy-vt`:

```toml
# 6-8-10 → viga de 9. Embaixo o nó pousa na lateral; em cima prende na travessa.
{ id = "coluna_a", type = "strut", from = [17, 0, 3], to = [9, 0, 9], from_arm = [0, 0, -1], to_arm = [-1, 0, 0] },
```

Poste do meio da gaiola uma célula ATRÁS da ponta alta (x=7 com a ponta em x=9): em x=8 ele bate na coluna A.

## Berço de bateria

Dois blocos `1×4×1` com `studs = "bottom"` no piso, com o vão do comprimento da bateria arredondado para cima em células, e a bateria como componente entre eles.

## Laterais de viga em alvenaria (alta resolução)

Cada lateral é feita de **camadas** de vigas 1×1×n ao longo de X, com as emendas **desencontradas** de uma camada para a outra. As cavilhas verticais (contato entre camadas) amarram tudo; nenhuma emenda fica sobre outra. Travessas ao longo de Y, cavilhadas na face interna.

```python
ROWS = {0: [(0, 17), (17, 34)], 1: [(0, 12), (12, 24), (24, 34)], 2: [(0, 14), (14, 22), (22, 34)]}
for z, segs in ROWS.items():
    for k, (x0, x1) in enumerate(segs):
        b.brick("chassi", f"lat{z}{'abc'[k]}_e", (x0, 0, z), (x1 - x0, 1, 1), OR, **LIFT_X)
for x in (1, 9, 17, 25, 32):
    b.brick("chassi", f"trav_x{x}", (x, 1, 0), (1, W - 2, 1), OR, **LIFT_Y)
b.mirror_y(W)
```

Camadas 0 a n−1 com `studs = "top"` (em peça arredondada isso já põe os pinos só nas células planas): o empilhamento vira encaixe por pino e só as pontas redondas ficam sem. Dois segmentos por camada (peça ≤ 27 células) com a emenda em x diferente a cada camada. No buggy-vt3 isso levou as cavilhas das laterais de 144 para 0. Sem pinos, use `dowel_every = 3–5`.

## Quadro de vigas de topo (cubo, moldura)

As vigas X são donas dos cantos; as Y entram **entre** elas; os postes ficam entre o quadro de baixo e o de cima. Toda junta é cavilha (`socket × socket`) — 16 cavilhas para 12 vigas num cubo.

```toml
{ id = "x0", type = "brick", at = [0, 0, 0], size = [8, 1, 1] },
{ id = "x1", type = "brick", at = [0, 7, 0], size = [8, 1, 1] },
{ id = "y0", type = "brick", at = [0, 1, 0], size = [1, 6, 1] },
{ id = "y1", type = "brick", at = [7, 1, 0], size = [1, 6, 1] },
{ id = "p0", type = "brick", at = [0, 0, 1], size = [1, 1, 6] },   # ×4 cantos; topo igual à base em z = 7
```

Para pinos impressos em vez de cavilhas: `studs = ["right", "left"]` nas vigas Y e `studs = ["bottom", "top"]` nos postes (só sem `rounded`). O cubo passa de 16 cavilhas para 16 encaixes por pino e 0 peças soltas.

## Cubo Technic empilhado

Camadas alternadas: z par = vigas X em y=0 e y=N−1; z ímpar = vigas Y em x=0 e x=N−1, todas de N células, `rounded = "z"`. Os cantos se sobrepõem e levam uma cavilha vertical por camada. As arestas verticais nascem da sobreposição; nenhuma viga encosta de topo. Empilhar é o jeito de cruzar vigas sem cavilha de topo (lei 7).

```toml
{ id = "x0-0", type = "brick", at = [0, 0, 0], size = [8, 1, 1], rounded = "z", corner_r = 4.0 },
{ id = "x1-0", type = "brick", at = [0, 7, 0], size = [8, 1, 1], rounded = "z", corner_r = 4.0 },
{ id = "y0-1", type = "brick", at = [0, 0, 1], size = [1, 8, 1], rounded = "z", corner_r = 4.0 },
{ id = "y1-1", type = "brick", at = [7, 0, 1], size = [1, 8, 1], rounded = "z", corner_r = 4.0 },
```

## Anel de cantos curvos

4 vigas retas + 4 curvas de `radius = 2` num plano. Use a macro: `b.ring(grupo, prefixo, x0, y0, z, nx, ny, radius=2)`. À mão, para um quadro N×N em z:

```toml
{ id = "s",   type = "brick", at = [2, 0, 0],     size = [N-4, 1, 1] },
{ id = "cSE", type = "curve",  at = [N-2, 0, 0],   dir = [1, 0, 0],  turn = [0, 1, 0] },
{ id = "l",   type = "brick", at = [N-1, 2, 0],   size = [1, N-4, 1] },
{ id = "cNE", type = "curve",  at = [N-1, N-2, 0], dir = [0, 1, 0],  turn = [-1, 0, 0] },
{ id = "n",   type = "brick", at = [2, N-1, 0],   size = [N-4, 1, 1] },
{ id = "cNO", type = "curve",  at = [1, N-1, 0],   dir = [-1, 0, 0], turn = [0, -1, 0] },
{ id = "o",   type = "brick", at = [0, 2, 0],     size = [1, N-4, 1] },
{ id = "cSO", type = "curve",  at = [0, 1, 0],     dir = [0, -1, 0], turn = [1, 0, 0] },
```

Dois anéis + postes sobre as **pontas das vigas retas** (x=2, x=N−3…) fazem um cubo de cantos arredondados. Postes não encaixam nas curvas.

## Pórtico curvo

Poste → curva (sobe e vira) → travessa → curva (vira e desce) → poste, num plano vertical. Os postes ficam nas células x=2 e x=N−3 de uma viga de base.

```toml
{ id = "pe", type = "brick", at = [2, 0, 1],     size = [1, 1, H-1] },
{ id = "ce", type = "curve",  at = [2, 0, H],     dir = [0, 0, 1], turn = [1, 0, 0] },
{ id = "tr", type = "brick", at = [4, 0, H+1],   size = [N-8, 1, 1] },
{ id = "cd", type = "curve",  at = [N-4, 0, H+1], dir = [1, 0, 0], turn = [0, 0, -1] },
{ id = "pd", type = "brick", at = [N-3, 0, 1],   size = [1, 1, H-1] },
```

Dois pórticos paralelos se unem por vigas Y entre as travessas (cumeeira).

No plano Y-Z (arco transversal, santantônio aberto) use a macro: `b.arch(grupo, prefixo, x, y0, y1, z0, top)` — postes em y0 e y1 de z0 até top−2, travessa em z = top ocupando y0+2 … y1−2. Os postes precisam de uma face embaixo (viga do quadro, deck). O rover-x6 tem dois sobre o quadro superior.

## Rampa (diagonal com apoio lateral)

A diagonal termina **de lado**: o braço de cada nó aponta para trás da viga (≥127°) — é o padrão do `strut`. O pé encosta num bloco atrás; o topo encosta num poste à frente.

```toml
{ id = "pe",    type = "brick", at = [1, 0, 1], size = [1, 1, 1] },
{ id = "rampa", type = "strut", from = [2, 0, 1], to = [6, 0, 4] },      # 3-4-5: nós e viga saem sozinhos
{ id = "poste", type = "brick", at = [7, 0, 1], size = [1, 1, 4] },
```

No `gen.py`: `b.strut(grupo, id, (2,0,1), (6,0,4))`. Rampa suave 12-5: mesmo desenho com `to = [14, 0, 6]`.

## Diagonal no plano e em 3D

- **No plano do chão** (contraventamento): pontas na mesma altura das longarinas, braços em ±Y nas faces internas delas: `from = [9,1,0], to = [15,9,0], from_arm = [0,-1,0], to_arm = [0,1,0]`, longarinas em y=0 e y=10.
- **3D 2-3-6**: a ponta de baixo apoia por baixo (`from_arm = [0,0,-1]`, 149°), a de cima **pendura** numa viga-teto (`to_arm = [0,0,1]`). Um braço lateral a 115° colide.

## S e grampo de curva

- **S** (sobe, anda, sobe): `poste` → `curve dir=+Z turn=+X` → viga X → `curve dir=+X turn=+Z` → poste. Termine o S numa peça apoiada dos dois lados, senão a última peça fica com uma junção só.
- **Grampo 180°**: viga A → `curve angle=180 dir=+X turn=+Y` → viga B de volta, `2·radius − 1` células ao lado. As duas vigas presas na mesma travessa.

```toml
{ id = "U-a", type = "brick", at = [16, 4, 1], size = [5, 1, 1] },
{ id = "U-c", type = "curve",  at = [21, 4, 1], dir = [1, 0, 0], turn = [0, 1, 0], radius = 2, angle = 180 },
{ id = "U-b", type = "brick", at = [16, 7, 1], size = [5, 1, 1] },
```

## Teto liso

Quadro de vigas (trilhos + travessas) e por cima uma tampa: chapa sem furos com pinos para baixo só no perímetro.

```toml
{ id = "teto", type = "cover", at = [0, 0, 15], size = [18, 16, 1] },
```

## Rodas grandes (off-road / balão)

`width = 4–5`, `tread = "balloon"`, `spokes = 5`, `spoke_style = "y"`, presas numa viga de lateral **que vai de ponta a ponta naquele nível** (a roda balança se a viga for curta). Diâmetro ≈ 0,35–0,45 × comprimento do corpo para visual de buggy (buggy-vt2: Ø112 em 304 mm).

## Rover aberto afunilado (rover-x6)

Corpo de rover sem cara de caixa, em 4 camadas:

1. **Base de blocos grandes**: duas laterais de viga (2 camadas, `studs = "top"`) e, entre elas, blocos 12×12×2 com `holes = "xz"` e `studs = ["right", "left", "front"]` — encaixe por pino nos lados e entre blocos.
2. **Deck** de placas com `studs = "bottom"` cobrindo toda a base (nenhum pino fica livre).
3. **Quadro inferior** `ring()` no perímetro do deck.
4. **Quadro superior mais estreito** (2 células para dentro de cada lado, mais curto) sobre postes que nascem do deck — a silhueta afunila. Arcos `arch()` sobre ele, mastro 2×2 redondo (`rounded = "z"`) com cabeça.

Medido: 17,9 peças/100 mm, 0 pinos livres, maior peça 192 mm.

## Suspensão rocker-bogie (visual)

Corpo erguido sobre pernas, a marca de um rover. Por lado (y = −1, fora do corpo):

```python
XM = 18                                      # roda do meio
b.brick("susp", "coluna_e", (XM, -1, AZ), (1, 1, BZ - AZ + 1), GF, holes="xyz", rounded="y")
for tag, xw, sgn in (("t", 4, -1), ("f", 32, 1)):
    x0, x1 = sorted((XM + sgn, xw - sgn))
    b.brick("susp", f"bogie_{tag}_e", (x0, -1, AZ), (x1 - x0 + 1, 1, 1), GF, **LIFT_X)
    b.brick("susp", f"cubo_{tag}_e", (xw, -1, AZ), (1, 1, 2), GF, holes="xyz")
    b.strut("susp", f"perna_{tag}_e", (XM + sgn, -1, BZ), (xw - sgn, -1, AZ + 1),
            from_arm=[-sgn, 0, 0], to_arm=[sgn, 0, 0])
# rodas: a do meio em coluna_e.right, as da ponta em cubo_*.right; depois b.mirror_y(W)
```

- **Coluna** da roda do meio vai do eixo até a lateral do corpo e encosta nela (junta no topo).
- **Bogie** no nível do eixo liga a coluna ao **cubo** 1×1×2 da roda da ponta.
- **Perna** 5-12-13 (com `BZ − AZ − 1 = 5`) sai de lado da coluna e chega de lado no cubo: os dois braços a 157° da diagonal (lei 6). Braço para baixo pousando no bogie fica a 113° e colide.
- O cubo precisa de 2 juntas além do eixo (bogie + perna): **eixo de roda não conta para rigidez**.
