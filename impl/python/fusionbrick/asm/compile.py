"""
Compilador de montagem FusionBrick.

A IA (ou uma pessoa) descreve a montagem em `assembly.toml` — quais
peças ocupam quais células. O compilador:

  1. posiciona cada peça (`Part.resolve`)
  2. junta as PORTAS que coincidem — mesma posição, direções opostas —
     e decide cada par pela tabela de spec/assembly.md
  3. roda as regras ASM-### (`checks.py`)
  4. entrega BOM, passo a passo e assembly.scad (`outputs.py`) e as
     métricas de qualidade e de física (`metrics.py`)

Stdlib pura; o OpenSCAD só entra em `outputs.render_jobs`.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional

from .. import geom as G
from ..params import Primitives
from . import checks, metrics, outputs
from .model import EPS, Finding, IRError, Joint, Part, Port
from . import names
from .parts import TYPES
from .variants import VARIANTS, expand

try:  # 3.11+
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as _toml  # type: ignore
    except ModuleNotFoundError:
        _toml = None

# stud × socket = integral · socket × socket = cavilha · o resto com pino = erro
# (por dentro: stud = pin, socket = recess, flat = plain — ver names.py)
PAIR_ERRORS = {
    frozenset(["pin"]): ("dois pinos (stud) frente a frente", "troque um dos dois para socket"),
    frozenset(["pin", "plain"]): ("pino (stud) contra face lisa",
                                  "fure o receptor nesse eixo (holes; a face auto vira socket) "
                                  "ou troque o pino por flat"),
}


def load(path: str) -> "Assembly":
    if path.endswith(".json"):
        with open(path) as f:
            data = json.load(f)
    else:
        if _toml is None:
            raise IRError("ler TOML exige Python 3.11+ (tomllib) ou o pacote tomli")
        with open(path, "rb") as f:
            data = _toml.load(f)
    return Assembly(data, base_dir=os.path.dirname(os.path.abspath(path)))


class Assembly:
    def __init__(self, data: dict, p: Optional[Primitives] = None, base_dir: str = "."):
        self.p = p or Primitives()
        self.base_dir = base_dir
        meta = names.normalize_meta(data.get("assembly", {}))

        def get(k):                        # em TOML, chaves depois de [assembly] caem dentro dela
            return data.get(k, meta.get(k, []))

        self.name = meta.get("name", "montagem")
        self.intent = meta.get("intent", "")
        self.dowel_step = max(1, int(meta.get("dowel_step", 1)))   # cavilha a cada N furos de um contato
        self.hero_rz = float(meta.get("hero_rz", 35))              # giro em Z da vista principal
        self.findings: List[Finding] = []
        self.parts: Dict[str, Part] = {}
        raw = list(get("parts")) + list(get("part"))
        if not raw:
            raise IRError("nenhuma peça: declare `parts = [...]`")
        self.expanded: Dict[str, List[str]] = {}    # peça escrita → peças que ela virou (strut)
        for i, rp in enumerate(raw):
            self._add_part(rp, i)

        def ids(seq):
            return [q for pid in seq for q in self.expanded.get(pid, [pid])]

        self.groups = [{**g, "parts": ids(g.get("parts", []))} for g in get("groups")]
        self.routes = [dict(r) for r in get("routes")]
        self.hinges = set(ids(h if isinstance(h, str) else h.get("part") for h in get("hinges")))
        self.ports: Dict[str, List[Port]] = {}
        self.joints: List[Joint] = []
        self.open_ports = set()            # (posição, eixo) reservados para fio (ASM-007)
        self.joined = set()                # pares de peças com junta

    # --- achados ---------------------------------------------------
    def err(self, code, msg, hint=""):
        self.findings.append(Finding("error", code, msg, hint))

    def warn(self, code, msg, hint=""):
        self.findings.append(Finding("warn", code, msg, hint))

    def info(self, code, msg, hint=""):
        self.findings.append(Finding("info", code, msg, hint))

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    # --- leitura ---------------------------------------------------
    def _add_part(self, rp: dict, i: int):
        written = rp.get("id") or f"p{i}"
        made = names.normalize({**rp, "id": written})
        if len(made) > 1:
            self.expanded[written] = [q["id"] for q in made]
        for q in made:
            pid = q["id"]
            if pid in self.parts:
                raise IRError(f"id repetido: {pid}")
            q = expand(q)
            cls = TYPES.get(q.get("type", "brick"))
            if cls is None:
                known = ", ".join(names.DESCRIPTIONS)
                self.err("ASM-000", f"{pid}: tipo '{q.get('type')}' não existe (tipos: {known})")
                continue
            self.parts[pid] = cls(pid, q, self.p.grid)

    def of(self, *types) -> List[Part]:
        return [q for q in self.parts.values() if q.type in types]

    # --- compilar --------------------------------------------------
    def compile(self) -> "Assembly":
        checks.routes(self)                # antes das juntas: marca as portas abertas para fio
        for part in sorted(self.parts.values(), key=lambda q: (q.stage, q.order)):
            if part.stage == 2:
                continue
            part.resolve(self)
            if part.placed:
                self.ports[part.id] = part.ports(self)
        self._join_ports()
        for part in self.parts.values():
            if part.stage == 2:
                part.resolve(self)
        self.joined = {frozenset((j.a, j.b)) for j in self.joints}
        for rule in checks.RULES:
            rule(self)
        return self

    # --- juntas: portas que coincidem ------------------------------
    def _join_ports(self):
        at = defaultdict(list)
        for pts in self.ports.values():
            for pt in pts:
                at[pt.key()].append(pt)
        dowels = defaultdict(list)         # (a, b, direção) → posições recess × recess
        for pts in at.values():
            mated = set()
            for i, pa in enumerate(pts):
                for pb in pts[i + 1:]:
                    if pa.part != pb.part and G.dot(pa.dir, pb.dir) < -0.9999:
                        mated.update((id(pa), id(pb)))
                        self._pair(pa, pb, dowels)
            for pt in pts:
                if pt.kind == "pin" and id(pt) not in mated:
                    self._lonely_pin(pt)
        for (a, b, axis, grid), spots in dowels.items():
            spots.sort(key=lambda s: s[0])
            for k, (pos, d) in enumerate(spots):
                if k % self.dowel_step == 0 or k == len(spots) - 1:
                    self.joints.append(Joint("dowel", a, b, axis, pos, d, grid=grid))

    def _pair(self, pa: Port, pb: Port, dowels):
        kinds = frozenset((pa.kind, pb.kind))
        where = (f"{pa.part}.{names.face(pa.label)} × {pb.part}.{names.face(pb.label)} "
                 f"em {self.cell_of(pa.pos, pa.axis)}")
        axis = pa.axis if pa.axis is not None else -1
        grid = all(self.parts[x].type == "brick" for x in (pa.part, pb.part))
        reserved = (pa.pos, axis) in self.open_ports
        if kinds in PAIR_ERRORS:
            msg, hint = PAIR_ERRORS[kinds]
            self.err("ASM-003", f"{msg} — {where}", hint)
        elif kinds == {"pin", "recess"}:
            male, recv = (pa, pb) if pa.kind == "pin" else (pb, pa)
            if reserved:
                self.err("ASM-007", f"rota de fio atravessa um pino (stud) — {where}",
                         "o pino fecha o furo; use socket × socket nessa porta")
            self.joints.append(Joint("integral", male.part, recv.part, axis, pa.pos, male.dir, grid=grid))
        elif kinds == {"recess"}:
            if reserved:
                self.info("ASM-007", f"porta aberta para fio (sem cavilha) — {where}")
            else:
                dowels[(pa.part, pb.part, axis, grid)].append((pa.pos, pa.dir))

    def _lonely_pin(self, pt: Port):
        """Pino sem par: ou está livre, ou entra numa peça fora de um centro de célula."""
        tip = G.add(pt.pos, G.mul(pt.dir, 1.0))
        for b in self.of("brick"):
            if b.id != pt.part and all(b.lo[i] + EPS < tip[i] < b.hi[i] - EPS for i in range(3)):
                return self.err("ASM-003", f"pino de {pt.part}.{names.face(pt.label)} entra em {b.id} fora de um "
                                "centro de célula — sem encaixe",
                                "alinhe as peças no grid ou troque o pino por flat")
        if self.parts[pt.part].type != "brick":
            self.info("ASM-011", f"{pt.part}: porta {names.face(pt.label)} livre")

    # --- apoio -----------------------------------------------------
    def cell_of(self, pos, axis) -> str:
        """Posição em mm → célula legível; no eixo da junta fica a fronteira."""
        g = self.p.grid
        return "[" + ",".join(f"{pos[i] / g:g}" if i == axis else f"{int((pos[i] / g + EPS) // 1):d}"
                              for i in range(3)) + "]"

    def assembly_order(self) -> List[str]:
        """Ordem de montagem: grupos na ordem declarada, depois o resto."""
        order = [pid for g in self.groups for pid in g.get("parts", []) if pid in self.parts]
        order = list(dict.fromkeys(order))
        return order + [pid for pid in self.parts if pid not in set(order)]

    def config_of(self, part: Part):
        """Compatibilidade: (chave, rotação, (scad, parâmetros))."""
        key, scad, prm = part.config(self)
        return key, part.matrix(self)[0] if part.placed else None, (scad, prm)

    # --- saídas (outputs.py, metrics.py) ---------------------------
    def bom(self):
        return outputs.bom(self)

    def steps(self):
        return outputs.steps(self)[0]

    def scad(self, parts_dir: str = "parts") -> str:
        return outputs.scad(self, parts_dir)

    def bom_md(self) -> str:
        return outputs.bom_md(self)

    def steps_md(self) -> str:
        return outputs.steps_md(self)

    def summary(self) -> str:
        return outputs.summary(self)

    def ports_report(self, pid: str) -> str:
        return outputs.ports_report(self, pid)

    def stats(self) -> dict:
        return metrics.stats(self)

    def stats_report(self) -> str:
        return metrics.stats_report(self)
