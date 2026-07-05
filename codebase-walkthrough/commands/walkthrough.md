---
description: Generate or update an interactive offline HTML codebase walkthrough (docs/walkthrough.html) for this repo or a given path.
---

Invoke the **codebase-walkthrough** skill for the target repo (default: the current working
directory; if the user passed a path in `$ARGUMENTS`, use that).

Follow the skill exactly (`skills/codebase-walkthrough/SKILL.md`):
- Detect CREATE vs UPDATE by checking for `docs/.walkthrough.docmap.json`.
- Read the real code; hand-trace each entrypoint's call lifecycle — never invent a flow.
- Fill only the template's `DATA` block + `<!-- EDIT -->` prose; keep the generic render code intact.
- Keep Diátaxis discipline (explanation tabs vs the how-to Dev guide).
- Emit `docs/walkthrough.html` + `docs/.walkthrough.docmap.json`, dated today, fully offline.
- Verify in a browser (no console errors, every tab renders, animations run) before finishing.

Arguments: `$ARGUMENTS` (optional target repo path).
