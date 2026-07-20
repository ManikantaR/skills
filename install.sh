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
         "$HERE"/repo-pulse/skills/repo-pulse/bin/assemble.py \
         "$HERE"/codebase-walkthrough/skills/codebase-walkthrough/bin/gather.py

# Vendor the shared core into each skill's bin/_core so a *plain copy* of a skill
# dir (e.g. into ~/.codex/skills) is self-contained — no dependency on the repo
# layout. core/ stays the single source of truth; these copies are generated.
echo "==> vendor shared core into skills"
vendor_core () {  # $1 = skill bin dir ; $2.. = core files to copy
  local dest="$1/_core"; shift
  mkdir -p "$dest"
  for f in "$@"; do cp "$HERE/core/$f" "$dest/$f"; done
}
vendor_core "$HERE/repo-pulse/skills/repo-pulse/bin" gather_lib.py assemble.py chassis.css render.js
vendor_core "$HERE/codebase-walkthrough/skills/codebase-walkthrough/bin" gather_lib.py
echo "  vendored core -> repo-pulse + codebase-walkthrough bin/_core/"

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
