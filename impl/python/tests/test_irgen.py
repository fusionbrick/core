"""irgen: as macros geram IR que o compilador aceita sem erro."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fusionbrick import assembly as A  # noqa: E402
from fusionbrick.irgen import Build, LIFT_X  # noqa: E402


def compile_(b):
    with tempfile.TemporaryDirectory() as td:
        path = b.write(td)
        try:
            import tomllib  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("tomllib indisponível (Python < 3.11)")
        return A.load(path).compile()


def errors(asm):
    return [f.line() for f in asm.findings if f.severity == "error"]


class TestIrgen(unittest.TestCase):
    def test_ring_closes(self):
        b = Build("t", "anel")
        b.ring("anel", "r", 0, 0, 0, 8, 6)
        asm = compile_(b)
        self.assertTrue(asm.ok, errors(asm))
        self.assertEqual(sum(1 for j in asm.joints if j.kind == "dowel"), 8)

    def test_ring_too_small(self):
        with self.assertRaises(ValueError):
            Build("t", "x").ring("a", "r", 0, 0, 0, 4, 4)

    def test_strut_and_mirror(self):
        b = Build("t", "rampa espelhada")
        b.brick("base", "long_e", (0, 0, 0), (12, 1, 1), **LIFT_X)
        b.brick("base", "pe_e", (1, 0, 1), (1, 1, 1))
        b.strut("rampa", "r_e", (2, 0, 1), (6, 0, 4), base_dir=[-1, 0, 0], top_dir=[1, 0, 0])
        b.brick("rampa", "poste_e", (7, 0, 1), (1, 1, 4))
        b.mirror_y(8)
        for x in (0, 11):
            b.brick("base", f"trav{x}", (x, 1, 0), (1, 6, 1))
        ids = [p["id"] for p in b.parts]
        self.assertIn("long_d", ids)
        self.assertIn("r_d", ids)
        mirrored = next(p for p in b.parts if p["id"] == "r_d")
        self.assertEqual(mirrored["from"], [2, 7, 1])              # a diagonal é UMA peça na IR
        self.assertEqual(next(p for p in b.parts if p["id"] == "long_d")["at"], [0, 7, 0])
        asm = compile_(b)
        self.assertTrue(asm.ok, errors(asm))
        for pid in ("r_d-n0", "r_d-n1", "r_d-v"):                  # … e três no compilador
            self.assertIn(pid, asm.parts)
        self.assertEqual(next(g for g in asm.groups if g["id"] == "rampa")["parts"][:3],
                         ["r_e-n0", "r_e-n1", "r_e-v"])

    def test_arch_on_beams(self):
        b = Build("t", "arco sobre duas vigas")
        b.brick("base", "v0", (0, 0, 0), (6, 1, 1))
        b.brick("base", "v1", (0, 9, 0), (6, 1, 1))
        for x in (0, 5):
            b.brick("base", f"t{x}", (x, 1, 0), (1, 8, 1))
        b.arch("arco", "a", 2, 0, 9, 1, 5)
        asm = compile_(b)
        self.assertTrue(asm.ok, errors(asm))

    def test_ring_splits_long_beams(self):
        b = Build("t", "anel longo")
        b.ring("anel", "r", 0, 0, 0, 40, 8)
        ids = [p["id"] for p in b.parts]
        self.assertIn("r-s0", ids)
        self.assertIn("r-s1", ids)
        self.assertTrue(all(max(p["size"]) <= 26 for p in b.parts if p["type"] == "brick"))
        asm = compile_(b)
        self.assertTrue(asm.ok, errors(asm))

    def test_ring_split_plain_needs_support(self):
        b = Build("t", "anel longo sobre deck")
        b.brick("deck", "d", (0, 0, 0), (40, 8, 1), axes="z")
        b.ring("anel", "r", 0, 0, 1, 40, 8, split="plain", faces={"zn": "pin"})
        asm = compile_(b)
        self.assertTrue(asm.ok, errors(asm))
        self.assertNotIn("r-s1", [w for f in asm.findings if f.code == "ASM-012" for w in [f.msg.split(":")[0]]])

    def test_toml_speaks_public_names(self):
        b = Build("t", "nomes", hero_rz=125)                       # nomes antigos no gen.py…
        b.liftarm("g", "v", (0, 0, 0), (6, 1, 1), studs="up")
        b.brick("g", "p", (0, 0, 1), (4, 1, 1), axes="z", faces={"zn": "pin"}, plain=["xn"])
        b.bend("g", "c", (6, 0, 0), (1, 0, 0), (0, 1, 0), k=1)
        b.mock("g", "bat", (0, 2, 0), (48, 26, 17))
        text = b.toml()                                            # … viram os atuais no TOML
        for new in ('type = "beam"', 'studs = "top"', 'holes = "z"', 'bottom = "stud"', 'flat = ["back"]',
                    'type = "curve"', "radius = 2", 'type = "component"', "size_mm = ", "view_angle = 125"):
            self.assertIn(new, text)
        for old in ("liftarm", "mock", "bend", "cells", "axes", '"zn"', '"pin"', "hero_rz"):
            self.assertNotIn(old, text)

    def test_duplicate_id(self):
        b = Build("t", "x")
        b.brick("g", "a", (0, 0, 0), (1, 1, 1))
        with self.assertRaises(ValueError):
            b.brick("g", "a", (1, 0, 0), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
