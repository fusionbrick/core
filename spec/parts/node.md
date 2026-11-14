# NODE

A única peça que sai do ortogonal. Une N portas em ângulos arbitrários.

Absorve a curva de ângulo livre (antes ELBOW). Não absorve as uniões a 90°, 180° e as 3-vias ortogonais — **essas já são [BRICK](brick.md)** com faces `pin`, porque as portas de uma união ortogonal caem exatamente nos centros de face da célula.

Modelo e valores: [constitution.md](../constitution.md) · [rules.md](../rules.md).

## Quando usar NODE e quando usar BRICK

| União | Peça |
| --- | --- |
| 90°, 180°, 3-vias ortogonal, união de 6 | **BRICK** com faces `pin` |
| 45°, 28°, 135°, qualquer não-ortogonal | **NODE** |

Se todas as portas apontam ao longo de eixos do grid, é BRICK. Basta uma sair disso e é NODE.

## Geometria

Cubo central com um braço por porta, cada um apontando na direção declarada e terminando na interface do sistema. A junção entre os braços recebe uma **concordância** (`fillet`).

O fillet é o que devolve o que a curva por varredura dava: quina externa arredondada e canal interno sem dobra seca. Com dois braços a 90° e fillet, o NODE reproduz o antigo ELBOW.

## Parâmetros

| Parâmetro | Padrão | O que é |
| --- | --- | --- |
| `dirs` | — | lista de direções, uma por porta |
| `ports` | `recess` | `recess` / `pin` / `plain`, por porta |
| `fillet` | `grid/4` | raio de concordância entre braços |
| `arm_len` | derivado | comprimento do braço, do centro à porta |

`dirs` é o parâmetro que define a peça. Duas direções fazem uma curva; três ou mais, um nó.

## A direção manda, o ângulo é consequência

A peça é declarada pelas **direções das portas**, não por um ângulo. Isso porque:

- com três ou mais portas não existe "o ângulo" — existem vários
- escrever o ângulo à mão é a origem de erro de orientação mais comum; derivar do vetor elimina a classe inteira

Quem monta informa para onde cada porta aponta. O ângulo entre elas sai da conta.

## O que fecha e o que não fecha no grid

Um NODE conecta em qualquer ângulo. O que **não** é livre é o percurso voltar ao reticulado:

- **Viga de comprimento livre** entre dois nós: as duas pontas precisam cair em furo existente; o comprimento é livre
- **Viga de comprimento inteiro**: só ângulo de terno pitagórico fecha — o prático é `3-4-5` → `53.13°`

`45°` é exatamente o ângulo que **não** fecha com viga inteira: a diagonal vale `grid·√2`, irracional contra o passo.

## Verificações

- Duas portas não podem apontar na mesma direção
- Braços adjacentes precisam de ângulo suficiente para o fillet caber
- Material atrás de cada porta ≥ `pin_len` + parede
- Portas não-ortogonais: avisar que o percurso só volta ao grid em ângulo pitagórico
