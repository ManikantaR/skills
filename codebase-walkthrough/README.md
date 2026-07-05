# codebase-walkthrough

A cross-harness skill that generates (and later updates) a **single self-contained, offline
`docs/walkthrough.html`** teaching any codebase to a junior dev. Six audience tabs:

- **New here** — curiosity hook, optional metaphor→real-terms, stats, a guided code-walk.
- **Architect** — C4 layers (context → components → module graph), guardrails, decision log.
- **Flows** — one call-lifecycle per entrypoint (Commands / Routes / Jobs / Tools): every
  cross-module hop with method, params, responsibility, and cost/guard/stop tags. Step through it.
- **Runtime** — an animated pipeline (generated from data), token moving through stages, cost table.
- **Roadmap** — milestone timeline + task status.
- **Dev guide** — a Diátaxis how-to: prerequisites, install, run, test, config, troubleshooting.

Stacks: **Python · React/TypeScript · C# · SQL** (and mixed full-stack repos). Guided-authoring:
the agent reads the real code and hand-traces flows; the artifact is a curated, dated snapshot.

## What's in here

```
.claude-plugin/plugin.json          Claude Code plugin manifest
commands/walkthrough.md             /walkthrough slash command (Claude Code)
prompts/walkthrough.md              portable prompt (Codex / Copilot / any harness)
skills/codebase-walkthrough/        the skill itself — used by every harness
  SKILL.md                          instructions (CREATE + UPDATE modes)
  assets/template.html              the data-driven single-file template
  reference/*.md                    authoring guide, flow-tracing, per-stack guide, update/docmap
```

The **skill directory is the single source of truth**. Every harness points at it; only the
binding differs.

## Install per harness

### Claude Code (plugin)
```
/plugin marketplace add ~/repo/skills      # or the GitHub URL
/plugin install codebase-walkthrough@mani-skills
```
Then use it: say *"make a codebase walkthrough for this repo"*, or run `/walkthrough [path]`.

**Or** make it a global user skill without the plugin system (works from any repo immediately):
```
ln -s ~/repo/skills/codebase-walkthrough/skills/codebase-walkthrough ~/.claude/skills/codebase-walkthrough
```
(`install.sh` at the marketplace root does this for you.)

### Codex CLI
Codex has no "skills" system, but it reads prompt files and `AGENTS.md`. Register the portable
prompt as a custom prompt:
```
mkdir -p ~/.codex/prompts && ln -s ~/repo/skills/codebase-walkthrough/prompts/walkthrough.md ~/.codex/prompts/walkthrough.md
```
Then in Codex: `/walkthrough` (or paste the prompt). It instructs Codex to open and follow
`skills/codebase-walkthrough/SKILL.md`.

### GitHub Copilot CLI
Copilot reads custom prompt/instruction files. Point it at the same portable prompt:
```
ln -s ~/repo/skills/codebase-walkthrough/prompts/walkthrough.md ~/.copilot/prompts/walkthrough.md
```
(verify the exact prompts dir for your Copilot version), or paste `prompts/walkthrough.md` into a
Copilot session. It follows the same SKILL.md.

## Note
The skill is model-driven (unlike the `statusline` plugin, which is a script). The quality of the
walkthrough depends on the agent reading the real code and tracing flows honestly — the skill's
guardrails enforce "verify by reading, never fabricate a call."
