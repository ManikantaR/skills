---
description: Judge whether a red CI check is a real regression or safe-to-rerun/merge-through flakiness.
---

Invoke the **ci-flake-triage** skill for PR `$ARGUMENTS` (a PR number; if omitted, use the
current branch's PR).

Follow the skill exactly (`skills/ci-flake-triage/SKILL.md`):
1. Read the actual failure log, not just the pass/fail summary.
2. Classify: confirmed external infra (503s, unreachable GitHub endpoints — including in your
   own `gh` calls) / test-isolation timing flakiness (different file fails each rerun, same
   failure shape) / likely real regression (same file fails deterministically, or the diff
   plausibly touches the failing area).
3. Check whether the PR's diff overlaps the failing test area before trusting a flake call.
4. Rerun once; if it fails again with a different signature, rerun once more; if it fails 2-3
   times running, stop and either wait ~10 min + retry, or ask the user for a merge decision.

Arguments: `$ARGUMENTS` (PR number, optional).
