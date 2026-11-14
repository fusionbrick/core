# Qualidade — de "válido" a "fiel e detalhado"

O compilador garante que encaixa. Ele **não** garante que parece o que foi pedido. O usuário reprovou duas vezes montagens válidas: "muito simples" e "baixa resolução". Este arquivo é o portão contra isso.

## 1. Métrica: `stats`

```bash
python3 hack/scripts/fb_assemble.py stats examples/<nome>/assembly.toml
```

| Métrica | Alvo | Referência medida |
| --- | --- | --- |
| peças estruturais / 100 mm da maior dimensão | **15–40** para kit técnico | rover-tub 10,7 (reprovado: "simples") · buggy-vt 13 (reprovado: "baixa resolução") · buggy-vt2 24,7 (aprovado) |
| cavilhas / peças impressas | < 55% | buggy-vt2 74% → buggy-vt3 55% · ds-tests t1 57% · com pinos impressos 0% |
| pinos livres | ~0 | buggy-vt2 658 → buggy-vt3 0 |
| cópias por STL único | ≥ 2 | t3-cubo-curvas 14 · t5-inclinadas 2,9 |
| maior peça | ≤ 220 mm | mesa típica de impressora |

Cada `dica:` do `stats` é um defeito a corrigir ou a justificar na entrega.

## 2. Rubrica visual (depois de cada render)

Abra montado, lateral, topo e explodido. Responda cada linha com sim/não; dois "não" = mais uma volta.

| # | Pergunta | Como checar |
| --- | --- | --- |
| 1 | A **silhueta** lateral lembra o objeto pedido (ou a foto)? | compare `assembly-side.png` com a referência lado a lado |
| 2 | As **proporções** batem? | comprimento : largura : altura, roda : corpo, gaiola : corpo — em células, com tolerância de ±10% |
| 3 | Há **detalhe técnico** onde a referência tem (furos à vista, vigas, recortes)? | furos à vista nas laterais e na gaiola, não em todo lugar |
| 4 | Nada parece **bloco maciço** grande? | qualquer bloco > 4×4 células nas duas direções visíveis é suspeito |
| 5 | **Cores** com função (estrutura, carenagem, acento)? | ≤ 3 cores além dos componentes |
| 6 | Os **componentes** contam a história (bateria, placa, câmera, fios, luzes)? | o que o usuário disse que vai dentro está visível e com medida real |
| 7 | **Simetria** onde o objeto é simétrico? | `mirror_y`; vista de topo |
| 8 | **Vão livre** e rodas plausíveis? | ASM-010 no relatório; roda ≈ 0,35–0,45 do comprimento num buggy |
| 9 | A **vista principal** mostra o melhor lado? | `view_angle` |
| 10 | Montável? | `steps.md` em ordem lógica (chassi → laterais → gaiola → teto → componentes) |

## 3. Escala é a alavanca principal

Mais resolução **não** é peça menor — o grid é fixo. É objeto maior descrito por mais peças. Para chegar a 15–40 peças/100 mm:

- vigas 1×1×n em vez de paredes 1×1×n altas;
- laterais em 3–5 camadas desencontradas;
- placas grandes divididas em iguais;
- gaiola de postes + trilhos + travessas, não uma moldura maciça;
- detalhes (faróis, para-choques, suportes, antena, letreiro, fios).

Diga ao usuário a escala escolhida (ex.: "1,8× a foto, 304 mm") e o porquê.

## 4. Laço de comparação com imagem

1. Antes da IR: tabela "na imagem → em FusionBrick" (`image.md`).
2. Depois do render: meça na imagem e no render as mesmas razões (altura total ÷ comprimento, roda ÷ comprimento, posição do eixo dianteiro ÷ comprimento). Erro > 10% → ajuste.
3. Se o usuário quiser, gere um **prompt de imagem** a partir da montagem (descrição técnica: vigas, cores, rodas, componentes) para ele gerar uma imagem e conferir se "bate". Foi como o buggy convergiu.

## 5. Portão final: a ficha e o conselho

`python3 hack/scripts/fb_assemble.py review <toml>` roda todos os portões medidos (encaixe, montagem à mão, mesa, pinos, cavilhas, colisão exata, reuso, tombamento, centro de massa, base de peças altas, resolução, cores, proporção de roda) e termina em **APTO** ou **NÃO APTO**. Só com APTO o conselho (`fusionbrick-council`) opina.

## 6. Verificação final (entrega de alta qualidade)

- `check` ok, `stats` sem dica não justificada.
- `make assemble-collide NAME=<nome>` → **ZERO COLISÃO**. `?` = refaça com manifold3d; contato < 0,5 mm³ é ruído de malha.
- Testes do compilador verdes se você mexeu nele: `make assemble-test`.
- Entrega: imagens, `stats` (dimensões, peças, cavilhas, STLs), vão livre, e o que ficou diferente do pedido.

## 7. Limites que você deve declarar, não esconder

- sem triângulo de treliça; diagonais só pitagóricas; curvas só 90°/180°;
- junta só por contato de face: não há pino atravessando furo, e diagonal/curva ligam só pelas pontas;
- cavilhas dominam a contagem em montagens de viga;
- eixo de roda em balanço numa viga só;
- pinos livres escondidos sob placas (aparecem no BOM, não no render).
