// RASCUNHO — perfil lateral, SÓ VIGAS
use <../../impl/openscad/pin.scad>

// x: 0 = FRENTE (onde a rampa desce) · x cresce para a traseira
// Proporções tiradas do desenho: rampa ~63%, caixa ~18%, mala ~19%
nose  = [  2.5,  2.5];   // ponta dianteira
box_f = [ 77.5, 42.5];   // topo do poste dianteiro da caixa
box_r = [ 97.5, 42.5];   // topo do poste traseiro da caixa
mala  = [117.5, 22.5];   // topo da mala (mais baixa)
base_z = 2.5;
LEN = 120;               // 6 células
ys = [-2.5, 62.5];

// Viga entre DOIS PONTOS. A rotação sai do vetor, não do meu
// palpite: +Y --Rx(90)--> +Z --Ry(θ)--> (sinθ, 0, cosθ),
// então θ = atan2(dx, dz).
module beam(a, b, y) {
    d   = b - a;
    len = norm(d);
    translate([a[0], y, a[1]])
        rotate([0, atan2(d[0], d[1]), 0])
            rotate([90, 0, 0])
                pin(top="none", bottom="none", sides="none", ends="pin", len=len);
}

color([0.15,0.15,0.15]) for (y = ys) {
    beam([0, base_z], [LEN, base_z], y);        // base corrida
    beam(box_f, nose, y);                        // rampa
    beam([box_f[0], base_z], box_f, y);          // poste dianteiro
    beam([box_r[0], base_z], box_r, y);          // poste traseiro
    beam(box_f, box_r, y);                       // tampo da caixa
    beam([mala[0], base_z], mala, y);            // poste traseiro da mala
    beam(box_r, mala, y);                        // tampo da mala
}
color([0.9,0.35,0.1]) for (y = ys) for (p = [nose, box_f, box_r, mala])
    translate([p[0], y, p[1]]) sphere(d=5);

ramp = norm(box_f - nose);
echo(str("rampa ", ramp, "mm a ", atan2(box_f[1]-nose[1], box_f[0]-nose[0]), "°"));
echo(str("comprimento total ", LEN, "mm | caixa ", box_r[0]-box_f[0], " | mala ", mala[0]-box_r[0]));
