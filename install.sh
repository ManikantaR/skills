#!/usr/bin/env bash
# Installer for the cross-harness status line. Does the SAFE automated bits
# (chmod, validate) and prints the per-harness manual steps. It never edits your
# settings files automatically — those merges are left to you.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> chmod +x scripts"
chmod +x "$HERE"/claude/bin/statusline.sh "$HERE"/copilot/statusline.sh \
         "$HERE"/repo-pulse/skills/repo-pulse/bin/gather.py \
         "$HERE"/repo-pulse/skills/repo-pulse/bin/publish.py \
         "$HERE"/codebase-walkthrough/skills/codebase-walkthrough/bin/gather.py

echo "==> validate JSON"
for f in "$HERE"/.claude-plugin/marketplace.json \
         "$HERE"/claude/.claude-plugin/plugin.json \
         "$HERE"/claude/settings.snippet.json \
         "$HERE"/copilot/settings.snippet.json \
         "$HERE"/codebase-walkthrough/.claude-plugin/plugin.json \
         "$HERE"/repo-pulse/.claude-plugin/plugin.json; do
  jq empty "$f" && echo "  ok: ${f#$HERE/}"
done

echo "==> smoke-test the shared gather engine (Python 3 stdlib)"
python3 -c "import sys; sys.path.insert(0,'$HERE/core'); import gather_lib" \
  && echo "  ok: core/gather_lib.py imports"

# codebase-walkthrough is a model-driven skill: the reliable "global from any repo"
# activation is a symlink into the user skills dir (no interactive plugin install needed).
echo "==> link model-driven skills globally (Claude Code)"
mkdir -p "$HOME/.claude/skills"
ln -sfn "$HERE/codebase-walkthrough/skills/codebase-walkthrough" "$HOME/.claude/skills/codebase-walkthrough"
echo "  linked: ~/.claude/skills/codebase-walkthrough -> codebase-walkthrough/skills/codebase-walkthrough"
ln -sfn "$HERE/repo-pulse/skills/repo-pulse" "$HOME/.claude/skills/repo-pulse"
echo "  linked: ~/.claude/skills/repo-pulse -> repo-pulse/skills/repo-pulse"

cat <<EOF

==> Next steps (pick your harness):

CLAUDE CODE
  Status line — add to ~/.claude/settings.json:
    "statusLine": { "type":"command", "command":"$HERE/claude/bin/statusline.sh", "padding":0, "refreshInterval":10 }
  Or install any plugin from the marketplace:
    /plugin marketplace add $HERE
    /plugin install statusline
    /plugin install codebase-walkthrough
    /plugin install repo-pulse
  codebase-walkthrough and repo-pulse are ALSO already linked as global user skills
  (above), so they work from any repo now — say "make a codebase walkthrough" /
  "make a status dashboard", or run /walkthrough or /pulse.

COPILOT CLI  (experimental)
  Status line: merge copilot/settings.snippet.json into ~/.copilot/settings.json (needs
  experimental features). Verify fields:  $HERE/copilot/statusline.sh debug
  Skills: link the portable prompts:
    ln -sfn $HERE/codebase-walkthrough/prompts/walkthrough.md ~/.copilot/prompts/walkthrough.md
    ln -sfn $HERE/repo-pulse/prompts/pulse.md ~/.copilot/prompts/pulse.md

CODEX CLI
  Status line (built-in): run /statusline, or append codex/config.snippet.toml to ~/.codex/config.toml
  Skills: link the portable prompts:
    mkdir -p ~/.codex/prompts
    ln -sfn $HERE/codebase-walkthrough/prompts/walkthrough.md ~/.codex/prompts/walkthrough.md
    ln -sfn $HERE/repo-pulse/prompts/pulse.md ~/.codex/prompts/pulse.md
EOF
