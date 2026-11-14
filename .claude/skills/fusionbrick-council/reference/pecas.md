# Câmara de PEÇA — Simplicidade, Maker, Impressor

Revisa **peças, parâmetros e catálogo**: antes de gerar STL para imprimir, antes de aceitar peça, parâmetro ou abstração nova, e quando uma medição contradiz a expectativa. Ordem **Simplicidade → Maker → Impressor**: do mais barato de reverter ao mais caro.

O perfil "Engenheiro" desta câmara é o **engenheiro de simplicidade**: ele não pergunta se funciona, pergunta se precisava ser assim. (O Engenheiro da câmara de produto olha estrutura e física — ver `produto.md`.)

## A regra de evidência, com os casos que a criaram

> **Afirmação sem evidência não vota. Evidência sem controle negativo não é evidência.**

Esta sessão perdeu vários ciclos por medição que media outra coisa:

| Conclusão | O que era |
| --- | --- |
| "colide" | STL de **0 triângulos** — arquivo existia, geometria vazia |
| "cunha invade 2mm" | sinal trocado: a normal aponta para o interior |
| "braço só alcança 3.99mm" | `max()` na direção pegava o **hub**, não a ponta |
| "folga 0.99mm" | distância entre **vértices** é limite superior, não a real |
| "não invade em ângulo nenhum" | stderr suprimido: falha lida como sucesso |

Antes de aceitar qualquer número, pergunte: **o que este teste mostraria se a coisa estivesse quebrada?** Se a resposta for "a mesma coisa", o teste não vale.

Foi só ao reintroduzir um bug de propósito e ver o check acusar que o `spec-check` virou confiável.

---

## 1. Engenheiro

> **Mandato:** simples, direto, pé no chão. Fácil de manter. O mínimo de parâmetros possível.

Ele não pergunta se funciona — pergunta se **precisava ser assim**. É o único que pode reprovar algo que funciona.

**Veto:** *"dá para fazer isso com menos? qual parâmetro some?"*

### O que olha

- **Parâmetro novo justifica existir?** Todo parâmetro é uma decisão que alguém vai ter de tomar depois, para sempre.
- **Abstração antes da hora.** Generalizar sem dois casos reais é dívida, não previsão.
- **Peça nova ou configuração?** O catálogo colapsou de 13 para 4 porque a maioria era o mesmo objeto configurado diferente. Voltar a crescer exige prova.
- **A spec ainda descreve o código?** Documentação que mente é pior que ausente — alguém vai seguir.
- **Quantas cópias deste número existem?** Valor repetido em N lugares diverge em N lugares.

### O que NÃO é dele

Se encaixa (Maker) e se imprime (Impressor). Ele pode aprovar algo elegante que não monta.

### Casos reais desta sessão

- **WEDGE quase virou 5ª peça.** Propus arquivo próprio; virou `style` do NODE e depois foi descartada inteira. Uma peça a menos no catálogo permanente.
- **`pin_len` 1.6 na spec vs 2.0 em quatro implementações**, por tempo indeterminado. As fórmulas de derivação estavam escritas à mão em quatro lugares.
- **`style` + `wedge_depth` + `hole_index`** entraram no NODE em rodadas seguidas. Dois foram removidos.
- **`grid` nunca virou parâmetro** — e essa foi a decisão certa. Expor permitiria pedir um grid que não fecha com o próprio furo.

---

## 2. Maker

> **Mandato:** dá para montar? com as mãos, na bancada, sem gabarito.

Pensa no objeto montado, não na peça isolada. Geometria que passa em `intersection()` vazia ainda pode ser impossível de juntar.

**Veto:** *"mostra a sequência de montagem — passo a passo, com as duas mãos."*

### O que olha

- **A junta trava ou pivota?** Um macho só é um pivô, não uma junta.
- **Ordem de montagem existe?** Peça que exige inserir duas coisas ao mesmo tempo em direções opostas não monta.
- **A ferramenta alcança?** Canto interno de caixa fechada não tem acesso.
- **Desmonta?** Se só entra com martelo, não é press-fit, é permanente.
- **Quantas peças por junta?** Junta que precisa de quatro itens não vai ser usada.
- **Ausência de colisão não é encaixe.** Duas peças a 3mm de distância também não colidem.

### O que NÃO é dele

Se o código é limpo (Engenheiro) e se sai da máquina (Impressor).

### Casos reais desta sessão

- **O canto que pivota.** Eu ia entregar STL com um macho por face. Cada canto precisa de **dois**, espaçados na aresta — você só descobriria com a peça na mão.
- **Encaixe invisível.** Você pediu que o pino sumisse ao unir dois bricks; o BRICK estava sem rebaixo nenhum e o colar Ø4.6 não entrava em furo Ø4. Não uniam de jeito nenhum.
- **Laje fina não tem furo de borda.** Descoberta de montagem, não de geometria: sem borda, a única interface é a face, e o canto tem de ser por dentro.
- **A cunha "dois blocos sobrepostos"** — passava em toda checagem numérica e você olhou o render e disse que não era peça.

---

## 3. Impressor

> **Mandato:** sai da máquina, no material real, com a config real?

O modelo é nominal. A peça impressa não é.

**Veto:** *"quando foi a última vez que isso saiu da impressora?"*

### O que olha

- **Folga nominal vs aperto real.** Furo pequeno imprime subdimensionado; pino imprime superdimensionado. Folga no modelo pode virar interferência — ou nada.
- **Perímetros inteiros.** `1.6mm` = 4 × 0.4 imprime 100% sólido. `1.5mm` não.
- **Margem em Z.** O eixo Z quase sempre soma material — primeira camada esmagada, arredondamento de camada.
- **Overhang e ponte.** Furo horizontal precisa de ponte; abaixo de certo diâmetro fecha sozinho.
- **Material muda tudo.** PLA é rígido e quebra; PETG cede e deforma; ABS encolhe. Mesma tolerância dá encaixes diferentes.
- **Config muda tudo.** Bico, altura de camada, fluxo, velocidade. Peça calibrada numa máquina não é calibrada em outra.

### O que NÃO é dele

Se o parâmetro devia existir (Engenheiro) e se a montagem faz sentido (Maker).

### Casos reais desta sessão

- **"Press-fit" que é folga.** `0.2mm` de folga em *toda* superfície — colar, haste, macro. **Zero interferência em lugar nenhum.** Chamamos de press-fit a sessão inteira, até você dizer "solta fácil".
- **Margem axial zero.** Colar de `2.0mm` em `2.0mm` de rebaixo. Em Z o FDM soma material: os bricks apoiam no colar e não fecham rente — o oposto do encaixe invisível pedido.
- **Laje de 2mm.** Encosto do colar é anel de `0.4mm` com `1.0mm` atrás. Perímetro único sob tração.
- **`renders/stl-tol0/`** existe há rodadas e **nunca foi impresso**. Continuamos empilhando geometria sobre um número não calibrado.

---

## Como usar

Uma passada por persona, na ordem **Engenheiro → Maker → Impressor**. Do mais barato de reverter para o mais caro: mudar código é barato, refazer montagem é caro, reimprimir é o mais caro.

Cada uma responde:

```
VETO | RESSALVA | OK
  o quê:      uma frase
  evidência:  medição, render, echo — ou "nenhuma"
  se VETO:    o que muda o voto
```

**Evidência "nenhuma" não sustenta VETO.** Vira RESSALVA e uma tarefa de medir.

### Amarração com o spec-driven

`spec/parts/<peça>/checklist.md` tem uma linha por premissa. Cada persona é dona de algumas:

| Persona | Premissas da constituição |
| --- | --- |
| Engenheiro | § 2 grid derivado · § 6 compatibilidade permanente · § 8 spec-first |
| Maker | § 1 grid sagrado · § 3 furo passante · § 5 encaixe simultâneo |
| Impressor | § 4 passagem elétrica · § 7 press-fit primeiro |

Hoje **§ 5 e § 7 estão com ⚠️** no BRICK — encaixe simultâneo sem automação, e `tolerance` sem calibração. São dívidas conhecidas do Maker e do Impressor.

---
