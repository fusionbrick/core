# PIN

O único macho solto do sistema. Une dois furos, em qualquer escala.

Absorve BRIDGE (cavilha de duas pontas), LINK (conector de face) e LINK-ONESIDE — os três eram o mesmo objeto em tamanhos diferentes.

> **Nota de nomenclatura:** até a v1, `PIN` era o nome da viga. A viga virou [BRICK](brick.md) `1×1×n`, e o nome passou para o macho, que é o que ele descreve.

Modelo e valores: [constitution.md](../constitution.md) · [params.md](../params.md).

## Geometria

Colar na raiz + haste. Nesta ordem, a partir da face:

| Trecho | Extensão | Diâmetro |
| --- | --- | --- |
| Colar | `0` … `collar_depth` | `collar_d` |
| Haste | `collar_depth` … `pin_len` | `pin_d` |

`pin_len` é a protrusão **total** — o colar não soma, ele é o primeiro trecho dela.

Na escala micro isso dá `2.0mm` de protrusão, dos quais `1.0mm` é colar e `1.0mm` é haste. **Quem retém é o colar**, assentando no rebaixo com `tolerance` de folga diametral. A haste alinha.

## Variantes

| Parâmetro | Padrão | O que muda |
| --- | --- | --- |
| `ends` | `2` | `1` = macho de uma ponta · `2` = cavilha, metade em cada furo |
| `size` | `hole_d` do sistema | diâmetro do furo receptor — define toda a escala |
| `spacer` | `0` | afastamento entre as duas pontas |
| `lead_in` | chanfro de entrada | facilita iniciar o encaixe |

`size` é o que unifica as escalas: um PIN para o furo padrão e um PIN para o recurso central são a mesma peça com `size` diferente. Todas as cotas derivam dele pelas fórmulas de [params.md](../params.md).

## Comprimento é contrato, não escolha

`pin_len` **não é parâmetro da peça**. Ele vale para o sistema inteiro.

Um macho mais longo entraria fundo demais numa célula que espera `2.0mm` e colidiria com o pino perpendicular *dela*, quebrando o encaixe simultâneo (premissa 5) da peça receptora. Comprimento variável por peça quebra a compatibilidade permanente.

Onde o macho é mais longo é no `spacer` — que afasta as duas pontas sem alterar quanto cada uma entra.

## Canal de fio

Vazado sempre que `size − tolerance − 2·wall ≥ 2.5mm`.

Na escala micro sobram `0.6mm` — abaixo do mínimo útil, então o macho micro é **maciço**. O canal existe no corpo das peças, não no conector. Em escalas maiores o PIN é vazado.

## Verificações

- `pin_len` igual ao valor do sistema — nunca sobrescrito por peça
- Duas pontas num furo passante compartilhado: `2 · pin_len ≤ grid − gap`
- Canal só existe se passar do mínimo útil
