#!/usr/bin/env python3
"""
Paridade do compilador (studio spec 003 D-3).

Para cada examples/*/assembly.toml, grava um JSON com a IR de entrada e o
que o compilador Python produz: achados, juntas, BOM, passos e stats. O
Studio porta o compilador para TypeScript e o teste dele exige igualdade
com estes arquivos — o exemplo muda aqui, regenera, o teste pega.

    python3 hack/scripts/fb_export_parity.py <pasta de saída>
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "impl", "python"))

import tomllib  # noqa: E402

from fusionbrick.asm import Assembly  # noqa: E402
from fusionbrick.asm import outputs as O  # noqa: E402


def export(toml_path: str) -> dict:
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    asm = Assembly(data).compile()
    steps, _, _ = O.steps(asm)
    return {
        "input": data,
        "ok": asm.ok,
        "findings": [[f.severity, f.code, f.msg, f.hint] for f in asm.findings],
        "joints": [[j.kind, j.a, j.b, j.axis, list(j.pos)] for j in asm.joints],
        "bom": [{"key": r["key"], "scad": r["scad"], "params": r["params"], "count": r["count"], "ids": r["ids"]}
                for r in asm.bom()],
        "steps": steps,
        "stats": asm.stats(),
        "summary": asm.summary(),
    }


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "parity"
    os.makedirs(out_dir, exist_ok=True)
    root = os.path.join(HERE, "..", "..", "examples")
    for path in sorted(glob.glob(os.path.join(root, "*", "assembly.toml"))):
        name = os.path.basename(os.path.dirname(path))
        with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
            json.dump(export(path), f, ensure_ascii=False, indent=1)
        print(f"✓ {name}")


if __name__ == "__main__":
    main()
