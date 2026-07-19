# repo-pulse (portable prompt)

Generate — or update — an interactive, self-contained **offline** `docs/pulse.html`: a status +
readiness dashboard for this repo. Target: the current working directory (or the path I give you).

Open and follow, step by step, the skill instructions at:

    ~/repo/skills/repo-pulse/skills/repo-pulse/SKILL.md

and its `reference/` files (data-sources, readiness, update). In short:

1. Detect CREATE vs UPDATE by checking for `docs/.pulse.docmap.json`.
2. **Gather** the measured baseline — run the engine (never hand-type counts):
   ```
   python3 ~/repo/skills/repo-pulse/skills/repo-pulse/bin/gather.py . -o /tmp/status.json
   ```
   It shells out to git + gh and degrades gracefully with neither. Read the JSON.
3. Read the roadmap sources (README/ROADMAP/SPEC + optional `pulse.config.json`) and **compose**
   `/tmp/pulse.data.json` = the measured `status.json` **plus** narrative: tagline, an optional
   pipeline, an honest readiness verdict, issue→phase/track grouping (map merged PRs by `(#N)`),
   and readiness cards (start from the engine's 6 dims; add domain dims you can evidence from the
   repo). Numbers come from the engine; if narrative and numbers disagree, the numbers win.
4. **Assemble** the single-file artifact:
   ```
   python3 ~/repo/skills/repo-pulse/skills/repo-pulse/bin/assemble.py \
     --template ~/repo/skills/repo-pulse/skills/repo-pulse/assets/template.html \
     --data /tmp/pulse.data.json --out docs/pulse.html --title "<Repo> — status"
   ```
5. **Verify** in a browser: serve `docs/` (`python3 -m http.server`), open `pulse.html`, confirm
   no console errors, sections render, filters + phase-click + theme toggle work. Fix, then stop.
6. **Publish** visibility-aware (see the skill): committed file always; for a *private* repo use a
   private target (homelab / hosted), NEVER public GitHub Pages. Report the verdict + blockers.

Keep it honest and offline. On UPDATE, diff the docmap, preserve `"keep":true` narrative, re-date,
and print a drift report before writing.
