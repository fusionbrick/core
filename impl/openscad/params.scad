// ============================================================
// PARAMS — primitivos e derivados do sistema
// ============================================================
// FONTE ÚNICA dos primitivos no OpenSCAD. Toda peça faz
// `include <params.scad>` em vez de redeclarar.
//
// Antes disto os 7 primitivos estavam copiados em brick, pin,
// node e dock — 28 declarações para 7 valores. Foi o que deixou
// `pin_len` ficar 1.6 na spec e 2.0 em quatro implementações sem
// ninguém notar. O `make spec-check` DETECTA essa divergência;
// este arquivo IMPEDE que ela exista.
//
// Reatribuir daqui funciona por include aninhado — testado:
// variante -> peça -> params propaga e os derivados recomputam.
//
// ⚠️ Variável NOVA da variante tem de ser declarada ANTES do
// `include`. Depois dele o OpenSCAD avalia a reatribuição no
// ponto da declaração original, onde a variável nova ainda não
// existe: sai `WARNING: Ignoring unknown variable` e o valor
// errado, em silêncio.
//
// contrato: spec/parts/brick/contracts.toml
// premissas: spec/constitution.md
// ============================================================

/* [Primitivos do sistema] */

// Diâmetro do furo passante — a interface mecânica
hole_d = 4.0; // [1:0.1:30]

// Parede interna mínima (4 perímetros de 0.4)
wall = 1.6; // [0.4:0.1:6]

// Degrau RADIAL entre furo e rebaixo (1 bico de 0.4)
collar_w = 0.4; // [0:0.1:2]

// Profundidade AXIAL do rebaixo
collar_depth = 1.0; // [0.25:0.25:4]

// Folga de press-fit, subtraída sempre do MACHO
tolerance = 0.2; // [0:0.05:0.6]

// Folga real mínima entre dois machos que se aproximam
gap = 0.5; // [0:0.1:2]

// Protrusão do macho. DECLARADO, não derivado: o limite é a
// colisão com o macho PERPENDICULAR, e essa aproximação é
// DIAGONAL, não axial. Ver constitution.md § 5.
pin_len = 2.0; // [0.5:0.05:6]

/* [Qualidade] */
$fn = 48;

// ============================================================
// DERIVADOS — nada aqui é escolhido à mão
// ============================================================
grid     = hole_d + 2 * (wall + collar_w);
recess_d = hole_d + 2 * collar_w;
pin_d    = hole_d - tolerance;
collar_d = recess_d - tolerance;
inset    = grid / 2;

// Teto do macho: duas hastes perpendiculares se tocam aqui.
pin_len_max = grid / 2 - pin_d / 2;

// Furo de BORDA exige seção — é o que fixa o grid.
edge_bore_min = hole_d + 2 * wall;

// Chanfro de entrada do macho. Constante, não parâmetro: existe
// para o macho achar o furo, e ninguém decide isso peça a peça.
lead_in = 0.4;

assert(pin_len <= pin_len_max,
       str("macho longo demais: ", pin_len, " > ", pin_len_max,
           " — encosta no macho perpendicular da célula receptora"));
assert(pin_len > collar_depth,
       "colar mais fundo que a protrusão: a haste não sai do colar");
assert(hole_d * sqrt(2) > recess_d,
       "rebaixo morde a barra da aresta: exige hole_d·√2 > recess_d");

// ============================================================
// O CONECTOR — desenhado UMA vez, usado por toda peça
// ============================================================
// Referencial: origem no centro da face, +Z para FORA da peça.

// Vocabulário dos encaixes. A IR de montagem diz stud / socket / flat
// (spec/assembly.md § Nomes); os parâmetros das peças sempre disseram
// pin / recess / plain. As duas formas valem em qualquer -D.
function fb_kind(k) = k == "stud" ? "pin" : k == "socket" ? "recess" : k == "flat" ? "plain" : k;

// MACHO: colar (quem retém) + haste + chanfro de entrada.
// `sink` afunda a base no corpo, só para a união não ficar coplanar.
module fb_male(sink = 0) {
    translate([0, 0, -sink]) cylinder(d = collar_d, h = collar_depth + sink);
    cylinder(d = pin_d, h = pin_len - lead_in);
    translate([0, 0, pin_len - lead_in])
        cylinder(r1 = pin_d / 2, r2 = pin_d / 2 - lead_in, h = lead_in);
}

// FÊMEA (para subtrair): rebaixo que aloja o colar e, com `bore > 0`,
// o furo de profundidade `bore` atrás dele.
module fb_female(bore = 0, recess = true) {
    e = 0.02;
    if (recess) translate([0, 0, -collar_depth]) cylinder(d = recess_d, h = collar_depth + e);
    if (bore > 0) translate([0, 0, -bore]) cylinder(d = hole_d, h = bore + e);
}
