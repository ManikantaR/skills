# Data sources, config & publishing

## What `bin/gather.py` measures (the deterministic baseline)
Shells out to `git` and (when authed + a remote exists) `gh`. Everything degrades to empty rather
than failing.

| Section | Source | Notes |
|---|---|---|
| `repo` | `gh repo view` | name, slug, **visibility**, url, description |
| `git` | `git` | branch, default branch, ahead/behind, dirty, last 8 commits, worktrees |
| `issues` | `gh issue list --state all` | number, title, state, labels, milestone |
| `pulls` | `gh pr list` | merged (for issue→PR mapping) + open |
| `ci` | `gh run list` | latest run conclusion; `has_ci` from `.github/workflows` |
| `security.dependabot` | `gh api …/dependabot/alerts` | severity counts; `null` if no perms/not enabled |
| `deploy.signals` | filesystem | docker-compose, Dockerfile, deploy scripts, deploy/release workflows |
| `tech_stack` | manifests (root + immediate subdirs) | languages + key framework versions — monorepo-aware |
| `tech_debt` | source scan | TODO/FIXME/HACK/XXX/BUG count, oversized files, files scanned |
| `readiness` | derived | 6 scored dimensions (see `readiness.md`) |
| `config` | `pulse.config.json` | user overlay (below) |

**No GitHub?** With no `gh`/remote, issues/PRs/security come back empty and the board falls back to
"repo + git + stack + debt + readiness(from local signals)". Still a useful page.

## `pulse.config.json` (optional, repo-local overlay)
JSON (stdlib-only — no YAML dep). Any field is optional; present values override inference.

```jsonc
{
  "display_name": "DocuPulse",              // pretty title (else repo name)
  "tagline": "Self-hosted document filer.",
  "pipeline": { "caption":"…", "sub":"…", "note":"…",
                "stages":[ {"b":"OCR","l":"Tesseract"}, {"b":"LLM","l":"qwen2.5:7b","kind":"key"} ] },
  "phases": [ {"id":"p0","tag":"P0","label":"Stabilize","issues":[1,2,3]} ],  // else infer from labels/docs
  "tracks": [ {"id":"v2","label":"v2 — autonomous","meta":"epic #57","label_match":"v2"} ],
  "readiness_criteria": { "accuracy": {"target":0.9,"metric":"date/vendor/amount"} },  // domain thresholds
  "publish": { "targets":["artifact","homelab"], "homelab_subdomain":"pulse" },
  "keep": { "verdict": true }               // fields to preserve verbatim on UPDATE
}
```

## Publishing — visibility-aware (§publish)
`docs/pulse.html` is **always** written + committable. Additional "view anywhere" targets are
chosen by **repo visibility** (from `gather.py`). `bin/publish.py <target>` handles each.

| Target | When to offer | Rule |
|---|---|---|
| **committed file** | always | just `docs/pulse.html` in the repo |
| **Claude Artifact** | Claude harness, any repo | private hosted link; the default "anywhere" for private repos |
| **GitHub Pages** | **public repos** (auto) | for a **private** repo: refuse unless `--publish-public` is passed, and warn that Pages exposes the content publicly |
| **homelab** | opt-in (config/flag) | scp/rsync to a NAS static path served at `<sub>.home.manikantar.com`; private to the network |

**Hard rule:** never publish a **private** repo's dashboard to public GitHub Pages by default —
it leaks issue titles/roadmap. Prefer Artifact or homelab. (This is a privacy control, not a nicety.)
