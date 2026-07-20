# UPDATE mode

`docs/pulse.html` is a **living board** — re-run it each session/milestone and it refreshes in
place at the same path (and, for hosted targets, the same URL).

## Detect
UPDATE when `docs/.pulse.docmap.json` exists (written by `assemble.py`). It records the last
`generated_at`, `repo`, a `data_sha`, and the section keys present.

## Flow
1. **Re-gather** → fresh `status.json` (same as CREATE step 1).
2. **Load the previous docmap** and, if present, the previous `pulse.data.json` (keep one next to
   the docmap, e.g. `docs/.pulse.data.json`, so narrative survives).
3. **Preserve human/authored narrative.** Any field the config marks under `"keep"` (e.g.
   `"keep": {"verdict": true, "tagline": true}`) or any DATA field carrying `"keep": true` is
   copied forward verbatim — do not regenerate it. Everything measured is always refreshed.
4. **Re-compose** the DATA (measured refreshed, kept narrative preserved, the rest re-judged).
5. **Diff and report drift** before writing — this is the value of an update:
   - issues newly closed / opened, PRs merged since last run,
   - readiness dimensions that changed status (esp. anything that became a `blocker` or cleared),
   - CI flipped, new Dependabot alerts, branch drift vs default.
   Print a short "since <last date>" changelog to chat.
6. **Re-assemble**, re-date, re-verify, re-publish to the same target/URL.

## Keep it honest across runs
- Never let a stale narrative outlive the numbers. If `verdict` is `"keep": true` but the measured
  data now contradicts it (e.g. the blocker cleared), surface that in the drift report and ask
  whether to refresh the kept field.
- Bump nothing by hand — the engine re-measures every time.
