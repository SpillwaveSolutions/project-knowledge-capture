#!/usr/bin/env python3
"""Add a typed edge between two OKF concepts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    DEFAULT_RELATIONS,
    add_typed_link,
    append_log,
    resolve_knowledge_root,
)


def resolve_concept(bundle: Path, ref: str) -> Path:
    ref = ref.strip()
    if ref.startswith("/"):
        return bundle / ref.lstrip("/")
    p = Path(ref)
    if p.is_file():
        return p.resolve()
    candidate = bundle / ref
    if candidate.is_file():
        return candidate
    # try with .md
    if not ref.endswith(".md"):
        c2 = bundle / f"{ref}.md"
        if c2.is_file():
            return c2
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add typed OKF edge")
    parser.add_argument("source", help="Source concept path (absolute in-bundle or file)")
    parser.add_argument("target", help="Target concept path (absolute in-bundle preferred)")
    parser.add_argument("--rel", required=True, help="Relation type")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--bidirectional", action="store_true")
    parser.add_argument("--reverse-rel", default=None)
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    src = resolve_concept(bundle, args.source)
    tgt_ref = args.target if args.target.startswith("/") else "/" + args.target.lstrip("./")
    if not tgt_ref.endswith(".md"):
        # keep as provided; add_typed_link does not require target exists
        pass

    if args.rel not in DEFAULT_RELATIONS:
        print(f"warning: rel '{args.rel}' is non-standard (allowed; OKF flags as info)", file=sys.stderr)

    action = add_typed_link(src, tgt_ref, args.rel)
    print(f"[{action}] {src.relative_to(bundle) if src.is_relative_to(bundle) else src} -[{args.rel}]-> {tgt_ref}")

    if args.bidirectional:
        rev = args.reverse_rel or "related_to"
        tgt_path = resolve_concept(bundle, args.target)
        src_ref = "/" + str(src.relative_to(bundle)).replace("\\", "/") if src.is_relative_to(bundle) else args.source
        action2 = add_typed_link(tgt_path, src_ref if src_ref.startswith("/") else "/" + src_ref, rev)
        print(f"[{action2}] reverse -[{rev}]-> {src_ref}")

    if action == "created":
        append_log(bundle, f"Linked {args.source} -[{args.rel}]-> {tgt_ref}")
    return 0 if action != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
