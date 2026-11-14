#!/usr/bin/env python3
"""
spec_docs — gera as tabelas de números de spec/params.md a partir do contrato.

As cotas do sistema têm UMA fonte: spec/parts/brick/contracts.toml
(conferida por `make spec-check`). Tabela escrita à mão em .md diverge —
a constituição ficou meses dizendo pin_len = 1.6 "derivado" enquanto o
contrato e as implementações declaravam 2.0. Então as tabelas não se
escrevem mais: geram-se.

    spec_docs.py            regrava o bloco gerado de spec/params.md
    spec_docs.py --check    falha se o bloco estiver desatualizado
"""

import os
import sys

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONTRACT = os.path.join(ROOT, "spec", "parts", "brick", "contracts.toml")
TARGET = os.path.join(ROOT, "spec", "params.md")
BEGIN = "<!-- GERADO por hack/scripts/spec_docs.py a partir de spec/parts/brick/contracts.toml — não edite -->"
END = "<!-- fim do bloco gerado -->"

WHY = {
    "hole_d": "furo passante — a interface mecânica",
    "wall": "parede interna mínima (4 perímetros de 0,4)",
    "collar_w": "degrau radial entre furo e rebaixo (1 bico)",
    "collar_depth": "profundidade axial do rebaixo (5 camadas de 0,2)",
    "tolerance": "folga de press-fit, sempre do macho",
    "gap": "folga mínima entre dois machos que se aproximam",
    "pin_len": "protrusão do macho — **declarado**, com teto `pin_len_max` (constitution.md § 5)",
}


def _mm(v) -> str:
    return f"`{v:g}mm`"


def _formula(f: str) -> str:
    return "`" + f.replace("*", "·").replace("-", "−") + "`"


def block() -> str:
    with open(CONTRACT, "rb") as f:
        c = tomllib.load(f)
    L = [BEGIN, "", "## Primitivos", "", "| Primitivo | Valor | Papel |", "| --- | --- | --- |"]
    L += [f"| `{k}` | {_mm(v)} | {WHY.get(k, '')} |" for k, v in c["primitives"].items()]
    L += ["", "## Derivados", "", "Nenhum é escolhido à mão: mudar um primitivo recalcula todos.", "",
          "| Derivado | Fórmula | Valor | Nota |", "| --- | --- | --- | --- |"]
    L += [f"| `{k}` | {_formula(d['formula'])} | {_mm(d['value'])} | {d.get('note', '')} |"
          for k, d in c["derived"].items()]
    L += ["", "## Invariantes", "", "Caem de graça da derivação; se um quebrar, o grid não fecha.", "",
          "| Invariante | Fórmula | Igual a | Valor | Nota |", "| --- | --- | --- | --- | --- |"]
    L += [f"| `{k}` | {_formula(d['formula'])} | {_formula(d['equals']) if 'equals' in d else '—'} | "
          f"{_mm(d['value'])} | {d.get('note', '')} |" for k, d in c["invariants"].items()]
    L += ["", "## Validações", "", "`fatal` não gera a peça; `warn` gera e avisa.", "",
          "| id | Severidade | Regra | Se falhar |", "| --- | --- | --- | --- |"]
    L += [f"| `{v['id']}` | {v['severity']} | {_formula(v['rule'])} | {v['message']} |"
          for v in c.get("validations", [])]
    return "\n".join(L + ["", END])


def main():
    with open(TARGET) as f:
        text = f.read()
    if BEGIN not in text or END not in text:
        print(f"spec_docs: {TARGET} não tem o bloco gerado (marcadores ausentes)")
        return 2
    a, b = text.index(BEGIN), text.index(END) + len(END)
    new = text[:a] + block() + text[b:]
    if "--check" in sys.argv:
        ok = new == text
        print("  ok    spec/params.md em dia com o contrato" if ok else
              "  FALHA spec/params.md desatualizado — rode `make spec-docs`")
        return 0 if ok else 1
    with open(TARGET, "w") as f:
        f.write(new)
    print("-> spec/params.md (bloco gerado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
