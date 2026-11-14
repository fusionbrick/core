SHELL := /bin/bash
AUTOMATIONS_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

include $(AUTOMATIONS_DIR)openscad.mk
include $(AUTOMATIONS_DIR)fusion.mk
include $(AUTOMATIONS_DIR)spec.mk
include $(AUTOMATIONS_DIR)assembly.mk

.PHONY: openscad-preview openscad-build

openscad-%:
	@$(MAKE) -f $(AUTOMATIONS_DIR)openscad.mk $(patsubst openscad-%,%,$@)
