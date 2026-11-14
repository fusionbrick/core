"""
Valida todo nome `adsk.*` usado pelo add-in contra os stubs da API
INSTALADA do Fusion.

Existe porque a API é gerada por SWIG e os nomes não são
adivinháveis: `DimensionOrientations.HorizontalDimension` parece
óbvio e NÃO existe — o certo é `HorizontalDimensionOrientation`.
Descobrir isso dentro do Fusion custa um ciclo Stop/Run inteiro.

Os stubs são lidos por AST, não importados: o `_core.so` depende do
Python que o Fusion embute (3.14) e não carrega no interpretador do
sistema.
"""
import ast
import glob
import os
import pathlib
import sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                   else "impl/fusion360/FusionBrick")

pkgs = sorted(glob.glob(os.path.expanduser(
    "~/Library/Application Support/Autodesk/webdeploy/production/*/"
    "Autodesk Fusion.app/Contents/Api/Python/packages/adsk")))
if not pkgs:
    print("  stubs da API não encontrados — pulei (Fusion instalado?)")
    sys.exit(0)
api = pkgs[-1]


def load_module(name):
    """{Classe: {atributos de classe}} lido do stub."""
    path = os.path.join(api, name + ".py")
    if not os.path.exists(path):
        return None
    tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    out = {}
    # SWIG declara alguns membros FORA da classe, no nível do
    # módulo: `Design.cast = lambda ...`. Sem varrer isso, todo
    # `.cast()` viraria falso positivo.
    extra = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if (isinstance(t, ast.Attribute)
                        and isinstance(t.value, ast.Name)):
                    extra.setdefault(t.value.id, set()).add(t.attr)
        if not isinstance(node, ast.ClassDef):
            continue
        members = set()
        for st in node.body:
            if isinstance(st, ast.Assign):
                for t in st.targets:
                    if isinstance(t, ast.Name):
                        members.add(t.id)
            elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                members.add(st.name)
        out[node.name] = members
    for k, v in extra.items():
        out.setdefault(k, set()).update(v)
    return out


MODS = {}
for m in ("core", "fusion"):
    d = load_module(m)
    if d is not None:
        MODS[m] = d
if not MODS:
    print("  nenhum stub legível — pulei")
    sys.exit(0)


def chain(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return list(reversed(parts))
    return None


bad, seen = 0, set()
for f in sorted(src.glob("*.py")):
    for node in ast.walk(ast.parse(f.read_text())):
        if not isinstance(node, ast.Attribute):
            continue
        c = chain(node)
        if not c or c[0] != "adsk" or len(c) < 3 or c[1] not in MODS:
            continue
        key = ".".join(c)
        if key in seen:
            continue
        seen.add(key)
        classes = MODS[c[1]]
        cls = c[2]
        if cls not in classes:
            bad += 1
            near = [k for k in classes if cls.lower()[:8] in k.lower()]
            print(f"  CLASSE NÃO EXISTE  {key}")
            print(f"     adsk.{c[1]} — parecidas: {sorted(near)[:4]}")
            continue
        if len(c) >= 4 and c[3] not in classes[cls]:
            bad += 1
            near = [k for k in classes[cls] if c[3].lower()[:6] in k.lower()]
            print(f"  ATRIBUTO NÃO EXISTE  {key}")
            print(f"     em {cls} — parecidos: {sorted(near)[:4] or sorted(classes[cls])[:4]}")

print(f"  {len(seen)} nomes adsk.* conferidos contra a API instalada")
sys.exit(1 if bad else 0)
