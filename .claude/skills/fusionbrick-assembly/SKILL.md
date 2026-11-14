---
name: fusionbrick-assembly
description: Monta protótipos com peças FusionBrick a partir de texto ou imagem — escreve examples/<nome>/assembly.toml (direto ou por gen.py), compila com o validador de encaixe e itera até ficar fiel e detalhado. Use quando pedirem para montar, construir, criar ou prototipar um objeto (rover, carro, buggy, caixa, suporte, case, organizador, robô, gaiola, estrutura) com o sistema. Triggers - "monta um", "constrói", "build a", "protótipo de", "assembly", "com as peças", "a partir desta imagem/croqui", "corpo de prova".
---

# FusionBrick Assembly

Você decide **o quê e onde** no grid. O compilador decide **o como**: insere as cavilhas, valida o encaixe pelas regras ASM-###, gera `.scad`, STLs, lista de peças e passo a passo.

**Nunca escreva `translate`, `rotate`, mm de posição ou cavilha.** O `assembly.scad` é gerado; editá-lo é sempre errado.

| Arquivo | Para quê |
| --- | --- |
| `reference/catalog.md` | todos os tipos de peça, campos, padrões, medidas — **consulte antes de escrever IR** |
| `reference/patterns.md` | trechos validados para compor (chassi, caixa, anel curvo, pórtico, rampa, gaiola, rodas) |
| `reference/pitfalls.md` | erro → causa → correção, colhidos em montagens reais |
| `reference/quality.md` | o que separa "brinquedo de bloco" de "kit técnico": rubrica, métricas, revisão visual |
| `reference/image.md` | rota a partir de foto ou croqui |
| skill `fusionbrick-council` | o padrão de qualidade e o conselho (ficha `review` + Maker · Engenheiro · Designer) — portão final de toda entrega |
| `spec/assembly.md` | regras normativas (nomes, tabela de portas, ASM-001…012) |

## O vocabulário (um nome por conceito)

| Peças (`type`) | Encaixes | Faces (frente = +X) |
| --- | --- | --- |
| `brick` bloco · `beam` viga · `plate` placa · `cover` tampa | `stud` = pino impresso na face | `front` +X · `back` −X |
| `curve` curva · `strut` diagonal | `socket` = encaixe que recebe pino | `left` +Y · `right` −Y |
| `wheel` roda · `component` o que se compra pronto | `flat` = liso · cavilha = pino solto entre dois `socket` | `top` +Z · `bottom` −Z |

Os nomes antigos (`liftarm`, `tile`, `bend`, `mock`, `cells`, `axes`, `pin`/`recess`/`plain`, `xn…zp`) ainda compilam, mas **escreva sempre os atuais**. Tabela completa: `spec/assembly.md` § Nomes.

## As leis do grid (decore — quase todo erro vem daqui)

1. **1 célula = 8 mm.** `at` é o canto mínimo em células; X/Y inteiros, Z múltiplo de 0.5 (meia célula só sobre chapa).
2. **Toda junta é uma porta encostada noutra**, centro de face com centro de face. `stud × socket` = pino impresso, sem peça solta; `socket × socket` = cavilha inserida; `stud × stud` e `stud × flat` = erro.
3. **O bloco não gira**: `size` e `faces` no referencial do mundo. Peças iguais giradas saem do mesmo STL.
4. **Retas só a 0°/90°. Inclinação só com `strut`, e o vetor precisa fechar no grid**: 3-4-5 (36,9°/53,1°), 5-12-13 (22,6°), 8-15-17, em 3D 1-2-2 e 2-3-6. **45°, 30° e 60° não existem.**
5. **Curva só com `curve`**, 90° ou 180°. `radius` = células que ela ocupa de lado: 1 (1×1), 2 (2×2, padrão), 3 (3×3). A saída tem os papéis trocados (fronteira ↔ centro de célula).
6. **O braço de um nó fica a ≥127° da diagonal.** A 90° ele invade a ponta da viga. O `strut` já escolhe o braço padrão (o eixo dominante, para trás da diagonal); mude com `from_arm` / `to_arm`. Consequência: **não há triângulo de treliça** (banzo + diagonal no mesmo nó). Diagonais terminam "de lado", continuando a direção da viga (padrão *Rampa* em `patterns.md`).
7. **Junta é sempre contato de face.** O bloco liga em qualquer face, em qualquer célula, desde que outra face **encoste** nela (de topo ou empilhada — é assim que o cubo Technic `t2` fecha). Não existe pino atravessando um furo para prender algo afastado ou inclinado. Diagonal e curva ligam **só pelas pontas**; os furos ao longo delas são visuais.
8. **Ponta arredondada não leva pino** (REQ-010). Para empilhar vigas sem cavilha, use `studs = "top"` (ou `"bottom"`): numa viga, os pinos saem só nas células planas (buggy-vt3: 242 → 100 cavilhas).
9. **Rigidez (ASM-004)**: as junções de cada peça não podem estar todas numa linha. **Montagem (ASM-012)**: na ordem dos `groups`, cada peça entra nas anteriores com **um** movimento (um eixo, um sentido); subconjunto montado à parte = grupo com `sub = true`. Eixo de roda não conta como junta. Poste 1×1 preso só pelas pontas é "membro de treliça" (aceito, com aviso); bloco preso por uma junção só gira — use `hinges` se for de propósito.
10. **Chapa** (`plate`, `cover`, ou `thickness = 4.0`): tudo acima em `z + 0.5`; não ponha pino dos dois lados no mesmo furo (ASM-006).

## Fluxo com portões de qualidade

1. **Briefing.** Função, dimensões em mm, o que precisa caber (componentes com medida real), estilo (bloco liso × kit técnico), cores. Em montagem grande ou ambígua, **pergunte com opções** (AskUserQuestion), uma rodada só: escala, estilo, nº de rodas/eixos, o que é componente. Pedido claro: assuma, diga o que assumiu, siga.
2. **Escala = resolução.** Escolha o tamanho para que o objeto tenha **15–40 peças estruturais por 100 mm** da maior dimensão (`stats` mede). Pedido de "alta qualidade" ou "parecido com a foto" → escale para cima (o `buggy-vt2` é 1,8× a foto: 75 peças estruturais, 24,7 por 100 mm). Pedido de "simples" → 8–12.
3. **Esboço por camada.** Grade ASCII por nível de Z no topo do arquivo (cabeçalho do `gen.py` ou do TOML). Marque eixos de roda, vãos de componente, onde entra cada diagonal e cada curva.
4. **Escrever a IR.** Até ~30 peças sem simetria: TOML à mão (esqueleto abaixo). Acima disso, ou com simetria: **`gen.py` com `fusionbrick.irgen`** — `Build`, `brick/beam/plate/cover/curve/strut/wheel/component`, macros `ring()` (quadro de cantos curvos; divide vigas > 26 células) e `arch()` (arco aberto no plano Y-Z), `mirror_y()` (lado `_e` → `_d`). Componha padrões, nomeie `groups` na ordem de montagem.
5. **Checar** (ms; repita):
   ```bash
   python3 hack/scripts/fb_assemble.py check examples/<nome>/assembly.toml
   ```
   Corrija o **primeiro** erro e cheque de novo. Erro desconhecido → `reference/pitfalls.md`. Ver o que uma peça oferece: `fb_assemble.py ports <toml> <peça>`.
6. **Medir qualidade**: `fb_assemble.py stats <toml>`. Trate cada `dica:` como defeito: resolução baixa, cavilha demais, reuso baixo, peça maior que a mesa.
7. **Gerar**: `make assemble NAME=<nome>` (ou `fb_assemble.py build <toml> --png`, caminho absoluto). Na nuvem Linux o PNG precisa de `xvfb-run` (o script já usa).
8. **Olhar e comparar.** Abra `assembly.png`, `assembly-side.png`, `assembly-top.png` e `assembly-exploded.png`. Julgue com a rubrica de `quality.md`: silhueta, proporções (meça em células e compare com o pedido/foto), densidade de detalhe, leitura das cores, nada flutuando. Ajuste e volte ao passo 5. **Duas voltas no mínimo** em pedido de alta qualidade. Vista principal ruim → `view_angle` no `[assembly]`.
9. **Conselho** (skill `fusionbrick-council`) — portão final de toda entrega. Primeiro a ficha: `fb_assemble.py review <toml>` precisa dar **APTO** (todos os portões medidos). Depois Maker → Engenheiro → Designer, com veto e nota 0–2 nos oito princípios do padrão; barra: nenhum veto, nenhuma nota 0, média ≥ 1,5. Resolva os conflitos, implemente, registre a ata em `examples/<nome>/conselho.md`.
10. **Verificar geometria (entrega final)**: `make assemble-collide NAME=<nome>` — interseção exata de cada par vizinho. Resultado `?` = o CGAL falhou; o script cai no manifold3d (`pip install manifold3d trimesh`).
11. **Entregar.** Imagens (montado + explodido), contagens (`stats`: peças, cavilhas, STLs únicos), dimensões, vão livre, e **limites honestos** (o que ficou diferente do pedido e por quê). Sem recapitular passos.

## Variantes — escreva o caso comum em uma linha

Uma variante é um bloco com padrões já escolhidos; qualquer campo que você escrever vence o padrão (controle paramétrico completo quando precisar).

| Escreva | Sai |
| --- | --- |
| `type = "beam", size = [12,1,1]` | viga furada nos 3 eixos, pontas redondas, furos à vista de lado |
| `type = "plate", size = [8,6,1]` | placa de 4 mm furada em Z, cantos redondos |
| `type = "cover", size = [8,6,1]` | tampa lisa de 4 mm, pinos para baixo só no perímetro |
| `studs = "top"` (ou `"bottom"`) em qualquer um | pinos nessa face, só nas células planas — empilha sem cavilha |
| `studs = ["right","left"]` · `flat = ["back"]` | essas faces levam pino / ficam lisas |

No `gen.py`: `b.beam(grupo, id, at, size, cor, studs="top")`, `b.plate(grupo, id, at, nx, ny, cor, studs="bottom")`, `b.cover(...)`.

## Qual peça para qual forma

| Quero… | Use | Não use |
| --- | --- | --- |
| volume cheio, base, parede | bloco com `holes` só onde encaixa | 1 bloco enorme (baixa resolução) |
| viga técnica, lateral perfurada | `beam`, camadas desencontradas, `studs = "top"` para empilhar | viga sem furos à vista |
| placa, deck, piso | `plate` (com `studs = "bottom"` sobre a base) | placa > 200 mm ou > ~130 células (divida em iguais) |
| tampa/teto liso | `cover` sobre um quadro | |
| inclinação (coluna A, rampa, braço) | `strut` entre duas células (3-4-5, 5-12-13…) | diagonal a 45° (não fecha) |
| canto arredondado, arco, U | `curve` de `radius = 2` (ou 1, compacto) | nó em L (canto vivo) |
| triângulo de treliça | **não há** — use painel de bloco ou empilhamento | nó com braço a 90° da diagonal |
| roda | `wheel` numa face com encaixe (`socket`) de uma lateral | |
| bateria, placa, motor, câmera, fio, letreiro | `component` com medida real (`box`, `cyl`, `cable`, `text`) | bloco fingindo componente |
| giro de propósito | 1 junção + `hinges` | |

## Esqueleto (TOML à mão)

```toml
# ============================================================
# <NOME> — <uma linha>
# <esboço ASCII por camada, com coordenadas de célula>
# ============================================================
[assembly]
name       = "<nome>"
intent     = "<o pedido, em uma frase>"
dowel_every = 3          # vigas: uma cavilha a cada 3 furos num contato longo
view_angle  = 125        # giro da vista principal

parts = [
  { id = "base",  type = "brick",     at = [0, 0, 0], size = [12, 6, 1], holes = "xyz" },
  { id = "lat_e", type = "beam",      at = [0, 0, 1], size = [12, 1, 1] },
  { id = "c1",    type = "curve",     at = [12, 0, 1], dir = [1, 0, 0], turn = [0, 1, 0], radius = 2 },
  { id = "roda",  type = "wheel",     at = [2, -1, 0], on = "base.right", diameter = 4 },
  { id = "bat",   type = "component", at = [3, 2, 1], size_mm = [48.5, 26.5, 17.5], label = "9V" },
]
groups = [ { id = "chassi", parts = ["base", "lat_e", "c1"], note = "…" } ]
hinges = []
```

## Esqueleto (gen.py)

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "impl", "python"))
from fusionbrick.irgen import Build, OR, GR, LIFT_X, LIFT_Y

W = 10
b = Build("<nome>", "<intenção>", view_angle=125, dowel_every=3)
b.header = """z=0: longarinas y=0 e y=9, travessas x=0 e x=19
z=1..4: rampa 4-3 e poste · z=5: deck em anel de cantos curvos"""
b.brick("chassi", "long_e", (0, 0, 0), (20, 1, 1), OR, **LIFT_X)
b.brick("rampa", "pe_e", (11, 0, 1), (1, 1, 1), GR)
b.strut("rampa", "rampa_e", (12, 0, 1), (16, 0, 4))      # diagonal 3-4-5; os nós saem sozinhos
b.brick("rampa", "poste_e", (17, 0, 1), (1, 1, 4), GR)
b.mirror_y(W)                       # tudo que termina em _e (ou _e-…) ganha o par _d
for x in (0, 19):
    b.brick("chassi", f"trav{x}", (x, 1, 0), (1, W - 2, 1), OR, **LIFT_Y)
b.ring("deck", "deck", 0, 0, 5, 20, W)
b.write(__file__)
```

Esse esqueleto passa no `check` (22 peças, 4 curvas, 2 rampas espelhadas). Rode `python3 examples/<nome>/gen.py` e siga do passo 5. Edite o gerador, nunca o TOML gerado.

## Cores

2–3 cores com função: estrutura escura (`BK`), carenagem clara (`WH`/`TN`), um acento (`OR`). Curvas e diagonais no acento leem bem. Cor por peça; o compilador não inventa.

## Limites atuais (diga ao usuário quando pesarem)

- DOCK e recurso central fora da IR (ASM-009): o componente só reserva o volume.
- Sem pino atravessando furo (lei 7) e sem triângulo de treliça (lei 6): diagonal não prende no meio de uma viga.
- Ângulos só pitagóricos; curvas só 90°/180°.
- Pontas de viga e contatos de topo ainda pedem cavilha (buggy-vt3: 100 de 183 peças impressas).
- Cada inclinação gera um nó próprio (reuso baixo).

## Referências de exemplo

- `examples/rover-tub/`, `rover-scout/` — blocos simples, junções integrais, laje, `hinges` (baixa resolução de propósito)
- `examples/buggy-vt/` → `buggy-vt2/` — a mesma foto em baixa (13 peças/100 mm, reprovado) e **alta resolução** (24,7 peças/100 mm, vigas em camadas, teto liso, rodas balão, componentes de fio e letreiro; `gen.py`)
- `examples/buggy-vt3/` — vt2 refeito com a skill v2: gaiola de arcos curvos, `studs_on = "inner"` nas laterais (242 → 102 cavilhas, 0 pinos livres)
- `examples/rover-x6/` — rover 6×6: base de blocos 12×12×2, carroceria aberta que afunila (quadro inferior + quadro superior mais estreito), 2 arcos, 16 curvas, mastro com cabeça, braço 4-3, antena
- `examples/ds-tests/` — corpos de prova das vigas: cubo de vigas, cubo Technic empilhado, cubo de cantos curvos, pórticos, rampas 3-4-5 / 5-12-13 / 6-8-10 / 3D 2-3-6, S e grampo de curva (`gen.py` com `irgen`)
- `impl/python/tests/test_assembly.py`, `test_irgen.py` — um caso mínimo por regra, por variante e por macro
- `impl/python/fusionbrick/asm/` — o compilador (`names.py` = vocabulário, `parts.py` = tipos de peça, `variants.py` = variantes, `checks.py` = regras)
