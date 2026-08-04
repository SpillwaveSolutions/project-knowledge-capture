#!/usr/bin/env python3
"""Weekly / daily knowledge digest + needs-verification queue.

Surfaces recent captures, open questions, unvalidated assumptions, stale items,
and decision activity for one-screen ADHD-friendly briefs.

Usage:
  python3 scripts/pkc_digest.py --bundle sample-knowledge
  python3 scripts/pkc_digest.py --days 7 --write sample-knowledge/packs/digest-weekly.md
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    iter_concepts,
    parse_frontmatter,
    parse_iso_date,
    resolve_knowledge_root,
    utc_now,
)
from pkc_doctor import doctor  # noqa: E402


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def collect(
    bundle: Path,
    *,
    days: int = 7,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = _aware(now) or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    health = doctor(bundle, stale_days=max(days, 30), now=now)

    recent: list[dict[str, Any]] = []
    verify: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    by_type: dict[str, int] = {}

    for path in iter_concepts(bundle):
        rel = "/" + path.relative_to(bundle).as_posix()
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        ctype = str(fm.get("type") or "Unknown")
        by_type[ctype] = by_type.get(ctype, 0) + 1
        title = fm.get("title") or path.stem
        ts = _aware(parse_iso_date(fm.get("timestamp") or fm.get("date")))
        item = {
            "path": rel,
            "type": ctype,
            "title": title,
            "status": fm.get("status"),
            "timestamp": fm.get("timestamp") or fm.get("date"),
            "verified": fm.get("verified"),
        }

        if ts and ts >= since:
            recent.append(item)
            if ctype == "DecisionRecord":
                decisions.append(item)

        if ctype == "Question" and str(fm.get("status") or "open").lower() in (
            "open",
            "active",
            "unanswered",
            "blocking",
        ):
            questions.append(item)

        if ctype == "Assumption" and fm.get("verified") is not True:
            if str(fm.get("status") or "unvalidated").lower() in (
                "unvalidated",
                "proposed",
                "active",
            ):
                assumptions.append(item)

        # needs verification queue
        needs = False
        if fm.get("verified") is False and ctype in (
            "Discovery",
            "Assumption",
            "DecisionRecord",
            "Meeting",
        ):
            needs = True
        if fm.get("stale_after"):
            sa = _aware(parse_iso_date(fm.get("stale_after")))
            if sa and sa < now:
                needs = True
        if needs:
            verify.append(item)

    def sort_ts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            items,
            key=lambda x: x.get("timestamp") or "",
            reverse=True,
        )

    return {
        "bundle": str(bundle),
        "generated": utc_now(),
        "days": days,
        "since": since.date().isoformat(),
        "counts": by_type,
        "recent": sort_ts(recent)[:40],
        "decisions": sort_ts(decisions)[:20],
        "open_questions": questions[:20],
        "unvalidated_assumptions": assumptions[:20],
        "needs_verification": verify[:30],
        "doctor": {
            "errors": health["by_severity"].get("error", 0),
            "warnings": health["by_severity"].get("warn", 0),
            "info": health["by_severity"].get("info", 0),
            "top_issues": health["issues"][:15],
        },
    }


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "---",
        "type: ContextPack",
        f"title: Knowledge digest ({data['days']}d)",
        f"description: Weekly/daily knowledge brief since {data['since']}",
        f"timestamp: {data['generated']}",
        "generated: true",
        "tags: [digest, pkc, brief]",
        "---",
        "",
        f"# Knowledge digest — last {data['days']} days",
        "",
        f"- Bundle: `{data['bundle']}`",
        f"- Since: **{data['since']}**",
        f"- Generated: {data['generated']}",
        f"- Health: {data['doctor']['errors']} errors · {data['doctor']['warnings']} warnings · {data['doctor']['info']} info",
        "",
        "## Inventory",
        "",
    ]
    for t, n in sorted(data["counts"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{t}`: {n}")

    lines += ["", "## Recent captures", ""]
    if not data["recent"]:
        lines.append("_Nothing new in this window._")
    else:
        for r in data["recent"]:
            lines.append(f"- [{r['title']}]({r['path']}) · `{r['type']}` · {r.get('timestamp') or '?'}")

    lines += ["", "## Decisions in window", ""]
    if not data["decisions"]:
        lines.append("_No decisions._")
    else:
        for r in data["decisions"]:
            lines.append(f"- [{r['title']}]({r['path']}) · {r.get('status') or '?'}")

    lines += ["", "## Open questions", ""]
    if not data["open_questions"]:
        lines.append("_None open._")
    else:
        for r in data["open_questions"]:
            lines.append(f"- [{r['title']}]({r['path']}) · `{r.get('status')}`")

    lines += ["", "## Unvalidated assumptions", ""]
    if not data["unvalidated_assumptions"]:
        lines.append("_None._")
    else:
        for r in data["unvalidated_assumptions"]:
            lines.append(f"- [{r['title']}]({r['path']})")

    lines += ["", "## Needs verification", ""]
    if not data["needs_verification"]:
        lines.append("_Queue empty._")
    else:
        for r in data["needs_verification"]:
            lines.append(f"- [{r['title']}]({r['path']}) · `{r['type']}`")

    lines += ["", "## Doctor highlights", ""]
    if not data["doctor"]["top_issues"]:
        lines.append("_All clear._")
    else:
        for i in data["doctor"]["top_issues"]:
            lines.append(f"- **{i['severity']}/{i['kind']}**: {i['message']}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC knowledge digest")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--write", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    data = collect(bundle, days=args.days)
    md = render_markdown(data)

    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}")

    if args.json:
        import json

        print(json.dumps(data, indent=2))
    elif not args.write:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
