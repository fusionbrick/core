// ============================================================
// CURVE (curva) — Design System 3D Modular
// ============================================================
// Viga CURVA de seção grid × grid. Faz o que o NODE não faz com
// suavidade: virar a esquina com um arco contínuo — anel de canto
// arredondado, retorno em U, arco de gaiola.
//
//        porta B (90°)
//          ┃
//      ╭───╯        ← arco de raio R na linha de centro
//      │
//   ━━━┛ porta A
//
// POR QUE R = (k + ½)·grid
// A porta A fica num centro de face (fronteira de célula na
// direção de avanço, centro de célula nas outras). Depois de 90°,
// a porta B precisa da MESMA regra no eixo novo. Isso só fecha se
// o raio da linha de centro for meia célula ímpar:
//   k = 0 → R = 4   cotovelo compacto, 1×1 célula
//   k = 1 → R = 12  curva aberta, 2×2 células
//   k = 2 → R = 20  3×3 células
// Com 180° a porta B volta na direção oposta, a 2R de A — também
// fecha. Outros ângulos não voltam ao grid: para eles, NODE.
//
// Referencial: arco no plano XY, centro na origem, começa em +X
// (ângulo 0) e gira no sentido anti-horário. A porta A fica em
// (R, 0, 0) olhando para −Y; o avanço é +Y e a curva vira para −X.
//
// spec: spec/parts/curve.md
// ============================================================

include <params.scad>

/* [Curva] */
// Raio em meias-células ímpares: R = (k + 0.5)·grid. Na IR de montagem: radius = k + 1
k = 1; // [0:1:6]
// 90 (esquina) ou 180 (retorno em U)
angle = 90; // [90, 180]

/* [Portas] */
port_a = "recess"; // [recess, pin, plain]  (ou socket, stud, flat)
port_b = "recess"; // [recess, pin, plain]  (ou socket, stud, flat)

// Raio das arestas da seção (acabamento)
edge_r = 1.2; // [0:0.2:3]

// ============================================================
// DERIVADOS
// ============================================================
R  = (k + 0.5) * grid;
ri = R - grid / 2;
ro = R + grid / 2;
// Furos verticais (Z) ao longo do arco, espaçados ~1 célula na
// linha de centro, longe das pontas (onde moram os furos de porta)
arc_len = R * angle * PI / 180;
n_side  = max(0, floor((arc_len - grid) / grid));
port_depth = grid / 2 + pin_len;     // furo da porta: entra além do macho

assert(angle == 90 || angle == 180, "CURVE só fecha no grid a 90° ou 180°");
assert(edge_r * 2 < grid, "edge_r grande demais para a seção");

// ============================================================
// MÓDULOS
// ============================================================
module section() {
    // quadrado grid × grid com cantos arredondados, centrado em R
    translate([R, 0])
        offset(r = edge_r) offset(delta = -edge_r) square(grid, center = true);
}

// referencial da porta: origem na face, +Z para FORA da peça
module at_port(which) {
    if (which == "a") translate([R, 0, 0]) rotate([90, 0, 0]) children();
    else rotate([0, 0, angle]) translate([R, 0, 0]) rotate([-90, 0, 0]) children();
}

pa = fb_kind(port_a);   // aceita também stud / socket / flat
pb = fb_kind(port_b);

module curve() {
    difference() {
        union() {
            rotate_extrude(angle = angle, $fn = max($fn, 96)) section();
            if (pa == "pin") at_port("a") fb_male(0.01);
            if (pb == "pin") at_port("b") fb_male(0.01);
        }
        // porta fêmea ou lisa: o furo entra no arco; só a fêmea leva rebaixo
        if (pa != "pin") at_port("a") fb_female(bore = pa == "plain" ? 0 : port_depth, recess = pa == "recess");
        if (pb != "pin") at_port("b") fb_female(bore = pb == "plain" ? 0 : port_depth, recess = pb == "recess");
        // furos verticais ao longo do arco, com rebaixo nas duas faces
        for (i = [0 : n_side - 1]) if (n_side > 0) {
            phi = (grid + i * grid + (arc_len - grid - (n_side - 1) * grid - grid) / 2) / R * 180 / PI;
            rotate([0, 0, phi + (grid / 2) / R * 180 / PI]) translate([R, 0, 0]) {
                translate([0, 0, -grid]) cylinder(d = hole_d, h = 2 * grid);
                translate([0, 0, grid / 2 - collar_depth]) cylinder(d = recess_d, h = collar_depth + 0.02);
                translate([0, 0, -grid / 2 - 0.02]) cylinder(d = recess_d, h = collar_depth + 0.02);
            }
        }
    }
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.11, 0.11, 0.12];
color(part_color) curve();

echo("=== CURVE ===");
echo(str("Curva       ", angle, "° | R ", R, " (interno ", ri, ", externo ", ro, ") | k ", k));
echo(str("Portas      A ", port_a, " · B ", port_b, " | furos laterais ", n_side));
