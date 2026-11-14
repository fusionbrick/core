"""
Verificação estática do add-in, fora do Fusion.

A API `adsk` só existe dentro do Fusion, então não dá para importar
o add-in aqui. O que dá para pegar sem abrir o programa é erro de
sintaxe e manifest inválido — que são a maioria dos erros de
digitação e custam um ciclo inteiro de Stop/Run para descobrir.
"""
import ast
import json
import pathlib
import sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                   else "impl/fusion360/FusionBrick")
bad = 0

for f in sorted(src.glob("*.py")):
    try:
        ast.parse(f.read_text())
        print(f"  sintaxe ok    {f.name}")
    except SyntaxError as e:
        bad += 1
        print(f"  SINTAXE FALHOU {f.name}: linha {e.lineno}: {e.msg}")

for m in sorted(src.glob("*.manifest")):
    try:
        data = json.loads(m.read_text())
        missing = [k for k in ("type", "id", "autodeskProduct")
                   if k not in data]
        if missing:
            bad += 1
            print(f"  MANIFEST INCOMPLETO {m.name}: falta {missing}")
        else:
            print(f"  manifest ok   {m.name}")
    except Exception as e:
        bad += 1
        print(f"  MANIFEST FALHOU {m.name}: {e}")

print("  nota: adsk só existe dentro do Fusion — isto não testa geometria")
sys.exit(1 if bad else 0)
