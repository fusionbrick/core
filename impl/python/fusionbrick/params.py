"""
Primitivos e derivados do FusionBrick — Python puro.

Espelha spec/constitution.md e spec/params.md. Sem dependência de
CAD nenhum: é o que permite testar a LEI do sistema fora do Fusion
e fora do OpenSCAD.

A regra central: o grid é DERIVADO, não declarado.

    grid = furo + 2 × (parede + colar)

Declarar o grid permitiria pedir um que não fecha com o próprio
furo. Por isso ele não é parâmetro em lugar nenhum do sistema.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Primitives:
    """Os seis valores dos quais toda cota do sistema deriva."""

    hole_d: float = 4.0        # furo passante — a interface mecânica
    wall: float = 1.6          # parede interna mínima (4 perímetros de 0.4)
    collar_w: float = 0.4      # degrau RADIAL entre furo e rebaixo
    collar_depth: float = 1.0  # profundidade AXIAL do rebaixo
    tolerance: float = 0.2     # folga de press-fit, sempre do MACHO
    gap: float = 0.5           # folga real mínima entre dois machos

    # Protrusão do macho. DECLARADA, não derivada: o limite é a
    # colisão com o macho perpendicular, e essa aproximação é
    # DIAGONAL. Descontar `gap` do eixo cobrava √2 a mais.
    pin_len: float = 2.0

    # --- derivados -----------------------------------------------
    @property
    def grid(self) -> float:
        return self.hole_d + 2 * (self.wall + self.collar_w)

    @property
    def recess_d(self) -> float:
        return self.hole_d + 2 * self.collar_w

    @property
    def pin_d(self) -> float:
        return self.hole_d - self.tolerance

    @property
    def collar_d(self) -> float:
        return self.recess_d - self.tolerance

    @property
    def inset(self) -> float:
        """Do canto da célula ao centro do furo."""
        return self.grid / 2

    @property
    def pin_len_max(self) -> float:
        """
        Teto do macho: a haste tem raio pin_d/2 e parte da face, a
        grid/2 do centro. Dois machos perpendiculares se tocam
        quando pin_len alcança essa diferença.
        """
        return self.grid / 2 - self.pin_d / 2

    @property
    def edge_bore_min(self) -> float:
        """Espessura mínima para caber um furo de BORDA."""
        return self.hole_d + 2 * self.wall

    # --- invariantes ---------------------------------------------
    @property
    def corner_sliver(self) -> float:
        """Material na quina da célula. Vale exatamente `wall`."""
        return self.inset - self.recess_d / 2

    @property
    def web_between_holes(self) -> float:
        """Material entre dois rebaixos vizinhos. Vale 2 × `wall`."""
        return self.grid - self.recess_d

    @property
    def edge_bar(self) -> float:
        """Seção da gaiola de 12 arestas, com os 3 eixos vazados."""
        return (self.grid - self.hole_d) / 2


# Expressões para os User Parameters do Fusion. O add-in cria os
# primitivos como valores e os derivados como EXPRESSÃO, para que a
# lei continue viva dentro do documento: mudar `wall` no diálogo de
# parâmetros do Fusion recalcula o grid e a peça inteira.
FUSION_PARAM_PREFIX = "fb_"

DERIVED_EXPRESSIONS: Dict[str, str] = {
    "grid": "fb_hole_d + 2 * (fb_wall + fb_collar_w)",
    "recess_d": "fb_hole_d + 2 * fb_collar_w",
    "pin_d": "fb_hole_d - fb_tolerance",
    "collar_d": "fb_recess_d - fb_tolerance",
}

PRIMITIVE_UNITS: Dict[str, str] = {
    "hole_d": "mm",
    "wall": "mm",
    "collar_w": "mm",
    "collar_depth": "mm",
    "tolerance": "mm",
    "gap": "mm",
    "pin_len": "mm",
}
