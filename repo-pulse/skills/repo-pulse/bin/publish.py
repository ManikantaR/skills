#!/usr/bin/env python3
"""repo-pulse publisher — visibility-aware "view anywhere" for docs/pulse.html.

Targets:
  pages   GitHub Pages. PUBLIC repos only unless --public is passed (private Pages
          exposes the content publicly — refused by default as a privacy control).
  hub     Homelab self-host + aggregator. scp pulse.html to the NAS hub dir and
          (re)generate an index.html listing every repo's dashboard from a manifest.
          Works for a single repo or many; private to your network.

(The Claude "Artifact" target is not handled here — a script can't publish an
Artifact; the skill calls the Artifact tool directly. "Committed file" is just git.)

Usage:
  publish.py pages [--repo-dir .] [--public]
  publish.py hub   [--repo-dir .] [--nas HOST] [--hub-dir PATH] [--domain HOST]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # for _corepath
from _corepath import resolve_core  # noqa: E402

CORE = resolve_core()
sys.path.insert(0, CORE)
import gather_lib as G  # noqa: E402


def _cfg(repo_dir):
    cfg, _ = G.load_config(repo_dir)
    return cfg.get("publish", {}) if isinstance(cfg, dict) else {}


def _docmap(docs):
    p = os.path.join(docs, ".pulse.docmap.json")
    if not os.path.exists(p):
        sys.exit(f"error: {p} not found — run the skill (assemble) first")
    return json.load(open(p))


# --------------------------------------------------------------------------- #
# GitHub Pages (public-only by default)
# --------------------------------------------------------------------------- #
def publish_pages(repo_dir, docs, allow_public):
    if not G.gh_ready(repo_dir):
        sys.exit("error: gh not available/authed — Pages needs a GitHub remote")
    meta = G.repo_meta(repo_dir)
    slug, vis = meta.get("slug"), meta.get("visibility")
    if vis == "PRIVATE" and not allow_public:
        sys.exit("REFUSED: this repo is PRIVATE. GitHub Pages would expose the dashboard "
                 "publicly. Use `hub` (homelab, private) or the Claude Artifact instead, "
                 "or pass --public to override intentionally.")
    branch = G.git_state(repo_dir)["default_branch"]
    payload = json.dumps({"source": {"branch": branch, "path": "/docs"}})
    p = subprocess.run(["gh", "api", "-X", "POST", f"/repos/{slug}/pages", "--input", "-"],
                       cwd=repo_dir, input=payload, capture_output=True, text=True)
    if p.returncode != 0 and "409" not in p.stderr and "already" not in p.stderr.lower():
        # try update (PUT) if it already exists
        subprocess.run(["gh", "api", "-X", "PUT", f"/repos/{slug}/pages", "--input", "-"],
                       cwd=repo_dir, input=payload, capture_output=True, text=True)
    owner, name = slug.split("/")
    url = f"https://{owner.lower()}.github.io/{name}/pulse.html"
    print(f"✓ Pages source set to {branch}:/docs · commit+push docs/ and it serves at:\n  {url}")
    print("  (first build can take ~1 min)")


# --------------------------------------------------------------------------- #
# Homelab hub
# --------------------------------------------------------------------------- #
def _slug_for(meta, repo_dir):
    s = (meta.get("slug") or os.path.basename(os.path.abspath(repo_dir)))
    return s.replace("/", "-")


def publish_hub(repo_dir, docs, nas, hub_dir, domain):
    meta = G.repo_meta(repo_dir) if G.gh_ready(repo_dir) else {}
    card = _docmap(docs).get("card", {})
    slug = _slug_for(meta, repo_dir)
    html = os.path.join(docs, "pulse.html")
    if not os.path.exists(html):
        sys.exit(f"error: {html} not found")

    # 1. push this repo's dashboard
    G.run(["ssh", nas, f"mkdir -p {hub_dir}/{slug}"])
    for f in (html, os.path.join(docs, ".pulse.docmap.json")):
        if os.path.exists(f):
            r = subprocess.run(["scp", "-O", f, f"{nas}:{hub_dir}/{slug}/"], capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"scp failed: {r.stderr.strip()}")

    # 2. read + update the manifest
    rc, out = G.run(["ssh", nas, f"cat {hub_dir}/manifest.json 2>/dev/null"])
    manifest = {}
    if rc == 0 and out:
        try:
            manifest = json.loads(out)
        except json.JSONDecodeError:
            manifest = {}
    manifest[slug] = {
        "slug": slug,
        "title": card.get("title") or slug,
        "tagline": card.get("tagline", ""),
        "url": card.get("url"),
        "visibility": card.get("visibility"),
        "readiness_score": card.get("readiness_score"),
        "verdict": card.get("verdict", {}),
        "blockers": card.get("blockers", []),
        "generated_at": _docmap(docs).get("generated_at"),
        "path": f"{slug}/pulse.html",
    }

    # 3. render + push index.html + manifest.json
    index = _render_hub_index(manifest, domain)
    with tempfile.TemporaryDirectory() as td:
        ip, mp = os.path.join(td, "index.html"), os.path.join(td, "manifest.json")
        open(ip, "w").write(index)
        json.dump(manifest, open(mp, "w"), indent=2)
        for f in (ip, mp):
            r = subprocess.run(["scp", "-O", f, f"{nas}:{hub_dir}/"], capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"scp failed: {r.stderr.strip()}")
    print(f"✓ Pushed {slug} to the hub ({len(manifest)} repo(s)).")
    print(f"  Hub:  https://{domain}/")
    print(f"  This: https://{domain}/{slug}/pulse.html")


def _render_hub_index(manifest, domain):
    chassis = open(os.path.join(CORE, "chassis.css")).read()
    cards = sorted(manifest.values(), key=lambda r: -(r.get("readiness_score") or 0))
    rows = []
    for r in cards:
        sc = r.get("readiness_score")
        pct = f"{round(sc*100)}%" if sc is not None else "—"
        tone = (r.get("verdict") or {}).get("tone", "gap")
        vt = {"solid": "s-done", "gap": "s-part", "blocker": "s-open"}.get(tone, "s-part")
        bl = r.get("blockers") or []
        blk = f'<span class="stat-pill s-open">{len(bl)} blocker(s)</span>' if bl else ""
        rows.append(
            f'<a class="hcard" href="{r.get("path","#")}">'
            f'<div class="ht"><span class="hn">{_esc(r.get("title",""))}</span>'
            f'<span class="stat-pill {vt}">{_esc(tone)}</span></div>'
            f'<div class="hd">{_esc(r.get("tagline",""))}</div>'
            f'<div class="hf"><span class="hs num">{pct}</span>{blk}'
            f'<span class="hv">{_esc(r.get("visibility","") or "")}</span></div></a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>repo-pulse · hub</title>
<style>{chassis}
.wrap{{max-width:900px;margin:0 auto;padding:clamp(24px,5vw,56px) 24px;background:var(--paper);color:var(--ink);font-family:var(--sans)}}
h1{{font-size:clamp(26px,4vw,38px);font-weight:680;letter-spacing:-.02em}} h1 b{{color:var(--accent)}}
.sub{{color:var(--ink-2);margin:.5em 0 28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.hcard{{border:1px solid var(--line);background:var(--surface);border-radius:var(--r);padding:16px 17px;text-decoration:none;color:inherit;box-shadow:var(--shadow);transition:transform .12s,border-color .14s;display:flex;flex-direction:column;gap:9px}}
.hcard:hover{{transform:translateY(-2px);border-color:color-mix(in srgb,var(--accent) 40%,var(--line))}}
.ht{{display:flex;justify-content:space-between;align-items:center;gap:10px}} .hn{{font-weight:640;font-size:15px}}
.hd{{color:var(--ink-2);font-size:12.5px;line-height:1.4;flex:1}}
.hf{{display:flex;align-items:center;gap:10px;margin-top:2px}} .hs{{font-size:20px;font-weight:600}}
.hv{{margin-left:auto;font-family:var(--mono);font-size:10px;color:var(--ink-3);text-transform:lowercase}}</style></head>
<body><div class="wrap"><h1>repo·<b>pulse</b></h1>
<div class="sub">Private status hub · {len(cards)} repositories · {domain}</div>
<div class="grid">{''.join(rows)}</div></div></body></html>"""


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", choices=["pages", "hub"])
    ap.add_argument("--repo-dir", default=".")
    ap.add_argument("--docs", default=None)
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--nas", default=None)
    ap.add_argument("--hub-dir", default=None)
    ap.add_argument("--domain", default=None)
    args = ap.parse_args()
    repo_dir = os.path.abspath(args.repo_dir)
    docs = args.docs or os.path.join(repo_dir, "docs")
    cfg = _cfg(repo_dir)

    if args.target == "pages":
        publish_pages(repo_dir, docs, args.public)
    else:
        publish_hub(repo_dir, docs,
                    args.nas or cfg.get("nas_host") or os.environ.get("PULSE_NAS_HOST", "nas"),
                    args.hub_dir or cfg.get("hub_dir") or os.environ.get("PULSE_HUB_DIR", "/volume1/docker/pulse-hub"),
                    args.domain or cfg.get("hub_domain") or os.environ.get("PULSE_HUB_DOMAIN", "pulse.home.manikantar.com"))


if __name__ == "__main__":
    main()
