"""Compilador de montagem FusionBrick — ver compile.py."""

from .compile import Assembly, load
from .model import Finding, IRError, Joint, Part, Port
from .outputs import render_jobs, scad_args
from .parts import TYPES
from .variants import DESCRIPTIONS, VARIANTS

__all__ = ["Assembly", "load", "Finding", "IRError", "Joint", "Part", "Port", "render_jobs", "scad_args",
           "TYPES", "VARIANTS", "DESCRIPTIONS"]
