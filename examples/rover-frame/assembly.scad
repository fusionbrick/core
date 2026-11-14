// ============================================================
// ASSEMBLY — Rover: armação da carroceria (só vigas)
// ============================================================
// Perfil lateral em rampa: nariz baixo na frente, caixa do
// cockpit atrás dela e mala fechando a traseira. Nenhuma PLATE —
// tudo é PIN, com pino só nas pontas.
//
// Vista lateral (X-Z), x=0 = FRENTE:
//
//                        ┌──────┬──────╮
//                     ╱  │      │      │   ← mala (topo z=22.5)
//                  ╱     │caixa │      │
//               ╱        │      │      │
//        ╱─────────────────────────────┘
//   ────────────────────────────────────   ← base corrida
//   0            77.5   97.5   117.5  120
//
// PROPORÇÕES — do croqui: rampa ~63% do comprimento, caixa
// ~17%, mala ~17%. Com os 80mm do chassi antigo a rampa saía a
// 45° e não sobrava traseira, por isso o comprimento foi para
// 120mm (6 células).
//
// VIGAS DE COMPRIMENTO LIVRE
//
// A rampa mede 85mm a 28.07° — nem o comprimento nem o ângulo
// são múltiplos do passo, e não precisam ser. Com `ends="pin"`
// e as outras faces em "none", a viga conecta só pelas duas
// pontas, então as posições intermediárias não têm função.
// Isso também é o que economiza filamento: pino só onde encaixa.
//
// A restrição que sobra é sobre os EXTREMOS: os dois pontos de
// cada viga têm de cair em furo existente. Os vértices abaixo
// respeitam o reticulado (2.5 / 17.5 por célula).
// ============================================================

use <../../impl/openscad/pin.scad>
use <../../impl/openscad/elbow.scad>

/* [Montagem] */

// Explodir a montagem (mm de afastamento)
explode = 0; // [0:1:30]

// Renderizar interseções entre peças (vermelho = colisão)
check_collisions = false;

// ============================================================
// VÉRTICES DO PERFIL  [x, z]
// ============================================================
nose   = [  2.5,  2.5];   // ponta dianteira
box_f  = [ 77.5, 42.5];   // topo do poste dianteiro da caixa
box_r  = [ 97.5, 42.5];   // topo do poste traseiro da caixa
mala   = [117.5, 22.5];   // topo da mala
base_z = 2.5;
LEN    = 120;             // 6 células

// Lados: mesma bitola do chassi anterior
ys = [-2.5, 62.5];

// ============================================================
// VIGA ENTRE DOIS PONTOS
// ============================================================
// A rotação sai do VETOR, nunca escrita à mão:
//   +Y --Rx(90)--> +Z --Ry(θ)--> (sin θ, 0, cos θ)
// logo θ = atan2(dx, dz).
//
// Escrever o ângulo de cabeça foi a origem de três erros de
// orientação seguidos neste desenho — vigas apontando para trás
// e conectores soltos no ar. Derivando, o erro é impossível.
module beam(a, b, y) {
    d   = b - a;
    len = norm(d);
    translate([a[0], y, a[1]])
        rotate([0, atan2(d[0], d[1]), 0])
            rotate([90, 0, 0])
                pin(top = "none", bottom = "none", sides = "none",
                    ends = "pin", len = len);
}

// Viga transversal, ligando os dois lados.
// SEM rotação: o eixo do PIN já é +Y, que é a direção da bitola.
// (`rotate([-90,0,0])` mandaria +Y para −Z e a travessa desceria
// em vez de atravessar.)
module cross(p) {
    translate([p[0], ys[0], p[1]])
        pin(top = "none", bottom = "none", sides = "none",
            ends = "pin", len = ys[1] - ys[0]);
}

// ============================================================
// ARMAÇÃO
// ============================================================

module side_frames() {
    for (y = ys) {
        beam([0, base_z], [LEN, base_z], y);       // base corrida
        beam(box_f, nose, y);                       // rampa
        beam([box_f[0], base_z], box_f, y);         // poste dianteiro
        beam([box_r[0], base_z], box_r, y);         // poste traseiro
        beam(box_f, box_r, y);                      // tampo da caixa
        beam([mala[0], base_z], mala, y);           // poste da mala
        beam(box_r, mala, y);                       // tampo da mala
    }
}

// Travessas — amarram os dois lados nos vértices principais
module cross_beams() {
    cross(nose);
    cross(box_f);
    cross(box_r);
    cross(mala);
    cross([box_f[0], base_z]);
    cross([box_r[0], base_z]);
}

// ============================================================
// CONECTORES
// ============================================================
// ELBOW encaixado num vértice, DERIVADO das direções das duas
// vigas que saem dele. Nada de ângulo escrito à mão — foi assim
// que a primeira versão saiu com os conectores fora do plano.
//
// A varredura do ELBOW acontece no plano XY; a armação está no
// XZ, então a base é sempre rotate([-90,0,0]). Com isso:
//     porta A aponta (sin θ, 0, cos θ)
//     porta B aponta no ângulo (sweep + θ + 180)
// Logo, para duas direções dadas:
//     θ     = ang(dirA)
//     sweep = ang(dirB) − θ − 180
//
// A porta A também não fica na origem da peça: ela está em
// (c, 0, c) local, o que após as rotações vira
// (c·cos θ, c, −c·sin θ). A origem tem de recuar isso, senão o
// conector flutua ao lado do vértice em vez de encaixar nele.
c_el = 2.5;   // raio das portas do ELBOW (= sec/2)

function ang2(v) = atan2(v[0], v[1]);
function dirv(p, q) = (q - p) / norm(q - p);

module elbow_at(v, y, dirA, dirB) {
    th    = ang2(dirA);
    sweep = ang2(dirB) - th - 180;
    s     = sweep < 0 ? sweep + 360 : sweep;
    // recuo para a porta A cair exatamente no vértice
    off   = [c_el * cos(th), c_el, -c_el * sin(th)];
    translate([v[0], y, v[1]] - off)
        rotate([0, th, 0])
            rotate([-90, 0, 0])
                // FÊMEA nas duas portas: as vigas chegam com pino
                // (`ends="pin"`). Deixar o elbow no default —
                // pino/pino — põe macho contra macho e não encaixa.
                elbow(s, "hole", "hole");
}

// Vértices de DUAS vias. Os de três vias (topo da caixa) ficam
// pendentes: o sistema não tem peça 3-vias em ângulo livre — o
// VERTEX é ortogonal e o ELBOW só faz duas.
module vertex_elbows() {
    for (y = ys) {
        // nariz: base (+X) encontra a rampa — sweep 151.9°
        elbow_at(nose, y, dirv(nose, [LEN, base_z]), dirv(nose, box_f));
        // traseira da mala: tampo encontra o poste — sweep 45°
        elbow_at(mala, y, dirv(mala, box_r), dirv(mala, [mala[0], base_z]));
    }
}

// ============================================================
// MONTAGEM
// ============================================================
// Vigas — laranja rally
color([0.85, 0.45, 0.15]) { side_frames(); cross_beams(); }

// Conectores de inclinação — verde, para destacar onde a
// armação muda de direção
color([0.10, 0.70, 0.45]) vertex_elbows();

// ============================================================
// INFO
// ============================================================
echo("=== ROVER FRAME (só vigas) ===");
echo(str("Comprimento ", LEN, "mm · bitola ", ys[1] - ys[0], "mm · altura ", box_f[1], "mm"));
echo(str("Rampa       ", norm(box_f - nose), "mm a ",
    atan2(box_f[1] - nose[1], box_f[0] - nose[0]), "°"));
echo(str("Caixa       ", box_r[0] - box_f[0], "mm  ·  Mala ", mala[0] - box_r[0], "mm"));
echo(str("Vigas       ", 7 * len(ys), " laterais + 6 travessas"));

if (check_collisions)
    color([1, 0, 0]) intersection() { side_frames(); cross_beams(); }
