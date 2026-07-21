# nas-migration-rehearsal

A cross-harness skill for rehearsing infra changes risky enough to fail silently in
production — codified after a Postgres engine swap (`postgres:16-alpine` ->
`pgvector/pgvector:pg16`) was nearly done in place on the live data volume, based on
a migration comment that turned out to be wrong about image compatibility.

## Why this exists

The specific failure mode this prevents: two Postgres images can look interchangeable
(same major version, same extension support) while actually differing in base OS C
library (musl vs glibc). Text/varchar indexes are collation-ordered, and different C
libraries sort text differently — swapping the image on an existing data directory
would have corrupted index ordering *silently*, not with a crash. There's also a
quieter gotcha in the recovery path: dump/restore into a fresh volume avoids the
collation risk, but doesn't carry role passwords, so a cutover can complete "healthy"
while the app still can't authenticate.

## Relationship to other skills

- **homelab-deploy** owns routine deploy mechanics; this skill is for the smaller set
  of changes too risky to just deploy directly.
- **coxd-pr-lifecycle** is what decides whether a given PR needs this rehearsal before
  its normal merge->deploy->verify flow, or can skip straight to it.

## Install

`/plugin marketplace add ~/repo/skills` then `/plugin install nas-migration-rehearsal`,
or point Claude directly at `skills/nas-migration-rehearsal/SKILL.md` — it auto-triggers
on compose/engine/extension changes or migrations that "shouldn't" need a rehearsal but
touch anything structural.

For Codex: copy `prompts/nas-migration-rehearsal.md` into `~/.codex/prompts/`, invoke
with `/nas-migration-rehearsal`. For Copilot CLI: point its custom-instructions
mechanism at the same file.
