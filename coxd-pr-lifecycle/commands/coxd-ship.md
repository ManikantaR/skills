---
description: Run the full merge -> deploy -> verify -> close -> cleanup lifecycle for a ready PR.
---

Invoke the **coxd-pr-lifecycle** skill for PR `$ARGUMENTS` (a PR number, or an issue number
if the PR isn't known yet — look it up).

Follow the skill exactly (`skills/coxd-pr-lifecycle/SKILL.md`):
1. Confirm CI is green (triage red checks with **ci-flake-triage** first); get explicit human
   go before merging.
2. `gh pr merge --squash --delete-branch`.
3. Diff the merge commit to decide deploy scope (migration? web? both?); deploy via the
   repo's own `deploy-to-nas.sh` (or the **homelab-deploy** skill if none exists).
4. Verify via `homelab-deploy`'s `scripts/verify-deploy.sh` — the real traffic path, never
   just "container is running".
5. Close the issue if it didn't auto-link; clean the worktree/branch and any external task
   store.

Arguments: `$ARGUMENTS` (PR number or issue number).
