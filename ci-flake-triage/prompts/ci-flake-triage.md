# CI flake triage (portable prompt)

Judge whether a red GitHub Actions check on a PR is a real regression that must be fixed, or
infrastructure/test-isolation flakiness safe to rerun or merge through.

Open and follow, step by step, the skill instructions at:

    ~/repo/skills/ci-flake-triage/skills/ci-flake-triage/SKILL.md

In short:

1. Read the actual failure log (`gh run view --job <id> --log`), never just the summary.
2. Classify: (A) confirmed external GitHub infra issue (503s, unreachable endpoints, even in
   your own `gh` calls) -> safe to merge through non-required checks or retry; (B) test
   isolation/timing flakiness -> the tell is a DIFFERENT spec file failing each rerun with the
   same failure shape -> rerun; (C) same file fails every time, or the diff plausibly touches
   the failing area -> real regression, investigate the code.
3. Check `gh pr diff <N> --name-only` against the failing area before trusting a flake call.
4. Rerun etiquette: one rerun is normal; 2-3 failures in a row on the same PR means stop
   rerunning blindly — wait ~10 min and retry once, or ask the user for a merge decision.

Report the classification and the evidence briefly, not a full transcript.
