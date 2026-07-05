# UPDATE mode — idempotent regeneration + drift detection

When `docs/.walkthrough.docmap.json` exists, you're updating, not creating. Goal: refresh the
artifact to match the current code, preserve human edits, and tell the user exactly what changed.

## The docmap sidecar

Written next to the HTML as `docs/.walkthrough.docmap.json`. It's the machine-readable memory that
makes updates honest and diffable:

```json
{
  "generated": "2026-07-05",
  "stacks": ["python"],
  "components": ["orchestrator","watcher","control-plane","workers","gate"],
  "entrypoints": {
    "dispatch": {"group":"Commands","file":"cox/dispatch.py","steps":15},
    "gate":     {"group":"Commands","file":"cox/gate.py","steps":11}
  },
  "guards": ["P1","P2","...","P10"],
  "roadmap": {"M0":[13,14],"M1":[0,1]},
  "hashes": { "cox/dispatch.py":"<sha1-of-file>", "cox/gate.py":"<sha1>" }
}
```

Include a `hashes` entry for every source file you traced (compute a sha1 of the file contents).

## Procedure

1. **Read** the existing `docs/.walkthrough.docmap.json` and `docs/walkthrough.html`.
2. **Re-map** the repo (SKILL.md steps 1–2): current components, entrypoints, guards, roadmap.
3. **Diff** against the docmap:
   - **file hash changed** for a traced file → re-read it and re-narrate that flow / snippet.
   - **new entrypoint / component / guard** → add it.
   - **removed** → drop its data (and any code snippet that referenced it).
   - **roadmap/task-status shifts** → update `roadmap` counts and pills.
   - files whose hash is unchanged → **leave their narration as-is** (don't churn stable prose).
4. **Preserve keep-blocks.** Any `<!-- KEEP --> … <!-- /KEEP -->` region in the existing HTML is
   copied verbatim into the new one. Never overwrite hand-tuned content inside them.
5. **Re-date.** Set `meta.date` and the footer to today. Keep it a curated snapshot.
6. **Report drift BEFORE writing.** Print a short changelog:
   `+ added flow "webhook" (Routes)`, `~ dispatch flow changed (dispatch.py edited)`,
   `- removed flow "legacy-sync"`, `~ M0 12/14 → 14/14`. Then write both files.
7. **Verify** as in CREATE (load it, no console errors, tabs render, animation runs).

## Idempotence

Running UPDATE twice with no code changes must produce a byte-identical HTML except the date. If it
doesn't, you churned stable content — stop and narrow the change to what actually drifted.

## When the template itself has changed

If this skill's `assets/template.html` is newer than the generated file's template version (a
`data-tpl` version attribute on `<html>`), migrate: re-emit from the new template, re-inserting the
current `DATA` block and keep-blocks. Note the template bump in the drift report.
