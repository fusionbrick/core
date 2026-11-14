# BRICK — plano de implementação

Como cada implementação realiza [`spec.md`](spec.md), e **onde não realiza**.

Contrato: [`contracts.toml`](contracts.toml) · Status: [`tasks.md`](tasks.md)

---

## Implementações

| | Arquivo | Cobre | Verificado por |
| --- | --- | --- | --- |
| **OpenSCAD** | `impl/openscad/brick.scad` | tudo: células, pele, laje, eixos, faces, recurso central, presets | `make spec-check` [3] · `assert` no próprio arquivo |
| **Python (core)** | `impl/python/fusionbrick/` | primitivos, derivados, invariantes, regras, posições de furo/face | `make spec-check` [2] · 19 testes |
| **Fusion 360** | `impl/fusion360/FusionBrick/` | célula `1×1×1` apenas | nada automático — `adsk` só existe dentro do Fusion |
| **Make** | `hack/automations/variables.mk` | injeta os primitivos em toda chamada do OpenSCAD | `make spec-check` [4] |

O OpenSCAD é a implementação de referência: é a única completa.

---

## Estratégia por ferramenta

### OpenSCAD

Geometria por CSG: bloco, `difference()` dos furos e rebaixos, `union()` dos machos.

Os primitivos vivem em `impl/openscad/params.scad`, incluído por toda peça. Eram 28 declarações (7 valores × 4 peças) e viraram 7 — foi a duplicação que deixou `pin_len` ficar 1.6 na spec e 2.0 nas implementações sem ninguém notar. O `spec-check` **detecta** divergência; a fonte única **impede** que exista.

`params.scad` não é peça: `variables.mk` a exclui do wildcard, senão o make geraria `params.stl`.

Variantes (HUB, PLATE) usam `include` e reatribuição, não módulo com argumento — ver spec.md § Variantes persistidas.

### Python (core)

`Primitives` é `@dataclass(frozen=True)` com os primitivos como campo e os derivados como `@property`. `BrickSpec` descreve **onde** as coisas ficam sem desenhar nada — é o que permite um adapter de CAD consumir a geometria sem reimplementar a lei.

`rules.py` implementa as validações do contrato. Os `id` são os mesmos de `contracts.toml`.

### Fusion 360

Sketch + features nativas, cada operação um nó na timeline. Os primitivos entram como **User Parameters** com valor; os derivados como **expressão** (`fb_grid = fb_hole_d + 2 * (fb_wall + fb_collar_w)`), para a derivação continuar viva dentro do documento.

Duas alternativas descartadas: **Custom Feature** (API ainda em preview — *"never deliver any programs that use any preview capabilities"* — e o recompute só cobre base+sketch+combine) e **B-Rep temporário** (corpo sem histórico, o usuário não edita cota).

Decisões que tiram palpite da geometria: `modelToSketchSpace` converte ponto global para o sistema do sketch; corte **simétrico** torna a direção irrelevante; a normal de plano é **lida** da geometria em vez de suposta.

---

## Lacunas conhecidas

| Lacuna | Onde | Efeito |
| --- | --- | --- |
| Fusion faz só `1×1×1` | `BrickCommand.py` | sem células múltiplas, pele, laje, eixos/faces configuráveis, recurso central |
| Recurso central só no eixo Z | `brick.scad` | não reproduz o ATOM original, que tinha macro nas 6 faces (falta `center_axes`) |
| Core Python só tem BRICK | `impl/python/` | PIN, NODE e DOCK não existem lá |
| `dist/fusion360/` versionado | — | cópia do core produzida por `make fusion-vendor` |
| AC-012 sem automação | — | encaixe simultâneo nas 6 faces é medido à mão |
| `tolerance` sem calibração | — | nunca conferida contra impressão real |

---

## O que o contrato NÃO impõe

`contracts.toml` é fonte de verdade **verificada**, não geradora. As implementações continuam declarando seus próprios valores; o check detecta divergência, não a impede.

Gerar o fragmento de `variables.mk` e as `@property` de `params.py` a partir do contrato é o passo seguinte natural — aí a divergência ficaria impossível, não só visível.
