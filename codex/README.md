# codex/ — status line for OpenAI Codex CLI

Codex is different from Claude/Copilot: there is **no custom-command hook**. The
footer status line is **built in** and configured as an ordered list of native
items. Codex already exposes **5-hour + weekly rate limits** natively, so you get
the same visibility as the Claude script without any code.

## Configure

Either:
- **Interactive:** run `/statusline` inside Codex — a multi-select picker with live
  preview and ordering. (Easiest; also shows the exact item identifiers.)
- **Declarative:** append `config.snippet.toml` to `~/.codex/config.toml`.

The snippet enables `model`, `context`, `rate_limits`, `git`, `tokens` with theme
colors on. Confirm exact identifier spellings via `/statusline` or the config
reference — they are inferred here.

Sources: developers.openai.com/codex/config-reference ·
github.com/openai/codex/pull/10546 (the `/statusline` command)

## Skills (portable prompts)

Codex has no skills system, but it reads custom prompt files. The model-driven skills in this repo
ship a portable prompt that tells Codex to open and follow the shared `SKILL.md`:

```
mkdir -p ~/.codex/prompts
ln -sfn ~/repo/skills/codebase-walkthrough/prompts/walkthrough.md ~/.codex/prompts/walkthrough.md
ln -sfn ~/repo/skills/repo-pulse/prompts/pulse.md               ~/.codex/prompts/pulse.md
```

Then use `/walkthrough` or `/pulse` in Codex. (`../install.sh` prints these steps too.)
