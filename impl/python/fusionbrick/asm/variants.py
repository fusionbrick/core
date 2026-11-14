"""
Variantes: nomes curtos para as configurações de BRICK que se repetem.

Uma variante NÃO é peça nova — é um BRICK com padrões já escolhidos.
Qualquer campo escrito na peça vence o padrão, então o controle
paramétrico completo continua disponível:

    { type = "beam", at = [0,0,0], size = [12,1,1] }                  # padrões
    { type = "beam", at = [0,0,0], size = [12,1,1], holes = "y" }     # só furos em Y

    beam      viga 1×1×n furada nos 3 eixos, pontas redondas, furos à vista
    plate     placa de 4 mm furada em Z, cantos redondos em planta
    cover     tampa lisa: sem furos, pinos para baixo só no perímetro

Açúcar que vale para qualquer BRICK (e variantes):

    studs = "top" | "bottom"      pinos na face de cima/baixo (em viga, só nas células planas)
    studs = ["left", "right"]     essas faces levam pino
    flat  = ["back"]              essas faces ficam lisas

Este módulo já recebe a peça nos nomes internos (`names.normalize`):
`cells`, `axes`, `round`, `pin_cells`, faces `xn…zp`, `pin/recess/plain`.
Fonte única: a skill e o schema leem esta tabela.
"""

from __future__ import annotations

from .model import IRError


def _beam(rp):
    cells = rp.get("cells", (1, 1, 1))
    long_axis = max(range(3), key=lambda i: cells[i])
    if sorted(cells)[:2] != [1, 1]:
        raise IRError(f"{rp.get('id')}: beam (viga) é 1×1×n — size = {list(cells)} tem seção maior; use brick")
    # furos à vista de lado: viga em X mostra os furos Y; viga em Y, os X; poste, os Y
    return {"axes": "xyz", "round": "x" if long_axis == 1 else "y"}


def _plate(rp):
    return {"thickness": 4.0, "axes": "z", "round": "z", "corner_r": 4.0}


def _cover(rp):
    return {"thickness": 4.0, "axes": "none", "round": "z", "corner_r": 4.0,
            "faces": {"zn": "pin"}, "pin_cells": "edge"}


VARIANTS = {"beam": _beam, "plate": _plate, "cover": _cover}

DESCRIPTIONS = {
    "beam": "viga 1×1×n furada nos 3 eixos, pontas redondas (furos à vista de lado)",
    "plate": "placa de 4 mm furada em Z, cantos redondos em planta",
    "cover": "tampa lisa de 4 mm: sem furos, pinos para baixo só no perímetro",
}

SUGAR = ("studs", "flat")


def _faces_dict(rp) -> dict:
    f = rp.get("faces") or {}
    return {"default": f} if isinstance(f, str) else dict(f)


def _apply_sugar(rp: dict) -> dict:
    faces = _faces_dict(rp)
    studs = rp.pop("studs", None)
    if studs in ("up", "down"):
        faces.setdefault("zp" if studs == "up" else "zn", "pin")
        if rp.get("round", "none") in ("x", "y"):    # face Z com ponta curva: macho só nas planas
            rp.setdefault("pin_cells", "inner")
    elif studs not in (None, "none"):
        raise IRError(f"{rp.get('id')}: studs = {studs!r}: use top, bottom ou uma lista de faces")
    for key, kind in (("pins", "pin"), ("plain", "plain")):
        for f in rp.pop(key, ()):
            faces[f] = kind
    if faces:
        rp["faces"] = faces
    return rp


def expand(rp: dict) -> dict:
    """Variante + açúcar → BRICK explícito. Peças de outros tipos passam intactas."""
    t = rp.get("type", "brick")
    if t not in VARIANTS and t != "brick":
        return rp
    out = dict(rp)
    if t in VARIANTS:
        defaults = VARIANTS[t](rp)
        own_faces = _faces_dict(rp)
        out = {**defaults, **out, "type": "brick"}
        if "faces" in defaults or own_faces:
            out["faces"] = {**defaults.get("faces", {}), **own_faces}
    return _apply_sugar(out)
