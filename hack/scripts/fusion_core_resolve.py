"""
Reproduz a resolução do core como o Fusion faz, a partir do caminho
INSTALADO (symlink ou cópia).

Existe porque `abspath` não resolve symlink: em desenvolvimento o
add-in é um link dentro de AddIns/, e o caminho do core caía em
API/python — que não existe. O erro só aparecia ao abrir o diálogo,
dentro do Fusion. Este script pega antes.
"""
import os
import sys

installed = sys.argv[1] if len(sys.argv) > 1 else None
if not installed or not os.path.exists(installed):
    print("  add-in não instalado — pulei (rode `make fusion-link`)")
    sys.exit(0)

entry = os.path.join(installed, "BrickCommand.py")
here = os.path.dirname(os.path.realpath(entry))
candidates = (here, os.path.normpath(os.path.join(here, "..", "..", "python")))

hit = next((c for c in candidates
            if os.path.isdir(os.path.join(c, "fusionbrick"))), None)
if not hit:
    print("  CORE NÃO ENCONTRADO a partir de:", installed)
    for c in candidates:
        print("    procurei em:", c)
    sys.exit(1)

sys.path.insert(0, hit)
from fusionbrick.params import Primitives
p = Primitives()
print(f"  core resolvido: {hit}")
print(f"  import ok: grid={p.grid:g} rebaixo={p.recess_d:g} macho={p.pin_d:g}")
