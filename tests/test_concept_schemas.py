#!/usr/bin/env python3
"""Every registry concept has a schema. New fields stay optional."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "okf-concepts"

# Fields added in 0.10.1. None of these may become required.
NEW_FIELDS = {
    "Story": ["sprint", "release"],
    "UserStory": [
        "persona",
        "capability",
        "outcome",
        "priority",
        "acceptance_criteria",
        "requirement_ids",
    ],
    "Persona": ["role", "goals", "pain_points"],
    "JourneyStage": ["outcome", "success_metric", "order"],
    "UserJourney": ["goal", "trigger", "end_state", "golden_thread"],
    "Scenario": ["preconditions", "steps", "success_outcome"],
    "Release": ["version", "tag", "date"],
    "Requirement": ["priority"],
    "Discovery": ["source", "confidence"],
    "Experiment": ["hypothesis", "result", "conclusion", "related_code"],
}


class ConceptSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = json.loads((SCHEMA_DIR / "registry.json").read_text(encoding="utf-8"))
        cls.concepts = list(registry["concepts"])
        cls.schemas = {}
        for concept in cls.concepts:
            path = SCHEMA_DIR / f"{concept}.schema.json"
            cls.schemas[concept] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def test_every_registry_concept_has_a_schema_file(self):
        missing = [name for name, schema in self.schemas.items() if schema is None]
        self.assertEqual(missing, [])

    def test_schema_identity_matches_the_concept(self):
        for concept, schema in self.schemas.items():
            self.assertIsNotNone(schema, concept)
            self.assertEqual(schema["title"], concept)
            self.assertEqual(schema["properties"]["type"]["const"], concept)
            self.assertTrue(str(schema["$id"]).endswith(f"/{concept}.schema.json"))

    def test_only_type_and_title_are_required(self):
        for concept, schema in self.schemas.items():
            self.assertEqual(schema["required"], ["type", "title"], concept)
            self.assertIs(schema["additionalProperties"], True, concept)

    def test_new_fields_are_optional_properties(self):
        for concept, fields in NEW_FIELDS.items():
            schema = self.schemas[concept]
            for field in fields:
                self.assertIn(field, schema["properties"], f"{concept}.{field}")
                self.assertNotIn(field, schema["required"], f"{concept}.{field}")

    def test_old_story_without_sprint_or_release_still_meets_the_schema(self):
        schema = self.schemas["Story"]
        old = {"type": "Story", "title": "Save a claim", "level": "story", "kind": "feature"}
        for key in ("sprint", "release"):
            self.assertNotIn(key, old)
            self.assertIn(key, schema["properties"])
        missing = [key for key in schema["required"] if key not in old]
        self.assertEqual(missing, [])

    def test_release_and_requirement_documents_can_omit_the_new_fields(self):
        for concept in ("Release", "Requirement"):
            schema = self.schemas[concept]
            document = {"type": concept, "title": "Example"}
            missing = [key for key in schema["required"] if key not in document]
            self.assertEqual(missing, [])
            self.assertGreater(len(schema["properties"]), 2)


if __name__ == "__main__":
    unittest.main()
