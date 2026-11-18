"""
Add-in FusionBrick — gera peças do design system no Fusion 360.

spec: ../../../spec/    core: ../../../impl/python/fusionbrick/

RECARGA EM DESENVOLVIMENTO
O Fusion mantém os módulos Python em cache entre Stop e Run. Ele
recarrega ESTE arquivo, mas não os que ele importa — então editar
`BrickCommand.py` ou o core não teria efeito nenhum sem reiniciar
o Fusion inteiro.

Por isso os imports acontecem DENTRO de run(), depois de limpar o
`sys.modules`. Com `DEV_RELOAD = True` o ciclo vira: edita, Stop,
Run — sem fechar o programa.

Deixe `False` ao distribuir: aí não há edição para recarregar, e
purgar módulo a cada Run é só custo.
"""

import sys
import traceback

import adsk.core

DEV_RELOAD = True

# Prefixos dos NOSSOS módulos. Nunca purgar `adsk` — é a API do
# próprio Fusion e removê-la do cache derruba o add-in.
_OURS = ("fusionbrick", "BrickCommand")

_commands = []

_CMD = {
    "cmd_name":         "FusionBrick Cell",
    "cmd_description":  "Gera a celula 1x1x1 do FusionBrick, parametrica",
    "cmd_id":           "FusionBrickCellCmd",
    "workspace":        "FusionSolidEnvironment",
    "toolbar_panel_id": "SolidCreatePanel",
}


def _purge_modules():
    """Tira os nossos módulos do cache para o próximo import ser fresco."""
    for name in list(sys.modules):
        leaf = name.split(".")[-1]
        if name.startswith(_OURS) or leaf in _OURS:
            del sys.modules[name]


def run(context):
    try:
        if DEV_RELOAD:
            _purge_modules()
        # Import tardio: só aqui o purge acima tem efeito.
        from .BrickCommand import BrickCommand

        _commands.append(BrickCommand(_CMD))
        for c in _commands:
            c.on_run()
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(
            "run() falhou:\n" + traceback.format_exc())


def stop(context):
    try:
        for c in _commands:
            c.on_stop()
        _commands.clear()
        if DEV_RELOAD:
            _purge_modules()
    except Exception:
        adsk.core.Application.get().userInterface.messageBox(
            "stop() falhou:\n" + traceback.format_exc())
