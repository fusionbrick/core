"""
Vocabulário do compilador: achado, porta, junta e a peça-base.

Tudo o que o compilador sabe de uma peça passa por QUATRO perguntas,
iguais para qualquer tipo:

    resolve(asm)   onde ela fica (origem, tamanho, referencial)
    ports(asm)     onde ela encaixa (posição, direção, acabamento)
    boxes()        que volume ela ocupa (caixas para colisão)
    config(asm)    que STL ela é (chave, .scad, parâmetros)

Um tipo novo de peça é uma classe que responde a essas quatro — nada
mais no compilador precisa saber que ele existe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .. import geom as G

EPS = 1e-6
Vec = Tuple[float, float, float]


def r4(v: float) -> float:
    return round(v + 0.0, 4)


def rvec(v) -> Vec:
    return tuple(r4(c) for c in v)


class IRError(Exception):
    """A descrição (IR) está malformada — diferente de uma montagem que não encaixa."""


@dataclass
class Finding:
    severity: str          # "error" | "warn" | "info"
    code: str              # ASM-### ou REQ-###
    msg: str
    hint: str = ""

    def line(self) -> str:
        tag = {"error": "ERRO ", "warn": "AVISO", "info": "info "}[self.severity]
        out = f"{tag} {self.code}  {self.msg}"
        if self.hint:
            out += f"\n      sugestão: {self.hint}"
        return out


@dataclass
class Port:
    """Um ponto de encaixe: centro de face, direção para FORA, acabamento."""
    part: str
    pos: Vec
    dir: Vec
    kind: str              # recess | pin | plain
    label: str = ""        # nome da face (BRICK) ou da porta

    @property
    def face(self) -> str:
        return self.label

    @property
    def axis(self) -> Optional[int]:
        return G.is_ortho(self.dir)

    def key(self):
        return tuple(round(c, 3) for c in self.pos)


@dataclass
class Joint:
    kind: str              # "integral" | "dowel" | "axle"
    a: str                 # macho (integral), 1ª peça (dowel) ou roda (axle)
    b: str                 # receptor ou 2ª peça
    axis: int              # 0..2 se ortogonal; -1 se diagonal
    pos: Vec
    dir: Vec               # direção da junta (de a para b)
    sign: int = 1          # axle: para onde aponta a roda
    width: int = 1         # axle: largura da roda em células
    grid: bool = True      # as duas peças vivem no grid (BRICK × BRICK)

    def line(self):
        return G.line_key(self.pos, self.dir)


class Part:
    """Peça-base. Subclasses em parts.py."""

    type = ""
    stage = 1              # 1 = antes das juntas; 2 = depende das portas dos outros (roda)
    structural = True      # conta como estrutura (resolução, rigidez)
    printed = True         # entra na BOM
    collides = True        # entra na checagem de colisão
    default_color: Optional[Sequence[float]] = [0.12, 0.12, 0.13]

    def __init__(self, pid: str, rp: dict, grid: float):
        at = tuple(float(x) for x in rp.get("at", (0, 0, 0)))
        if len(at) != 3:
            raise IRError(f"{pid}: at precisa de 3 coordenadas")
        self.id, self.at = pid, at
        self.group = rp.get("group")
        self.color = rp.get("color")
        self.origin: Vec = tuple(a * grid for a in at)
        self.size: Vec = (0.0, 0.0, 0.0)
        self.placed = False            # resolve() conseguiu posicionar
        self.parse(rp, grid)

    # --- as quatro perguntas -------------------------------------
    def parse(self, rp: dict, grid: float):
        pass

    def resolve(self, asm):
        self.placed = True

    def ports(self, asm) -> List[Port]:
        return []

    def boxes(self) -> List[G.Box]:
        return [G.Box.aabb(self.lo, self.hi, self.id, self.type)] if self.placed else []

    def config(self, asm):
        """(chave do STL, arquivo .scad, parâmetros)."""
        raise NotImplementedError

    # --- apoio ----------------------------------------------------
    def matrix(self, asm):
        """Matriz 4×4 que leva o STL à posição na montagem."""
        raise NotImplementedError

    def explode_with(self) -> Sequence[str]:
        """Peças cujo deslocamento na vista explodida esta acompanha (média)."""
        return (self.id,)

    def ignores(self, other: "Part", asm) -> bool:
        """Pares que encostam por projeto e não são colisão."""
        return False

    def mass_center(self):
        return tuple(self.origin[i] + self.size[i] / 2 for i in range(3))

    @property
    def lo(self) -> Vec:
        return self.origin

    @property
    def hi(self) -> Vec:
        return tuple(self.origin[i] + self.size[i] for i in range(3))

    def on_grid(self, asm, what: str):
        if any(abs(c - round(c)) > EPS for c in self.at):
            asm.err("ASM-001", f"{self.id}: {what} — at precisa ser inteiro")
