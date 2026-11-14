"""Nome histórico do compilador de montagem. O código vive em `fusionbrick.asm`."""

from .asm import *  # noqa: F401,F403
from .asm import Assembly, IRError, load, render_jobs, scad_args  # noqa: F401
