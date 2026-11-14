# Add-in do Fusion 360 — desenvolvimento e teste

Fluxo de trabalho para `impl/fusion360/`. Automação em [`fusion.mk`](fusion.mk); config em [`variables.mk`](variables.mk).

---

## Instalação (uma vez)

```bash
make fusion-link
make fusion-status
```

`fusion-link` cria um **symlink** da pasta do add-in para onde o Fusion procura. Confira:

```
pasta de add-ins : ~/Library/.../Autodesk Fusion 360/API/AddIns
fonte no repo    : .../impl/fusion360/FusionBrick
instalação       : SYMLINK ok -> .../impl/fusion360/FusionBrick
```

**Por que symlink e não cópia.** Você edita no repo e o Fusion vê a mudança — não há passo de sincronizar. E cópia **quebraria o import do core**: o add-in alcança `impl/python/` subindo dois níveis, caminho que não existe fora do repo. Para distribuir existe `fusion-vendor`, que embute o core.

Se a pasta não for encontrada (a Autodesk renomeou de "Autodesk Fusion 360" para "Autodesk Fusion" em versões novas):

```bash
make fusion-link FUSION_ADDINS_DIR="/caminho/para/AddIns"
```

No Fusion: **Utilities → Add-Ins → FusionBrick → Run**.

---

## O ciclo

```
  editar  ──►  make fusion-test   ──►  make fusion-check  ──►  Fusion: Stop → Run
   ▲              core, 19 testes      sintaxe + manifest         ▲
   │                                                              │
   └──────────────────  erro na tela  ◄─────────────────────────  ┘
```

**Rode os dois `make` antes de ir ao Fusion.** Um ciclo Stop/Run custa muito mais que dois segundos de terminal, e a maioria dos erros (digitação, JSON quebrado, regra violada) morre aqui.

| Comando | Pega | Não pega |
| --- | --- | --- |
| `make fusion-test` | a lei do sistema: derivação, invariantes, validações | nada de CAD |
| `make fusion-check` | sintaxe, manifest, **nomes `adsk.*` contra a API instalada**, resolução do core | geometria, assinatura de método |

Os stubs da API ficam **em disco**, dentro do app do Fusion, e `fusion_api_check.py` os lê por AST. Isso pega nome inexistente antes do Fusion — foi assim que `DimensionOrientations.HorizontalDimension` (o certo é `HorizontalDimensionOrientation`) deixou de custar um ciclo Stop/Run.

Os stubs não são *importados*: o `_core.so` exige o Python 3.14 que o Fusion embute e não carrega no interpretador do sistema.

Continua fora do alcance: **geometria** e **assinatura de método**. Espelhamento, plano trocado e ordem de argumentos só aparecem rodando.

---

## Recarga após editar

Com `DEV_RELOAD = True` em `FusionBrick.py`, **Stop → Run basta**.

Isso não é automático no Fusion: ele mantém os módulos Python **em cache**. Recarrega o arquivo de entrada, mas não os que ele importa — então editar `BrickCommand.py` ou o core não teria efeito, e o sintoma é traiçoeiro: você jura que salvou, o comportamento é o antigo, e a conclusão errada é "o código não funciona".

Resolvido em `FusionBrick.py`: os imports acontecem **dentro de `run()`**, depois de limpar `sys.modules` dos nossos módulos. O `adsk` nunca é purgado — removê-lo derrubaria o add-in.

Ao distribuir, ponha `DEV_RELOAD = False`.

| Você editou | Ação |
| --- | --- |
| `BrickCommand.py` ou `fusionbrick/*.py` | Stop → Run |
| `FusionBrick.manifest` | reiniciar o Fusion |
| adicionou/removeu arquivo `.py` | Stop → Run |

---

## Onde os erros aparecem

**Caixa de mensagem.** Todo handler está dentro de `try/except` com `traceback.format_exc()`. Erro em Python vira janela com o stack trace inteiro. É a fonte principal.

**Text Commands.** `View → Show Text Commands` abre o console. Ative o Python nele e o `print()` do add-in passa a aparecer — útil para inspecionar valor sem parar o fluxo.

**Silêncio.** Se o comando some do menu ou nada acontece, o `run()` falhou antes de registrar. Um `make fusion-check` limpo elimina sintaxe; sobra erro de API.

---

## Ler os parâmetros gerados

Depois de rodar o comando: **Modify → Change Parameters** (ou, no browser, **Document Settings → Parameters**).

> **Não há atalho padrão** para esse comando, em nenhuma plataforma. As únicas teclas `K` padrão ficam no ambiente Form (T-Splines). Para criar um: passe o mouse sobre o comando no menu, clique nos **três pontos** à direita e escolha *Change Keyboard Shortcut*. No Mac, onde a documentação mostra `Ctrl`, leia `Cmd`.

```
fb_hole_d        4.0 mm
fb_wall          1.6 mm
fb_collar_w      0.4 mm
fb_grid          = fb_hole_d + 2 * (fb_wall + fb_collar_w)     8 mm
fb_recess_d      = fb_hole_d + 2 * fb_collar_w               4.8 mm
```

Os primitivos entram como **valor**; os derivados como **expressão**. É isso que mantém a lei viva dentro do documento: mudar `fb_wall` ali recalcula o grid e a peça inteira, sem rodar o add-in de novo — o equivalente do `-D wall=` do OpenSCAD.

**Teste que vale a pena fazer uma vez:** mude `fb_wall` para `2.4mm` e confirme que `fb_grid` vira `9.6mm` e a peça cresce coerentemente. Se não crescer, alguma cota foi gravada como número em vez de expressão.

---

## Conferir contra o OpenSCAD

As duas implementações vêm da mesma spec e têm de bater:

```bash
make vars                                          # derivados pelo make
cd impl/python && python3 -c "
from fusionbrick.params import Primitives; p=Primitives()
print(p.grid, p.recess_d, p.pin_d, p.collar_d)"    # pelo core Python
make build PART=brick                              # e o STL do OpenSCAD
```

Divergência entre eles é **bug**, não escolha. Reporte antes de seguir.

---

## Distribuição

```bash
make fusion-vendor      # dist/fusion360/FusionBrick/ com o core embutido
```

A pasta resultante funciona **copiada**, sem depender do repo: o `_core()` procura o core embutido primeiro e cai no do repo só se não achar. É o pacote para zip ou Autodesk App Store.

Antes de empacotar: `DEV_RELOAD = False`.

---

## Referência

| Comando | O que faz |
| --- | --- |
| `make fusion-help` | lista os alvos |
| `make fusion-status` | onde resolveu, e como está instalado |
| `make fusion-link` | cria o symlink |
| `make fusion-unlink` | remove **só** symlink |
| `make fusion-test` | testes do core (19) |
| `make fusion-check` | sintaxe, manifest, nomes da API, resolução do core |
| `make fusion-vendor` | empacota em `dist/` |

`fusion-link` e `fusion-unlink` **nunca** tocam num diretório real — se houver uma cópia manual no lugar, os dois recusam e avisam. Mover ou apagar é decisão sua.

---

## Armadilhas já encontradas

**Cópia em vez de symlink** — o import do core quebra em silêncio no primeiro uso do comando, não no carregamento. `make fusion-status` avisa: `DIRETÓRIO REAL (cópia)`.

**Módulo em cache** — resolvido pelo `DEV_RELOAD`, mas se você tirar essa flag o sintoma volta: edições sem efeito.

**Heredoc em receita de make** — cada linha da receita roda num shell separado, então heredoc quebra pela metade. Foi por isso que o `fusion-check` virou `hack/scripts/fusion_check.py` em vez de Python inline.

**Nome de API inventado** — a API vem do SWIG e os nomes não são adivinháveis. `make fusion-check` confere contra os stubs instalados. Cuidado: o SWIG declara alguns membros FORA da classe (`Design.cast = lambda ...`), o que o validador precisa varrer para não dar falso positivo.

**Documento Part Design** — aceita UM componente só; `addNewComponent` levanta `RuntimeError` nele. `_target_component()` cai para o root nesse caso.

**`abspath` vs `realpath`** — `abspath` não resolve symlink. Com o add-in linkado, o caminho do core caía em `API/python` e o import falhava só ao abrir o diálogo.

**`cm` vs `mm`** — o Fusion trabalha internamente em **centímetros**. Todo valor lido de `ValueInput` sai em cm; o core fala mm. A conversão está isolada em `MM = 0.1` e `_mm()`, e é a origem clássica de peça 10× maior ou menor.
