// ============================================================
// DOCK — Design System 3D Modular
// ============================================================
// Adapter: torna um dispositivo não-modular (motor, sensor,
// placa) compatível com o sistema.
//
// Por DENTRO é exclusivo do dispositivo (cavidade = perfil);
// por FORA é BRICK — mesmas células, mesmos eixos, mesmas
// faces. Trocar o dispositivo troca só o perfil.
//
//     pele    volume de grid    pele
//      ├─┤   ├───────────┤     ├─┤
//     ┌───┬───────────────────┬───┐
//     │   │        ( )        │   │   ← furos ancorados no GRID
//     └───┴───────────────────┴───┘
//
// LEI DE CENTRAGEM: o eixo do dispositivo coincide com o CENTRO
// DE UMA CÉLULA — é o que faz a ponta cair num furo padrão e
// receber engrenagem ou acoplador como qualquer outra peça.
//
// PELE: um dispositivo maior que a célula NÃO exige mais
// células, exige pele — material fora do volume de grid, na
// escala fina. Os furos continuam ancorados no reticulado.
//
// spec: spec/parts/dock.md
// ============================================================

// Primitivos e derivados: fonte única, não redeclarar aqui.
include <params.scad>

/* [Dispositivo] */
device = "motor-130"; // [motor-130]

// Folga radial da cavidade — LOCAL, não é a `tolerance` do
// sistema. Dispositivo comercial tem dispersão de lote própria.
device_clearance = 0.2; // [0:0.05:1]

// Material atrás do dispositivo
wall_back = 2.5; // [1:0.5:20]

/* [Envelope] */
cells_x = 1; // [1:1:8]
cells_y = 1; // [1:1:8]
cells_z = 3; // [1:1:8]

skin_x = 10;  // [0:2.5:30]
skin_y = 7.5; // [0:2.5:30]
skin_z = 2.5; // [0:2.5:30]

// Célula em que o eixo está centrado
axis_cell_x = 0; // [0:1:7]
axis_cell_y = 0; // [0:1:7]

/* [Divisão] */
// O dispositivo não entra num volume fechado: o dock parte no
// plano do eixo, o único onde a abertura tem a maior seção.
split = "none"; // [none, a, b]

/* [Bordas] */
border_radius = 0;       // [0:0.1:5]
border_style  = "round"; // [round, chamfer]

// ============================================================
// PERFIS DE DISPOSITIVO
// ============================================================
// Descrevem SÓ o dispositivo, nunca o dock.
// [can_d, can_flat, can_len, boss_d, boss_h, shaft_d, shaft_len]
//
// motor-130: motor DC do "motor amarelo" (TT), SEM redutor.
// DATASHEET, não medido — confirmar com paquímetro. Os
// achatamentos travam o torque de reação: fricção no cilindro
// não impede o motor de girar dentro do dock sob carga.
function device_profile(n) =
    n == "motor-130" ? [20.1, 15.1, 25.0, 6.15, 1.7, 2.0, 9.0] :
    undef;

// ============================================================
// DERIVADOS
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

fine     = 2.5;

prof = device_profile(device);
can_d = prof[0]; can_flat = prof[1]; can_len = prof[2];
boss_d = prof[3]; boss_h = prof[4];
shaft_d = prof[5]; shaft_len = prof[6];

total_x = cells_x * grid + 2 * skin_x;
total_y = cells_y * grid + 2 * skin_y;
total_z = cells_z * grid + 2 * skin_z;

function centers(n, skin) = [ for (i = [0 : n-1]) skin + i * grid + grid/2 ];
xs = centers(cells_x, skin_x);
ys = centers(cells_y, skin_y);
zs = centers(cells_z, skin_z);

axis_x = skin_x + axis_cell_x * grid + grid/2;
axis_y = skin_y + axis_cell_y * grid + grid/2;

device_z0        = wall_back;
shaft_protrusion = wall_back + can_len + shaft_len - total_z;
wall_front       = total_z - (wall_back + can_len);

wall_x = min(axis_x, total_x - axis_x) - can_d/2    - device_clearance;
wall_y = min(axis_y, total_y - axis_y) - can_flat/2 - device_clearance;

// Pele mínima por eixo — o eixo tem de cair num CENTRO DE
// CÉLULA, então a conta não é só "cabe a cavidade"
function skin_min(half, cells) =
    max(0, ceil((half + device_clearance + wall - cells*grid/2) / fine) * fine);
skin_x_min = skin_min(can_d/2,    cells_x);
skin_y_min = skin_min(can_flat/2, cells_y);

split_y = axis_y;
safe_r  = min(border_radius, grid/2 - 0.01);

// ============================================================
// VALIDAÇÃO
// ============================================================
assert(wall_x >= wall, str("parede lateral X insuficiente: ", wall_x, " < ", wall));
assert(wall_y >= wall, str("parede lateral Y insuficiente: ", wall_y, " < ", wall));
assert(wall_front > 0, "sem material na frente: reduza wall_back ou aumente cells_z/skin_z");
assert(shaft_d + 2*device_clearance <= hole_d, "eixo do dispositivo maior que o furo padrão");
assert(skin_x % fine == 0 && skin_y % fine == 0 && skin_z % fine == 0,
       "pele precisa ser múltipla da escala fina (2.5mm)");

// ============================================================
// MÓDULOS
// ============================================================
module border_finish(r) {
    if (border_style == "chamfer")
        polyhedron(points = [[r,0,0],[-r,0,0],[0,r,0],[0,-r,0],[0,0,r],[0,0,-r]],
                   faces = [[4,2,0],[4,1,2],[4,3,1],[4,0,3],[5,0,2],[5,2,1],[5,1,3],[5,3,0]]);
    else sphere(r = r);
}

module body() {
    if (safe_r <= 0) cube([total_x, total_y, total_z]);
    else minkowski() {
        translate([safe_r, safe_r, safe_r])
            cube([total_x - 2*safe_r, total_y - 2*safe_r, total_z - 2*safe_r]);
        border_finish(safe_r);
    }
}

// Furos passantes nos três eixos, no centro de cada célula
module bores() {
    e = 0.02;
    for (b = ys) for (c = zs) translate([-e, b, c]) rotate([0,90,0])
        cylinder(d = hole_d, h = total_x + 2*e);
    for (a = xs) for (c = zs) translate([a, -e, c]) rotate([-90,0,0])
        cylinder(d = hole_d, h = total_y + 2*e);
    for (a = xs) for (b = ys) translate([a, b, -e])
        cylinder(d = hole_d, h = total_z + 2*e);
}

// Rebaixo nas bocas externas
module recesses() {
    e = 0.01;
    for (b = ys) for (c = zs) {
        translate([-e, b, c]) rotate([0,90,0]) cylinder(d = recess_d, h = collar_depth+e);
        translate([total_x+e, b, c]) rotate([0,-90,0]) cylinder(d = recess_d, h = collar_depth+e);
    }
    for (a = xs) for (c = zs) {
        translate([a, -e, c]) rotate([-90,0,0]) cylinder(d = recess_d, h = collar_depth+e);
        translate([a, total_y+e, c]) rotate([90,0,0]) cylinder(d = recess_d, h = collar_depth+e);
    }
    for (a = xs) for (b = ys) {
        translate([a, b, -e]) cylinder(d = recess_d, h = collar_depth+e);
        translate([a, b, total_z - collar_depth]) cylinder(d = recess_d, h = collar_depth+e);
    }
}

// Volume negativo do dispositivo. Origem na face traseira do
// can, eixo em +Z.
module device_negative(clr) {
    intersection() {
        cylinder(d = can_d + 2*clr, h = can_len + clr);
        translate([-(can_d/2 + clr + 1), -(can_flat/2 + clr), -1])
            cube([can_d + 2*clr + 2, can_flat + 2*clr, can_len + clr + 2]);
    }
    translate([0,0,can_len]) cylinder(d = boss_d + 2*clr, h = boss_h + clr);
    translate([0,0,can_len]) cylinder(d = shaft_d + 2*clr, h = shaft_len + clr + 0.01);
}

module split_cut() {
    e = 1;
    if (split == "a")
        translate([-e, split_y, -e]) cube([total_x+2*e, total_y+e, total_z+2*e]);
    else if (split == "b")
        translate([-e, split_y - total_y - e, -e]) cube([total_x+2*e, total_y+e, total_z+2*e]);
}

module dock() {
    difference() {
        body();
        bores();
        recesses();
        translate([axis_x, axis_y, device_z0]) device_negative(device_clearance);
        split_cut();
    }
}

module device_ghost() {
    translate([axis_x, axis_y, device_z0]) device_negative(0);
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.35, 0.38, 0.42];
ghost = 0; // [0:1]
color(part_color) dock();
if (ghost > 0) color([0.85, 0.25, 0.15, 0.55]) device_ghost();

// ============================================================
// INFO
// ============================================================
echo("=== DOCK ===");
echo(str("Dispositivo ", device, " — can Ø", can_d, "/", can_flat, " × ", can_len));
echo(str("Envelope    ", total_x, " × ", total_y, " × ", total_z, "mm  (", cells_x, "×", cells_y, "×", cells_z, " células + pele ", skin_x, "/", skin_y, "/", skin_z, ")"));
echo(str("Eixo em     (", axis_x, ", ", axis_y, ") — centro da célula [", axis_cell_x, "][", axis_cell_y, "]"));
echo("---");
echo(str("Parede X ", wall_x, "mm · Y ", wall_y, "mm · traseira ", wall_back, "mm · dianteira ", wall_front, "mm"));
echo(str("Saliência do eixo : ", shaft_protrusion, "mm"));
echo(str("Pele mínima       : X ", skin_x_min, " · Y ", skin_y_min));
