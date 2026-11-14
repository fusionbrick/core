// ============================================================
// NODE — Design System 3D Modular
// ============================================================
// A única peça que sai do ortogonal. Une N portas em ângulos
// arbitrários.
//
// NÃO absorve as uniões a 90°, 180° e 3-vias ortogonais: essas
// já são BRICK com faces "pin", porque as portas de uma união
// ortogonal caem exatamente nos centros de face da célula.
//
//          ╲   │
//           ╲  │      cubo central + um braço por porta,
//            ╲ │      com concordância (fillet) entre eles
//         ────●────
//
// DECLARADO POR DIREÇÕES, NÃO POR ÂNGULO
//
// Com três ou mais portas não existe "o ângulo" — existem
// vários. E escrever ângulo à mão é a origem de erro de
// orientação mais comum: derivar do vetor elimina a classe.
//
// O FILLET devolve o que a curva por varredura dava: quina
// externa arredondada e canal sem dobra seca. Com dois braços
// a 90° e fillet, o NODE reproduz o antigo ELBOW.
//
// spec: spec/parts/node.md
// ============================================================

// Primitivos e derivados: fonte única, não redeclarar aqui.
include <params.scad>

/* [Portas] */
// Direções, uma por porta. Duas fazem curva; três ou mais, nó.
// O ângulo entre elas é CONSEQUÊNCIA.
dirs = [[1,0,0], [0,0,1]];

// Acabamento por porta: recess | pin | plain
ports = ["recess", "recess"];

/* [Canto de laje] */
// Ângulo INTERNO entre duas lajes. 0 = usa `dirs` cru.
//
// Laje fina não tem furo de BORDA — ele exige hole_d + 2·wall =
// 7.2mm e a laje tem 4 ou 2. Então virar uma quina só é possível
// por DENTRO, encaixando na FACE de cada laje. Não é contorno:
// é a única interface que uma laje fina tem.
//
// A porta cai no primeiro furo, a grid/2 da quina. Daí sai o
// comprimento do braço:
//
//     arm_len = (grid/2) · tan(θ/2)
//
// θ=90° dá exatamente grid/2 — por isso o BRICK com preset
// `corner_90` já resolve a quina reta, e não por coincidência.
//
// A aresta do braço encosta exatamente na quina em QUALQUER
// ângulo, porque a seção é `grid` e a porta está a `grid/2`.
corner_angle = 0; // [0:1:170]

// Em qual furo de cada laje a porta encaixa. -1 = automático:
// escolhe o MENOR índice que fecha a geometria.
//
// É o parâmetro que destrava o ângulo agudo. A porta fica a
// d = grid/2 + k·grid do vértice, e o braço vale d·tan(θ/2) —
// então afastar a porta ALONGA o braço e abre espaço para o
// corpo. Com k=0 e θ<90° o braço fica curto demais e o hub
// invadiria a laje; com k=1 ou 2 ele cabe.
hole_index = -1; // [-1:1:4]

/* [Forma] */
// Raio de concordância entre os braços
fillet = 2; // [0:0.25:8]

// Comprimento do braço, do centro à porta. 0 = derivado (grid/2)
arm_len = 0; // [0:0.5:40]

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

sec = grid;                                   // seção do braço

// --- Modo canto ---------------------------------------------
// Bissetor em +X, aresta da quina ao longo de Y. Os braços
// apontam do hub PARA as lajes, ou seja ao longo das normais
// internas invertidas.
is_corner   = corner_angle > 0;
ch          = corner_angle / 2;
// Raio do hub — é ele que precisa caber entre as duas lajes
hub_r = fillet > 0 ? (sec / 2 + 2 * fillet) / 2 : sec / 2 * sqrt(2) / 2;

// Distância da porta ao vértice para um dado índice de furo
function port_dist(k) = grid / 2 + k * grid;
function arm_for(k, hh) = port_dist(k) * tan(hh);

// Folga entre o braço e a LAJE OPOSTA. Acima de 90° o mínimo
// está na ponta do braço; abaixo, na base.
function corner_slack(k, th) =
    th >= 90 ? sin(th) * (port_dist(k) - grid/2)
             : arm_for(k, th/2) - (grid/2) * sin(th);

// Menor índice que fecha: braço não invade a laje oposta E o hub
// cabe entre as duas.
function auto_k(th, i = 0) =
    i > 6 ? 6
  : (corner_slack(i, th) >= -1e-6 && arm_for(i, th/2) >= hub_r - 1e-6) ? i
  : auto_k(th, i + 1);

corner_k   = !is_corner ? 0
           : (hole_index >= 0 ? hole_index : auto_k(corner_angle));
corner_arm = arm_for(corner_k, ch);
corner_dirs = [ [-sin(ch),  cos(ch), 0],
                [-sin(ch), -cos(ch), 0] ];

// Ângulo ENTRE OS BRAÇOS é o suplemento do ângulo entre lajes:
// θ=90 → 90, θ=120 → 60.

eff_dirs = is_corner ? corner_dirs : dirs;
eff_alen = is_corner ? corner_arm : (arm_len > 0 ? arm_len : grid / 2);

alen = eff_alen;
n    = len(eff_dirs);

function unit(v) = v / norm(v);
function ang_between(a, b) = acos(max(-1, min(1, unit(a) * unit(b))));

// Menor ângulo entre braços — o fillet precisa caber nele
min_ang = n < 2 ? 180 :
    min([ for (i = [0 : n-2], j = [i+1 : n-1]) ang_between(eff_dirs[i], eff_dirs[j]) ]);

// Uma porta é ortogonal se aponta ao longo de um eixo do grid
function is_ortho(v) = let (u = unit(v))
    (abs(abs(u[0]) - 1) < 1e-6) || (abs(abs(u[1]) - 1) < 1e-6) || (abs(abs(u[2]) - 1) < 1e-6);
all_ortho = [ for (d = eff_dirs) if (!is_ortho(d)) 1 ] == [];

// ============================================================
// VALIDAÇÃO
// ============================================================
assert(n >= 2, "NODE precisa de pelo menos duas portas");
assert(len(ports) == n, "uma entrada de `ports` por direção em `dirs`");
assert(min_ang > 1, "duas portas apontam na mesma direção");
// Quem invade a laje num canto agudo é o HUB, e o raio dele
// depende do `fillet` — daí o limite ser função dele, não o
// `pin_len + wall` fixo que estava aqui antes. Com fillet menor
// o hub encolhe e ângulos mais fechados passam a caber.
assert(alen >= pin_len + wall, "braço curto demais para a porta e a parede");
assert(!is_corner || alen >= hub_r,
       str("canto agudo demais: θ=", corner_angle, "° dá braço ", alen,
           "mm e o hub tem raio ", hub_r,
           " — ele invadiria a laje. Reduza `fillet` ou abra o ângulo."));
assert(!is_corner || len(ports) == 2, "modo canto usa exatamente duas portas");
assert(fillet * 2 <= sec, "fillet maior que a seção do braço");

// ============================================================
// MÓDULOS
// ============================================================

// Orienta os filhos com +Z ao longo de `d`. A rotação sai do
// VETOR, nunca escrita à mão.
// O eixo tem de sair de +Z × u, NÃO de [u.y, -u.x, 0].
//
// A versão anterior dava o MESMO eixo para +X e -X (nos dois
// casos [0,1,0]), e como acos() só devolve 0..180° o sinal se
// perdia: `along([-1,0,0])` mandava o braço para +X. Errava
// toda direção com componente negativa, em silêncio.
module along(d) {
    u  = unit(d);
    ax = cross([0, 0, 1], u);
    a  = acos(max(-1, min(1, u[2])));
    if (norm(ax) < 1e-9)                       // u paralelo a Z
        if (u[2] > 0) children();
        else rotate([180, 0, 0]) children();
    else rotate(a = a, v = ax) children();
}

// Seção QUADRADA de lado `sec`, alinhada aos eixos.
//
// Era `cylinder(d = sec, $fn = 4)`, que inscreve o quadrado no
// diâmetro: o lado saía sec/√2 = 5.66, não 8, e ainda girado 45°
// (losango). Com o lado valendo `sec` de verdade, a aresta do
// braço encosta exatamente na quina — a porta fica a grid/2 dela
// e a meia-seção vale grid/2.
module arm(a) {
    translate([0, 0, a / 2]) cube([sec, sec, a], center = true);
}

// Argumentos com default no global: `use <node.scad>` importa só
// o módulo, então SEM eles um assembly ficaria preso ao NODE
// default e não conseguiria instanciar dois ângulos diferentes.
module node(dirs = eff_dirs, ports = ports, arm_len = eff_alen) {
    pk = [ for (k = ports) fb_kind(k) ];   // aceita também stud / socket / flat
    nn = len(dirs);
    a  = arm_len;
    difference() {
        union() {
            // CANTO: o corpo é o FECHO CONVEXO dos braços, não um
            // hub separado. A esfera sobrava para fora e a peça
            // lia como dois blocos colados; o hull dá um sólido
            // único e alinhado — um elbow de verdade.
            //
            // E é seguro por construção: os braços terminam NA
            // face de cada laje, todos do lado interno; o fecho
            // convexo de conjuntos de um mesmo lado de um plano
            // não atravessa esse plano.
            if (is_corner) hull() for (i = [0 : nn-1]) along(dirs[i]) arm(a);
            else {
                // Hub — a esfera dá a concordância entre os braços
                if (fillet > 0) sphere(d = sec / 2 + 2 * fillet);
                else cube(sec, center = true);
                for (i = [0 : nn-1]) along(dirs[i]) arm(a);
            }
            for (i = [0 : nn-1]) if (pk[i] == "pin")
                along(dirs[i]) translate([0, 0, a]) fb_male();
        }
        for (i = [0 : nn-1]) if (pk[i] == "recess")
            along(dirs[i]) translate([0, 0, a]) fb_female(bore = a);
    }
}

// Comprimento do braço para um canto de θ graus. Exposto para o
// assembly calcular sem repetir a fórmula.
function corner_arm_len(theta) = (grid / 2) * tan(theta / 2);

// ============================================================
// RENDER
// ============================================================
part_color = [0.10, 0.70, 0.45];
color(part_color) node();

// ============================================================
// INFO
// ============================================================
echo("=== NODE ===");
echo(str("Portas      ", n, " | direções ", dirs));
echo(str("Acabamento  ", ports));
echo(str("Braço       ", alen, "mm | seção ", sec, " | fillet ", fillet));
echo(str("Menor ângulo entre braços: ", min_ang, "°"));
echo("---");
echo(str("Todas as portas ortogonais? ", all_ortho ? "SIM" : "não"));
if (all_ortho)
    echo("AVISO: união totalmente ortogonal — use BRICK com faces 'pin', é mais simples");
echo(str("Volta ao grid?  ", all_ortho ? "sim"
    : "só em ângulo de terno pitagórico (3-4-5 = 53.13°); a 45° a diagonal vale grid·√2"));

// --- Modo canto ---------------------------------------------
if (is_corner) {
    echo(str("CANTO       θ interno ", corner_angle, "° | furo #", corner_k,
             " (a ", port_dist(corner_k), "mm do vértice) | braço ",
             corner_arm, "mm | entre braços ", min_ang, "°"));
    echo(str("            folga braço↔laje oposta: ",
             corner_slack(corner_k, corner_angle), "mm",
             hole_index >= 0 ? "  (furo forçado)" : "  (furo automático)"));
    // O canto encaixa na FACE da laje, que é fêmea — logo a porta
    // tem de ser macho. Aviso, não erro: pode haver uso legítimo.
    if (fb_kind(ports[0]) != "pin" || fb_kind(ports[1]) != "pin")
        echo(str("AVISO canto: portas ", ports, " — a face da laje é",
                 " fêmea, o canto precisa de ports=[\"pin\",\"pin\"]"));
    // Acima de uma célula as lajes já estão quase coplanares e
    // uma emenda deitada sobre as duas faces é mais curta e mais
    // rígida que um braço longo em balanço.
    if (corner_arm > grid)
        echo(str("AVISO canto: braço ", corner_arm, "mm > 1 célula (", grid,
                 ") — considere LAJE DE EMENDA sobre as duas faces"));
}
