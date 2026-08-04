#!/usr/bin/env python3
"""Plain-assert tests for PKC helpers (no pytest required)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pkc_common import (  # noqa: E402
    add_typed_link,
    ensure_bundle,
    parse_frontmatter,
    path_for_type,
    slugify,
    write_concept,
)
from pkc_capture import capture_decision, capture_meeting  # noqa: E402
from pkc_materialize import main as materialize_main  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Use JWT for Session!"), "use-jwt-for-session")

    def test_empty(self):
        self.assertEqual(slugify("???"), "untitled")


class TestWriteConcept(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        ensure_bundle(self.tmp, "Test")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_create_and_idempotent_skip(self):
        rel = path_for_type("Feature", "demo")
        fm = {
            "type": "Feature",
            "title": "Demo",
            "description": "d",
            "timestamp": "2026-08-03T00:00:00Z",
            "stable_timestamp": True,
        }
        _, a1 = write_concept(self.tmp, rel, dict(fm), "# Demo\n")
        self.assertEqual(a1, "created")
        _, a2 = write_concept(self.tmp, rel, dict(fm), "# Demo\n")
        self.assertEqual(a2, "skipped")

    def test_truth_state_skip(self):
        rel = "decisions/frozen.md"
        write_concept(
            self.tmp,
            rel,
            {
                "type": "DecisionRecord",
                "title": "Frozen",
                "description": "x",
                "timestamp": "2026-01-01T00:00:00Z",
                "truth_state": "snapshot",
                "status": "accepted",
            },
            "# Frozen\n",
            merge=False,
        )
        _, action = write_concept(
            self.tmp,
            rel,
            {
                "type": "DecisionRecord",
                "title": "Frozen",
                "description": "changed",
                "timestamp": "2026-08-03T00:00:00Z",
                "truth_state": "current",
                "status": "accepted",
            },
            "# Changed\n",
        )
        self.assertEqual(action, "skipped")
        text = (self.tmp / rel).read_text(encoding="utf-8")
        self.assertIn("snapshot", text)
        self.assertNotIn("# Changed", text)


class TestCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        ensure_bundle(self.tmp, "Test")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_meeting_with_decision(self):
        results = capture_meeting(
            self.tmp,
            title="Auth design",
            date="2026-08-03",
            attendees=["rick"],
            notes="We picked JWT.",
            decisions=["Use JWT for session management"],
        )
        paths = {r[0] for r in results}
        self.assertTrue(any(p.startswith("meetings/") for p in paths))
        self.assertTrue(any(p.startswith("decisions/") for p in paths))
        meet = next(p for p, _ in results if p.startswith("meetings/"))
        fm, _ = parse_frontmatter((self.tmp / meet).read_text(encoding="utf-8"))
        self.assertEqual(fm["type"], "Meeting")
        self.assertTrue(fm.get("links"))

    def test_decision_links(self):
        results = capture_decision(
            self.tmp,
            title="Use JWT",
            context="scale",
            decision="JWT",
            consequences="refresh needed",
            decides=["user-authentication"],
        )
        rel = results[0][0]
        fm, body = parse_frontmatter((self.tmp / rel).read_text(encoding="utf-8"))
        self.assertEqual(fm["type"], "DecisionRecord")
        self.assertTrue(any(l.get("rel") == "decides" for l in fm.get("links") or []))
        self.assertIn("user-authentication", body)


class TestLink(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        ensure_bundle(self.tmp, "Test")
        write_concept(
            self.tmp,
            "features/a.md",
            {"type": "Feature", "title": "A", "description": "a", "timestamp": "2026-08-03T00:00:00Z"},
            "# A\n",
            merge=False,
        )
        write_concept(
            self.tmp,
            "decisions/b.md",
            {
                "type": "DecisionRecord",
                "title": "B",
                "description": "b",
                "timestamp": "2026-08-03T00:00:00Z",
                "status": "accepted",
            },
            "# B\n",
            merge=False,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_add_link(self):
        action = add_typed_link(self.tmp / "decisions/b.md", "/features/a.md", "decides")
        self.assertEqual(action, "created")
        action2 = add_typed_link(self.tmp / "decisions/b.md", "/features/a.md", "decides")
        self.assertEqual(action2, "exists")


class TestMaterialize(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bundle = self.tmp / "knowledge"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_fold_materialize(self):
        fold = ROOT / "tests" / "fixtures" / "fold.json"
        rc = materialize_main(
            [
                "--repo",
                str(self.tmp),
                "--bundle",
                "knowledge",
                "--fold",
                str(fold),
                "--include",
                "features,tickets",
            ]
        )
        self.assertEqual(rc, 0)
        features = list((self.bundle / "features").glob("*.md"))
        features = [p for p in features if p.name != "index.md"]
        tickets = [p for p in (self.bundle / "tickets").glob("*.md") if p.name != "index.md"]
        # epic + story → 2 features; epic + story + task → 3 tickets; cancelled skipped
        self.assertEqual(len(features), 2)
        self.assertEqual(len(tickets), 3)
        # idempotent
        rc2 = materialize_main(
            [
                "--repo",
                str(self.tmp),
                "--bundle",
                "knowledge",
                "--fold",
                str(fold),
                "--include",
                "features,tickets",
            ]
        )
        self.assertEqual(rc2, 0)
        features2 = [p for p in (self.bundle / "features").glob("*.md") if p.name != "index.md"]
        self.assertEqual(len(features2), 2)


class TestSampleKnowledge(unittest.TestCase):
    def test_chain_files_exist(self):
        sk = ROOT / "sample-knowledge"
        required = [
            "index.md",
            "meetings/2026-08-03-auth-design.md",
            "experiments/jwt-vs-cookie.md",
            "decisions/use-jwt-for-session.md",
            "features/user-authentication.md",
        ]
        for rel in required:
            self.assertTrue((sk / rel).is_file(), rel)
        fm, _ = parse_frontmatter((sk / "decisions/use-jwt-for-session.md").read_text())
        rels = { (l.get("rel"), l.get("target")) for l in fm.get("links") or [] }
        self.assertIn(("decides", "/features/user-authentication.md"), rels)
        self.assertIn(("originates_from", "/meetings/2026-08-03-auth-design.md"), rels)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
