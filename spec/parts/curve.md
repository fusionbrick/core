# CURVE — curva

**Intenção.** Virar uma esquina com arco contínuo, sem o cotovelo quadrado do nó: anéis de canto arredondado, pórticos, grampos de retorno, gaiolas. Implementação: `impl/openscad/curve.scad`. Compilador: tipo `curve` em `spec/assembly.md` (antes `bend`, que continua aceito).

## Geometria

- Seção `grid × grid`, arestas com `edge_r` (acabamento).
- Raio da linha de centro **MUST** ser `R = (k + ½)·grid`, `k ≥ 0`.
- Ângulo **MUST** ser 90° ou 180°.

**Por quê.** A entrada fica num centro de face: fronteira de célula na direção de avanço, centro de célula na direção da curva. Depois de 90° os papéis se trocam, e a saída só cai num centro de face se `R` for meia célula ímpar. A 180° a saída volta a `2R = (2k+1)·grid` da entrada, também no grid. Qualquer outro ângulo sai do grid — para isso existe a diagonal (`strut`).

Na IR de montagem o tamanho se escreve como `radius`: quantas células a curva ocupa de lado. No OpenSCAD o parâmetro é `k = radius − 1`.

| `radius` (IR) | `k` (OpenSCAD) | R (mm) | ocupa (90°) | uso |
| --- | --- | --- | --- | --- |
| 1 | 0 | 4 | 1×1 | cotovelo compacto (raio interno 0 — canto vivo por dentro) |
| 2 | 1 | 12 | 2×2 | curva padrão de anel e pórtico |
| 3 | 2 | 20 | 3×3 | curva aberta |

## Portas

- Pontas: `socket` (padrão), `stud` ou `flat` — no OpenSCAD, `port_a` / `port_b` = `recess`, `pin`, `plain` (as duas formas valem). Furo da porta com profundidade `grid/2 + pin_len`.
- Furos transversais (eixo da curva) a cada ~1 célula de arco. São **visuais**: fora do eixo de simetria não caem no grid.

## Restrições conhecidas

- Sem portas laterais utilizáveis: uma curva só liga pelas pontas.
- O miolo da curva é livre, mas nada do grid encaixa nele.
