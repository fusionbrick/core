// ============================================================
// HUB — Design System 3D Modular
// ============================================================
// BRICK 3×3×3 com recurso central. Não é peça nova: é uma
// CONFIGURAÇÃO do BRICK persistida em arquivo, para render, STL
// e catálogo saírem prontos sem ninguém redigitar parâmetros.
//
// É o que era o ATOM. O nome mudou porque ATOM dizia "unidade
// indivisível do sistema" — e não é mais: a unidade é a célula
// de 8mm. O que esta peça faz é concentrar passagem no centro
// e distribuir encaixe nas bordas.
//
//     ┌───┬───┬───┐
//     │ o │   │ o │    o  furo do grid (sobrevive)
//     ├───┼───┼───┤
//     │   │███│   │   ███ furo macro central
//     ├───┼───┼───┤
//     │ o │   │ o │
//     └───┴───┴───┘
//
// Os furos do meio de cada aresta NÃO sobrevivem — o macro
// alcança até 9.4mm do centro e eles estão a 8mm. Sobram os
// quatro das quinas, a 11.31mm. Isso é do BRICK, não daqui:
// `alive()` filtra por distância.
//
// COMO A VARIANTE FUNCIONA
// `include`, não `use`. `use <>` importa só o módulo, com os
// parâmetros congelados no valor padrão de brick.scad — não há
// como reconfigurar. `include <>` cola o arquivo aqui, e a
// reatribuição abaixo vence (último valor ganha) e propaga para
// os derivados e para dentro de brick().
//
// Por isso NÃO há chamada de render neste arquivo: quem desenha
// é o `color(part_color) brick();` do próprio brick.scad, já
// executando com a configuração abaixo. Acrescentar uma chamada
// aqui renderizaria a peça duas vezes.
//
// spec: spec/parts/brick.md
// ============================================================

include <brick.scad>

// ------------------------------------------------------------
// CONFIGURAÇÃO DO HUB
// ------------------------------------------------------------
// Três células por eixo é o BLOCO MÍNIMO para este macro, não
// escolha estética: com Ø10 o recurso precisa de anel de
// material em volta e de furos de grid que sobrevivam a ele.
cells_x = 3;
cells_y = 3;
cells_z = 3;

// Passagem central. Ø10 é o limite de MONTAGEM: uma peça de uma
// célula encaixada no furo vizinho estende (grid/2)·√2 = 5.66mm
// até a quina, e ela precisa não bater no macro. Ø13 passava na
// continuidade de material e falhava na impressão — foi medido.
center      = "hole";
center_size = 10;

// Os três eixos passantes e as seis faces fêmeas: o HUB é ponto
// de convergência, então toda direção tem de aceitar encaixe.
axis_x = "bored";
axis_y = "bored";
axis_z = "bored";

// ------------------------------------------------------------
// INFO
// ------------------------------------------------------------
echo("=== HUB (variante de BRICK) ===");
echo(str("Bloco       ", total_x, " × ", total_y, " × ", total_z, "mm"));
echo(str("Macro       Ø", center_size, " (rebaixo Ø", center_recess, ")"));
// A folga de montagem e a contagem de furos vivos já saem no
// bloco do BRICK acima — são cálculo dele, não desta variante.
