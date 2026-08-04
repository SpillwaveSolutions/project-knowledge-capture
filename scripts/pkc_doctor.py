#!/usr/bin/env python3
"""PKC doctor — one-screen health check for a knowledge bundle."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    CATALOGS,
    iter_concepts,
    parse_frontmatter,
    parse_iso_date,
    resolve_knowledge_root,
)

MD_LINK = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def load_graph(bundle: Path) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[tuple[str, str, str]] = []
    for path in iter_concepts(bundle):
        rel = "/" + path.relative_to(bundle).as_posix()
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        nodes[rel] = {
            "path": rel,
            "type": fm.get("type") or "Unknown",
            "title": fm.get("title") or path.stem,
            "status": fm.get("status"),
            "verified": fm.get("verified"),
            "truth_state": fm.get("truth_state"),
            "timestamp": fm.get("timestamp") or fm.get("date"),
            "stale_after": fm.get("stale_after"),
            "fm": fm,
            "body": body,
        }
        links = fm.get("links") or []
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("target"):
                    edges.append((rel, link.get("rel") or "related_to", link["target"]))
        for m in MD_LINK.finditer(body):
            tgt = m.group(2).split("#", 1)[0]
            edges.append((rel, "links_to", tgt))
    return nodes, edges


def doctor(
    bundle: Path,
    *,
    stale_days: int = 90,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = _aware(now) or datetime.now(timezone.utc)
    nodes, edges = load_graph(bundle)
    issues: list[dict[str, str]] = []

    for c in CATALOGS:
        if not (bundle / c).is_dir():
            issues.append(
                {
                    "severity": "info",
                    "kind": "missing_catalog",
                    "message": f"catalog dir missing: {c}/",
                }
            )

    for src, rel, tgt in edges:
        if not tgt.startswith("/"):
            continue
        if not (bundle / tgt.lstrip("/")).is_file():
            issues.append(
                {
                    "severity": "error",
                    "kind": "broken_link",
                    "message": f"{src} -[{rel}]-> {tgt} (missing)",
                }
            )

    out_deg: dict[str, int] = defaultdict(int)
    in_deg: dict[str, int] = defaultdict(int)
    for src, rel, tgt in edges:
        out_deg[src] += 1
        in_deg[tgt] += 1

    for rel, n in nodes.items():
        if out_deg[rel] == 0 and in_deg[rel] == 0:
            issues.append(
                {
                    "severity": "warn",
                    "kind": "orphan",
                    "message": f"{rel} (`{n['type']}`) has no edges",
                }
            )

    decides_to: dict[str, list[str]] = defaultdict(list)
    for src, rel, tgt in edges:
        if rel == "decides" and nodes.get(src, {}).get("type") == "DecisionRecord":
            decides_to[tgt].append(src)

    for rel, n in nodes.items():
        if n["type"] != "Feature":
            continue
        proven: set[str] = set(decides_to.get(rel, []))
        for src, r, tgt in edges:
            if src == rel and nodes.get(tgt, {}).get("type") in (
                "DecisionRecord",
                "Meeting",
                "Experiment",
                "Design",
            ):
                proven.add(tgt)
            if tgt == rel and nodes.get(src, {}).get("type") in (
                "DecisionRecord",
                "Meeting",
                "Experiment",
                "Design",
            ):
                proven.add(src)
        has_decision = any(nodes.get(p, {}).get("type") == "DecisionRecord" for p in proven)
        if not proven:
            issues.append(
                {
                    "severity": "warn",
                    "kind": "thin_feature",
                    "message": f"{rel} has no Meeting/Experiment/Decision/Design links",
                }
            )
        elif not has_decision:
            issues.append(
                {
                    "severity": "info",
                    "kind": "thin_feature",
                    "message": f"{rel} has context but no DecisionRecord",
                }
            )

    feature_decisions: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for src, rel, tgt in edges:
        if rel != "decides":
            continue
        if nodes.get(src, {}).get("type") != "DecisionRecord":
            continue
        if nodes.get(tgt, {}).get("type") != "Feature":
            continue
        status = (nodes[src].get("status") or "accepted").lower()
        if status in ("accepted", "active", "proposed"):
            feature_decisions[tgt].append((src, status))

    for feat, decs in feature_decisions.items():
        accepted = [d for d in decs if d[1] in ("accepted", "active")]
        if len(accepted) > 1:
            paths = ", ".join(d[0] for d in accepted)
            issues.append(
                {
                    "severity": "error",
                    "kind": "decision_conflict",
                    "message": f"{feat} decided by multiple active/accepted decisions: {paths}",
                }
            )

    for rel, n in nodes.items():
        if n["type"] != "Question":
            continue
        status = (n.get("status") or "open").lower()
        if status not in ("open", "active", "unanswered", "blocking"):
            continue
        for src, r, tgt in edges:
            if src == rel and r in ("blocks", "related_to") and nodes.get(tgt, {}).get("type") == "Feature":
                issues.append(
                    {
                        "severity": "warn",
                        "kind": "open_question",
                        "message": f"{rel} blocks {tgt} (status={status})",
                    }
                )

    cutoff = now - timedelta(days=stale_days)
    for rel, n in nodes.items():
        if n["type"] not in ("Discovery", "Assumption", "Experiment"):
            continue
        sa = _aware(parse_iso_date(n.get("stale_after")))
        ts = _aware(parse_iso_date(n.get("timestamp")))
        if sa and sa < now:
            issues.append(
                {
                    "severity": "warn",
                    "kind": "stale",
                    "message": f"{rel} past stale_after {n.get('stale_after')}",
                }
            )
        elif ts and ts < cutoff:
            if n.get("verified") is not True:
                issues.append(
                    {
                        "severity": "warn",
                        "kind": "stale",
                        "message": f"{rel} older than {stale_days}d and not verified",
                    }
                )
        if n["type"] == "Assumption" and n.get("verified") is not True:
            status = (n.get("status") or "proposed").lower()
            if status in ("proposed", "active", "unvalidated"):
                issues.append(
                    {
                        "severity": "info",
                        "kind": "unvalidated_assumption",
                        "message": f"{rel} is unvalidated (promote/validate when proven)",
                    }
                )

    by_kind: dict[str, int] = defaultdict(int)
    by_sev: dict[str, int] = defaultdict(int)
    for i in issues:
        by_kind[i["kind"]] += 1
        by_sev[i["severity"]] += 1

    return {
        "bundle": str(bundle),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "issues": issues,
        "by_kind": dict(by_kind),
        "by_severity": dict(by_sev),
        "ok": by_sev.get("error", 0) == 0,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# PKC doctor — {result['bundle']}",
        "",
        f"- Nodes: {result['node_count']}",
        f"- Edges: {result['edge_count']}",
        f"- Errors: {result['by_severity'].get('error', 0)}",
        f"- Warnings: {result['by_severity'].get('warn', 0)}",
        f"- Info: {result['by_severity'].get('info', 0)}",
        "",
    ]
    if not result["issues"]:
        lines.append("All clear — no issues found.")
        return "\n".join(lines) + "\n"

    order = {"error": 0, "warn": 1, "info": 2}
    sorted_issues = sorted(result["issues"], key=lambda i: (order.get(i["severity"], 9), i["kind"]))
    current = None
    for i in sorted_issues:
        if i["severity"] != current:
            current = i["severity"]
            lines.append(f"## {current.upper()}")
            lines.append("")
        lines.append(f"- **{i['kind']}**: {i['message']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC knowledge bundle doctor")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--stale-days", type=int, default=90)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    if not bundle.is_dir():
        print(f"error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    result = doctor(bundle, stale_days=args.stale_days)
    if args.json:
        import json

        print(json.dumps(result, indent=2))
    else:
        print(render_report(result))

    if args.strict and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
