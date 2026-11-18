# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is FusionBrick

Parametric modular 3D design system for FDM printing. Parts connect on any face via press-fit connectors (LINKs). Currently implemented in OpenSCAD. Architecture is **spec-first**: `spec/` defines the system contract, `impl/` contains tool-specific implementations.

## Commands

```bash
make preview                          # isometric PNG for every part in impl/openscad/
make preview-animated                 # 360° turntable GIF for every part (renders/img/*.gif)
make preview-animated ANIM_DELAY=10 ANIM_FRAMES=72  # slower/smoother (defaults: 15, 36)
make build                            # export STL for every part in impl/openscad/
make assembly                         # isometric PNGs (normal + exploded) for every examples/*/assembly.scad
make assembly-animated                # looping GIF (360° spin + explode/collapse) for every examples/*/assembly.scad
make assembly-animated ASM_ANIM_DELAY=10 ASM_ANIM_FRAMES=96 ASM_ANIM_EXPLODE=20  # tune (defaults: 5, 72, 12)
make assembly-animated ASM_ANIM_SPIN=360                                        # enable full rotation (default: 0 — fixed isometric camera)
make assembly-animated ASM_ANIM_SPEED=2                                         # 2x faster (default: 1; 0.5 = half speed)
make preview PART_COLOR="[r,g,b]"    # override render color (values 0.0–1.0)
make vars                             # print effective config + derived values
make openscad-preview                 # explicit namespace alias
make openscad-build
```

**Configuration:** every tunable lives in `hack/automations/variables.mk`; `openscad.mk` is recipes only. The six system primitives are injected into **every** openscad call as `SYSTEM_D`, so a value changed in one place changes every part coherently.

Precedence, lowest to highest:

| | Where | Example |
| --- | --- | --- |
| 1 | `.scad` default | `hole_d = 4.0;` |
| 2 | `variables.mk` default | `HOLE_D ?= 4.0` |
| 3 | `.env` at repo root (gitignored) | `HOLE_D=5.0` |
| 4 | command-line variable | `make build HOLE_D=5.0` |
| 5 | `EXTRA_D` | `make build EXTRA_D='-D hole_d=5.0'` |

3 beats 2 because defaults use `?=` and `.env` is read first. 4 beats 3 by make's own rule. 5 beats 4 because openscad applies the **last** `-D` of a given name, and `EXTRA_D` is emitted after `SYSTEM_D` in every recipe.

`.env` is parsed as a makefile: `KEY=value`, no quotes, no `export`. Copy `.env.example`.

There is no `GRID` knob — grid is derived (`hole_d + 2·(wall + collar_w)`). Exposing it would allow asking for a grid that doesn't close with its own hole.

⚠️ `$fn` in `EXTRA_D` needs double escaping — `$` is meaningful to make **and** to the shell:

```bash
make build FN=16                          # use this
make build EXTRA_D='-D \$$fn=16'          # only if you must
```

### Fusion 360 add-in

```bash
make fusion-link      # symlink into the Fusion AddIns folder (development)
make fusion-status    # where it resolved, and how it is installed
make fusion-test      # pure-Python core tests (core + assembly compiler)
make fusion-check     # add-in syntax + manifest, without opening Fusion
make fusion-vendor    # package to dist/ with the core embedded
make fusion-unlink
```

Step-by-step development workflow: [`hack/automations/fusion.md`](hack/automations/fusion.md).

Development uses a **symlink**, not a copy: edit in the repo, then Stop → Run the add-in in Fusion. A copy breaks the core import — `plugins/fusion360/FusionBrick/` reaches `impl/python/` at `../../../impl/python`, which does not exist outside the repo. `fusion-vendor` is the copy-safe path: it embeds `fusionbrick/` inside the add-in folder, and `_core()` prefers the embedded one.

`fusion-unlink` refuses to delete a real directory — only a symlink. Same for `fusion-link`, which will not clobber one.

The AddIns path has spaces and Autodesk renamed it across versions ("Autodesk Fusion 360" → "Autodesk Fusion"), so it is resolved in the recipe's shell, not with `$(wildcard)`. Set `FUSION_ADDINS_DIR` to force one.

**Architecture:** `impl/python/fusionbrick/` is the tool-agnostic core (params, geometry positions, rules) — plain stdlib, testable without any CAD. `plugins/fusion360/` is the adapter. The add-in creates Fusion **User Parameters**: primitives as values, derived as **expressions** (`fb_grid = fb_hole_d + 2 * (fb_wall + fb_collar_w)`), so the derivation stays alive inside the document — changing `fb_wall` in Fusion's Parameters dialog rebuilds the part.

Fusion **caches Python modules** between Stop and Run — it reloads the entry file but not what it imports. `FusionBrick.py` imports inside `run()` after purging `sys.modules` of our own modules (never `adsk`), gated by `DEV_RELOAD`. Without it, edits appear to have no effect.

Custom Features were rejected: still a preview API ("never deliver any programs that use any preview capabilities") and their recompute covers only base+sketch+combine.

**Dependencies:** `openscad` (see `.tool-versions`) + `magick` (ImageMagick 7).

```bash
asdf plugin add openscad https://github.com/gabrielelana/asdf-openscad
asdf install   # installs openscad version from .tool-versions
```

## Building models

To build a model/prototype from a description or an image, use the `fusionbrick-assembly` skill (`.claude/skills/fusionbrick-assembly/SKILL.md`).

Assemblies are **described, not drawn**: `examples/<name>/assembly.toml` lists parts in grid cells (`brick`, `beam`, `plate`, `cover`, `curve`, `strut`, `wheel`, `component`). Above ~30 parts or with symmetry, generate it from a `gen.py` using `impl/python/fusionbrick/irgen.py` (`Build`, `strut()`, `ring()`, `arch()`, `mirror_y()`). The compiler (`impl/python/fusionbrick/asm/`; `assembly.py` is a thin alias) inserts every dowel, validates fit by the ASM-### rules in `spec/assembly.md`, and generates `assembly.scad` (never edit it), `parts/*.stl` (one per unique config, rotated copies share), `bom.md`, `steps.md`, `report.txt`.

```bash
make assemble-check NAME=rover-tub   # validate only, milliseconds
make assemble-stats NAME=rover-tub   # quality: parts per 100mm, dowel share, STL reuse
make assemble-review NAME=rover-tub  # quality sheet: every measured gate of the council (APTO / NÃO APTO)
make assemble NAME=rover-tub         # + STLs (cached) + .scad + BOM + steps + 5 PNGs
make assemble-test                   # compiler tests, one per rule
make assemble-collide NAME=rover-tub # independent check: exact CGAL intersection per neighbor pair (slow)
python3 hack/scripts/fb_assemble.py ports examples/<name>/assembly.toml <part>
```

Face default is `auto` (`socket` where the part is holed on that axis, `flat` where it is not); an explicit `socket` on an axis without a hole is an error in both the core and `brick.scad`.

**Vocabulary** — one name per concept, single source `asm/names.py`, full table in `spec/assembly.md` § Nomes. Always write the current names:

| | Current (write these) | Older (still accepted) | OpenSCAD parameter (unchanged) |
| --- | --- | --- | --- |
| parts | `beam` · `cover` · `curve` · `strut` · `component` | `liftarm` · `tile` · `bend` · `node`+`beam` · `mock` | `brick.scad` · `curve.scad` · `node.scad` |
| connectors | `stud` · `socket` · `flat` (dowel = loose two-ended PIN) | `pin` · `recess` · `plain` | `pin` · `recess` · `plain` (both accepted in `-D`) |
| faces (front = +X) | `front` `back` `left` `right` `top` `bottom` | `xp` `xn` `yp` `yn` `zp` `zn` | `face_xp` … `face_zn` |
| fields | `size` · `holes` · `rounded` · `studs_on` · `radius` · `diameter` · `size_mm` · `view_angle` · `dowel_every` | `cells` · `axes` · `round` · `pin_cells` · `k` · `cells` · `size` · `hero_rz` · `dowel_step` | `cells_x/y/z` · `axis_x/y/z` · `round_axis` · `pin_cells` · `k` · `wheel_cells` |

Inside the compiler the internal names are the older/OpenSCAD ones (`names.normalize` translates on the way in, `names.face`/`names.kind`/`names.publicize` on the way out). Every message, report, schema and generated TOML speaks the current names. `hack/scripts/fb_migrate.py <toml>` rewrites a hand-written file.

**Variants** are BRICKs with defaults, not new parts: `type = "beam" | "plate" | "cover"`, plus the shortcuts `studs` (`"top"`, `"bottom"` or a list of faces) and `flat` (list of faces). Any field written on the part overrides the default. Single source: `asm/variants.py`.

**`strut`** is one line (`from`/`to` cells); the compiler expands it into `<id>-n0`, `<id>-n1` (nodes) and `<id>-v` (the beam). Groups reference the strut id.

**Compiler layout** — every part type answers the same four questions (`resolve`, `ports`, `boxes`, `config`) in `asm/parts.py`; nothing else branches on type. Every joint comes from one step: two ports at the same position facing each other. One function per ASM rule in `asm/checks.py`. A new part type is one class.

**Quality gate** — before delivering any assembly, run the `fusionbrick-council` skill: `review` must print APTO, then the Maker · Engineer · Designer pass.

**The connector is drawn once**: `fb_male()` / `fb_female()` in `impl/openscad/params.scad`; every part uses them. Do not redraw a pin or recess in a part file.

## Architecture

### Spec → Impl separation

`spec/` is the source of truth — tool-agnostic definitions:

- `spec/constitution.md` — system premises (grid integrity, wire passage by default, permanent compatibility)
- `spec/params.md` — system numbers; tables are GENERATED from the contract (never hand-edit them)
- `spec/parts/*.md` — intent, geometry rules, constraints per part
- `spec/rules.md` — compatibility and design rules (Grid Law, face/edge interfaces)

`impl/openscad/` translates spec to OpenSCAD. CAD plugins (implementations of the standard inside other tools) live in `plugins/<tool>/` — today `plugins/fusion360/`.

### Make pipeline

```text
Makefile → core.mk → openscad.mk → variables.mk → .env
```

`core.mk` routes `openscad-*` targets. `openscad.mk` owns all render/export logic and nothing else — every variable was moved to `variables.mk`, which includes `.env` if present. `openscad.mk` includes `variables.mk` directly (not via `core.mk`) because the `openscad-%` passthrough runs it as a submake with `-f`.

Part list is dynamic: `$(wildcard impl/openscad/*.scad)` — adding a file is enough.

### OpenSCAD conventions

Every `.scad` file follows this order: parameters → derived values → modules → render call.

```openscad
part_color = [0.35, 0.38, 0.42];   // default; overridden by make via -D
border_radius = 0;                   // default 0 (VERTEX: 2)
border_style = "round";              // "round" (sphere) | "chamfer" (45° octahedron minkowski)
color(part_color) my_part();
```

`-D` flags passed at render time override any variable declared in the file. `color()` only affects `--preview` mode (F5/CLI `--preview`), not full render (`--render`/F6).

### Global system parameters

Do **not** copy numbers into code from anywhere. The single source is the part's contract:

```
spec/parts/<part>/contracts.toml
```

It holds every primitive and derived value with its **formula**, and `make spec-check` verifies it against the Python core, the OpenSCAD echoes and `make vars`. Divergence is a bug, not a choice.

Grid is **derived**, never declared (`hole_d + 2·(wall + collar_w)`). `pin_len` is **declared**, not derived, with ceiling `grid/2 − pin_d/2` — see `spec/constitution.md` § 5 for why the old derivation was wrong.

Format and how to convert a part: `spec/README.md`.

```bash
make spec-check      # contract vs implementations (+ params.md tables up to date)
make spec-docs       # regenerate the number tables of spec/params.md from the contract
make spec-status     # which parts are converted
```

### Known quirk — Y-axis face rotation

```openscad
// Face +Y
translate([0, size/2, 0])  rotate([90,  0, 0]) cylinder(...);
// Face -Y  ← rotate NEGATIVE
translate([0, -size/2, 0]) rotate([-90, 0, 0]) cylinder(...);
```

`rotate([90,0,0])` points toward −Y. Counterintuitive — always verify with F5.

### Preview render pipeline

1. OpenSCAD renders `.tmp.png` with `--preview --colorscheme=Monotone`
2. ImageMagick samples `[0,0]` pixel → removes background color → transparent PNG
3. Output goes to `renders/img/<part>.png`

`make preview` injects `border_radius=1` for documentation renders; `.scad` defaults stay `0`.

## Wiki

Este repositório possui documentação em `.agents/wiki/`.

Comece por [Wiki quickstart](.agents/wiki/quickstart.md).
