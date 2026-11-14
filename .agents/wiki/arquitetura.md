# Arquitetura

O repositório é organizado em quatro camadas com responsabilidades distintas e sem código de aplicação: **contrato** (`spec/`), **implementação geométrica** (`impl/openscad/`), **automação de artefatos** (`hack/automations/` + `Makefile`) e **verificação por montagem** (`examples/`). Os artefatos resultantes são versionados em `renders/`.

## Contrato: `spec/` como fonte de verdade

`../../spec/design-system.md` enumera seis premissas que governam qualquer mudança — entre elas "o grid é sagrado" (`cell_size = 20` nunca muda por causa de uma junção), "circuito elétrico passa por padrão", "compatibilidade é permanente", "interfaces não competem", "press-fit primeiro" e "spec-first". A premissa 6 é explícita: divergência entre `spec/` e `impl/` é bug da implementação, ou proposta de mudança que deve começar pela spec.

`../../spec/params.md` é a tabela de parâmetros que **todas** as peças devem repetir com valores idênticos (`cell_size`, `hole_d`, `relief_depth`, `relief_margin`, `tolerance`, `canal_d`, `thickness`, família `edge_*`, `border_radius`, `border_style`, `$fn`). Não existe arquivo de parâmetros compartilhado no OpenSCAD: cada `.scad` **redeclara** os mesmos defaults no próprio topo. A consistência é, portanto, uma convenção verificada por leitura e pelas asserções de `echo` de cada peça — não por um mecanismo de linguagem.

`../../spec/rules.md` formaliza as regras que a geometria precisa respeitar:

- **Lei do Grid** — o volume do grid é delimitado pelas faces internas das PLATEs; a espessura da PLATE vive fora do grid. Consequência prática usada em todas as montagens: paredes e trilhos ficam em coordenadas negativas ou além do footprint.
- **1 pino por furo** na interface de face: a alma da PLATE entre os dois rebaixos vale `thickness − 2×relief_depth = 1mm`, então o segundo conector no mesmo furo entra flange-only (`pin = 0`).
- **Interface de borda** — furos `Ø3 × 4mm` a `edge_inset = 2.5mm` das extremidades de cada célula, com rebaixo de colar `Ø3.8 × 1mm`; todo macho tem `edge_pin_len = 2.25mm` para que dois machos opostos dividam um furo passante compartilhado (`2.25 + 2.25 = 4.5 ≤ 5 − 0.5`).

`../../spec/parts/` mantém uma spec por peça (`atom`, `plate`, `link`, `bridge`, `corner`, `pin`, `elbow`, `vertex`) com intenção, geometria e restrições.

## Implementação: `impl/openscad/`

`impl/` contém apenas o subdiretório `openscad/`. Cada peça é um arquivo autônomo que segue sempre a mesma ordem: parâmetros com faixas de customizer (`hole_d = 10; // [0.5:0.1:15]`), valores calculados, módulos, chamada de render e bloco de `echo` com dimensões e verificações.

Três convenções amarram os arquivos entre si:

1. **`part_color` sobrescrita externamente.** Todo arquivo declara `part_color = [0.35, 0.38, 0.42]` e renderiza `color(part_color) <peça>()`. A automação injeta outro valor via `-D` (`impl/openscad/atom.scad`, `impl/openscad/plate.scad`, etc.). `color()` só tem efeito em `--preview`.
2. **Acabamento de aresta duplicado por peça.** `atom.scad`, `plate.scad`, `corner.scad`, `pin.scad`, `elbow.scad` e `vertex.scad` cada um define seu próprio `border_finish(r)` — esfera para `border_style = "round"`, `polyhedron` octaédrico para `"chamfer"` — aplicado via `minkowski()`, e um `safe_radius` que satura o raio pela seção da peça. `elbow.scad` é a exceção de técnica: usa `offset(r=...)`/`offset(delta=..., chamfer=true)` sobre o perfil 2D antes do `rotate_extrude`.
3. **Asserções por `echo`.** Cada arquivo termina imprimindo "SIM"/"VERIFICAR" para as invariantes que lhe cabem (parede mínima, pino que não invade rebaixo oposto, dois machos numa seção compartilhada). Ver [Testes](testes.md).

O único arquivo que reaproveita outro é `impl/openscad/link-oneside.scad`, que faz `use <link.scad>` e fixa a variante `link(pin_a = 1, pin_b = 0)` apenas para ganhar preview e STL automáticos do Make.

O catálogo completo, com o que cada peça resolve e a interface que usa, está em [Peças e interfaces](pecas.md).

## Sistemas de coordenadas — a fronteira mais escorregadia

Os módulos **não compartilham a mesma origem**, e isso é o que determina como as montagens são escritas:

| Módulo | Volume ocupado pelos defaults | Observação |
| --- | --- | --- |
| `plate()` | `20 × 20 × 5` **centrado na origem** | célula `(cx,cy)` do piso: `translate([cx*20+10, cy*20+10, 2.5])` |
| `atom()` | `[0,20]³` — canto na origem | grid interno cresce em `+X/+Y/+Z` conforme `qty_*` |
| `link()` | centrado no **plano da junção** entre os flanges | posicionar independe de `pin_a`/`pin_b`; lado A em `+Z` |
| `bridge()` | dowel no eixo X, centrado na costura `x = 0` | ao longo de Y: `rotate([0,0,90])` |
| `corner()` | viga `x ∈ [-5,0]`, `y ∈ [0,20]`, `z ∈ [0,5]` | pinos nas faces `+X` e `+Z`; canal axial `Ø3` |
| `pin()` | viga ao longo de Y `[0,20]`, seção `5×5` centrada em X/Z | features por grupo de faces, com presets |
| `elbow()` | quarto de cilindro `r = 5`, `z ∈ [0,5]`, 1º quadrante | portas nas faces `X=0` e `Y=0` |
| `vertex()` | cubo `[0,5]³` | pinos/furos nas faces `X=0`, `Y=0`, `Z=0`; ponta externa arredondada |
| `wheel()` | cilindro `Ø20 × 8`, eixo Z, centrado | furo central `Ø10` com rebaixo nas duas faces |
| `track()` | cápsula ao longo de X, altura em Y, espessura em Z | 2 furos `Ø10` distantes `cells × cell_size` |

Há também um comportamento contraintuitivo do OpenSCAD documentado no repositório e usado em toda parte: `rotate([90,0,0])` aponta `+Z` para **−Y**; para `+Y` usa-se `rotate([-90,0,0])` (comentários em `impl/openscad/plate.scad` e no `README.md`/`CLAUDE.md`).

## Montagens: `examples/*/assembly.scad`

As montagens são a camada de verificação de sistema. Elas importam as peças com `use <../../impl/openscad/*.scad>` — o que traz **apenas os módulos com seus defaults**, sem executar o render top-level de cada arquivo e sem permitir sobrescrever parâmetros. Daí a consequência estrutural: uma PLATE é sempre `1×1`, e áreas maiores são feitas por ladrilho de PLATEs mais dowels nas costuras.

Toda montagem expõe três parâmetros de controle:

- `explode` — afastamento em mm, aplicado por nível (`ez1`, `ez2`, `ez3` em `examples/rover-chassis/assembly.scad`), usado pela automação para as vistas explodida e animada;
- `check_collisions` — adiciona `intersection()` par a par em vermelho;
- `collisions_only` — oculta as peças e deixa só as interseções, o que permite exportar um STL cujo volume mede a colisão.

`examples/u-channel/assembly.scad` é o teste canônico da Lei do Grid: 3 PLATEs coplanares travadas por 2 BRIDGEs cada junção, 2 paredes fora do grid, 2 CORNERs preenchendo as lacunas de canto e 1 ATOM interno ligado por LINKs assimétricos (`link(pin_a = 3, pin_b = 1)` — 3 mm no lado ATOM, 1 mm na alma da PLATE). `examples/rover-chassis/assembly.scad` é o caso complexo: piso 4×3 com dowels em todas as costuras, capô/deck empilhados por LINK, trilhos de CORNER fora do grid, para-choques de PIN, ELBOWs arredondando os quatro cantos e gaiola de PINs fechada por VERTEXes.

## Automação: `Makefile` → `core.mk` → `openscad.mk`

O `Makefile` da raiz só resolve `ROOT_DIR` e inclui `hack/automations/core.mk`. `core.mk` inclui `hack/automations/openscad.mk` e adiciona a regra-padrão `openscad-%`, que reencaminha `openscad-preview`/`openscad-build` para o alvo homônimo em `openscad.mk` — um namespace explícito para quando outra implementação for adicionada.

`openscad.mk` concentra toda a lógica e descobre o trabalho dinamicamente:

```make
PARTS      := $(basename $(notdir $(wildcard $(IMPL_DIR)/*.scad)))
ASSEMBLIES := $(wildcard examples/*/assembly.scad)
```

Adicionar um `.scad` em `impl/openscad/` ou um `examples/<nome>/assembly.scad` já o inclui em todos os targets, sem editar o Makefile. Os detalhes de cada target e variável estão em [Operações](operacoes.md).

## Fronteiras e o que não existe no repositório

- `impl/` tem **apenas** `openscad/`. `impl/fusion360/` e `impl/manual/`, listados como estrutura no `README.md`, não existem como diretórios — são roadmap.
- Não há código de aplicação, servidor, HTTP, banco de dados ou gerenciador de pacotes: não existem `go.mod`, `package.json` ou equivalentes. O diretório `apps/*` está presente na árvore de trabalho vazio e sem nenhum arquivo versionado (`git ls-files apps` não retorna nada), logo não faz parte do sistema.
- Não há suíte de testes automatizada nem CI configurado no repositório; a verificação é a descrita em [Testes](testes.md).

## Divergências entre documentação e código

Registradas por serem armadilhas reais para quem for mexer no projeto — em todos os casos o código atual é a referência:

1. **`make preview` e `border_radius`.** `CLAUDE.md` afirma que `make preview` injeta `border_radius=1`. A receita `preview` de `hack/automations/openscad.mk` injeta apenas `part_color`; `border_radius`/`border_style` só são passados por `-D` na receita `build`, com default `BORDER_RADIUS := 0`.
2. **`assembly-video` e `ffmpeg` não documentados.** O target `assembly-video` existe em `openscad.mk` e depende de `ffmpeg` (fixado em `.tool-versions`), mas nem o `README.md` nem `CLAUDE.md` o listam entre comandos ou dependências.
3. **`track` e `wheel` sem contrato.** `impl/openscad/track.scad` e `impl/openscad/wheel.scad` existem e usam a interface de face (`hole_d = 10` + rebaixos), mas não têm spec em `spec/parts/`, não aparecem na tabela de componentes do `README.md` e não têm artefatos em `renders/img/` nem `renders/stl/` — contrariando a premissa spec-first de `spec/design-system.md`.
4. **Exemplo inexistente citado.** `.claude/skills/fusionbrick-builder/SKILL.md` cita `examples/car-body/` como exemplo de referência; o diretório não existe (só `examples/u-channel/` e `examples/rover-chassis/`).
5. **Variáveis mortas na automação.** `IMG_W`, `IMG_H`, `GRAD_TOP` e `GRAD_BOT` são definidas em `openscad.mk` e nunca referenciadas; `.PHONY` declara `_assembly-frames`, que não existe como target — a lógica compartilhada de frames é o `define ASM_RENDER_FRAMES`.
6. **Artefato estranho versionado.** `console-full.log` está versionado na raiz e contém log de console de navegador (Vite/React/three.js), sem relação com o conteúdo OpenSCAD do repositório.
