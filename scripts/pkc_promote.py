#!/usr/bin/env python3
"""Promote a Discovery/Experiment/Meeting into Feature, Requirement, or DecisionRecord."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    add_typed_link,
    append_log,
    parse_frontmatter,
    path_for_type,
    refresh_catalog_index,
    resolve_author,
    resolve_knowledge_root,
    slugify,
    utc_now,
    write_knowledge,
)

PROMOTE_MAP = {
    "Feature": "features",
    "Requirement": "requirements",
    "DecisionRecord": "decisions",
    "Specification": "specs",
    "Design": "designs",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote informal concept to formal")
    parser.add_argument("source", help="Source concept path")
    parser.add_argument(
        "--to",
        required=True,
        choices=list(PROMOTE_MAP.keys()),
        help="Target concept type",
    )
    parser.add_argument("--title", default=None)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--author", default="")
    args = parser.parse_args(argv)

    author = resolve_author(args.author)
    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    src_path = Path(args.source)
    if not src_path.is_file():
        src_path = bundle / args.source.lstrip("/")
    if not src_path.is_file():
        print(f"error: source not found: {args.source}", file=sys.stderr)
        return 1

    fm, body = parse_frontmatter(src_path.read_text(encoding="utf-8"))
    title = args.title or fm.get("title") or src_path.stem
    slug = args.slug or slugify(title)
    rel = path_for_type(args.to, slug)
    src_rel = "/" + str(src_path.resolve().relative_to(bundle.resolve())).replace("\\", "/")

    new_fm: dict[str, Any] = {
        "type": args.to,
        "title": title,
        "description": fm.get("description") or f"Promoted from {src_rel}",
        "tags": list(dict.fromkeys((fm.get("tags") or []) + ["promoted", args.to.lower()])),
        "timestamp": utc_now(),
        "status": "proposed" if args.to != "DecisionRecord" else "proposed",
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"{PROMOTE_MAP[args.to]}-{slug}",
        "truth_state": "current",
        "sources": [src_rel],
        "links": [
            {
                "target": src_rel,
                "rel": "originates_from" if args.to == "DecisionRecord" else "informs",
            }
        ],
    }

    new_body = f"# {title}\n\n> Promoted from [{fm.get('title', src_path.stem)}]({src_rel}) (`{fm.get('type', 'unknown')}`)\n\n"
    new_body += body.strip() + "\n"

    path, action = write_knowledge(bundle, rel, new_fm, new_body, author=author)
    # Back-link from source
    back_rel = "informs" if args.to in ("Feature", "Requirement", "Specification", "Design") else "decides"
    # From source, the formal concept is what was shaped — use related_to / informs inverse as originates conceptually
    add_typed_link(src_path, f"/{rel}", "related_to", body_label=title)

    refresh_catalog_index(bundle, PROMOTE_MAP[args.to])
    append_log(bundle, f"Promoted {src_rel} → /{rel} as {args.to}")
    print(f"[{action}] {rel} (from {src_rel})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
