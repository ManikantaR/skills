#!/usr/bin/env bash
# Installer for the cross-harness status line. Does the SAFE automated bits
# (chmod, validate) and prints the per-harness manual steps. It never edits your
# settings files automatically — those merges are left to you.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> chmod +x scripts"
chmod +x "$HERE"/claude/bin/statusline.sh "$HERE"/copilot/statusline.sh

echo "==> validate JSON"
for f in "$HERE"/.claude-plugin/marketplace.json \
         "$HERE"/claude/.claude-plugin/plugin.json \
         "$HERE"/claude/settings.snippet.json \
         "$HERE"/copilot/settings.snippet.json \
         "$HERE"/codebase-walkthrough/.claude-plugin/plugin.json; do
  jq empty "$f" && echo "  ok: ${f#$HERE/}"
done

# codebase-walkthrough is a model-driven skill: the reliable "global from any repo"
# activation is a symlink into the user skills dir (no interactive plugin install needed).
echo "==> link codebase-walkthrough skill globally (Claude Code)"
mkdir -p "$HOME/.claude/skills"
ln -sfn "$HERE/codebase-walkthrough/skills/codebase-walkthrough" "$HOME/.claude/skills/codebase-walkthrough"
echo "  linked: ~/.claude/skills/codebase-walkthrough -> codebase-walkthrough/skills/codebase-walkthrough"

cat <<EOF

==> Next steps (pick your harness):

CLAUDE CODE
  Status line — add to ~/.claude/settings.json:
    "statusLine": { "type":"command", "command":"$HERE/claude/bin/statusline.sh", "padding":0, "refreshInterval":10 }
  Or install either plugin from the marketplace:
    /plugin marketplace add $HERE
    /plugin install statusline
    /plugin install codebase-walkthrough
  codebase-walkthrough is ALSO already linked as a global user skill (above), so
  it works from any repo now — say "make a codebase walkthrough" or run /walkthrough.

COPILOT CLI  (experimental)
  Status line: merge copilot/settings.snippet.json into ~/.copilot/settings.json (needs
  experimental features). Verify fields:  $HERE/copilot/statusline.sh debug
  Walkthrough skill: link the portable prompt:
    ln -sfn $HERE/codebase-walkthrough/prompts/walkthrough.md ~/.copilot/prompts/walkthrough.md

CODEX CLI
  Status line (built-in): run /statusline, or append codex/config.snippet.toml to ~/.codex/config.toml
  Walkthrough skill: link the portable prompt:
    mkdir -p ~/.codex/prompts
    ln -sfn $HERE/codebase-walkthrough/prompts/walkthrough.md ~/.codex/prompts/walkthrough.md
EOF
