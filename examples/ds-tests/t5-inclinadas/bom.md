# t5-inclinadas — lista de peças

Corpo de prova: vigas inclinadas por ternos pitagóricos (3-4-5, 5-12-13, 6-8-10 no plano, 2-3-6 em 3D) e vigas dobradas por BEND (S e grampo 180°)

| Qtd | Peça | Configuração | Usada em |
| --- | --- | --- | --- |
| 2 | `brick-24x1x1-16b900.stl` | brick.scad cells_x=24, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | long0, long1 |
| 4 | `brick-9x1x1-b197c4.stl` | brick.scad cells_x=9, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | trav0, trav1, trav2, trav3 |
| 3 | `brick-1x1x1-a5072e.stl` | brick.scad cells_x=1, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | r-pe, s-pe, S-topo |
| 1 | `node-2p-3bc5ca.stl` | node.scad dirs=[[-1, 0, 0], [4, 0, 3]], ports=['pin', 'pin'] | r0 |
| 1 | `node-2p-a3bc8d.stl` | node.scad dirs=[[-4, 0, -3], [1, 0, 0]], ports=['pin', 'pin'] | r1 |
| 1 | `strut-4.stl` | brick.scad cells_x=4, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | r-diag |
| 2 | `brick-4x1x1-1dceef.stl` | brick.scad cells_x=4, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | r-poste, d-teto |
| 1 | `node-2p-4a3e9d.stl` | node.scad dirs=[[-1, 0, 0], [12, 0, 5]], ports=['pin', 'pin'] | s0 |
| 1 | `node-2p-7d0325.stl` | node.scad dirs=[[-12, 0, -5], [1, 0, 0]], ports=['pin', 'pin'] | s1 |
| 1 | `strut-12.stl` | brick.scad cells_x=12, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | s-diag |
| 5 | `brick-6x1x1-43a46b.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | s-poste, d-apoio0, d-apoio1, S-alto, S-poste2 |
| 1 | `node-2p-3220b2.stl` | node.scad dirs=[[0, -1, 0], [6, 8, 0]], ports=['pin', 'pin'] | p0 |
| 1 | `node-2p-5f1aa2.stl` | node.scad dirs=[[-6, -8, 0], [0, 1, 0]], ports=['pin', 'pin'] | p1 |
| 1 | `strut-9.stl` | brick.scad cells_x=9, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | p-diag |
| 1 | `node-2p-9b88d0.stl` | node.scad dirs=[[0, 0, -1], [2, 3, 6]], ports=['pin', 'pin'] | d0 |
| 1 | `node-2p-ee94e8.stl` | node.scad dirs=[[-2, -3, -6], [0, 0, 1]], ports=['pin', 'pin'] | d1 |
| 1 | `strut-6.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, round_axis=y, corner_r=4.0 | d-diag |
| 1 | `brick-7x1x1-fb3791.stl` | brick.scad cells_x=7, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | d-poste |
| 2 | `brick-2x1x1-583f63.stl` | brick.scad cells_x=2, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | S-poste, S-meio |
| 2 | `curve-r2-a90-soso.stl` | curve.scad k=1, angle=90, port_a=recess, port_b=recess | S-c1, S-c2 |
| 2 | `brick-5x1x1-664640.stl` | brick.scad cells_x=5, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | U-a, U-b |
| 1 | `curve-r2-a180-soso.stl` | curve.scad k=1, angle=180, port_a=recess, port_b=recess | U-c |
| 31 | `dowel.stl` | pin.scad ends=2 | — |

Total: 67 peças impressas.
