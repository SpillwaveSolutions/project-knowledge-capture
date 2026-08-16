#!/usr/bin/env python3
"""Capture Slack / Discord / chat thread paste as Meeting or Discovery.

Detects timestamps, @mentions, and thread structure. Always scrubs secrets/PII.

Usage:
  python3 scripts/pkc_thread.py --file thread.txt --as meeting --title "Auth thread"
  cat paste.txt | python3 scripts/pkc_thread.py --as discovery --title "Customer feedback"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_capture import capture_discovery, capture_meeting  # noqa: E402
from pkc_common import ensure_bundle, resolve_author, resolve_knowledge_root, scrub_text, utc_now  # noqa: E402

# Slack-ish: [10:32 AM] Alice: message   or Alice  [10:32]
# Discord-ish: Alice — Today at 10:32 AM
SLACK_LINE = re.compile(
    r"^(?:\[(?P<ts1>[^\]]+)\]\s*)?(?P<who>[A-Za-z][\w .'-]{0,40}?)(?:\s*[—-]\s*|\s+)(?:Today at |Yesterday at )?(?P<ts2>\d{1,2}:\d{2}(?:\s*[AP]M)?)?\s*:?\s*(?P<body>.+)$",
    re.I,
)
MENTION = re.compile(r"@([\w.-]+)")


def normalize_thread(raw: str, *, title: str | None = None) -> dict[str, Any]:
    clean, redactions = scrub_text(raw)
    lines_out: list[str] = []
    speakers: list[str] = []
    for line in clean.splitlines():
        s = line.strip()
        if not s:
            continue
        m = SLACK_LINE.match(s)
        if m:
            who = (m.group("who") or "?").strip()
            body = (m.group("body") or "").strip()
            ts = m.group("ts1") or m.group("ts2")
            if who and who not in speakers and len(who) < 40:
                speakers.append(who)
            prefix = f"**{who}**"
            if ts:
                prefix += f" _{ts}_"
            lines_out.append(f"- {prefix}: {body}")
        else:
            # bare message
            lines_out.append(s)

    mentions = sorted(set(MENTION.findall(clean)))
    for m in mentions:
        if m not in speakers:
            speakers.append(m)

    notes = "## Thread\n\n" + ("\n".join(lines_out) if lines_out else clean.strip())
    if mentions:
        notes += "\n\n## Mentions\n\n" + ", ".join(f"@{m}" for m in mentions)

    return {
        "title": title or "Chat thread",
        "date": utc_now()[:10],
        "attendees": speakers[:20],
        "notes": notes,
        "redactions": redactions,
        "format": "thread",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture chat thread paste into PKC")
    parser.add_argument("--file", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--as", dest="kind", choices=["meeting", "discovery"], default="meeting")
    parser.add_argument("--source", default="slack/discord thread")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--capture", action="store_true", help="Write concept (default: print only)")
    parser.add_argument("--author", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    result = normalize_thread(raw, title=args.title)

    if args.capture:
        bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
        ensure_bundle(bundle)
        author = resolve_author(args.author)
        if args.kind == "meeting":
            written = capture_meeting(
                bundle,
                author=author,
                title=result["title"],
                date=result["date"],
                attendees=result["attendees"],
                notes=result["notes"],
            )
        else:
            written = capture_discovery(
                bundle,
                author=author,
                title=result["title"],
                source=args.source,
                notes=result["notes"],
                confidence="medium",
            )
        for rel, action in written:
            print(f"[{action}] {rel}")
        if result["redactions"]:
            print(f"redacted: {', '.join(result['redactions'])}", file=sys.stderr)
        return 0

    if args.json:
        import json

        print(json.dumps(result, indent=2))
    else:
        print(f"# {result['title']}\n")
        print(f"Date: {result['date']}")
        print(f"Attendees: {', '.join(result['attendees']) or '_'}")
        if result["redactions"]:
            print(f"Redacted: {', '.join(result['redactions'])}")
        print()
        print(result["notes"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
