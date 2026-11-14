"""
Confere `contracts.toml` de uma peça contra as implementações.

Existe porque as fórmulas de derivação estavam escritas à mão em
quatro lugares independentes (tabelas da spec, cabeçalho de cada
.scad, params.py, bloco awk do variables.mk) e divergiram sem
ninguém notar: a spec dizia `pin_len = 1.6` derivado enquanto as
quatro implementações declaravam `2.0`.

Quatro checagens:

  1. auto-consistência  fórmula avalia para o `value` declarado
  2. core Python        impl/python/fusionbrick/params.py
  3. OpenSCAD           echos de impl/openscad/<peça>.scad
  4. make               derivados de `make vars`
  5. casos              comportamento: cells, axis, face, thickness,
                        center — conferido no core e no echo do .scad

Falha aponta QUAL cópia divergiu e de quanto.

stdlib only: `tomllib` desde 3.11. Nada de PyYAML — o core roda
dentro do Fusion, onde instalar dependência é hostil.
"""

import math
import os
import re
import subprocess
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOL = 1e-9

# Ambiente de avaliação das fórmulas. Sem builtins: as fórmulas
# são dado versionado do repo, não entrada externa, mas restringir
# é barato e evita que um contrato vire vetor de execução.
SAFE = {"__builtins__": {}, "sqrt": math.sqrt, "min": min, "max": max}


class Report:
    def __init__(self):
        self.fail = 0
        self.checks = 0

    def ok(self, what, detail=""):
        self.checks += 1
        print(f"    ok    {what}{('  ' + detail) if detail else ''}")

    def bad(self, what, detail):
        self.checks += 1
        self.fail += 1
        print(f"    FALHA {what}  {detail}")

    def near(self, what, got, want, unit="mm"):
        if got is None:
            self.bad(what, "não encontrado na implementação")
        elif abs(got - want) < TOL:
            self.ok(what, f"{got:g}{unit}")
        else:
            self.bad(what, f"contrato {want:g}{unit} != impl {got:g}{unit} "
                           f"(dif {got - want:+g})")


def resolve(contract):
    """Avalia primitivos e derivados na ordem em que fecham."""
    env = dict(contract.get("primitives", {}))
    pending = dict(contract.get("derived", {}))
    # Resolução por passadas: uma derivada pode depender de outra
    # (collar_d usa recess_d). Sem ordenar à mão.
    for _ in range(len(pending) + 2):
        if not pending:
            break
        for name in list(pending):
            try:
                env[name] = eval(pending[name]["formula"], SAFE, env)
                del pending[name]
            except NameError:
                continue
    if pending:
        raise SystemExit(
            "  fórmulas não resolvem (dependência circular ou nome "
            f"desconhecido): {sorted(pending)}")
    for name, spec in contract.get("invariants", {}).items():
        env[name] = eval(spec["formula"], SAFE, env)
    return env


def check_self(contract, env, r):
    """1. A fórmula bate com o `value` que o contrato declara?"""
    print("  [1] auto-consistência do contrato")
    for section in ("derived", "invariants"):
        for name, spec in contract.get(section, {}).items():
            got = env[name]
            want = spec["value"]
            if abs(got - want) > TOL:
                r.bad(f"{name}", f"fórmula `{spec['formula']}` dá {got:g}, "
                                 f"mas value diz {want:g}")
            else:
                r.ok(name, f"{spec['formula']} = {got:g}")
            if "equals" in spec:
                alias = eval(spec["equals"], SAFE, env)
                if abs(alias - got) > TOL:
                    r.bad(f"{name} equals",
                          f"`{spec['equals']}` = {alias:g} != {got:g}")

    print("  [1b] validações do contrato, com os valores atuais")
    for v in contract.get("validations", []):
        passed = bool(eval(v["rule"], SAFE, env))
        if passed:
            r.ok(v["id"], v["rule"])
        elif v["severity"] == "fatal":
            r.bad(v["id"], f"{v['rule']} — {v['message']}")
        else:
            r.checks += 1
            print(f"    aviso {v['id']}  {v['message']}")


def check_python(env, r):
    """2. O core Python produz os mesmos números?"""
    print("  [2] core Python  impl/python/fusionbrick/params.py")
    sys.path.insert(0, os.path.join(ROOT, "impl", "python"))
    try:
        from fusionbrick.params import Primitives
    except Exception as e:
        r.bad("import do core", str(e))
        return
    p = Primitives()
    for name in ("hole_d", "wall", "collar_w", "collar_depth",
                 "tolerance", "gap", "pin_len", "grid", "recess_d",
                 "pin_d", "collar_d", "inset", "pin_len_max",
                 "edge_bore_min", "corner_sliver", "edge_bar"):
        if name in env:
            r.near(name, getattr(p, name, None), env[name])
    if "web_between_holes" in env:
        r.near("web_between_holes", p.web_between_holes,
               env["web_between_holes"])


# Os echos do .scad são prosa; estes padrões extraem os números.
# Casar por rótulo em vez de posição sobrevive a mudança de texto.
SCAD_PATTERNS = {
    "grid":              r"grid\s+([\d.]+)",
    "recess_d":          r"rebaixo\s+Ø([\d.]+)",
    "pin_d":             r"pino\s+Ø([\d.]+)",
    "collar_d":          r"colar\s+Ø([\d.]+)",
    "corner_sliver":     r"Lasca na quina\s*:\s*([\d.]+)",
    "web_between_holes": r"Alma entre furos\s*:\s*([\d.]+)",
    "edge_bar":          r"Barra da aresta\s*:\s*([\d.]+)",
    "shaft_len":         r"Haste além do colar\s*:\s*([\d.]+)",
}


def check_openscad(part, env, r):
    """3. Os echos do .scad produzem os mesmos números?"""
    scad = os.path.join(ROOT, "impl", "openscad", part + ".scad")
    print(f"  [3] OpenSCAD  impl/openscad/{part}.scad")
    if not os.path.exists(scad):
        r.bad("arquivo", f"não existe: {scad}")
        return
    try:
        out = subprocess.run(
            ["openscad", "-o", os.devnull, "--export-format", "binstl",
             "-D", f"pin_len={env['pin_len']:g}", scad],
            capture_output=True, text=True, timeout=300).stderr
    except FileNotFoundError:
        print("    pulei  openscad não instalado")
        return
    except subprocess.TimeoutExpired:
        r.bad("render", "openscad estourou o tempo")
        return
    for name, pat in SCAD_PATTERNS.items():
        if name not in env:
            continue
        m = re.search(pat, out)
        r.near(name, float(m.group(1)) if m else None, env[name])


def check_cases(contract, part, r):
    """
    5. Os casos do contrato produzem o comportamento declarado?

    Os primitivos são números com fórmula. `cells`, `axis`, `face`,
    `thickness` e `center` não têm valor para conferir — têm
    CONSEQUÊNCIA. Um caso nomeia a configuração e o que ela deve
    produzir, e isso é conferido nas duas implementações.

    Sem framework: o core Python já calcula (`BrickSpec`) e o .scad
    já ecoa o tamanho. É a mesma comparação de número de sempre,
    sobre outra pergunta.
    """
    cases = contract.get("cases", [])
    if not cases:
        return
    print("  [5] casos de comportamento")
    sys.path.insert(0, os.path.join(ROOT, "impl", "python"))
    try:
        from fusionbrick.brick import BrickSpec
        from fusionbrick.params import Primitives
    except Exception as e:
        r.bad("import do core", str(e))
        return

    for c in cases:
        cid, prm, exp = c["id"], c.get("params", {}), c["expect"]
        cells = tuple(prm.get(f"cells_{a}", 1) for a in "xyz")
        axes = tuple(prm.get(f"axis_{a}", "bored") for a in "xyz")
        FACE_ORDER = ("xn", "xp", "yn", "yp", "zn", "zp")
        default = prm.get("faces", "auto")
        faces = [prm.get(f"face_{f}", default) for f in FACE_ORDER]
        b = BrickSpec(cells=cells, axes=axes, faces=faces)

        # laje: o core não modela `thickness`; o Z vira a espessura
        size = list(b.size)
        if prm.get("thickness"):
            size[2] = prm["thickness"]

        if "size" in exp:
            for i, ax in enumerate("XYZ"):
                r.near(f"{cid}.size{ax}", size[i], exp["size"][i])
        if "bores" in exp:
            n = len(b.bores()) if not prm.get("thickness") else \
                len(b.centers(0)) * len(b.centers(1))
            r.near(f"{cid}.bores", float(n), float(exp["bores"]), "")
        if "face_features" in exp:
            n = len(b.face_features()) if not prm.get("thickness") else \
                2 * len(b.centers(0)) * len(b.centers(1))
            r.near(f"{cid}.faces", float(n), float(exp["face_features"]), "")
        if "live_z_holes" in exp:
            n = _live_holes(part, prm)
            r.near(f"{cid}.furos_vivos", n, float(exp["live_z_holes"]), "")

        # o .scad concorda com o tamanho?
        got = _scad_size(part, prm)
        if got and "size" in exp:
            for i, ax in enumerate("XYZ"):
                r.near(f"{cid}.scad.{ax}", got[i], exp["size"][i])


def _scad_args(prm):
    out = []
    for k, v in prm.items():
        if k == "faces":
            out += [a for f in ("xn", "xp", "yn", "yp", "zn", "zp")
                    for a in ("-D", f'face_{f}="{v}"')]
        elif isinstance(v, str):
            out += ["-D", f'{k}="{v}"']
        else:
            out += ["-D", f"{k}={v:g}"]
    return out


def _render(part, prm):
    scad = os.path.join(ROOT, "impl", "openscad", part + ".scad")
    try:
        return subprocess.run(
            ["openscad", "-o", os.devnull, "--export-format", "binstl"]
            + _scad_args(prm) + [scad],
            capture_output=True, text=True, timeout=300).stderr
    except Exception:
        return ""


def _scad_size(part, prm):
    m = re.search(r"(?:Bloco|Laje)\s+([\d.]+) × ([\d.]+) × ([\d.]+)mm",
                  _render(part, prm))
    return [float(m.group(i)) for i in (1, 2, 3)] if m else None


def _live_holes(part, prm):
    m = re.search(r"furos vivos: (\d+)", _render(part, prm))
    return float(m.group(1)) if m else None


def env_overrides():
    """
    O que o `.env` local sobrepõe.

    `.env` é config da máquina, gitignored — divergência vinda dali
    não é bug do repo, é experimento deliberado de quem está
    mexendo. O check informa em vez de reprovar; reprovar tornaria
    `make spec-check` inútil justamente para quem está calibrando.
    """
    path = os.path.join(ROOT, ".env")
    out = {}
    if not os.path.exists(path):
        return out
    for i, line in enumerate(open(path), 1):
        m = re.match(r"\s*([A-Z_]+)\s*=\s*([\d.]+)\s*$", line)
        if m:
            out[m.group(1).lower()] = (float(m.group(2)), i)
    return out


def check_make(env, r):
    """4. Os derivados do make batem?"""
    print("  [4] make vars  hack/automations/variables.mk")
    local = env_overrides()
    try:
        out = subprocess.run(["make", "vars"], cwd=ROOT,
                             capture_output=True, text=True,
                             timeout=120).stdout
    except Exception as e:
        r.bad("make vars", str(e))
        return
    for name in ("grid", "recess_d", "pin_d", "collar_d",
                 "pin_len", "pin_len_max"):
        if name not in env:
            continue
        m = re.search(rf"^\s*{re.escape(name)}\s+([\d.]+)", out, re.M)
        got = float(m.group(1)) if m else None
        if name in local and got is not None and abs(got - env[name]) > TOL:
            val, line = local[name]
            r.checks += 1
            print(f"    local {name}  {got:g}mm — .env:{line} "
                  f"sobrepõe o contrato ({env[name]:g}mm)")
            continue
        r.near(name, got, env[name])


def main():
    parts = sys.argv[1:] or ["brick"]
    total = Report()
    for part in parts:
        path = os.path.join(ROOT, "spec", "parts", part, "contracts.toml")
        print(f"\n=== {part}  ({os.path.relpath(path, ROOT)}) ===")
        if not os.path.exists(path):
            print(f"  sem contracts.toml — peça ainda não convertida")
            continue
        with open(path, "rb") as f:
            contract = tomllib.load(f)
        env = resolve(contract)
        check_self(contract, env, total)
        check_python(env, total)
        check_openscad(part, env, total)
        check_make(env, total)
        check_cases(contract, part, total)

    print(f"\n{total.checks} checagens, {total.fail} falha(s)")
    if total.fail:
        print("\nDivergência entre contrato e implementação é BUG. "
              "Não escolha em silêncio: ou o contrato está errado, "
              "ou a implementação está.")
    return 1 if total.fail else 0


if __name__ == "__main__":
    sys.exit(main())
