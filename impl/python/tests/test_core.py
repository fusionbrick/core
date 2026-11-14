import sys, os, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fusionbrick.params import Primitives
from fusionbrick.brick import BrickSpec, FACES
from fusionbrick import rules


class TestDerivation(unittest.TestCase):
    """O grid é derivado. Se estes números mudarem, a spec mudou."""

    def setUp(self):
        self.p = Primitives()

    def test_grid_derives_from_hole_and_wall(self):
        self.assertAlmostEqual(self.p.grid, 8.0)

    def test_derived_values(self):
        self.assertAlmostEqual(self.p.recess_d, 4.8)
        self.assertAlmostEqual(self.p.pin_d, 3.8)
        self.assertAlmostEqual(self.p.collar_d, 4.6)
        self.assertAlmostEqual(self.p.pin_len_max, 2.1)
        self.assertAlmostEqual(self.p.edge_bore_min, 7.2)

    def test_invariants(self):
        # Caem de graça da derivação — se quebrarem, o grid não fecha
        self.assertAlmostEqual(self.p.corner_sliver, self.p.wall)
        self.assertAlmostEqual(self.p.web_between_holes, 2 * self.p.wall)
        self.assertAlmostEqual(self.p.edge_bar, 2.0)

    def test_grid_follows_wall(self):
        # Mudar a parede move o grid inteiro, coerentemente
        q = Primitives(wall=2.4)
        self.assertAlmostEqual(q.grid, 9.6)
        self.assertAlmostEqual(q.corner_sliver, 2.4)
        self.assertAlmostEqual(q.web_between_holes, 4.8)


class TestRules(unittest.TestCase):
    def test_default_is_valid(self):
        self.assertEqual(rules.fatal(Primitives()), [])

    def test_pin_over_ceiling_is_fatal(self):
        v = rules.fatal(Primitives(pin_len=2.5))
        self.assertTrue(any(x.rule == "pin_len_max" for x in v))

    def test_pin_at_ceiling_passes(self):
        self.assertEqual(rules.fatal(Primitives(pin_len=2.1)), [])

    def test_pin_shorter_than_collar_is_fatal(self):
        v = rules.fatal(Primitives(pin_len=0.8))
        self.assertTrue(any(x.rule == "pin_len_vs_collar" for x in v))

    def test_passage_warning_above_tangency(self):
        # tangente em grid/2 - hole_d/2 = 2.0; acima disso avisa
        w = rules.warnings(Primitives(pin_len=2.1))
        self.assertTrue(any(x.rule == "pin_vs_passage" for x in w))
        self.assertEqual(rules.warnings(Primitives(pin_len=2.0)), [])

    def test_fat_recess_bites_edge_bar(self):
        v = rules.fatal(Primitives(collar_w=1.2))
        self.assertTrue(any(x.rule == "recess_vs_edge_bar" for x in v))


class TestBrickGeometry(unittest.TestCase):
    def test_unit_cell_size(self):
        b = BrickSpec()
        self.assertEqual(b.size, (8.0, 8.0, 8.0))

    def test_unit_cell_has_three_bores(self):
        # 1×1×1 com os 3 eixos vazados: um furo por eixo
        self.assertEqual(len(BrickSpec().bores()), 3)

    def test_bores_pass_through_center(self):
        for bore in BrickSpec().bores():
            perp = [i for i in range(3) if i != bore["axis"]]
            for i in perp:
                self.assertAlmostEqual(bore["pos"][i], 4.0)

    def test_unit_cell_has_six_face_features(self):
        self.assertEqual(len(BrickSpec().face_features()), 6)

    def test_recess_requires_bored_axis(self):
        # eixo X sólido -> as faces xn/xp não recebem rebaixo
        b = BrickSpec(axes=("solid", "bored", "bored"))
        got = {f["face"] for f in b.face_features()}
        self.assertNotIn("xn", got)
        self.assertNotIn("xp", got)
        self.assertEqual(len(got), 4)

    def test_auto_face_follows_axis(self):
        b = BrickSpec(axes=("solid", "bored", "bored"))
        self.assertEqual(b.face(0), "plain")
        self.assertEqual(b.face(2), "recess")
        self.assertEqual(b.errors(), [])

    def test_explicit_recess_on_solid_axis_is_error(self):
        b = BrickSpec(axes=("solid", "bored", "bored"),
                      faces=["recess"] + ["auto"] * 5)
        self.assertEqual(len(b.errors()), 1)

    def test_plain_faces_produce_nothing(self):
        b = BrickSpec(faces=["plain"] * 6)
        self.assertEqual(b.face_features(), [])

    def test_cell_centers_follow_grid(self):
        b = BrickSpec(cells=(3, 1, 1))
        self.assertEqual(b.centers(0), [4.0, 12.0, 20.0])

    def test_multicell_bore_count(self):
        # 3×2×1: X -> 2·1=2, Y -> 3·1=3, Z -> 3·2=6
        b = BrickSpec(cells=(3, 2, 1))
        self.assertEqual(len(b.bores()), 2 + 3 + 6)

    def test_face_features_sit_on_the_face_plane(self):
        b = BrickSpec()
        for f in b.face_features():
            a = f["axis"]
            expected = 0.0 if f["normal"][a] < 0 else b.size[a]
            self.assertAlmostEqual(f["pos"][a], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
