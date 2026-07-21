---
description: Rehearse a risky infra change (DB engine swap, structural migration) on on-demand staging before touching the real NAS deployment.
---

Follow the `nas-migration-rehearsal` skill (see `skills/nas-migration-rehearsal/SKILL.md` in this plugin) end to end:

1. Confirm this change actually warrants a rehearsal (base-image/engine swap, structural migration, or anything that could fail silently) rather than routine CI coverage.
2. Stand up an on-demand staging stack via a Compose override on the real base file — never a hand-maintained parallel copy.
3. Pick test data honestly: synthetic Faker fixtures for routine regression, a bounded one-time copy of real data only when proving real-data survival is the actual point — and never real secrets.
4. Dump-and-restore into a fresh volume for any base-image/engine change; never swap the image in place on existing data.
5. Reconcile role passwords after restore (`ALTER ROLE ... WITH PASSWORD`) before cutover.
6. Verify with row counts + content checksums, not vibes.
7. Cut over deliberately, say plainly when a same-named container will be replaced, keep the old volume untouched for a real rollback window, and clean up temp copies of real data immediately after.
8. Make sure any config touched outside the synced repo (e.g. a hand-edited NAS compose file) ends up tracked in git.

Report what was rehearsed, what was verified, what changed in git, and how long the rollback window stays open.
