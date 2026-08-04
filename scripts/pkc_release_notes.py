#!/usr/bin/env python3
"""Generate release notes from Release / CodeChange / Feature edges.

Walks `released_in`, `lands_in`, and `implements` links around a Release concept
or free-form version tag.

Usage:
  python3 scripts/pkc_release_notes.py --bundle sample-knowledge
  python3 scripts/pkc_release_notes.py releases/v0-1-0.md --bundle sample-knowledge
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import iter_concepts, parse_frontmatter, resolve_knowledge_root, utc_now  # noqa: E402

MD_LINK = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")


def load_nodes(bundle: Path) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for path in iter_concepts(bundle):
        rel = "/" + path.relative_to(bundle).as_posix()
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        edges: list[tuple[str, str]] = []
        for link in fm.get("links") or []:
            if isinstance(link, dict) and link.get("target"):
                edges.append((link.get("rel") or "related_to", link["target"]))
        for m in MD_LINK.finditer(body):
            edges.append(("links_to", m.group(2).split("#", 1)[0]))
        nodes[rel] = {
            "path": rel,
            "type": fm.get("type") or "Unknown",
            "title": fm.get("title") or path.stem,
            "description": fm.get("description") or "",
            "status": fm.get("status"),
            "timestamp": fm.get("timestamp") or fm.get("date"),
            "edges": edges,
            "body": body,
        }
    return nodes


def find_releases(nodes: dict[str, dict[str, Any]], ref: str | None) -> list[str]:
    if ref:
        if not ref.startswith("/"):
            # try match
            for p, n in nodes.items():
                if n["type"] == "Release" and (ref in p or ref in n["title"]):
                    return [p]
            candidate = ref if ref.startswith("/") else f"/releases/{ref}"
            if not candidate.endswith(".md"):
                candidate += ".md"
            return [candidate]
        return [ref]
    return sorted(p for p, n in nodes.items() if n["type"] == "Release")


def notes_for_release(nodes: dict[str, dict[str, Any]], release_path: str) -> dict[str, Any]:
    rel = nodes.get(release_path) or {
        "path": release_path,
        "title": Path(release_path).stem,
        "type": "Release",
        "description": "",
        "edges": [],
    }
    features: list[dict[str, Any]] = []
    code: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []

    # inbound: X -released_in-> Release, X -lands_in-> Release
    for p, n in nodes.items():
        for r, t in n["edges"]:
            if t != release_path:
                continue
            if r in ("released_in", "lands_in", "links_to"):
                if n["type"] == "Feature":
                    features.append(n)
                elif n["type"] == "CodeChange":
                    code.append(n)
                elif n["type"] == "DecisionRecord":
                    decisions.append(n)

    # outbound from release
    for r, t in rel.get("edges") or []:
        n = nodes.get(t)
        if not n:
            continue
        if n["type"] == "Feature":
            features.append(n)
        elif n["type"] == "CodeChange":
            code.append(n)

    # code that implements features in this release
    feat_paths = {f["path"] for f in features}
    for p, n in nodes.items():
        if n["type"] != "CodeChange":
            continue
        for r, t in n["edges"]:
            if r in ("implements", "lands_in") and t in feat_paths:
                code.append(n)

    def uniq(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        out = []
        for i in items:
            if i["path"] in seen:
                continue
            seen.add(i["path"])
            out.append(i)
        return out

    return {
        "release": rel,
        "features": uniq(features),
        "code": uniq(code),
        "decisions": uniq(decisions),
    }


def render(bundle_notes: list[dict[str, Any]]) -> str:
    lines = [
        "---",
        "type: ContextPack",
        "title: Release notes",
        "description: Generated from Release/Feature/CodeChange edges",
        f"timestamp: {utc_now()}",
        "generated: true",
        "tags: [release-notes, pkc]",
        "---",
        "",
        "# Release notes",
        "",
    ]
    if not bundle_notes:
        lines.append("_No Release concepts found._")
        return "\n".join(lines) + "\n"

    for pack in bundle_notes:
        r = pack["release"]
        lines.append(f"## {r.get('title') or r['path']}")
        lines.append("")
        if r.get("description"):
            lines.append(r["description"])
            lines.append("")
        lines.append(f"- Path: `{r['path']}`")
        if r.get("timestamp"):
            lines.append(f"- Date: {r['timestamp']}")
        lines.append("")
        lines.append("### Features")
        lines.append("")
        if not pack["features"]:
            lines.append("_None linked._")
        else:
            for f in pack["features"]:
                lines.append(f"- [{f['title']}]({f['path']}) — {f.get('description') or ''}".rstrip())
        lines.append("")
        lines.append("### Code changes")
        lines.append("")
        if not pack["code"]:
            lines.append("_None linked._")
        else:
            for c in pack["code"]:
                lines.append(f"- [{c['title']}]({c['path']})")
        lines.append("")
        if pack["decisions"]:
            lines.append("### Decisions")
            lines.append("")
            for d in pack["decisions"]:
                lines.append(f"- [{d['title']}]({d['path']})")
            lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC release notes generator")
    parser.add_argument("release", nargs="?", default=None)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--write", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    nodes = load_nodes(bundle)
    releases = find_releases(nodes, args.release)
    packs = [notes_for_release(nodes, r) for r in releases if r in nodes or True]
    # filter empty missing nodes without edges unless path exists
    packs = [p for p in packs if p["release"].get("type") == "Release" or p["features"] or p["code"]]
    if not packs and releases:
        # still emit placeholder for requested release
        packs = [notes_for_release(nodes, releases[0])]

    md = render(packs)
    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}")
    if args.json:
        import json

        print(json.dumps(packs, indent=2, default=str))
    elif not args.write:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
