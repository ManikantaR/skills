# grill-me

A cross-harness skill for pressure-testing a vague plan or design, promoted here
after being found duplicated with two slightly different wordings across
MoneyPulse and moneypulse-web — drift that happens naturally once a skill lives
in more than one repo, which is exactly why it now lives in exactly one.

## What it does

Interviews the user (or the current spec) one branch of the decision tree at a
time, always proposing a recommended answer + tradeoff rather than asking
open-ended questions, and only stops once scope, file areas, validations, and
risks are all explicit.

## Install

`/plugin marketplace add ~/repo/skills` then `/plugin install grill-me`, or point
Claude at `skills/grill-me/SKILL.md` directly.

For Codex: copy `prompts/grill-me.md` into `~/.codex/prompts/`, invoke with
`/grill-me`. For Copilot CLI: point its custom-instructions mechanism at the same
file.
