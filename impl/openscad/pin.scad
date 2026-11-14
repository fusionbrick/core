// ============================================================
// PIN — Design System 3D Modular
// ============================================================
// O único macho solto do sistema. Une dois furos, em qualquer
// escala. Absorve BRIDGE (cavilha), LINK (conector de face) e
// LINK-ONESIDE — os três eram o mesmo objeto em tamanhos
// diferentes.
//
// NOTA DE NOMENCLATURA: até a v1, PIN era o nome da viga. A
// viga virou BRICK 1×1×n, e o nome passou para o macho — que
// é o que ele descreve.
//
//        ┌──┐        ← Ø pino
//     ┌──┴──┴──┐     ← Ø colar (assenta no rebaixo)
//     └──┬──┬──┘
//        └──┘
//
// QUEM RETÉM É O COLAR. A haste além dele ALINHA, não segura —
// alongar `pin_len` melhora torção e balanço, e não muda a
// força de arrancamento. Essa é `collar_depth` / `tolerance`.
//
// spec: spec/parts/pin.md
// ============================================================

// Primitivos e derivados: fonte única, não redeclarar aqui.
include <params.scad>

/* [Escala] */
// Diâmetro do furo RECEPTOR. Um PIN para o furo padrão e um
// para o recurso central são a mesma peça, com `size` diferente.
size = 4.0; // [2:0.5:60]

/* [Forma] */
// 1 = macho de uma ponta · 2 = cavilha, metade em cada furo
ends = 2; // [1:1:2]

// Afastamento entre as duas pontas. É onde o macho fica mais
// longo sem alterar quanto cada ponta entra.
spacer = 0; // [0:0.5:60]

// Chanfro de entrada

// Cópias lado a lado — peça pequena solta imprime mal
qty     = 1; // [1:1:20]
qty_gap = 4; // [2:0.5:20]

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

// Vazado quando o diâmetro permite. Na escala micro sobram
// 0.6mm — abaixo do jumper Dupont, então o macho é maciço.
canal_raw = pin_d - 2 * wall;
canal_d   = canal_raw >= 2.5 ? canal_raw : 0;

total_len = ends == 2 ? 2 * pin_len + spacer : pin_len;
collar_h  = ends == 2 ? 2 * collar_depth + spacer : collar_depth;

// ============================================================
// VALIDAÇÃO
// ============================================================
assert(ends != 2 || 2 * pin_len <= grid - gap,
       "duas pontas não cabem num furo passante compartilhado");
// ============================================================
// MÓDULOS
// ============================================================
// Haste centrada na origem, chanfrada nas DUAS pontas. O
// chanfro corta para DENTRO do comprimento — não estende.
module shaft_chamfered(len) {
    r = pin_d / 2;
    h = len / 2;
    if (lead_in <= 0) cylinder(d = pin_d, h = len, center = true);
    else union() {
        cylinder(d = pin_d, h = len - 2 * lead_in, center = true);
        translate([0, 0,  h - lead_in]) cylinder(r1 = r, r2 = r - lead_in, h = lead_in);
        translate([0, 0, -h])           cylinder(r1 = r - lead_in, r2 = r, h = lead_in);
    }
}

module pin_solid() {
    if (ends == 2) {
        // Cavilha: haste passante + colar central, dividido
        // entre os rebaixos dos dois furos
        union() {
            shaft_chamfered(total_len);
            translate([0, 0, -collar_h/2]) cylinder(d = collar_d, h = collar_h);
        }
    } else {
        fb_male();
    }
}

// Módulo público da peça — mesmo padrão de brick()/node()/dock(),
// que é o nome que um assembly importa com `use <pin.scad>`.
module pin() {
    if (canal_d <= 0) pin_solid();
    else difference() {
        pin_solid();
        translate([0, 0, -total_len])
            cylinder(d = canal_d, h = 3 * total_len);
    }
}

// ============================================================
// RENDER
// ============================================================
part_color = [0.85, 0.55, 0.20];
color(part_color)
    for (i = [0 : qty - 1])
        translate([i * (collar_d + qty_gap), 0, 0]) pin();

// ============================================================
// INFO
// ============================================================
echo("=== PIN ===");
echo(str("Escala      furo receptor Ø", size, " | grid do sistema ", grid));
echo(str("PINO        haste Ø", pin_d, " | colar Ø", collar_d, "×", collar_h, " | protrusão ", pin_len, " por ponta"));
echo(str("Forma       ", ends, " ponta(s) | spacer ", spacer, " | total ", total_len, "mm (×", qty, ")"));
echo("---");
echo(str("Haste além do colar : ", pin_len - collar_depth, "mm  — quem retém é o COLAR"));
echo(str("Aperto no colar     : ", recess_d - collar_d, "mm no diâmetro"));
echo(str("Canal de fio        : ", canal_d > 0 ? str("Ø", canal_d, "mm") : str("fechado (só ", canal_raw, "mm, mínimo 2.5)")));
