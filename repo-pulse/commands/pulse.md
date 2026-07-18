---
description: Generate or update an interactive offline status + readiness dashboard (docs/pulse.html) for this repo or a given path.
---

Invoke the **repo-pulse** skill for the target repo (default: the current working directory;
if the user passed a path in `$ARGUMENTS`, use that).

Follow the skill exactly (`skills/repo-pulse/SKILL.md`):
- Detect CREATE vs UPDATE by checking for `docs/.pulse.docmap.json`.
- Run `bin/gather.py` to produce the measured `status.json` — never hand-type counts.
- Read the roadmap sources (README/ROADMAP/SPEC + optional `pulse.config.json`) and compose
  `pulse.data.json` = status.json + narrative (tagline, pipeline, verdict, groups, readiness).
- Keep readiness **honest** — surface the gap between what's merged and what's actually live.
- Run `core/assemble.py` to emit a single-file offline `docs/pulse.html` + docmap, dated today.
- Verify in a browser (no console errors, sections render, filters + theme toggle work).
- Publish visibility-aware (never a private repo's board to public Pages); link it in chat and
  report the readiness verdict + top blockers.

Arguments: `$ARGUMENTS` (optional target repo path; optional `--publish <target>`).
