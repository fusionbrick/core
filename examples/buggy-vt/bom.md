# buggy-vt — lista de peças

Buggy off-road 4×4 baseado em imagem: chassi laranja em blocos, gaiola preta de vigas furadas com colunas diagonais, teto bege com faróis, eletrônica como mock

| Qtd | Peça | Configuração | Usada em |
| --- | --- | --- | --- |
| 1 | `brick-22x8x1-7169c4.stl` | brick.scad cells_x=22, cells_y=8, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | piso |
| 2 | `brick-22x2x1-a7ee35.stl` | brick.scad cells_x=22, cells_y=2, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | lateral_e, lateral_d |
| 1 | `brick-6x4x2-bbc69f.stl` | brick.scad cells_x=6, cells_y=4, cells_z=2, axis_x=solid, axis_y=solid, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=pin | traseira |
| 1 | `brick-6x3x2-7c1c30.stl` | brick.scad cells_x=6, cells_y=3, cells_z=2, axis_x=solid, axis_y=solid, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=pin | nariz |
| 1 | `brick-8x2x1-10f2bc.stl` | brick.scad cells_x=8, cells_y=2, cells_z=1, axis_x=solid, axis_y=bored, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | parachoque_f |
| 1 | `brick-6x1x1-28df21.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=solid, axis_y=bored, axis_z=solid, face_xn=plain, face_xp=plain, face_yn=pin, face_yp=recess, face_zn=plain, face_zp=plain | frente_alta |
| 1 | `brick-8x1x1-310787.stl` | brick.scad cells_x=8, cells_y=1, cells_z=1, axis_x=solid, axis_y=bored, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=pin, face_yp=recess, face_zn=recess, face_zp=recess | parachoque_t |
| 2 | `brick-4x1x1-066d89.stl` | brick.scad cells_x=4, cells_y=1, cells_z=1, axis_x=solid, axis_y=bored, axis_z=solid, face_xn=plain, face_xp=plain, face_yn=pin, face_yp=recess, face_zn=plain, face_zp=plain | berco_t, berco_f |
| 6 | `brick-6x1x1-bb40a0.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=pin, face_xp=pin, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | poste_te, poste_td, poste_me, poste_md, trilho_e, trilho_d |
| 3 | `brick-8x1x1-7a067e.stl` | brick.scad cells_x=8, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | travessa_t, travessa_f, painel |
| 2 | `node-2p-f12150.stl` | node.scad dirs=[[-1, 0, 0], [4, 0, -3]], ports=['pin', 'pin'] | no_alto_e, no_alto_d |
| 2 | `node-2p-868738.stl` | node.scad dirs=[[0, 0, -1], [-4, 0, 3]], ports=['pin', 'pin'] | no_baixo_e, no_baixo_d |
| 2 | `strut-9-box.stl` | brick.scad cells_x=9, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored | coluna_a_e, coluna_a_d |
| 1 | `brick-8x8-t4-dfc26e.stl` | brick.scad cells_x=8, cells_y=8, cells_z=1, axis_x=solid, axis_y=solid, axis_z=bored, face_xn=plain, face_xp=plain, face_yn=plain, face_yp=plain, face_zn=recess, face_zp=recess, thickness=4.0 | teto |
| 4 | `wheel-d8-w3-offroad-s8.stl` | wheel.scad wheel_cells=8, width_cells=3, tread=offroad, spokes=8, tread_count=22 | roda_te, roda_td, roda_fe, roda_fd |
| 30 | `dowel.stl` | pin.scad ends=2 | — |
| 4 | `axle-w3.stl` | axle.scad width_cells=3 | — |

Total: 64 peças impressas.

## Componentes — não imprimir

Volumes reservados para componentes reais; entram na checagem de colisão.

| Componente | Medidas (mm) |
| --- | --- |
| bateria 9V | 48.5 × 26.5 × 17.5 |
| ESP32-CAM | 27 × 40 × 4.5 |
| lente | 8 × 8 × 7 |
| LED âmbar ×4 | 5 × 5 × 6 |
| LED branco ×4 | 5 × 5 × 6 |
| farol de teto ×2 | 9 × 9 × 7 |
