// ============================================================
// PLATE — Design System 3D Modular
// ============================================================
// Chão e parede. BRICK com espessura livre de grid/2 = 4mm,
// vazado só no eixo Z. Não é peça nova: é uma CONFIGURAÇÃO do
// BRICK persistida em arquivo. Ver spec/parts/brick.md.
//
//     ┌───┬───┬───┬───┬───┐
//     │ o │ o │ o │ o │ o │   campo de furos no passo do grid,
//     ├───┼───┼───┼───┼───┤   fêmea nos dois lados
//     │ o │ o │ o │ o │ o │
//     └───┴───┴───┴───┴───┘   costas planas: assenta na mesa
//
// POR QUE FÊMEA E NÃO MACHO
// Um campo de machos é base de Lego: compromete toda posição
// para sempre, não assenta plana e só aceita peça fêmea. Furo +
// PIN onde precisar dá os dois estados, e mantém a simetria do
// sistema — toda peça é fêmea, todo macho é peça solta.
//
// POR QUE 4mm
// É grid/2, e é a espessura mais fina que preserva o contrato:
//
//   2.0mm  os dois rebaixos se encontram, some o encosto
//   2.6mm  a haste do macho cabe (um lado por vez)
//   3.2mm  abaixo disso dois machos coaxiais SE TOCAM
//   3.7mm  os dois com a folga `gap` entre as pontas
//   4.0mm  idem, com 0.8mm de folga  ← aqui
//   7.2mm  mínimo para ter furo de BORDA
//
// Duas lajes empilhadas fecham uma célula, então a espessura
// compõe com o grid em vez de brigar com ele.
//
// O QUE ELA NÃO FAZ
// Não tem furo de borda: precisaria de 7.2mm. Logo não é viga —
// toda carga entra pela face. Para estrutura, use BRICK.
//
// E o passo é o do grid (8mm), grosso para componente
// eletrônico: isto é campo de MONTAGEM, não de componente. Quem
// hospeda placa e motor é o DOCK, que se fixa aqui.
//
// spec: spec/parts/brick.md
// ============================================================

// De quantos lados a laje aceita encaixe. É o parâmetro que
// decide a espessura, porque a espessura mínima é consequência
// dele — não escolha independente.
//
//   2 = CHÃO/BASE   grid/2 = 4mm   fêmea nas duas faces
//   1 = PELE/PAREDE grid/4 = 2mm   fêmea só em cima; a ponta do
//                                  macho para rasante nas costas
//
// 2mm fecha exato porque `pin_len` = 2.0: colar 1.0 + haste 1.0.
// Costas lisas, nada atravessa.
//
// ⚠️ DECLARADO ANTES DO `include`, e tem que ficar aqui.
// Quando uma variável do BRICK é reatribuída abaixo (`thickness`,
// `face_zn`), o OpenSCAD avalia a atribuição vencedora no ponto
// da declaração ORIGINAL — lá dentro de brick.scad. Uma variável
// nova declarada depois do include ainda não existe nesse ponto:
// sai `WARNING: Ignoring unknown variable` e o ternário cai no
// ramo errado, em silêncio.
sided = 2; // [1:1:2]

include <brick.scad>

// ------------------------------------------------------------
// CONFIGURAÇÃO DA PLATE
// ------------------------------------------------------------
cells_x = 5;
cells_y = 5;

thickness = sided == 2 ? 4 : 2;

// Só o eixo Z é vazado. X e Y não cabem numa laje — o furo de
// borda exige 7.2mm — e o `assert` do BRICK recusa se tentar.
axis_x = "solid";
axis_y = "solid";
axis_z = "bored";

// Face de cima sempre fêmea; a de baixo depende de `sided`.
face_zp = "recess";
face_zn = sided == 2 ? "recess" : "plain";
face_xn = "plain";
face_xp = "plain";
face_yn = "plain";
face_yp = "plain";

// ------------------------------------------------------------
// INFO
// ------------------------------------------------------------
echo("=== PLATE (variante de BRICK) ===");
echo(str("Campo       ", cells_x, "×", cells_y, " furos no passo ", grid, "mm"));
echo(str("Espessura   ", thickness, "mm (grid/", sided == 2 ? 2 : 4,
         ") — fêmea de ", sided, " lado(s), sem furo de borda"));
