# O padrão de qualidade

O que separa um protótipo de um produto raramente é uma ideia a mais: é o rigor com que a ideia foi levada até o fim. Este padrão destila o que empresas consolidadas praticam de forma consistente — e traduz cada prática numa pergunta que dá para responder com as ferramentas deste repositório.

Não é imitação de estilo. Um rover FusionBrick não precisa parecer um produto da Apple; precisa ter sido **decidido** com o mesmo cuidado.

## De onde vem cada princípio

| Princípio | Prática de referência | No FusionBrick |
| --- | --- | --- |
| 1. Uma ideia | Apple: linha curta, foco, dizer não a quase tudo | o `intent` do `assembly.toml` cabe em uma frase, e cada grupo de peças serve a ela |
| 2. Menos, porém melhor | Braun / Dieter Rams: "tão pouco design quanto possível"; LEGO: milhares de modelos com poucas peças | variantes em vez de peças novas; poucos STLs únicos; 2–3 cores com função |
| 3. Funciona de verdade | Dyson: a função manda na forma, validada em protótipos sucessivos | `physics` (massa, tombamento, base de peças altas); componentes com medida e massa reais |
| 4. Cuidado onde ninguém vê | Apple: o interior montado com o mesmo capricho do exterior | nenhum pino sem uso, fios roteados por onde cabem, parte de baixo resolvida |
| 5. Encaixe e acabamento | LEGO: tolerância apertada e compatibilidade que não quebra entre gerações; Toyota: parar a linha no primeiro defeito | zero erro, zero colisão exata, simetria, alinhamento; `review` bloqueia em vez de avisar |
| 6. Montar é parte do produto | IKEA / LEGO: instrução que dispensa texto, uma ação por passo | `groups` como passos, `sub` para subconjuntos, ASM-012 zerado, nota em todo passo |
| 7. Possível | "Quem faz, entrega": o que não sai da máquina não é produto | mesa de 220 mm, PLA/PETG, sem suporte onde der, peça repetida |
| 8. Presença | Apple / Teenage Engineering: silhueta reconhecível, um ponto focal, fotografia que vende | arquétipo legível, proporção heroica, "rosto", `view_angle`, nome à vista |

## Como dar a nota (0 · 1 · 2)

| Princípio | 0 — falha | 1 — aceitável | 2 — exemplar |
| --- | --- | --- | --- |
| 1. Uma ideia | não dá para dizer o que é; ou são dois produtos colados | a frase existe, mas há elementos que não servem a ela | cada elemento responde "por quê?" pela frase |
| 2. Menos, porém melhor | peça nova onde cabia configuração; arco-íris de cores | reuso ≥ 2, mas com peças quase iguais que poderiam ser uma | poucas peças diferentes fazem muito; nada sobra |
| 3. Funciona de verdade | tomba, arrasta, ou não tem como andar/ligar | fica em pé e tem os componentes, com ressalvas declaradas | caminho da carga claro, margens medidas, limites ditos |
| 4. Onde ninguém vê | pinos soltos, fio atravessando peça, parte de baixo esquecida | limpo, com um ou dois atalhos | o explodido e a vista de baixo são tão bons quanto a frente |
| 5. Encaixe e acabamento | colisão, peça torta, assimetria sem motivo | tudo fecha; pequenos desalinhamentos | linhas contínuas, emendas onde fazem sentido, simetria exata |
| 6. Montar | não existe ordem; duas mãos não bastam | monta, com passos confusos ou cavilha demais | subconjuntos óbvios, um movimento por peça, passos com nota |
| 7. Possível | peça maior que a mesa; depende de peça que não existe | imprime, com tempo ou suporte altos | imprime deitado, sem suporte, em lotes de peças iguais |
| 8. Presença | caixa genérica; não se sabe para onde olhar | reconhecível, sem ponto focal | silhueta icônica, um ponto focal, imagem que dispensa legenda |

## Perguntas que fazem a diferença

Estas são as que mais mudaram resultados nas montagens deste projeto:

1. **O que eu tiraria?** Antes de adicionar detalhe, remova o que não serve à frase. O rover-x6 perdeu um LiDAR no topo do mastro: virou cartola e escondia a cabeça.
2. **E por baixo?** O buggy-vt2 tinha 658 pinos impressos que não encaixavam em nada, escondidos sob as placas. Ninguém via — e eram horas de impressão.
3. **Quem segura isto?** Uma cavilha aguenta cisalhamento, mas quase nada contra arrancamento. Mastro com 4 juntas a 11 mm virou pé 4×4 com juntas a 34 mm.
4. **Em que ordem?** 16 peças do rover-x6 pediam dois movimentos ao mesmo tempo. O render não mostra isso.
5. **Mede o que parece medir?** Um teste que daria o mesmo resultado com a coisa quebrada não é teste.
6. **Qual é a foto?** Se a vista principal não mostra o ponto focal, o produto não tem um — ou a câmera está no lugar errado.

## O que este padrão não é

- **Não é gosto.** Cada nota aponta para algo observável; sem evidência, é ressalva.
- **Não é perfeccionismo sem fim.** A barra é explícita (`SKILL.md` § 3); passou, entrega.
- **Não é esconder limite.** Produto exemplar diz o que não faz: suspensão que não articula, motor que ainda não liga na roda.
