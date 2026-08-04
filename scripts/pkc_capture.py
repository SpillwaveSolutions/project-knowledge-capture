#!/usr/bin/env python3
"""Deterministic capture helpers for meetings, experiments, discoveries, decisions.

These helpers write skeleton OKF files; agents still extract structure from free text.
Useful for idempotent path selection and golden tests.

Usage:
  python3 scripts/pkc_capture.py meeting --title "Auth design" --date 2026-08-03 \\
      --attendees rick,alice --notes-file notes.md --bundle knowledge
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    append_log,
    ensure_bundle,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    slugify,
    utc_now,
    write_concept,
)


def capture_meeting(
    bundle: Path,
    *,
    title: str,
    date: str,
    attendees: list[str],
    notes: str,
    decisions: list[str] | None = None,
    wiki_key: str | None = None,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    slug = slugify(f"{date}-{title}")
    rel = path_for_type("Meeting", slug)
    decision_links = []
    decision_paths: list[str] = []
    for d in decisions or []:
        dslug = slugify(d)
        drel = path_for_type("DecisionRecord", dslug)
        decision_paths.append(drel)
        decision_links.append({"target": f"/{drel}", "rel": "decides"})
        dfm = {
            "type": "DecisionRecord",
            "title": d,
            "description": f"Decision from meeting: {title}",
            "status": "accepted",
            "tags": ["decision", "adr", "from-meeting"],
            "timestamp": utc_now(),
            "verified": False,
            "generated": True,
            "stable_timestamp": True,
            "wiki_key": f"adr-{dslug}",
            "truth_state": "current",
            "links": [
                {"target": f"/{rel}", "rel": "originates_from"},
            ],
        }
        dbody = (
            f"# {d}\n\n## Context\n\nCaptured from meeting [{title}](/{rel}).\n\n"
            f"## Decision\n\n{d}\n\n## Consequences\n\n_TBD — refine after capture._\n"
        )
        _, action = write_concept(bundle, drel, dfm, dbody)
        results.append((drel, action))

    fm: dict[str, Any] = {
        "type": "Meeting",
        "title": title,
        "description": notes.strip().splitlines()[0][:160] if notes.strip() else title,
        "date": date,
        "attendees": attendees,
        "tags": ["meeting"],
        "timestamp": utc_now(),
        "status": "active",
        "verified": True,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": wiki_key or f"meeting-{slug}",
        "truth_state": "current",
    }
    if decision_links:
        fm["links"] = decision_links
    body = f"# {title}\n\n## Meta\n\n- Date: {date}\n- Attendees: {', '.join(attendees) or '_none_'}\n\n"
    body += "## Notes\n\n" + (notes.strip() or "_No notes provided._") + "\n"
    if decision_paths:
        body += "\n## Decisions extracted\n\n"
        for dp in decision_paths:
            body += f"- [{Path(dp).stem}](/{dp})\n"
    _, action = write_concept(bundle, rel, fm, body)
    results.insert(0, (rel, action))
    refresh_catalog_index(bundle, "meetings")
    if decision_paths:
        refresh_catalog_index(bundle, "decisions")
    append_log(bundle, f"Captured meeting: {title}")
    return results


def capture_experiment(
    bundle: Path,
    *,
    title: str,
    hypothesis: str,
    result: str,
    conclusion: str,
    informs: list[str] | None = None,
) -> list[tuple[str, str]]:
    slug = slugify(title)
    rel = path_for_type("Experiment", slug)
    links = []
    for t in informs or []:
        target = t if t.startswith("/") else f"/features/{slugify(t)}.md"
        links.append({"target": target, "rel": "informs"})
    fm: dict[str, Any] = {
        "type": "Experiment",
        "title": title,
        "description": conclusion[:200] if conclusion else hypothesis[:200],
        "hypothesis": hypothesis,
        "result": result,
        "conclusion": conclusion,
        "tags": ["experiment"],
        "timestamp": utc_now(),
        "status": "completed",
        "verified": True,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"experiment-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Hypothesis

{hypothesis}

## Method & results

{result}

## Conclusion

{conclusion}
"""
    if links:
        body += "\n## Informs\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']})\n"
    _, action = write_concept(bundle, rel, fm, body)
    refresh_catalog_index(bundle, "experiments")
    append_log(bundle, f"Captured experiment: {title}")
    return [(rel, action)]


def capture_discovery(
    bundle: Path,
    *,
    title: str,
    source: str,
    notes: str,
    confidence: str = "medium",
    links_to: list[str] | None = None,
) -> list[tuple[str, str]]:
    slug = slugify(title)
    rel = path_for_type("Discovery", slug)
    links = []
    for t in links_to or []:
        target = t if t.startswith("/") else f"/features/{slugify(t)}.md"
        links.append({"target": target, "rel": "informs"})
    fm: dict[str, Any] = {
        "type": "Discovery",
        "title": title,
        "description": notes.strip().splitlines()[0][:160] if notes.strip() else title,
        "source": source,
        "confidence": confidence,
        "tags": ["discovery", "research"],
        "timestamp": utc_now(),
        "status": "active",
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"discovery-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Source

{source}

## Confidence

`{confidence}`

## Findings

{notes.strip() or '_No findings provided._'}
"""
    if links:
        body += "\n## Related\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']}) (`informs`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    refresh_catalog_index(bundle, "discoveries")
    append_log(bundle, f"Captured discovery: {title}")
    return [(rel, action)]


def capture_decision(
    bundle: Path,
    *,
    title: str,
    context: str,
    decision: str,
    consequences: str,
    status: str = "accepted",
    originates_from: str | None = None,
    decides: list[str] | None = None,
) -> list[tuple[str, str]]:
    slug = slugify(title)
    rel = path_for_type("DecisionRecord", slug)
    links = []
    if originates_from:
        t = originates_from if originates_from.startswith("/") else f"/{originates_from}"
        links.append({"target": t, "rel": "originates_from"})
    for d in decides or []:
        t = d if d.startswith("/") else f"/features/{slugify(d)}.md"
        links.append({"target": t, "rel": "decides"})
    fm: dict[str, Any] = {
        "type": "DecisionRecord",
        "title": title,
        "description": decision[:200],
        "status": status,
        "tags": ["decision", "adr"],
        "timestamp": utc_now(),
        "verified": True,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"adr-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Context

{context}

## Decision

{decision}

## Consequences

{consequences}
"""
    if links:
        body += "\n## Related\n\n"
        for link in links:
            label = Path(link["target"]).stem
            body += f"- [{label}]({link['target']}) (`{link['rel']}`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    refresh_catalog_index(bundle, "decisions")
    append_log(bundle, f"Captured decision: {title}")
    return [(rel, action)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC capture helpers")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    sub = parser.add_subparsers(dest="kind", required=True)

    m = sub.add_parser("meeting")
    m.add_argument("--title", required=True)
    m.add_argument("--date", required=True)
    m.add_argument("--attendees", default="")
    m.add_argument("--notes", default="")
    m.add_argument("--notes-file", default=None)
    m.add_argument("--decision", action="append", default=[])

    e = sub.add_parser("experiment")
    e.add_argument("--title", required=True)
    e.add_argument("--hypothesis", required=True)
    e.add_argument("--result", required=True)
    e.add_argument("--conclusion", required=True)
    e.add_argument("--informs", action="append", default=[])

    d = sub.add_parser("discovery")
    d.add_argument("--title", required=True)
    d.add_argument("--source", default="unknown")
    d.add_argument("--notes", default="")
    d.add_argument("--notes-file", default=None)
    d.add_argument("--confidence", default="medium")
    d.add_argument("--links-to", action="append", default=[])

    r = sub.add_parser("decision")
    r.add_argument("--title", required=True)
    r.add_argument("--context", default="")
    r.add_argument("--decision", required=True)
    r.add_argument("--consequences", default="")
    r.add_argument("--status", default="accepted")
    r.add_argument("--originates-from", default=None)
    r.add_argument("--decides", action="append", default=[])

    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    bundle = resolve_knowledge_root(repo, args.bundle)
    ensure_bundle(bundle)

    if args.kind == "meeting":
        notes = args.notes
        if args.notes_file:
            notes = Path(args.notes_file).read_text(encoding="utf-8")
        results = capture_meeting(
            bundle,
            title=args.title,
            date=args.date,
            attendees=[a.strip() for a in args.attendees.split(",") if a.strip()],
            notes=notes,
            decisions=args.decision,
        )
    elif args.kind == "experiment":
        results = capture_experiment(
            bundle,
            title=args.title,
            hypothesis=args.hypothesis,
            result=args.result,
            conclusion=args.conclusion,
            informs=args.informs,
        )
    elif args.kind == "discovery":
        notes = args.notes
        if args.notes_file:
            notes = Path(args.notes_file).read_text(encoding="utf-8")
        results = capture_discovery(
            bundle,
            title=args.title,
            source=args.source,
            notes=notes,
            confidence=args.confidence,
            links_to=args.links_to,
        )
    else:
        results = capture_decision(
            bundle,
            title=args.title,
            context=args.context,
            decision=args.decision,
            consequences=args.consequences,
            status=args.status,
            originates_from=args.originates_from,
            decides=args.decides,
        )

    for rel, action in results:
        print(f"[{action}] {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
