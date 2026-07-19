#!/usr/bin/env python3
"""assemble.py — stamp core partials + a DATA object into a single-file offline artifact.

Shared by repo-pulse and codebase-walkthrough. Reads a template with placeholders
({{CHASSIS_CSS}}, {{RENDER_JS}}, {{DATA}}, {{TITLE}}, {{FAVICON}}), inlines core/chassis.css
+ core/render.js, injects the JSON data, and writes a self-contained HTML file plus a
docmap sidecar (for CREATE/UPDATE + drift detection).

Usage:
    assemble.py --template T.html --data data.json --out docs/pulse.html \
                [--title "…"] [--favicon 🗂️]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os

CORE = os.path.dirname(os.path.abspath(__file__))


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _load_prev(out):
    """Previous composed DATA, kept next to the output as .pulse.data.json."""
    p = os.path.join(os.path.dirname(os.path.abspath(out)), ".pulse.data.json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _carry_kept(new, prev):
    """UPDATE mode: preserve human-authored narrative verbatim across runs.
    A field is kept if it's named in the new data's `keep` list, or its previous
    value is an object carrying `"keep": true`. Measured fields are never kept."""
    if not prev:
        return []
    keep_named = set(new.get("keep") or [])
    carried = []
    for k, v in prev.items():
        if k in ("summary", "git", "generated_at", "eyebrow", "readiness", "tiles"):
            continue  # always-measured — never preserve
        if k in keep_named or (isinstance(v, dict) and v.get("keep")):
            new[k] = v
            carried.append(k)
    return carried


def _drift(prev, new):
    """Human-readable 'what changed since last run' lines."""
    if not prev:
        return []
    lines = []
    ps, ns = prev.get("summary") or {}, new.get("summary") or {}
    for label, key in (("open issues", "issues_open"), ("PRs merged", "prs_merged"),
                       ("readiness", "readiness_score")):
        a, b = ps.get(key), ns.get(key)
        if a != b:
            lines.append(f"{label}: {a} → {b}")
    pb, nb = set(ps.get("blockers") or []), set(ns.get("blockers") or [])
    if pb - nb:
        lines.append("blockers cleared: " + ", ".join(sorted(pb - nb)))
    if nb - pb:
        lines.append("NEW blockers: " + ", ".join(sorted(nb - pb)))
    return lines


def assemble(template, data, out, title=None, favicon="🗂️", preserve=True):
    tpl = _read(template)
    chassis = _read(os.path.join(CORE, "chassis.css"))
    render = _read(os.path.join(CORE, "render.js"))

    prev = _load_prev(out) if preserve else None
    carried = _carry_kept(data, prev) if preserve else []
    drift = _drift(prev, data) if preserve else []

    data_json = json.dumps(data, ensure_ascii=False)
    title = title or data.get("repo", {}).get("name", "Status") + " — repo-pulse"

    html = (tpl
            .replace("{{CHASSIS_CSS}}", chassis)
            .replace("{{RENDER_JS}}", render)
            .replace("{{DATA}}", data_json)
            .replace("{{TITLE}}", title)
            .replace("{{FAVICON}}", favicon)
            .replace("{{GENERATED_AT}}", data.get("generated_at", "")))

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    # docmap sidecar for UPDATE mode + hub index cards
    repo = data.get("repo") or {}
    summary = data.get("summary") or {}
    docmap = {
        "generated_at": data.get("generated_at"),
        "repo": repo,
        "data_sha": hashlib.sha256(data_json.encode()).hexdigest()[:16],
        "sections": sorted(data.keys()),
        "card": {
            "title": data.get("display_name") or repo.get("name"),
            "tagline": data.get("tagline", ""),
            "url": data.get("repo_url") or repo.get("url"),
            "visibility": repo.get("visibility"),
            "readiness_score": summary.get("readiness_score"),
            "verdict": data.get("verdict") or {},
            "blockers": summary.get("blockers", []),
        },
    }
    outdir = os.path.dirname(os.path.abspath(out))
    side = os.path.join(outdir, ".pulse.docmap.json")
    with open(side, "w", encoding="utf-8") as f:
        json.dump(docmap, f, indent=2)
    # persist the composed DATA so the next run can preserve kept narrative + diff drift
    data_side = os.path.join(outdir, ".pulse.data.json")
    with open(data_side, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"out": out, "docmap": side, "data": data_side, "carried": carried, "drift": drift}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="docs/pulse.html")
    ap.add_argument("--title", default=None)
    ap.add_argument("--favicon", default="🗂️")
    ap.add_argument("--no-preserve", action="store_true",
                    help="ignore any prior .pulse.data.json (full rebuild, no keep/drift)")
    args = ap.parse_args()
    data = json.load(open(args.data, encoding="utf-8"))
    r = assemble(args.template, data, args.out, args.title, args.favicon,
                 preserve=not args.no_preserve)
    print(f"wrote {r['out']}\nwrote {r['docmap']}\nwrote {r['data']}")
    if r["carried"]:
        print("preserved (keep): " + ", ".join(r["carried"]))
    if r["drift"]:
        print("drift since last run:")
        for line in r["drift"]:
            print("  · " + line)


if __name__ == "__main__":
    main()
