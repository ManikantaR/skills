# nas-migration-rehearsal

Portable pointer for non-Claude harnesses (Codex, Copilot, etc.). Read the full
procedure at `skills/nas-migration-rehearsal/SKILL.md` in this plugin before doing
any of the following.

Use this whenever a change is risky enough to fail silently in production — a
database engine/base-image swap, a structural migration, a multi-service
integration — and you want to prove it works on a copy of real data, on an
on-demand staging stack, before touching the live NAS deployment.

Core sequence: Compose override on the real base file (never a parallel copy) →
honest test-data choice (Faker for routine cases, bounded one-time real-data copy
only to prove real-data survival, never real secrets) → dump/restore into a FRESH
volume for any engine/base-image change (never an in-place swap — different C
libraries collate text differently, corrupting indexes silently) → reconcile role
passwords post-restore before cutover → verify via row counts + content checksums →
cut over deliberately (state plainly when a same-named container will be replaced,
keep the old volume untouched for a real rollback window, clean up temp copies of
real data immediately) → get any out-of-repo config change into git.

See SKILL.md for full detail, exact commands, and the concrete gotchas this
procedure was built from.
