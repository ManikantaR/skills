# copilot/ — status line for GitHub Copilot CLI

Copilot CLI exposes the **same** `statusLine.command` mechanism as Claude Code
(`~/.copilot/settings.json`, stdin JSON) — but it is **experimental** (since 2026-05,
requires experimental features enabled) and uses **different JSON keys** and a
different billing model: Copilot meters **premium requests**, not Claude's 5-hour /
weekly windows. So this variant shows model · repo/branch, then context %, tokens,
and premium requests — no 5h/weekly bars.

## Install

1. Enable experimental features in Copilot CLI.
2. Merge `settings.snippet.json` into `~/.copilot/settings.json`.
3. **Verify the FIELD MAP** — the schema is unstable. Capture your real payload:
   ```
   ~/repo/skills/copilot/statusline.sh debug
   ```
   (or paste a captured payload via stdin) and adjust the `j '...'` paths near the
   bottom of `statusline.sh` to match. The current paths are defensive best-guesses.

Toggle: `statusline.sh on | off | toggle` (flag `~/.copilot/.statusline-disabled`).

Sources: tgrall.github.io/blog/2026/05/02/copilot-cli-customize-statusline ·
github.com/github/copilot-cli/issues/2342
