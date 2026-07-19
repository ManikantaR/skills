"""Install-agnostic locator for the shared core/ (gather_lib.py, assemble.py, …).

The skills share one `core/` at the marketplace root, but a skill dir may be
installed several ways — symlinked, cloned, or *plain-copied* into a harness's
skills/prompts dir (Codex/Copilot). A hard-coded `../../../../core` only works
for the in-repo layout, so resolve robustly instead. First match wins:

  1. $REPO_PULSE_CORE                     explicit override
  2. <this dir>/_core                     vendored copy (install.sh writes this)
  3. <ancestor>/core                      walk up for the in-repo / cloned layout
  4. <this dir>/../../../../core          legacy relative fallback

Vendoring (2) is what makes a plain copy self-contained; the walk-up (3) covers
symlink/clone installs without duplication.
"""

from __future__ import annotations

import os

_MARKER = "gather_lib.py"


def resolve_core():
    here = os.path.dirname(os.path.abspath(__file__))
    cands = []
    env = os.environ.get("REPO_PULSE_CORE")
    if env:
        cands.append(env)
    cands.append(os.path.join(here, "_core"))
    d = here
    for _ in range(10):
        cands.append(os.path.join(d, "core"))
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    cands.append(os.path.join(here, "..", "..", "..", "..", "core"))
    for c in cands:
        if c and os.path.isfile(os.path.join(c, _MARKER)):
            return os.path.abspath(c)
    raise SystemExit(
        "repo-pulse: could not locate the shared core/ (looked for %s). "
        "Set REPO_PULSE_CORE=/path/to/core, or run the marketplace install.sh to "
        "vendor it into this skill." % _MARKER)
