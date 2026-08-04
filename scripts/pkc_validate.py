#!/usr/bin/env python3
"""Validate a PKC/OKF knowledge bundle structure.

Checks:
  - root index.md with okf_version
  - catalogs present (optional warn)
  - concept frontmatter minimum fields
  - absolute link targets resolve inside the bundle
  - typed links are dicts with target + rel
  - truth_state / wiki_key consistency (info)

Exit 0 = ok (warnings allowed); exit 1 = errors.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import CATALOGS, parse_frontmatter, resolve_knowledge_root  # noqa: E402

MD_LINK = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")
REQUIRED_FM = ("type", "title")
RECOMMENDED_FM = ("description", "timestamp")


def iter_concepts(bundle: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(bundle.rglob("*.md")):
        if p.name in ("index.md", "log.md"):
            continue
        if "packs" in p.parts:
            continue
        files.append(p)
    return files


def validate_bundle(bundle: Path, *, strict: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    index = bundle / "index.md"
    if not index.is_file():
        errors.append("missing root index.md")
        return errors, warnings

    idx_fm, _ = parse_frontmatter(index.read_text(encoding="utf-8"))
    if "okf_version" not in idx_fm and "okf_version" not in index.read_text(encoding="utf-8"):
        # also allow bare okf_version in frontmatter parsed
        if "okf_version" not in index.read_text(encoding="utf-8"):
            errors.append("root index.md missing okf_version")

    for cat in CATALOGS:
        cat_dir = bundle / cat
        if not cat_dir.is_dir():
            warnings.append(f"catalog dir missing: {cat}/")
        elif not (cat_dir / "index.md").is_file():
            warnings.append(f"catalog index missing: {cat}/index.md")

    if not (bundle / "log.md").is_file():
        warnings.append("missing log.md")

    for path in iter_concepts(bundle):
        rel = path.relative_to(bundle).as_posix()
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if not fm:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue

        for key in REQUIRED_FM:
            if not fm.get(key):
                errors.append(f"{rel}: missing frontmatter field `{key}`")

        for key in RECOMMENDED_FM:
            if not fm.get(key):
                warnings.append(f"{rel}: recommended field missing `{key}`")

        links = fm.get("links")
        if links is not None:
            if not isinstance(links, list):
                errors.append(f"{rel}: links must be a list")
            else:
                for i, link in enumerate(links):
                    if not isinstance(link, dict):
                        errors.append(f"{rel}: links[{i}] must be a map with target/rel")
                        continue
                    if not link.get("target"):
                        errors.append(f"{rel}: links[{i}] missing target")
                    if not link.get("rel"):
                        warnings.append(f"{rel}: links[{i}] missing rel")
                    tgt = link.get("target") or ""
                    if tgt.startswith("/") and not (bundle / tgt.lstrip("/")).is_file():
                        # allow missing targets as warning (WIP graphs)
                        msg = f"{rel}: broken typed link → {tgt}"
                        (errors if strict else warnings).append(msg)

        for m in MD_LINK.finditer(body):
            tgt = m.group(2).split("#", 1)[0]
            if not (bundle / tgt.lstrip("/")).is_file():
                msg = f"{rel}: broken body link → {tgt}"
                (errors if strict else warnings).append(msg)

        ts = fm.get("truth_state")
        if ts and ts not in ("current", "snapshot", "superseded", "archived"):
            warnings.append(f"{rel}: unusual truth_state `{ts}`")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PKC knowledge bundle")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--strict", action="store_true", help="Treat broken links as errors")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    errors, warnings = validate_bundle(bundle, strict=args.strict)

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "bundle": str(bundle),
                    "ok": not errors,
                    "errors": errors,
                    "warnings": warnings,
                },
                indent=2,
            )
        )
    else:
        print(f"Bundle: {bundle}")
        for w in warnings:
            print(f"  warn  {w}")
        for e in errors:
            print(f"  error {e}")
        print(
            f"Summary: {len(errors)} error(s), {len(warnings)} warning(s) — "
            f"{'PASS' if not errors else 'FAIL'}"
        )

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
