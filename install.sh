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
         "$HERE"/copilot/settings.snippet.json; do
  jq empty "$f" && echo "  ok: ${f#$HERE/}"
done

cat <<EOF

==> Next steps (pick your harness):

CLAUDE CODE
  Add to ~/.claude/settings.json:
    "statusLine": { "type":"command", "command":"$HERE/claude/bin/statusline.sh", "padding":0, "refreshInterval":10 }
  Or install as a plugin:
    /plugin marketplace add $HERE
    /plugin install statusline
  Toggle:  $HERE/claude/bin/statusline.sh toggle

COPILOT CLI  (experimental)
  Enable experimental features, then merge copilot/settings.snippet.json into
  ~/.copilot/settings.json. Verify field names:
    $HERE/copilot/statusline.sh debug

CODEX CLI  (built-in, no script)
  Run /statusline inside Codex, or append codex/config.snippet.toml to ~/.codex/config.toml
EOF
