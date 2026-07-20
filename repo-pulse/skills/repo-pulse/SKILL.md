---
name: repo-pulse
description: Generate or update an interactive, self-contained HTML status dashboard for any repo — a live pipeline, phase/roadmap progress, a filterable issue+PR board, and an always-on readiness scorecard (tests/CI, open criticals, security, deploy freshness, tech debt, tech stack). Use when the user asks for a "status dashboard", "repo status page", "readiness assessment", "where are we / what's left visually", "project pulse", or runs /pulse. Produces a dated, offline, single-file docs/pulse.html, viewable anywhere via a visibility-aware publish step. Works on any Git repo; richer when the repo has GitHub issues/PRs.
---

# repo-pulse

Turn any repo into a **single self-contained `docs/pulse.html`** — a scannable, interactive
status + readiness board — and update it in place on later runs. A **portable Python engine**
(`bin/gather.py`) does the measuring; **you (the LLM)** add judgement and narrative; a shared
template renders it. The split keeps every run cheap, deterministic, and identical across
Claude / Codex / Copilot.

## The pipeline
```
bin/gather.py  →  status.json      (mechanical: git, gh, CI, security, stack, debt, readiness scores)
you            →  pulse.data.json  (status.json + narrative: tagline, pipeline, verdict, groups, domain readiness)
assemble.py    →  docs/pulse.html  (+ docs/.pulse.docmap.json)   ← single-file, offline
publish.py     →  view-anywhere    (visibility-aware: committed / Artifact / Pages / homelab)
```

## Two modes
- **CREATE** — no `docs/.pulse.docmap.json` exists. Build from scratch.
- **UPDATE** — it exists. Re-gather, refresh the DATA, **preserve any narrative the human marked
  with `"keep": true`** on a field or in `pulse.config.json`, re-date, and print a drift report
  (what changed since last run). See `reference/update.md`.

Decide the mode by checking for `docs/.pulse.docmap.json` first.

## Core principles (do not violate)
1. **Measured, then judged.** Numbers (issue/PR counts, CI, alerts, stack, debt, ahead/behind)
   come from `gather.py` — never hand-type them. Your job is the *narrative*: what it means, the
   readiness verdict, the pipeline, the roadmap framing. Don't contradict the measured data.
2. **Honest readiness.** "Deployed & green" ≠ "works well." Surface the gap between what's merged
   and what's actually live/proven. A confident-but-wrong "all good" is the failure mode to avoid.
3. **Self-contained & offline.** One file. Inline everything (assemble.py handles it). No CDN,
   no build step, no network at view time. GitHub links are fine.
4. **Privacy-aware publishing.** Never push a *private* repo's dashboard to public GitHub Pages.
   Default to committed file + (Claude) Artifact + homelab. See `reference/data-sources.md` §publish.
5. **Dated, curated snapshot.** Stamp the date; tell the reader to re-run at milestones.
6. **Accessible.** Keep the template's dark/light, `prefers-reduced-motion`, focus states, and
   keyboard-reachable controls intact.

## Procedure (CREATE)

Use TaskCreate to track these if the repo is non-trivial.

1. **Gather.** Run the engine against the target repo (default: cwd):
   ```
   python3 <skill>/bin/gather.py <repo> -o /tmp/status.json
   ```
   It degrades gracefully with no `gh`/network. Read the printed summary + the JSON. **If
   `status.json` has a top-level `warning` (GitHub data unavailable), copy it verbatim into
   `DATA.warning` and treat every issue/PR/security count as *unknown*, never zero — a repo whose
   tracker you couldn't read is not a repo with no issues.**

2. **Read the roadmap sources** the engine can't judge: `README`, `ROADMAP.md`, `SPEC.md`,
   any `docs/*plan*`, and an optional **`pulse.config.json`** (phases, display name, readiness
   criteria, publish targets, pipeline — see `reference/data-sources.md`). Config values win.

3. **Compose `pulse.data.json`** = the measured `status.json` **plus** your narrative. Build the
   DATA object described in "DATA schema" below:
   - **Group issues** into phases/tracks. Prefer `phase:N` / track labels; else infer from the
     roadmap doc; else one flat "Backlog" group. Map each issue's `state` (done/prog/open), owner,
     and — where a merged PR closed it — its `pr` number (parse `(#N)` from PR titles).
   - **Phases** (optional): only if the project actually has an ordered roadmap. Don't invent
     phases for a repo that has none — omit the rail instead.
   - **Pipeline** (optional): only if the repo has a natural runtime flow worth showing (a data
     pipeline, request lifecycle, build→deploy). Omit for a plain library.
   - **Readiness**: start from `status.json.readiness` (the 6 engine dims). Refine each `finding`
     into plain language, add a `ref` (issue link or action). **Add domain dims** the engine can't
     see (e.g. "accuracy unmeasured", "LLM path degraded in prod") when you have real evidence
     from the repo — never from chat history alone. See `reference/readiness.md`.
   - **Verdict**: one honest sentence on "is it ready for its actual use?" with a `tone`.
   - **Attention**: the 2–5 things truly blocking. Include non-issue operational blockers as
     `{id:"◆", label, title}` (no href).

4. **Assemble.**
   ```
   python3 <skill>/bin/assemble.py --template <skill>/assets/template.html \
       --data /tmp/pulse.data.json --out docs/pulse.html --title "<Repo> — status" --favicon 🗂️
   ```

5. **Verify.** Serve `docs/` over http (`python3 -m http.server`) and open `docs/pulse.html` in a
   browser. Confirm: no console errors, every present section renders, filters + phase-click work,
   theme toggle works. Fix, then continue.

6. **Publish** per `reference/data-sources.md` §publish (visibility-aware). At minimum the file is
   committed; offer the right "view anywhere" target for the repo's visibility.

7. **Report** the readiness verdict + top blockers in chat, and link the published dashboard.

## DATA schema (what the template renders)

All fields optional unless noted; absent sections hide. `finding`/`ref`/`text`/`note` may contain
safe inline HTML (`<b>`, `<a>`). Everything else is escaped.

```jsonc
{
  "generated_at": "ISO",                      // from gather.py
  "repo": { "name","slug","visibility","url","description" },
  "repo_url": "https://github.com/owner/repo",// base for #issue links
  "eyebrow": "Build status · YYYY-MM-DD",
  "display_name": "DocuPulse",                // optional pretty title (else repo.name)
  "tagline": "one line on what this is",
  "warning": "carried verbatim from status.json.warning when GitHub data is unavailable",
  "live": [ {"label":"Live · API 200","kind":"good|warn|neutral"} ],
  "pipeline": { "caption","sub","note",
                "stages":[ {"b":"Local LLM","l":"qwen2.5:7b","kind":"key|human|null"} ] },
  "verdict": { "tone":"solid|gap|blocker", "text":"honest sentence" },
  "readiness_meta": "6 automated signals + product judgement",
  "readiness": [ {"dim","status":"solid|measuring|gap|blocker","label","finding","ref"} ],
  "tiles": [ {"k","v","small","sub","bar":0-100} ],   // optional; else derived from summary
  "rail_title","rail_meta",
  "phases": [ {"id":"p0","tag":"P0","label":"Stabilize","status":"complete|partial|none","done":7,"total":7} ],
  "groups": { "p0": {"label","tag"} },        // for issue tags
  "issues_meta",
  "issues": [ {"n","t","state":"done|prog|open","group","track":"main|<trackId>","owner","pr","note","attn":bool} ],
  "tracks": [ {"id":"v2","label":"v2 — …","meta":"epic #57"} ],   // extra boards below main
  "attn_meta",
  "attention": [ {"id":"#60|◆","label":"live parity","title":"…","href":"…"} ],
  "stack": ["Python","fastapi","next 16.2.6"],
  "footer":"Generated … by repo-pulse …",
  "summary": {…}, "git": {…}                  // pass through from status.json (tiles use them)
}
```

## Notes
- `<skill>` = this skill dir. `bin/assemble.py` and `bin/gather.py` locate the shared `core/`
  themselves (env `REPO_PULSE_CORE` → vendored `bin/_core` → walk-up → relative), so they work
  whether the skill is symlinked, cloned, or plain-copied into another harness.
- The engine is the source of truth for counts; if your narrative and the numbers disagree, the
  numbers win — fix the narrative.
- Keep the whole thing under a few seconds of LLM work: the engine did the heavy lifting.
