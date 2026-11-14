"""
Nomes: o vocabulário público da IR, num lugar só.

Quem escreve uma montagem usa as palavras desta tabela. O compilador
trabalha por dentro com os códigos da geometria (`xn`, `pin`, `cells`…)
— os mesmos dos parâmetros do OpenSCAD e do contrato — e este módulo
traduz na entrada (`normalize`) e na saída (`face`, `kind`, `publicize`).

Os nomes antigos continuam aceitos: todo arquivo escrito antes da
revisão compila igual.

    PEÇAS      brick · beam · plate · cover · curve · strut · wheel · component
               (node continua existindo para quem monta a diagonal à mão)
    ENCAIXES   stud (pino impresso) · socket (encaixe) · flat (liso)
               dowel = cavilha solta que une dois sockets
    FACES      front +X · back −X · left +Y · right −Y · top +Z · bottom −Z
"""

from __future__ import annotations

from .model import IRError

# público → interno -----------------------------------------------------
TYPES = {"liftarm": "beam", "tile": "cover", "bend": "curve", "mock": "component"}   # antigos → atuais
FACES = {"front": "xp", "back": "xn", "left": "yp", "right": "yn", "top": "zp", "bottom": "zn"}
KINDS = {"stud": "pin", "socket": "recess", "flat": "plain"}
STUDS = {"top": "up", "bottom": "down"}
META = {"view_angle": "hero_rz", "dowel_every": "dowel_step"}

BRICKS = ("brick", "beam", "plate", "cover")
FIELDS = {                      # por tipo: nome público → nome interno
    "brick": {"size": "cells", "holes": "axes", "rounded": "round", "studs_on": "pin_cells", "flat": "plain"},
    "curve": {},
    "wheel": {"diameter": "cells"},
    "component": {"size_mm": "size"},
    "node": {},
    "strut": {},
}

# interno → público -----------------------------------------------------
FACE_OUT = {v: k for k, v in FACES.items()}
KIND_OUT = {v: k for k, v in KINDS.items()}
STUDS_OUT = {v: k for k, v in STUDS.items()}
META_OUT = {v: k for k, v in META.items()}

DESCRIPTIONS = {
    "brick": "Bloco — a peça-base: qualquer tamanho, furos e encaixes que você escolher",
    "beam": "Viga — barra 1×1×n furada, de pontas redondas",
    "plate": "Placa — chapa fina furada, para pisos e bases",
    "cover": "Tampa — chapa lisa que fecha por cima",
    "curve": "Curva — viga que vira 90° ou 180°",
    "strut": "Diagonal — viga inclinada entre dois pontos; os nós das pontas são criados sozinhos",
    "wheel": "Roda — com eixo incluso",
    "component": "Componente — o que você compra pronto: bateria, placa, motor, fio",
    "node": "Nó — ponta de diagonal montada à mão (uso avançado)",
}


def face(code: str) -> str:
    """`xn` → `back`. Rótulos que não são face (portas de nó, A/B) passam."""
    return FACE_OUT.get(code, code)


def kind(code: str) -> str:
    return KIND_OUT.get(code, code)


def _face_in(f, pid):
    if f in FACES:
        return FACES[f]
    if f in FACE_OUT or f == "default":
        return f
    raise IRError(f"{pid}: face '{f}' não existe (use {', '.join(FACES)})")


def _kind_in(k):
    return KINDS.get(k, k)


def _kinds_in(v):
    return _kind_in(v) if isinstance(v, str) else [_kind_in(k) for k in v]


def type_of(rp: dict) -> str:
    t = rp.get("type", "brick")
    if t == "beam" and "from" in rp:        # IR antiga: `beam` era a viga entre dois nós
        return "strut"
    return TYPES.get(t, t)


def _brick(rp, pid):
    faces = rp.get("faces")
    if isinstance(faces, str):
        rp["faces"] = _kind_in(faces)
    elif faces:
        rp["faces"] = {_face_in(f, pid): _kind_in(k) for f, k in faces.items()}
    studs = rp.get("studs")
    if isinstance(studs, (list, tuple)):    # studs = ["left", "right"] → essas faces levam pino
        rp["pins"] = list(rp.get("pins", ())) + list(rp.pop("studs"))
    elif studs in STUDS:
        rp["studs"] = STUDS[studs]
    for key in ("pins", "plain"):
        if key in rp:
            rp[key] = [_face_in(f, pid) for f in rp[key]]


def _curve(rp, pid):
    if "radius" in rp:
        r = int(rp.pop("radius"))
        if r < 1:
            raise IRError(f"{pid}: radius ≥ 1 (células que a curva ocupa de lado)")
        rp.setdefault("k", r - 1)
    if "ports" in rp:
        rp["ports"] = _kinds_in(rp["ports"])


def _node(rp, pid):
    if "ports" in rp:
        rp["ports"] = _kinds_in(rp["ports"])


def _wheel(rp, pid):
    on = rp.get("on", "")
    if "." in on:
        host, f = on.rsplit(".", 1)
        rp["on"] = f"{host}.{FACES.get(f, f)}"


def _strut(rp, pid):
    if rp.get("style") == "liftarm":
        rp["style"] = "beam"


_BY_TYPE = {"curve": _curve, "node": _node, "wheel": _wheel, "strut": _strut}


def _back_arm(v):
    """Braço padrão do nó: o eixo dominante da diagonal, para trás dela."""
    a = max(range(3), key=lambda i: abs(v[i]))
    out = [0, 0, 0]
    out[a] = -1 if v[a] > 0 else 1
    return out


def _expand_strut(rp, pid):
    """`strut` por coordenadas → dois nós e a viga, com os ids `<id>-n0/-n1/-v`."""
    a, b = [int(c) for c in rp["from"]], [int(c) for c in rp["to"]]
    v = [b[i] - a[i] for i in range(3)]
    common = {k: rp[k] for k in ("color", "fillet") if k in rp}
    arm_a = rp.get("from_arm") or _back_arm(v)
    arm_b = rp.get("to_arm") or _back_arm([-c for c in v])
    link = {"id": f"{pid}-v", "type": "strut", "from": f"{pid}-n0", "to": f"{pid}-n1",
            "style": rp.get("style", "beam")}
    if "color" in rp:
        link["color"] = rp["color"]
    return [
        {"id": f"{pid}-n0", "type": "node", "at": a, "dirs": [list(arm_a), v], **common},
        {"id": f"{pid}-n1", "type": "node", "at": b, "dirs": [[-c for c in v], list(arm_b)], **common},
        link,
    ]


def normalize(rp: dict) -> list:
    """Uma peça como foi escrita → uma ou mais peças nos nomes internos."""
    rp = dict(rp)
    pid = rp.get("id")
    t = rp["type"] = type_of(rp)
    table = FIELDS["brick"] if t in BRICKS else FIELDS.get(t, {})
    for public, internal in table.items():
        if public in rp:
            rp.setdefault(internal, rp[public])
            del rp[public]
    if t in BRICKS:
        _brick(rp, pid)
    elif t in _BY_TYPE:
        _BY_TYPE[t](rp, pid)
    if t == "strut" and not isinstance(rp.get("from"), str) and rp.get("from") is not None:
        if not isinstance(rp.get("to"), (list, tuple)):
            raise IRError(f"{pid}: strut precisa de from e to do mesmo jeito (duas células ou dois nós)")
        return [q for part in _expand_strut(rp, pid) for q in normalize(part)]
    return [rp]


def normalize_meta(meta: dict) -> dict:
    return {META.get(k, k): v for k, v in meta.items()}


# interno/antigo → público (gerador e migração) -------------------------
def publicize(rp: dict) -> dict:
    """Reescreve uma peça com os nomes públicos, na mesma ordem de campos."""
    t = type_of(rp)
    table = FIELDS["brick"] if t in BRICKS else FIELDS.get(t, {})
    rename = {internal: public for public, internal in table.items()}
    out = {}
    for k, v in rp.items():
        if k == "type":
            v = t
        elif k == "faces" and isinstance(v, dict):
            v = {face(f): kind(x) for f, x in v.items()}
        elif k == "faces":
            v = kind(v)
        elif k == "studs" and isinstance(v, str):
            v = STUDS_OUT.get(v, v)
        elif k == "pins" and t in BRICKS and "studs" not in rp:
            k, v = "studs", [face(f) for f in v]
        elif k == "plain" and t in BRICKS:
            v = [face(f) for f in v]
        elif k == "ports":
            v = kind(v) if isinstance(v, str) else [kind(x) for x in v]
        elif k == "k" and t == "curve":
            k, v = "radius", v + 1
        elif k == "on" and "." in v:
            host, f = v.rsplit(".", 1)
            v = f"{host}.{face(f)}"
        elif k == "style" and v == "liftarm":
            v = "beam"
        out[rename.get(k, k)] = v
    return out
