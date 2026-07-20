# Readiness rubric

Readiness answers one question: **is this repo ready for the job it's actually meant to do?** —
not "does it build," but "would you trust it in real use?" The engine scores 6 generic dimensions;
you refine the wording and add domain dimensions the engine can't see.

## Statuses (four, semantic)
| status | meaning | colour |
|---|---|---|
| `solid` | this dimension is fine | green |
| `measuring` | in progress / not yet known | teal |
| `gap` | a real shortfall, not blocking today | amber |
| `blocker` | would stop you shipping / trusting it | red |

## The 6 engine dimensions (auto-scored in `gather.py`)
1. **Tests + CI** — tests present? latest CI green? → solid / blocker (red if CI failing) / gap (no tests).
2. **Open criticals / bugs** — open issues labelled bug/critical/blocker/regression/security → solid / gap / blocker (≥3).
3. **Security posture** — open Dependabot alerts by severity → solid (0) / gap (low-med) / blocker (any critical/high) / measuring (no perms).
4. **Deploy & freshness** — deploy config present + branch ahead/dirty vs default → the "is what's live actually current" gap. solid / gap / measuring (no deploy config).
5. **Tech debt** — TODO/FIXME density + oversized files → solid / gap.
6. **Tech stack** — detected languages + key deps (informational; flag obvious staleness).

Refine each `finding` into a plain sentence a non-engineer gets. Add a `ref` — a linked issue
(`<a href="…">#N</a>`) or a concrete action (`redeploy backend`).

## Domain dimensions (you add these)
The engine can't know a project's *purpose*. Add dimensions that capture "ready for THIS" — but
only with **evidence from the repo** (a doc, a test result, an eval report, a config), never from
chat history alone (a portable skill can't see other sessions). Examples:
- an ML/extraction app → **accuracy** (is there a measured baseline? → `measuring` until there is),
  and **is the model actually used in prod** (or silently bypassed?).
- a data pipeline → **grounding / correctness** against real targets.
- an API → **contract/versioning**, rate-limit/abuse posture.

If `pulse.config.json.readiness_criteria` sets targets (e.g. accuracy ≥ 0.9), score against them.

## The verdict
One honest sentence + a `tone` (`solid` / `gap` / `blocker`). It must reconcile "what's merged"
with "what's actually true in production." The DocuPulse example: *everything shipped and CI-green,
but the LLM path was silently failing in prod and accuracy was unmeasured* → verdict tone `gap`,
"functionally built, not yet proven." That honesty is the whole point — don't let a green board
imply a working product.

## Score
`summary.readiness_score` = mean of the dimension scores (0–1). Show it as a %, but the **verdict +
blockers** carry the real signal — a number alone hides a single red blocker.
