# WHEEL · AXLE

Roda e eixo. A roda **gira**; o eixo prende na peça como qualquer macho.

Modelo e valores: [constitution.md](../constitution.md) · montagem: [assembly.md](../assembly.md) (ASM-010).

## Por que duas peças

Toda junção do sistema é press-fit: prende. Uma roda precisa do contrário, um mancal que solta. Fazer a roda girar direto num furo de BRICK exigiria um furo de outro diâmetro, e a premissa *compatibilidade é permanente* proíbe uma interface nova.

A saída é separar as duas funções:

| | Encaixe | Folga |
| --- | --- | --- |
| **AXLE** na peça | colar `collar_d` no rebaixo + haste até `pin_len` — **idêntico a um PIN** | `tolerance` (prende) |
| **WHEEL** no AXLE | furo `collar_d + run_clear` sobre o mancal `Ø collar_d` | `run_clear = 2·tolerance` (gira) |

O eixo entra em qualquer porta `recess` de qualquer BRICK. Nenhuma peça ganhou furo especial.

## AXLE

Da face da peça para fora:

| Trecho | Extensão | Diâmetro |
| --- | --- | --- |
| Haste | `−pin_len` … `−collar_depth` | `pin_d` |
| Colar | `−collar_depth` … `0` | `collar_d` |
| Mancal | `0` … `grid − collar_depth` | `collar_d` |
| Flange | `grid − collar_depth` … `grid` | `recess_d + 2·wall` |

Imprimir em pé, com o flange na mesa.

## WHEEL

| | Valor |
| --- | --- |
| Diâmetro | `wheel_cells · grid` (padrão 4 → 32mm) |
| Largura | `width_cells · grid` — células inteiras ao longo do eixo, fora da peça (Lei do Grid). O AXLE acompanha (`width_cells`) |
| Pneu | espessura `max(2·wall + collar_depth, 0.14·diâmetro)`; `tread = street` (sulco transversal) ou `offroad` (gomos alternados + sulco central) |
| Aro | `spokes = 0`: alma com furos de alívio · `spokes > 0`: anel + raios retos |
| Furo | `collar_d + run_clear` = 5.0mm |
| Rebaixo do flange | `flange_d + run_clear` × `collar_depth + tolerance` (folga axial) |
| Pneu | recua `gap` da face interna: só o cubo encosta na peça e a banda não roça |

Imprimir com a face **externa** na mesa: cubo e pneu apoiam no mesmo plano.

## Verificações

- O eixo exige porta `recess` (ASM-010)
- A roda não invade nenhuma peça nem outra roda (ASM-002, por cilindro)
- O eixo conta como macho para o furo compartilhado (ASM-006)
- `run_clear` nunca calibrado contra impressão real, assim como `tolerance` (T041)
