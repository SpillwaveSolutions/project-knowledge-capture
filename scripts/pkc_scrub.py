#!/usr/bin/env python3
"""Scrub secrets and optional PII from text before writing knowledge concepts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import scrub_text  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redact secrets/PII from notes")
    parser.add_argument("--file", default=None)
    parser.add_argument("--text", default=None)
    parser.add_argument("--no-pii", action="store_true", help="Only scrub secrets, keep emails/phones")
    parser.add_argument("--out", default=None, help="Write cleaned text to file")
    parser.add_argument("--report", action="store_true", help="Print redaction labels to stdout as JSON header")
    args = parser.parse_args(argv)

    if args.file:
        raw = Path(args.file).read_text(encoding="utf-8")
    elif args.text is not None:
        raw = args.text
    else:
        raw = sys.stdin.read()

    clean, labels = scrub_text(raw, pii=not args.no_pii, secrets=True)
    if args.report:
        import json

        print(json.dumps({"redacted": labels, "count": len(labels)}))
    if args.out:
        Path(args.out).write_text(clean, encoding="utf-8")
        print(f"Wrote {args.out}" + (f" (redacted {len(labels)})" if labels else ""), file=sys.stderr)
    else:
        sys.stdout.write(clean)
    return 0


if __name__ == "__main__":
    sys.exit(main())
