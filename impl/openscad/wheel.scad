// ============================================================
// WHEEL — Design System 3D Modular
// ============================================================
// Roda do sistema. GIRA sobre um AXLE (axle.scad), que por sua
// vez entra num rebaixo comum de qualquer face `recess` — a roda
// monta em qualquer BRICK sem furo dedicado.
//
//        ╭───────────╮
//      ╱ ▮ ▮ ▮ ▮ ▮ ▮ ▮ ╲     ← pneu com sulcos (banda central)
//     │   ◯    ◯    ◯   │    ← alma com furos de alívio
//     │      ┌───┐      │
//     │   ◯  │ ◎ │  ◯   │    ← cubo: furo de giro + rebaixo
//     │      └───┘      │       do flange do eixo
//      ╲               ╱
//        ╰───────────╯
//
// Eixo de rotação = Z. z = 0 é a face INTERNA (encosta na peça),
// z = grid é a face EXTERNA (onde o flange do eixo assenta).
//
// LARGURA = 1 célula. A roda ocupa exatamente uma célula ao longo
// do eixo, FORA do volume da peça onde monta — é material de
// acabamento, igual à pele (Lei do Grid). O diâmetro é múltiplo
// do grid para a montagem raciocinar em células.
//
// GIRO, NÃO PRESS-FIT. O furo do cubo é `collar_d + run_clear`:
// gira sobre o mancal do eixo (Ø collar_d). Quem prende é o
// eixo — colar no rebaixo da peça, flange no rebaixo da roda.
//
// Imprimir com a face EXTERNA na mesa: cubo e pneu apoiam no
// mesmo plano, e o rebaixo do flange sai sem suporte.
//
// spec: spec/parts/wheel.md
// ============================================================

include <params.scad>

/* [Tamanho] */
// Diâmetro em células (diâmetro = wheel_cells × grid)
wheel_cells = 4; // [3:1:12]

// Largura em células ao longo do eixo
width_cells = 1; // [1:1:6]

/* [Pneu] */
// Número de sulcos/gomos da banda (0 = lisa)
tread_count = 20; // [0:1:48]

// "street" = sulco transversal · "offroad" = gomos alternados ·
// "balloon" = pneu balão: perfil redondo + gomos em RELEVO
tread = "street"; // [street, offroad, balloon]

// Raios do aro (0 = alma com furos de alívio)
spokes = 0; // [0:1:10]
// "straight" = raio reto · "y" = raio que abre em Y perto do aro
spoke_style = "straight"; // [straight, y]

// ============================================================
// DERIVADOS
// ============================================================
wheel_d = wheel_cells * grid;
wheel_w = width_cells * grid;   // células inteiras ao longo do eixo

// Folga DIAMETRAL de giro. Maior que `tolerance` de propósito:
// tolerance é press-fit (prende), esta é mancal (solta).
run_clear   = 2 * tolerance;
// Folga AXIAL entre o fundo do rebaixo e o flange
axial_play  = tolerance;

// Flange do eixo — mesma conta do axle.scad
flange_d = recess_d + 2 * wall;
flange_h = collar_depth;

bore_d   = collar_d + run_clear;           // gira sobre o mancal
cbore_d  = flange_d + run_clear;           // aloja o flange
cbore_h  = flange_h + axial_play;
hub_d    = max(cbore_d + 2 * wall, wheel_d * 0.16);   // cubo cresce com a roda

// O pneu recua `gap` da face interna: só o cubo encosta na peça,
// então a banda não roça nela ao girar.
// Espessura radial: proporção de pneu, com piso no mínimo de parede
tire_t   = tread == "balloon" ? wheel_d * 0.22
         : max(2 * wall + collar_depth, wheel_d * 0.14);
tire_ri  = wheel_d / 2 - tire_t;
edge     = 2 * collar_w;                   // chanfro do pneu
web_t    = 3 * collar_w * 2;               // alma (2.4mm)
tread_d  = max(collar_depth, tire_t * 0.25); // profundidade do sulco

// Furos de alívio na alma, entre cubo e pneu
lite_r   = (hub_d / 2 + tire_ri) / 2;
lite_d   = (tire_ri - hub_d / 2) - 2 * wall;
lite_n   = 5;

// ============================================================
// VALIDAÇÃO
// ============================================================
assert(lite_d > 0 || wheel_cells >= 3,
       "roda pequena demais: não sobra alma entre cubo e pneu");
assert(tire_ri > hub_d / 2 + wall,
       str("pneu invade o cubo: raio interno ", tire_ri, " <= ", hub_d/2 + wall));

// ============================================================
// MÓDULOS
// ============================================================
lug_h = tire_t * 0.13;                     // relevo do gomo (balão)

// Perfil do balão: retângulo de cantos bem arredondados (ombro
// redondo), raio externo `ro`.
module balloon_profile(ro) {
    w0 = gap; w1 = wheel_w; sh = min(tire_t * 0.45, (w1 - w0) * 0.42);
    hull() {
        translate([tire_ri, w0]) square([0.01, w1 - w0]);
        translate([ro - sh, w0 + sh]) circle(r = sh, $fn = 32);
        translate([ro - sh, w1 - sh]) circle(r = sh, $fn = 32);
    }
}

module balloon() {
    n = tread_count;
    rotate_extrude($fn = max($fn, 96)) balloon_profile(wheel_d / 2 - lug_h);
    // Gomos: blocos em duas fileiras desencontradas, recortados pelo
    // perfil cheio — o relevo acompanha o ombro redondo.
    if (n > 0) intersection() {
        rotate_extrude($fn = max($fn, 96)) balloon_profile(wheel_d / 2);
        union() for (i = [0 : n - 1]) {
            mid = (gap + wheel_w) / 2;
            lw  = PI * wheel_d / n * 0.62;
            rotate([0, 0, i * 360 / n])
                translate([tire_ri, -lw / 2, i % 2 == 0 ? mid - wall * 0.4 : gap - 1])
                    cube([wheel_d, lw, (i % 2 == 0 ? wheel_w - mid + wall * 0.4 + 1
                                                   : mid - gap + wall * 0.4 + 1)]);
        }
    }
}

module tire() {
    if (tread == "balloon") balloon(); else
    rotate_extrude($fn = max($fn, 96))
        polygon([
            [tire_ri,            gap],
            [wheel_d/2 - edge,   gap],
            [wheel_d/2,          gap + edge],
            [wheel_d/2,          wheel_w - edge],
            [wheel_d/2 - edge,   wheel_w],
            [tire_ri,            wheel_w],
        ]);
}

module treads() {
    if (tread_count > 0 && tread == "street")
        for (i = [0 : tread_count - 1])
            rotate([0, 0, i * 360 / tread_count])
                translate([wheel_d/2 - tread_d, -wall/2, gap + 2*edge])
                    cube([tread_d + 1, wall, wheel_w - gap - 4*edge]);
    // Gomos: sulcos transversais em meia largura, alternando lado a
    // cada passo — a banda vira um tabuleiro de blocos
    if (tread_count > 0 && tread == "offroad") {
        mid = (gap + wheel_w) / 2;
        gw  = PI * wheel_d / tread_count * 0.42;   // largura do sulco
        for (i = [0 : tread_count - 1])
            rotate([0, 0, i * 360 / tread_count])
                translate([wheel_d/2 - tread_d, -gw/2,
                           i % 2 == 0 ? mid - wall/2 : gap - 1])
                    cube([tread_d + 1, gw,
                          i % 2 == 0 ? wheel_w - mid + wall/2 + 1 : mid - gap + wall/2 + 1]);
        // sulco circunferencial raso no centro
        translate([0, 0, mid - wall/4])
            difference() {
                cylinder(r = wheel_d/2 + 1, h = wall/2);
                translate([0, 0, -1]) cylinder(r = wheel_d/2 - tread_d/2, h = wall/2 + 2);
            }
    }
}

module web() {
    zc = (gap + wheel_w) / 2;
    if (spokes > 0) {
        // Aro: anel interno do pneu + raios retos até o cubo. O
        // disco fica recuado da face externa (prato), o que dá
        // profundidade sem custar material.
        rim_t = wall * 1.5;
        translate([0, 0, gap])
            difference() {
                cylinder(r = tire_ri + 0.01, h = wheel_w - gap - wall);
                translate([0, 0, -1]) cylinder(r = tire_ri - rim_t, h = wheel_w + 2);
            }
        sp_w = spoke_style == "y" ? max(wall * 1.6, wheel_d * 0.05) : max(wall * 1.6, hub_d * 0.32);
        // raio em Y fica rente à face externa (roda "de prato raso");
        // o reto continua no meio da largura
        zc = spoke_style == "y" ? wheel_w - wall - web_t : (gap + wheel_w) / 2;
        // Raio em Y: dois braços que saem juntos do cubo e se abrem
        // até o aro — o desenho de roda de 5 raios duplos
        ri = tire_ri - rim_t / 2;
        for (i = [0 : spokes - 1]) rotate([0, 0, i * 360 / spokes]) {
            if (spoke_style == "y")
                for (sgn = [-1, 1]) hull() {
                    translate([hub_d / 2, 0, zc - web_t]) cylinder(d = sp_w, h = 2 * web_t, $fn = 16);
                    rotate([0, 0, sgn * 360 / spokes * 0.16])
                        translate([ri, 0, zc - web_t]) cylinder(d = sp_w * 0.7, h = 2 * web_t, $fn = 16);
                }
            else
                translate([0, -sp_w/2, zc - web_t]) cube([ri, sp_w, 2 * web_t]);
        }
        // Prato: anel externo do aro avança até a face, dá borda
        translate([0, 0, wheel_w - wall])
            difference() {
                cylinder(r = tire_ri + 0.01, h = wall);
                translate([0, 0, -1]) cylinder(r = tire_ri - rim_t * 0.8, h = wall + 2);
            }
    } else
    difference() {
        translate([0, 0, zc - web_t/2])
            cylinder(r = tire_ri + 0.01, h = web_t);
        if (lite_d > 2)
            for (i = [0 : lite_n - 1])
                rotate([0, 0, i * 360 / lite_n])
                    translate([lite_r, 0, -1]) cylinder(d = lite_d, h = wheel_w + 2);
    }
}

module wheel() {
    difference() {
        union() {
            difference() { tire(); treads(); }
            web();
            cylinder(d = hub_d, h = wheel_w);
        }
        translate([0, 0, -0.01]) cylinder(d = bore_d, h = wheel_w + 0.02);
        translate([0, 0, wheel_w - cbore_h]) cylinder(d = cbore_d, h = cbore_h + 0.01);
    }
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.12, 0.12, 0.13];
color(part_color) wheel();

// ============================================================
// INFO
// ============================================================
echo("=== WHEEL ===");
echo(str("Roda        Ø", wheel_d, " × ", wheel_w, "mm (", wheel_cells, " células)"));
echo(str("Cubo        Ø", hub_d, " | furo de giro Ø", bore_d, " | rebaixo do flange Ø", cbore_d, "×", cbore_h));
echo(str("Pneu        ", tire_t, "mm | ", tread_count, " sulcos | recuo interno ", gap, "mm"));
