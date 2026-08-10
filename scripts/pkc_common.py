#!/usr/bin/env python3
"""Shared helpers for Project Knowledge Capture (PKC)."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CATALOGS = (
    "meetings",
    "experiments",
    "discoveries",
    "decisions",
    "assumptions",
    "questions",
    "features",
    "requirements",
    "specs",
    "designs",
    "releases",
    "code",
    "packages",
    "tickets",
    "risks",
    "acceptance",
)

TYPE_TO_DIR = {
    "Meeting": "meetings",
    "Experiment": "experiments",
    "Discovery": "discoveries",
    "DecisionRecord": "decisions",
    "Assumption": "assumptions",
    "Question": "questions",
    "Feature": "features",
    "Requirement": "requirements",
    "Specification": "specs",
    "Design": "designs",
    "Release": "releases",
    "CodeChange": "code",
    "Package": "packages",
    "Module": "packages",
    "Risk": "risks",
    "Acceptance": "acceptance",
    "TicketLink": "tickets",
    "ContextPack": "packs",
}

DEFAULT_RELATIONS = (
    "depends_on",
    "routes_to",
    "implements",
    "documents",
    "uses",
    "owns",
    "supersedes",
    "related_to",
    "tracks",
    "maps_to",
    "satisfies",
    "designed_by",
    "decides",
    "informs",
    "discovered_in",
    "originates_from",
    "lands_in",
    "released_in",
    "verified_by",
    "assumes",
    "blocks",
    "answers",
    "validates",
    "invalidates",
    "mitigates",
    "exposes",
)

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?i)\b(sk|pk|api[_-]?key|token|secret|password|passwd|pwd)[-_]?[a-z0-9]*\s*[:=]\s*['\"]?[^\s'\"\n]{8,}"
        ),
        "[REDACTED_SECRET]",
    ),
    # OpenAI-style / generic sk- keys
    (re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), "[REDACTED_GOOGLE_KEY]"),
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b"), "Bearer [REDACTED_TOKEN]"),
]

PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "[REDACTED_PHONE]",
    ),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str, max_len: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    if not text:
        text = "untitled"
    return text[:max_len].rstrip("-")


def scrub_text(text: str, *, pii: bool = True, secrets: bool = True) -> tuple[str, list[str]]:
    found: list[str] = []
    out = text
    if secrets:
        for pat, repl in SECRET_PATTERNS:
            if pat.search(out):
                found.append(repl)
            out = pat.sub(repl, out)
    if pii:
        for pat, repl in PII_PATTERNS:
            if pat.search(out):
                found.append(repl)
            out = pat.sub(repl, out)
    seen: set[str] = set()
    labels = []
    for f in found:
        if f not in seen:
            seen.add(f)
            labels.append(f)
    return out, labels


def load_config(repo_root: Path) -> dict[str, Any]:
    candidates = [
        repo_root / ".pkc" / "config.yml",
        repo_root / ".pkc" / "config.yaml",
        repo_root / ".work" / "config.yml",
        repo_root / ".work" / "config.yaml",
    ]
    for path in candidates:
        if path.is_file():
            return _parse_simple_yaml(path.read_text(encoding="utf-8")).get("pkc", {}) or {}
    return {}


def resolve_knowledge_root(repo_root: Path, override: str | None = None) -> Path:
    if override:
        root = Path(override)
        return root if root.is_absolute() else (repo_root / root)
    cfg = load_config(repo_root)
    name = cfg.get("knowledge_root") or "knowledge"
    for candidate in (repo_root / name, repo_root / "sample-knowledge", repo_root / ".okf"):
        if candidate.is_dir() and (candidate / "index.md").is_file():
            return candidate
    return repo_root / name


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            item_body = line[2:].strip()
            if isinstance(parent, dict) and len(stack) >= 2 and isinstance(stack[-2][1], dict):
                gp = stack[-2][1]
                for k, v in list(gp.items()):
                    if v is parent and isinstance(v, dict) and len(v) == 0:
                        new_list: list[Any] = []
                        gp[k] = new_list
                        stack[-1] = (stack[-1][0], new_list)
                        parent = new_list
                        break
            if not isinstance(parent, list):
                continue
            if ":" in item_body and not _is_quoted(item_body):
                key, _, rest = item_body.partition(":")
                item_map: dict[str, Any] = {key.strip(): _scalar(rest.strip())}
                parent.append(item_map)
                stack.append((indent, item_map))
            else:
                parent.append(_scalar(item_body))
            continue
        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "" or rest in ("|", ">"):
                j = i
                next_line = None
                while j < len(lines):
                    peek = lines[j]
                    if peek.strip() and not peek.lstrip().startswith("#"):
                        next_line = peek
                        break
                    j += 1
                if next_line is not None:
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    next_stripped = next_line.strip()
                    if next_indent > indent and next_stripped.startswith("- "):
                        new_list = []
                        if isinstance(parent, dict):
                            parent[key] = new_list
                        stack.append((indent, new_list))
                        continue
                new_map: dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[key] = new_map
                stack.append((indent, new_map))
            else:
                if isinstance(parent, dict):
                    parent[key] = _scalar(rest)
    return root


def _is_quoted(value: str) -> bool:
    return (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    )


def _unescape(s: str) -> str:
    """Reverse the escaping `_fmt_scalar` applies to a quoted scalar.

    Without this, `parse(dump(x)) != x` for any value containing a quote or a
    backslash: the dumper escapes, the reader only strips the quotes, and every
    read-modify-write cycle re-escapes what was already escaped. Backslash count
    doubles per pass, so a script that edits one field corrupts every quoted
    string in the file.

    It is also self-concealing -- reading the file back with this same parser
    returns a value that looks right, because the escaping is never undone, so
    the damage lives only in the bytes on disk.

    Single-pass, so a literal backslash-quote in the source survives intact.
    """
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in ('"', "\\"):
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _scalar(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p.strip()) for p in _split_csv(inner)]
    if _is_quoted(value):
        return _unescape(value[1:-1])
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    if value.lower() in ("null", "~", "none"):
        return None
    if value == "":
        return ""
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _split_csv(inner: str) -> list[str]:
    parts: list[str] = []
    buf = ""
    in_q = False
    qch = ""
    for ch in inner:
        if in_q:
            buf += ch
            if ch == qch:
                in_q = False
            continue
        if ch in ('"', "'"):
            in_q = True
            qch = ch
            buf += ch
            continue
        if ch == ",":
            parts.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return _parse_simple_yaml(parts[1]), parts[2].lstrip("\n")


def dump_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        lines.extend(_dump_key(key, value, 0))
    lines.append("---")
    return "\n".join(lines) + "\n"


def _dump_key(key: str, value: Any, indent: int) -> list[str]:
    pad = "  " * indent
    if isinstance(value, dict):
        out = [f"{pad}{key}:"]
        for k, v in value.items():
            out.extend(_dump_key(k, v, indent + 1))
        return out
    if isinstance(value, list):
        if not value:
            return [f"{pad}{key}: []"]
        if all(isinstance(x, (str, int, float, bool)) or x is None for x in value):
            if all(isinstance(x, str) and re.match(r"^[\w./:@+-]+$", x) for x in value):
                inner = ", ".join(str(x) for x in value)
                return [f"{pad}{key}: [{inner}]"]
        out = [f"{pad}{key}:"]
        ipad = "  " * (indent + 1)
        for item in value:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    if first:
                        out.append(f"{ipad}- {k}: {_fmt_scalar(v)}")
                        first = False
                    else:
                        out.append(f"{ipad}  {k}: {_fmt_scalar(v)}")
            else:
                out.append(f"{ipad}- {_fmt_scalar(item)}")
        return out
    return [f"{pad}{key}: {_fmt_scalar(value)}"]


def _fmt_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if s == "" or any(c in s for c in ":#{}[]&*!|>'\"%@`") or s.strip() != s:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def write_concept(
    bundle: Path,
    rel_path: str,
    frontmatter: dict[str, Any],
    body: str,
    *,
    merge: bool = True,
) -> tuple[Path, str]:
    path = bundle / rel_path.lstrip("/")
    path.parent.mkdir(parents=True, exist_ok=True)
    if "timestamp" not in frontmatter:
        frontmatter = {**frontmatter, "timestamp": utc_now()}
    if path.is_file():
        existing = path.read_text(encoding="utf-8")
        if merge:
            old_fm, old_body = parse_frontmatter(existing)
            ts = old_fm.get("truth_state")
            if ts in ("snapshot", "superseded", "archived") and frontmatter.get(
                "truth_state", "current"
            ) == "current":
                if not frontmatter.get("force"):
                    return path, "skipped"
            new_fm = {**old_fm, **{k: v for k, v in frontmatter.items() if k != "force"}}
            if "timestamp" in old_fm and old_fm.get("title") == new_fm.get("title"):
                if frontmatter.get("stable_timestamp"):
                    new_fm["timestamp"] = old_fm["timestamp"]
            new_fm.pop("force", None)
            new_fm.pop("stable_timestamp", None)
            content = dump_frontmatter(new_fm) + "\n" + (body.strip() or old_body).rstrip() + "\n"
            if content == existing:
                return path, "skipped"
            path.write_text(content, encoding="utf-8")
            return path, "updated"
        content = dump_frontmatter(frontmatter) + "\n" + body.rstrip() + "\n"
        if content == existing:
            return path, "skipped"
        path.write_text(content, encoding="utf-8")
        return path, "updated"
    fm = {k: v for k, v in frontmatter.items() if k not in ("force", "stable_timestamp")}
    path.write_text(dump_frontmatter(fm) + "\n" + body.rstrip() + "\n", encoding="utf-8")
    return path, "created"


def ensure_catalog_index(bundle: Path, catalog: str, title: str | None = None) -> Path:
    cat_dir = bundle / catalog
    cat_dir.mkdir(parents=True, exist_ok=True)
    index = cat_dir / "index.md"
    if index.is_file():
        return index
    t = title or catalog.replace("-", " ").title()
    fm = {
        "type": "Catalog",
        "title": t,
        "description": f"Catalog of {t.lower()} concepts",
        "timestamp": utc_now(),
        "tags": ["catalog", catalog],
    }
    body = f"# {t}\n\nConcepts in this catalog:\n\n"
    for p in sorted(cat_dir.glob("*.md")):
        if p.name == "index.md":
            continue
        fm_c, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        label = fm_c.get("title") or p.stem
        body += f"- [{label}](/{catalog}/{p.name})\n"
    if body.endswith(":\n\n"):
        body += "_None yet._\n"
    index.write_text(dump_frontmatter(fm) + "\n" + body, encoding="utf-8")
    return index


def refresh_catalog_index(bundle: Path, catalog: str) -> None:
    cat_dir = bundle / catalog
    if not cat_dir.is_dir():
        return
    ensure_catalog_index(bundle, catalog)
    index = cat_dir / "index.md"
    fm, _ = parse_frontmatter(index.read_text(encoding="utf-8"))
    title = fm.get("title") or catalog.title()
    fm["timestamp"] = fm.get("timestamp") or utc_now()
    body = f"# {title}\n\nConcepts in this catalog:\n\n"
    entries = []
    for p in sorted(cat_dir.glob("*.md")):
        if p.name == "index.md":
            continue
        fm_c, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        label = fm_c.get("title") or p.stem
        entries.append(f"- [{label}](/{catalog}/{p.name})")
    body += "\n".join(entries) + ("\n" if entries else "_None yet._\n")
    index.write_text(dump_frontmatter(fm) + "\n" + body, encoding="utf-8")


def append_log(bundle: Path, message: str) -> None:
    log = bundle / "log.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"- {utc_now()}: {message}\n"
    if not log.is_file():
        log.write_text(
            f"---\ntitle: Change log\ndescription: PKC knowledge bundle log\ntimestamp: {utc_now()}\n---\n\n# Change log\n\n## {today}\n\n{entry}",
            encoding="utf-8",
        )
        return
    text = log.read_text(encoding="utf-8")
    heading = f"## {today}"
    if heading in text:
        text = text.replace(heading + "\n", heading + "\n\n" + entry, 1)
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        text = text.rstrip() + f"\n\n{heading}\n\n{entry}"
    log.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def ensure_bundle(bundle: Path, title: str = "Project Knowledge") -> None:
    bundle.mkdir(parents=True, exist_ok=True)
    index = bundle / "index.md"
    if not index.is_file():
        catalogs_md = "\n".join(f"- [{c.title()}](/{c}/index.md)" for c in CATALOGS)
        content = f"""---
okf_version: "0.2"
title: {title}
description: Project knowledge capture bundle — institutional memory as an OKF graph.
timestamp: {utc_now()}
tags: [pkc, okf, knowledge]
---

# {title}

Continuous capture of meetings, experiments, discoveries, decisions, and work artifacts.

## Catalogs

{catalogs_md}

## Change log

See [log.md](/log.md).
"""
        index.write_text(content, encoding="utf-8")
    if not (bundle / "log.md").is_file():
        append_log(bundle, "Bundle created for Project Knowledge Capture")
    for cat in CATALOGS:
        ensure_catalog_index(bundle, cat)


def add_typed_link(
    concept_path: Path,
    target: str,
    rel: str,
    *,
    also_body: bool = True,
    body_label: str | None = None,
) -> str:
    if not concept_path.is_file():
        return "error"
    text = concept_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    links = fm.get("links") or []
    if not isinstance(links, list):
        links = []
    links = [l for l in links if isinstance(l, dict)]
    target_norm = target if target.startswith("/") else "/" + target
    for link in links:
        if link.get("target") == target_norm and link.get("rel") == rel:
            return "exists"
    links.append({"target": target_norm, "rel": rel})
    fm["links"] = links
    if also_body:
        label = body_label or Path(target_norm).stem.replace("-", " ").title()
        md_link = f"[{label}]({target_norm})"
        if target_norm not in body and md_link not in body:
            if "## Related" not in body and "## Links" not in body:
                body = body.rstrip() + f"\n\n## Related\n\n- {md_link} (`{rel}`)\n"
            else:
                body = body.rstrip() + f"\n- {md_link} (`{rel}`)\n"
    concept_path.write_text(dump_frontmatter(fm) + "\n" + body.rstrip() + "\n", encoding="utf-8")
    return "created"


def content_fingerprint(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:12]


def concept_ref(value: str, default_dir: str) -> str:
    """Normalize a concept reference to an absolute in-bundle path.

    Accepts an absolute path (`/features/x.md`), a relative path
    (`features/x.md`), or a bare title (`User Authentication`) which is
    slugified into `default_dir`.

    Exists because callers used to do `t if t.startswith("/") else
    f"/{dir}/{slugify(t)}.md"`, which mangles a relative path:
    slugify strips `/` and `.`, so `features/user-auth.md` became
    `featuresuser-authmd`. Paths are the natural thing to pass, since every
    other command takes them.
    """
    v = value.strip()
    if v.startswith("/"):
        return v
    if "/" in v or v.endswith(".md"):
        return "/" + v.lstrip("./")
    return f"/{default_dir}/{slugify(v)}.md"


def path_for_type(concept_type: str, slug: str) -> str:
    directory = TYPE_TO_DIR.get(concept_type, "knowledge")
    return f"{directory}/{slug}.md"


def iter_concepts(bundle: Path) -> list[Path]:
    files: list[Path] = []
    skip_names = {"index.md", "log.md"}
    for p in sorted(bundle.rglob("*.md")):
        if p.name in skip_names:
            continue
        if "packs" in p.parts:
            continue
        files.append(p)
    return files


def parse_iso_date(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKC common utilities CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init-bundle")
    p_init.add_argument("--bundle", default="knowledge")
    p_init.add_argument("--title", default="Project Knowledge")
    p_init.add_argument("--repo", default=".")
    p_slug = sub.add_parser("slugify")
    p_slug.add_argument("text")
    p_root = sub.add_parser("resolve-root")
    p_root.add_argument("--repo", default=".")
    p_root.add_argument("--override", default=None)
    p_scrub = sub.add_parser("scrub")
    p_scrub.add_argument("--text", default=None)
    p_scrub.add_argument("--no-pii", action="store_true")
    p_scrub.add_argument("--file", default=None)
    args = parser.parse_args(argv)
    if args.cmd == "init-bundle":
        repo = Path(args.repo).resolve()
        bundle = resolve_knowledge_root(repo, args.bundle)
        ensure_bundle(bundle, args.title)
        print(bundle)
        return 0
    if args.cmd == "slugify":
        print(slugify(args.text))
        return 0
    if args.cmd == "resolve-root":
        print(resolve_knowledge_root(Path(args.repo).resolve(), args.override))
        return 0
    if args.cmd == "scrub":
        if args.file:
            raw = Path(args.file).read_text(encoding="utf-8")
        elif args.text is not None:
            raw = args.text
        else:
            raw = sys.stdin.read()
        clean, labels = scrub_text(raw, pii=not args.no_pii, secrets=True)
        if labels:
            print(f"# redacted: {', '.join(labels)}", file=sys.stderr)
        sys.stdout.write(clean)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
