// ============================================================
// AXLE — Design System 3D Modular
// ============================================================
// Eixo de roda. É um PIN de uma ponta com um MANCAL e um FLANGE
// no lugar da segunda ponta: a ponta interna prende na peça como
// qualquer macho, o mancal carrega a roda girando, e o flange
// segura a roda no lugar.
//
//   peça   │ roda (gira)        │
//   ───────┤────────────────────┤
//    ┌─┐┌──┴────────────────┐┌──┴┐
//    │ ││ colar   mancal    ││fl.│   ← flange no rebaixo da roda
//    └─┘└──┬────────────────┘└──┬┘
//   haste  │                    │
//
// Eixo ao longo de Z. z = 0 é a FACE da peça; z < 0 entra nela,
// z > 0 é o lado da roda.
//
// A ponta interna é IDÊNTICA à de um PIN: colar `collar_d` ×
// `collar_depth` no rebaixo + haste até `pin_len`. Por isso o
// eixo entra em qualquer porta `recess` e obedece às mesmas
// regras de encaixe (constituição § 5).
//
// Imprimir em pé, com o flange na mesa.
//
// spec: spec/parts/wheel.md
// ============================================================

include <params.scad>

// Largura da roda em células — o mancal acompanha
width_cells = 1; // [1:1:4]

// ============================================================
// DERIVADOS
// ============================================================
wheel_w  = width_cells * grid;
flange_d = recess_d + 2 * wall;
flange_h = collar_depth;
bearing  = wheel_w - flange_h;         // mancal: do rosto da peça ao flange

// ============================================================
// MÓDULOS
// ============================================================
module axle() {
    union() {
        // ponta interna — o mesmo macho de toda peça, virado para dentro
        mirror([0, 0, 1]) fb_male();
        // mancal + flange
        cylinder(d = collar_d, h = bearing + 0.01);
        translate([0, 0, bearing]) cylinder(d = flange_d, h = flange_h);
    }
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.85, 0.55, 0.20];
color(part_color) axle();

echo("=== AXLE ===");
echo(str("Ponta       colar Ø", collar_d, "×", collar_depth, " + haste Ø", pin_d, " | entra ", pin_len, "mm"));
echo(str("Mancal      Ø", collar_d, " × ", bearing, "mm | flange Ø", flange_d, "×", flange_h));
