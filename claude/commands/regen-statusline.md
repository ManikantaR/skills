---
description: Regenerate the Claude Code status line script from intent (portable, no source needed)
---

Create a Claude Code status line at `~/.claude/statusline.sh` (bash; deps: jq + git
only — NO ccusage/Node) and wire it into `~/.claude/settings.json`.

DATA SOURCE — the statusLine stdin JSON (see code.claude.com/docs/en/statusline).
Use these native fields, each with a safe `// empty` / `// 0` jq fallback:
  - `rate_limits.five_hour.used_percentage` + `.resets_at`   (5-hour rolling window)
  - `rate_limits.seven_day.used_percentage` + `.resets_at`   (weekly limit)
  - `context_window.used_percentage`
  - `cost.total_cost_usd`
  - `workspace.current_dir`, `workspace.repo.name`, `model.display_name`
  Note: `rate_limits` appears only for Pro/Max AFTER the first API response and can
  be absent per account (regression #40094) — degrade to "5h --" / "wk --".

LAYOUT — two lines:
  Line 1: `model · repo · ⎇ branch`   (branch via `git -C <cwd> rev-parse`)
  Line 2: `5h bar+% (↻reset) │ wk bar+% (↻reset) │ ctx bar+% │ $cost │ time-until-cap`
  Bars = 10 cells (▓ filled / ░ empty).

COLORS — muted 256-color, professional (not neon):
  sage 108 (<60% used) → amber 179 (<85%) → terracotta 167 (≥85%);
  grey 244 separators/dim, mauve 139 model, teal 109 repo, slate 103 branch.

BURN / TIME-UNTIL-CAP — not in the payload; derive it: keep per-session state in
  `$TMPDIR/cc-statusline/<session_id>.state`; each refresh compute the 5h
  `used_percentage` delta over elapsed time, EMA-smooth the rate, project seconds to
  100%. If the window resets before that, show "safe→reset"; else "~<dur>→cap".
  If usage is flat/decreasing (idle or window reset), show "burn idle".

TOGGLE — `statusline.sh on|off|toggle` manages a flag file
  `~/.claude/.statusline-disabled`; when present the script prints nothing and exits 0.
  A no-arg invocation (how Claude Code calls it) must render normally.

SETTINGS — add: `statusLine {type:"command", command:"~/.claude/statusline.sh",
  padding:0, refreshInterval:10}`. Validate settings.json parses. Test with mock
  payloads: full data, missing rate_limits, high-usage (red), and two successive
  readings to confirm the burn ETA appears.
