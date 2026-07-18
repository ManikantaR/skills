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


def assemble(template, data, out, title=None, favicon="🗂️"):
    tpl = _read(template)
    chassis = _read(os.path.join(CORE, "chassis.css"))
    render = _read(os.path.join(CORE, "render.js"))
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

    # docmap sidecar for UPDATE mode
    docmap = {
        "generated_at": data.get("generated_at"),
        "repo": data.get("repo"),
        "data_sha": hashlib.sha256(data_json.encode()).hexdigest()[:16],
        "sections": sorted(data.keys()),
    }
    side = os.path.join(os.path.dirname(os.path.abspath(out)), ".pulse.docmap.json")
    with open(side, "w", encoding="utf-8") as f:
        json.dump(docmap, f, indent=2)
    return out, side


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="docs/pulse.html")
    ap.add_argument("--title", default=None)
    ap.add_argument("--favicon", default="🗂️")
    args = ap.parse_args()
    data = json.load(open(args.data, encoding="utf-8"))
    out, side = assemble(args.template, data, args.out, args.title, args.favicon)
    print(f"wrote {out}\nwrote {side}")


if __name__ == "__main__":
    main()
