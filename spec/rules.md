# Regras do Sistema

Regras de compatibilidade que toda peça e toda junção devem respeitar. As premissas estão em [constitution.md](constitution.md); os valores em [params.md](params.md).

---

## Lei do Grid

> **O volume do grid é delimitado pelas faces internas. Material de acabamento vive sempre FORA dele.**

Consequências:

1. **A superfície de apoio é plano do grid** — uma célula assenta diretamente sobre ela, e seu centro fica a `grid/2` da superfície
2. **Parede perpendicular** assenta com a borda sobre a superfície e a face interna num plano do grid; a espessura projeta para fora
3. **Nenhuma junção altera o passo.** Peças de junção conectam furos existentes sem inserir espaçamento
4. **Pele é material fora do grid** — os furos continuam ancorados no reticulado; só o envelope cresce

Com pele, o volume de grid fica **deslocado** da face externa. Quem mata na face alinha pela **célula**, não pela face — igual ao que acontece ao redor de uma parede.

---

## A interface é uma só

Não existem mais duas interfaces competindo. Existe **um furo**, no centro de cada célula, em cada eixo `bored`.

| | |
| --- | --- |
| Reticulado | centro de célula — `i·grid + grid/2` |
| Furo | `Ø hole_d`, **passante** ao longo do eixo |
| Boca | rebaixo `Ø recess_d × collar_depth`, quando a face é `recess` |
| Macho | colar `Ø collar_d × collar_depth` + haste `Ø pin_d`, total `pin_len` |

Isso substitui a divisão antiga entre interface de face (`Ø10`) e de borda (`Ø3`). O que era "interface macro" virou o **recurso central** — mesma geometria, outra escala, e uma abstração de leitura em vez de um segundo contrato.

### Furos se cruzam por projeto

Os três eixos passam pelo centro da célula, então os furos se cruzam ali. Não é defeito: é o que dá a passagem de fio e o que limita `pin_len` (premissa 5).

O material que sobra numa célula toda vazada é a **gaiola das 12 arestas**, de seção `(grid − hole_d)/2` = `2.0mm`.

---

## Junções

### Coplanar — lado a lado

Duas peças encostadas: os furos ficam a `grid/2` de cada lado da emenda, então distam `grid` através dela. O grid se preserva sozinho.

Travamento por **cavilha** — um macho de duas pontas dividido entre os dois furos, com o colar assentando nos dois rebaixos. Nada protrui.

### Perpendicular — 90°

Duas peças a 90° deixam uma lacuna no canto externo. A curva de `90°` preenche e pina nos dois furos.

### Diagonal — ângulo livre

Uma diagonal entre dois pontos do grid tem comprimento `Δ·√2` (ou `√(a²+b²)·grid`), que **quase nunca** é múltiplo do passo.

Duas saídas:

| | Restrição |
| --- | --- |
| **Viga de comprimento livre** | as duas **pontas** devem cair em furo existente; o comprimento é livre |
| **Viga de comprimento inteiro** | só ângulos de terno pitagórico fecham — o prático é `3-4-5` → `53.13°` |

**45° é exatamente o ângulo que não fecha** com viga inteira: `grid·√2` contra `grid` é irracional.

A curva aceita qualquer ângulo, mas só o pitagórico devolve a diagonal ao reticulado.

---

## Recurso central

Um furo ou macho maior no centro de um bloco `N×N`. O bloco mínimo é consequência do tamanho.

Dois limites, e **o menor manda**:

| Limite | Fórmula |
| --- | --- |
| Material | `center_recess/2 + recess_d/2 + wall ≤ dist(centro, furo vizinho)` |
| **Montagem** | `center_recess/2 + (grid/2)·√2 ≤ dist(centro, furo vizinho)` |

O de montagem manda quase sempre, e é o que se esquece: uma peça encaixada no furo vizinho **ocupa espaço acima da face**. A quina dela avança `(grid/2)·√2` a partir do próprio centro.

Continuidade de material não basta. Uma chapa pode estar geometricamente correta e mesmo assim não aceitar a peça vizinha.

O recurso engole os furos que alcança **por filtro de distância** — não há lista fixa a manter.

---

## Passagem elétrica

Todo eixo `bored` é canal. Um macho é vazado sempre que `pin_d − 2·wall ≥ 2.5mm` (jumper Dupont).

Na escala atual o macho micro é **maciço** — `3.8 − 3.2 = 0.6mm`, abaixo do mínimo útil. O canal existe no corpo das peças, não no conector.

Macho num eixo `bored` **tampa** aquela boca. Para o canal sair inteiro, use `recess` ou `plain` nas duas pontas.

---

## Tolerância

`tolerance` é subtraída sempre do **conector**, nunca da peça receptora — receptoras são nominais.

O ajuste por impressora acontece no conector: peça pequena, reimpressão barata. E quem retém não é a haste, é o **colar** — `Ø collar_d` em `Ø recess_d`, com `tolerance` de folga diametral.
