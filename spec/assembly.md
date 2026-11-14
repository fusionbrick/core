# Montagem — regras de encaixe

Como as peças se juntam. Toda montagem do sistema (à mão, por IA ou por ferramenta) obedece a estas regras, e o compilador `fusionbrick.asm` as verifica.

| | |
| --- | --- |
| Premissas | [`constitution.md`](constitution.md) |
| Peças | [`parts/`](parts/) |
| Implementação | `impl/python/fusionbrick/asm/` · CLI `hack/scripts/fb_assemble.py` |
| Nomes | `impl/python/fusionbrick/asm/names.py` — fonte única do vocabulário |
| Testes | `impl/python/tests/test_assembly.py` — um teste por regra |
| Skill | `.claude/skills/fusionbrick-assembly/` |

---

## A ideia

**Quem monta decide o quê e onde; o compilador garante o como.**

A montagem é descrita em `examples/<nome>/assembly.toml`: quais peças ocupam quais células, com quais furos e encaixes. Ninguém escreve `translate`, `rotate`, mm ou cavilha. O compilador:

1. resolve a geometria a partir das células
2. acha os contatos face a face e, em cada um, os **pares de portas**
3. decide cada par pela tabela abaixo: junção, cavilha inserida, apoio ou erro
4. aplica as regras ASM
5. gera `assembly.scad`, `bom.md`, `steps.md` e um STL por configuração única de peça

Como o grid é inteiro e o bloco é sempre ortogonal, montar é um problema de **ocupação de células**. O encaixe não é escrito: ele é consequência de duas faces encostadas.

---

## Nomes

Um nome por conceito, com as palavras de quem monta. Fonte única: `asm/names.py`.

### Peças

| `type` | Nome | O que é |
| --- | --- | --- |
| `brick` | Bloco | a peça-base: qualquer tamanho, furos e encaixes que você escolher |
| `beam` | Viga | barra 1×1×n furada, de pontas redondas |
| `plate` | Placa | chapa fina furada, para pisos e bases |
| `cover` | Tampa | chapa lisa que fecha por cima |
| `curve` | Curva | viga que vira 90° ou 180° |
| `strut` | Diagonal | viga inclinada entre dois pontos; os nós das pontas são criados sozinhos |
| `wheel` | Roda | roda com eixo incluso |
| `component` | Componente | o que se compra pronto: bateria, placa, motor, fio. Não imprime |

`beam`, `plate` e `cover` são **variantes** do bloco (ver adiante). `node` (nó) continua existindo para quem precisa de um nó com três ou mais portas.

### Encaixes

| Palavra | Em português | O que é |
| --- | --- | --- |
| `stud` | pino | macho que já sai impresso na face |
| `socket` | encaixe | furo com rebaixo que recebe um pino |
| `flat` | liso | face sem nada |
| *dowel* | cavilha | pino solto de duas pontas que une dois `socket` (o compilador insere) |

### Faces

A frente do modelo é **+X**; Z é para cima.

| Face | Lado | | Face | Lado |
| --- | --- | --- | --- | --- |
| `front` | +X | | `back` | −X |
| `left` | +Y | | `right` | −Y |
| `top` | +Z | | `bottom` | −Z |

### Nomes antigos e nomes do OpenSCAD

Todo nome de antes desta revisão continua aceito, e os parâmetros das peças no OpenSCAD e no contrato (`spec/parts/*/contracts.toml`) não mudaram. A tabela é a ponte entre as três camadas:

| Nome atual (IR) | Nome antigo (IR, aceito) | Parâmetro no OpenSCAD |
| --- | --- | --- |
| `beam` · `cover` · `curve` · `component` | `liftarm` · `tile` · `bend` · `mock` | `brick.scad` · `brick.scad` · `curve.scad` · — |
| `strut` com `from`/`to` em células | `node` + `node` + `beam` com `from`/`to` em ids | `node.scad` + `brick.scad` |
| `stud` · `socket` · `flat` | `pin` · `recess` · `plain` | `pin` · `recess` · `plain` (as duas formas valem em `-D`) |
| `front` `back` `left` `right` `top` `bottom` | `xp` `xn` `yp` `yn` `zp` `zn` | `face_xp` `face_xn` `face_yp` `face_yn` `face_zp` `face_zn` |
| `size` | `cells` | `cells_x`, `cells_y`, `cells_z` |
| `holes` | `axes` | `axis_x`, `axis_y`, `axis_z` (`bored` / `solid`) |
| `rounded` | `round` | `round_axis` |
| `studs_on` | `pin_cells` | `pin_cells` |
| `studs = "top"` / `"bottom"` / lista de faces | `studs = "up"` / `"down"`, `pins = […]` | `face_* = "pin"` |
| `flat = […]` | `plain = […]` | `face_* = "plain"` |
| `radius` (curva: 1, 2, 3) | `k` (0, 1, 2) | `k` |
| `diameter` (roda) | `cells` | `wheel_cells` |
| `size_mm` (componente) | `size` | — |
| `view_angle` · `dowel_every` | `hero_rz` · `dowel_step` | — |
| cavilha (`dowel.stl`) | PIN de duas pontas (`pin-dowel.stl`) | `pin.scad` com `ends = 2` |

O BOM lista cada STL com os parâmetros do OpenSCAD, na orientação de impressão — por isso ali aparecem `face_zn`, `pin`, `recess`.

Para reescrever um `assembly.toml` antigo com os nomes atuais: `python3 hack/scripts/fb_migrate.py <arquivo>`.

---

## Porta

Uma **porta** é o centro de célula de uma face. Quando duas peças encostam face com face, cada centro de célula compartilhado forma um par de portas.

| Face A | Face B | Resultado | O compilador |
| --- | --- | --- | --- |
| `socket` | `socket` | junção por cavilha, nada protrui | insere uma cavilha |
| `stud` | `socket` | junção por pino impresso, sem peça solta | — |
| `socket` | `flat` | apoio, sem junção | — |
| `flat` | `flat` | apoio, sem junção | — |
| `stud` | `stud` | **erro**: dois pinos colidem | rejeita |
| `stud` | `flat` | **erro**: pino contra face lisa | rejeita |

A face padrão é `auto`: `socket` se a peça é furada naquele eixo (`holes`), `flat` se não é (REQ-005 do BRICK). `socket` declarado num eixo sem furo é erro.

---

## Regras

**ASM-001 — Grid.** Toda peça MUST ser ancorada em células: X e Y inteiros, Z em múltiplos de meia célula (para empilhar sobre laje de `grid/2`). O bloco não gira: dimensões e faces são declaradas no referencial do mundo. Isso elimina a classe inteira de erros de rotação.

**ASM-002 — Ocupação.** Duas peças MUST NOT ocupar o mesmo volume, e nenhuma peça MUST invadir um componente. A checagem é por intervalo em mm: caixas para bloco, nó e componente, caixa orientada (teste de eixo separador) para a diagonal, cilindro para a roda.

**ASM-003 — Par de portas.** Todo par MUST cair numa linha válida da tabela acima.

**ASM-004 — Rigidez.** Uma peça MUST ter junções fora de uma única linha de eixo. Junções todas coaxiais (inclusive uma só) deixam a peça girar em torno delas: o press-fit segura por atrito, não contra torque. Exceção: a peça declarada em `hinges`, quando girar é a intenção.

O critério é geométrico, não uma contagem: duas junções coaxiais ainda giram, e duas junções em células vizinhas já travam. Ele não depende de `tolerance` — a calibração muda a força da junção, não se ela gira.

**Membro de treliça.** Uma barra de seção `1×1` (bloco `1×1×n` ou a viga de uma diagonal) presa pelas **duas pontas**, ao longo do próprio eixo, só pode girar sobre si mesma: a posição não muda e a estrutura não se mexe. É informada, não reprovada. Presa por uma ponta só, continua sendo erro.

**ASM-005 — Conectividade.** O grafo de peças, com junções como arestas, MUST ser um componente único. Contato sem junção não conta: peça só apoiada é peça solta.

**ASM-006 — Furo compartilhado.** Dois pinos entrando pelo mesmo furo, de lados opostos, MUST caber: `2·pin_len + gap ≤ extensão da peça naquele eixo`. Numa célula sempre cabe (4.5 ≤ 8mm). Numa laje de `grid/2` (4mm) **não cabe**: cada furo serve um lado por vez.

**ASM-007 — Passagem de fio.** Uma rota declarada em `routes` MUST percorrer furos contíguos (`holes`). Na escala micro o pino é maciço e fecha o furo, então:
- um encontro `socket × socket` cruzado pela rota fica **sem cavilha** (porta aberta para o fio)
- um encontro `stud × socket` cruzado pela rota é erro

**ASM-008 — Diagonal.** Uma diagonal (`strut`) liga dois nós. O vetor entre os nós é inteiro em células e seu módulo MUST ser inteiro — terno pitagórico (3-4-5, 6-8-10, 5-12-13) ou alinhado a um eixo. A viga mede `|Δ| − 1` células, porque cada nó avança `grid/2`. Cada nó MUST ter porta apontando para a viga, e nenhum OUTRO braço do nó MUST invadir a ponta da viga — um braço a 90° da diagonal invade; a ~127° não.

**ASM-009 — Dispositivo.** *(próxima versão do compilador)* O eixo de um DOCK MUST coincidir com um centro de célula.

**ASM-010 — Roda.** Uma roda MUST ocupar a célula encostada numa face, com o eixo numa porta `socket`. O eixo (AXLE) entra como qualquer pino e conta para ASM-006. O compilador informa o vão livre do chão e avisa se a estrutura desce abaixo das rodas.

**REQ-010 — Pino em aresta arredondada.** Uma face com pino (`stud`) MUST NOT estar numa aresta arredondada de raio maior que `grid/2 − collar_d/2` (1.7mm): a base do colar ficaria solta no ar. Peça de ponta redonda junta por **cavilha** (`socket × socket`), como um kit técnico — ou leva pinos só nas células planas (`studs_on = "inner"`). Mesmo assert no `brick.scad`.

**ASM-011 — Pino livre.** Pinos sem par são informados. Pino na face de baixo da peça mais baixa é aviso: a montagem não assenta plana.

O encaixe simultâneo nas 6 faces (constituição § 5) não precisa de checagem na montagem: é garantido pelo teto de `pin_len` em cada peça.

---

## Formato — `assembly.toml`

```toml
[assembly]
name   = "mini"
intent = "base com viga, rampa, roda e bateria"
# 1 célula = grid (8mm). Origem no canto da base, frente em +X, Z para cima.

parts = [
  { id = "base",  type = "brick",     at = [0, 0, 0], size = [10, 6, 1] },
  { id = "viga",  type = "beam",      at = [0, 0, 1], size = [10, 1, 1], studs = "bottom" },
  { id = "pe",    type = "brick",     at = [1, 5, 1], size = [1, 1, 1] },
  { id = "rampa", type = "strut",     from = [2, 5, 1], to = [6, 5, 4] },      # diagonal 3-4-5
  { id = "poste", type = "brick",     at = [7, 5, 1], size = [1, 1, 4] },
  { id = "roda",  type = "wheel",     at = [2, -1, 1], on = "viga.right", diameter = 4 },
  { id = "bat",   type = "component", at = [3, 1, 1], size_mm = [48.5, 26.5, 17.5], label = "9V" },
]
groups = [ { id = "tudo", parts = ["base", "viga", "pe", "rampa", "poste"], note = "…" } ]   # = passos de montagem
routes = [ { id = "fio", path = [[0,1,0], [9,1,0]] } ]                                       # ASM-007
hinges = []                                                                                  # ASM-004: peças que giram de propósito
```

| Tipo | Campos | Observação |
| --- | --- | --- |
| `brick` | `at` (canto mínimo), `size` (células), `holes` (`"xyz"`, `"xz"`, `"none"`), `faces` (`{ bottom = "stud", default = "auto" }`), `thickness` (mm, chapa), `rounded` (`x`/`y`/`z`: arestas paralelas a esse eixo arredondadas), `corner_r` (padrão `grid/2`), `studs_on` (`all` / `edge`: só o perímetro / `inner`: só as células planas de uma peça arredondada) | não gira (ASM-001) |
| `curve` | `at` (1ª célula do arco), `dir` (avanço na entrada), `turn` (para onde vira), `radius` (1, 2 ou 3 células de lado), `angle` (90/180), `ports` | liga só pelas pontas; o miolo da curva fica livre |
| `strut` | `from`, `to` (células das pontas), `from_arm`, `to_arm` (braço de cada nó; padrão: eixo dominante, para trás da diagonal), `style` (`beam`/`box`) | cria `<id>-n0`, `<id>-n1` e `<id>-v`; comprimento e orientação calculados (ASM-008) |
| `wheel` | `at` (célula encostada na face), `on` (`"<peça>.<face>"`), `diameter` (células), `width` (células), `tread` (`street`/`offroad`/`balloon`), `spokes`, `spoke_style` (`straight`/`y`) | eixo AXLE inferido |
| `component` | `at` (células, aceita fração), `size_mm`, `shape` (`box`/`cyl`/`text`/`cable`), `axis`, `label`, `mass` (g), `color` `[r,g,b,a]`; `text`; `points` (cabo, em células) | não imprime, não conecta; `box`/`cyl` colidem, `text`/`cable` não |
| `node` | `at` (célula), `dirs` (vetores inteiros, um por porta), `ports` (`"stud"` padrão, ou lista), `fillet` (mm) | uso avançado: nó com 3+ portas. `strut` aceita `from`/`to` como ids de nós |

Todos aceitam `color = [r, g, b]`. No `[assembly]`: `dowel_every = N` põe uma cavilha a cada N furos de cada encontro `socket × socket` (a primeira e a última sempre entram); `view_angle` gira a vista principal.

### Variantes — bloco com padrões

Uma variante **não é peça nova**: é um bloco com padrões já escolhidos, para o caso comum sair em uma linha. Qualquer campo escrito na peça **vence** o padrão — o controle paramétrico completo continua lá.

| Variante | Padrões que aplica |
| --- | --- |
| `beam` | `holes = "xyz"`, `rounded` no eixo que deixa os furos à vista de lado (viga em X ou Z → `y`; em Y → `x`). Exige seção 1×1 |
| `plate` | `thickness = 4`, `holes = "z"`, `rounded = "z"`, `corner_r = 4` |
| `cover` | `thickness = 4`, `holes = "none"`, `rounded = "z"`, `faces.bottom = "stud"`, `studs_on = "edge"` (tampa lisa sobre um quadro) |

Atalhos válidos em qualquer bloco ou variante:

| Atalho | Equivale a |
| --- | --- |
| `studs = "top"` / `"bottom"` | `faces.top` / `faces.bottom` `= "stud"`; em peça arredondada, também `studs_on = "inner"` |
| `studs = ["left", "right"]` | essas faces `= "stud"` |
| `flat = ["back"]` | essas faces `= "flat"` |

Fonte única: `impl/python/fusionbrick/asm/variants.py` (o schema e a skill leem de lá).

### Como o compilador é organizado

Cada tipo de peça responde às mesmas quatro perguntas — onde fica (`resolve`), onde encaixa (`ports`), que volume ocupa (`boxes`), que STL é (`config`) — e nada mais no compilador ramifica por tipo. Toda junta nasce do mesmo passo: **duas portas na mesma posição, apontando uma contra a outra**, decididas pela tabela de portas acima. Tipo novo de peça = uma classe em `asm/parts.py`.

| Módulo (`impl/python/fusionbrick/asm/`) | Papel |
| --- | --- |
| `model.py` | achado, porta, junta, peça-base |
| `names.py` | vocabulário público ↔ nomes internos; expande `strut` |
| `parts.py` | `brick`, `node`, `strut`, `curve`, `wheel`, `component` |
| `variants.py` | variantes e atalhos → bloco explícito |
| `compile.py` | leitura da IR, posicionamento, juntas |
| `checks.py` | uma função por regra ASM-### |
| `outputs.py` | BOM, passos, relatório, `assembly.scad` |
| `metrics.py` | `stats` (qualidade) e `physics` (massa, tombamento) |

O JSON Schema equivalente sai de `fb_assemble.py schema`, para preencher via *tool use*.

### ASM-012 — Montagem à mão (aviso)

Na ordem dos `groups` (depois as peças fora de grupo), cada peça encaixa nas já montadas com **um** movimento: todas as juntas novas no mesmo eixo e no mesmo sentido. Grupo com `sub = true` é um subconjunto montado à parte e entra como um corpo só. Ficam de fora eixos de roda e juntas diagonais. É aviso, não erro: press-fit com folga às vezes fecha com flexão — mas diga ao usuário.

**Ainda não suportado:** DOCK (ASM-009), o recurso central e portas laterais da diagonal e da curva (os furos transversais são visuais; na curva eles nem caem no grid, salvo no eixo de simetria).

---

## Saídas

| Arquivo | Conteúdo |
| --- | --- |
| `report.txt` | o veredito: contagens + achados por severidade |
| `assembly.scad` | gerado, **não editar** — importa os STLs e posiciona com `multmatrix` |
| `parts/*.stl` | um por configuração única; peças que são a mesma girada compartilham STL |
| `bom.md` | lista de peças para imprimir |
| `steps.md` | passo a passo, na ordem de `groups` |
| `assembly*.png` | com `--png`: isométrica, explodida, lateral, topo, traseira |

```bash
make assemble NAME=rover-tub          # check + STLs + .scad + BOM + passos + PNGs
make assemble-check NAME=rover-tub    # só valida (milissegundos)
make assemble-stats NAME=rover-tub    # qualidade: resolução, cavilhas, reuso
make assemble-test                    # testes do compilador
```
