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
# shared skip set (build output / vcs / vendor dirs) — used by stack + debt scans
# --------------------------------------------------------------------------- #
_SKIP_DIRS = {".git", ".worktrees", "node_modules", ".venv", "venv", "dist", "build",
              ".next", "__pycache__", ".pytest_cache", "vendor", "coverage"}


# --------------------------------------------------------------------------- #
# tech stack detection
# --------------------------------------------------------------------------- #
# Exact-name manifests -> language. Extension- and pattern-based detection
# (.NET project/solution files, compose files) is handled separately below so
# a monorepo whose manifests live under src/*/ or tests/*/ is still detected.
_MANIFEST_MAP = {
    "requirements.txt": "Python", "pyproject.toml": "Python", "Pipfile": "Python",
    "setup.py": "Python", "package.json": "Node/JS", "go.mod": "Go",
    "Cargo.toml": "Rust", "Gemfile": "Ruby", "pom.xml": "Java",
    "build.gradle": "Java/Kotlin", "composer.json": "PHP", "Dockerfile": "Docker",
    "global.json": ".NET", "Directory.Build.props": ".NET",
}
_DOTNET_EXTS = {".csproj", ".fsproj", ".vbproj", ".sln", ".slnx"}
_COMPOSE_RE = re.compile(r"^(docker|podman)-compose.*\.ya?ml$", re.I)
# Build output / vendor dirs that carry no first-party manifests or source.
_MANIFEST_SKIP = _SKIP_DIRS | {"obj", "bin", "TestResults", "publish"}


def _walk_manifests(cwd, max_depth=3):
    """Yield (dir, filenames) up to max_depth deep, pruning build/vendor dirs.
    One level was too shallow — .NET/monorepo layouts keep manifests under
    src/<proj>/ and tests/<proj>/ (depth 2)."""
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in _MANIFEST_SKIP and not d.startswith(".")]
        rel = os.path.relpath(root, cwd)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth >= max_depth:
            dirs[:] = []
        yield root, files


def _scan_dotnet(path, frameworks):
    """Pull Aspire / ASP.NET / target-framework hints out of a .csproj."""
    try:
        txt = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return
    if path.endswith(".AppHost.csproj") or re.search(r"Aspire\.Hosting", txt):
        frameworks.add("Aspire")
    if re.search(r'Sdk="Microsoft\.NET\.Sdk\.Web"', txt) or re.search(r"Microsoft\.AspNetCore", txt):
        frameworks.add("ASP.NET Core")
    if re.search(r"EntityFrameworkCore", txt):
        frameworks.add("EF Core")
    m = re.search(r"<TargetFrameworks?>\s*(net[\d.]+)", txt)
    if m:
        frameworks.add(".NET " + m.group(1)[3:])


def tech_stack(cwd):
    langs, frameworks, files = set(), set(), []
    seen = set()
    for root, fnames in _walk_manifests(cwd):
        rel = os.path.relpath(root, cwd)
        prefix = "" if rel == "." else rel + "/"
        for f in fnames:
            ext = os.path.splitext(f)[1].lower()
            hit = None
            if f in _MANIFEST_MAP:
                hit = _MANIFEST_MAP[f]
            elif ext in _DOTNET_EXTS:
                hit = ".NET"
            elif _COMPOSE_RE.match(f):
                hit = "Docker"
            if hit:
                langs.add(hit)
                if len(files) < 40:
                    files.append(prefix + f)
            path = os.path.join(root, f)
            if f == "package.json" and path not in seen:
                seen.add(path)
                try:
                    data = json.load(open(path))
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for k in ("next", "react", "vue", "svelte", "express", "tailwindcss", "vite", "@angular/core"):
                        if k in deps:
                            frameworks.add(k.replace("@angular/core", "angular") + " " + str(deps[k]).lstrip("^~"))
                except Exception:
                    pass
            elif f == "requirements.txt" and path not in seen:
                seen.add(path)
                try:
                    for line in open(path):
                        m = re.match(r"^(fastapi|django|flask|sqlalchemy|pydantic|alembic|uvicorn|torch|transformers|ollama)\b.*?([\d.]+)?",
                                     line.strip(), re.I)
                        if m and m.group(1):
                            frameworks.add(m.group(1).lower() + (" " + m.group(2) if m.group(2) else ""))
                except Exception:
                    pass
            elif ext == ".csproj":
                _scan_dotnet(path, frameworks)
    return {"languages": sorted(langs), "frameworks": sorted(frameworks), "manifests": files}


# --------------------------------------------------------------------------- #
# tech debt scan
# --------------------------------------------------------------------------- #
_DEBT_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG)\b")
# Build output + generated-code locations that shouldn't count as source or debt.
_DEBT_SKIP_DIRS = _SKIP_DIRS | {"obj", "bin", "Migrations", "migrations"}
_CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".java",
             ".cs", ".php", ".c", ".cpp", ".sh", ".css", ".html", ".sql"}
# Generated files: real bytes, but not human-authored — don't blame them for debt.
_GENERATED_RE = re.compile(r"\.(Designer\.cs|g\.cs|generated\.cs|g\.ts|min\.js|min\.css)$", re.I)


def _is_generated(name):
    return bool(_GENERATED_RE.search(name)) or name.endswith(".d.ts")


def tech_debt(cwd, big_lines=600):
    markers, big_files, scanned, total_lines = 0, [], 0, 0
    for root, dirs, fnames in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in _DEBT_SKIP_DIRS]
        for f in fnames:
            ext = os.path.splitext(f)[1]
            if ext not in _CODE_EXT or _is_generated(f):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    lines = fh.readlines()
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            n = len(lines)
            total_lines += n
            hits = sum(1 for ln in lines if _DEBT_RE.search(ln))
            markers += hits
            if n >= big_lines:
                big_files.append({"path": os.path.relpath(path, cwd), "lines": n})
    big_files.sort(key=lambda x: -x["lines"])
    return {"markers": markers, "files_scanned": scanned, "total_lines": total_lines,
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
