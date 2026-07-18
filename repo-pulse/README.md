# repo-pulse

A cross-harness skill that generates (and later updates) a **single self-contained, offline
`docs/pulse.html`** — a status **and readiness** dashboard for any repo. Not "does it build," but
*"would you trust it in real use?"*

- **Live pipeline** (optional) — the repo's core flow as a labelled, animated hero.
- **Readiness scorecard** — six always-on dimensions scored by the engine: tests/CI, open
  criticals, security posture (Dependabot), deploy freshness, tech debt, tech stack — plus any
  **domain dimensions** the author can evidence from the repo (e.g. measured accuracy for an ML app).
- **Verdict** — one honest sentence that reconciles "what's merged" with "what's actually true in
  prod." A green board never gets to imply a working product.
- **Issue + PR board** — filterable, grouped into phases/tracks; merged PRs mapped to issues by `(#N)`.
- **Stat tiles, phase rail, attention list, footer** — all driven by data; sections hide when absent.

## Engine + judgement split

```
bin/gather.py  ──►  status.json   (deterministic: git + gh, Python 3 stdlib, no deps)
                        │
                        ▼
   LLM composes  ──►  pulse.data.json   (measured numbers + narrative/verdict)
                        │
core/assemble.py ──►  docs/pulse.html + docs/.pulse.docmap.json   (single-file, offline)
```

**Engine owns the numbers, the LLM owns the judgement, and the numbers win** — if narrative and
measurement disagree, the measurement is authoritative. Every run is cheap and identical across
harnesses because the gather step is pure Python, not a model call. Shares `core/gather_lib.py`
with the `codebase-walkthrough` skill.

## What's in here

```
.claude-plugin/plugin.json     Claude Code plugin manifest
commands/pulse.md              /pulse slash command (Claude Code)
prompts/pulse.md               portable prompt (Codex / Copilot / any harness)
skills/repo-pulse/             the skill itself — used by every harness
  SKILL.md                     instructions (CREATE + UPDATE modes)
  assets/template.html         the data-driven single-file template
  bin/gather.py                deterministic status collector (→ status.json)
  bin/publish.py               visibility-aware publishing (pages / homelab hub)
  reference/*.md               data-sources + config, readiness rubric, update/docmap
```

The **skill directory is the single source of truth**. Every harness points at it; only the
binding differs.

## Publishing — visibility-aware (privacy control, not a nicety)

`docs/pulse.html` is always written and committable. Additional "view anywhere" targets are chosen
by **repo visibility** (from the gather step):

| Target | When | Rule |
|---|---|---|
| **committed file** | always | just `docs/pulse.html` in the repo |
| **Claude Artifact** | Claude harness | private hosted link — the default "anywhere" for private repos |
| **GitHub Pages** | **public repos** | a **private** repo is **refused** unless `--public` — Pages would leak issue titles/roadmap publicly |
| **homelab hub** | opt-in | `bin/publish.py hub` scp's to a NAS static path + a private multi-repo aggregator; private to your network |

**Hard rule:** never publish a private repo's dashboard to public GitHub Pages by default.

## Install per harness

### Claude Code (plugin)
```
/plugin marketplace add ~/repo/skills      # or the GitHub URL
/plugin install repo-pulse@mani-skills
```
Then: say *"make a status dashboard for this repo"*, or run `/pulse [path]`.

**Or** make it a global user skill without the plugin system (works from any repo immediately):
```
ln -s ~/repo/skills/repo-pulse/skills/repo-pulse ~/.claude/skills/repo-pulse
```
(`install.sh` at the marketplace root does this for you.)

### Codex CLI
```
mkdir -p ~/.codex/prompts && ln -s ~/repo/skills/repo-pulse/prompts/pulse.md ~/.codex/prompts/pulse.md
```
Then in Codex: `/pulse` (or paste the prompt). It instructs Codex to open and follow
`skills/repo-pulse/SKILL.md`.

### GitHub Copilot CLI
```
ln -s ~/repo/skills/repo-pulse/prompts/pulse.md ~/.copilot/prompts/pulse.md
```
(verify the exact prompts dir for your Copilot version), or paste `prompts/pulse.md` into a session.

## Note
The gather engine is deterministic, but the **verdict and domain dimensions are model-driven** — the
skill's guardrails enforce honesty: score only what you can evidence from the repo (a doc, a test
result, an eval report), never from chat history a portable skill can't see.
