"""
Validações do sistema — as mesmas que os `assert` do OpenSCAD.

Ficam aqui, no core, para valerem em qualquer implementação. No
add-in do Fusion elas alimentam `validateInputs`, que desabilita o
OK quando a combinação é inválida — o equivalente de UI ao assert.
"""

from typing import List, NamedTuple

from .params import Primitives


class Violation(NamedTuple):
    rule: str
    message: str
    fatal: bool  # True = assert (impede gerar) · False = aviso


def check(p: Primitives) -> List[Violation]:
    """Roda toda a validação e devolve o que falhou."""
    out: List[Violation] = []

    # O rebaixo não pode morder a barra da aresta. A diagonal entre
    # dois furos perpendiculares vale hole_d·√2; o rebaixo tem de
    # caber nela.
    if p.hole_d * 2 ** 0.5 <= p.recess_d:
        out.append(Violation(
            "recess_vs_edge_bar",
            f"rebaixo Ø{p.recess_d} morde a barra da aresta: "
            f"exige hole_d·√2 ({p.hole_d * 2 ** 0.5:.2f}) > recess_d",
            True))

    # Encaixe simultâneo: um macho tem de parar antes de entrar no
    # raio do perpendicular da célula receptora.
    if p.pin_len > p.pin_len_max:
        out.append(Violation(
            "pin_len_max",
            f"macho longo demais: {p.pin_len} > {p.pin_len_max:.2f} — "
            f"encosta no macho perpendicular da célula receptora",
            True))

    # A haste tem de sair do colar, senão quem entra no furo é o
    # colar e o macho não alinha.
    if p.pin_len <= p.collar_depth:
        out.append(Violation(
            "pin_len_vs_collar",
            f"colar mais fundo que a protrusão ({p.collar_depth} >= "
            f"{p.pin_len}): a haste não sai do colar",
            True))

    if p.pin_len <= 0:
        out.append(Violation("pin_len_positive", "macho sem comprimento", True))

    # Brandos — peça válida, mas provavelmente não é o que se quis.
    if abs(p.corner_sliver - p.wall) > 1e-9:
        out.append(Violation(
            "invariant_corner",
            f"lasca na quina {p.corner_sliver:.3f} != parede {p.wall}",
            False))

    if abs(p.web_between_holes - 2 * p.wall) > 1e-9:
        out.append(Violation(
            "invariant_web",
            f"alma entre furos {p.web_between_holes:.3f} != 2×parede "
            f"{2 * p.wall}",
            False))

    # O macho tangencia a passagem transversal em grid/2 − hole_d/2.
    # Acima disso ele come a seção livre do furo perpendicular.
    passage_max = p.grid / 2 - p.hole_d / 2
    if p.pin_len > passage_max:
        out.append(Violation(
            "pin_vs_passage",
            f"macho invade a passagem transversal em "
            f"{p.pin_len - passage_max:.2f}mm (tangente em {passage_max})",
            False))

    return out


def fatal(p: Primitives) -> List[Violation]:
    return [v for v in check(p) if v.fatal]


def warnings(p: Primitives) -> List[Violation]:
    return [v for v in check(p) if not v.fatal]
