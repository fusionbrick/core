# t3-cubo-curvas — lista de peças

Corpo de prova: cubo 10×10×10 de cantos arredondados — dois anéis de vigas + BEND 90° (R = 1,5 célula) e 8 postes

| Qtd | Peça | Configuração | Usada em |
| --- | --- | --- | --- |
| 8 | `brick-6x1x1-43a46b.stl` | brick.scad cells_x=6, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | vb-i, vd-i, vt-i, ve-i, vb-s, vd-s, vt-s, ve-s |
| 8 | `curve-r2-a90-soso.stl` | curve.scad k=1, angle=90, port_a=recess, port_b=recess | cBD-i, cTD-i, cTE-i, cBE-i, cBD-s, cTD-s, cTE-s, cBE-s |
| 8 | `brick-8x1x1-7a067e.stl` | brick.scad cells_x=8, cells_y=1, cells_z=1, axis_x=bored, axis_y=bored, axis_z=bored, face_xn=recess, face_xp=recess, face_yn=recess, face_yp=recess, face_zn=recess, face_zp=recess | poste0, poste1, poste2, poste3, poste4, poste5, poste6, poste7 |
| 32 | `dowel.stl` | pin.scad ends=2 | — |

Total: 56 peças impressas.
