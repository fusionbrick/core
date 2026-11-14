SHELL := /bin/bash

# Configuração inteira em variables.mk — aqui só receitas.
include $(dir $(lastword $(MAKEFILE_LIST)))variables.mk

.PHONY: preview preview-animated build assembly assembly-animated assembly-video _assembly-frames preview-wireframe assembly-wireframe

preview:
	@mkdir -p $(IMG_DIR)
	@for part in $(SELECTED); do \
		$(OPENSCAD) \
			--export-format png \
			--colorscheme=$(COLORSCHEME) \
			--imgsize=$(IMGSIZE) \
			$(ISO_CAMERA) \
			--preview \
			-D "part_color=$(PART_COLOR)" \
			$(SYSTEM_D) $(EXTRA_D) \
			-o $(IMG_DIR)/$$part.tmp.png \
			$(IMPL_DIR)/$$part.scad || { echo "SKIP $$part (render failed)"; continue; }; \
		BG=$$($(MAGICK) $(IMG_DIR)/$$part.tmp.png -format "%[pixel:u.p{0,0}]" info:); \
		$(MAGICK) $(IMG_DIR)/$$part.tmp.png -fuzz 2% -transparent "$$BG" $(IMG_DIR)/$$part.png; \
		rm -f $(IMG_DIR)/$$part.tmp.png; \
	done
	@echo "-> $(IMG_DIR)   [<peca>.png]  $(SELECTED)"

build:
	@mkdir -p $(STL_DIR)
	@for part in $(SELECTED); do \
		echo "STL $$part (radius=$(BORDER_RADIUS))"; \
		$(OPENSCAD) --export-format binstl \
			-D "border_radius=$(BORDER_RADIUS)" \
			-D 'border_style="$(BORDER_STYLE)"' \
			$(SYSTEM_D) $(EXTRA_D) \
			-o $(STL_DIR)/$$part.stl $(IMPL_DIR)/$$part.scad; \
	done
	@echo "-> $(STL_DIR)   [<peca>.stl]  $(SELECTED)"

assembly:
	@for asm in $(ASSEMBLIES); do \
		dir=$$(dirname $$asm); \
		echo "ASSEMBLY $$dir"; \
		$(OPENSCAD) \
			--export-format png \
			--imgsize=$(ASM_IMGSIZE) \
			$(ISO_CAMERA) \
			--preview \
			$(SYSTEM_D) $(EXTRA_D) \
			-o $$dir/assembly.png \
			$$asm || { echo "SKIP $$asm (render failed)"; continue; }; \
		$(OPENSCAD) \
			--export-format png \
			--imgsize=$(ASM_IMGSIZE) \
			$(ISO_CAMERA) \
			--preview \
			$(SYSTEM_D) \
			-D explode=12 \
			$(EXTRA_D) \
			-o $$dir/assembly-exploded.png \
			$$asm; \
	done
	@echo "-> examples/<nome>/   [assembly.png + assembly-exploded.png]  $(notdir $(patsubst %/,%,$(dir $(ASSEMBLIES))))"

# Wireframe das peças. Usa --render porque --preview ignora a
# opção de view (ver nota em VIEW).
preview-wireframe:
	@mkdir -p $(IMG_DIR)
	@for part in $(SELECTED); do \
		echo "WIREFRAME $$part"; \
		$(OPENSCAD) \
			--export-format png \
			--imgsize=$(IMGSIZE) \
			$(ISO_CAMERA) \
			--render \
			--view=wireframe \
			$(SYSTEM_D) $(EXTRA_D) \
			-o $(IMG_DIR)/$$part-wireframe.png \
			$(IMPL_DIR)/$$part.scad || echo "SKIP $$part"; \
	done
	@echo "-> $(IMG_DIR)   [<peca>-wireframe.png]  $(SELECTED)"

# Wireframe dos assemblies — mostra a topologia da armação sem a
# espessura das vigas escondendo as junções
assembly-wireframe:
	@for asm in $(ASSEMBLIES); do \
		dir=$$(dirname $$asm); \
		echo "WIREFRAME ASSEMBLY $$dir"; \
		$(OPENSCAD) \
			--export-format png \
			--imgsize=$(ASM_IMGSIZE) \
			$(ISO_CAMERA) \
			--render \
			--view=wireframe \
			$(SYSTEM_D) $(EXTRA_D) \
			-o $$dir/assembly-wireframe.png \
			$$asm || echo "SKIP $$asm"; \
	done
	@echo "-> examples/<nome>/   [assembly-wireframe.png]  $(notdir $(patsubst %/,%,$(dir $(ASSEMBLIES))))"

preview-animated:
	@mkdir -p $(IMG_DIR)
	@for part in $(SELECTED); do \
		echo "ANIMATE $$part"; \
		tmpdir=$$(mktemp -d); \
		ok=1; \
		for i in $$(seq 0 $$(( $(ANIM_FRAMES) - 1 ))); do \
			rot=$$(( $(ISO_AZIM) + i * 360 / $(ANIM_FRAMES) )); \
			frame=$$tmpdir/frame_$$(printf '%03d' $$i).png; \
			$(OPENSCAD) \
				--export-format png \
				--colorscheme=$(COLORSCHEME) \
				--imgsize=$(IMGSIZE) \
				--projection=o \
				--camera=0,0,0,$(ISO_ELEV),0,$$rot,500 \
				--autocenter --viewall \
				--preview \
				-D "part_color=$(PART_COLOR)" \
				$(SYSTEM_D) $(EXTRA_D) \
				-o $$frame \
				$(IMPL_DIR)/$$part.scad 2>/dev/null || { echo "SKIP $$part (render failed)"; ok=0; break; }; \
			BG=$$($(MAGICK) $$frame -format "%[pixel:u.p{0,0}]" info:); \
			$(MAGICK) $$frame -fuzz 2% -transparent "$$BG" $$frame; \
		done; \
		if [ $$ok -eq 1 ]; then \
			$(MAGICK) -delay $(ANIM_DELAY) -loop 0 -dispose Background $$tmpdir/frame_*.png $(IMG_DIR)/$$part.gif; \
			echo "  -> $(IMG_DIR)/$$part.gif"; \
		fi; \
		rm -rf $$tmpdir; \
	done
	@echo "-> $(IMG_DIR)   [<peca>.gif]  $(SELECTED)"

# Renderiza os frames do boomerang (explode/recolhe, giro opcional) para
# $$tmpdir e ecoa "OK" ou "FAIL" — usado por assembly-animated e
# assembly-video para não duplicar a lógica de render entre GIF e MP4.
# Requer: asm, dir, tmpdir (variáveis do shell já definidas pelo chamador).
define ASM_RENDER_FRAMES
	ok=1; \
	for i in $$(seq 0 $$(( $(ASM_ANIM_FRAMES) - 1 ))); do \
		rot=$$(( $(ISO_AZIM) + i * $(ASM_ANIM_SPIN) / $(ASM_ANIM_FRAMES) )); \
		frac=$$(LC_NUMERIC=C awk -v i=$$i -v n=$(ASM_ANIM_FRAMES) 'BEGIN { pi = atan2(0,-1); print (1 - cos(2*pi*i/n)) / 2 }'); \
		explode=$$(LC_NUMERIC=C awk -v f=$$frac -v e=$(ASM_ANIM_EXPLODE) 'BEGIN { print f * e }'); \
		frame=$$tmpdir/frame_$$(printf '%03d' $$i).png; \
		$(OPENSCAD) \
			--export-format png \
			--imgsize=$(ASM_IMGSIZE) \
			--projection=o \
			--camera=0,0,0,$(ISO_ELEV),0,$$rot,500 \
			--autocenter --viewall \
			--preview \
			$(SYSTEM_D) \
			-D "explode=$$explode" \
			$(EXTRA_D) \
			-o $$frame \
			$$asm 2>/dev/null || { echo "SKIP $$asm (render failed)"; ok=0; break; }; \
	done;
endef

# Explode e recolhe (boomerang) — loop perfeito, câmera isométrica fixa
# por padrão (ASM_ANIM_SPIN=0). Se ASM_ANIM_SPIN > 0, soma um giro
# completo ao ângulo isométrico inicial (ISO_AZIM) enquanto anima.
# explode segue 1-cos (vai e volta suave), varrendo o mesmo número de
# frames que o giro para fechar o loop exatamente.
assembly-animated:
	@for asm in $(ASSEMBLIES); do \
		dir=$$(dirname $$asm); \
		echo "ANIMATE ASSEMBLY $$dir"; \
		tmpdir=$$(mktemp -d); \
		$(ASM_RENDER_FRAMES) \
		if [ $$ok -eq 1 ]; then \
			eff_delay=$$(LC_NUMERIC=C awk -v d=$(ASM_ANIM_DELAY) -v s=$(ASM_ANIM_SPEED) 'BEGIN { v = d / s; print (v < 1) ? 1 : int(v + 0.5) }'); \
			$(MAGICK) -delay $$eff_delay -loop 0 $$tmpdir/frame_*.png $$dir/assembly.gif; \
			echo "  -> $$dir/assembly.gif (delay=$$eff_delay)"; \
		fi; \
		rm -rf $$tmpdir; \
	done
	@echo "-> examples/<nome>/   [assembly.gif]  $(notdir $(patsubst %/,%,$(dir $(ASSEMBLIES))))"

# Mesmo boomerang do assembly-animated, exportado como MP4 (H.264) —
# bem mais leve que o GIF equivalente, ideal para docs/ e compartilhamento.
# fps efetivo = ASM_VIDEO_FPS * ASM_ANIM_SPEED (duração do loop muda com a velocidade).
assembly-video:
	@for asm in $(ASSEMBLIES); do \
		dir=$$(dirname $$asm); \
		echo "VIDEO ASSEMBLY $$dir"; \
		tmpdir=$$(mktemp -d); \
		$(ASM_RENDER_FRAMES) \
		if [ $$ok -eq 1 ]; then \
			eff_fps=$$(LC_NUMERIC=C awk -v f=$(ASM_VIDEO_FPS) -v s=$(ASM_ANIM_SPEED) 'BEGIN { print f * s }'); \
			$(FFMPEG) -y -loglevel error -framerate $$eff_fps -i $$tmpdir/frame_%03d.png \
				-vf "format=yuv420p" -movflags +faststart \
				$$dir/assembly.mp4; \
			echo "  -> $$dir/assembly.mp4 (fps=$$eff_fps)"; \
		fi; \
		rm -rf $$tmpdir; \
	done
	@echo "-> examples/<nome>/   [assembly.mp4]  $(notdir $(patsubst %/,%,$(dir $(ASSEMBLIES))))"
