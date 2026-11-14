# rover-x6 — lista de peças

Rover de exploração 6×6: base de blocos grandes, carroceria aberta de vigas e curvas que afunila para cima, mastro com cabeça de câmeras, braço robótico, antena, rodas off-road; grafite, branco e laranja

| Qtd | Peça | Configuração | Usada em |
| --- | --- | --- | --- |
| 2 | `brick-12x1x1-18a051.stl` | brick.scad cells_x=12, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=z, corner_r=4.0, pin_cells=inner, face_xn=plain, face_xp=recess, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | lat0a_e, lat0a_d |
| 2 | `brick-24x1x1-6e31a9.stl` | brick.scad cells_x=24, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=z, corner_r=4.0, pin_cells=inner, face_xn=plain, face_xp=recess, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | lat0b_e, lat0b_d |
| 2 | `brick-24x1x1-d30a11.stl` | brick.scad cells_x=24, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=plain, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | lat1a_e, lat1a_d |
| 2 | `brick-12x1x1-d97ae6.stl` | brick.scad cells_x=12, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=plain, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | lat1b_e, lat1b_d |
| 3 | `brick-12x12x2-759ccc.stl` | brick.scad cells_x=12, cells_y=12, cells_z=2, axis_x=bored, axis_y=solid, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=pin, face_yp=pin, face_zn=recess, face_zp=recess | bloco0, bloco1, bloco2 |
| 16 | `curve-r2-a90-soso.stl` | curve.scad k=1, angle=90, port_a=recess, port_b=recess | bico_f_e, bico_t_e, bico_f_d, bico_t_d, q_inf-cSE, q_inf-cNE, q_inf-cNO, q_inf-cSO, q_sup-cSE, q_sup-cNE, q_sup-cNO, q_sup-cSO, arco0-ce, arco0-cd, arco1-ce, arco1-cd |
| 2 | `brick-10x1x1-cec150.stl` | brick.scad cells_x=10, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | bico_f, bico_t |
| 2 | `brick-2x2x1-bb1015.stl` | brick.scad cells_x=2, cells_y=2, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | ombro_e, ombro_d |
| 2 | `brick-7x1x1-24a293.stl` | brick.scad cells_x=7, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | coluna_e, coluna_d |
| 4 | `brick-13x1x1-a7759f.stl` | brick.scad cells_x=13, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | bogie_t_e, bogie_f_e, bogie_t_d, bogie_f_d |
| 4 | `brick-2x1x1-583f63.stl` | brick.scad cells_x=2, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | cubo_t_e, cubo_f_e, cubo_t_d, cubo_f_d |
| 2 | `node-2p-20fa6d.stl` | node.scad dirs=[[1, 0, 0], [-12, 0, -5]], ports=['pin', 'pin'] | perna_t_e-n0, perna_t_d-n0 |
| 2 | `node-2p-fe1f61.stl` | node.scad dirs=[[12, 0, 5], [-1, 0, 0]], ports=['pin', 'pin'] | perna_t_e-n1, perna_t_d-n1 |
| 4 | `strut-12.stl` | brick.scad cells_x=12, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | perna_t_e-v, perna_f_e-v, perna_t_d-v, perna_f_d-v |
| 2 | `node-2p-6e7589.stl` | node.scad dirs=[[-1, 0, 0], [12, 0, -5]], ports=['pin', 'pin'] | perna_f_e-n0, perna_f_d-n0 |
| 2 | `node-2p-5731b9.stl` | node.scad dirs=[[-12, 0, 5], [1, 0, 0]], ports=['pin', 'pin'] | perna_f_e-n1, perna_f_d-n1 |
| 6 | `wheel-d11-w4-offroad-s6-y.stl` | wheel.scad wheel_cells=11, width_cells=4, tread=offroad, spokes=6, tread_count=30, spoke_style=y | roda_t_e, roda_m_e, roda_f_e, roda_t_d, roda_m_d, roda_f_d |
| 4 | `brick-14x9x1-1b45c9.stl` | brick.scad cells_x=14, cells_y=9, cells_z=1, axis_x=solid, axis_y=solid, axis_z=bored, round_axis=z, corner_r=4.0, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=pin | deck0, deck1, deck2, deck3 |
| 4 | `brick-16x1x1-352205.stl` | brick.scad cells_x=16, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=z, corner_r=4.0, pin_cells=inner, face_xn=plain, face_xp=recess, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | q_inf-s0, q_inf-s1, q_inf-n0, q_inf-n1 |
| 2 | `brick-10x1x1-e18b63.stl` | brick.scad cells_x=10, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=x, corner_r=4.0, pin_cells=inner, face_xn=recess, face_xp=recess, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | q_inf-l, q_inf-o |
| 12 | `brick-4x1x1-6a9b56.stl` | brick.scad cells_x=4, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | poste_x8_y2, poste_x8_y11, poste_x13_y2, poste_x13_y11, poste_x22_y2, poste_x22_y11, poste_x25_y2, poste_x25_y11, pendural_x13_y3, pendural_x13_y10, pendural_x23_y3, pendural_x23_y10 |
| 4 | `brick-9x1x1-25b780.stl` | brick.scad cells_x=9, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=plain, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | q_sup-s0, q_sup-s1, q_sup-n0, q_sup-n1 |
| 4 | `brick-6x1x1-eb2c0b.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=x, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | q_sup-l, q_sup-o, arco0-tr, arco1-tr |
| 4 | `brick-2x1x1-885acc.stl` | brick.scad cells_x=2, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | arco0-pe, arco0-pd, arco1-pe, arco1-pd |
| 1 | `brick-4x4x1-89473a.stl` | brick.scad cells_x=4, cells_y=4, cells_z=1, axis_x=solid, axis_y=solid, axis_z=bored, round_axis=z, corner_r=4.0, pin_cells=inner, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=pin | pe_mastro |
| 1 | `brick-10x2x2-8262e2.stl` | brick.scad cells_x=10, cells_y=2, cells_z=2, axis_x=bored, axis_y=solid, axis_z=solid, round_axis=x, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=plain, face_yp=plain, face_zn=plain, face_zp=plain | mastro |
| 1 | `brick-8x3x2-545bd2.stl` | brick.scad cells_x=8, cells_y=3, cells_z=2, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | cabeca |
| 1 | `brick-2x2x1-af9853.stl` | brick.scad cells_x=2, cells_y=2, cells_z=1, axis_x=bored, axis_y=solid, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=recess | braco_base |
| 1 | `node-2p-3bc5ca.stl` | node.scad dirs=[[-1, 0, 0], [4, 0, 3]], ports=['pin', 'pin'] | braco-n0 |
| 1 | `node-2p-a3bc8d.stl` | node.scad dirs=[[-4, 0, -3], [1, 0, 0]], ports=['pin', 'pin'] | braco-n1 |
| 1 | `strut-4.stl` | brick.scad cells_x=4, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | braco-v |
| 1 | `brick-1x1x1-a5072e.stl` | brick.scad cells_x=1, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | punho |
| 1 | `brick-11x8x1-5984b2.stl` | brick.scad cells_x=11, cells_y=8, cells_z=1, axis_x=solid, axis_y=solid, axis_z=bored, round_axis=z, corner_r=4.0, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=recess | bandeja |
| 1 | `brick-10x7-t4-8a24f0.stl` | brick.scad cells_x=10, cells_y=7, cells_z=1, axis_x=solid, axis_y=solid, axis_z=bored, round_axis=z, corner_r=4.0, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=pin, thickness=4.0 | base_pi |
| 1 | `brick-5x2x1-2b8fa2.stl` | brick.scad cells_x=5, cells_y=2, cells_z=1, axis_x=bored, axis_y=bored, axis_z=solid, round_axis=z, corner_r=4.0, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=plain, face_zp=plain | antena_haste |
| 86 | `dowel.stl` | pin.scad ends=2 | — |
| 6 | `axle-w4.stl` | axle.scad width_cells=4 | — |

Total: 196 peças impressas.

## Componentes — não imprimir

Volumes reservados para componentes reais; entram na checagem de colisão.

| Componente | Medidas (mm) |
| --- | --- |
| Raspberry Pi 4 | 85 × 56 × 17 |
| bateria 2S | 67 × 42 × 28 |
| bateria (terminal) | 10 × 42 × 28 |
| câmera estéreo E | 14 × 14 × 6 |
| câmera estéreo D | 14 × 14 × 6 |
| LiDAR LD06 | 38.6 × 38.6 × 33.5 |
| antena de alto ganho | 48 × 48 × 5 |
| hazcam ×2 | 6 × 6 × 5 |
| garra | 10 × 6 × 6 |
| fio ×2 | 2.2 × 2.2 × 2.2 |
| motor N20 ×6 | 12 × 34 × 10 |
| fio ×6 | 2 × 2 × 2 |
| driver de motor | 40 × 30 × 12 |
| fio | 2.4 × 2.4 × 2.4 |
| farol ×2 | 6 × 6 × 3 |
| letreiro X6 | 9 × 0 × 0.6 |
