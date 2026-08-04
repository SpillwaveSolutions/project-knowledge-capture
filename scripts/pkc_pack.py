#!/usr/bin/env python3
"""Build a progressive-disclosure context pack around a concept.

Walks typed frontmatter links and absolute Markdown body links up to N hops.
Does not require okf-plugin (works standalone; prefer okf-graph.py pack when available).

Usage:
  python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --hops 2
  python3 scripts/pkc_pack.py features/user-authentication.md --tiny
  python3 scripts/pkc_pack.py features/user-authentication.md --mermaid
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import parse_frontmatter, resolve_knowledge_root, utc_now  # noqa: E402

MD_LINK = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")


def resolve_concept(bundle: Path, ref: str) -> Path:
    ref = ref.strip()
    if ref.startswith("/"):
        return bundle / ref.lstrip("/")
    p = Path(ref)
    if p.is_file():
        return p.resolve()
    for candidate in (bundle / ref, bundle / f"{ref}.md"):
        if candidate.is_file():
            return candidate
    if not ref.endswith(".md"):
        matches = list(bundle.rglob(f"{Path(ref).name}.md"))
        if len(matches) == 1:
            return matches[0]
    return bundle / ref


def extract_edges(bundle: Path, path: Path) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    edges: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    links = fm.get("links") or []
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            tgt = link.get("target") or ""
            rel = link.get("rel") or "related_to"
            if not tgt.startswith("/"):
                continue
            key = (rel, tgt)
            if key in seen:
                continue
            seen.add(key)
            edges.append((rel, tgt, Path(tgt).stem))

    for m in MD_LINK.finditer(body):
        label, tgt = m.group(1), m.group(2).split("#", 1)[0]
        if not tgt.startswith("/"):
            continue
        key = ("links_to", tgt)
        if key in seen:
            continue
        if any(t == tgt for _, t, _ in edges):
            continue
        seen.add(key)
        edges.append(("links_to", tgt, label))

    return edges


def pack(
    bundle: Path,
    seed: Path,
    *,
    hops: int = 2,
    max_nodes: int = 20,
) -> dict[str, Any]:
    seed_rel = "/" + seed.resolve().relative_to(bundle.resolve()).as_posix()
    queue: deque[tuple[str, int]] = deque([(seed_rel, 0)])
    visited: dict[str, int] = {}
    edge_list: list[dict[str, str]] = []
    nodes: dict[str, dict[str, Any]] = {}

    while queue and len(visited) < max_nodes:
        rel, depth = queue.popleft()
        if rel in visited:
            continue
        path = bundle / rel.lstrip("/")
        if not path.is_file():
            continue
        visited[rel] = depth
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        nodes[rel] = {
            "path": rel,
            "type": fm.get("type") or "Unknown",
            "title": fm.get("title") or path.stem,
            "description": fm.get("description") or "",
            "status": fm.get("status"),
            "depth": depth,
            "excerpt": _excerpt(body),
        }
        if depth >= hops:
            continue
        for rel_type, tgt, label in extract_edges(bundle, path):
            edge_list.append({"from": rel, "to": tgt, "rel": rel_type, "label": label})
            if tgt not in visited and len(visited) + len(queue) < max_nodes:
                queue.append((tgt, depth + 1))

    priority = {
        "DecisionRecord": 0,
        "Meeting": 1,
        "Experiment": 2,
        "Discovery": 3,
        "Assumption": 4,
        "Question": 5,
        "Design": 6,
        "Requirement": 7,
        "Feature": 8,
        "TicketLink": 9,
        "CodeChange": 10,
        "Release": 11,
    }
    ordered = sorted(
        nodes.values(),
        key=lambda n: (n["depth"], priority.get(n["type"], 50), n["title"]),
    )

    return {
        "seed": seed_rel,
        "hops": hops,
        "max_nodes": max_nodes,
        "node_count": len(ordered),
        "nodes": ordered,
        "edges": edge_list,
        "excluded_note": "Nodes beyond hops/max_nodes omitted for progressive disclosure.",
    }


def _excerpt(body: str, limit: int = 400) -> str:
    lines = [ln for ln in body.splitlines() if ln.strip() and not ln.startswith("#")]
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _mermaid_id(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", path.strip("/"))


def render_mermaid(result: dict[str, Any]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for n in result["nodes"]:
        nid = _mermaid_id(n["path"])
        label = f"{n['type']}: {n['title']}".replace('"', "'")
        shape = {
            "DecisionRecord": f'{nid}{{"{label}"}}',
            "Feature": f'{nid}["{label}"]',
            "Meeting": f'{nid}(["{label}"])',
            "Experiment": f'{nid}[("{label}")]',
            "Question": f'{nid}{{"{label}?"}}',
        }.get(n["type"], f'{nid}["{label}"]')
        lines.append(f"  {shape}")
    seen = set()
    for e in result["edges"]:
        if e["from"] not in {n["path"] for n in result["nodes"]}:
            continue
        if e["to"] not in {n["path"] for n in result["nodes"]}:
            continue
        key = (e["from"], e["to"], e["rel"])
        if key in seen:
            continue
        seen.add(key)
        a, b = _mermaid_id(e["from"]), _mermaid_id(e["to"])
        lines.append(f"  {a} -- {e['rel']} --> {b}")
    lines.append("```")
    return "\n".join(lines)


def render_markdown(result: dict[str, Any], *, include_mermaid: bool = True) -> str:
    seed = result["seed"]
    lines = [
        "---",
        "type: ContextPack",
        f"title: Context pack for {seed}",
        f"description: Progressive disclosure pack ({result['hops']} hops, {result['node_count']} nodes)",
        f"timestamp: {utc_now()}",
        "generated: true",
        "tags: [pack, pkc, progressive-disclosure]",
        "---",
        "",
        f"# Context pack: `{seed}`",
        "",
        f"- Hops: **{result['hops']}**",
        f"- Nodes: **{result['node_count']}** (max {result['max_nodes']})",
        f"- Generated: {utc_now()}",
        "",
    ]
    if include_mermaid and result["nodes"]:
        lines.append("## Graph")
        lines.append("")
        lines.append(render_mermaid(result))
        lines.append("")
    lines.append("## Nodes (ranked)")
    lines.append("")
    for n in result["nodes"]:
        lines.append(
            f"### [{n['title']}]({n['path']}) · `{n['type']}` · depth {n['depth']}"
        )
        if n.get("description"):
            lines.append("")
            lines.append(n["description"])
        if n.get("excerpt"):
            lines.append("")
            lines.append(f"> {n['excerpt']}")
        lines.append("")

    if result["edges"]:
        lines.append("## Edges")
        lines.append("")
        for e in result["edges"]:
            lines.append(f"- `{e['from']}` —[{e['rel']}]→ `{e['to']}`")
        lines.append("")

    lines.append(f"_{result['excluded_note']}_")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC progressive disclosure pack")
    parser.add_argument("concept", help="Concept path (in-bundle or filesystem)")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--hops", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=20)
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="ADHD/chat mode: 1 hop, max 8 nodes",
    )
    parser.add_argument("--mermaid", action="store_true", help="Print mermaid only")
    parser.add_argument("--write", default=None, help="Directory or file to write pack markdown")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    hops = 1 if args.tiny else args.hops
    max_nodes = 8 if args.tiny else args.max_nodes

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    seed = resolve_concept(bundle, args.concept)
    if not seed.is_file():
        print(f"error: concept not found: {args.concept}", file=sys.stderr)
        return 1

    result = pack(bundle, seed, hops=hops, max_nodes=max_nodes)

    if args.mermaid:
        print(render_mermaid(result))
        return 0

    md = render_markdown(result, include_mermaid=True)

    if args.write:
        out = Path(args.write)
        if out.is_dir() or str(args.write).endswith("/"):
            out.mkdir(parents=True, exist_ok=True)
            slug = seed.stem + ("-tiny" if args.tiny else "")
            out = out / f"{slug}-pack.md"
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}")

    if args.json:
        import json

        print(json.dumps(result, indent=2))
    elif not args.write:
        print(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
