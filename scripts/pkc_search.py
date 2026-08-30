#!/usr/bin/env python3
"""Full-text search over a PKC knowledge bundle (Git stays source of truth).

No database required — walks concept Markdown and ranks simple term hits.
Uses ripgrep as a prefilter when `rg` is on PATH (or PKC_RG_PATH). Ranking
is always computed in Python over the candidate files, so scores stay
identical to a full scan. `--no-rg` forces the linear walk.

Usage:
  python3 scripts/pkc_search.py "JWT refresh" --bundle sample-knowledge
  python3 scripts/pkc_search.py JWT --type DecisionRecord,Feature --json
  python3 scripts/pkc_search.py JWT --rg
  python3 scripts/pkc_search.py JWT --no-rg
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    find_rg,
    is_concept_path,
    iter_concepts,
    parse_frontmatter,
    resolve_knowledge_root,
    rg_list_files,
)


def tokenize(q: str) -> list[str]:
    return [t for t in re.split(r"\s+", q.strip().lower()) if t]


def candidate_files(
    bundle: Path,
    terms: list[str],
    *,
    path_prefix: str | None = None,
    use_rg: bool | None = None,
) -> tuple[list[Path], str]:
    """Return (files, engine) where engine is 'rg' or 'scan'.

    use_rg True: prefer rg, fall back to scan if missing.
    use_rg False: always scan.
    use_rg None: auto (rg if found).
    """
    universe = iter_concepts(bundle)
    if path_prefix:
        prefix = path_prefix.lstrip("/")
        universe = [
            p
            for p in universe
            if ("/" + p.relative_to(bundle).as_posix()).lstrip("/").startswith(prefix)
        ]
    if use_rg is False:
        return universe, "scan"
    if use_rg is None and not find_rg():
        return universe, "scan"
    hits = rg_list_files(bundle, terms, ignore_case=True, fixed_string=False)
    if hits is None:
        return universe, "scan"
    allowed = {p.resolve() for p in hits}
    filtered = [
        p
        for p in universe
        if p.resolve() in allowed and is_concept_path(bundle, p)
    ]
    return filtered, "rg"


def search(
    bundle: Path,
    query: str,
    *,
    types: list[str] | None = None,
    limit: int = 20,
    path_prefix: str | None = None,
    use_rg: bool | None = None,
) -> list[dict[str, Any]]:
    terms = tokenize(query)
    if not terms:
        return []

    type_filter = {t.lower() for t in (types or []) if t}
    results: list[dict[str, Any]] = []
    files, _engine = candidate_files(
        bundle, terms, path_prefix=path_prefix, use_rg=use_rg
    )

    for path in files:
        rel = "/" + path.relative_to(bundle).as_posix()
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
    parser.add_argument(
        "--rg",
        action="store_true",
        help="Use ripgrep to prefilter candidate files (default when rg is on PATH)",
    )
    parser.add_argument(
        "--no-rg",
        action="store_true",
        help="Disable ripgrep; always full-scan",
    )
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    if args.rg and args.no_rg:
        print("error: --rg and --no-rg are mutually exclusive", file=sys.stderr)
        return 2
    if args.no_rg:
        use_rg: bool | None = False
    elif args.rg:
        use_rg = True
        if not find_rg():
            print(
                "pkc_search: rg not found; falling back to full scan. "
                "Install ripgrep or pass --no-rg. See /pkc-setup.",
                file=sys.stderr,
            )
    else:
        use_rg = None

    types = [t.strip() for t in (args.types or "").split(",") if t.strip()] or None
    results = search(
        bundle,
        args.query,
        types=types,
        limit=args.limit,
        path_prefix=args.prefix,
        use_rg=use_rg,
    )
    engine = "scan" if use_rg is False or not find_rg() else "rg"

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "query": args.query,
                    "count": len(results),
                    "engine": engine,
                    "results": results,
                },
                indent=2,
            )
        )
    else:
        print(render(results, args.query))
    return 0


if __name__ == "__main__":
    sys.exit(main())
