#!/usr/bin/env python3
"""Import MADR / adr-tools style Architecture Decision Records into DecisionRecords.

Supports common layouts:
  - docs/adr/NNNN-title.md (adr-tools)
  - docs/decisions/*.md (MADR-ish)

Usage:
  python3 scripts/pkc_adr_import.py --from docs/adr --repo . --dry-run
  python3 scripts/pkc_adr_import.py --from tests/fixtures/adr --repo /tmp/x --bundle knowledge
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    ensure_bundle,
    parse_frontmatter,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    scrub_text,
    slugify,
    utc_now,
    write_concept,
)

STATUS_MAP = {
    "accepted": "accepted",
    "proposed": "proposed",
    "rejected": "rejected",
    "deprecated": "superseded",
    "superseded": "superseded",
    "approved": "accepted",
}


def parse_adr(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    text, _ = scrub_text(text)
    fm, body = parse_frontmatter(text)

    title = fm.get("title")
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.M)
        title = m.group(1).strip() if m else path.stem
    # strip ADR number prefix from title
    title = re.sub(r"^(?:ADR[- ]?)?\d+\.?\s*", "", title, flags=re.I).strip() or path.stem

    status_raw = str(fm.get("status") or "accepted").lower()
    # adr-tools often has **Status:** Accepted in body
    m = re.search(r"(?im)^\*?\*?Status\*?\*?:\s*(\w+)", body)
    if m:
        status_raw = m.group(1).lower()
    status = STATUS_MAP.get(status_raw, status_raw)

    def section(*names: str) -> str:
        for name in names:
            pat = re.compile(
                rf"(?ims)^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s+|\Z)"
            )
            sm = pat.search(body)
            if sm:
                return sm.group(1).strip()
        return ""

    context = section("Context", "Context and Problem Statement", "Problem")
    decision = section("Decision", "Decision Outcome", "Chosen option") or body[:500]
    consequences = section("Consequences", "Pros and Cons of the Options")

    return {
        "title": title,
        "status": status,
        "context": context or f"Imported from {path.name}",
        "decision": decision,
        "consequences": consequences or "_See original ADR._",
        "source": str(path),
    }


def import_dir(
    bundle: Path,
    source: Path,
    *,
    dry_run: bool = False,
) -> list[tuple[str, str]]:
    files = sorted(source.rglob("*.md")) if source.is_dir() else [source]
    results: list[tuple[str, str]] = []
    for path in files:
        if path.name.lower() in ("readme.md", "index.md", "template.md"):
            continue
        parsed = parse_adr(path)
        if not parsed:
            continue
        slug = slugify(parsed["title"])
        rel = path_for_type("DecisionRecord", slug)
        fm = {
            "type": "DecisionRecord",
            "title": parsed["title"],
            "description": parsed["decision"][:200],
            "status": parsed["status"],
            "tags": ["decision", "adr", "imported"],
            "timestamp": utc_now(),
            "verified": True,
            "generated": True,
            "stable_timestamp": True,
            "wiki_key": f"adr-{slug}",
            "truth_state": "current",
            "external_system": "adr-import",
            "external_id": path.name,
        }
        body = f"""# {parsed['title']}

## Context

{parsed['context']}

## Decision

{parsed['decision']}

## Consequences

{parsed['consequences']}

## Source

Imported from `{parsed['source']}`.
"""
        if dry_run:
            results.append((rel, "proposed"))
        else:
            _, action = write_concept(bundle, rel, fm, body)
            results.append((rel, action))
    if not dry_run and results:
        refresh_catalog_index(bundle, "decisions")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import ADR directory into PKC DecisionRecords")
    parser.add_argument("--from", dest="source", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.exists():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not args.dry_run:
        ensure_bundle(bundle)

    results = import_dir(bundle, source, dry_run=args.dry_run)
    if not results:
        print("No ADR files found.")
        return 0
    for rel, action in results:
        print(f"[{action}] {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
