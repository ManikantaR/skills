# claude/ — status line for Claude Code

A Claude Code **plugin** (marketplace-installable) that ships:
- `bin/statusline.sh` — the two-line status line (added to `$PATH` when the plugin is enabled)
- `commands/regen-statusline.md` — `/regen-statusline`, regenerates the script from intent
- `settings.snippet.json` — the `statusLine` block to add to `settings.json`

## What it shows

```
Opus 4.8 · smartocrprocess · ⎇ main
5h ▓▓▓▓░░░░░░ 41% ↻2h30m │ wk ▓▓▓▓▓▓░░░░ 63% ↻3d16h │ ctx ▓▓▓░░░░░░░ 34% │ $0.87 │ ~1h20m→cap
```

- **5h / wk** — native `rate_limits.five_hour` / `.seven_day` (Pro/Max only, after the
  first API response; degrades to `--` if absent, incl. regression #40094)
- **ctx** — `context_window.used_percentage`; **$** — `cost.total_cost_usd`
- **→cap** — derived: EMA of the 5h-% delta between refreshes projects time-to-100%
  (`safe→reset` if the window resets first); state in `$TMPDIR/cc-statusline/`
- Muted 256-color palette: sage <60% → amber <85% → terracotta ≥85%

## Install

Option A — direct (dotfiles style): point `statusLine.command` at
`~/repo/skills/claude/bin/statusline.sh` using `settings.snippet.json`.

Option B — plugin: `/plugin marketplace add ~/repo/skills` → `/plugin install statusline`.
Then still add the `statusLine` block manually (plugins can't set it).

Toggle without editing settings: `statusline.sh on | off | toggle`
(flag file `~/.claude/.statusline-disabled`).
