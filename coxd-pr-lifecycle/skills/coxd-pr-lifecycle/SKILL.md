---
name: coxd-pr-lifecycle
description: Run the full merge -> deploy -> verify -> close -> cleanup lifecycle for a PR that's ready to land, especially one shipped by an autonomous coding-agent worker (coxd, or similar) whose PR body never auto-links the issue. Use when the user says "merge this PR", "ship #N", "merge and deploy", "close out #N", or when a PR reaches a ready-to-merge state after CI is green. Repo-agnostic across any NAS-deployed app (MoneyPulse, PlaylistMiner, DocuPulse/smartocrprocess, and others sharing the deploy-to-nas.sh pattern).
---

# coxd PR lifecycle

Landing a PR is not just `gh pr merge`. Five things have to happen, in order, and three of
them are easy to silently skip — this skill exists because all three got skipped at least
once in real use before it was written.

## Why this exists
Worker-authored PRs (coxd, or any autonomous agent) don't reliably write `Closes #N` in the
PR body, so GitHub never auto-closes the issue — every single one needs a manual close.
Deploy scope (api-only vs web vs migration vs all) isn't uniform across PRs; guessing wrong
either deploys too little (stale code live) or wastes a rebuild. And "the container is
running" is not the same as "the app is reachable" — a missing/misconfigured healthcheck or
a bind-address quirk can make a container-internal check lie while the real traffic path
(through the reverse proxy) works fine, or vice versa.

## The five steps

### 1. Confirm merge-ready, get explicit human go
Check `gh pr checks <N>`. All required checks green. If a check is red, first triage it —
see the companion skill **ci-flake-triage** before assuming it blocks merge.
**Never merge without an explicit go from the human** — this is the one standing gate, even
in an otherwise-autonomous pipeline. State what's green/red and wait for a clear yes.

### 2. Merge
```
gh pr merge <N> --squash --delete-branch
```
If branch deletion fails because a worktree still references it, that's fine — it means
step 5's cleanup hasn't run yet. Don't force it; clean the worktree first, then retry the
branch delete, or just let step 5 handle it.

### 3. Determine deploy scope, then deploy
Diff the merge commit against its parent to decide what changed:
```
git diff --stat HEAD~1 HEAD -- db/migrations   # any output -> migration present
git diff --stat HEAD~1 HEAD -- apps/web        # any output -> web changed (adjust path per repo)
```
Map to the repo's own `deploy-to-nas.sh` target (names vary by repo — read its own usage
banner, don't assume):
- Migration present -> the `db:migrate`-equivalent target (runs API build + migration).
- Web changed, no migration -> `web`, or `all` if both API and web changed and there's no
  combined migrate+web target.
- Neither -> `api` (or the repo's default/no-arg target) is enough.

Run it: `cd <repo> && ./deploy-to-nas.sh <target>`.

If the repo has no `deploy-to-nas.sh` of its own, or you need the underlying deploy
mechanics/conventions (Traefik labels, `homelab.yml`, secrets placement), invoke the
**homelab-deploy** skill instead of improvising.

### 4. Verify via the REAL traffic path — not just "is the container running"
**Always run `~/.claude/skills/homelab-deploy/scripts/verify-deploy.sh <container> <subdomain>`
after deploying.** This is not optional. It waits for the container to be genuinely healthy,
checks the actual HTTPS route through Traefik, and retries once if still unreachable.

Do not substitute a container-internal check (`docker exec <c> curl localhost:PORT`) for
this. A Next.js standalone server binding to `process.env.HOSTNAME` (which Docker sets to
the container ID, not `0.0.0.0`) will make `localhost`/`127.0.0.1` checks fail from *inside*
the same container while the app is completely reachable through the real Traefik path —
this happened in practice and cost real debugging time before the real fix (checking
`docker exec traefik wget ... http://<container>:<port>/` or, better, just running the
verify script) was found. A missing Docker `HEALTHCHECK` on the service will also make the
deploy script itself print a false "health check timed out" — that's a deploy-script
limitation, not a real failure; `verify-deploy.sh` doesn't have this blind spot.

If there's a DB migration, also spot-check the new column/table exists:
```
ssh nas "docker exec <db-container> psql -U <user> -d <db> -t -c \"SELECT column_name FROM information_schema.columns WHERE table_name='<table>' AND column_name LIKE '%<hint>%';\""
```

### 5. Close the issue, clean up
```
gh issue view <N> --json state,closed -q '{state: .state, closed: .closed}'
```
If not already closed (the common case for worker-authored PRs):
```
gh issue close <N> --comment "Closed via PR #<PR-number> (merged $(date -u +%Y-%m-%dT%H:%M:%SZ))."
```
Then clean the worktree and branch (adjust the worktree path to whatever convention the
driving system used):
```
git worktree remove --force <worktree-path>
git branch -D <branch-name>
```
If this task was tracked in an external store (e.g. coxd's sqlite `tasks` table), update its
terminal state too:
```
UPDATE tasks SET state='landed', reason='merged as PR #<N>' WHERE id='<task-id>';
```

## Report
One short summary: what merged, what deployed (target + what was verified), whether the
issue auto-closed or needed a manual close, and confirmation the worktree/branch/store are
clean. Don't narrate each step separately if nothing went wrong.
