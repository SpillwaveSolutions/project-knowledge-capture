#!/usr/bin/env python3
"""Extract action items from a Meeting concept and optionally bridge to WikiTicket.

Default is dry-run (print proposed work items). Never hand-edits .work/*.jsonl.
When --apply is set, shells out to bin/worklog if present.

Usage:
  python3 scripts/pkc_action_items.py meetings/2026-08-03-auth-design.md --bundle sample-knowledge
  python3 scripts/pkc_action_items.py meetings/….md --apply --repo .
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    parse_frontmatter,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    slugify,
    utc_now,
    write_concept,
)

ACTION_HEADER = re.compile(r"^##\s+Action items\s*$", re.I | re.M)
BULLET = re.compile(r"^[-*]\s+(.+)$")
OWNER = re.compile(r"\b(?:owner|@)\s*[:=]?\s*([A-Za-z][\w.-]*)", re.I)
DUE = re.compile(r"\b(?:due|by)\s*[:=]?\s*(\d{4}-\d{2}-\d{2}|\w+\s+\d{1,2})", re.I)


def extract_action_items(body: str) -> list[dict[str, Any]]:
    """Parse ## Action items section bullets."""
    m = ACTION_HEADER.search(body)
    if not m:
        # fallback: lines starting with action-like verbs
        items = []
        for line in body.splitlines():
            bm = BULLET.match(line.strip())
            if not bm:
                continue
            text = bm.group(1).strip()
            if re.match(
                r"^(implement|add|create|write|document|fix|build|ship|investigate)\b",
                text,
                re.I,
            ):
                items.append(_parse_item(text))
        return items

    section = body[m.end() :]
    # stop at next ## header
    nxt = re.search(r"^##\s+", section, re.M)
    if nxt:
        section = section[: nxt.start()]

    items = []
    for line in section.splitlines():
        bm = BULLET.match(line.strip())
        if bm:
            items.append(_parse_item(bm.group(1).strip()))
    return items


def _parse_item(text: str) -> dict[str, Any]:
    owner_m = OWNER.search(text)
    due_m = DUE.search(text)
    # strip parenthetical owner notes for title cleanliness
    title = re.sub(r"\s*\(owner:\s*[^)]+\)\s*", " ", text, flags=re.I).strip()
    title = re.sub(r"\s+", " ", title)
    return {
        "title": title,
        "owner": owner_m.group(1) if owner_m else None,
        "due": due_m.group(1) if due_m else None,
        "raw": text,
    }


def propose_worklog_commands(items: list[dict[str, Any]], *, parent: str | None = None) -> list[str]:
    cmds = []
    for it in items:
        parts = ["bin/worklog", "add", "--level", "task", "--kind", "feature"]
        if parent:
            parts += ["--parent", parent]
        # quote title safely for shell display
        title = it["title"].replace('"', '\\"')
        parts += [f'--title "{title}"']
        if it.get("owner"):
            parts += [f'--assignee "{it["owner"]}"']
        cmds.append(" ".join(parts))
    return cmds


def emit_ticketlinks(
    bundle: Path,
    items: list[dict[str, Any]],
    *,
    meeting_rel: str,
    dry_run: bool = True,
) -> list[tuple[str, str]]:
    results = []
    for it in items:
        # synthetic placeholder ULID-like id for dry-run demo only when applying without worklog
        slug = slugify(f"action-{it['title']}")
        rel = path_for_type("TicketLink", slug)
        fm = {
            "type": "TicketLink",
            "title": it["title"],
            "description": f"Action item from {meeting_rel}",
            "tags": ["ticket", "action-item", "from-meeting"],
            "timestamp": utc_now(),
            "status": "open",
            "verified": False,
            "generated": True,
            "stable_timestamp": True,
            "truth_state": "current",
            "wiki_key": f"action-{slug}",
            "links": [
                {"target": meeting_rel if meeting_rel.startswith("/") else f"/{meeting_rel}", "rel": "originates_from"},
            ],
        }
        if it.get("owner"):
            fm["owners"] = [it["owner"]]
        body = (
            f"# {it['title']}\n\n"
            f"Action item extracted from [{Path(meeting_rel).stem}]({meeting_rel if meeting_rel.startswith('/') else '/' + meeting_rel}).\n\n"
            f"- Raw: {it['raw']}\n"
        )
        if dry_run:
            results.append((rel, "proposed"))
        else:
            _, action = write_concept(bundle, rel, fm, body)
            results.append((rel, action))
    if not dry_run and results:
        refresh_catalog_index(bundle, "tickets")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract meeting action items → WikiTicket bridge")
    parser.add_argument("meeting", help="Meeting concept path")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--apply", action="store_true", help="Create TicketLinks (and worklog if available)")
    parser.add_argument("--worklog", action="store_true", help="Also run bin/worklog add when applying")
    parser.add_argument("--parent", default=None, help="Parent worklog ULID for tasks")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    bundle = resolve_knowledge_root(repo, args.bundle)
    path = Path(args.meeting)
    if not path.is_file():
        path = bundle / args.meeting.lstrip("/")
    if not path.is_file():
        print(f"error: meeting not found: {args.meeting}", file=sys.stderr)
        return 1

    fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if fm.get("type") and fm.get("type") != "Meeting":
        print(f"warning: type is {fm.get('type')}, expected Meeting", file=sys.stderr)

    items = extract_action_items(body)
    if not items:
        print("No action items found.")
        return 0

    print(f"Found {len(items)} action item(s) in {path.name}:\n")
    for i, it in enumerate(items, 1):
        extra = []
        if it.get("owner"):
            extra.append(f"owner={it['owner']}")
        if it.get("due"):
            extra.append(f"due={it['due']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        print(f"  {i}. {it['title']}{suffix}")

    print("\nProposed worklog commands (not run unless --apply --worklog):\n")
    for cmd in propose_worklog_commands(items, parent=args.parent):
        print(f"  {cmd}")

    meeting_rel = "/" + path.resolve().relative_to(bundle.resolve()).as_posix()
    results = emit_ticketlinks(
        bundle, items, meeting_rel=meeting_rel, dry_run=not args.apply
    )
    print("\nTicketLinks:")
    for rel, action in results:
        print(f"  [{action}] {rel}")

    if args.apply and args.worklog:
        worklog = repo / "bin" / "worklog"
        if not worklog.is_file():
            print("warning: bin/worklog not found — skipped worklog writes", file=sys.stderr)
        else:
            for it in items:
                cmd = [
                    str(worklog),
                    "add",
                    "--level",
                    "task",
                    "--kind",
                    "feature",
                    "--title",
                    it["title"],
                ]
                if args.parent:
                    cmd += ["--parent", args.parent]
                print(f"\n$ {' '.join(cmd)}")
                subprocess.run(cmd, cwd=str(repo), check=False)

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write TicketLinks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
