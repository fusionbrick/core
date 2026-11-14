# Peças e interfaces

São 11 arquivos em `impl/openscad/` — 11 peças renderizáveis, porque `link-oneside.scad` é uma variante fixada do LINK e não uma geometria nova. Cada peça pertence a uma das duas interfaces de encaixe do sistema (ou às duas), e é a interface que determina o que encaixa em quê.

## As duas interfaces

### Interface de face

Furo passante `hole_d = 10mm` com rebaixo `relief_d = hole_d + relief_margin×2 = 14mm` e `relief_depth = 2mm` **nas duas faces**. Presente nas 6 faces do ATOM (`impl/openscad/atom.scad`), nas faces topo/base da PLATE, no furo central da WHEEL e nos dois furos de montagem da TRACK.

O conector é o LINK: `pin_d = hole_d − tolerance = 9.8mm` entra no furo, `flange_d = relief_d − tolerance = 13.8mm` assenta no rebaixo. O ponto crítico é que na PLATE o pino só tem contato na **alma** entre os dois rebaixos: `thickness − 2×relief_depth = 1mm`. Daí duas regras que aparecem tanto em `spec/rules.md` quanto nas asserções de `impl/openscad/link.scad`:

- pino de `1mm` no lado que entra em PLATE, `3mm` no lado que entra em ATOM (furo de 20 mm);
- **1 pino por furo** — o segundo conector no mesmo furo entra flange-only (`pin = 0`), segurando pelo ajuste do flange no rebaixo.

Furos laterais em PLATE são impossíveis por construção (`hole_d = 10 > thickness = 5`), o que é exatamente o motivo de existir a segunda interface.

### Interface de borda

Interface pura pino → furo, sem rebaixos de face, nas bordas das PLATEs e nas faces laterais dos ATOMs:

| Elemento | Valor | Onde é gerado |
| --- | --- | --- |
| Furo | `edge_hole_d = 3mm`, profundidade `edge_hole_depth = 4mm` | `edge_hole_cut()` em `plate.scad`, `atom_edge_hole_cut()` em `atom.scad` |
| Posição | `edge_inset = 2.5mm` das duas extremidades de cada célula (posições 2.5 / 17.5) | listas `pin_positions` / `xs`,`ys`,`zs` |
| Rebaixo do colar | `Ø3.8 × 1mm` na boca (`edge_collar_w = 0.4`, `edge_collar_depth = 1`) | mesmos módulos de corte |
| Macho | haste `Ø2.8` (`edge_hole_d − tolerance`) + colar `Ø3.6 × 1mm` na raiz, total `edge_pin_len = 2.25mm` | `edge_pin()` em `corner.scad`, `pin.scad`, `elbow.scad`, `vertex.scad` |

O colar é uma trava de profundidade: no dowel ele fica no centro e divide o comprimento 50/50 entre os dois furos; nos machos ele fica na raiz e impede afundamento, além de reforçar a haste. O comprimento `2.25mm` existe para que **dois machos opostos** compartilhem um furo passante de uma seção de 5 mm (`2.25 + 2.25 = 4.5 ≤ 5 − 0.5`). Machos **perpendiculares no mesmo nível** colidiriam no centro da seção — a regra de uso (em `spec/rules.md`) é alternar eixos entre as duas posições da célula.

A vantagem sistêmica: junções por borda não consomem nenhum furo de face, então LINK e ATOM continuam podendo conectar em qualquer célula, inclusive nos cantos.

## Catálogo

### Corpos

**ATOM** — `impl/openscad/atom.scad`. Cubo `atom_size = 20`, furo passante nos 3 eixos com rebaixo nas 6 faces. Suporta grid interno via `qty_x`/`qty_y`/`qty_z` (o módulo `atom_grid()` replica a unidade) e os furos de borda são recortados **apenas nas 4 faces laterais externas** do grid resultante, 4 por face por célula (2 embaixo + 2 em cima). Origem no canto: ocupa `[0, qty*20]`.

**PLATE** — `impl/openscad/plate.scad`. Placa `cell_size × qty_x` por `cell_size × qty_y` por `thickness = 5`, centrada na origem, com a grade de furos alinhada ao ATOM e furos de borda nas 4 bordas (2 por célula). Dois clamps de segurança: `safe_relief` limita o rebaixo a `thickness/2 − 0.5` para garantir alma, e `safe_radius` limita o arredondamento pela espessura e pela célula.

### Conector de face

**LINK** — `impl/openscad/link.scad`. Dois semi-links espelhados com profundidade de pino independente por lado (`pin_depth_a`/`pin_depth_b`, `0` = flange-only), `spacer` opcional e canal de fio `canal_d = 6`. Detalhe deliberado e importante para montagens: o módulo é centrado no **plano da junção** (entre os flanges), não no meio do comprimento — assim o `translate` de posicionamento não muda quando os pinos mudam. A assimetria entra por argumento: `link(pin_a = 3, pin_b = 1)`.

**LINK-ONESIDE** — `impl/openscad/link-oneside.scad`. Não define geometria: faz `use <link.scad>` e renderiza `link(pin_a = 1, pin_b = 0)`. Existe para materializar a regra "1 pino por furo" como peça imprimível e para ganhar preview/STL automáticos do Make.

### Conectores de borda

**BRIDGE** — `impl/openscad/bridge.scad`. Dowel `Ø2.8` no eixo X centrado na costura `x = 0`, com colar central. O meio-comprimento é o mínimo entre não bater no fundo do furo (`edge_hole_depth − 0.5`) e caber num furo passante compartilhado (`shared_sec/2 − 0.25`), resultando `2.25mm` por lado. Sem canal de fio — a seção não comporta; os fios passam pelos furos de face, que a BRIDGE deixa livres. Uso: 2 dowels por junção para travar rotação.

**CORNER** — `impl/openscad/corner.scad`. Viga que preenche exatamente a lacuna `wall_thickness × plate_thickness` do encontro a 90° de duas PLATEs: ocupa `x ∈ [-5,0]`, `z ∈ [0,5]`, comprimento `cells × cell_size` em Y. Pinos em duas faces perpendiculares (`+X` para os furos de borda da base, `+Z` para os da parede) e canal axial `canal_d = 3` (passa jumper Dupont). As bocas do canal recebem rebaixo de colar, o que permite o encaixe em "L": o pino da ponta de outra viga entra no canal desta.

**PIN** — `impl/openscad/pin.scad`. Generalização do CORNER: viga de seção `sec_w × sec_h = 5 × 5` onde **cada grupo de faces** (topo, base, laterais `±X`, pontas `±Y`) pode ser `pin`, `hole` ou `none`. Os presets `full_pins_hole_bottom` e `full_holes` sobrepõem a configuração `custom` por meio das variáveis `top_c`/`bottom_c`/`sides_c`/`ends_c`. Com furos opostos numa seção de 5 mm o bore vira passante — comportamento esperado, dimensionado para receber um macho de cada lado.

**ELBOW** — `impl/openscad/elbow.scad`. Curva de 90° obtida por `rotate_extrude(angle = 90)` de um perfil `5 × 5`, raio externo igual à seção, com duas portas (`port_a` na face `Y=0`, `port_b` na face `X=0`) que podem ser pino ou furo. Quando **as duas** portas são furo, um canal curvo `Ø3` é subtraído e o fio vira a esquina por dentro da peça.

**VERTEX** — `impl/openscad/vertex.scad`. Cubo `5³` com as três faces internas (`X=0`, `Y=0`, `Z=0`) configuráveis em `pin`/`hole`/`none` no centro de cada face, e ponta externa arredondada — único arquivo cujo `border_radius` tem default `2`. O corpo é um `hull()` de três lajes com o sólido de acabamento no canto externo, o que preserva as três faces internas planas para o encaixe ficar flush. Com 2+ faces em `hole`, os furos se cruzam no centro do cubo (profundidade 4 > 2.5) e o fio dobra por dentro.

### Peças de locomoção (sem spec)

**WHEEL** — `impl/openscad/wheel.scad`. Roda `Ø20 × 8` com sulcos radiais na banda e furo central `Ø10` com rebaixo nas duas faces: monta em qualquer face de ATOM ou PLATE com um LINK comum, sem eixo dedicado. Eixo de rotação em Z.

**TRACK** — `impl/openscad/track.scad`. Esteira em cápsula (`hull` de dois cilindros) com dentes de tração no perímetro inferior e dois furos `Ø10` separados por `cells × cell_size`, ou seja, no passo do grid.

Ambas usam a interface de face corretamente, mas não têm contrapartida em `spec/parts/` nem artefatos em `renders/` — ver [as divergências registradas](arquitetura.md#divergências-entre-documentação-e-código).

## Padrões de junção já validados

Extraídos das montagens em `examples/` e consolidados em `.claude/skills/fusionbrick-builder/SKILL.md`:

- **Empilhar placa sobre placa/ATOM** — `link()` no furo de face, `spacer = 0`; mais aderência no lado ATOM com `link(pin_a = 3, pin_b = 1)`.
- **Dois conectores no mesmo furo de PLATE** — o segundo entra flange-only (`pin_b = 0`) ou usa a peça `link-oneside`.
- **Placas lado a lado** — 2 `bridge()` por junção, nos furos de borda em 2.5 e 17.5.
- **Parede a 90° sobre uma base** — parede assentada fora do grid + `corner()` espelhado preenchendo a lacuna `5×5`.
- **Poste vertical** — `pin()` em pé sobre o pino `+Z` de um trilho de `corner()`; dois PINs mais dowel axial dão 40 mm.
- **Canto 3-vias e canto arredondado** — `vertex()` para o encontro de três direções, `elbow()` para ligar ponta de viga ao canal de outra com curva.

## Vocabulário de montagem

As seções acima descrevem as peças no OpenSCAD. Quem **monta** (`examples/<nome>/assembly.toml`, compilador em `impl/python/fusionbrick/asm/`) usa um vocabulário próprio, com um nome por conceito. Fonte única: `impl/python/fusionbrick/asm/names.py`; tabela completa e ponte para os parâmetros do OpenSCAD em `spec/assembly.md` § Nomes.

| Peça (`type`) | O que é |
| --- | --- |
| `brick` | bloco: a peça-base |
| `beam` · `plate` · `cover` | viga · placa · tampa — blocos com padrões já escolhidos |
| `curve` | curva de 90° ou 180° (`impl/openscad/curve.scad`) |
| `strut` | diagonal entre duas células; cria os próprios nós |
| `wheel` | roda com eixo |
| `component` | o que se compra pronto; não imprime |

Encaixes: `stud` (pino impresso), `socket` (encaixe), `flat` (liso); cavilha = PIN de duas pontas que une dois `socket`. Faces: `front`/`back` (±X), `left`/`right` (±Y), `top`/`bottom` (±Z). Os nomes antigos (`liftarm`, `tile`, `bend`, `mock`, `pin`/`recess`/`plain`, `xn…zp`) continuam aceitos.
