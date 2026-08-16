#!/usr/bin/env python3
"""Isolation sessions must not clobber each other.

Public tests use only fictional project names.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "scripts" / "brain_session.py"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def run_session(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    import os
    run_env = os.environ.copy()
    if env is None:
        run_env.pop("SECOND_BRAIN_IDENTITY", None)
    else:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(SESSION), *args],
        capture_output=True,
        text=True,
        env=run_env,
    )


def test_isolation_two_sessions_do_not_clobber():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "brain"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "tester")
        knowledge = repo / "knowledge"
        knowledge.mkdir()
        (knowledge / "index.md").write_text("# Shared\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "seed")

        a = run_session(
            "open",
            "--repo",
            str(repo),
            "--bundle",
            "knowledge",
            "--actor",
            "claude-code/lumenfield-detector",
            "--host",
            "claude-code",
            "--project",
            "lumenfield-detector",
            "--plugin",
            "project-knowledge-capture",
        )
        assert a.returncode == 0, a.stdout + a.stderr
        sa = json.loads(a.stdout)
        b = run_session(
            "open",
            "--repo",
            str(repo),
            "--bundle",
            "knowledge",
            "--actor",
            "grok-bot/northstar-console",
            "--host",
            "grok-bot",
            "--project",
            "northstar-console",
            "--plugin",
            "project-knowledge-capture",
        )
        assert b.returncode == 0, b.stdout + b.stderr
        sb = json.loads(b.stdout)
        assert sa["branch"] != sb["branch"]
        assert sa["worktree"] != sb["worktree"]
        assert "lumenfield-detector" in sa["branch"]
        assert "northstar-console" in sb["branch"]

        Path(sa["bundle"]).mkdir(parents=True, exist_ok=True)
        Path(sb["bundle"]).mkdir(parents=True, exist_ok=True)
        (Path(sa["bundle"]) / "meetings").mkdir(exist_ok=True)
        (Path(sb["bundle"]) / "meetings").mkdir(exist_ok=True)
        (Path(sa["bundle"]) / "meetings" / "lumenfield-spike.md").write_text(
            "---\ntype: Meeting\ntitle: Lumenfield spike\n---\n", encoding="utf-8"
        )
        (Path(sb["bundle"]) / "meetings" / "northstar-layout.md").write_text(
            "---\ntype: Meeting\ntitle: Northstar layout\n---\n", encoding="utf-8"
        )

        assert (Path(sa["bundle"]) / "meetings" / "lumenfield-spike.md").exists()
        assert not (Path(sa["bundle"]) / "meetings" / "northstar-layout.md").exists()
        assert (Path(sb["bundle"]) / "meetings" / "northstar-layout.md").exists()
        assert not (Path(sb["bundle"]) / "meetings" / "lumenfield-spike.md").exists()

        ca = run_session("close", "--repo", str(repo), "--session", sa["session_id"], "--no-push", "--allow-local")
        assert ca.returncode == 0, ca.stdout + ca.stderr
        cb = run_session("close", "--repo", str(repo), "--session", sb["session_id"], "--no-push", "--allow-local")
        assert cb.returncode == 0, cb.stdout + cb.stderr

        git(repo, "merge", "--no-ff", sa["branch"], "-m", "merge lumenfield-detector")
        git(repo, "merge", "--no-ff", sb["branch"], "-m", "merge northstar-console")
        assert (knowledge / "meetings" / "lumenfield-spike.md").exists()
        assert (knowledge / "meetings" / "northstar-layout.md").exists()


def test_open_requires_identity():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "brain"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "tester")
        (repo / "knowledge").mkdir()
        (repo / "knowledge" / "index.md").write_text("# Shared\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "seed")
        r = run_session("open", "--repo", str(repo), "--bundle", "knowledge")
        assert r.returncode != 0
        data = json.loads(r.stdout)
        assert "identity" in data.get("error", "").lower()


if __name__ == "__main__":
    test_open_requires_identity()
    test_isolation_two_sessions_do_not_clobber()
    print("ok")
