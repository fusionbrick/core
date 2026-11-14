"""
Comando que gera um BRICK como corpo PARAMÉTRICO no Fusion.

Estratégia: sketch + features nativas. Cada operação vira um nó na
timeline, editável depois, e o Fusion recalcula sozinho.

Descartei as duas alternativas:

  Custom Feature — agruparia tudo num nó só, mas a Autodesk diz
  "never deliver any programs that use any preview capabilities",
  e o recompute só cobre base+sketch+combine (extrude fica fora).

  B-Rep temporário — corpo mudo, sem histórico. O usuário não
  edita cota nenhuma, o que anula o sentido de "parametrizado".

A LEI DO SISTEMA VIVE NO DOCUMENTO. Os primitivos entram como User
Parameters com valor; os derivados entram como EXPRESSÃO. Mudar
`fb_wall` no diálogo de parâmetros do Fusion recalcula o grid e a
peça inteira — igual ao `-D wall=` do OpenSCAD.
"""

import os
import sys
import traceback

import adsk.core
import adsk.fusion

_handlers = []


def _core():
    """
    Importa o core Python puro. Tardio de propósito: se falhar, o
    erro aparece no comando e não impede o add-in de carregar.
    """
    # realpath, NÃO abspath: em desenvolvimento o add-in é um
    # symlink dentro de AddIns/, e abspath não resolve symlink —
    # o caminho ficaria em AddIns/ e subir dois níveis daria
    # API/python, que não existe. O core nunca era achado e o
    # import estourava ao abrir o diálogo.
    here = os.path.dirname(os.path.realpath(__file__))

    # Dois modos de instalação:
    #   symlink  -> o core vive em impl/python/, dois níveis acima
    #   vendor   -> o core foi copiado para DENTRO do add-in
    # Tenta o vendorizado primeiro: quem distribuiu quis aquele.
    candidates = (here, os.path.normpath(
        os.path.join(here, "..", "..", "python")))
    for cand in candidates:
        if os.path.isdir(os.path.join(cand, "fusionbrick")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            break
    else:
        raise ImportError(
            "core `fusionbrick` não encontrado. Procurei em:\n  " +
            "\n  ".join(candidates) +
            "\n\nRode `make fusion-link` no repo, ou `make fusion-vendor` "
            "para embutir o core no add-in.")
    from fusionbrick.params import Primitives, DERIVED_EXPRESSIONS
    from fusionbrick.brick import BrickSpec
    from fusionbrick import rules
    return Primitives, DERIVED_EXPRESSIONS, BrickSpec, rules


MM = 0.1  # Fusion trabalha em cm internamente


def _mm(v):
    return v * MM


def _ensure_params(design, prims, derived):
    """
    Cria/atualiza os User Parameters. Os derivados vão como string
    para o Fusion avaliar — é isso que mantém a derivação viva.
    """
    ups = design.userParameters
    units = "mm"

    def put(name, expr):
        full = "fb_" + name
        existing = ups.itemByName(full)
        if existing:
            existing.expression = expr
            return existing
        return ups.add(full, adsk.core.ValueInput.createByString(expr),
                       units, "")

    for name in ("hole_d", "wall", "collar_w", "collar_depth",
                 "tolerance", "gap", "pin_len"):
        put(name, "{} mm".format(getattr(prims, name)))

    # Derivados DEPOIS dos primitivos: as expressões referenciam eles
    for name, expr in derived.items():
        put(name, expr)


def _axis_of(vec, axis):
    return (vec.x, vec.y, vec.z)[axis]


def _far_face_plane(comp, base, axis, size_expr, name):
    """
    Plano na face OPOSTA à do plano base.

    O deslocamento segue a NORMAL REAL do plano, lida da geometria —
    não um sinal escrito à mão. A orientação dos planos XZ/YZ é a
    origem clássica de peça espelhada, e cada suposição errada custa
    um ciclo inteiro dentro do Fusion para descobrir.
    """
    n = _axis_of(base.geometry.normal, axis)
    expr = size_expr if n > 0 else "-(" + size_expr + ")"
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, adsk.core.ValueInput.createByString(expr))
    pl = comp.constructionPlanes.add(pi)
    pl.name = name
    return pl


def _cut_at(comp, plane, gx, gy, gz, diameter_expr, span_expr, name):
    """
    Corte cilíndrico centrado NO PLANO, simétrico.

    Duas decisões que tiram o palpite da jogada:

    `modelToSketchSpace` converte o ponto GLOBAL para o sistema do
    sketch. Sem isso eu teria de saber como cada plano mapeia seus
    eixos locais — e XZ/YZ não são óbvios.

    Extrusão SIMÉTRICA: a direção do corte deixa de importar. No
    furo passante o excesso é irrelevante; no rebaixo, metade de
    2×profundidade entra no material e a outra corta o vazio, o que
    dá exatamente a profundidade pedida.
    """
    sk = comp.sketches.add(plane)
    sk.name = name
    local = sk.modelToSketchSpace(adsk.core.Point3D.create(gx, gy, gz))
    local.z = 0
    circle = sk.sketchCurves.sketchCircles.addByCenterRadius(local, 1.0)
    sk.sketchDimensions.addDiameterDimension(
        circle,
        adsk.core.Point3D.create(local.x + 1, local.y + 1, 0)
    ).parameter.expression = diameter_expr

    ext = comp.features.extrudeFeatures
    inp = ext.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.CutFeatureOperation)
    inp.setSymmetricExtent(
        adsk.core.ValueInput.createByString(span_expr), True)
    feat = ext.add(inp)
    feat.name = name
    return feat


def _target_component(design):
    """
    Onde construir.

    Documento "Part Design" aceita UM componente só — addNewComponent
    levanta RuntimeError nele. Nesse caso construímos no root, que é
    o único que existe. Em Assembly ganhamos um componente próprio.
    """
    root = design.rootComponent
    try:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "FusionBrick 1x1x1"
        return comp, True
    except RuntimeError:
        return root, False


def build_brick(design, prims, spec):
    """Constrói a célula: bloco, furos passantes, rebaixos."""
    comp, own = _target_component(design)
    g = "fb_grid"
    half = "fb_grid / 2"
    c = _mm(prims.grid) / 2      # centro da célula, em cm
    full = _mm(prims.grid)

    # --- bloco ---------------------------------------------------
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = "brick_base"
    rect = sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(full, full, 0))

    # Qual linha é horizontal não é garantido pela ordem — descubro
    # comparando os extremos em vez de assumir item(0)/item(1).
    horiz = vert = None
    for i in range(rect.count):
        ln = rect.item(i)
        a = ln.startSketchPoint.geometry
        b = ln.endSketchPoint.geometry
        if horiz is None and abs(a.y - b.y) < 1e-9:
            horiz = ln
        elif vert is None and abs(a.x - b.x) < 1e-9:
            vert = ln
    for ln, orient, at in (
            (horiz, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
             adsk.core.Point3D.create(full / 2, -0.5, 0)),
            (vert, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
             adsk.core.Point3D.create(-0.5, full / 2, 0))):
        if ln is not None:
            sk.sketchDimensions.addDistanceDimension(
                ln.startSketchPoint, ln.endSketchPoint, orient, at
            ).parameter.expression = g

    ext = comp.features.extrudeFeatures
    inp = ext.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByString(g)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    block = ext.add(inp)
    block.name = "block"
    if not own and block.bodies.count:
        block.bodies.item(0).name = "FusionBrick 1x1x1"

    xy = comp.xYConstructionPlane
    xz = comp.xZConstructionPlane
    yz = comp.yZConstructionPlane

    # --- furos passantes, um por eixo ----------------------------
    # Span generoso: o corte é simétrico e o excesso não faz mal.
    span = "fb_grid * 3"
    _cut_at(comp, xy, c, c, 0, "fb_hole_d", span, "bore_z")
    _cut_at(comp, xz, c, 0, c, "fb_hole_d", span, "bore_y")
    _cut_at(comp, yz, 0, c, c, "fb_hole_d", span, "bore_x")

    # --- rebaixos: dois por eixo, um em cada boca ----------------
    # Simétrico de 2×profundidade centrado na face = exatamente
    # `collar_depth` para dentro. Rebaixo sem furo seria bolso cego,
    # por isso só existem onde o eixo é vazado.
    rspan = "fb_collar_depth * 2"
    rd = "fb_recess_d"
    _cut_at(comp, xy, c, c, 0, rd, rspan, "recess_zn")
    _cut_at(comp, xz, c, 0, c, rd, rspan, "recess_yn")
    _cut_at(comp, yz, 0, c, c, rd, rspan, "recess_xn")

    for nm, base, axis, gp in (
            ("recess_zp", xy, 2, (c, c, full)),
            ("recess_yp", xz, 1, (c, full, c)),
            ("recess_xp", yz, 0, (full, c, c))):
        pl = _far_face_plane(comp, base, axis, g, nm + "_pl")
        _cut_at(comp, pl, gp[0], gp[1], gp[2], rd, rspan, nm)

    return comp


class _CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            Primitives, DERIVED, BrickSpec, rules = _core()
            cmd = args.command
            inputs = cmd.commandInputs
            p = Primitives()

            grp = inputs.addGroupCommandInput("prim", "Primitivos do sistema")
            gi = grp.children
            for name, label in (
                    ("hole_d", "Furo Ø"),
                    ("wall", "Parede"),
                    ("collar_w", "Colar (radial)"),
                    ("collar_depth", "Colar (axial)"),
                    ("tolerance", "Tolerância"),
                    ("gap", "Folga entre machos"),
                    ("pin_len", "Protrusão do macho")):
                gi.addValueInput(
                    name, label, "mm",
                    adsk.core.ValueInput.createByReal(
                        _mm(getattr(p, name))))

            # Derivados: só leitura. Deixa explícito que o grid não
            # é escolha — é consequência.
            der = inputs.addGroupCommandInput("der", "Derivados (não editáveis)")
            der.children.addTextBoxCommandInput(
                "derived_txt", "", _derived_text(p), 4, True)
            der.isExpanded = True

            inputs.addTextBoxCommandInput(
                "warn", "", "", 2, True).isVisible = False

            for ev, h in (("inputChanged", _ChangedHandler()),
                          ("validateInputs", _ValidateHandler()),
                          ("execute", _ExecuteHandler())):
                getattr(cmd, ev).add(h)
                _handlers.append(h)
        except Exception:
            _msg("CommandCreated falhou:\n" + traceback.format_exc())


def _read(inputs):
    Primitives, _, _, _ = _core()
    kw = {}
    for name in ("hole_d", "wall", "collar_w", "collar_depth",
                 "tolerance", "gap", "pin_len"):
        kw[name] = inputs.itemById(name).value / MM  # cm -> mm
    return Primitives(**kw)


def _derived_text(p):
    return (
        "grid = furo + 2 x (parede + colar) = {:g} mm\n"
        "rebaixo {:g} | pino {:g} | colar {:g}\n"
        "lasca na quina {:g} (= parede) | alma {:g} (= 2 x parede)\n"
        "teto do macho {:g} mm"
    ).format(p.grid, p.recess_d, p.pin_d, p.collar_d,
             p.corner_sliver, p.web_between_holes, p.pin_len_max)


class _ChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            box = inputs.itemById("derived_txt")
            if box:
                box.text = _derived_text(_read(inputs))
        except Exception:
            pass


class _ValidateHandler(adsk.core.ValidateInputsEventHandler):
    """As regras do core viram o OK habilitado/desabilitado."""

    def notify(self, args):
        try:
            _, _, _, rules = _core()
            bad = rules.fatal(_read(args.inputs))
            args.areInputsValid = not bad
        except Exception:
            args.areInputsValid = False


class _ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            Primitives, DERIVED, BrickSpec, rules = _core()
            inputs = adsk.core.Command.cast(
                args.firingEvent.sender).commandInputs
            p = _read(inputs)

            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType

            _ensure_params(design, p, DERIVED)
            build_brick(design, p, BrickSpec(p=p))

            warn = rules.warnings(p)
            if warn:
                _msg("BRICK gerado, com avisos:\n\n" +
                     "\n".join("- " + w.message for w in warn))
        except Exception:
            _msg("Execute falhou:\n" + traceback.format_exc())


def _msg(text):
    adsk.core.Application.get().userInterface.messageBox(text)


class BrickCommand:
    def __init__(self, cmd_def):
        self._d = cmd_def

    def on_run(self):
        ui = adsk.core.Application.get().userInterface
        try:
            existing = ui.commandDefinitions.itemById(self._d["cmd_id"])
            if existing:
                existing.deleteMe()
            cd = ui.commandDefinitions.addButtonDefinition(
                self._d["cmd_id"], self._d["cmd_name"],
                self._d["cmd_description"])
            h = _CreatedHandler()
            cd.commandCreated.add(h)
            _handlers.append(h)

            ws = ui.workspaces.itemById(self._d["workspace"])
            panel = ws.toolbarPanels.itemById(self._d["toolbar_panel_id"])
            panel.controls.addCommand(cd).isVisible = True
        except Exception:
            ui.messageBox("AddIn start falhou:\n" + traceback.format_exc())

    def on_stop(self):
        ui = adsk.core.Application.get().userInterface
        try:
            ws = ui.workspaces.itemById(self._d["workspace"])
            panel = ws.toolbarPanels.itemById(self._d["toolbar_panel_id"])
            ctrl = panel.controls.itemById(self._d["cmd_id"])
            if ctrl:
                ctrl.deleteMe()
            cd = ui.commandDefinitions.itemById(self._d["cmd_id"])
            if cd:
                cd.deleteMe()
            _handlers.clear()
        except Exception:
            ui.messageBox("AddIn stop falhou:\n" + traceback.format_exc())
