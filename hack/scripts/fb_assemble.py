#!/usr/bin/env python3
"""
fb_assemble — compila examples/<nome>/assembly.toml.

  fb_assemble.py check  <assembly.toml>          valida, não renderiza (ms)
  fb_assemble.py build  <assembly.toml> [--png]  valida + STLs + .scad + BOM + passos
  fb_assemble.py ports  <assembly.toml> <peça>   portas de uma peça e o que cada uma faz
  fb_assemble.py stats  <assembly.toml>          métricas de qualidade: resolução, cavilhas, reuso
  fb_assemble.py physics <assembly.toml>         massa, centro de massa, tombamento, mastro (após build)
  fb_assemble.py review <assembly.toml>          ficha de qualidade: os portões medidos do conselho
  fb_assemble.py schema                          JSON Schema da IR (para tool use)

Regras: spec/assembly.md · Skill: .claude/skills/fusionbrick-assembly/
"""

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "impl", "python"))

from fusionbrick import assembly as A  # noqa: E402
from fusionbrick.params import Primitives  # noqa: E402

SCAD_DIR = os.path.join(ROOT, "impl", "openscad")

FACE_KINDS = ["auto", "socket", "stud", "flat"]
FACE_NAMES = ["front", "back", "left", "right", "top", "bottom"]
VEC3 = {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3}
IVEC3 = {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3}
RGB = {"type": "array", "items": {"type": "number", "minimum": 0, "maximum": 1}, "minItems": 3, "maxItems": 3}
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "FusionBrick assembly IR",
    "description": "Peças em células (1 célula = 8 mm). Eixos: x, y no chão, z para cima; frente = +X. "
                   "Encaixes: stud (pino impresso), socket (encaixe), flat (liso). "
                   "Regras: spec/assembly.md. Nunca mm, translate ou rotate.",
    "type": "object",
    "required": ["assembly", "parts"],
    "properties": {
        "assembly": {"type": "object", "required": ["name"], "properties": {
            "name": {"type": "string"}, "intent": {"type": "string"},
            "dowel_every": {"type": "integer", "minimum": 1,
                            "description": "uma cavilha a cada N furos num contato longo (padrão 1); 3 com vigas"},
            "view_angle": {"type": "number", "description": "giro em Z da vista principal (35, 125, 215…)"},
        }},
        "parts": {"type": "array", "items": {"oneOf": [
            {"type": "object", "required": ["id", "type", "at", "size"],
             "description": "Bloco e variantes. Não gira: size e faces no referencial do mundo "
                            "(frente = +X).",
             "properties": {
                 "id": {"type": "string"},
                 "type": {"enum": ["brick"] + list(A.VARIANTS),
                          "description": "brick, ou uma variante (bloco com padrões): "
                                         + "; ".join(f"{k} = {v}" for k, v in A.DESCRIPTIONS.items())},
                 "at": {**VEC3, "description": "canto mínimo; X/Y inteiros, Z múltiplo de 0.5"},
                 "size": {"type": "array", "items": {"type": "integer", "minimum": 1},
                          "minItems": 3, "maxItems": 3, "description": "células em x, y, z"},
                 "studs": {"description": "pinos impressos: 'top', 'bottom', ou lista de faces",
                           "oneOf": [{"enum": ["top", "bottom", "none"]},
                                     {"type": "array", "items": {"enum": FACE_NAMES}}]},
                 "flat": {"type": "array", "items": {"enum": FACE_NAMES},
                          "description": "faces que ficam lisas"},
                 "thickness": {"type": "number", "description": "mm; > 0 vira chapa (Z fora do grid)"},
                 "holes": {"type": "string", "description": "eixos furados: letras de 'xyz', ou 'none'"},
                 "faces": {"type": "object", "properties": {
                     k: {"enum": FACE_KINDS} for k in ["default"] + FACE_NAMES},
                     "description": "auto = socket no eixo furado, flat no sólido; declare só stud e flat"},
                 "rounded": {"enum": ["none", "x", "y", "z"],
                             "description": "arredonda as pontas em torno deste eixo; pino em ponta "
                                            "redonda é proibido (REQ-010) — junte por cavilha"},
                 "corner_r": {"type": "number", "maximum": 4, "description": "mm; ≤ grid/2"},
                 "studs_on": {"enum": ["all", "edge", "inner"],
                              "description": "onde ficam os pinos da face: todos, só a borda, só o miolo plano"},
                 "color": RGB,
             }},
            {"type": "object", "required": ["id", "type", "at", "dir", "turn"],
             "description": "Curva: viga que vira 90° ou 180°. Liga só pelas pontas.",
             "properties": {
                 "id": {"type": "string"}, "type": {"const": "curve"},
                 "at": {**IVEC3, "description": "1ª célula do arco; a entrada fica na face de trás (−dir)"},
                 "dir": {**IVEC3, "description": "avanço na entrada (um eixo)"},
                 "turn": {**IVEC3, "description": "para onde a curva vira (⊥ dir)"},
                 "radius": {"type": "integer", "minimum": 1, "maximum": 3,
                            "description": "células que a curva ocupa de lado: 1, 2 (padrão) ou 3"},
                 "angle": {"enum": [90, 180]},
                 "ports": {"description": "'socket' (padrão), 'stud', 'flat' ou [entrada, saída]"},
                 "color": RGB,
             }},
            {"type": "object", "required": ["id", "type", "from", "to"],
             "description": "Diagonal: viga inclinada entre duas células. O vetor precisa fechar no grid "
                            "(3-4-5, 5-12-13…). Cria os nós <id>-n0, <id>-n1 e a viga <id>-v.",
             "properties": {
                 "id": {"type": "string"}, "type": {"const": "strut"},
                 "from": {**IVEC3, "description": "célula de uma ponta (ou o id de um node)"},
                 "to": {**IVEC3, "description": "célula da outra ponta (ou o id de um node)"},
                 "from_arm": {**IVEC3, "description": "braço do nó em `from` que prende no resto; padrão: "
                              "o eixo dominante, para trás da diagonal. Sempre a ≥127° dela"},
                 "to_arm": IVEC3,
                 "style": {"enum": ["beam", "box"], "description": "beam = furada de pontas redondas"},
                 "color": RGB,
             }},
            {"type": "object", "required": ["id", "type", "at", "on"],
             "properties": {
                 "id": {"type": "string"}, "type": {"const": "wheel"},
                 "at": {**VEC3, "description": "a célula do cubo, encostada na face"},
                 "on": {"type": "string", "description": "<peça>.<face>, ex. 'lateral_e.right'; a face "
                        "precisa ter encaixe (socket)"},
                 "diameter": {"type": "integer", "minimum": 3, "description": "diâmetro em células"},
                 "width": {"type": "integer", "minimum": 1, "maximum": 6, "description": "largura em células"},
                 "tread": {"enum": ["street", "offroad", "balloon"]},
                 "spokes": {"type": "integer", "minimum": 0},
                 "spoke_style": {"enum": ["straight", "y"]},
                 "color": RGB,
             }},
            {"type": "object", "required": ["id", "type"],
             "description": "Componente: volume do que se compra pronto (não imprime). cable e text não colidem.",
             "properties": {
                 "id": {"type": "string"}, "type": {"const": "component"},
                 "at": {**VEC3, "description": "células, aceita fração"},
                 "size_mm": {**VEC3, "description": "medida real em mm"},
                 "shape": {"enum": ["box", "cyl", "cable", "text"]}, "axis": {"enum": ["x", "y", "z"]},
                 "points": {"type": "array", "description": "cable: pontos em células"},
                 "text": {"type": "string"},
                 "label": {"type": "string"}, "color": RGB,
                 "mass": {"type": "number", "description": "g; sem ela, physics estima pelo volume"},
             }},
            {"type": "object", "required": ["id", "type", "at", "dirs"],
             "description": "Nó solto (uso avançado: 3+ portas). Para uma diagonal comum, use strut.",
             "properties": {
                 "id": {"type": "string"}, "type": {"const": "node"},
                 "at": {**IVEC3, "description": "célula do nó"},
                 "dirs": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}},
                          "description": "uma direção inteira por porta. Braço ortogonal a ≥127° de toda "
                                         "diagonal (senão invade a viga)"},
                 "ports": {"description": "'stud' (padrão) ou lista por porta"},
                 "fillet": {"type": "number", "maximum": 2, "description": "mm; ≤ grid/4"},
                 "color": RGB,
             }},
        ]}},
        "groups": {"type": "array", "items": {"type": "object", "required": ["id", "parts"],
                   "properties": {"id": {"type": "string"}, "note": {"type": "string"},
                                  "sub": {"type": "boolean", "description": "subconjunto montado à parte; "
                                          "entra como um corpo só (ASM-012)"},
                                  "parts": {"type": "array", "items": {"type": "string"}}}}},
        "routes": {"type": "array", "items": {"type": "object", "required": ["id", "path"],
                   "properties": {"id": {"type": "string"},
                                  "path": {"type": "array", "items": {"type": "array"}}}}},
        "hinges": {"type": "array", "items": {"type": "string"}},
    },
}


def _openscad():
    """openscad sem tela precisa de X virtual para PNG no Linux."""
    exe = shutil.which("openscad") or "openscad"
    return exe


def _png_prefix():
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") \
            and shutil.which("xvfb-run"):
        return ["xvfb-run", "-a"]
    return []


def cmd_check(path, quiet=False):
    asm = A.load(path).compile()
    print(asm.summary())
    return asm


def cmd_build(path, fn, png, jobs, force):
    asm = cmd_check(path)
    if not asm.ok and not force:
        print("\nmontagem com ERRO — nada foi gerado (use --force para gerar assim mesmo)")
        return 1
    out = os.path.dirname(os.path.abspath(path))
    parts_dir = os.path.join(out, "parts")
    os.makedirs(parts_dir, exist_ok=True)

    todo = A.render_jobs(asm, SCAD_DIR, parts_dir, fn)
    if todo:
        print(f"\nrenderizando {len(todo)} peça(s) única(s) (cache em parts/)...")

    def run(job):
        stl, stamp, sig, cmd = job
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(stl):
            with open(stamp, "w") as f:
                f.write(sig)
            return f"  ok    {os.path.basename(stl)}"
        err = [l for l in r.stderr.splitlines() if "ERROR" in l or "Assert" in l]
        return f"  FALHA {os.path.basename(stl)}: {' | '.join(err[:2])}"

    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for line in ex.map(run, todo):
            print(line)

    with open(os.path.join(out, "assembly.scad"), "w") as f:
        f.write(asm.scad("parts"))
    with open(os.path.join(out, "bom.md"), "w") as f:
        f.write(asm.bom_md())
    with open(os.path.join(out, "steps.md"), "w") as f:
        f.write(asm.steps_md())
    with open(os.path.join(out, "report.txt"), "w") as f:
        f.write(asm.summary() + "\n\n" + asm.stats_report() + "\n")
    print(asm.stats_report())
    print(f"-> {os.path.relpath(out, ROOT)}/  assembly.scad · bom.md · steps.md · report.txt · parts/")

    if png:
        render_pngs(out, asm.hero_rz)
    return 0 if asm.ok else 1


VIEWS = {
    # nome: (rot_x, rot_y, rot_z, explode)
    "assembly": (62, 0, 35, 0),
    "assembly-exploded": (62, 0, 35, 18),
    "assembly-side": (90, 0, 0, 0),
    "assembly-top": (0, 0, 0, 0),
    "assembly-back": (62, 0, 215, 0),
}


def render_pngs(out, hero_rz=35):
    scad = os.path.join(out, "assembly.scad")
    for name, (rx, ry, rz, ex) in VIEWS.items():
        if name in ("assembly", "assembly-exploded"):
            rz = hero_rz
        png = os.path.join(out, name + ".png")
        cmd = _png_prefix() + [_openscad(), scad, "--preview", "-o", png,
                               "--imgsize=1600,1200", "--projection=o", "--viewall",
                               "--autocenter", "--colorscheme=Tomorrow",
                               f"--camera=0,0,0,{rx},{ry},{rz},0", "-D", f"explode={ex}"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=out)
        print(f"  {'ok' if r.returncode == 0 else 'FALHA'}    {name}.png")


def cmd_review(path):
    """Portões medidos do conselho (.claude/skills/fusionbrick-council). Sai 1 se algum falha."""
    from fusionbrick.asm import metrics
    asm = A.load(path).compile()
    parts = os.path.join(os.path.dirname(os.path.abspath(path)), "parts")
    print(metrics.review_report(asm, parts))
    return 0 if all(r[4] for r in metrics.gates(asm, parts)) else 1


def cmd_physics(path):
    """Métricas do Engenheiro (fusionbrick.asm.metrics) — usa os STLs de parts/."""
    from fusionbrick.asm import metrics
    asm = A.load(path).compile()
    print(metrics.physics_report(asm, os.path.join(os.path.dirname(os.path.abspath(path)), "parts")))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("ir")
    b = sub.add_parser("build"); b.add_argument("ir")
    b.add_argument("--fn", type=int, default=48)
    b.add_argument("--png", action="store_true")
    b.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2)
    b.add_argument("--force", action="store_true")
    p = sub.add_parser("ports"); p.add_argument("ir"); p.add_argument("part")
    st = sub.add_parser("stats"); st.add_argument("ir")
    ph = sub.add_parser("physics"); ph.add_argument("ir")
    rv = sub.add_parser("review"); rv.add_argument("ir")
    sub.add_parser("schema")
    a = ap.parse_args()
    try:
        if a.cmd == "check":
            return 0 if cmd_check(a.ir).ok else 1
        if a.cmd == "build":
            return cmd_build(a.ir, a.fn, a.png, a.jobs, a.force)
        if a.cmd == "ports":
            asm = A.load(a.ir).compile()
            print(asm.ports_report(a.part))
            return 0
        if a.cmd == "review":
            return cmd_review(a.ir)
        if a.cmd == "physics":
            return cmd_physics(a.ir)
        if a.cmd == "stats":
            asm = A.load(a.ir).compile()
            print(asm.stats_report())
            return 0
        if a.cmd == "schema":
            print(json.dumps(SCHEMA, indent=2, ensure_ascii=False))
            return 0
    except A.IRError as e:
        print(f"ERRO IR  {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
