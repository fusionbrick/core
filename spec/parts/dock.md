# DOCK

Adapter: torna um dispositivo **não-modular** (motor, sensor, placa, bateria) compatível com o sistema.

É a única peça que hospeda algo de fora. Por dentro é exclusiva do dispositivo; por fora é [BRICK](brick.md) — mesmas células, mesmos eixos, mesmas faces.

Modelo e valores: [constitution.md](../constitution.md) · [params.md](../params.md).

## Contrato da categoria

> **Por dentro o adapter é exclusivo do dispositivo; por fora é sistema puro.**

A premissa *compatibilidade é permanente* proíbe pares exclusivos. Uma cavidade moldada para um motor específico é exclusiva por definição — e é legítima porque a exclusividade fica **contida na cavidade**. A superfície externa continua BRICK.

Consequência: trocar o dispositivo troca só o **perfil**. Tudo que estava conectado continua conectando.

| Camada | Responsabilidade | Varia por dispositivo? |
| --- | --- | --- |
| Células | ancoram os furos | não — é o grid |
| Pele | parede fora do volume de grid | espessura, sim |
| Cavidade | volume negativo do dispositivo | **sim** — é o perfil |
| Saída | por onde eixo/conector/fio sai | posição sim, formato não |

## Lei de centragem

> **O eixo do dispositivo coincide com o centro de uma célula.**

É isso que faz a ponta do eixo cair num furo padrão — e portanto receber engrenagem, polia ou acoplador com a mesma interface de qualquer outra peça.

## Envelope mínimo

Cada eixo é dimensionado **separadamente**: o mínimo é o que a cavidade exige, nada além. Dispositivo de seção não-circular usa pele diferente em cada eixo, o que evita o envelope cúbico desperdiçado.

Para meia-seção `s`:

```text
skin ≥ s + device_clearance + wall − (cells · grid)/2      (nunca negativo)
```

Arredondado para cima na escala fina (`2.5mm`).

### `motor-130` — envelope no grid de 8mm

| Eixo | Cavidade | Células | Pele | Total |
| --- | --- | --- | --- | --- |
| X (redondo) | `20.1` | 2 | `5.0` | **26mm** |
| Y (chanfros) | `15.1` | 2 | `2.5` | **21mm** |
| Z (comprimento) | `25.0` | 3 | `2.5` | **29mm** |

`26 × 21 × 29mm`. Mais células reduzem a pele mas aumentam o total — o ótimo é por eixo, não global.

## Perfis de dispositivo

O perfil é **desacoplado da peça**: descreve só o dispositivo, nunca o dock.

| Campo | Descrição |
| --- | --- |
| `can_d` | diâmetro do corpo (eixo redondo) |
| `can_flat` | distância entre achatamentos (`= can_d` se cilíndrico) |
| `can_len` | comprimento do corpo, sem eixo |
| `boss_d` / `boss_h` | ressalto frontal em volta do eixo |
| `shaft_d` / `shaft_len` | eixo de saída |

### `motor-130` — motor DC do "motor amarelo" (TT), sem redutor

| Campo | Valor |
| --- | --- |
| `can_d` | `20.1mm` |
| `can_flat` | `15.1mm` |
| `can_len` | `25.0mm` |
| `boss_d` / `boss_h` | `6.15 / 1.7mm` |
| `shaft_d` / `shaft_len` | `2.0 / 9.0mm` |

> ⚠️ **Valores de datasheet, não medidos.** Lote comercial varia. Confirmar com paquímetro — especialmente `can_d` (a costura da carcaça engorda um lado) e a distância entre achatamentos.

Os achatamentos travam o **torque de reação**: fricção no cilindro não impede o motor de girar dentro do dock sob carga.

Este perfil é o motor **nu** — carcaça e trem de redução ficam de fora.

## Divisão e montagem

O dispositivo não entra num volume fechado. O dock parte **no plano do eixo** — é o único plano onde a abertura tem a maior seção do corpo.

As metades se unem por [PIN](pin.md) nos furos passantes, com rebaixo também na face de corte.

**Consequência inevitável:** o furo de saída é coaxial com o eixo, então qualquer plano que deixe o dispositivo entrar **corta esse furo ao meio**. Encaixar dentro dele empurra as metades para fora. Alternativas: PINs nas células vizinhas resistindo ao esforço, cola, ou acoplar no eixo do dispositivo em vez de no furo.

## Parâmetros

| Parâmetro | Padrão | Descrição |
| --- | --- | --- |
| `device` | `motor-130` | perfil do dispositivo |
| `cells_x/y/z` | por dispositivo | volume de grid |
| `skin_x/y/z` | derivado do perfil | pele fora do grid |
| `axis_cell_x/y` | `0 / 0` | célula em que o eixo está centrado |
| `device_clearance` | `0.2mm` | folga radial da cavidade — **local**, não é a `tolerance` do sistema |
| `split` | `none` | `none` / `a` / `b` — metade a exportar |

`device_clearance` é separado da `tolerance` de propósito: a folga do sistema é press-fit entre peças impressas, com dispersão conhecida. Dispositivo comercial tem dispersão de lote própria.

## Verificações

- Eixo do dispositivo em centro de célula
- Parede efetiva ≥ `wall` em cada eixo
- Pele múltipla da escala fina
- Eixo de saída cabe no furo padrão
