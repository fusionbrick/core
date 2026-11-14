#!/usr/bin/env python3
"""
fb_migrate — reescreve um assembly.toml escrito à mão com os nomes atuais
(`impl/python/fusionbrick/asm/names.py`), preservando comentários e layout.

    python3 hack/scripts/fb_migrate.py examples/meu/assembly.toml [...]

Os nomes antigos continuam compilando; isto só deixa o arquivo legível
no vocabulário novo. TOML gerado por gen.py: migre o gen.py e gere de novo.
"""
import re
import sys

TYPES = {"liftarm": "beam", "tile": "cover", "bend": "curve", "mock": "component"}
FACES = {"xp": "front", "xn": "back", "yp": "left", "yn": "right", "zp": "top", "zn": "bottom"}
KINDS = {"pin": "stud", "recess": "socket", "plain": "flat"}
BRICK_KEYS = {"cells": "size", "axes": "holes", "round": "rounded", "pin_cells": "studs_on"}
BRICKS = ("brick", "beam", "plate", "cover")


def key(line, old, new):
    return re.sub(rf"(?<![\w.]){old}(\s*=)", rf"{new}\1", line)


def migrate_line(line: str) -> str:
    if line.lstrip().startswith("#"):
        return line
    m = re.search(r'type\s*=\s*"(\w+)"', line)
    t = m.group(1) if m else ("brick" if re.search(r"\bcells\s*=", line) else None)
    if t == "beam" and re.search(r"\bfrom\s*=", line):
        t = "strut"
    t = TYPES.get(t, t)
    if m:
        line = line[:m.start(1)] + t + line[m.end(1):]
    line = key(line, "hero_rz", "view_angle")
    line = key(line, "dowel_step", "dowel_every")
    if t in BRICKS:
        for old, new in BRICK_KEYS.items():
            line = key(line, old, new)
        line = re.sub(r'studs\s*=\s*"up"', 'studs = "top"', line)
        line = re.sub(r'studs\s*=\s*"down"', 'studs = "bottom"', line)
        if not re.search(r"\bstuds\s*=", line):
            line = key(line, "pins", "studs")
        line = re.sub(r"(?<![\w.])plain(\s*=\s*\[)", r"flat\1", line)
    elif t == "wheel":
        line = key(line, "cells", "diameter")
    elif t == "component":
        line = key(line, "size", "size_mm")
    elif t == "curve":
        line = re.sub(r"(?<![\w.])k\s*=\s*(\d+)", lambda k: f"radius = {int(k.group(1)) + 1}", line)
    elif t == "strut":
        line = line.replace('style = "liftarm"', 'style = "beam"')
    for code, name in FACES.items():
        line = re.sub(rf"(?<![\w.]){code}(\s*=)", rf"{name}\1", line)          # faces = { zn = … }
        line = re.sub(rf'"{code}"', f'"{name}"', line)                         # listas de faces
        line = re.sub(rf'(on\s*=\s*"[^"]*)\.{code}"', rf'\1.{name}"', line)    # roda
    for old, new in KINDS.items():
        line = line.replace(f'"{old}"', f'"{new}"')
    return line


def migrate(text: str) -> str:
    return "".join(migrate_line(l) for l in text.splitlines(keepends=True))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path) as f:
            src = f.read()
        out = migrate(src)
        if out != src:
            with open(path, "w") as f:
                f.write(out)
        print(("migrado  " if out != src else "já atual ") + path)
