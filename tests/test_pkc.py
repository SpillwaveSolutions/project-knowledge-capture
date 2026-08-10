#!/usr/bin/env python3
"""Plain-assert tests for PKC helpers (no pytest required)."""

from __future__ import annotations

import contextlib
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
    dump_frontmatter,
    ensure_bundle,
    iter_concepts,
    parse_frontmatter,
    path_for_type,
    slugify,
    write_concept,
)


class TestFrontmatterRoundTrip(unittest.TestCase):
    """parse(dump(x)) == x.

    Regression: `_fmt_scalar` escaped backslashes and quotes on write, `_scalar`
    stripped only the surrounding quotes on read. Every write-modify-write cycle
    re-escaped already-escaped text, doubling the backslash count each pass, so
    a script that edited one field corrupted every quoted string in the file.
    Self-concealing too: reading back with the same parser looked correct.
    """

    VALUES = ['[{"a":"b"}]', "back\\slash", 'quote"inside', 'both\\"mixed', ":colon", "plain"]

    def test_single_round_trip_is_identity(self):
        for v in self.VALUES:
            with self.subTest(value=v):
                fm = {"type": "Concept", "title": "T", "v": v}
                self.assertEqual(parse_frontmatter(dump_frontmatter(fm))[0]["v"], v)

    def test_repeated_round_trips_do_not_grow(self):
        fm = {"type": "Concept", "title": "T", "sources_json": '[{"a":"b"}]'}
        first = None
        for _ in range(5):
            text = dump_frontmatter(fm)
            line = [l for l in text.splitlines() if l.startswith("sources_json")][0]
            if first is None:
                first = line
            self.assertEqual(line, first, "escaping grew across a round trip")
            fm, _ = parse_frontmatter(text)


def mtimes(bundle: Path) -> dict[str, int]:
    """Concept path -> mtime_ns. Uses iter_concepts so the generated catalog
    indexes and log.md — which are rewritten every run by design — stay out."""
    return {str(p.relative_to(bundle)): p.stat().st_mtime_ns for p in iter_concepts(bundle)}
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


class TestIncrementalMaterialize(unittest.TestCase):
    """Unchanged worklog items must be skipped without re-rendering the concept."""

    ITEM = {
        "id": "01KTEST000000000000000INCR",
        "title": "Incremental demo",
        "level": "story",
        "kind": "feature",
        "status": "todo",
        "body": "Original body.",
        "updated_at": "2026-08-05T00:00:00Z",
    }

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bundle = self.tmp / "knowledge"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_fold(self, item):
        """Materialize a one-item fold; returns the parsed --json report."""
        fold = self.tmp / "fold.json"
        fold.write_text(json.dumps([item]), encoding="utf-8")
        out = self.tmp / "report.json"
        with out.open("w") as fh, contextlib.redirect_stdout(fh):
            rc = materialize_main(
                ["--repo", str(self.tmp), "--bundle", "knowledge", "--json",
                 "--fold", str(fold), "--include", "features,tickets"]
            )
        self.assertEqual(rc, 0)
        return json.loads(out.read_text())["results"]

    def feature_file(self):
        hits = [p for p in (self.bundle / "features").glob("*.md") if p.name != "index.md"]
        self.assertEqual(len(hits), 1, hits)
        return hits[0]

    def test_records_source_fingerprint(self):
        self.run_fold(dict(self.ITEM))
        fm, _ = parse_frontmatter(self.feature_file().read_text(encoding="utf-8"))
        self.assertTrue(fm.get("source_fingerprint"), "concept must record the item fingerprint")

    def test_unchanged_item_skips_without_rendering(self):
        self.run_fold(dict(self.ITEM))
        import pkc_materialize

        calls = []
        original = pkc_materialize.write_concept

        def counting(*args, **kwargs):
            calls.append(args[1])
            return original(*args, **kwargs)

        pkc_materialize.write_concept = counting
        try:
            self.run_fold(dict(self.ITEM))
        finally:
            pkc_materialize.write_concept = original
        self.assertEqual(calls, [], "unchanged item must not reach write_concept")

    def test_changed_field_rerenders(self):
        self.run_fold(dict(self.ITEM))
        before = parse_frontmatter(self.feature_file().read_text(encoding="utf-8"))[0]
        changed = {**self.ITEM, "title": "Incremental demo", "body": "Rewritten body."}
        self.run_fold(changed)
        after_text = self.feature_file().read_text(encoding="utf-8")
        after = parse_frontmatter(after_text)[0]
        self.assertNotEqual(before.get("source_fingerprint"), after.get("source_fingerprint"))
        self.assertIn("Rewritten body.", after_text)

    def test_rerun_reports_unchanged_not_skipped(self):
        """Short-circuited items report `unchanged`, distinct from `skipped`.

        Neither mtimes nor `0 created` can prove incremental materialize
        works: write_concept() already declined to write byte-identical
        content before the fingerprint existed, so both were true either
        way. A distinct action label is the only signal visible from
        outside the process -- which is what CI needs.
        """
        self.run_fold(dict(self.ITEM))
        report = self.run_fold(dict(self.ITEM))
        actions = {r["action"] for r in report}
        self.assertEqual(actions, {"unchanged"}, f"expected all unchanged, got {actions}")

    def test_rerun_touches_no_files(self):
        """Guards write_concept's byte-compare, NOT the fingerprint skip.

        This passes with the fingerprint short-circuit removed -- verified.
        Kept because it catches a different regression: materialize starting
        to rewrite files whose content did not change.
        """
        self.run_fold(dict(self.ITEM))
        before = mtimes(self.bundle)
        self.assertTrue(before, "expected concepts on disk after the first run")
        self.run_fold(dict(self.ITEM))
        self.assertEqual(before, mtimes(self.bundle), "re-materialize rewrote files")


class TestConceptRef(unittest.TestCase):
    """Capture flags accept a path or a bare name; slugify must not eat paths."""

    def test_absolute_path_passes_through(self):
        from pkc_common import concept_ref

        self.assertEqual(concept_ref("/features/x.md", "features"), "/features/x.md")

    def test_relative_path_is_not_slugified(self):
        from pkc_common import concept_ref

        # the bug: slugify("features/user-auth.md") -> "featuresuser-authmd"
        self.assertEqual(
            concept_ref("features/user-authentication.md", "decisions"),
            "/features/user-authentication.md",
        )

    def test_bare_name_lands_in_the_default_dir(self):
        from pkc_common import concept_ref

        self.assertEqual(
            concept_ref("User Authentication", "features"), "/features/user-authentication.md"
        )

    def test_bare_name_with_md_suffix_is_treated_as_a_path(self):
        from pkc_common import concept_ref

        self.assertEqual(concept_ref("x.md", "features"), "/x.md")


class TestRiskAndAcceptance(unittest.TestCase):
    """Risk and Acceptance are first-class concepts, not free-form Markdown."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        ensure_bundle(self.tmp, "Test")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_types_map_to_their_own_catalogs(self):
        self.assertEqual(path_for_type("Risk", "x"), "risks/x.md")
        self.assertEqual(path_for_type("Acceptance", "x"), "acceptance/x.md")

    def test_new_relations_are_known(self):
        from pkc_common import DEFAULT_RELATIONS

        for rel in ("mitigates", "exposes"):
            self.assertIn(rel, DEFAULT_RELATIONS)

    def test_ensure_bundle_creates_both_catalogs(self):
        for cat in ("risks", "acceptance"):
            self.assertTrue((self.tmp / cat / "index.md").is_file(), cat)

    def test_capture_risk_writes_a_valid_concept(self):
        from pkc_capture import capture_risk

        write_concept(
            self.tmp,
            "decisions/use-jwt-for-session.md",
            {"type": "DecisionRecord", "title": "Use JWT", "description": "d",
             "timestamp": "2026-08-03T00:00:00Z", "status": "accepted"},
            "# Use JWT\n",
            merge=False,
        )

        results = capture_risk(
            self.tmp,
            title="Token replay after logout",
            statement="A stolen access token stays valid until it expires.",
            severity="high",
            exposes=["features/user-authentication.md"],
            mitigated_by=["decisions/use-jwt-for-session.md"],
        )
        rel, action = results[0]
        self.assertEqual(action, "created")
        fm, body = parse_frontmatter((self.tmp / rel).read_text(encoding="utf-8"))
        self.assertEqual(fm["type"], "Risk")
        self.assertEqual(fm["severity"], "high")
        self.assertIn(
            ("exposes", "/features/user-authentication.md"),
            {(l["rel"], l["target"]) for l in fm["links"]},
        )
        self.assertIn("stolen access token", body)
        # the mitigation edge belongs on the decision, pointing back at the risk
        dfm, _ = parse_frontmatter(
            (self.tmp / "decisions/use-jwt-for-session.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            ("mitigates", f"/{rel}"), {(l["rel"], l["target"]) for l in dfm["links"]}
        )

    def test_capture_acceptance_writes_a_valid_concept(self):
        from pkc_capture import capture_acceptance

        write_concept(
            self.tmp,
            "features/user-authentication.md",
            {"type": "Feature", "title": "Auth", "description": "d",
             "timestamp": "2026-08-03T00:00:00Z"},
            "# Auth\n",
            merge=False,
        )

        results = capture_acceptance(
            self.tmp,
            title="Session expires within 15 minutes",
            criterion="An access token is rejected 15 minutes after issue.",
            satisfies="features/user-authentication.md",
            verified_by=["code/pr-12-jwt-middleware.md"],
        )
        rel, action = results[0]
        self.assertEqual(action, "created")
        fm, _ = parse_frontmatter((self.tmp / rel).read_text(encoding="utf-8"))
        self.assertEqual(fm["type"], "Acceptance")
        rels = {(l["rel"], l["target"]) for l in fm["links"]}
        self.assertIn(("satisfies", "/features/user-authentication.md"), rels)
        self.assertIn(("verified_by", "/code/pr-12-jwt-middleware.md"), rels)
        # pack() walks outbound only, so the Feature must point back or the
        # criterion never appears in that Feature's context pack
        ffm, _ = parse_frontmatter(
            (self.tmp / "features/user-authentication.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            ("verified_by", f"/{rel}"), {(l["rel"], l["target"]) for l in ffm["links"]}
        )

    def test_captures_are_idempotent(self):
        from pkc_capture import capture_risk

        kw = dict(title="Same risk", statement="Same statement.")
        self.assertEqual(capture_risk(self.tmp, **kw)[0][1], "created")
        self.assertEqual(capture_risk(self.tmp, **kw)[0][1], "skipped")


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


from pkc_pack import pack, resolve_concept  # noqa: E402
from pkc_validate import validate_bundle  # noqa: E402
from pkc_action_items import extract_action_items  # noqa: E402


class TestValidate(unittest.TestCase):
    def test_sample_passes(self):
        errors, warnings = validate_bundle(ROOT / "sample-knowledge")
        self.assertEqual(errors, [], errors)


class TestPack(unittest.TestCase):
    def test_feature_pack_has_decision(self):
        bundle = ROOT / "sample-knowledge"
        seed = resolve_concept(bundle, "features/user-authentication.md")
        result = pack(bundle, seed, hops=2, max_nodes=20)
        self.assertGreaterEqual(result["node_count"], 5)
        types = {n["type"] for n in result["nodes"]}
        self.assertIn("DecisionRecord", types)
        self.assertIn("Meeting", types)


class TestActionItems(unittest.TestCase):
    def test_extract_from_sample_meeting(self):
        text = (ROOT / "sample-knowledge/meetings/2026-08-03-auth-design.md").read_text()
        from pkc_common import parse_frontmatter
        _, body = parse_frontmatter(text)
        items = extract_action_items(body)
        self.assertGreaterEqual(len(items), 2)
        titles = " ".join(i["title"].lower() for i in items)
        self.assertIn("jwt", titles)


from pkc_doctor import doctor  # noqa: E402
from pkc_common import scrub_text  # noqa: E402
from pkc_transcript import normalize as normalize_transcript  # noqa: E402
from pkc_pr_capture import materialize_pr  # noqa: E402
from pkc_capture import capture_assumption, capture_question  # noqa: E402
import json


class TestDoctor(unittest.TestCase):
    def test_sample_doctor_runs(self):
        result = doctor(ROOT / "sample-knowledge", stale_days=90)
        self.assertIn("issues", result)
        self.assertGreaterEqual(result["node_count"], 8)
        kinds = {i["kind"] for i in result["issues"]}
        # open question should surface
        self.assertTrue("open_question" in kinds or any("question" in i["message"].lower() for i in result["issues"]))


class TestScrub(unittest.TestCase):
    def test_github_token(self):
        clean, labels = scrub_text("token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345 and a@b.com")
        self.assertNotIn("ghp_", clean)
        self.assertIn("[REDACTED", clean)


class TestTranscript(unittest.TestCase):
    def test_speaker_lines(self):
        raw = (ROOT / "tests/fixtures/transcript_speakers.txt").read_text()
        result = normalize_transcript(raw, title="T", date="2026-08-03")
        self.assertEqual(result["format"], "speaker_lines")
        self.assertIn("REDACTED", " ".join(result["redactions"]) or result["notes"])


class TestPRCapture(unittest.TestCase):
    def test_fixture_pr(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            ensure_bundle(tmp, "T")
            pr = json.loads((ROOT / "tests/fixtures/pr.json").read_text())
            rel, action = materialize_pr(tmp, pr, implements=["user-authentication"])
            self.assertEqual(action, "created")
            self.assertTrue((tmp / rel).is_file())
        finally:
            shutil.rmtree(tmp)


class TestAssumptionQuestion(unittest.TestCase):
    def test_capture(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            ensure_bundle(tmp, "T")
            a = capture_assumption(tmp, title="A1", statement="S", assumes_for=["feat"])
            q = capture_question(tmp, title="Q1", question="Why?", blocks=["feat"])
            self.assertTrue(a[0][0].startswith("assumptions/"))
            self.assertTrue(q[0][0].startswith("questions/"))
        finally:
            shutil.rmtree(tmp)


class TestTinyPack(unittest.TestCase):
    def test_tiny_bounds(self):
        bundle = ROOT / "sample-knowledge"
        seed = resolve_concept(bundle, "features/user-authentication.md")
        result = pack(bundle, seed, hops=1, max_nodes=8)
        self.assertLessEqual(result["node_count"], 8)
        self.assertEqual(result["hops"], 1)


from pkc_search import search  # noqa: E402
from pkc_digest import collect as digest_collect  # noqa: E402
from pkc_release_notes import notes_for_release, load_nodes  # noqa: E402
from pkc_thread import normalize_thread  # noqa: E402
from pkc_federate import federated_search, list_roots  # noqa: E402
from pkc_adr_import import import_dir  # noqa: E402


class TestSearch(unittest.TestCase):
    def test_jwt_hits(self):
        hits = search(ROOT / "sample-knowledge", "JWT", limit=10)
        self.assertGreaterEqual(len(hits), 1)
        self.assertTrue(any("jwt" in h["title"].lower() or "jwt" in h["path"].lower() for h in hits))


class TestDigest(unittest.TestCase):
    def test_digest_has_sections(self):
        data = digest_collect(ROOT / "sample-knowledge", days=3650)
        self.assertIn("recent", data)
        self.assertIn("open_questions", data)
        self.assertTrue(len(data["open_questions"]) >= 1)


class TestReleaseNotes(unittest.TestCase):
    def test_release_pack(self):
        nodes = load_nodes(ROOT / "sample-knowledge")
        releases = [p for p, n in nodes.items() if n["type"] == "Release"]
        self.assertTrue(releases)
        pack = notes_for_release(nodes, releases[0])
        self.assertIn("features", pack)


class TestThread(unittest.TestCase):
    def test_slack_fixture(self):
        raw = (ROOT / "tests/fixtures/thread_slack.txt").read_text()
        result = normalize_thread(raw, title="T")
        self.assertTrue(result["attendees"])
        self.assertTrue(result["redactions"] or "REDACTED" in result["notes"])


class TestFederate(unittest.TestCase):
    def test_remote_search(self):
        # write temp config pointing at fixture remote
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / ".pkc").mkdir()
            remote = ROOT / "tests/fixtures/remote-knowledge"
            (tmp / ".pkc" / "config.yml").write_text(
                f"pkc:\n  knowledge_root: knowledge\n  federation:\n    - name: remote\n      path: {remote}\n"
            )
            # local bundle
            ensure_bundle(tmp / "knowledge", "Local")
            roots = list_roots(tmp)
            self.assertTrue(any(r["name"] == "remote" and r["exists"] for r in roots))
            hits = federated_search(tmp, "caching", limit=10)
            self.assertTrue(any(h.get("federation") == "remote" for h in hits))
        finally:
            shutil.rmtree(tmp)


class TestAdrImport(unittest.TestCase):
    def test_import_fixture(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            ensure_bundle(tmp, "T")
            results = import_dir(tmp, ROOT / "tests/fixtures/adr", dry_run=False)
            self.assertGreaterEqual(len(results), 1)
            self.assertTrue((tmp / results[0][0]).is_file())
        finally:
            shutil.rmtree(tmp)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
