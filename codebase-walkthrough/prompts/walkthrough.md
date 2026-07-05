# Codebase walkthrough (portable prompt)

Generate — or update — an interactive, self-contained **offline** `docs/walkthrough.html` that
teaches this codebase to a junior developer. Target repo: the current working directory (or the
path I give you).

Open and follow, step by step, the skill instructions at:

    ~/repo/skills/codebase-walkthrough/skills/codebase-walkthrough/SKILL.md

and its `reference/` files (authoring-guide, flow-tracing, stack-guide, update). In short:

1. Detect CREATE vs UPDATE by checking for `docs/.walkthrough.docmap.json`.
2. Map the repo: components, entrypoints (Commands/Routes/Jobs/Tools), guardrails, roadmap.
3. **Read the real code and hand-trace each entrypoint's call lifecycle. Never invent a flow —
   verify order and params by reading. A confident wrong diagram is the failure mode to avoid.**
4. Copy `assets/template.html` → `docs/walkthrough.html` and edit ONLY its `const DATA = {…}` block
   plus the `<!-- EDIT -->` prose. Leave the generic render/animation/highlighter code untouched.
5. Keep Diátaxis discipline: the New/Architect/Flows/Runtime tabs are *explanation*; the Dev guide
   tab is a *how-to* (action only). Never mix them.
6. Emit `docs/walkthrough.html` + `docs/.walkthrough.docmap.json`, dated today, fully offline
   (no CDN, no network). On UPDATE, diff the docmap, re-narrate only drifted flows, preserve
   `<!-- KEEP -->` blocks, and print a drift report before writing.
7. Verify: load the file in a browser, confirm no console errors, every tab renders, and the
   stepper + runtime animation run. Fix, then stop.
