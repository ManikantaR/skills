#!/usr/bin/env python3
"""codebase-walkthrough gatherer — deterministic facts for the walkthrough DATA.

Shares the same engine as repo-pulse (core/gather_lib.py). It emits ONLY the
*measured* subset the author should never hand-count — repo name/description,
stack, line/file totals, git state, and a roadmap skeleton from milestones. The
qualitative parts of the walkthrough (components, guardrails, the traced flows,
the code walk, the dev guide) are judgement — you still author those by reading
the code. "Engine owns the numbers, you own the narrative."

Usage:
    gather.py [REPO_PATH] [-o OUT]        # default: cwd, ./walkthrough.facts.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "core"))
import gather_lib as G  # noqa: E402

TEST_HINTS = ("tests", "test", "__tests__", "spec")


def _human(n):
    """1234 -> '1.2k', 980 -> '980', 2_000_000 -> '2.0M'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _test_files(cwd):
    count = 0
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in G._SKIP_DIRS]
        if os.path.relpath(root, cwd).count(os.sep) > 4:
            dirs[:] = []
            continue
        in_test_dir = os.path.basename(root).lower() in TEST_HINTS
        for f in files:
            fl = f.lower()
            if in_test_dir or fl.startswith("test_") or fl.endswith(
                    ("_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", "_test.go")):
                count += 1
    return count


def _roadmap_skeleton(cwd, gh):
    """Group issues by milestone into the shape DATA.roadmap expects — a skeleton
    the author refines (titles/copy/pill wording). Empty when there's no gh/remote."""
    if not gh:
        return []
    issues = G.issues(cwd)
    by_ms = {}
    for i in issues:
        ms = i.get("milestone") or "Unscheduled"
        by_ms.setdefault(ms, []).append(i)
    road = []
    for idx, (ms, items) in enumerate(by_ms.items()):
        done = [i for i in items if i["state"] == "closed"]
        cls = "done" if len(done) == len(items) else ("now" if done else "wait")
        road.append({
            "id": f"m{idx}", "title": ms, "cls": cls,
            "prog": [len(done), len(items)],
            "tasks": [[f"#{i['n']}", "done" if i["state"] == "closed" else "wait"] for i in items[:12]],
            "_hint": "refine title/body/pill; tasks are issue numbers, rename to labels",
        })
    return road


def build(cwd):
    if not G.is_git_repo(cwd):
        sys.exit(f"error: {cwd} is not a git repository")
    gh = G.gh_ready(cwd)
    meta = G.repo_meta(cwd) if gh else {}
    debt = G.tech_debt(cwd)
    stack = G.tech_stack(cwd)
    name = (meta.get("name") if meta else None) or os.path.basename(os.path.abspath(cwd))

    # Measured stats -> DATA.meta.stats rows. Author adds curated rows
    # (components, guardrails) whose counts only they can know.
    stats = [
        [_human(debt["total_lines"]), "lines of code"],
        [str(debt["files_scanned"]), "source files"],
    ]
    tests = _test_files(cwd)
    if tests:
        stats.append([str(tests), "test files"])
    if stack["languages"]:
        stats.append([str(len(stack["languages"])), "languages"])

    return {
        "schema": "walkthrough-facts/1",
        "generated_at": G.now_iso(),
        "meta": {
            "name": name,
            "tagline": (meta.get("description") if meta else "") or "",
            "date": G.now_iso()[:10],
        },
        "measured_stats": stats,
        "tech_stack": stack,
        "git": G.git_state(cwd),
        "tech_debt": debt,
        "roadmap_skeleton": _roadmap_skeleton(cwd, gh),
        "_note": "Fold measured_stats/tech_stack/roadmap_skeleton into DATA. Author the "
                 "flows, code walk, guardrails and dev guide by reading the code — never guess.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("-o", "--out", default="walkthrough.facts.json")
    args = ap.parse_args()
    facts = build(os.path.abspath(args.repo))
    with open(args.out, "w") as f:
        json.dump(facts, f, indent=2)
    m, d = facts["meta"], facts["tech_debt"]
    print(f"walkthrough facts: {m['name']} · {d['total_lines']} LOC / {d['files_scanned']} files · "
          f"{', '.join(facts['tech_stack']['languages']) or 'stack undetected'} · "
          f"{len(facts['roadmap_skeleton'])} milestone(s)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
