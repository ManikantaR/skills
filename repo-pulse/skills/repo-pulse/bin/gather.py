#!/usr/bin/env python3
"""repo-pulse gatherer — collect a repo's status into a single status.json.

Deterministic + dependency-free (Python 3 stdlib). Shells out to git and,
when available, gh. The LLM skill reads this JSON and adds qualitative
readiness judgement + narrative; this script provides the measured baseline so
every run is cheap and identical across harnesses.

Usage:
    gather.py [REPO_PATH] [-o OUT]        # default: cwd, ./status.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "core"))
import gather_lib as G  # noqa: E402

CRIT_LABELS = {"bug", "critical", "blocker", "regression", "security", "p0", "p1"}
TEST_HINTS = ("tests", "test", "__tests__", "spec")


def _has_tests(cwd):
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in G._SKIP_DIRS]
        depth = os.path.relpath(root, cwd).count(os.sep)
        if depth > 3:
            dirs[:] = []
            continue
        if os.path.basename(root).lower() in TEST_HINTS:
            return True
        for f in files:
            fl = f.lower()
            if fl.startswith("test_") or fl.endswith(("_test.py", ".test.ts", ".test.tsx",
                                                       ".spec.ts", ".spec.tsx", "_test.go")):
                return True
    return False


def _has_deploy(cwd):
    signals = ["docker-compose.yml", "docker-compose.yaml", "Dockerfile", "deploy.sh",
               "deploy-to-nas.sh", "Procfile", "fly.toml", "vercel.json", "netlify.toml"]
    found = [s for s in signals if os.path.exists(os.path.join(cwd, s))]
    wf = os.path.join(cwd, ".github", "workflows")
    if os.path.isdir(wf):
        for f in os.listdir(wf):
            if any(k in f.lower() for k in ("deploy", "release", "publish")):
                found.append(f".github/workflows/{f}")
    return found


def _dim(key, dim, status, score, finding, evidence=""):
    return {"key": key, "dim": dim, "status": status, "score": round(score, 2),
            "finding": finding, "evidence": evidence}


def readiness(cwd, model):
    dims = []
    open_issues = [i for i in model["issues"] if i["state"] == "open"]

    # 1. tests + CI
    has_tests = _has_tests(cwd)
    ci = model["ci"]
    if not has_tests:
        dims.append(_dim("tests_ci", "Tests + CI", "gap", 0.35,
                         "No test suite detected — nothing gates regressions."))
    elif ci.get("conclusion") == "success":
        dims.append(_dim("tests_ci", "Tests + CI", "solid", 0.95,
                         "Tests present and the latest CI run is green.", ci.get("workflow", "")))
    elif ci.get("conclusion") in ("failure", "cancelled", "timed_out"):
        dims.append(_dim("tests_ci", "Tests + CI", "blocker", 0.2,
                         f"Latest CI run is {ci.get('conclusion')}.", ci.get("workflow", "")))
    else:
        dims.append(_dim("tests_ci", "Tests + CI", "measuring", 0.6,
                         "Tests present; latest CI conclusion unknown."))

    # 2. open criticals / bugs
    crits = [i for i in open_issues if CRIT_LABELS & {l.lower() for l in i["labels"]}]
    if not open_issues:
        dims.append(_dim("criticals", "Open criticals / bugs", "solid", 0.9, "No open issues on file."))
    elif not crits:
        dims.append(_dim("criticals", "Open criticals / bugs", "solid", 0.85,
                         f"{len(open_issues)} open issues, none labelled critical/bug/blocker."))
    else:
        st = "blocker" if len(crits) >= 3 else "gap"
        dims.append(_dim("criticals", "Open criticals / bugs", st, max(0.2, 0.7 - 0.1 * len(crits)),
                         f"{len(crits)} open critical/blocker issue(s).",
                         ", ".join(f"#{i['n']}" for i in crits[:6])))

    # 3. security
    dep = model["security"]["dependabot"]
    if dep is None:
        dims.append(_dim("security", "Security posture", "measuring", 0.6,
                         "Dependabot alerts unavailable (no perms / not enabled)."))
    elif dep["total"] == 0:
        dims.append(_dim("security", "Security posture", "solid", 0.95, "No open Dependabot alerts."))
    elif dep["by_severity"]["critical"] or dep["by_severity"]["high"]:
        sev = dep["by_severity"]
        dims.append(_dim("security", "Security posture", "blocker", 0.3,
                         f"{sev['critical']} critical / {sev['high']} high alerts open.", json.dumps(sev)))
    else:
        dims.append(_dim("security", "Security posture", "gap", 0.6,
                         f"{dep['total']} lower-severity alerts open.", json.dumps(dep["by_severity"])))

    # 4. deploy & freshness
    deploy = model["deploy"]["signals"]
    g = model["git"]
    if not deploy:
        dims.append(_dim("deploy", "Deploy & freshness", "measuring", 0.55,
                         "No deploy config detected — can't assess live parity."))
    elif g["ahead"] > 0 or g["dirty"]:
        dims.append(_dim("deploy", "Deploy & freshness", "gap", 0.6,
                         f"Deployable, but {g['ahead']} commit(s) ahead of {g['default_branch']}"
                         + (" and uncommitted work present" if g["dirty"] else "") + "."))
    else:
        dims.append(_dim("deploy", "Deploy & freshness", "solid", 0.85,
                         "Deploy config present; branch in sync with default."))

    # 5. tech debt
    debt = model["tech_debt"]
    ratio = debt["markers"] / max(1, debt["files_scanned"])
    if ratio < 0.4 and debt["big_file_count"] <= 2:
        dims.append(_dim("techdebt", "Tech debt", "solid", 0.85,
                         f"{debt['markers']} TODO/FIXME across {debt['files_scanned']} files; few oversized files."))
    elif ratio < 1.2:
        dims.append(_dim("techdebt", "Tech debt", "gap", 0.6,
                         f"{debt['markers']} debt markers; {debt['big_file_count']} oversized file(s).",
                         ", ".join(f"{b['path']} ({b['lines']}L)" for b in debt["big_files"][:3])))
    else:
        dims.append(_dim("techdebt", "Tech debt", "gap", 0.45,
                         f"High debt density: {debt['markers']} markers across {debt['files_scanned']} files."))

    # 6. tech stack (informational)
    stack = model["tech_stack"]
    langs = ", ".join(stack["languages"]) or "undetected"
    dims.append(_dim("techstack", "Tech stack", "solid", 0.8,
                     f"{langs}." + (f" Key deps: {', '.join(stack['frameworks'][:5])}." if stack["frameworks"] else ""),
                     ", ".join(stack["manifests"])))
    return dims


def build(cwd):
    if not G.is_git_repo(cwd):
        sys.exit(f"error: {cwd} is not a git repository")
    gh = G.gh_ready(cwd)
    meta = G.repo_meta(cwd) if gh else {}
    model = {
        "schema": "repo-pulse/1",
        "generated_at": G.now_iso(),
        "repo": meta or {"name": os.path.basename(os.path.abspath(cwd))},
        "gh_available": gh,
        "git": G.git_state(cwd),
        "issues": G.issues(cwd) if gh else [],
        "pulls": G.pulls(cwd) if gh else {"merged": [], "open": []},
        "ci": G.ci_status(cwd),
        "security": {"dependabot": G.dependabot_alerts(cwd) if gh else None},
        "deploy": {"signals": _has_deploy(cwd)},
        "tech_stack": G.tech_stack(cwd),
        "tech_debt": G.tech_debt(cwd),
    }
    model["readiness"] = readiness(cwd, model)
    cfg, cfg_name = G.load_config(cwd)
    model["config"] = cfg
    model["config_source"] = cfg_name
    iss = model["issues"]
    model["summary"] = {
        "issues_total": len(iss),
        "issues_open": len([i for i in iss if i["state"] == "open"]),
        "prs_merged": len(model["pulls"]["merged"]),
        "prs_open": len(model["pulls"]["open"]),
        "readiness_score": round(sum(d["score"] for d in model["readiness"]) / len(model["readiness"]), 2),
        "blockers": [d["dim"] for d in model["readiness"] if d["status"] == "blocker"],
    }
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("-o", "--out", default="status.json")
    args = ap.parse_args()
    model = build(os.path.abspath(args.repo))
    with open(args.out, "w") as f:
        json.dump(model, f, indent=2)
    s = model["summary"]
    print(f"repo-pulse: {model['repo'].get('name')} · {s['issues_open']} open / {s['issues_total']} issues · "
          f"{s['prs_merged']} PRs merged · readiness {s['readiness_score']} · "
          f"blockers: {', '.join(s['blockers']) or 'none'}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
