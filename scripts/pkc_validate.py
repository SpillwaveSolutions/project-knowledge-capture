#!/usr/bin/env python3
"""Validate a PKC/OKF knowledge bundle structure.

Checks:
  - root index.md with okf_version
  - catalogs present (optional warn)
  - concept frontmatter minimum fields (type + title)
  - shared JSON Schema pack when okf_schema is importable
  - absolute link targets resolve inside the bundle
  - typed links are dicts with target + rel
  - truth_state union (PKC/SAC + DEKC)

When the SQLite index is available, concepts are validated from the
self-healing snapshot (mtime+size refresh) instead of re-reading every
file. `--no-index` forces a disk walk. Exit 0 = ok (warnings allowed);
exit 1 = errors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    CATALOGS,
    MD_LINK,
    parse_frontmatter,
    resolve_knowledge_root,
)
from pkc_index import open_graph  # noqa: E402

# Shared schema pack lives in okf-plugin; sibling checkout is the default.
_OKF_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "okf-plugin" / "scripts"
if _OKF_SCRIPTS.is_dir() and str(_OKF_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_OKF_SCRIPTS))
try:
    from okf_schema import TRUTH_STATES, load_default_registry  # type: ignore
except ImportError:
    TRUTH_STATES = frozenset(
        {"current", "snapshot", "superseded", "archived", "historical", "proposed"}
    )
    load_default_registry = None  # type: ignore

REQUIRED_FM = ("type", "title")
RECOMMENDED_FM = ("description", "timestamp")
BUG_RECOMMENDED_RELS = frozenset(
    {"affects", "reproduces_in", "fixed_in", "lands_in", "implements", "on_branch"}
)


def iter_concepts(bundle: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(bundle.rglob("*.md")):
        if p.name in ("index.md", "log.md"):
            continue
        if "packs" in p.parts:
            continue
        files.append(p)
    return files


def _validate_concept(
    bundle: Path,
    rel: str,
    fm: dict[str, Any],
    body: str,
    *,
    strict: bool,
    schema_reg: Any,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not fm:
        errors.append(f"{rel}: missing YAML frontmatter")
        return

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
                    msg = f"{rel}: broken typed link → {tgt}"
                    (errors if strict else warnings).append(msg)

    for m in MD_LINK.finditer(body):
        tgt = m.group(2).split("#", 1)[0]
        if not (bundle / tgt.lstrip("/")).is_file():
            msg = f"{rel}: broken body link → {tgt}"
            (errors if strict else warnings).append(msg)

    ts = fm.get("truth_state")
    if ts and ts not in TRUTH_STATES:
        warnings.append(f"{rel}: unusual truth_state `{ts}`")

    if fm.get("type") == "TicketLink" and fm.get("kind") == "bug":
        rels = set()
        if isinstance(fm.get("links"), list):
            for link in fm["links"]:
                if isinstance(link, dict) and link.get("rel"):
                    rels.add(str(link["rel"]))
        if not (rels & BUG_RECOMMENDED_RELS) and not fm.get("branch"):
            warnings.append(
                f"{rel}: kind=bug should link to a Module/Package/Release/CodeChange/Branch "
                f"(rels {sorted(BUG_RECOMMENDED_RELS)}) or set `branch`"
            )

    if fm.get("type") == "Bug":
        rels = set()
        if isinstance(fm.get("links"), list):
            for link in fm["links"]:
                if isinstance(link, dict) and link.get("rel"):
                    rels.add(str(link["rel"]))
        if not (rels & BUG_RECOMMENDED_RELS) and not fm.get("branch"):
            warnings.append(
                f"{rel}: Bug should link to a Module/Package/Release/CodeChange/Branch "
                f"(rels {sorted(BUG_RECOMMENDED_RELS)}) or set `branch`"
            )

    if schema_reg is not None:
        for issue in schema_reg.validate_frontmatter(fm, path=rel):
            if issue.severity == "error":
                if "missing required" in issue.message and (
                    "`type`" in issue.message or "`title`" in issue.message
                ):
                    continue
                errors.append(f"{rel}: {issue.message}")
            elif issue.severity == "warn":
                if issue.message.startswith("unusual truth_state"):
                    continue
                if "kind=bug" in issue.message or "recommended link rel" in issue.message:
                    continue
                if issue.message.startswith("Bug should link"):
                    continue
                warnings.append(f"{rel}: {issue.message}")


def _bundle_header(
    bundle: Path, *, strict: bool
) -> tuple[list[str], list[str], Any]:
    errors: list[str] = []
    warnings: list[str] = []

    index = bundle / "index.md"
    if not index.is_file():
        errors.append("missing root index.md")
        return errors, warnings, None

    idx_fm, _ = parse_frontmatter(index.read_text(encoding="utf-8"))
    if "okf_version" not in idx_fm and "okf_version" not in index.read_text(encoding="utf-8"):
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

    schema_reg = None
    if load_default_registry:
        schema_reg = load_default_registry(start=bundle.parent)
        pkc_schemas = Path(__file__).resolve().parent.parent / "schemas" / "okf-concepts"
        if pkc_schemas.is_dir():
            schema_reg.load_dir(pkc_schemas)
    return errors, warnings, schema_reg


def validate_bundle(
    bundle: Path, *, strict: bool = False, use_index: bool | None = None
) -> tuple[list[str], list[str]]:
    errors, warnings, schema_reg = _bundle_header(bundle, strict=strict)
    if any(e == "missing root index.md" for e in errors):
        return errors, warnings

    used_index = False
    if use_index is not False:
        graph = open_graph(bundle)
        if graph is not None:
            try:
                for rec in graph.iter_nodes():
                    rel = rec.path.lstrip("/")
                    _validate_concept(
                        bundle,
                        rel,
                        rec.frontmatter(),
                        rec.body,
                        strict=strict,
                        schema_reg=schema_reg,
                        errors=errors,
                        warnings=warnings,
                    )
                used_index = True
            finally:
                graph.close()

    if not used_index:
        for path in iter_concepts(bundle):
            rel = path.relative_to(bundle).as_posix()
            text = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(text)
            _validate_concept(
                bundle,
                rel,
                fm,
                body,
                strict=strict,
                schema_reg=schema_reg,
                errors=errors,
                warnings=warnings,
            )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PKC knowledge bundle")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--strict", action="store_true", help="Treat broken links as errors")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Disable the SQLite index; always re-read every concept",
    )
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    errors, warnings = validate_bundle(
        bundle, strict=args.strict, use_index=False if args.no_index else None
    )

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
