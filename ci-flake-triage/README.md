# ci-flake-triage

A cross-harness skill for one recurring judgment call: **is this red CI check a real bug, or
noise?** Written after hitting the same decision repeatedly in one session — sometimes it was
a genuine GitHub Actions platform outage (confirmed by the log-fetch calls *themselves*
failing to reach GitHub), sometimes it was E2E test-isolation flakiness that hit a different
spec file every single retry, and once it was worth knowing the difference cost real time.

## The core insight

A **real regression fails the same test, the same way, every time.** Flakiness (whether
platform-side or test-isolation) tends to fail *differently* — a different file, a different
error shape, or it clears entirely on a rerun. That randomness is itself diagnostic, not just
an annoyance to route around.

## What it's not

This skill doesn't tell you to always rerun, and it doesn't tell you to always investigate.
It's a classification + evidence-gathering procedure, ending in either "safe to proceed" or
"here's what I've ruled out, your call" — never a silent unilateral merge-through on a
required, code-adjacent check.

## Relationship to other skills

Used as step 1 of **coxd-pr-lifecycle**'s merge gate — a red check gets triaged here before
the lifecycle skill decides whether to proceed.

## Install

`/plugin marketplace add ~/repo/skills` then `/plugin install ci-flake-triage`, or point
Claude at `skills/ci-flake-triage/SKILL.md` directly — it auto-triggers on "is this a flake",
"why did CI fail", "should I rerun this", or when a check goes red on a PR you're driving.

For Codex: copy `prompts/ci-flake-triage.md` into `~/.codex/prompts/`, invoke with
`/ci-flake-triage`. For Copilot CLI: point its custom-instructions mechanism at the same file
(verify your current setup — no established convention for this in this repo yet).
