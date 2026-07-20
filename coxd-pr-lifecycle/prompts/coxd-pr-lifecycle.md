# coxd PR lifecycle (portable prompt)

Run the full merge -> deploy -> verify -> close -> cleanup lifecycle for a ready-to-land PR,
especially one from an autonomous coding-agent worker whose PR body won't auto-link the issue.

Open and follow, step by step, the skill instructions at:

    ~/repo/skills/coxd-pr-lifecycle/skills/coxd-pr-lifecycle/SKILL.md

In short:

1. Confirm CI is green; get an explicit human go before merging (never auto-merge).
2. `gh pr merge <N> --squash --delete-branch`.
3. Diff the merge commit to pick the deploy target (migration present? web changed?), then
   deploy via the repo's own `deploy-to-nas.sh`.
4. Verify via the REAL traffic path (`homelab-deploy`'s `verify-deploy.sh`), never just a
   container-internal check — those can lie.
5. Close the issue if it didn't auto-link (`gh issue close <N> --comment ...`); clean up the
   worktree/branch and any external task-tracking store.

Report a short summary at the end, not a step-by-step narration.
