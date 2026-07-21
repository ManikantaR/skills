---
name: nas-migration-rehearsal
description: Rehearse a mid/complex infrastructure change (DB engine/extension swap, risky migration, multi-service integration) on an on-demand staging stack before it touches the real NAS deployment, then apply the same proven procedure to production. Use when a PR touches docker-compose*.yml, a database engine or extension, or a migration you don't want to gamble on directly against prod. Companion to homelab-deploy (which owns routine deploy mechanics) and coxd-pr-lifecycle (which decides when this applies).
---

# NAS migration rehearsal

Routine deploys are covered by **homelab-deploy**. This skill is for the other case:
a change risky enough that you want to prove it works — on a copy of real data,
without touching the real deployment — before doing it for real. It exists because
skipping this once, for a Postgres engine swap, would have silently corrupted text
index ordering; the migration doing the swap even claimed (wrongly) that it was safe
to do in place.

## When to use this, not a routine deploy
- Swapping a service's base image (e.g. a database engine/build variant change)
- A migration doing something structural (new extension, index type, large backfill)
- Any change where "if this is wrong, it's wrong silently, not with a crash"

Routine app-code PRs should NOT go through this — CI's ephemeral integration tests
are the right gate for those. Reserve this for the genuinely risky class.

## The procedure

### 1. Stand up on-demand staging (never persistent)
Use a Compose **override file** on top of the real, tracked base compose file — never
a hand-maintained parallel copy. Override only what must differ to coexist on the
same NAS: `container_name`, volume paths, and Traefik `Host()` rules (see
`reference/staging-override-template.yml`).

**Traefik label gotcha**: to neutralize an inherited prod router label, set it to an
explicit non-matching host (`Host(\`disabled-in-staging.invalid\`)`), not an empty
string. Compose merges `labels:`/`environment:` as key=value maps (later file wins
per key) — an empty Traefik rule's parse behavior isn't something to bet real prod
routing on.

Bring up only the data-layer services first (e.g. `postgres`, `redis`) — prove the
data survives before booting the app against it.

### 2. Choose your test data honestly
- **Ongoing regression testing** (every mid/complex change, ordinary case): synthetic
  Faker-generated fixtures. No PII/regulatory exposure, reproducible via a fixed seed,
  committable, safe even if staging is ever reachable.
- **A specific migration/engine-swap rehearsal** (this skill's primary case): a
  **bounded, one-time** copy of real prod data is justified — the whole point is
  proving the actual data survives, which synthetic data can't prove. Tear down and
  wipe it the moment verification is done; never leave it sitting.
- Either way: **never copy real secrets** (encryption keys, signing secrets) into
  staging just to make restored data "fully readable." If the rehearsal's actual
  question is data-integrity (row counts, checksums, extension/migration success),
  none of that requires decrypting anything — verify at the byte/count level instead.

### 3. Dump-and-restore into a FRESH volume — never an in-place image swap
Even if a migration's own comments claim two images are "based on the same thing" and
volume-compatible, verify that claim empirically rather than trust it (see the
corrected note in MoneyPulse's own `0021_semantic_search.sql` — the claim was wrong).
An in-place image swap on an existing data directory risks a real, non-obvious hazard:
different base images can use different C libraries (e.g. musl vs glibc), which sort
text differently — an index built under one collation and read under another
corrupts silently, not with an error.

Dump/restore into a **fresh, empty** volume sidesteps this entirely: `pg_restore`
rebuilds every index from scratch under the new image's real collation.

```
pg_dump -Fc -U <user> -d <db> > dump.dump          # from the currently-running source, no downtime
docker run -d --name <temp> -v <fresh-empty-path>:/var/lib/postgresql/data <new-image>
pg_restore -U <user> -d <db> --no-owner --no-privileges < dump.dump
```

### 4. The password-preservation gotcha (easy to miss, will break the cutover if you do)
`POSTGRES_PASSWORD` (or equivalent) only takes effect at a container's **first**
init on a truly empty volume. Once you've restored existing data into that volume,
the role's password is whatever was set at that first boot — NOT necessarily what
your compose file's env var says, and NOT the original source's password either
(`pg_dump`/`pg_restore` don't carry role/password definitions by default).

**Fix before cutover, not after**: explicitly reconcile the restored cluster's role
password to match what the app's connection string actually expects:
```sql
ALTER ROLE <user> WITH PASSWORD '<the-real-target-password>';
```
Read that target password server-side only (e.g. via an SSH-run script) — never let
it pass through your own visible output, even when the intent is legitimate.

### 5. Verify with cheap, decisive checks — not vibes
```sql
-- row counts per table, compare source vs restored
SELECT 'transactions', count(*) FROM transactions;  -- etc per table

-- content-level checksum (catches corruption row-counts alone would miss)
SELECT md5(string_agg(t.row_text, '' ORDER BY t.id))
FROM (SELECT id, (id, col_a, col_b, ...)::text AS row_text FROM some_table) t;
```
Run both against source and restored, compare. A mismatch here is the signal to stop
and investigate — not something to hand-wave past.

### 6. Cut over carefully — old data stays untouched, always
1. Confirm the new cluster is healthy, migrated, and verified (steps 3-5).
2. Only then touch the real deployment: update the tracked (git!) compose file's
   image/volume, `docker compose up -d --force-recreate <service>`.
3. **This is the one moment a same-named container is genuinely replaced** — Docker
   can't run two containers under an identical name/hostname simultaneously, so if the
   app connects by a fixed service name, some replacement is structurally unavoidable.
   Say this plainly before doing it, not after — don't let "keep the old one running"
   instructions get silently reinterpreted as "stop it whenever convenient."
4. Restart dependent services (the API) so they reconnect; verify health end-to-end,
   including a real functional check (a query that touches real data), not just "the
   healthcheck passed."
5. **Keep the old volume completely untouched** for a real rollback window — days, not
   minutes. Rollback is "point the compose file back," not "restore from backup,"
   because nothing destructive happened to it.
6. Clean up temp verification containers/dumps immediately once the real cutover is
   confirmed working — a stray copy of real data sitting in `/tmp` indefinitely is
   exactly the kind of exposure this whole rehearsal was designed to avoid elsewhere.

### 7. Close the loop: get the touched config into git
If the cutover required editing a file that lives outside your synced repo (a
hand-maintained NAS-only compose file, for example), that edit needs to land in git
too — otherwise the exact "silent drift" problem this skill exists to prevent just
recurs at the config layer instead of the data layer. See `homelab-deploy`'s
single-source-of-truth principle; this skill's output isn't done until the config
change is reviewable and revertable via git, not just applied over SSH.

## Report
State clearly: what was rehearsed, what was verified (name the specific checks), what
changed in git, and the rollback path that remains available and for how long.
