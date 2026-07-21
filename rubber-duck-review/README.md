# rubber-duck-review

A cross-harness skill for a five-statement self-review, promoted here after being
found duplicated byte-for-byte across three separate repos (MoneyPulse, MyMoney,
moneypulse-web) — a sign it belonged in one place rather than three copy-pasted ones.

## What it does

Forces five explicit statements before any plan, spec, implementation, or fix is
treated as done: the exact problem, the smallest solving change, the invariant that
must hold, the validation that proves success, and the next likely failure mode.
Deliberately mechanical — the point is to surface hand-waving, not to produce prose.

## Install

`/plugin marketplace add ~/repo/skills` then `/plugin install rubber-duck-review`, or
point Claude at `skills/rubber-duck-review/SKILL.md` directly.

For Codex: copy `prompts/rubber-duck-review.md` into `~/.codex/prompts/`, invoke with
`/rubber-duck-review`. For Copilot CLI: point its custom-instructions mechanism at the
same file.
