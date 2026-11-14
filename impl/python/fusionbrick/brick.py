"""
Descrição geométrica do BRICK, independente de CAD.

Não desenha nada: devolve ONDE as coisas ficam. O adapter (Fusion,
OpenSCAD, o que vier) traduz isso para features da sua ferramenta.

Convenção de eixos e faces, igual à do OpenSCAD:

    eixo  0=X  1=Y  2=Z          o furo, sempre PASSANTE
    face  xn xp yn yp zn zp      o acabamento na boca

Eixo e face são camadas separadas de propósito. Com furo passante,
tratar "furo" como propriedade de face abriria a face oposta à
revelia dela.
"""

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from .params import Primitives

AXES = ("x", "y", "z")
FACES = ("xn", "xp", "yn", "yp", "zn", "zp")

# Normal de cada face, apontando para FORA da peça
FACE_NORMAL = {
    "xn": (-1, 0, 0), "xp": (1, 0, 0),
    "yn": (0, -1, 0), "yp": (0, 1, 0),
    "zn": (0, 0, -1), "zp": (0, 0, 1),
}
FACE_AXIS = {"xn": 0, "xp": 0, "yn": 1, "yp": 1, "zn": 2, "zp": 2}


@dataclass
class BrickSpec:
    cells: Tuple[int, int, int] = (1, 1, 1)
    axes: Tuple[str, str, str] = ("bored", "bored", "bored")
    faces: Sequence[str] = field(
        default_factory=lambda: ["auto"] * 6)
    p: Primitives = field(default_factory=Primitives)

    # --- faces ---------------------------------------------------
    def face(self, fi: int) -> str:
        """
        Acabamento EFETIVO da face `fi`. "auto" segue o eixo:
        recess se bored, plain se solid — igual ao brick.scad.
        """
        kind = self.faces[fi]
        if kind != "auto":
            return kind
        a = FACE_AXIS[FACES[fi]]
        return "recess" if self.axes[a] == "bored" else "plain"

    def errors(self) -> List[str]:
        """
        REQ-005: "recess" EXPLÍCITO num eixo solid é erro — mesma
        regra do assert do brick.scad. "auto" nunca cai aqui.
        """
        out = []
        for fi, f in enumerate(FACES):
            if self.faces[fi] == "recess" and \
                    self.axes[FACE_AXIS[f]] != "bored":
                out.append(f"face {f} 'recess' exige o eixo "
                           f"{AXES[FACE_AXIS[f]]} 'bored' (REQ-005)")
        return out

    # --- dimensões -----------------------------------------------
    @property
    def size(self) -> Tuple[float, float, float]:
        g = self.p.grid
        return tuple(c * g for c in self.cells)

    def centers(self, axis: int) -> List[float]:
        """Centros de célula ao longo de um eixo: grid/2 + i·grid."""
        g = self.p.grid
        return [self.p.inset + i * g for i in range(self.cells[axis])]

    # --- furos ---------------------------------------------------
    def bores(self) -> List[dict]:
        """
        Um furo passante por célula, por eixo vazado. A posição é o
        centro da célula nos DOIS eixos perpendiculares.
        """
        out = []
        for a, name in enumerate(AXES):
            if self.axes[a] != "bored":
                continue
            perp = [i for i in range(3) if i != a]
            for u in self.centers(perp[0]):
                for v in self.centers(perp[1]):
                    pos = [0.0, 0.0, 0.0]
                    pos[perp[0]] = u
                    pos[perp[1]] = v
                    out.append({
                        "axis": a, "axis_name": name,
                        "pos": tuple(pos), "d": self.p.hole_d,
                        "length": self.size[a],
                    })
        return out

    # --- rebaixos e machos ---------------------------------------
    def face_features(self) -> List[dict]:
        """
        Rebaixo ou macho no centro de cada célula de cada face.

        Um rebaixo exige o eixo correspondente vazado — rebaixo sem
        furo é bolso cego: aceita o colar de um macho que não tem o
        que agarrar.
        """
        out = []
        for fi, f in enumerate(FACES):
            kind = self.face(fi)
            if kind == "plain":
                continue
            a = FACE_AXIS[f]
            if kind == "recess" and self.axes[a] != "bored":
                continue
            perp = [i for i in range(3) if i != a]
            normal = FACE_NORMAL[f]
            plane_at = 0.0 if normal[a] < 0 else self.size[a]
            for u in self.centers(perp[0]):
                for v in self.centers(perp[1]):
                    pos = [0.0, 0.0, 0.0]
                    pos[perp[0]] = u
                    pos[perp[1]] = v
                    pos[a] = plane_at
                    out.append({
                        "face": f, "kind": kind, "axis": a,
                        "pos": tuple(pos), "normal": normal,
                        "d": self.p.recess_d if kind == "recess"
                             else self.p.collar_d,
                        "depth": self.p.collar_depth,
                        "pin_len": self.p.pin_len,
                    })
        return out

    # --- resumo ---------------------------------------------------
    def summary(self) -> str:
        sx, sy, sz = self.size
        return (
            f"BRICK {self.cells[0]}×{self.cells[1]}×{self.cells[2]}  "
            f"{sx:g} × {sy:g} × {sz:g}mm\n"
            f"  furos   {len(self.bores())}\n"
            f"  faces   {len(self.face_features())} features\n"
            f"  grid    {self.p.grid:g}  rebaixo Ø{self.p.recess_d:g}  "
            f"macho Ø{self.p.pin_d:g}×{self.p.pin_len:g}"
        )
