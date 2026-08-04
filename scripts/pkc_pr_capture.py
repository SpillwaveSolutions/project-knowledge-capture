#!/usr/bin/env python3
"""Capture a GitHub PR as an OKF CodeChange concept.

Uses `gh pr view --json` when available; can also accept a JSON file fixture.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    append_log,
    ensure_bundle,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    scrub_text,
    slugify,
    utc_now,
    write_concept,
)


def fetch_pr(number: str, *, repo: str | None = None) -> dict[str, Any]:
    cmd = [
        "gh",
        "pr",
        "view",
        str(number),
        "--json",
        "number,title,body,baseRefName,headRefName,mergedAt,url,author,files,labels,state",
    ]
    if repo:
        cmd += ["--repo", repo]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "gh pr view failed")
    return json.loads(proc.stdout)


def materialize_pr(
    bundle: Path,
    pr: dict[str, Any],
    *,
    implements: list[str] | None = None,
) -> tuple[str, str]:
    number = pr.get("number") or pr.get("pr_number")
    title = pr.get("title") or f"PR #{number}"
    body = pr.get("body") or ""
    body, _ = scrub_text(body)
    branch = pr.get("headRefName") or pr.get("branch") or ""
    merged = pr.get("mergedAt") or pr.get("merged_at")
    state = (pr.get("state") or "OPEN").lower()
    status = "merged" if merged or state == "merged" else state
    slug = slugify(f"pr-{number}-{title}")
    rel = path_for_type("CodeChange", slug)

    links = []
    for t in implements or []:
        target = t if t.startswith("/") else f"/features/{slugify(t)}.md"
        links.append({"target": target, "rel": "implements"})

    fm: dict[str, Any] = {
        "type": "CodeChange",
        "title": f"PR #{number} {title}" if number else title,
        "description": (body.splitlines()[0] if body.strip() else title)[:200],
        "pr_number": number,
        "branch": branch,
        "merged_at": merged,
        "tags": ["code", "pr"],
        "timestamp": merged or utc_now(),
        "status": status,
        "verified": True,
        "generated": True,
        "stable_timestamp": True,
        "external_id": str(number) if number else None,
        "external_system": "github",
        "wiki_key": f"code-pr-{number}",
        "truth_state": "current",
    }
    if pr.get("url"):
        fm["url"] = pr["url"]
    if links:
        fm["links"] = links
    # drop Nones
    fm = {k: v for k, v in fm.items() if v is not None}

    files = pr.get("files") or []
    file_list = []
    for f in files:
        if isinstance(f, dict):
            file_list.append(f.get("path") or f.get("filename") or str(f))
        else:
            file_list.append(str(f))

    content = f"# PR #{number}: {title}\n\n"
    if pr.get("url"):
        content += f"- URL: {pr['url']}\n"
    content += f"- Branch: `{branch}`\n"
    content += f"- Status: `{status}`\n"
    if merged:
        content += f"- Merged: {merged}\n"
    content += "\n## Summary\n\n" + (body.strip() or "_No description._") + "\n"
    if file_list:
        content += "\n## Files\n\n"
        for fp in file_list[:50]:
            content += f"- `{fp}`\n"
    if links:
        content += "\n## Implements\n\n"
        for link in links:
            content += f"- [{link['target']}]({link['target']})\n"

    path, action = write_concept(bundle, rel, fm, content)
    refresh_catalog_index(bundle, "code")
    append_log(bundle, f"Captured CodeChange from PR #{number}: {title}")
    return rel, action


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture GitHub PR → CodeChange")
    parser.add_argument("pr", nargs="?", help="PR number")
    parser.add_argument("--json-file", default=None, help="Fixture JSON instead of gh")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--gh-repo", default=None, help="owner/name for gh --repo")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--implements", action="append", default=[])
    args = parser.parse_args(argv)

    if args.json_file:
        pr = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    elif args.pr:
        try:
            pr = fetch_pr(args.pr, repo=args.gh_repo)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            print("hint: pass --json-file fixture if gh is unavailable", file=sys.stderr)
            return 1
    else:
        print("error: provide PR number or --json-file", file=sys.stderr)
        return 1

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    ensure_bundle(bundle)
    rel, action = materialize_pr(bundle, pr, implements=args.implements)
    print(f"[{action}] {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
