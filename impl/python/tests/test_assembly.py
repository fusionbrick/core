"""
Testes do compilador de montagem — uma regra ASM por teste.

    cd impl/python && python3 -m unittest tests.test_assembly
"""

import unittest

from fusionbrick.assembly import Assembly


from fusionbrick import assembly as A  # noqa: E402


def build(*parts, **extra):
    data = {"assembly": {"name": "t"}, "parts": list(parts)}
    data.update(extra)
    return Assembly(data).compile()


def codes(asm, sev="error"):
    return [f.code for f in asm.findings if f.severity == sev]


def B(id, at, cells=(1, 1, 1), **kw):
    d = {"id": id, "type": "brick", "at": list(at), "cells": list(cells)}
    d.update(kw)
    return d


# Base 3×2 com uma viga de 3 em cima, machos para baixo
BASE = B("base", (0, 0, 0), (3, 2, 1), axes="z")
TOP = B("top", (0, 0, 1), (3, 1, 1), axes="xz", faces={"zn": "pin"})


class TestPorts(unittest.TestCase):
    def test_pin_into_recess_is_integral_joint(self):
        a = build(BASE, TOP)
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(sum(j.kind == "integral" for j in a.joints), 3)

    def test_recess_recess_inserts_dowel(self):
        a = build(BASE, B("top", (0, 0, 1), (3, 1, 1), axes="xz"))
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(sum(j.kind == "dowel" for j in a.joints), 3)

    def test_pin_against_plain_is_error(self):
        a = build(B("base", (0, 0, 0), (3, 2, 1), axes="none"), TOP)
        self.assertIn("ASM-003", codes(a))

    def test_pin_against_pin_is_error(self):
        base = B("base", (0, 0, 0), (3, 2, 1), axes="z", faces={"zp": "pin"})
        self.assertIn("ASM-003", codes(build(base, TOP)))

    def test_explicit_recess_on_solid_axis_is_error(self):
        a = build(B("x", (0, 0, 0), axes="yz", faces={"xn": "recess"}))
        self.assertIn("REQ-005", codes(a))


class TestOccupancy(unittest.TestCase):
    def test_overlap_is_error(self):
        a = build(BASE, B("o", (2, 1, 0)))
        self.assertIn("ASM-002", codes(a))

    def test_xy_must_be_integer(self):
        self.assertIn("ASM-001", codes(build(B("a", (0.5, 0, 0)))))


class TestStructure(unittest.TestCase):
    def test_loose_part_is_error(self):
        a = build(BASE, B("far", (10, 0, 0)))
        self.assertIn("ASM-005", codes(a))

    def test_contact_without_joint_does_not_connect(self):
        # apoio plain × plain: encosta, não junta
        a = build(B("a", (0, 0, 0), axes="none"), B("b", (0, 0, 1), axes="none"))
        self.assertIn("ASM-005", codes(a))

    def test_single_coaxial_joints_rotate(self):
        # poste 1×1×1 entre base e teto: as duas junções na mesma linha Z
        a = build(B("base", (0, 0, 0), (3, 1, 1), axes="z"),
                  B("post", (1, 0, 1), axes="z"),
                  B("roof", (0, 0, 2), (3, 1, 1), axes="z"))
        # o poste é membro de treliça (gira só sobre si); a base, presa
        # por UMA cavilha, gira de verdade
        errs = [f for f in a.findings if f.code == "ASM-004" and f.severity == "error"]
        self.assertFalse(any(f.msg.startswith("post") for f in errs), a.summary())
        self.assertTrue(any(f.msg.startswith("base") for f in errs), a.summary())

    def test_hinge_declaration_silences_rotation(self):
        a = build(B("base", (0, 0, 0), (3, 1, 1), axes="z"),
                  B("post", (1, 0, 1), axes="z"),
                  B("roof", (0, 0, 2), (3, 1, 1), axes="z"),
                  hinges=["post"])
        # base e teto também giram: cada um tem uma cavilha só
        msgs = [f.msg for f in a.findings if f.code == "ASM-004"]
        self.assertFalse(any(m.startswith("post") for m in msgs))
        self.assertTrue(any(m.startswith("base") for m in msgs))

    def test_two_cells_of_contact_are_rigid(self):
        a = build(BASE, B("top", (0, 0, 1), (2, 1, 1), axes="xz", faces={"zn": "pin"}))
        self.assertNotIn("ASM-004", codes(a))


class TestSharedBore(unittest.TestCase):
    def test_slab_4mm_both_sides_same_hole_is_error(self):
        slab = B("slab", (0, 0, 1), (3, 1, 1), thickness=4.0, axes="z")
        below = B("below", (0, 0, 0), (3, 1, 1), axes="xz", faces={"zp": "pin"})
        above = B("above", (0, 0, 1.5), (3, 1, 1), axes="xz", faces={"zn": "pin"})
        self.assertIn("ASM-006", codes(build(below, slab, above)))

    def test_full_cell_takes_both_sides(self):
        mid = B("mid", (0, 0, 1), (3, 1, 1), axes="z")
        below = B("below", (0, 0, 0), (3, 1, 1), axes="xz", faces={"zp": "pin"})
        above = B("above", (0, 0, 2), (3, 1, 1), axes="xz", faces={"zn": "pin"})
        self.assertNotIn("ASM-006", codes(build(below, mid, above)))


class TestRoutes(unittest.TestCase):
    def test_route_through_integral_pin_is_error(self):
        a = build(BASE, TOP, routes=[{"id": "fio", "path": [[0, 0, 0], [0, 0, 1]]}])
        self.assertIn("ASM-007", codes(a))

    def test_route_keeps_port_open(self):
        top = B("top", (0, 0, 1), (3, 1, 1), axes="xz")
        a = build(BASE, top, routes=[{"id": "fio", "path": [[0, 0, 0], [0, 0, 1]]}])
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(sum(j.kind == "dowel" for j in a.joints), 2)

    def test_route_through_solid_axis_is_error(self):
        a = build(BASE, TOP, routes=[{"id": "fio", "path": [[0, 0, 0], [2, 0, 0]]}])
        self.assertIn("ASM-007", codes(a))


class TestWheels(unittest.TestCase):
    CHASSIS = B("ch", (0, 0, 0), (6, 3, 1), axes="xyz")

    def wheel(self, at, on="ch.yn", **kw):
        d = {"id": "w", "type": "wheel", "at": list(at), "on": on, "cells": 4}
        d.update(kw)
        return d

    def test_wheel_on_recess_port(self):
        a = build(self.CHASSIS, self.wheel((1, -1, 0)))
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(sum(j.kind == "axle" for j in a.joints), 1)

    def test_wheel_on_solid_face_is_error(self):
        ch = B("ch", (0, 0, 0), (6, 3, 1), axes="xz")
        self.assertIn("ASM-010", codes(build(ch, self.wheel((1, -1, 0)))))

    def test_wheel_must_touch_face(self):
        self.assertIn("ASM-010", codes(build(self.CHASSIS, self.wheel((1, -2, 0)))))

    def test_wheels_too_close_touch(self):
        w1 = self.wheel((1, -1, 0)); w1["id"] = "w1"
        w2 = self.wheel((3, -1, 0)); w2["id"] = "w2"
        self.assertIn("ASM-002", codes(build(self.CHASSIS, w1, w2)))

    def test_wheel_hitting_part_is_error(self):
        side = B("side", (0, -1, 2), (1, 1, 1), axes="xyz")
        a = build(self.CHASSIS, side, self.wheel((1, -1, 0)))
        self.assertIn("ASM-002", codes(a))


def N(id, at, dirs, ports="pin"):
    return {"id": id, "type": "node", "at": list(at), "dirs": [list(d) for d in dirs], "ports": ports}


class TestFreeForm(unittest.TestCase):
    # Dois nós sobre uma base, ligados por uma viga 3-4-5
    BASE = B("base", (0, 0, 0), (8, 1, 1), axes="xz")

    def frame(self, top_at=(3, 0, 5), extra=()):
        # lo na base; hi preso numa barra que desce por um poste.
        # Poste logo abaixo de hi colidiria com a ponta da viga.
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (3, 0, 4)])
        hi = N("hi", top_at, [(1, 0, 0), (-3, 0, -4)])
        bar = B("bar", (4, 0, 5), (4, 1, 1), axes="xz", faces={"zn": "pin"})
        post = B("post", (7, 0, 1), (1, 1, 4), axes="z", faces={"zn": "pin"})
        beam = {"id": "viga", "type": "beam", "from": "lo", "to": "hi"}
        return build(self.BASE, lo, hi, bar, post, beam, *extra)

    def test_pythagorean_beam_compiles(self):
        a = self.frame()
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(a.parts["viga"].cells[0], 4)          # 5 − 1
        self.assertEqual(sum(j.kind == "integral" for j in a.joints), 6)

    def test_non_integer_length_is_error(self):
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (1, 0, 1)])
        hi = N("hi", (3, 0, 4), [(-1, 0, -1), (0, 0, -1)])
        beam = {"id": "viga", "type": "beam", "from": "lo", "to": "hi"}
        self.assertIn("ASM-008", codes(build(self.BASE, lo, hi, beam)))

    def test_node_without_port_toward_beam(self):
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (1, 0, 0)])
        hi = N("hi", (3, 0, 5), [(0, 0, -1), (-3, 0, -4)])
        beam = {"id": "viga", "type": "beam", "from": "lo", "to": "hi"}
        self.assertIn("ASM-008", codes(build(self.BASE, lo, hi, beam)))

    def test_post_under_node_hits_beam_end(self):
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (3, 0, 4)])
        hi = N("hi", (3, 0, 5), [(0, 0, -1), (-3, 0, -4)])
        post = B("post", (3, 0, 1), (1, 1, 4), axes="z", faces={"zn": "pin"})
        beam = {"id": "viga", "type": "beam", "from": "lo", "to": "hi"}
        self.assertIn("ASM-002", codes(build(self.BASE, lo, hi, post, beam)))

    def test_node_arm_at_90_degrees_hits_beam(self):
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (3, 0, 4), (0, 1, 0)])
        hi = N("hi", (3, 0, 5), [(1, 0, 0), (-3, 0, -4)])
        bar = B("bar", (4, 0, 5), (4, 1, 1), axes="xz", faces={"zn": "pin"})
        post = B("post", (7, 0, 1), (1, 1, 4), axes="z", faces={"zn": "pin"})
        beam = {"id": "viga", "type": "beam", "from": "lo", "to": "hi"}
        a = build(self.BASE, lo, hi, bar, post, beam)
        msgs = [f.msg for f in a.findings if f.code == "ASM-008"]
        self.assertTrue(any("[0, 1, 0]" in m for m in msgs), a.summary())

    def test_node_fillet_bigger_than_cell_is_error(self):
        lo = N("lo", (0, 0, 1), [(0, 0, -1), (3, 0, 4)])
        lo["fillet"] = 4.0
        self.assertIn("ASM-002", codes(build(self.BASE, lo)))

    def test_beam_through_part_collides(self):
        wall = B("wall", (1, 0, 2), (1, 1, 1), axes="z")
        a = self.frame(extra=[wall])
        self.assertIn("ASM-002", codes(a))

    def test_mock_collision(self):
        m = {"id": "bat", "type": "mock", "at": [5, 0, 0.5], "size": [20, 8, 8]}
        self.assertIn("ASM-002", codes(self.frame(extra=[m])))

    def test_mock_is_not_printed_nor_connected(self):
        m = {"id": "bat", "type": "mock", "at": [4, 0, 1], "size": [16, 8, 6]}
        a = self.frame(extra=[m])
        self.assertTrue(a.ok, a.summary())
        self.assertFalse(any("bat" in r["ids"] for r in a.bom()))

    def test_beam_is_truss_member(self):
        a = self.frame()
        infos = [f for f in a.findings if f.code == "ASM-004"]
        self.assertTrue(all(f.severity == "info" for f in infos))


class TestDetail(unittest.TestCase):
    def test_edge_pins_mate_only_on_frame(self):
        # tampa 4×4 sobre um quadro: machos só no perímetro, miolo liso
        frame = [B("f0", (0, 0, 0), (4, 1, 1), axes="z"), B("f1", (0, 3, 0), (4, 1, 1), axes="z"),
                 B("f2", (0, 1, 0), (1, 2, 1), axes="z"), B("f3", (3, 1, 0), (1, 2, 1), axes="z")]
        lid = B("lid", (0, 0, 1), (4, 4, 1), axes="none", faces={"zn": "pin"}, pin_cells="edge")
        a = build(*frame, lid)
        self.assertNotIn("ASM-011", codes(a, "info"), a.summary())   # nenhum macho livre
        self.assertEqual(sum(j.kind == "integral" for j in a.joints), 12)

    def test_dowel_step_thins_dowels_keeps_ends(self):
        a1 = build(B("a", (0, 0, 0), (9, 1, 1), axes="z"), B("b", (0, 0, 1), (9, 1, 1), axes="z"))
        data = {"assembly": {"name": "t", "dowel_step": 3},
                "parts": [B("a", (0, 0, 0), (9, 1, 1), axes="z"), B("b", (0, 0, 1), (9, 1, 1), axes="z")]}
        a3 = Assembly(data).compile()
        self.assertEqual(sum(j.kind == "dowel" for j in a1.joints), 9)
        self.assertEqual(sum(j.kind == "dowel" for j in a3.joints), 4)   # 0, 3, 6, 8
        self.assertTrue(a3.ok, a3.summary())

    def test_pin_on_round_face_is_error(self):
        a = build(B("a", (0, 0, 0), (6, 1, 1), axes="xyz", round="y", faces={"zn": "pin"}))
        self.assertIn("REQ-010", codes(a))


class TestPinInner(unittest.TestCase):
    """pin_cells = "inner": liftarm empilhado com machos só nas células planas."""

    def stack(self, pc):
        lift = dict(round="y", corner_r=4.0)
        faces = {"zp": "pin"}
        top = B("cima", (0, 0, 1), (6, 1, 1), **lift)
        low = B("baixo", (0, 0, 0), (6, 1, 1), faces=faces, **lift)
        if pc:
            low["pin_cells"] = pc
        return A.Assembly({"assembly": {"name": "t"}, "parts": [low, top]}).compile()

    def test_pin_on_round_face_still_rejected(self):
        self.assertIn("REQ-010", [f.code for f in self.stack(None).findings if f.severity == "error"])

    def test_inner_makes_integral_joints(self):
        a = self.stack("inner")
        self.assertTrue(a.ok, [f.line() for f in a.findings if f.severity == "error"])
        self.assertEqual(sum(1 for j in a.joints if j.kind == "integral"), 4)   # 6 células − 2 pontas
        self.assertEqual(sum(1 for j in a.joints if j.kind == "dowel"), 0)


class TestInsertion(unittest.TestCase):
    """ASM-012: cada peça entra nas anteriores com um movimento só."""

    def parts(self):
        return [B("a", (0, 0, 0), (1, 4, 1)), B("meio", (1, 0, 0), (2, 1, 1)), B("b", (3, 0, 0), (1, 4, 1))]

    def warns(self, groups):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": self.parts(), "groups": groups}).compile()
        return [f.msg.split(":")[0] for f in a.findings if f.code == "ASM-012"]

    def test_between_two_placed_parts(self):
        self.assertEqual(self.warns([{"id": "g", "parts": ["a", "b", "meio"]}]), ["meio"])

    def test_good_order(self):
        self.assertEqual(self.warns([{"id": "g", "parts": ["a", "meio", "b"]}]), [])

    def test_sub_assembly_enters_as_one(self):
        self.assertEqual(self.warns([{"id": "x", "parts": ["a"]},
                                     {"id": "y", "parts": ["meio", "b"], "sub": True}]), [])


class TestVariants(unittest.TestCase):
    """Variante = BRICK com padrões; o que a peça escreve vence o padrão."""

    def part(self, **rp):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": [dict(id="p", at=(0, 0, 0), **rp)]})
        return a.parts["p"]

    def test_liftarm_defaults(self):
        p = self.part(type="liftarm", cells=(6, 1, 1))
        self.assertEqual((p.type, p.axes, p.round_axis), ("brick", ("bored",) * 3, "y"))
        self.assertEqual(self.part(type="liftarm", cells=(1, 6, 1)).round_axis, "x")

    def test_explicit_field_wins(self):
        p = self.part(type="liftarm", cells=(6, 1, 1), axes="y", round="z")
        self.assertEqual((p.axes, p.round_axis), (("solid", "bored", "solid"), "z"))

    def test_liftarm_rejects_thick_section(self):
        with self.assertRaises(A.IRError):
            self.part(type="liftarm", cells=(6, 2, 1))

    def test_studs_on_round_part_skip_the_ends(self):
        p = self.part(type="liftarm", cells=(6, 1, 1), studs="up")
        self.assertEqual((p.faces[5], p.pin_cells), ("pin", "inner"))

    def test_tile_and_pins_sugar(self):
        t = self.part(type="tile", cells=(4, 4, 1))
        self.assertEqual((t.thickness, t.axes, t.faces[4], t.pin_cells), (4.0, ("solid",) * 3, "pin", "edge"))
        b = self.part(cells=(2, 2, 1), pins=["yn"], plain=["xp"])
        self.assertEqual((b.faces[2], b.faces[1]), ("pin", "plain"))

    def test_variant_equals_explicit_brick(self):
        v = self.part(type="plate", cells=(4, 3, 1))
        e = self.part(cells=(4, 3, 1), thickness=4.0, axes="z", round="z", corner_r=4.0)
        p = A.Assembly({"parts": [{"id": "x"}]}).p
        self.assertEqual(v.canonical(p)[0], e.canonical(p)[0])

    def test_unknown_type_is_reported(self):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": [{"id": "p", "type": "dock"}, {"id": "q"}]})
        self.assertIn("ASM-000", [f.code for f in a.findings])


class TestReview(unittest.TestCase):
    """A ficha de qualidade bloqueia em portão medido, não em opinião."""

    def gates(self, parts, groups=()):
        from fusionbrick.asm import metrics
        a = A.Assembly({"assembly": {"name": "t"}, "parts": parts, "groups": list(groups)}).compile()
        return {name: ok for _, name, _, _, ok in metrics.gates(a, "/nonexistent")}, metrics

    def test_free_studs_and_missing_collide_fail(self):
        g, _ = self.gates([B("a", (0, 0, 0), (2, 2, 1), faces={"zp": "pin"}), B("b", (0, 0, 1), (2, 1, 1))])
        self.assertFalse(g["pinos sem uso"])
        self.assertFalse(g["colisão exata (fb_collide)"])
        self.assertTrue(g["erros de encaixe"])

    def test_undocumented_step_fails(self):
        parts = [B("a", (0, 0, 0), (2, 1, 1)), B("b", (0, 0, 1), (2, 1, 1))]
        g, _ = self.gates(parts, [{"id": "g", "parts": ["a", "b"]}])
        self.assertFalse(g["passos de montagem sem nota"])
        g, _ = self.gates(parts, [{"id": "g", "parts": ["a", "b"], "note": "base e tampa"}])
        self.assertTrue(g["passos de montagem sem nota"])


class TestBend(unittest.TestCase):
    """BEND: só fecha no grid com R = (k+½)·grid a 90°/180°."""

    def ring(self):
        N, L = 6, 2
        bd = lambda i, at, d, t: {"id": i, "type": "bend", "at": at, "dir": d, "turn": t}
        return [B("vb", (2, 0, 0), (L, 1, 1)), B("vd", (N - 1, 2, 0), (1, L, 1)),
                B("vt", (2, N - 1, 0), (L, 1, 1)), B("ve", (0, 2, 0), (1, L, 1)),
                bd("c1", (N - 2, 0, 0), (1, 0, 0), (0, 1, 0)), bd("c2", (N - 1, N - 2, 0), (0, 1, 0), (-1, 0, 0)),
                bd("c3", (1, N - 1, 0), (-1, 0, 0), (0, -1, 0)), bd("c4", (0, 1, 0), (0, -1, 0), (1, 0, 0))]

    def test_ring_of_bends_closes(self):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": self.ring()}).compile()
        self.assertTrue(a.ok, [f.line() for f in a.findings if f.severity == "error"])
        self.assertEqual(sum(1 for j in a.joints if j.kind == "dowel"), 8)

    def test_bend_angle_off_grid_rejected(self):
        with self.assertRaises(A.IRError):
            A.Assembly({"assembly": {"name": "t"}, "parts": [
                {"id": "c", "type": "bend", "at": (0, 0, 0), "angle": 45}]})

    def test_part_inside_the_curve_collides(self):
        parts = self.ring() + [B("x", (5, 1, 0), (1, 1, 1))]
        a = A.Assembly({"assembly": {"name": "t"}, "parts": parts}).compile()
        self.assertIn("ASM-002", [f.code for f in a.findings if f.severity == "error"])


class TestOutputs(unittest.TestCase):
    def test_rotated_copies_share_one_config(self):
        l = B("l", (0, 0, 0), (4, 1, 1), axes="xz", faces={"yp": "pin"})
        r = B("r", (0, 2, 0), (4, 1, 1), axes="xz", faces={"yn": "pin"})
        a = build(l, r, B("mid", (0, 1, 0), (4, 1, 1), axes="y"))
        keys = {a.config_of(a.parts[p])[0] for p in ("l", "r")}
        self.assertEqual(len(keys), 1)

    def test_scad_mentions_every_part(self):
        a = build(BASE, TOP)
        s = a.scad()
        self.assertIn("// base", s)
        self.assertIn("// top", s)



class TestNames(unittest.TestCase):
    """O vocabulário público e o antigo descrevem a mesma montagem."""

    OLD = [
        {"id": "base", "type": "brick", "at": [0, 0, 0], "cells": [8, 4, 1], "axes": "z"},
        {"id": "v", "type": "liftarm", "at": [0, 0, 1], "cells": [8, 1, 1], "studs": "down"},
        {"id": "tampa", "type": "tile", "at": [0, 1, 1], "cells": [8, 3, 1]},
        {"id": "p", "type": "brick", "at": [0, 0, 2], "cells": [2, 1, 1], "axes": "z",
         "faces": {"zn": "pin"}, "plain": ["xn"], "pin_cells": "all"},
        {"id": "bat", "type": "mock", "at": [3, 0, 3], "size": [16, 8, 8]},
    ]
    NEW = [
        {"id": "base", "type": "brick", "at": [0, 0, 0], "size": [8, 4, 1], "holes": "z"},
        {"id": "v", "type": "beam", "at": [0, 0, 1], "size": [8, 1, 1], "studs": "bottom"},
        {"id": "tampa", "type": "cover", "at": [0, 1, 1], "size": [8, 3, 1]},
        {"id": "p", "type": "brick", "at": [0, 0, 2], "size": [2, 1, 1], "holes": "z",
         "faces": {"bottom": "stud"}, "flat": ["back"], "studs_on": "all"},
        {"id": "bat", "type": "component", "at": [3, 0, 3], "size_mm": [16, 8, 8]},
    ]

    @staticmethod
    def shape(parts, **meta):
        a = A.Assembly({"assembly": {"name": "t", **meta}, "parts": parts}).compile()
        return (sorted((j.kind, j.a, j.b, j.pos) for j in a.joints),
                sorted((f.severity, f.code) for f in a.findings),
                {pid: q.type for pid, q in a.parts.items()})

    def test_old_and_new_compile_the_same(self):
        self.assertEqual(self.shape(self.OLD), self.shape(self.NEW))
        self.assertEqual(self.shape(self.NEW)[2]["bat"], "component")

    def test_meta(self):
        a = A.Assembly({"assembly": {"name": "t", "view_angle": 125, "dowel_every": 3}, "parts": self.NEW})
        self.assertEqual((a.hero_rz, a.dowel_step), (125, 3))

    def test_studs_as_face_list(self):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": [
            {"id": "a", "type": "brick", "at": [0, 0, 0], "size": [2, 1, 1], "studs": ["left", "right"]}]})
        faces = dict(zip(("xn", "xp", "yn", "yp", "zn", "zp"), a.parts["a"].faces))
        self.assertEqual((faces["yp"], faces["yn"], faces["zp"]), ("pin", "pin", "auto"))

    def test_curve_radius_is_cells_per_side(self):
        new = A.Assembly({"assembly": {"name": "t"}, "parts": [
            {"id": "c", "type": "curve", "at": [0, 0, 0], "dir": [1, 0, 0], "turn": [0, 1, 0], "radius": 2}]})
        old = A.Assembly({"assembly": {"name": "t"}, "parts": [
            {"id": "c", "type": "bend", "at": [0, 0, 0], "dir": [1, 0, 0], "turn": [0, 1, 0], "k": 1}]})
        self.assertEqual(new.parts["c"].k, old.parts["c"].k)
        self.assertEqual(new.parts["c"].type, "curve")

    def test_strut_by_cells_makes_its_own_nodes(self):
        parts = [
            {"id": "chao", "type": "beam", "at": [0, 0, 0], "size": [12, 1, 1]},
            {"id": "pe", "type": "brick", "at": [1, 0, 1], "size": [1, 1, 1]},
            {"id": "rampa", "type": "strut", "from": [2, 0, 1], "to": [6, 0, 4]},
            {"id": "poste", "type": "brick", "at": [7, 0, 1], "size": [1, 1, 4]},
        ]
        a = A.Assembly({"assembly": {"name": "t"}, "parts": parts,
                        "groups": [{"id": "g", "parts": ["chao", "pe", "rampa", "poste"]}]}).compile()
        self.assertTrue(a.ok, a.summary())
        self.assertEqual(a.parts["rampa-n0"].dirs, [(-1, 0, 0), (4, 0, 3)])     # braço padrão: para trás
        self.assertEqual(a.parts["rampa-n1"].dirs, [(-4, 0, -3), (1, 0, 0)])
        self.assertEqual(a.parts["rampa-v"].cells[0], 4)                       # 3-4-5: viga de 4
        self.assertEqual(a.groups[0]["parts"], ["chao", "pe", "rampa-n0", "rampa-n1", "rampa-v", "poste"])

    def test_old_beam_between_nodes_is_a_strut(self):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": [
            {"id": "n0", "type": "node", "at": [0, 0, 0], "dirs": [[-1, 0, 0], [4, 0, 3]]},
            {"id": "n1", "type": "node", "at": [4, 0, 3], "dirs": [[-4, 0, -3], [1, 0, 0]]},
            {"id": "v", "type": "beam", "from": "n0", "to": "n1", "style": "liftarm"}]}).compile()
        self.assertEqual(a.parts["v"].type, "strut")
        self.assertEqual(a.parts["v"].config(a)[0], "strut-4")

    def test_wheel_on_named_face_and_messages(self):
        a = A.Assembly({"assembly": {"name": "t"}, "parts": [
            {"id": "lat", "type": "brick", "at": [0, 0, 2], "size": [6, 1, 1], "holes": "x"},
            {"id": "roda", "type": "wheel", "at": [2, -1, 2], "on": "lat.right", "diameter": 4}]}).compile()
        msg = " ".join(f.line() for f in a.findings if f.code == "ASM-010" and f.severity == "error")
        self.assertIn("lat.right", msg)
        self.assertIn("socket", msg)
        self.assertNotIn("recess", msg)

    def test_unknown_face_name(self):
        with self.assertRaises(A.IRError):
            A.Assembly({"assembly": {"name": "t"}, "parts": [
                {"id": "a", "type": "brick", "at": [0, 0, 0], "size": [1, 1, 1], "faces": {"cima": "stud"}}]})

    def test_publicize_round_trip(self):
        from fusionbrick.asm import names
        for old, new in zip(self.OLD, self.NEW):
            self.assertEqual(names.publicize(old), new)

if __name__ == "__main__":
    unittest.main()
