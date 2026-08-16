#!/usr/bin/env python3
"""Normalize meeting transcripts (plain, Fireflies, Otter, Granola-ish JSON) into notes.

Outputs structured markdown suitable for pkc_capture meeting. Always scrubs secrets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import scrub_text, slugify, utc_now  # noqa: E402


def detect_format(raw: str) -> str:
    s = raw.strip()
    if s.startswith("{") or s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, dict):
                if "sentences" in data or "transcript_json" in data or data.get("app") == "fireflies":
                    return "fireflies"
                if "otters" in data or data.get("provider") == "otter" or "speech" in data:
                    return "otter"
                if "granola" in str(data.get("source", "")).lower() or "panels" in data:
                    return "granola"
                if "segments" in data or "utterances" in data:
                    return "generic_json"
            return "generic_json"
        except json.JSONDecodeError:
            pass
    # speaker labels like "Alice 00:12" or "Alice:"
    if re.search(r"^(?:\[[\d:]+\]\s*)?[A-Z][\w.-]{1,20}:\s+", s, re.M):
        return "speaker_lines"
    return "plain"


def normalize(raw: str, *, title: str | None = None, date: str | None = None) -> dict[str, Any]:
    fmt = detect_format(raw)
    clean, redactions = scrub_text(raw)
    if fmt == "fireflies":
        notes, meta = _from_fireflies(clean)
    elif fmt == "otter":
        notes, meta = _from_otter(clean)
    elif fmt == "granola":
        notes, meta = _from_granola(clean)
    elif fmt == "generic_json":
        notes, meta = _from_generic_json(clean)
    elif fmt == "speaker_lines":
        notes, meta = _from_speaker_lines(clean)
    else:
        notes, meta = clean.strip(), {}

    # extract action-like lines
    actions = []
    for line in notes.splitlines():
        m = re.match(r"^[-*]\s+(.*)", line.strip())
        if m and re.search(r"\b(TODO|action|owner:|will)\b", m.group(1), re.I):
            actions.append(m.group(1).strip())

    attendees = meta.get("attendees") or _guess_attendees(notes)
    return {
        "format": fmt,
        "title": title or meta.get("title") or "Captured meeting",
        "date": date or meta.get("date") or utc_now()[:10],
        "attendees": attendees,
        "notes": notes.strip(),
        "actions": actions,
        "redactions": redactions,
    }


def _from_fireflies(raw: str) -> tuple[str, dict[str, Any]]:
    data = json.loads(raw)
    title = data.get("title") or data.get("meeting_title") or "Fireflies meeting"
    date = (data.get("date") or data.get("start_time") or "")[:10] or None
    attendees = []
    for a in data.get("meeting_attendees") or data.get("attendees") or []:
        if isinstance(a, dict):
            attendees.append(a.get("name") or a.get("displayName") or a.get("email") or "unknown")
        else:
            attendees.append(str(a))
    lines = []
    sentences = data.get("sentences") or data.get("transcript") or []
    if isinstance(sentences, str):
        lines.append(sentences)
    else:
        for s in sentences:
            if isinstance(s, dict):
                sp = s.get("speaker_name") or s.get("speaker") or "?"
                text = s.get("text") or s.get("sentence") or ""
                lines.append(f"- **{sp}**: {text}")
            else:
                lines.append(f"- {s}")
    summary = data.get("summary") or data.get("short_summary")
    body = ""
    if summary:
        body += f"## Summary\n\n{summary}\n\n"
    body += "## Transcript\n\n" + "\n".join(lines)
    return body, {"title": title, "date": date, "attendees": attendees}


def _from_otter(raw: str) -> tuple[str, dict[str, Any]]:
    data = json.loads(raw)
    title = data.get("title") or "Otter meeting"
    lines = []
    for u in data.get("speech") or data.get("transcripts") or data.get("utterances") or []:
        if isinstance(u, dict):
            sp = u.get("speaker") or u.get("speaker_id") or "?"
            lines.append(f"- **{sp}**: {u.get('text') or u.get('transcript') or ''}")
    return "## Transcript\n\n" + "\n".join(lines), {"title": title, "attendees": []}


def _from_granola(raw: str) -> tuple[str, dict[str, Any]]:
    data = json.loads(raw)
    title = data.get("title") or "Granola meeting"
    notes = data.get("notes") or data.get("markdown") or data.get("summary") or ""
    if not notes and isinstance(data.get("panels"), list):
        chunks = []
        for p in data["panels"]:
            if isinstance(p, dict):
                chunks.append(p.get("content") or p.get("text") or "")
        notes = "\n\n".join(chunks)
    return str(notes), {"title": title, "attendees": data.get("attendees") or []}


def _from_generic_json(raw: str) -> tuple[str, dict[str, Any]]:
    data = json.loads(raw)
    if isinstance(data, list):
        lines = []
        for u in data:
            if isinstance(u, dict):
                lines.append(f"- **{u.get('speaker', '?')}**: {u.get('text', '')}")
            else:
                lines.append(f"- {u}")
        return "## Transcript\n\n" + "\n".join(lines), {}
    notes = data.get("notes") or data.get("text") or data.get("transcript") or json.dumps(data, indent=2)
    return str(notes), {
        "title": data.get("title"),
        "date": (str(data.get("date") or "")[:10] or None),
        "attendees": data.get("attendees") or [],
    }


def _from_speaker_lines(raw: str) -> tuple[str, dict[str, Any]]:
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(?:\[[\d:]+\]\s*)?([A-Z][\w.-]{1,20}):\s+(.*)$", line)
        if m:
            lines.append(f"- **{m.group(1)}**: {m.group(2)}")
        else:
            lines.append(line)
    return "## Transcript\n\n" + "\n".join(lines), {"attendees": _guess_attendees("\n".join(lines))}


def _guess_attendees(notes: str) -> list[str]:
    names = re.findall(r"\*\*([A-Z][\w.-]{1,20})\*\*:", notes)
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen[:20]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize transcripts for PKC meeting capture")
    parser.add_argument("--file", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--capture", action="store_true", help="Also write via pkc_capture meeting")
    parser.add_argument("--author", default="")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    args = parser.parse_args(argv)

    raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    result = normalize(raw, title=args.title, date=args.date)

    if args.capture:
        from pkc_capture import capture_meeting
        from pkc_common import ensure_bundle, resolve_author, resolve_knowledge_root

        bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
        ensure_bundle(bundle)
        author = resolve_author(args.author)
        notes = result["notes"]
        if result["actions"]:
            notes += "\n\n## Action items\n\n" + "\n".join(f"- {a}" for a in result["actions"])
        written = capture_meeting(
            bundle,
            author=author,
            title=result["title"],
            date=result["date"],
            attendees=[str(a) for a in result["attendees"]],
            notes=notes,
        )
        for rel, action in written:
            print(f"[{action}] {rel}")
        if result["redactions"]:
            print(f"redacted: {', '.join(result['redactions'])}", file=sys.stderr)
        return 0

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"# {result['title']}")
        print(f"\nDate: {result['date']}")
        print(f"Format: {result['format']}")
        print(f"Attendees: {', '.join(result['attendees']) or '_'}")
        if result["redactions"]:
            print(f"Redacted: {', '.join(result['redactions'])}")
        print()
        print(result["notes"])
        if result["actions"]:
            print("\n## Action items\n")
            for a in result["actions"]:
                print(f"- {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
