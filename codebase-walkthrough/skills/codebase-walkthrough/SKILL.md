---
name: codebase-walkthrough
description: Generate or update an interactive, self-contained HTML walkthrough that teaches a codebase — architecture (C4), guided code-walk, per-entrypoint call-flow lifecycles, animated runtime flow, roadmap/task status, and a dev build/install/run guide. Use when the user asks to "explain this codebase visually", "make a walkthrough/onboarding page", "document the architecture and flows", "create/update the code walkthrough", or points at a repo (Python, React/TypeScript, C#, or SQL) and wants a teaching artifact a junior dev can navigate. Produces a dated, offline, single-file docs/walkthrough.html.
---

# Codebase Walkthrough

Build a **single self-contained HTML file** (`docs/walkthrough.html`) that teaches a repo to a
junior developer, and update it in place on later runs. Curated, hand-narrated, but structurally
accurate — you read the real code and trace real call paths; you never invent flows.

## Two modes

- **CREATE** — no `docs/walkthrough.html` (or no `docs/.walkthrough.docmap.json`) exists yet. Analyze
  the repo from scratch, fill the template, write both files.
- **UPDATE** — those files exist. Re-read the repo, refresh the data, **preserve human edits marked
  with `<!-- KEEP -->`**, re-date the snapshot, and report what drifted. See `reference/update.md`.

Decide the mode by checking for `docs/.walkthrough.docmap.json` first.

## Core principles (do not violate)

1. **Structurally accurate, hand-narrated.** Every call-flow row must correspond to a real
   call you verified by reading the code. If unsure, open the file — do not guess. Wrong flows are
   worse than no flows.
2. **Diátaxis discipline — never mix doc types.** The New/Architect/Flows/Runtime tabs are
   *explanation*. The Dev guide tab is a *how-to* (action only, no "why"). Keep them separate.
3. **Self-contained & offline.** One file. Inline all CSS/JS/SVG. No CDN, no build step, no network.
4. **Dated, curated snapshot.** Stamp today's date; tell the reader to regenerate at milestones.
5. **Accessible.** Keep the template's dark/light, `prefers-reduced-motion`, and keyboard-nav intact.
6. **Metaphor as scaffolding, then real terms** (if the project has a natural metaphor) — introduce
   an idea intuitively, then immediately map it to the real component/file.

## Procedure (CREATE)

Work in this order. Use TaskCreate to track it if the repo is non-trivial.

0. **Gather the measured facts first.** Run `bin/gather.py` (shares repo-pulse's engine,
   `core/gather_lib.py` — Python 3 stdlib, no deps):

   ```
   python3 skills/codebase-walkthrough/bin/gather.py /path/to/repo -o walkthrough.facts.json
   ```

   It emits the numbers you must **never hand-count** — `measured_stats` (LOC, source/test files,
   languages → drop straight into `DATA.meta.stats`), `tech_stack` (languages + framework versions),
   `git` state, and a `roadmap_skeleton` grouped by milestone (refine its titles/copy → `DATA.roadmap`).
   Everything else in DATA is judgement you author by reading the code. **Engine owns the numbers, you
   own the narrative.** (No `gh`/remote → repo/roadmap come back empty; stats + stack still work.)

1. **Map the repo.** Detect the stack(s) and read `reference/stack-guide.md` for how to find
   entrypoints and trace flows in Python / React-TS / C# / SQL. Build a short list of:
   - the 4–6 top-level **components** (C4 "container/component" level),
   - the **entrypoints** — group them as **Commands / Routes / Jobs / Tools** (whatever fits: CLI
     subcommands, HTTP routes, background jobs, adapters, stored procs),
   - the 5–10 **guardrails / invariants** that actually matter, each with the file that enforces it,
   - the **roadmap / task status** if the repo has ROADMAP/TASKS/issues; else omit that tab's data.
2. **Trace each entrypoint** into a call lifecycle (see `reference/flow-tracing.md`): entry → the
   meaningful cross-module hops, each with `method(params)`, one-line responsibility, and tags.
   Collapse trivial helpers. 6–15 rows per flow. **Read the code to confirm the order.**
3. **Pick the runtime "hero" flow** — the one pipeline that best explains the system (e.g. request
   → handler → service → store → response). It becomes the animated Runtime tab (a `STAGES` array).
4. **Fill the template.** Copy `assets/template.html` to `docs/walkthrough.html` and edit ONLY the
   `const DATA = {…}` block near the top of its `<script>` plus the intro prose placeholders marked
   `<!-- EDIT -->`. The rendering/animation/highlighter code is generic — don't touch it. Field-by-
   field guidance is in `reference/authoring-guide.md`.
5. **Write the Dev guide** (`DATA.dev`) strictly as how-to: prerequisites, install, run, test,
   common tasks, config, troubleshooting — real copy-pasteable commands from THIS repo.
6. **Emit the docmap.** Write `docs/.walkthrough.docmap.json` (schema in `reference/update.md`):
   the date, detected stacks, components, entrypoints + their flow-step counts, and a content hash
   per source file you traced. This is what UPDATE diffs against.
7. **Verify.** Open the file (a static server + the browser preview, or just load it) and confirm:
   no console errors, every tab renders, the stepper and the runtime animation run. Fix, then stop.

## Procedure (UPDATE)

Read `reference/update.md`. In short: re-run step 1–2, diff against the stored docmap, re-narrate
only drifted flows, keep `<!-- KEEP -->` blocks verbatim, bump the date, and print a drift report
(new/removed/changed entrypoints, task-status shifts) before writing.

## Files in this skill

- `bin/gather.py` — deterministic facts collector (shares `core/gather_lib.py` with repo-pulse).
  Run it first (step 0); fold `measured_stats` / `tech_stack` / `roadmap_skeleton` into `DATA`.
- `assets/template.html` — the single-file template. Edit only its `DATA` block + `<!-- EDIT -->` prose.
- `reference/authoring-guide.md` — field-by-field: what each `DATA` key means and how to write it well.
- `reference/flow-tracing.md` — how to turn code into an honest call lifecycle without a hairball.
- `reference/stack-guide.md` — finding entrypoints & tracing flows in Python, React/TS, C#, SQL.
- `reference/update.md` — docmap schema, drift detection, keep-blocks, idempotent regeneration.

## Guardrails for you, the author

- Do not fabricate a call, a file path, or a number. Verify by reading. Mark anything uncertain and
  ask, rather than shipping a confident wrong diagram.
- Keep the file offline: if you're tempted to add a CDN link or a web font, don't.
- One file out (`docs/walkthrough.html`) + one sidecar (`docs/.walkthrough.docmap.json`). Nothing else.
