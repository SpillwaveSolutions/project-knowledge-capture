#!/usr/bin/env python3
"""Build a progressive-disclosure context pack around a concept.

Walks typed frontmatter links and absolute Markdown body links up to N hops.
Does not require okf-plugin (works standalone; prefer okf-graph.py pack when available).

Usage:
  python3 scripts/pkc_pack.py features/user-authentication.md --bundle sample-knowledge --hops 2
  python3 scripts/pkc_pack.py features/user-authentication.md --tiny
  python3 scripts/pkc_pack.py features/user-authentication.md --mermaid
  python3 scripts/pkc_pack.py features/user-authentication.md --tiny --summary
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    extract_concept_edges,
    find_rg,
    is_concept_rel,
    iter_concepts,
    parse_frontmatter,
    resolve_knowledge_root,
    rg_list_files,
    utc_now,
)
from pkc_index import open_graph  # noqa: E402

MD_LINK = re.compile(r"\[([^\]]+)\]\((/[^)]+)\)")

DEFAULT_WINDOW_TOKENS = 128_000
PACK_BUDGET_DENOMINATOR = 4
SUMMARY_LEAD_LIMIT = 8
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class PackBudgetError(Exception):
    def __init__(self, tokens: int, budget: int, window: int, nodes: list[str]):
        self.tokens = tokens
        self.budget = budget
        self.window = window
        self.nodes = nodes
        super().__init__(f"pack exceeds token budget ({tokens}/{budget})")


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


def extract_edges(
    bundle: Path,
    path: Path,
    *,
    cache: dict[str, list[tuple[str, str, str]]] | None = None,
) -> list[tuple[str, str, str]]:
    key = str(path.resolve()) if path.exists() else str(path)
    if cache is not None and key in cache:
        return cache[key]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # build_reverse_index() reads every file in the bundle, not just the
        # ones on the walk. One unreadable file must not break pack().
        edges: list[tuple[str, str, str]] = []
        if cache is not None:
            cache[key] = edges
        return edges
    fm, body = parse_frontmatter(text)
    edges = extract_concept_edges(fm, body)
    if cache is not None:
        cache[key] = edges
    return edges


def _inbound_via_rg(
    bundle: Path,
    target: str,
    *,
    cache: dict[str, list[tuple[str, str, str]]] | None = None,
) -> list[tuple[str, str, str]] | None:
    """Files that mention `target`, parsed for real inbound edges. None = fall back."""
    hits = rg_list_files(bundle, [target], fixed_string=True, ignore_case=False)
    if hits is None:
        return None
    inbound: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    # rg_list_files already returns resolved paths. A bundle reached through a
    # symlink alias (macOS /var -> /private/var) would make relative_to raise
    # and silently drop a real inbound edge, so resolve the bundle -- ONCE,
    # never per hit -- and keep the concept-rule check on strings.
    bundle_root = bundle.resolve()
    for path in hits:
        try:
            rel = path.relative_to(bundle_root).as_posix()
        except ValueError:
            continue
        if not is_concept_rel(rel):
            continue
        src = "/" + rel
        if src == target:
            continue
        for rel_type, tgt, label in extract_edges(bundle, path, cache=cache):
            if tgt != target:
                continue
            key = (rel_type, src, label)
            if key in seen:
                continue
            seen.add(key)
            inbound.append((rel_type, src, label))
    return inbound


def build_reverse_index(
    bundle: Path,
    *,
    cache: dict[str, list[tuple[str, str, str]]] | None = None,
    use_rg: bool | None = None,
) -> dict[str, list[tuple[str, str, str]]]:
    """Map each target path to the edges that point at it.

    pack() used to walk outbound links only, so a concept that pointed *at*
    the seed was invisible from it unless the seed happened to point back.
    Capture helpers wrote that inverse edge by hand, which covers only the
    concepts those helpers create -- not one authored by hand, or by a sibling
    plugin sharing the bundle.

    When ripgrep is available, this still builds a full map (needed for the
    BFS walk) but only parses files that mention at least one concept path
    would be more work than it's worth on small bundles. Instead, pack()
    uses a lazy ReverseIndex that rg-filters per visited node.
    """
    # iter_concepts() skips index.md, log.md and packs/. Those are generated
    # listings of the bundle, so every concept has an inbound edge from its
    # catalog -- following those would drag the whole directory into the pack
    # and crowd out the knowledge the seed actually relates to.
    #
    # ponytail: O(bundle) scan per pack() call. Cache it under .pkc/ if
    # bundles grow past a few thousand files -- the auto-context hook pays
    # this cost on every turn. rg-backed ReverseIndex is the accelerator
    # until that index exists.
    if use_rg is False:
        pass
    index: dict[str, list[tuple[str, str, str]]] = {}
    for path in iter_concepts(bundle):
        src = "/" + path.relative_to(bundle).as_posix()
        for rel_type, tgt, label in extract_edges(bundle, path, cache=cache):
            index.setdefault(tgt, []).append((rel_type, src, label))
    return index


class ReverseIndex:
    """Inbound edges: SQLite index → rg → full scan."""

    def __init__(
        self,
        bundle: Path,
        *,
        cache: dict[str, list[tuple[str, str, str]]] | None = None,
        use_rg: bool | None = None,
        use_index: bool | None = None,
    ):
        self.bundle = bundle
        self.cache = cache if cache is not None else {}
        self._full: dict[str, list[tuple[str, str, str]]] | None = None
        self._memo: dict[str, list[tuple[str, str, str]]] = {}
        self._graph = None
        if use_index is False:
            self._index = False
        else:
            self._graph = open_graph(bundle)
            self._index = self._graph is not None
            if use_index is True and not self._index:
                self._index = False
        if use_rg is False:
            self._rg = False
        else:
            self._rg = bool(find_rg())

    @property
    def engine(self) -> str:
        if self._index:
            return "index"
        return "rg" if self._rg else "scan"

    def close(self) -> None:
        if self._graph is not None:
            self._graph.close()
            self._graph = None

    def get(self, target: str, default: list | None = None) -> list[tuple[str, str, str]]:
        if target in self._memo:
            return self._memo[target]
        if self._index and self._graph is not None:
            found = self._graph.inbound(target)
            self._memo[target] = found
            return found
        if self._rg:
            found = _inbound_via_rg(self.bundle, target, cache=self.cache)
            if found is not None:
                self._memo[target] = found
                return found
            self._rg = False
        if self._full is None:
            self._full = build_reverse_index(
                self.bundle, cache=self.cache, use_rg=False
            )
        edges = self._full.get(target, default or [])
        self._memo[target] = edges
        return edges


def pack(
    bundle: Path,
    seed: Path,
    *,
    hops: int = 2,
    max_nodes: int = 20,
    use_rg: bool | None = None,
    use_index: bool | None = None,
) -> dict[str, Any]:
    seed_rel = "/" + seed.resolve().relative_to(bundle.resolve()).as_posix()
    parse_cache: dict[str, list[tuple[str, str, str]]] = {}
    inbound = ReverseIndex(bundle, cache=parse_cache, use_rg=use_rg, use_index=use_index)
    try:
        return _pack_walk(
            bundle, seed, seed_rel, hops, max_nodes, parse_cache, inbound
        )
    finally:
        inbound.close()


def _pack_walk(
    bundle: Path,
    seed: Path,
    seed_rel: str,
    hops: int,
    max_nodes: int,
    parse_cache: dict[str, list[tuple[str, str, str]]],
    inbound: ReverseIndex,
) -> dict[str, Any]:
    queue: deque[tuple[str, int]] = deque([(seed_rel, 0)])
    visited: dict[str, int] = {}
    edge_list: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()
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
            "body": body if rel == seed_rel else "",
        }
        if depth >= hops:
            continue
        # Outbound: this node -> its targets. Inbound: the nodes that name
        # this one. Each edge is recorded in the direction it was authored,
        # so both renderers draw the true arrow with no change to either.
        neighbours: list[tuple[str, str, str, str]] = [
            (rel, tgt, rel_type, label)
            for rel_type, tgt, label in extract_edges(bundle, path, cache=parse_cache)
        ]
        neighbours += [
            (src, rel, rel_type, label)
            for rel_type, src, label in inbound.get(rel, [])
        ]
        for src, tgt, rel_type, label in neighbours:
            key = (src, tgt, rel_type)
            if key not in seen_edges:
                seen_edges.add(key)
                edge_list.append(
                    {"from": src, "to": tgt, "rel": rel_type, "label": label}
                )
            other = tgt if src == rel else src
            if other not in visited and len(visited) + len(queue) < max_nodes:
                queue.append((other, depth + 1))

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
        "reverse_index": inbound.engine,
        "excluded_note": "Nodes beyond hops/max_nodes omitted for progressive disclosure. Node clip is not a token budget.",
    }


def estimate_tokens(text: str) -> int:
    """Cheap chars/4 estimator. Not a model tokenizer."""
    if not text:
        return 0
    return (len(text) + 3) // 4


def resolve_pack_budget(
    max_tokens: str | int | None = None,
    window_tokens: str | int | None = None,
) -> tuple[int, int]:
    raw_window = window_tokens if window_tokens not in (None, "") else os.environ.get("SECOND_BRAIN_WINDOW_TOKENS") or ""
    window = int(raw_window) if str(raw_window).strip() else DEFAULT_WINDOW_TOKENS
    if window < 1:
        raise SystemExit("error: window tokens must be >= 1")
    raw_budget = max_tokens if max_tokens not in (None, "") else os.environ.get("SECOND_BRAIN_PACK_MAX_TOKENS") or ""
    budget = int(raw_budget) if str(raw_budget).strip() else max(1, window // PACK_BUDGET_DENOMINATOR)
    if budget < 1:
        raise SystemExit("error: max tokens must be >= 1")
    return window, budget


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


def render_markdown(
    result: dict[str, Any],
    *,
    include_mermaid: bool = True,
    tokens: int | None = None,
    budget: int | None = None,
) -> str:
    seed = result["seed"]
    token_line = ""
    if tokens is not None and budget is not None:
        token_line = f"- Tokens: **{tokens}/{budget}**\n"
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
        token_line.rstrip(),
        f"- Generated: {utc_now()}",
        "",
    ]
    lines = [ln for ln in lines if ln is not None]
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
        if n["path"] == seed:
            body = (n.get("body") or "").strip()
            if body:
                lines.append("")
                lines.append(body)
        elif n.get("description"):
            lines.append("")
            lines.append(str(n["description"]))
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


def finalize_markdown(
    result: dict[str, Any],
    *,
    include_mermaid: bool = True,
    max_tokens: str | int | None = None,
    window_tokens: str | int | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the pack and fail closed if it exceeds the token budget.

    Bodies off unless that node is the pack root. Node clip is not a token budget.
    """
    window, budget = resolve_pack_budget(max_tokens, window_tokens)
    draft = render_markdown(result, include_mermaid=include_mermaid, tokens=0, budget=budget)
    tokens = estimate_tokens(draft)
    md = render_markdown(result, include_mermaid=include_mermaid, tokens=tokens, budget=budget)
    tokens = estimate_tokens(md)
    meta = {"tokens": tokens, "budget": budget, "window": window}
    if tokens > budget:
        raise PackBudgetError(tokens, budget, window, [n["path"] for n in result["nodes"]])
    return md, meta


def _one_line(text: str, max_chars: int = 140) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def excerpt_sentences(text: str, *, count: int = 3, max_chars: int = 420) -> str:
    """First 2–3 sentences of a body. Not a full pack dump."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(cleaned) if p.strip()]
    return _one_line(" ".join(parts[:count]), max_chars)


def seed_node(result: dict[str, Any]) -> dict[str, Any] | None:
    seed = result.get("seed")
    for n in result.get("nodes") or []:
        if n.get("path") == seed:
            return n
    return None


def lead_nodes(
    result: dict[str, Any], *, limit: int = SUMMARY_LEAD_LIMIT
) -> list[dict[str, Any]]:
    leads: list[dict[str, Any]] = []
    for n in result.get("nodes") or []:
        leads.append(
            {
                "title": n.get("title") or "",
                "type": n.get("type") or "Unknown",
                "path": n.get("path") or "",
                "description": _one_line(n.get("description") or ""),
                "depth": n.get("depth", 0),
            }
        )
        if len(leads) >= limit:
            break
    return leads


def render_summary(
    result: dict[str, Any],
    *,
    tokens: int | None = None,
    budget: int | None = None,
    seed_excerpt: str | None = None,
    lead: list[dict[str, Any]] | None = None,
) -> str:
    """Compact card-friendly markdown. No mermaid, no ranked bodies, no edge dump."""
    seed = result["seed"]
    node = seed_node(result)
    seed_type = (node or {}).get("type") or "Unknown"
    seed_title = (node or {}).get("title") or seed
    leads = lead if lead is not None else lead_nodes(result)
    edges = result.get("edges") or []
    token_line = None
    if tokens is not None and budget is not None:
        token_line = f"- Tokens: **{tokens}/{budget}**"
    lines = [
        "## Pack summary",
        f"- Seed: `{seed}` (`{seed_type}`) — {seed_title}",
        f"- Hops: **{result['hops']}**",
        f"- Nodes: **{result['node_count']}** (max {result['max_nodes']})",
        token_line,
        f"- Engine: **{result.get('reverse_index') or 'scan'}**",
        f"- Edges: **{len(edges)}**",
        "- Lead nodes:",
    ]
    lines = [ln for ln in lines if ln]
    if leads:
        for n in leads:
            why = n.get("description") or "no description"
            lines.append(f"  - {n['title']} · {n['type']} · `{n['path']}` — {why}")
    else:
        lines.append("  - none")
    if seed_excerpt:
        lines.append(f"- Seed excerpt: {seed_excerpt}")
    lines.append(f"- Excluded: {result.get('excluded_note') or ''}")
    lines.append("")
    return "\n".join(lines)


def finalize_summary(
    result: dict[str, Any],
    *,
    max_tokens: str | int | None = None,
    window_tokens: str | int | None = None,
    include_seed_excerpt: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Render a compact summary and fail closed if it exceeds the token budget."""
    window, budget = resolve_pack_budget(max_tokens, window_tokens)
    excerpt = ""
    if include_seed_excerpt:
        node = seed_node(result)
        excerpt = excerpt_sentences((node or {}).get("body") or "")
    leads = lead_nodes(result)
    draft = render_summary(
        result, tokens=0, budget=budget, seed_excerpt=excerpt or None, lead=leads
    )
    tokens = estimate_tokens(draft)
    md = render_summary(
        result, tokens=tokens, budget=budget, seed_excerpt=excerpt or None, lead=leads
    )
    tokens = estimate_tokens(md)
    meta: dict[str, Any] = {
        "tokens": tokens,
        "budget": budget,
        "window": window,
        "edge_count": len(result.get("edges") or []),
        "lead_nodes": leads,
        "summary_markdown": md,
    }
    if excerpt:
        meta["seed_excerpt"] = excerpt
    if tokens > budget:
        raise PackBudgetError(tokens, budget, window, [n["path"] for n in result["nodes"]])
    return md, meta


def _strip_node_bodies(result: dict[str, Any]) -> None:
    for n in result.get("nodes") or []:
        if isinstance(n, dict):
            n["body"] = ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC progressive disclosure pack")
    parser.add_argument("concept", help="Concept path (in-bundle or filesystem)")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--hops", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=20)
    parser.add_argument("--max-tokens", default="")
    parser.add_argument("--window-tokens", default="")
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="ADHD/chat mode: 1 hop, max 8 nodes",
    )
    parser.add_argument("--mermaid", action="store_true", help="Print mermaid only")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact card (seed, hops, leads, edge count). "
        "Mutually exclusive with --mermaid for stdout shape",
    )
    parser.add_argument(
        "--summary-seed-excerpt",
        action="store_true",
        help="With --summary, include a 2–3 sentence excerpt of the seed body",
    )
    parser.add_argument("--write", default=None, help="Directory or file to write pack markdown")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--rg",
        action="store_true",
        help="Use ripgrep for inbound/backlink discovery (default when rg is on PATH)",
    )
    parser.add_argument(
        "--no-rg",
        action="store_true",
        help="Disable ripgrep; full-scan the reverse index (unless SQLite index is used)",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Disable the SQLite index; fall through to rg then scan",
    )
    args = parser.parse_args(argv)

    hops = 1 if args.tiny else args.hops
    max_nodes = 8 if args.tiny else args.max_nodes
    if args.summary and args.mermaid:
        print("error: --summary and --mermaid are mutually exclusive", file=sys.stderr)
        return 2
    if args.summary_seed_excerpt and not args.summary:
        print("error: --summary-seed-excerpt requires --summary", file=sys.stderr)
        return 2
    if args.rg and args.no_rg:
        print("error: --rg and --no-rg are mutually exclusive", file=sys.stderr)
        return 2
    use_rg: bool | None
    if args.no_rg:
        use_rg = False
    elif args.rg:
        use_rg = True
    else:
        use_rg = None
    use_index: bool | None = False if args.no_index else None

    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    seed = resolve_concept(bundle, args.concept)
    if not seed.is_file():
        print(f"error: concept not found: {args.concept}", file=sys.stderr)
        return 1

    result = pack(bundle, seed, hops=hops, max_nodes=max_nodes, use_rg=use_rg, use_index=use_index)

    try:
        if args.mermaid:
            window, budget = resolve_pack_budget(args.max_tokens, args.window_tokens)
            diagram = render_mermaid(result)
            tokens = estimate_tokens(diagram)
            if tokens > budget:
                raise PackBudgetError(tokens, budget, window, [n["path"] for n in result["nodes"]])
            print(diagram)
            return 0
        if args.summary:
            md, meta = finalize_summary(
                result,
                max_tokens=args.max_tokens,
                window_tokens=args.window_tokens,
                include_seed_excerpt=args.summary_seed_excerpt,
            )
        else:
            md, meta = finalize_markdown(
                result,
                include_mermaid=True,
                max_tokens=args.max_tokens,
                window_tokens=args.window_tokens,
            )
    except PackBudgetError as exc:
        payload = {
            "error": "pack exceeds token budget",
            "tokens": exc.tokens,
            "budget": exc.budget,
            "window": exc.window,
            "nodes": exc.nodes,
            "hint": "narrow --hops / --tiny; node clip is not a token budget",
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                f"error: pack exceeds token budget ({exc.tokens}/{exc.budget})",
                file=sys.stderr,
            )
        return 1

    result.update(meta)
    if args.summary:
        _strip_node_bodies(result)

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
        print(json.dumps(result, indent=2))
    elif not args.write:
        print(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
