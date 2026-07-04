# skills

Personal, cross-harness agent tooling. Single source of truth so a customization
is authored once and carried to any machine (personal → work) and any harness.

First (and currently only) artifact: **the status line** — 5-hour / weekly rate
limits, context %, cost, and a derived *time-until-cap*.

## Why this is a repo, not a loose script

The status line is fundamentally a **script** (the harness invokes it every refresh;
the model is not involved — so it is *not* a skill or a prompt). But "a script" isn't
portable by itself: each harness has a different config binding and a different stdin
payload. This repo packages the script per harness plus a regeneration prompt.

## Harness support matrix

| Harness | Mechanism | Rate limits available? | This repo ships |
|---|---|---|---|
| **Claude Code** | `statusLine.command` in `~/.claude/settings.json`, stdin JSON | ✅ native `rate_limits.five_hour` + `.seven_day` (Pro/Max) | `claude/` — working script + Claude Code plugin + `/regen-statusline` |
| **GitHub Copilot CLI** | `statusLine.command` in `~/.copilot/settings.json` (⚠ experimental, 2026-05), stdin JSON | ❌ meters *premium requests*, not 5h/weekly | `copilot/` — adapter script (context/tokens/premium); FIELD MAP to verify |
| **Codex CLI** | built-in `[tui].status_line` in `~/.codex/config.toml` or `/statusline` picker — **no script** | ✅ native `rate_limits` item (5h + weekly) | `codex/` — config snippet enabling the built-in items |

Key point: **Codex needs no script** (it has a native rate-limit item); **Copilot**
shares Claude's command mechanism but different JSON keys and no 5h/weekly concept.

## Install

Run `./install.sh` (chmods scripts, validates JSON, prints the per-harness steps),
then follow the harness you want:

- **Claude Code** — either symlink/point `statusLine.command` at
  `claude/bin/statusline.sh` (see `claude/settings.snippet.json`), or install as a
  plugin: `/plugin marketplace add ~/repo/skills` then `/plugin install statusline`.
  Plugins **cannot** set `statusLine`, so you still add that one block to
  `settings.json` manually. Toggle: `statusline.sh on|off|toggle`.
- **Copilot CLI** — merge `copilot/settings.snippet.json` into `~/.copilot/settings.json`
  (needs experimental features on). Run `copilot/statusline.sh debug` once to capture
  your real payload and correct the FIELD MAP.
- **Codex CLI** — run `/statusline` in Codex, or append `codex/config.snippet.toml`
  to `~/.codex/config.toml`.

## Portability notes

- Snippets use `~/repo/skills/...`; on a locked-down work box where `~/.claude` isn't
  writable, set `CLAUDE_CONFIG_DIR=/writable/path/.claude` (Claude Code ≥ v2.1.181).
- The scripts are self-contained (jq + git only) — no Node/ccusage.
- Lost the script? `claude/commands/regen-statusline.md` regenerates it from intent.
