#!/usr/bin/env python3
"""UserPromptSubmit hook: inject a tiny context pack when a prompt names a Feature.

`UserPromptSubmit` is the only hook whose output reaches the model *before* the
turn runs, so it is the only place auto-injection can happen at all. A
`PostToolUse` hook fires after Claude has already decided what to read.

Detection is deliberately narrow -- a `features/` path that exists, or a ULID
that resolves to a concept of type Feature. Anything looser fires on prompts
that never asked about a Feature, and an unwanted injection is worse than none:
it spends context on every turn.

Silence is the default. No match, no bundle, no config, bad stdin, an
unreadable concept -- all exit 0 with empty output. A hook that errors or
chatters is a hook people disable.

Usage:
  echo '{"prompt": "...", "cwd": "/repo"}' | python3 scripts/pkc_auto_context.py
  python3 scripts/pkc_auto_context.py --repo . --prompt "features/user-auth.md"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import (  # noqa: E402
    load_config,
    parse_frontmatter,
    resolve_knowledge_root,
)
from pkc_pack import finalize_markdown, pack  # noqa: E402

# `\b` before `features` matches whether the prompt wrote `features/x`,
# `/features/x`, or `` `features/x` ``. The slug class is greedy so it swallows
# a trailing `.md`, which is then stripped -- non-greedy would stop at the first
# hyphen, since `-` is not a word character.
FEATURE_PATH = re.compile(r"\bfeatures/([A-Za-z0-9][A-Za-z0-9._-]*)")

# Crockford base32: no I, L, O, or U. First char is 0-7 (48-bit timestamp).
ULID = re.compile(r"\b[0-7][0-9A-HJKMNP-TV-Z]{25}\b")

TINY_HOPS = 1
TINY_MAX_NODES = 8


def _concept_type(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    return fm.get("type")


def _feature_for_ulid(bundle: Path, ulid: str) -> str | None:
    features = bundle / "features"
    if not features.is_dir():
        return None
    for path in sorted(features.glob("*.md")):
        try:
            fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if fm.get("worklog_id") == ulid and fm.get("type") == "Feature":
            return f"/features/{path.name}"
    return None


def detect_feature(bundle: Path, prompt: str) -> str | None:
    """Return the in-bundle path of a Feature the prompt refers to, or None.

    A path wins over a ULID: it is what the human actually typed.
    """
    for match in FEATURE_PATH.finditer(prompt):
        slug = match.group(1).rstrip(".")
        if slug.endswith(".md"):
            slug = slug[:-3]
        rel = f"/features/{slug}.md"
        if _concept_type(bundle / rel.lstrip("/")) == "Feature":
            return rel

    for match in ULID.finditer(prompt):
        rel = _feature_for_ulid(bundle, match.group(0))
        if rel:
            return rel

    return None


def build_injection(
    bundle: Path,
    rel: str,
    *,
    hops: int = TINY_HOPS,
    max_nodes: int = TINY_MAX_NODES,
) -> str:
    """Render the tiny pack for `rel` as Markdown.

    No mermaid: a diagram costs tokens the model cannot act on any better than
    the edge list it already gets.
    """
    result = pack(bundle, bundle / rel.lstrip("/"), hops=hops, max_nodes=max_nodes)
    md, _meta = finalize_markdown(result, include_mermaid=False)
    return md


def injection_for(repo: Path, prompt: str, bundle_override: str | None = None) -> str | None:
    cfg = load_config(repo)
    if cfg.get("enabled") is False:
        return None
    pack_cfg = cfg.get("pack") or {}
    if pack_cfg.get("auto_inject_on_feature") is False:
        return None

    bundle = resolve_knowledge_root(repo, bundle_override)
    if not (bundle / "index.md").is_file():
        return None

    rel = detect_feature(bundle, prompt)
    if not rel:
        return None

    return build_injection(
        bundle,
        rel,
        hops=int(pack_cfg.get("tiny_hops") or TINY_HOPS),
        max_nodes=int(pack_cfg.get("tiny_max_nodes") or TINY_MAX_NODES),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC auto-context UserPromptSubmit hook")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--prompt", default=None, help="Bypass stdin (for debugging)")
    args = parser.parse_args(argv)

    try:
        prompt = args.prompt
        repo = args.repo
        if prompt is None:
            payload = json.loads(sys.stdin.read() or "{}")
            # Hosts disagree on the field name; read both rather than guess.
            prompt = payload.get("prompt") or payload.get("user_prompt") or ""
            repo = repo or payload.get("cwd")

        text = injection_for(Path(repo or ".").resolve(), prompt, args.bundle)
        if text:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": text,
                        }
                    }
                )
            )
    except Exception:  # noqa: BLE001 - a hook never fails the turn it decorates
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
