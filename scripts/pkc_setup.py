#!/usr/bin/env python3
"""Consent-gated toolchain setup for PKC.

Detects ripgrep (and reports SQLite FTS5). May install ripgrep only when the
user passes `--yes`. Never invoke this from a hook (SessionStart / PostToolUse)
— a failed package install inside a hook blocks turns.

Usage:
  python3 scripts/pkc_setup.py --check
  python3 scripts/pkc_setup.py --install-rg          # print the command, exit 2
  python3 scripts/pkc_setup.py --install-rg --yes    # run the install
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkc_common import find_rg, rg_install_hints, toolchain_report  # noqa: E402


def render_check(report: dict) -> str:
    rg = report["rg"]
    sqlite = report["sqlite"]
    lines = [
        "# PKC setup",
        "",
        f"- Python: {report['python']}",
        f"- SQLite: {sqlite.get('version') or '?'}  FTS5: {'yes' if sqlite.get('fts5') else 'no'}",
    ]
    if rg["found"]:
        lines.append(f"- ripgrep: found at `{rg['path']}`")
        lines.append("")
        lines.append("Search and pack will use rg as a prefilter. No install needed.")
    else:
        lines.append("- ripgrep: **not found**")
        lines.append("")
        lines.append("PKC still works (full scan). rg is an accelerator, not a dependency.")
        lines.append("Install with one of:")
        for hint in rg["hints"]:
            lines.append(f"  `{hint}`")
        lines.append("")
        lines.append("Re-run with `--install-rg` to see the command, `--install-rg --yes` to run it.")
        lines.append("Do **not** run this from a hook.")
    lines.append("")
    return "\n".join(lines)


def install_rg(*, yes: bool) -> int:
    existing = find_rg()
    if existing:
        print(f"ripgrep already installed: {existing}")
        return 0
    hints = rg_install_hints()
    print("ripgrep is not on PATH. Suggested install (pick one):")
    for h in hints:
        print(f"  {h}")
    print()
    print("Never install from a SessionStart/PostToolUse hook.")
    if not yes:
        print("Refusing to install without --yes (consent-gated).")
        return 2
    cmd = hints[0]
    print(f"running: {cmd}")
    # Constant from our table, not user input.
    rc = subprocess.call(cmd, shell=True)
    if rc != 0:
        print(f"install failed (exit {rc}). Try another hint from the list.", file=sys.stderr)
        return rc
    found = find_rg() or shutil.which("rg")
    if not found:
        print("install finished but `rg` is still not on PATH. Open a new shell?", file=sys.stderr)
        return 1
    print(f"ripgrep installed: {found}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PKC toolchain setup (consent-gated ripgrep install)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report toolchain; never install (default)",
    )
    parser.add_argument(
        "--install-rg",
        action="store_true",
        help="Install ripgrep. Requires --yes. Never from a hook.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Consent to run the platform install command",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = toolchain_report()
    if args.install_rg:
        if args.json:
            payload = {
                **report,
                "action": "install-rg",
                "consented": bool(args.yes),
            }
            print(json.dumps(payload, indent=2))
        return install_rg(yes=args.yes)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_check(report))
    return 0 if report["rg"]["found"] else 0  # missing rg is not a failure


if __name__ == "__main__":
    raise SystemExit(main())
