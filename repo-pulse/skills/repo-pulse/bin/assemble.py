#!/usr/bin/env python3
"""Install-agnostic launcher for the shared assemble step.

Resolves core/ the same way gather.py/publish.py do, then runs the real
core/assemble.py with the same arguments. Call this (stable path) instead of
reaching into core/ directly, so the skill works whether core/ is vendored,
symlinked, or cloned:

    python3 <skill>/bin/assemble.py --template … --data … --out docs/pulse.html
"""

from __future__ import annotations

import os
import runpy
import sys

from _corepath import resolve_core

core = resolve_core()
target = os.path.join(core, "assemble.py")
if not os.path.isfile(target):
    sys.exit(f"repo-pulse: found core at {core} but no assemble.py in it.")
sys.path.insert(0, core)
sys.argv[0] = target
runpy.run_path(target, run_name="__main__")
