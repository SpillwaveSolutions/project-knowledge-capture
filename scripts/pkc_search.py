#!/usr/bin/env python3
"""Full-text search over a PKC knowledge bundle (Git stays source of truth).

No database required — walks concept Markdown and ranks simple term hits.
Optional: use ripgrep when available for large trees (`--rg`).

Usage:
  python3 scripts/pkc_search.py "JWT refresh" --bundle sample-knowledge
  python3 scripts/pkc_search.py JWT --type DecisionRecord,Feature --json
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import iter_concepts, parse_frontmatter, resolve_knowledge_root  # noqa: E402


def tokenize(q: str) -> list[str]:
    return [t for t in re.split(r"\s+", q.strip().lower()) if t]


def search(
    bundle: Path,
    query: str,
    *,
    types: list[str] | None = None,
    limit: int = 20,
    path_prefix: str | None = None,
) -> list[dict[str, Any]]:
    terms = tokenize(query)
    if not terms:
        return []

    type_filter = {t.lower() for t in (types or []) if t}
    results: list[dict[str, Any]] = []

    for path in iter_concepts(bundle):
        rel = "/" + path.relative_to(bundle).as_posix()
        if path_prefix and not rel.lstrip("/").startswith(path_prefix.lstrip("/")):
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        ctype = str(fm.get("type") or "Unknown")
        if type_filter and ctype.lower() not in type_filter:
            continue

        hay_title = str(fm.get("title") or path.stem).lower()
        hay_desc = str(fm.get("description") or "").lower()
        hay_tags = " ".join(str(t) for t in (fm.get("tags") or [])).lower()
        hay_body = body.lower()
        full = f"{hay_title}\n{hay_desc}\n{hay_tags}\n{hay_body}"

        score = 0
        hits: list[str] = []
        missing = False
        for term in terms:
            if term not in full:
                missing = True
                break
            # AND semantics
            c_title = hay_title.count(term)
            c_desc = hay_desc.count(term)
            c_tags = hay_tags.count(term)
            c_body = hay_body.count(term)
            score += c_title * 10 + c_desc * 5 + c_tags * 4 + min(c_body, 8)
            if c_title:
                hits.append("title")
            if c_desc:
                hits.append("description")
            if c_tags:
                hits.append("tags")
            if c_body:
                hits.append("body")
        if missing or score <= 0:
            continue

        snippet = _snippet(body or hay_desc, terms)
        results.append(
            {
                "path": rel,
                "type": ctype,
                "title": fm.get("title") or path.stem,
                "description": fm.get("description") or "",
                "status": fm.get("status"),
                "score": score,
                "hits": sorted(set(hits)),
                "snippet": snippet,
            }
        )

    results.sort(key=lambda r: (-r["score"], r["title"]))
    return results[:limit]


def _snippet(body: str, terms: list[str], width: int = 160) -> str:
    low = body.lower()
    pos = -1
    for t in terms:
        i = low.find(t)
        if i >= 0:
            pos = i
            break
    if pos < 0:
        text = re.sub(r"\s+", " ", body).strip()
        return text[:width] + ("…" if len(text) > width else "")
    start = max(0, pos - 40)
    end = min(len(body), pos + width)
    frag = re.sub(r"\s+", " ", body[start:end]).strip()
    if start > 0:
        frag = "…" + frag
    if end < len(body):
        frag = frag + "…"
    return frag


def render(results: list[dict[str, Any]], query: str) -> str:
    lines = [f"# Search: {query}", "", f"{len(results)} hit(s)", ""]
    if not results:
        lines.append("_No matches._")
        return "\n".join(lines) + "\n"
    for r in results:
        lines.append(f"## [{r['title']}]({r['path']}) · `{r['type']}` · score {r['score']}")
        if r.get("description"):
            lines.append("")
            lines.append(r["description"])
        if r.get("snippet"):
            lines.append("")
            lines.append(f"> {r['snippet']}")
        lines.append("")
        lines.append(f"_hits: {', '.join(r['hits'])}_")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC full-text search")
    parser.add_argument("query", help="Search terms (AND)")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--type", dest="types", default=None, help="Comma-separated types")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--prefix", default=None, help="Path prefix filter e.g. decisions/")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    types = [t.strip() for t in (args.types or "").split(",") if t.strip()] or None
    results = search(
        bundle, args.query, types=types, limit=args.limit, path_prefix=args.prefix
    )

    if args.json:
        import json

        print(json.dumps({"query": args.query, "count": len(results), "results": results}, indent=2))
    else:
        print(render(results, args.query))
    return 0


if __name__ == "__main__":
    sys.exit(main())
