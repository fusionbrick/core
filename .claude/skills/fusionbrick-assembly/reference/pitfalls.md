# Armadilhas — erro → causa → correção

Colhidas em montagens reais (rover-tub, rover-scout, buggy-vt, buggy-vt2, ds-tests). Corrija sempre o **primeiro** erro do `check`; os seguintes costumam ser consequência dele.

## Encaixe e posição

| Sintoma | Causa | Correção |
| --- | --- | --- |
| ASM-003 `stud × stud` / `stud × flat` | pino declarado nas duas peças, ou pino contra face sem furo | pino só na peça que **chega**; a que recebe precisa de furo nessa direção (`holes`) |
| REQ-005 `socket` onde não há furo | `faces` pede encaixe numa direção que `holes` não fura | deixe `auto` ou inclua o eixo em `holes` |
| REQ-010 pino em face arredondada | `rounded` + `stud` numa face com ponta curva | `studs = "top"` numa viga (pino só nas células planas) ou faces `auto` (cavilha) |
| ASM-006 pinos colidindo no furo | chapa com pino dos dois lados no mesmo furo | desloque a peça de cima uma célula ou use cavilha |
| ASM-005 "blocos soltos" | peça sem nenhuma porta encostada; curva com `at` errado; nó sem bloco onde o braço aponta | rode `ports` na peça; confira `at` da curva com a fórmula de `catalog.md` |
| ASM-001 meia célula | Z fracionário fora de chapa, X/Y fracionário | só `z + 0.5` sobre chapa (`plate`, `cover`) |
| peça "flutuando" no render, sem erro | encosta só por aresta ou canto | precisa de face com face |

## Colisão

| Sintoma | Causa | Correção |
| --- | --- | --- |
| ASM-002 nó × viga | braço do nó a menos de 127° da diagonal | gire o apoio para "trás" da viga (padrão Rampa); em 3D, pendure por cima |
| ASM-002 poste × ponta da viga | poste logo abaixo/ao lado do nó onde a viga chega | afaste o poste uma célula para trás do nó |
| ASM-002 com fillet | `fillet` > 2 mm transborda a célula | `fillet ≤ grid/4` |
| ASM-002 roda × lateral | rodas da frente e de trás próximas demais; roda maior que o vão até o chão | distância entre `at` > diâmetro em células; suba o eixo |
| ASM-002 algo dentro da curva | curva reserva o arco inteiro, inclusive para vizinhos | nada encaixa no miolo de uma curva; afaste |
| treliça (banzo + diagonal no mesmo nó) reprovada | lei 6: a 53° o braço do banzo invade a diagonal | não há triângulo hoje: painel de bloco, empilhamento ou diagonal com apoio lateral |
| diagonal a 45° | (1,1) não fecha no grid | 3-4-5 (37°/53°) é o mais perto |

## Montagem à mão

| Sintoma | Causa | Correção |
| --- | --- | --- |
| ASM-012 em 2 eixos | peça com pinos/cavilhas em dois eixos para as já montadas (bloco preso na lateral E no bloco vizinho) | deixe `flat` a face do segundo eixo; amarre por outra peça (deck) |
| ASM-012 em ±z / ±y | peça entre duas já montadas (poste entre dois quadros, bloco entre duas laterais) | reordene os `groups` (poste antes do quadro de cima); lateral montada à parte com `sub = true` |
| ASM-012 num anel fechado | a última peça do anel entra em dois eixos | divida uma viga com `split = "flat"` (cada metade apoiada em outra coisa) e comece a ordem logo depois da emenda |
| controle | troque a ordem de propósito e veja o aviso voltar | se não voltar, a checagem não está medindo nada |

## Rigidez

| Sintoma | Causa | Correção |
| --- | --- | --- |
| ASM-004 gira em torno de uma linha | todas as junções da peça colineares (coluna 1×1 só nas pontas, peça com 1 junção) | base de 2 células, segunda face de junção, ou `hinges` se for de propósito |
| info "membro de treliça" | viga esbelta presa só nas pontas | aceito; se for estrutural, trave por outra face |
| roda balança | viga da lateral curta segura o eixo | eixo numa viga que vai de ponta a ponta naquele nível |
| ASM-004 no cubo de uma roda | o eixo da roda não conta como junta; o cubo só tem a perna | cubo de 2 células com uma segunda junta (bogie), padrão rocker-bogie |

## Ferramenta

| Sintoma | Causa | Correção |
| --- | --- | --- |
| `tomllib` ausente | Python < 3.11 (comum no macOS) | rode o compilador com Python 3.11+ ou na nuvem |
| PNG não sai no Linux | OpenSCAD sem tela | `xvfb-run` (o script usa se existir); arquivo antes de `--preview` |
| render da placa grande leva 50 min | CGAL em placa enorme cheia de furos ou pinos (18×14 com 252 pinos travou o rover-x6) | divida em placas iguais (4 × 9×14) — mais resolução e um STL só; mantenha placas ≤ ~130 células |
| `fb_collide` acusa ~500 mm³ em nó × viga | o CGAL do OpenSCAD 2021 quebrou em faces quase coplanares | o script refaz com manifold3d e marca `?` se não tiver; nunca trate falha do CGAL como colisão |
| TOML com chaves erradas depois de `[assembly]` | `parts = [...]` escrito antes de fechar o bloco | o parser aceita as duas posições; prefira o esqueleto da skill |
| `-D` de string some no OpenSCAD | aspas perdidas em `eval`/shell | passe argumentos como lista, sem shell |

## Qualidade (não dá erro, mas o usuário reprova)

| Sintoma | Causa | Correção |
| --- | --- | --- |
| "parece brinquedo de bloco", "muito simples" | poucas peças grandes; resolução < 15 peças/100 mm | escale 1,5–2×; vigas 1×1 em camadas; placas divididas; detalhes como componente |
| "não parece a imagem" | proporções erradas, partes faltando | tabela "na imagem → em FusionBrick" (`image.md`) e medida de proporção depois do render |
| teto/gaiola longos ou baixos demais | gaiola dimensionada pelo chassi, não pela foto | meça altura da gaiola ÷ altura do corpo na foto e reproduza em células |
| centenas de cavilhas | vigas empilhadas por cavilha; muitos segmentos curtos por camada | `studs = "top"` nas camadas; 2 segmentos por camada; travessas sem `rounded` com pinos nas pontas |
| centenas de pinos livres | placas e decks com `studs = "bottom"` sobre poucos apoios | faces `auto` (cavilha só no contato) ou `studs_on = "edge"` sobre um quadro |
| uma cor só, ou arco-íris | cores sem função | 2–3 cores: estrutura, carenagem, acento |
| vista principal esconde o melhor lado | `view_angle` padrão | `view_angle = 125` ou `215` |
