#!/usr/bin/env python3
"""Materialize WikiTicket worklog fold + docs into OKF concepts.

Reads JSON fold (from `bin/worklog fold` or a fixture file) and writes
idempotent OKF concept files under the knowledge root.

Usage:
  bin/worklog fold | python3 scripts/pkc_materialize.py --repo . --bundle knowledge
  python3 scripts/pkc_materialize.py --repo . --fold tests/fixtures/fold.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    append_log,
    content_fingerprint,
    ensure_bundle,
    parse_frontmatter,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    slugify,
    utc_now,
    write_concept,
)

LEVEL_FEATURE = {"epic", "story"}

LEVEL_TO_WORK_TYPE = {
    "epic": "Epic",
    "story": "Story",
    "task": "Task",
    "subtask": "Subtask",
}


def work_concept_type(level: str, kind: str) -> str:
    if kind == "bug":
        return "Bug"
    return LEVEL_TO_WORK_TYPE.get(level, "Task")


def load_fold(path: str | None) -> dict[str, Any]:
    if path:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            return {"items": [], "meta": {}}
        data = json.loads(raw)
    if isinstance(data, list):
        return {"items": data, "meta": {}}
    if "items" not in data and "entities" in data:
        data = {**data, "items": data["entities"]}
    data.setdefault("items", [])
    return data


def item_status(item: dict[str, Any]) -> str:
    s = (item.get("status") or item.get("state") or "open").lower()
    mapping = {
        "todo": "open",
        "open": "open",
        "in_progress": "in_progress",
        "doing": "in_progress",
        "blocked": "blocked",
        "done": "done",
        "closed": "done",
        "cancelled": "cancelled",
        "canceled": "cancelled",
    }
    return mapping.get(s, s)


def extract_external(item: dict[str, Any]) -> tuple[str | None, str | None]:
    ext = item.get("external") or {}
    if isinstance(ext, dict):
        key = ext.get("key") or ext.get("id") or ext.get("number")
        system = ext.get("system") or ext.get("provider") or "github"
        if key is not None:
            return str(key), str(system)
    if item.get("external_id"):
        return str(item["external_id"]), str(item.get("external_system") or "github")
    if item.get("github_issue") is not None:
        return str(item["github_issue"]), "github"
    return None, None


# Fields that actually reach the rendered concept. A change to anything else
# (priority churn, a re-fold timestamp) must not force a rewrite.
FINGERPRINT_FIELDS = ("title", "body", "description", "status", "state",
                      "level", "kind", "parent", "parent_id", "wiki_key",
                      "truth_state", "priority")


def item_fingerprint(item: dict[str, Any]) -> str:
    """Stable hash of the item fields that affect the rendered concept."""
    parts = [f"{k}={item.get(k)!r}" for k in FINGERPRINT_FIELDS]
    ext_id, ext_system = extract_external(item)
    parts.append(f"external={ext_system!r}:{ext_id!r}")
    return content_fingerprint(*parts)


def fingerprint_matches(path: Path, fingerprint: str) -> bool:
    """True when `path` already records this fingerprint — skip before rendering."""
    if not path.is_file():
        return False
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm.get("source_fingerprint") == fingerprint


def materialize_item(
    bundle: Path,
    item: dict[str, Any],
    *,
    include: set[str],
    force: bool = False,
) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    fingerprint = item_fingerprint(item)
    ulid = item.get("id") or item.get("ulid") or item.get("worklog_id")
    title = item.get("title") or item.get("name") or "Untitled"
    level = (item.get("level") or "task").lower()
    kind = (item.get("kind") or "triage").lower()
    body_src = item.get("body") or item.get("description") or ""
    status = item_status(item)
    external_id, external_system = extract_external(item)
    wiki_key = item.get("wiki_key") or (f"work-{ulid}" if ulid else None)
    truth = item.get("truth_state") or "current"
    ts = item.get("updated_at") or item.get("created_at") or utc_now()
    parent = item.get("parent") or item.get("parent_id")

    feature_rel: str | None = None
    if level in LEVEL_FEATURE and "features" in include:
        slug = slugify(title)
        if ulid:
            slug = slugify(f"{title}-{str(ulid)[-6:].lower()}")
        feature_rel = path_for_type("Feature", slug)
    if feature_rel and not force and fingerprint_matches(bundle / feature_rel, fingerprint):
        results.append((feature_rel, "unchanged", "Feature"))
    elif feature_rel:
        fm: dict[str, Any] = {
            "type": "Feature",
            "title": title,
            "description": (body_src or title)[:200],
            "tags": ["feature", kind, "materialized"],
            "timestamp": ts,
            "status": "active" if status not in ("done", "cancelled") else status,
            "verified": False,
            "generated": True,
            "stable_timestamp": True,
            "level": level,
            "kind": kind,
            "truth_state": truth,
            "source_fingerprint": fingerprint,
        }
        if item.get("priority") is not None:
            fm["priority"] = item.get("priority")
        if wiki_key:
            fm["wiki_key"] = wiki_key
        if ulid:
            fm["worklog_id"] = ulid
        if external_id:
            fm["external_id"] = external_id
            fm["external_system"] = external_system
        links: list[dict[str, str]] = []
        if ulid and "tickets" in include:
            ticket_rel = path_for_type("TicketLink", slugify(f"ticket-{ulid}"))
            links.append({"target": f"/{ticket_rel}", "rel": "tracks"})
        if parent:
            links.append(
                {
                    "target": f"/tickets/ticket-{slugify(str(parent))}.md",
                    "rel": "related_to",
                }
            )
        if links:
            fm["links"] = links
        if force:
            fm["force"] = True
        body = f"# {title}\n\n"
        if body_src:
            body += body_src.strip() + "\n\n"
        body += "## Provenance\n\n- Materialized from WikiTicket work item\n"
        if ulid:
            body += f"- Worklog ULID: `{ulid}`\n"
        if external_id:
            body += f"- External: {external_system} `{external_id}`\n"
        _, action = write_concept(bundle, feature_rel, fm, body)
        results.append((feature_rel, action, "Feature"))

    trel: str | None = None
    if ulid and "tickets" in include:
        trel = path_for_type("TicketLink", slugify(f"ticket-{ulid}"))
    if trel and not force and fingerprint_matches(bundle / trel, fingerprint):
        results.append((trel, "unchanged", "TicketLink"))
    elif trel:
        tfm: dict[str, Any] = {
            "type": "TicketLink",
            "title": title,
            "description": f"TicketLink for {ulid}",
            "tags": ["ticket", "worklog", "materialized", kind],
            "timestamp": ts,
            "status": status,
            "verified": False,
            "generated": True,
            "stable_timestamp": True,
            "worklog_id": ulid,
            "truth_state": truth,
            "source_fingerprint": fingerprint,
        }
        if wiki_key:
            tfm["wiki_key"] = wiki_key
        if external_id:
            tfm["external_id"] = external_id
            tfm["external_system"] = external_system
        tlinks: list[dict[str, str]] = []
        if feature_rel:
            tlinks.append({"target": f"/{feature_rel}", "rel": "tracks"})
        if tlinks:
            tfm["links"] = tlinks
        if force:
            tfm["force"] = True
        tbody = f"# {title}\n\n## External reference\n\n- Worklog ULID: `{ulid}`\n"
        if external_id:
            tbody += f"- System: {external_system}\n- ID: `{external_id}`\n"
        tbody += f"\n## Status\n\n`{status}` · level `{level}` · kind `{kind}`\n"
        _, action = write_concept(bundle, trel, tfm, tbody)
        results.append((trel, action, "TicketLink"))

    work_type = work_concept_type(level, kind)
    wrel: str | None = None
    if ulid and "tickets" in include:
        wrel = path_for_type(work_type, slugify(f"{work_type.lower()}-{ulid}"))
    if wrel and not force and fingerprint_matches(bundle / wrel, fingerprint):
        results.append((wrel, "unchanged", work_type))
    elif wrel:
        wfm: dict[str, Any] = {
            "type": work_type,
            "title": title,
            "description": (body_src or title)[:200],
            "tags": ["work", "materialized", kind, level],
            "timestamp": ts,
            "status": status,
            "verified": False,
            "generated": True,
            "stable_timestamp": True,
            "worklog_id": ulid,
            "level": level,
            "kind": kind,
            "truth_state": truth,
            "source_fingerprint": fingerprint,
        }
        if wiki_key:
            wfm["wiki_key"] = wiki_key
        if external_id:
            wfm["external_id"] = external_id
            wfm["external_system"] = external_system
        if parent:
            wfm["parent"] = str(parent)
        if item.get("priority") is not None:
            wfm["priority"] = item.get("priority")
        branch_name = item.get("branch")
        if branch_name:
            wfm["branch"] = str(branch_name)
        wlinks: list[dict[str, str]] = []
        if trel:
            wlinks.append({"target": f"/{trel}", "rel": "tracks"})
        if feature_rel:
            wlinks.append({"target": f"/{feature_rel}", "rel": "implements"})
        if parent:
            parent_ticket = path_for_type("TicketLink", slugify(f"ticket-{parent}"))
            wlinks.append({"target": f"/{parent_ticket}", "rel": "child_of"})
            parent_work = work_concept_type(
                str(item.get("parent_level") or "task"),
                str(item.get("parent_kind") or "feature"),
            )
            parent_rel = path_for_type(parent_work, slugify(f"{parent_work.lower()}-{parent}"))
            if parent_rel != parent_ticket:
                wlinks.append({"target": f"/{parent_rel}", "rel": "child_of"})
        if branch_name:
            brel = path_for_type("Branch", slugify(str(branch_name)))
            wlinks.append({"target": f"/{brel}", "rel": "on_branch"})
        if wlinks:
            wfm["links"] = wlinks
        if force:
            wfm["force"] = True
        wbody = f"# {title}\n\n`{work_type}` · `{status}` · level `{level}` · kind `{kind}`\n"
        if body_src:
            wbody += "\n" + body_src.strip() + "\n"
        if ulid:
            wbody += f"\n## Provenance\n\n- Worklog ULID: `{ulid}`\n"
        _, action = write_concept(bundle, wrel, wfm, wbody)
        results.append((wrel, action, work_type))

    branch_name = item.get("branch")
    if branch_name and "tickets" in include:
        brel = path_for_type("Branch", slugify(str(branch_name)))
        if not force and fingerprint_matches(bundle / brel, fingerprint):
            results.append((brel, "unchanged", "Branch"))
        elif not (bundle / brel).is_file() or force:
            bfm = {
                "type": "Branch",
                "title": str(branch_name),
                "name": str(branch_name),
                "description": f"Branch {branch_name}",
                "tags": ["branch", "materialized"],
                "timestamp": ts,
                "status": "active",
                "verified": False,
                "generated": True,
                "stable_timestamp": True,
                "truth_state": "current",
                "source_fingerprint": fingerprint,
            }
            blinks: list[dict[str, str]] = []
            if wrel:
                blinks.append({"target": f"/{wrel}", "rel": "heads"})
            if trel:
                blinks.append({"target": f"/{trel}", "rel": "related_to"})
            if blinks:
                bfm["links"] = blinks
            if force:
                bfm["force"] = True
            bbody = f"# {branch_name}\n\nSource-control branch materialized from a work item.\n"
            _, action = write_concept(bundle, brel, bfm, bbody)
            results.append((brel, action, "Branch"))

    return results


def materialize_docs(
    repo: Path,
    bundle: Path,
    *,
    include: set[str],
    force: bool = False,
) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    docs = repo / "docs"
    if not docs.is_dir():
        return results

    if "decisions" in include:
        for pattern in ("**/adr*.md", "**/ADR*.md", "**/decisions/**/*.md", "**/adrs/**/*.md"):
            for path in docs.glob(pattern):
                if path.name.lower() in ("index.md", "readme.md"):
                    continue
                results.extend(_doc_to_concept(path, bundle, "DecisionRecord", "decisions", force))

    if "designs" in include:
        for pattern in ("**/design*/**/*.md", "**/walkthrough*/**/*.md"):
            for path in docs.glob(pattern):
                if path.name.lower() in ("index.md", "readme.md"):
                    continue
                results.extend(_doc_to_concept(path, bundle, "Design", "designs", force))

    if "specs" in include:
        for pattern in ("**/plans/**/*.md", "**/plan*.md"):
            for path in docs.glob(pattern):
                if path.name.lower() in ("index.md", "readme.md"):
                    continue
                results.extend(_doc_to_concept(path, bundle, "Specification", "specs", force))

    if "releases" in include:
        for pattern in ("**/releases/**/*.md",):
            for path in docs.glob(pattern):
                if path.name.lower() in ("index.md", "readme.md"):
                    continue
                results.extend(_doc_to_concept(path, bundle, "Release", "releases", force))

    # de-dupe by path (glob overlaps)
    seen: set[str] = set()
    unique: list[tuple[str, str, str]] = []
    for rel, action, kind in results:
        if rel in seen:
            continue
        seen.add(rel)
        unique.append((rel, action, kind))
    return unique


def _doc_to_concept(
    path: Path,
    bundle: Path,
    concept_type: str,
    catalog: str,
    force: bool,
) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    body = text
    title = path.stem.replace("-", " ").replace("_", " ").title()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip("\n")
            for line in parts[1].splitlines():
                if line.strip().startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip("\"'")
    slug = slugify(path.stem)
    rel = f"{catalog}/{slug}.md"
    fm: dict[str, Any] = {
        "type": concept_type,
        "title": title,
        "description": f"Materialized from {path.as_posix()}",
        "tags": [catalog.rstrip("s"), "materialized", "docs"],
        "timestamp": utc_now(),
        "status": "accepted" if concept_type == "DecisionRecord" else "active",
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "sources": [str(path.as_posix())],
        "truth_state": "current",
        "wiki_key": f"{catalog}-{slug}",
    }
    if force:
        fm["force"] = True
    content_body = f"# {title}\n\n> Source: `{path.as_posix()}`\n\n{body.strip()}\n"
    _, action = write_concept(bundle, rel, fm, content_body)
    return [(rel, action, concept_type)]


# Only these two actions put new bytes on disk. `skipped` compared and
# discarded, `unchanged` short-circuited on the fingerprint, `refused` was
# blocked by the truth_state barrier -- none of them change what a catalog
# index would say, so none of them justify rewriting one.
WROTE = ("created", "updated")


def catalogs_touched(report: list[dict[str, str]]) -> set[str]:
    cats: set[str] = set()
    for r in report:
        if r["action"] not in WROTE:
            continue
        top = r["path"].split("/", 1)[0]
        cats.add(top)
    return cats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize WikiTicket → OKF/PKC")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--bundle", default=None, help="Knowledge root (default: resolve)")
    parser.add_argument("--fold", default=None, help="Path to fold JSON (else stdin)")
    parser.add_argument(
        "--include",
        default="features,decisions,designs,releases,tickets,specs",
        help="Comma-separated catalogs to materialize",
    )
    parser.add_argument("--from-docs", action="store_true", default=False)
    parser.add_argument("--no-worklog", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Machine-readable report")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    bundle = resolve_knowledge_root(repo, args.bundle)
    include = {x.strip() for x in args.include.split(",") if x.strip()}
    from_worklog = not args.no_worklog

    if not args.dry_run:
        ensure_bundle(bundle)

    report: list[dict[str, str]] = []
    if from_worklog:
        fold = load_fold(args.fold)
        for item in fold.get("items") or []:
            if not isinstance(item, dict):
                continue
            if item_status(item) == "cancelled" and not args.force:
                continue
            for rel, action, kind in materialize_item(
                bundle, item, include=include, force=args.force
            ):
                report.append({"path": rel, "action": action, "type": kind})

    if args.from_docs:
        for rel, action, kind in materialize_docs(
            repo, bundle, include=include, force=args.force
        ):
            report.append({"path": rel, "action": action, "type": kind})

    if not args.dry_run:
        for cat in sorted(catalogs_touched(report)):
            refresh_catalog_index(bundle, cat)
        created = sum(1 for r in report if r["action"] == "created")
        updated = sum(1 for r in report if r["action"] == "updated")
        skipped = sum(1 for r in report if r["action"] == "skipped")
        unchanged = sum(1 for r in report if r["action"] == "unchanged")
        # A run where every item short-circuited on its fingerprint wrote
        # nothing. Appending a log line would be the only diff it produced,
        # which is exactly the churn the fingerprint exists to prevent.
        # `refused` still logs -- a blocked write is worth a record.
        if any(r["action"] != "unchanged" for r in report):
            append_log(
                bundle,
                f"Materialize: {created} created, {updated} updated, "
                f"{skipped} skipped, {unchanged} unchanged",
            )

    if args.json:
        print(json.dumps({"bundle": str(bundle), "results": report}, indent=2))
    else:
        print(f"Bundle: {bundle}")
        counts = {"created": 0, "updated": 0, "skipped": 0, "unchanged": 0, "refused": 0}
        for r in report:
            counts[r["action"]] = counts.get(r["action"], 0) + 1
            print(f"  [{r['action']:9}] {r['type']:14} {r['path']}")
        # `unchanged` = short-circuited on fingerprint, never rendered.
        # `skipped`   = rendered, compared, found identical (or truth_state barrier).
        # The split is what lets CI prove incremental materialize actually works.
        print(
            f"Summary: {counts.get('created', 0)} created, "
            f"{counts.get('updated', 0)} updated, {counts.get('skipped', 0)} skipped, "
            f"{counts.get('unchanged', 0)} unchanged"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
