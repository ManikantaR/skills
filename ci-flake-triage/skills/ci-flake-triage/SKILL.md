---
name: ci-flake-triage
description: Judge whether a red CI check on a PR is a real regression that must be fixed, or infrastructure/test-isolation flakiness safe to rerun or merge through. Use when a GitHub Actions check fails and you need to decide whether it blocks a merge, when the user asks "is this a flake?", "why did CI fail?", or "should I rerun this?". Applies to any repo using GitHub Actions.
---

# CI flake triage

Don't reflexively rerun a failing check, and don't reflexively treat a failure as a real bug
either. Both mistakes cost real time in practice: rerunning without checking the log risks
merging through a genuine regression; investigating a genuine platform outage as if it were
a code bug wastes an hour chasing nothing.

## Step 1: always read the actual failure, never just the summary
```
gh run view --job <job-id> --log 2>/dev/null | grep -viE "warn|deprecat" | grep -iE "FAIL|Error|Hook timed|Test Files|Tests |Duration|passed|failed" | tail -30
```
If this returns nothing, the run may have *just* finished and GitHub's log API hasn't caught
up yet — wait ~10s and retry, or check `gh run view <run-id>` for overall status first
(sometimes the whole workflow is still `in_progress` even though one job shows failed).

## Step 2: classify the failure

**A. Confirmed external infrastructure.** Look for `RequestError [HttpError]`, `503`, or
`error connecting to <*.github.com / *.githubusercontent.com>` — including in your *own*
`gh` CLI calls, not just the workflow's. If your own `gh run view` hits the same connectivity
error, that's strong independent confirmation the platform itself is degraded right now, not
your code. Common on secondary scanners (gitleaks, CodeQL) that call back to GitHub's API
mid-run. Safe to merge through if the check isn't a hard-required one, or wait and retry.

**B. Test-isolation / environment timing flakiness.** Signature: `Hook timed out in 60000ms`
(or similar) followed by cascading auth failures (401/403, `Invalid value "undefined" for
header "Cookie"`) in a shared-DB E2E suite. **The tell is WHICH file fails**: if a rerun
fails in a *different* spec file than the first attempt (auth this time, budgets next time,
auth again after that), that randomness itself is the diagnostic — a real regression fails
the *same* test deterministically. Random-file failures with a consistent *shape* point at
CI-runner resource contention or DB/Redis connection races during sequential test-file boot,
not your diff.

**C. Likely a real regression.** The *same* test/file fails on every rerun, or the failure is
inside a class of logic you can trace directly from the diff (e.g. a DB constraint error in a
table your migration touched). Investigate the code, don't rerun blind.

## Step 3: check diff overlap before trusting your own "it's a flake" instinct
```
gh pr diff <N> --name-only
```
If the failing test file/area has zero file-level relationship to what the PR actually
changed, that raises confidence in (A) or (B). If there's a plausible connection (the PR
touched a guard, a shared module the failing test also exercises, migration/schema changes),
investigate before dismissing it as flake — don't pattern-match on "looks like the flake
we've seen before" without checking.

## Step 4: rerun/wait protocol
- One rerun (`gh run rerun <run-id> --failed`) is normal triage, not suspicious.
- If it fails again with a **different** file/signature shape than before: still likely (B).
  Rerun once more.
- If it fails **2-3 times in a row on the same PR** (even hitting different files each time),
  stop blindly rerunning. Either wait ~10 minutes (GitHub Actions platform issues do resolve)
  and retry once, or escalate: tell the user what you've ruled out and ask for a merge
  decision rather than deciding unilaterally, especially if this is the PR's first-ever clean
  run (weaker footing than "it passed once before and just needs a rerun").
- Waiting works: a batch of failures that all cleared after a ~10 minute wait is real
  evidence of (A), not a coincidence.

## What NOT to do
- Don't treat "gitleaks/CodeQL failed" as a security finding without reading the actual
  error — a `503` from GitHub's own API is not a secret-scan hit.
- Don't merge through a **required, code-adjacent** check on unverified "probably a flake"
  reasoning. Reserve merging-through for secondary/non-required checks with confirmed
  external causes, or an E2E failure you've watched clear cleanly on a rerun.
- Don't keep rerunning past 2-3 attempts without telling the user — that's burning CI
  minutes on a guess, not triage.

## Report
State the classification and evidence briefly (which log line, which pattern), not a
transcript of every command run.
