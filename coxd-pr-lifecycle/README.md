# coxd-pr-lifecycle

A cross-harness skill for the merge -> deploy -> verify -> close -> cleanup lifecycle of a
ready PR, written after that sequence was re-derived from scratch about eight times in one
session before being worth codifying.

## Why this exists

Three steps kept getting silently skipped or improvised badly:

1. **Closing the issue.** PRs opened by an autonomous coding-agent worker rarely write
   `Closes #N` in the body, so GitHub never auto-closes it — every one needs a manual
   `gh issue close`.
2. **Picking the right deploy target.** Not every merge needs the same deploy — some need a
   DB migration run, some touch the web frontend, some are API-only. Guessing wrong either
   ships stale code or wastes a rebuild.
3. **Verifying the deploy actually worked.** "The container is running" is not the same as
   "the app is reachable." A container-internal check can lie (e.g. a Next.js server bound
   to `HOSTNAME` instead of `0.0.0.0` makes `localhost` checks fail from inside the very same
   container that's serving traffic fine through the reverse proxy). The fix: always verify
   through the real traffic path, via `homelab-deploy`'s `verify-deploy.sh`.

## Relationship to other skills

- **homelab-deploy** owns the actual deploy mechanics (Traefik labels, `homelab.yml`,
  `verify-deploy.sh`, secrets placement). This skill calls into it rather than duplicating it.
- **ci-flake-triage** is the companion for step 1 (deciding whether a red CI check actually
  blocks the merge).
- **work-issue** covers implementing an issue yourself; this skill picks up *after* a PR
  (self-authored or worker-authored) is ready to land.

## Install

`/plugin marketplace add ~/repo/skills` then `/plugin install coxd-pr-lifecycle`, or just
point Claude at `skills/coxd-pr-lifecycle/SKILL.md` — it auto-triggers on "merge this PR",
"ship #N", "merge and deploy", "close out #N", or when CI goes green on a ready PR.

For Codex: symlink or copy `prompts/coxd-pr-lifecycle.md` into `~/.codex/prompts/`, invoke
with `/coxd-pr-lifecycle`. For Copilot CLI: point its custom-instructions mechanism at the
same `prompts/coxd-pr-lifecycle.md` (verify your current Copilot CLI setup — no established
convention for this in this repo yet).
