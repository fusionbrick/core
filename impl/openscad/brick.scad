// ============================================================
// BRICK — Design System 3D Modular
// ============================================================
// O bloco universal. Ocupa células do grid e é sempre ORTOGONAL.
//
// Absorve o que eram cinco peças — ATOM, PLATE, viga, quina e
// vértice. Todas eram o mesmo objeto: um bloco de n células com
// furos e machos em faces diferentes.
//
//        ┌─────┬─────┬─────┐
//        │  ○  │  ○  │  ○  │   1 célula = 1 furo por eixo,
//        ├─────┼─────┼─────┤   no centro
//        │  ○  │  ○  │  ○  │
//        └─────┴─────┴─────┘
//
// DUAS CAMADAS, e a distinção importa:
//   EIXO (3)  bored | solid   — o furo, sempre PASSANTE
//   FACE (6)  recess | pin | plain — o acabamento na boca
//
// Fundir as duas acopla faces opostas: com furo passante, um
// "hole" numa face abriria a face oposta à revelia dela.
//
// O macho é material SOMADO por fora, então pode existir numa
// face cujo eixo é bored — ele tampa aquela boca.
//
// spec: spec/parts/brick/spec.md
// ============================================================

// Primitivos e derivados: fonte única, não redeclarar aqui.
include <params.scad>

// Diâmetro do furo passante — a interface mecânica

// Parede interna mínima (4 perímetros de 0.4)

// Degrau RADIAL entre furo e rebaixo (1 bico de 0.4)

// Profundidade AXIAL do rebaixo (5 camadas de 0.2)

// Folga de press-fit

// Folga mínima entre dois machos que se aproximam

/* [Dimensões] */
cells_x = 1; // [1:1:20]
cells_y = 1; // [1:1:20]
cells_z = 1; // [1:1:20]

// LAJE: fixa a extensão em Z em mm, fora do grid. 0 = usa
// cells_z normalmente.
//
// É o que permite chão e parede — uma célula inteira tem 8mm
// porque esse é o mínimo para abrigar um furo de BORDA
// (recess_d + 2·wall). Uma laje não tem furo de borda, então
// não precisa pagar por ele. Em troca, ela deixa de ser viga:
// toda carga entra pela face.
//
// grid/2 = 4mm é a espessura recomendada — duas lajes empilhadas
// fecham uma célula, então ela compõe com o grid em vez de
// brigar com ele.
thickness = 0; // [0:0.5:20]

/* [Eixos — o furo é do eixo, e é passante] */
axis_x = "bored"; // [bored, solid]
axis_y = "bored"; // [bored, solid]
axis_z = "bored"; // [bored, solid]

/* [Faces — o acabamento é da face] */
// "auto" = recess se o eixo da face é bored, plain se é solid.
// É o padrão porque rebaixo sem furo é bolso cego (REQ-005): a
// face acompanha o eixo sem precisar ser declarada. Um "recess"
// EXPLÍCITO num eixo solid continua sendo erro — ali é intenção
// errada, não omissão.
face_xn = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)
face_xp = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)
face_yn = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)
face_yp = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)
face_zn = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)
face_zp = "auto"; // [auto, recess, pin, plain]  (ou socket, stud, flat)

/* [Contorno — arredondamento das arestas] */
// Eixo das arestas arredondadas: "none" = caixa reta. Com "y", as
// 4 arestas paralelas a Y viram cilindros — uma viga 1×n vira um
// LIFTARM (pontas redondas no plano X-Z, furos à vista em Y).
round_axis = "none"; // [none, x, y, z]
// Raio das arestas. grid/2 numa viga de 1 célula = ponta redonda
// cheia. O raio fica limitado à meia-espessura da peça.
corner_r = 0; // [0:0.5:40]

/* [Machos] */
// "edge" = macho só nas células do PERÍMETRO de cada face macho.
// Para placas que assentam sobre um quadro (teto, tampa): prende na
// borda, e o miolo fica liso dos dois lados.
pin_cells = "all"; // [all, edge, inner]

/* [Recurso central — a generalização do "macro"] */
// Furo ou macho maior no centro do bloco. O bloco mínimo é
// CONSEQUÊNCIA do tamanho, não escolha.
center = "none"; // [none, hole]
center_size = 10; // [2:0.5:60]

// ============================================================
// DERIVADOS — nada aqui é escolhido à mão
// ============================================================

// Protrusão do macho. DECLARADO, não derivado.
//
// A versão anterior fazia `wall + collar_w + tolerance/2 - gap`,
// que cobrava √2 a mais do que a geometria pede: o limite é a
// colisão com o macho PERPENDICULAR da célula receptora, e essa
// aproximação é DIAGONAL, não axial. Subtrair `gap` do eixo
// gastava 0.5mm de engate para comprar 0.71mm de folga.
//
// O teto verdadeiro está no assert abaixo. 2.0 foi verificado
// por dilatação (minkowski): folga real ≥ 0.5mm.

// Teto geométrico: a haste tem raio pin_d/2 e parte da face, a
// grid/2 do centro. Duas hastes perpendiculares se tocam quando
// pin_len alcança essa diferença.

// Chanfro de entrada do macho. CONSTANTE, não parâmetro: é um
// bico de bico, existe para o macho achar o furo, e ninguém
// precisa decidir isso peça a peça.

center_recess = center_size + 2 * collar_w;

slab = thickness > 0;

total_x = cells_x * grid;
total_y = cells_y * grid;
total_z = slab ? thickness : cells_z * grid;

function centers(n) = [ for (i = [0 : n - 1]) i * grid + inset ];
xs = centers(cells_x);
ys = centers(cells_y);
// A laje é uma camada só, centrada na própria espessura — não há
// célula em Z para dividir.
zs = slab ? [ total_z / 2 ] : centers(cells_z);

ax = [axis_x, axis_x, axis_y, axis_y, axis_z, axis_z];

// Faces como declaradas, e depois resolvidas: "auto" segue o eixo.
fc_decl = [ for (f = [face_xn, face_xp, face_yn, face_yp, face_zn, face_zp]) fb_kind(f) ];
fc = [ for (i = [0 : 5]) fc_decl[i] == "auto"
         ? (ax[i] == "bored" ? "recess" : "plain")
         : fc_decl[i] ];

// ------------------------------------------------------------
// Espessuras mínimas de laje — dependem de QUANTAS faces Z são
// fêmeas, não da espessura sozinha. Uma laje fêmea de um lado só
// precisa da metade do que uma de dois lados precisa.
// ------------------------------------------------------------
z_recess = (fc[4] == "recess" ? 1 : 0) + (fc[5] == "recess" ? 1 : 0);

// Piso ABSOLUTO: abaixo disso não sobra encosto para o colar
// assentar — o macho atravessa. Com as duas faces fêmeas os dois
// rebaixos se encontram em 2·collar_depth.
slab_floor =
    z_recess == 2 ? 2 * collar_depth :
    z_recess == 1 ?     collar_depth : 0;

// Espessura IDEAL: a haste do macho cabe inteira, sem sair pelo
// lado oposto. Com um lado só isso é exatamente `pin_len`.
slab_min =
    z_recess == 2 ? 2 * collar_depth + (pin_len - collar_depth) :
    z_recess == 1 ? pin_len : 0;

// Dois machos coaxiais no MESMO furo, um por face. Só faz
// sentido com as duas faces fêmeas.
slab_both = 2 * pin_len + gap;

// Furo de BORDA exige seção; é o que fixa o grid em 8mm

// Centro do bloco — onde vai o recurso central
cx = total_x / 2;
cy = total_y / 2;
cz = total_z / 2;

// Um furo micro sobrevive se o recurso central não o alcançar.
// Filtro por distância: não há lista fixa a manter.
center_reach = center == "none" ? 0 : center_recess / 2 + recess_d / 2 + wall;
function alive(a, b) = center == "none" ||
    sqrt(pow(a - cx, 2) + pow(b - cy, 2)) >= center_reach;

// Folga de MONTAGEM: uma peça de 1 célula encaixada no furo
// vizinho estende (grid/2)·√2 até a quina. Continuidade de
// material não basta — foi o que a impressão mostrou.
live_pts   = [ for (x = xs) for (y = ys) if (alive(x, y)) [x, y] ];
near_micro = center == "none" || len(live_pts) == 0 ? 1e9
    : min([ for (p = live_pts) sqrt(pow(p[0]-cx,2) + pow(p[1]-cy,2)) ]);
asm_clear  = near_micro - (grid/2) * sqrt(2) - center_recess / 2;

// ============================================================
// VALIDAÇÃO — crítico para a geração; brando avisa
// ============================================================
for (i = [0 : 5])
    assert(!(fc[i] == "recess" && ax[i] == "solid"),
           "face 'recess' exige o eixo correspondente 'bored'");
assert(center == "none" || asm_clear > 0,
       "recurso central invade a quina de uma peça encaixada no furo vizinho");

// --- Laje ---
assert(!slab || z_recess == 0 || thickness > slab_floor,
       str("laje fina demais: ", thickness, " <= ", slab_floor,
           " com ", z_recess, " face(s) Z fêmea(s) — sem encosto para o",
           " colar, o macho atravessa"));
// Furo de borda exige seção que a laje não tem. Erro em vez de
// corrigir em silêncio: quem pediu 'bored' precisa saber por que
// não pode.
assert(!slab || thickness >= edge_bore_min || axis_x == "solid",
       str("laje de ", thickness, "mm não comporta furo no eixo X (mínimo ",
           edge_bore_min, "): use axis_x=\"solid\""));
assert(!slab || thickness >= edge_bore_min || axis_y == "solid",
       str("laje de ", thickness, "mm não comporta furo no eixo Y (mínimo ",
           edge_bore_min, "): use axis_y=\"solid\""));

// ============================================================
// MÓDULOS
// ============================================================
// Arredondar come a face plana perto da aresta. Um macho no centro
// da célula da ponta precisa de grid/2 − collar_d/2 de face plana
// em volta dele; acima disso, a base do colar ficaria solta no ar.
// Peça arredondada se junta por CAVILHA (recess × recess), como um
// kit técnico — não por macho integral.
ra = round_axis == "x" ? 0 : round_axis == "y" ? 1 : round_axis == "z" ? 2 : -1;
dims = [total_x, total_y, total_z];
r_eff = ra < 0 ? 0 :
    min(corner_r, min([ for (i = [0 : 2]) if (i != ra) dims[i] ]) / 2);
pin_safe_r = grid / 2 - collar_d / 2;
for (i = [0 : 5])
    assert(!(fc[i] == "pin" && ra >= 0 && floor(i / 2) != ra && r_eff > pin_safe_r + 1e-6
             && pin_cells != "inner"),
           str("face ", ["xn","xp","yn","yp","zn","zp"][i], " 'pin' numa aresta arredondada (raio ",
               r_eff, " > ", pin_safe_r, "): use recess (cavilha) ou corner_r menor"));

module body() {
    if (ra < 0 || r_eff <= 0) cube(dims);
    else {
        // casco das 4 arestas arredondadas, no plano perpendicular a `ra`
        q = [ for (i = [0 : 2]) if (i != ra) i ];
        hull() for (u = [r_eff, dims[q[0]] - r_eff]) for (v = [r_eff, dims[q[1]] - r_eff]) {
            p = [ for (i = [0 : 2]) i == q[0] ? u : i == q[1] ? v : 0 ];
            translate(p)
                rotate(ra == 0 ? [0, 90, 0] : ra == 1 ? [-90, 0, 0] : [0, 0, 0])
                    cylinder(r = r_eff, h = dims[ra]);
        }
    }
}

// Leva os filhos para cada furo da face `f`, com +Z apontando
// para FORA. Furo, rebaixo e macho passam pelo MESMO referencial,
// então não podem divergir entre si.
// A origem cai EXATAMENTE na superfície, sem épsilon: o rebaixo
// mede a profundidade a partir dela, e um deslocamento aqui
// deixaria uma lasca no fundo do rebaixo — que colide com o
// colar do macho. Quem precisa de overshoot para render limpo o
// declara localmente.
FACE_Q   = [[1, 2], [1, 2], [0, 2], [0, 2], [0, 1], [0, 1]];   // eixos no plano de cada face
FACE_ROT = [[0, -90, 0], [0, 90, 0], [90, 0, 0], [-90, 0, 0], [180, 0, 0], [0, 0, 0]];
cs = [xs, ys, zs];

function face_at(f, u, v) = let (a = floor(f / 2), q = FACE_Q[f])
    [ for (i = [0 : 2]) i == a ? (f % 2 == 1 ? dims[a] : 0) : i == q[0] ? u : v ];

// Quais células da face recebem o filho. Faces Z passam pelo filtro
// do recurso central: onde ele comeu o furo, não sobra rebaixo nem
// macho (rebaixo sem furo é bolso cego).
//   all    todas
//   edge   só o perímetro (tampa lisa sobre um quadro)
//   inner  só as planas — pula as pontas arredondadas (viga empilhada)
function on_edge(v, list) = v == list[0] || v == list[len(list) - 1];
function rnd(q) = ra >= 0 && q != ra && r_eff > pin_safe_r + 1e-6;
function flat(v, list, q) = !(rnd(q) && on_edge(v, list));
function keep(f, u, v, mode) = let (q = FACE_Q[f], U = cs[q[0]], V = cs[q[1]])
    (floor(f / 2) != 2 || alive(u, v)) &&
    (mode == "edge"  ? (on_edge(u, U) || on_edge(v, V)) :
     mode == "inner" ? (flat(u, U, q[0]) && flat(v, V, q[1])) : true);

module at_face(f, mode = "all") {
    q = FACE_Q[f];
    for (u = cs[q[0]]) for (v = cs[q[1]]) if (keep(f, u, v, mode))
        translate(face_at(f, u, v)) rotate(FACE_ROT[f]) children();
}

// Furo passante ao longo de um eixo bored
module bores() {
    e = 0.02;
    if (axis_x == "bored") for (b = ys) for (c = zs) if (alive_axis(1,b,c))
        translate([-e, b, c]) rotate([0,90,0]) cylinder(d = hole_d, h = total_x + 2*e);
    if (axis_y == "bored") for (a = xs) for (c = zs) if (alive_axis(2,a,c))
        translate([a, -e, c]) rotate([-90,0,0]) cylinder(d = hole_d, h = total_y + 2*e);
    if (axis_z == "bored") for (a = xs) for (b = ys) if (alive(a, b))
        translate([a, b, -e]) cylinder(d = hole_d, h = total_z + 2*e);
}

// O recurso central só filtra o eixo Z (é onde ele mora)
function alive_axis(axis, u, v) = true;

// Rebaixo e macho passam pelo MESMO referencial (at_face) e pela
// MESMA geometria (params.scad), então não podem divergir.
module recesses() {
    for (i = [0 : 5]) if (fc[i] == "recess" && ax[i] == "bored") at_face(i) fb_female();
}

module face_pins() {
    for (i = [0 : 5]) if (fc[i] == "pin") at_face(i, pin_cells) fb_male(0.01);
}

module center_hole() {
    e = 0.02;
    translate([cx, cy, -e]) cylinder(d = center_size, h = total_z + 2*e);
    translate([cx, cy, -e]) cylinder(d = center_recess, h = collar_depth + e);
    translate([cx, cy, total_z - collar_depth])
        cylinder(d = center_recess, h = collar_depth + e);
}

module brick() {
    difference() {
        union() {
            body();
            face_pins();
        }
        bores();
        recesses();
        if (center != "none") center_hole();
    }
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.35, 0.38, 0.42];
color(part_color) brick();

// ============================================================
// INFO
// ============================================================
echo("=== BRICK ===");
echo(str("PRIMITIVOS  furo Ø", hole_d, " | parede ", wall, " | colar ", collar_w, "×", collar_depth, " | folga ", tolerance, " | gap ", gap));
echo(str("DERIVADOS   grid ", grid, " | rebaixo Ø", recess_d, " | pino Ø", pin_d, "×", pin_len, " | colar Ø", collar_d));
echo(slab
    ? str("Laje        ", total_x, " × ", total_y, " × ", total_z, "mm (", cells_x, "×", cells_y, " células, espessura livre)")
    : str("Bloco       ", total_x, " × ", total_y, " × ", total_z, "mm (", cells_x, "×", cells_y, "×", cells_z, " células)"));
echo(str("Eixos       x=", axis_x, " y=", axis_y, " z=", axis_z));
echo(str("Faces       ", fc));
echo(str("Central     ", center == "none" ? "nenhum" : str(center, " Ø", center_size)));
echo("---");
echo(str("Lasca na quina    : ", inset - recess_d/2, "mm  (= parede ", wall, ")"));
echo(str("Alma entre furos  : ", grid - recess_d, "mm  (= 2×parede ", 2*wall, ")"));
echo(str("Barra da aresta   : ", (grid - hole_d)/2, "mm"));
echo(str("Haste além do colar: ", pin_len - collar_depth, "mm"));
// Uma laje entre slab_min e slab_both é peça válida, só não
// aceita macho dos dois lados NO MESMO FURO — as pontas se
// aproximam mais que `gap`. Aviso, não erro.
if (slab && z_recess > 0) {
    echo(str("Laje: ", z_recess, " face(s) Z fêmea(s) | piso ", slab_floor,
             " | ideal ", slab_min, " | atual ", thickness));
    // Entre o piso e o ideal a peça é válida: só falta espessura
    // para a haste caber inteira, e ela sai pelo lado oposto.
    if (thickness < slab_min)
        echo(str("AVISO laje: a haste do macho ultrapassa ",
                 slab_min - thickness, "mm — sai pela face oposta"));
    // Coaxial só existe com as duas faces fêmeas
    if (z_recess == 2)
        echo(thickness >= slab_both
            ? str("Laje: furo serve os DOIS lados (folga entre machos ",
                  thickness - 2*pin_len, "mm >= gap ", gap, ")")
            : str("AVISO laje: ", thickness, "mm < ", slab_both,
                  " — cada furo serve UM lado por vez; macho dos dois lados",
                  " deixa só ", thickness - 2*pin_len, "mm entre as pontas"));
}
// O assert de montagem passa POR VACUIDADE quando o recurso
// central engole todos os furos — não sobra nada com o que
// colidir. Geometricamente é peça válida (um flange), mas
// raramente é o que se quis. Daí o aviso.
if (center != "none")
    echo(len(live_pts) == 0
        ? str("AVISO: o recurso central Ø", center_size,
              " engoliu TODOS os furos — o bloco ficou sem interface micro")
        : str("Folga de montagem : ", asm_clear, "mm  (furos vivos: ", len(live_pts), ")"));
