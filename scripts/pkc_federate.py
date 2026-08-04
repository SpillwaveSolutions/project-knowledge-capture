#!/usr/bin/env python3
"""Multi-repo / federated knowledge roots (read-only remotes).

Reads `pkc.federation` from config — a list of named external bundle paths.
Reports cross-repo `maps_to` candidates and optional shadow index under
`knowledge/federation/`.

Config example:
  pkc:
    federation:
      - name: platform
        path: ../platform-service/knowledge
        readonly: true
      - name: design-system
        path: /abs/path/to/knowledge

Usage:
  python3 scripts/pkc_federate.py list --repo .
  python3 scripts/pkc_federate.py search JWT --repo .
  python3 scripts/pkc_federate.py index --repo . --write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    dump_frontmatter,
    iter_concepts,
    load_config,
    parse_frontmatter,
    resolve_knowledge_root,
    utc_now,
)
from pkc_search import search as search_bundle  # noqa: E402


def federation_entries(repo: Path) -> list[dict[str, Any]]:
    cfg = load_config(repo)
    fed = cfg.get("federation") or []
    if not isinstance(fed, list):
        return []
    out = []
    for entry in fed:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name") or "remote"
        path = entry.get("path")
        if not path:
            continue
        p = Path(path)
        if not p.is_absolute():
            p = (repo / p).resolve()
        out.append(
            {
                "name": name,
                "path": p,
                "readonly": entry.get("readonly", True),
                "exists": p.is_dir() and (p / "index.md").is_file(),
            }
        )
    return out


def local_and_remote(repo: Path, bundle_override: str | None = None) -> list[dict[str, Any]]:
    local = resolve_knowledge_root(repo, bundle_override)
    roots = [{"name": "local", "path": local, "readonly": False, "exists": local.is_dir()}]
    roots.extend(federation_entries(repo))
    return roots


def list_roots(repo: Path, bundle_override: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for r in local_and_remote(repo, bundle_override):
        count = 0
        if r["exists"]:
            count = len(iter_concepts(r["path"]))
        rows.append({**r, "path": str(r["path"]), "concept_count": count})
    return rows


def federated_search(
    repo: Path,
    query: str,
    *,
    bundle_override: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for r in local_and_remote(repo, bundle_override):
        if not r["exists"]:
            continue
        for h in search_bundle(r["path"], query, limit=limit):
            hits.append({**h, "federation": r["name"], "bundle": str(r["path"])})
    hits.sort(key=lambda x: (-x["score"], x.get("federation", ""), x["title"]))
    return hits[:limit]


def build_index(repo: Path, bundle_override: str | None = None) -> str:
    """Markdown shadow index of federated catalogs (paths only, no copy)."""
    lines = [
        "---",
        "type: Catalog",
        "title: Federation index",
        "description: Read-only map of local + remote knowledge roots",
        f"timestamp: {utc_now()}",
        "generated: true",
        "tags: [federation, pkc]",
        "---",
        "",
        "# Federation index",
        "",
        "Remotes are **read-only**. Use `maps_to` edges to link local concepts.",
        "",
    ]
    for r in list_roots(repo, bundle_override):
        status = "ok" if r["exists"] else "missing"
        lines.append(f"## {r['name']} (`{status}`)")
        lines.append("")
        lines.append(f"- Path: `{r['path']}`")
        lines.append(f"- Concepts: {r['concept_count']}")
        lines.append(f"- Readonly: {r.get('readonly', True)}")
        lines.append("")
        if r["exists"] and r["name"] != "local":
            # sample titles
            root = Path(r["path"])
            samples = []
            for path in iter_concepts(root)[:12]:
                fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
                rel = path.relative_to(root).as_posix()
                samples.append(f"- `{r['name']}:{rel}` — {fm.get('title') or path.stem}")
            if samples:
                lines.append("### Sample concepts")
                lines.append("")
                lines.extend(samples)
                lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC multi-repo federation")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List local + federated roots")
    p_s = sub.add_parser("search", help="Search across federation")
    p_s.add_argument("query")
    p_s.add_argument("--limit", type=int, default=20)
    p_s.add_argument("--json", action="store_true")
    p_i = sub.add_parser("index", help="Build federation shadow index markdown")
    p_i.add_argument("--write", action="store_true", help="Write to local bundle federation/index.md")

    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()

    if args.cmd == "list":
        import json

        print(json.dumps(list_roots(repo, args.bundle), indent=2))
        return 0

    if args.cmd == "search":
        hits = federated_search(repo, args.query, bundle_override=args.bundle, limit=args.limit)
        if args.json:
            import json

            print(json.dumps({"query": args.query, "count": len(hits), "results": hits}, indent=2))
        else:
            print(f"# Federated search: {args.query}\n")
            for h in hits:
                print(f"- [{h['federation']}] [{h['title']}]({h['path']}) · `{h['type']}` · score {h['score']}")
        return 0

    if args.cmd == "index":
        md = build_index(repo, args.bundle)
        if args.write:
            local = resolve_knowledge_root(repo, args.bundle)
            out = local / "federation" / "index.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md if md.endswith("\n") else md + "\n", encoding="utf-8")
            print(f"Wrote {out}")
        else:
            print(md)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
