#!/usr/bin/env python3
"""Deterministic capture helpers for meetings, experiments, discoveries, decisions,
assumptions, and questions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    add_typed_link,
    append_log,
    concept_ref,
    ensure_bundle,
    path_for_type,
    refresh_catalog_index,
    resolve_knowledge_root,
    scrub_text,
    slugify,
    utc_now,
    write_concept,
)


def _scrub(notes: str) -> str:
    clean, _ = scrub_text(notes)
    return clean


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
    notes = _scrub(notes)
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
            "links": [{"target": f"/{rel}", "rel": "originates_from"}],
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
        target = concept_ref(t, "features")
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
    stale_after: str | None = None,
) -> list[tuple[str, str]]:
    notes = _scrub(notes)
    slug = slugify(title)
    rel = path_for_type("Discovery", slug)
    links = []
    for t in links_to or []:
        target = concept_ref(t, "features")
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
    if stale_after:
        fm["stale_after"] = stale_after
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
        t = concept_ref(originates_from, "meetings")
        links.append({"target": t, "rel": "originates_from"})
    for d in decides or []:
        t = concept_ref(d, "features")
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


def capture_assumption(
    bundle: Path,
    *,
    title: str,
    statement: str,
    rationale: str = "",
    status: str = "unvalidated",
    assumes_for: list[str] | None = None,
) -> list[tuple[str, str]]:
    slug = slugify(title)
    rel = path_for_type("Assumption", slug)
    links = []
    for t in assumes_for or []:
        target = concept_ref(t, "features")
        links.append({"target": target, "rel": "assumes"})
    fm: dict[str, Any] = {
        "type": "Assumption",
        "title": title,
        "description": statement[:200],
        "status": status,
        "tags": ["assumption"],
        "timestamp": utc_now(),
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"assumption-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Statement

{statement}

## Rationale

{rationale or '_TBD_'}

## Validation path

_What experiment or evidence would validate or invalidate this?_
"""
    if links:
        body += "\n## Applies to\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']}) (`assumes`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    refresh_catalog_index(bundle, "assumptions")
    append_log(bundle, f"Captured assumption: {title}")
    return [(rel, action)]


def capture_risk(
    bundle: Path,
    *,
    title: str,
    statement: str,
    severity: str = "medium",
    exposes: list[str] | None = None,
    mitigated_by: list[str] | None = None,
) -> list[tuple[str, str]]:
    """A Risk names what could go wrong and what holds it back.

    Edge directions are not symmetric and matter:
      Risk     --exposes--> Feature    (the risk threatens it)
      Decision --mitigates--> Risk     (the decision reduces it)

    So `mitigated_by` writes its edge on the *decision*, not here --
    "Risk mitigates Decision" would read backwards.
    """
    slug = slugify(title)
    rel = path_for_type("Risk", slug)
    links = []
    for t in exposes or []:
        target = concept_ref(t, "features")
        links.append({"target": target, "rel": "exposes"})
    fm: dict[str, Any] = {
        "type": "Risk",
        "title": title,
        "description": statement[:200],
        "severity": severity,
        "status": "open",
        "tags": ["risk", severity],
        "timestamp": utc_now(),
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"risk-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Risk

{statement}

## Severity

`{severity}`

## Mitigation

_What reduces the likelihood or blast radius?_
"""
    if links:
        body += "\n## Related\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']}) (`{link['rel']}`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    # The mitigation edge belongs on the decision that mitigates, pointing here.
    for t in mitigated_by or []:
        target = concept_ref(t, "decisions")
        if add_typed_link(bundle / target.lstrip("/"), f"/{rel}", "mitigates") == "error":
            # add_typed_link returns "error" for a missing file. Don't fail the
            # capture -- the graph is often WIP -- but never drop it silently.
            print(f"warning: no mitigation edge written, {target} not found", file=sys.stderr)
    refresh_catalog_index(bundle, "risks")
    append_log(bundle, f"Captured risk: {title}")
    return [(rel, action)]


def capture_acceptance(
    bundle: Path,
    *,
    title: str,
    criterion: str,
    satisfies: str | None = None,
    verified_by: list[str] | None = None,
) -> list[tuple[str, str]]:
    """One atomic, checkable condition for calling a Feature done.

    Deliberately small: one criterion per concept, so each can be checked off
    on its own and `verified_by` points at the specific thing that proves it.

    `satisfies` also writes the inverse edge (Feature --verified_by--> this).
    pack() reads inbound edges, so this is no longer needed for reachability;
    it stays because `verified_by` is a claim the Feature genuinely makes.
    """
    slug = slugify(title)
    rel = path_for_type("Acceptance", slug)
    links = []
    if satisfies:
        target = concept_ref(satisfies, "features")
        links.append({"target": target, "rel": "satisfies"})
    for t in verified_by or []:
        target = concept_ref(t, "code")
        links.append({"target": target, "rel": "verified_by"})
    fm: dict[str, Any] = {
        "type": "Acceptance",
        "title": title,
        "description": criterion[:200],
        "status": "unverified",
        "tags": ["acceptance"],
        "timestamp": utc_now(),
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"acceptance-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Criterion

{criterion}

## How it is verified

_Test, review, or observation that settles this._
"""
    if links:
        body += "\n## Related\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']}) (`{link['rel']}`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    if satisfies:
        target = concept_ref(satisfies, "features")
        if add_typed_link(bundle / target.lstrip("/"), f"/{rel}", "verified_by") == "error":
            print(f"warning: no inverse edge written, {target} not found", file=sys.stderr)
    refresh_catalog_index(bundle, "acceptance")
    append_log(bundle, f"Captured acceptance criterion: {title}")
    return [(rel, action)]


def capture_question(
    bundle: Path,
    *,
    title: str,
    question: str,
    context: str = "",
    status: str = "open",
    blocks: list[str] | None = None,
) -> list[tuple[str, str]]:
    slug = slugify(title)
    rel = path_for_type("Question", slug)
    links = []
    for t in blocks or []:
        target = concept_ref(t, "features")
        links.append({"target": target, "rel": "blocks"})
    fm: dict[str, Any] = {
        "type": "Question",
        "title": title,
        "description": question[:200],
        "status": status,
        "tags": ["question", "open"],
        "timestamp": utc_now(),
        "verified": False,
        "generated": True,
        "stable_timestamp": True,
        "wiki_key": f"question-{slug}",
        "truth_state": "current",
    }
    if links:
        fm["links"] = links
    body = f"""# {title}

## Question

{question}

## Context

{context or '_TBD_'}

## Resolution

_Unanswered — capture a Decision or Discovery when resolved._
"""
    if links:
        body += "\n## Blocks\n\n"
        for link in links:
            body += f"- [{link['target']}]({link['target']}) (`blocks`)\n"
    _, action = write_concept(bundle, rel, fm, body)
    refresh_catalog_index(bundle, "questions")
    append_log(bundle, f"Captured question: {title}")
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
    d.add_argument("--stale-after", default=None)

    r = sub.add_parser("decision")
    r.add_argument("--title", required=True)
    r.add_argument("--context", default="")
    r.add_argument("--decision", required=True)
    r.add_argument("--consequences", default="")
    r.add_argument("--status", default="accepted")
    r.add_argument("--originates-from", default=None)
    r.add_argument("--decides", action="append", default=[])

    a = sub.add_parser("assumption")
    a.add_argument("--title", required=True)
    a.add_argument("--statement", required=True)
    a.add_argument("--rationale", default="")
    a.add_argument("--status", default="unvalidated")
    a.add_argument("--for", dest="assumes_for", action="append", default=[])

    q = sub.add_parser("question")
    q.add_argument("--title", required=True)
    q.add_argument("--question", required=True)
    q.add_argument("--context", default="")
    q.add_argument("--status", default="open")
    q.add_argument("--blocks", action="append", default=[])

    rk = sub.add_parser("risk")
    rk.add_argument("--title", required=True)
    rk.add_argument("--statement", required=True)
    rk.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])
    rk.add_argument("--exposes", action="append", default=[])
    rk.add_argument("--mitigated-by", dest="mitigated_by", action="append", default=[])

    ac = sub.add_parser("acceptance")
    ac.add_argument("--title", required=True)
    ac.add_argument("--criterion", required=True)
    ac.add_argument("--for", dest="satisfies", default=None)
    ac.add_argument("--verified-by", dest="verified_by", action="append", default=[])

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
            attendees=[x.strip() for x in args.attendees.split(",") if x.strip()],
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
            stale_after=args.stale_after,
        )
    elif args.kind == "decision":
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
    elif args.kind == "risk":
        results = capture_risk(
            bundle,
            title=args.title,
            statement=args.statement,
            severity=args.severity,
            exposes=args.exposes,
            mitigated_by=args.mitigated_by,
        )
    elif args.kind == "acceptance":
        results = capture_acceptance(
            bundle,
            title=args.title,
            criterion=args.criterion,
            satisfies=args.satisfies,
            verified_by=args.verified_by,
        )
    elif args.kind == "assumption":
        results = capture_assumption(
            bundle,
            title=args.title,
            statement=args.statement,
            rationale=args.rationale,
            status=args.status,
            assumes_for=args.assumes_for,
        )
    else:
        results = capture_question(
            bundle,
            title=args.title,
            question=args.question,
            context=args.context,
            status=args.status,
            blocks=args.blocks,
        )

    for rel, action in results:
        print(f"[{action}] {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
