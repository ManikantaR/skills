"""Shared, dependency-free helpers for gathering repo state.

Pure Python 3 stdlib. Shells out to `git` and (optionally) `gh`. Everything
degrades gracefully: no `gh`, no remote, or no network → the relevant sections
come back empty rather than raising. Used by repo-pulse's gather.py and by the
codebase-walkthrough gatherer.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# process / availability
# --------------------------------------------------------------------------- #
def run(args, cwd=".", timeout=30):
    """Run a command; return (returncode, stdout). Never raises on non-zero."""
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 1, ""


def have(binary):
    return shutil.which(binary) is not None


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# git
# --------------------------------------------------------------------------- #
def is_git_repo(cwd):
    rc, out = run(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    return rc == 0 and out == "true"


def git_state(cwd):
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)[1]
    default = _default_branch(cwd)
    ahead = behind = 0
    if default and default != branch:
        rc, out = run(["git", "rev-list", "--left-right", "--count",
                       f"{default}...HEAD"], cwd)
        if rc == 0 and "\t" in out:
            behind, ahead = (int(x) for x in out.split("\t")[:2])
    dirty = bool(run(["git", "status", "--porcelain"], cwd)[1])
    commits = []
    rc, out = run(["git", "log", "-8", "--pretty=%h\t%s\t%cr"], cwd)
    if rc == 0 and out:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                commits.append({"hash": parts[0], "subject": parts[1], "when": parts[2]})
    worktrees = []
    rc, out = run(["git", "worktree", "list", "--porcelain"], cwd)
    if rc == 0:
        cur = {}
        for line in out.splitlines():
            if line.startswith("worktree "):
                if cur:
                    worktrees.append(cur)
                cur = {"path": line[9:]}
            elif line.startswith("branch "):
                cur["branch"] = line[7:].replace("refs/heads/", "")
        if cur:
            worktrees.append(cur)
    return {
        "branch": branch, "default_branch": default,
        "ahead": ahead, "behind": behind, "dirty": dirty,
        "commits": commits,
        "worktree_count": len(worktrees), "worktrees": worktrees,
    }


def _default_branch(cwd):
    rc, out = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd)
    if rc == 0 and out:
        return out.rsplit("/", 1)[-1]
    for b in ("main", "master"):
        if run(["git", "rev-parse", "--verify", "--quiet", b], cwd)[0] == 0:
            return b
    return "main"


# --------------------------------------------------------------------------- #
# GitHub (via gh) — all optional
# --------------------------------------------------------------------------- #
def gh_ready(cwd):
    if not have("gh"):
        return False
    return run(["gh", "auth", "status"], cwd)[0] == 0 and \
        run(["gh", "repo", "view", "--json", "name"], cwd)[0] == 0


def gh_json(args, cwd):
    rc, out = run(["gh"] + args, cwd)
    if rc != 0 or not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def repo_meta(cwd):
    data = gh_json(["repo", "view", "--json",
                    "name,nameWithOwner,visibility,url,defaultBranchRef,description"], cwd)
    if not data:
        return {}
    return {
        "name": data.get("name"),
        "slug": data.get("nameWithOwner"),
        "visibility": (data.get("visibility") or "").upper(),
        "url": data.get("url"),
        "description": data.get("description"),
    }


def issues(cwd, limit=200):
    data = gh_json(["issue", "list", "--state", "all", "--limit", str(limit),
                    "--json", "number,title,state,labels,milestone"], cwd) or []
    out = []
    for i in data:
        out.append({
            "n": i["number"], "t": i["title"], "state": i["state"].lower(),
            "labels": [l["name"] for l in i.get("labels", [])],
            "milestone": (i.get("milestone") or {}).get("title"),
        })
    return out


def pulls(cwd, limit=100):
    merged = gh_json(["pr", "list", "--state", "merged", "--limit", str(limit),
                      "--json", "number,title,mergedAt"], cwd) or []
    openp = gh_json(["pr", "list", "--state", "open", "--limit", "50",
                     "--json", "number,title,isDraft"], cwd) or []
    return {
        "merged": [{"n": p["number"], "t": p["title"]} for p in merged],
        "open": [{"n": p["number"], "t": p["title"], "draft": p.get("isDraft", False)} for p in openp],
    }


def ci_status(cwd):
    """Latest workflow run conclusion on the default branch."""
    if not (".github" and os.path.isdir(os.path.join(cwd, ".github", "workflows"))):
        return {"has_ci": False}
    runs = gh_json(["run", "list", "--limit", "1",
                    "--json", "conclusion,status,workflowName,headBranch"], cwd)
    if not runs:
        return {"has_ci": True, "conclusion": None}
    r = runs[0]
    return {"has_ci": True, "conclusion": r.get("conclusion"),
            "status": r.get("status"), "workflow": r.get("workflowName")}


def dependabot_alerts(cwd):
    """Open Dependabot alert count by severity. Needs repo perms; degrades to None."""
    slug = repo_meta(cwd).get("slug")
    if not slug:
        return None
    data = gh_json(["api", f"/repos/{slug}/dependabot/alerts?state=open&per_page=100"], cwd)
    if data is None:
        return None
    sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in data:
        s = (a.get("security_advisory") or {}).get("severity", "").lower()
        if s in sev:
            sev[s] += 1
    return {"total": sum(sev.values()), "by_severity": sev}


# --------------------------------------------------------------------------- #
# tech stack detection
# --------------------------------------------------------------------------- #
_MANIFESTS = [
    ("requirements.txt", "Python"), ("pyproject.toml", "Python"), ("Pipfile", "Python"),
    ("package.json", "Node/JS"), ("go.mod", "Go"), ("Cargo.toml", "Rust"),
    ("Gemfile", "Ruby"), ("pom.xml", "Java"), ("build.gradle", "Java/Kotlin"),
    ("composer.json", "PHP"), ("Dockerfile", "Docker"), ("docker-compose.yml", "Docker"),
]


def _search_dirs(cwd):
    """Repo root + immediate child dirs (monorepos keep manifests in subdirs)."""
    dirs = [cwd]
    try:
        for d in sorted(os.listdir(cwd)):
            p = os.path.join(cwd, d)
            if os.path.isdir(p) and d not in _SKIP_DIRS and not d.startswith("."):
                dirs.append(p)
    except OSError:
        pass
    return dirs


def tech_stack(cwd):
    langs, frameworks, files = set(), set(), []
    for base in _search_dirs(cwd):
        rel = os.path.relpath(base, cwd)
        prefix = "" if rel == "." else rel + "/"
        for fname, lang in _MANIFESTS:
            if os.path.exists(os.path.join(base, fname)):
                langs.add(lang)
                files.append(prefix + fname)
        pj = os.path.join(base, "package.json")
        if os.path.exists(pj):
            try:
                data = json.load(open(pj))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for k in ("next", "react", "vue", "svelte", "express", "tailwindcss", "vite", "@angular/core"):
                    if k in deps:
                        frameworks.add(k.replace("@angular/core", "angular") + " " + str(deps[k]).lstrip("^~"))
            except Exception:
                pass
        req = os.path.join(base, "requirements.txt")
        if os.path.exists(req):
            try:
                for line in open(req):
                    m = re.match(r"^(fastapi|django|flask|sqlalchemy|pydantic|alembic|uvicorn|torch|transformers|ollama)\b.*?([\d.]+)?",
                                 line.strip(), re.I)
                    if m and m.group(1):
                        frameworks.add(m.group(1).lower() + (" " + m.group(2) if m.group(2) else ""))
            except Exception:
                pass
    return {"languages": sorted(langs), "frameworks": sorted(frameworks), "manifests": files}


# --------------------------------------------------------------------------- #
# tech debt scan
# --------------------------------------------------------------------------- #
_DEBT_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG)\b")
_SKIP_DIRS = {".git", ".worktrees", "node_modules", ".venv", "venv", "dist", "build",
              ".next", "__pycache__", ".pytest_cache", "vendor", "coverage"}
_CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".java",
             ".cs", ".php", ".c", ".cpp", ".sh", ".css", ".html", ".sql"}


def tech_debt(cwd, big_lines=600):
    markers, big_files, scanned = 0, [], 0
    for root, dirs, fnames in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for f in fnames:
            ext = os.path.splitext(f)[1]
            if ext not in _CODE_EXT:
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    lines = fh.readlines()
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            n = len(lines)
            hits = sum(1 for ln in lines if _DEBT_RE.search(ln))
            markers += hits
            if n >= big_lines:
                big_files.append({"path": os.path.relpath(path, cwd), "lines": n})
    big_files.sort(key=lambda x: -x["lines"])
    return {"markers": markers, "files_scanned": scanned,
            "big_files": big_files[:8], "big_file_count": len(big_files)}


# --------------------------------------------------------------------------- #
# config overlay (stdlib-only → JSON)
# --------------------------------------------------------------------------- #
def load_config(cwd):
    for name in ("pulse.config.json", ".pulse.json", "docs/pulse.config.json"):
        path = os.path.join(cwd, name)
        if os.path.exists(path):
            try:
                return json.load(open(path)), name
            except json.JSONDecodeError:
                pass
    return {}, None
