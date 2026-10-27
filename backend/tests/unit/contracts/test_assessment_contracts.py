"""Standard-library tests for the versioned assessment contracts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = ROOT / "contracts" / "v1"
EXAMPLES = ROOT / "contracts" / "examples" / "v1"


class AssessmentContractTests(unittest.TestCase):
    def test_all_versioned_schemas_have_stable_metadata(self) -> None:
        expected_titles = {
            "start_assessment_request.schema.json": "Start assessment request",
            "start_assessment_response.schema.json": "Start assessment response",
            "subject_summary_request.schema.json": "Subject summary request",
            "subject_summary_response.schema.json": "Subject summary response",
            "submit_attempt_request.schema.json": "Submit assessment attempt request",
            "submit_attempt_response.schema.json": "Submit assessment attempt response",
            "tutor_request.schema.json": "Tutor support request",
            "tutor_response.schema.json": "Tutor support response",
            "weak_area_quiz_request.schema.json": "Weak-area quiz request",
            "weak_area_quiz_response.schema.json": "Weak-area quiz response",
        }

        for filename, title in expected_titles.items():
            schema = self._load_contract(filename)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertTrue(schema["$id"].startswith("adapted/contracts/v1/"))
            self.assertEqual(schema["title"], title)
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])

    def test_riya_example_matches_contracts_and_shows_foundation_support(self) -> None:
        example = self._load_example("riya_assessment.json")
        self._assert_assessment_example_matches_contracts(example)

        submit_response = example["submit"]["response"]
        recommendation = submit_response["recommendation"]
        references = submit_response["evidence_references"]

        self.assertEqual(example["scenario"]["expected_next_action"], "prerequisite_support")
        self.assertEqual(submit_response["gap_status"], "prerequisite_blocked")
        self.assertTrue(recommendation["teacher_review_required"])
        self.assertEqual(recommendation["target_concept_id"], "ALG-DIST-01")
        self.assertIn("dist-riya-1", recommendation["evidence_reference_ids"])
        self.assertIn("dist-riya-2", recommendation["evidence_reference_ids"])
        self.assertEqual(
            {reference["misconception"] for reference in references if reference["misconception"]},
            {"negative sign not distributed"},
        )

    def test_arjun_example_matches_contracts_and_shows_transfer_practice(self) -> None:
        example = self._load_example("arjun_assessment.json")
        self._assert_assessment_example_matches_contracts(example)

        submit_response = example["submit"]["response"]
        recommendation = submit_response["recommendation"]

        self.assertEqual(example["scenario"]["expected_next_action"], "transfer_practice")
        self.assertEqual(submit_response["gap_status"], "secure")
        self.assertEqual(recommendation["action_type"], "transfer_practice")
        self.assertFalse(recommendation["teacher_review_required"])
        self.assertEqual(submit_response["mastery"]["evidence_count"], 4)
        self.assertEqual(submit_response["mastery"]["independence_score"], 1.0)

    def test_riya_subject_summary_example_preserves_concept_drilldown(self) -> None:
        example = self._load_example("riya_subject_summary.json")
        self.assertTrue(example["scenario"]["synthetic"])

        self._assert_matches_schema(
            example["request"],
            self._load_contract("subject_summary_request.schema.json"),
        )
        self._assert_matches_schema(
            example["response"],
            self._load_contract("subject_summary_response.schema.json"),
        )

        response = example["response"]
        self.assertEqual(response["summary"]["evidence_count"], 3)
        self.assertEqual(response["summary"]["assessed_concept_count"], 2)
        self.assertEqual(len(response["concepts"]), 3)
        self.assertEqual(response["concepts"][1]["gap_status"], "prerequisite_blocked")
        self.assertEqual(
            response["concepts"][1]["recommendation"]["target_concept_id"],
            "ALG-DIST-01",
        )

    def test_riya_learning_support_example_is_grounded_and_answer_safe(self) -> None:
        example = self._load_example("riya_learning_support.json")
        self.assertTrue(example["scenario"]["synthetic"])

        self._assert_matches_schema(
            example["tutor"]["request"],
            self._load_contract("tutor_request.schema.json"),
        )
        self._assert_matches_schema(
            example["tutor"]["response"],
            self._load_contract("tutor_response.schema.json"),
        )
        self._assert_matches_schema(
            example["quiz"]["request"],
            self._load_contract("weak_area_quiz_request.schema.json"),
        )
        self._assert_matches_schema(
            example["quiz"]["response"],
            self._load_contract("weak_area_quiz_response.schema.json"),
        )

        tutor_response = example["tutor"]["response"]
        quiz_response = example["quiz"]["response"]
        self.assertFalse(tutor_response["answer_revealed"])
        self.assertFalse(tutor_response["fallback_used"])
        self.assertEqual(tutor_response["source_ids"], ["lesson-algebra-distributive-01"])
        self.assertEqual(quiz_response["concept_id"] if "concept_id" in quiz_response else quiz_response["concept"]["id"], "ALG-DIST-01")
        self.assertTrue(all("answer" not in item for item in quiz_response["items"]))
        self.assertTrue(quiz_response["items"][-1]["is_transfer"])

    def _assert_assessment_example_matches_contracts(self, example: dict[str, Any]) -> None:
        self.assertTrue(example["scenario"]["synthetic"])

        start_request = example["start"]["request"]
        start_response = example["start"]["response"]
        submit_request = example["submit"]["request"]
        submit_response = example["submit"]["response"]

        self._assert_matches_schema(
            start_request,
            self._load_contract("start_assessment_request.schema.json"),
        )
        self._assert_matches_schema(
            start_response,
            self._load_contract("start_assessment_response.schema.json"),
        )
        self._assert_matches_schema(
            submit_request,
            self._load_contract("submit_attempt_request.schema.json"),
        )
        self._assert_matches_schema(
            submit_response,
            self._load_contract("submit_attempt_response.schema.json"),
        )

        self.assertEqual(start_response["session"]["learner_id"], start_request["learner_id"])
        self.assertEqual(start_response["session"]["subject_id"], start_request["subject_id"])
        self.assertEqual(start_response["subject"]["id"], start_request["subject_id"])
        self.assertEqual(start_response["session"]["current_concept_id"], start_response["concept"]["id"])
        self.assertEqual(start_response["concept"]["subject_id"], start_response["subject"]["id"])
        self.assertEqual(start_response["item"]["concept_id"], start_response["concept"]["id"])
        self.assertNotIn("answer", start_response["item"])

        self.assertEqual(submit_response["learner_id"], submit_request["learner_id"])
        self.assertEqual(submit_response["session"]["id"], submit_request["session_id"])
        self.assertEqual(submit_response["session"]["learner_id"], submit_request["learner_id"])
        self.assertEqual(submit_response["subject"]["id"], submit_response["session"]["subject_id"])
        self.assertEqual(submit_response["concept"]["id"], submit_request["attempt"]["concept_id"])
        self.assertEqual(submit_response["item"]["id"], submit_request["attempt"]["item_id"])
        self.assertEqual(submit_response["item"]["concept_id"], submit_response["concept"]["id"])
        self.assertEqual(submit_response["evidence"]["item_id"], submit_response["item"]["id"])
        self.assertEqual(submit_response["evidence"]["concept_id"], submit_response["concept"]["id"])
        self.assertEqual(submit_response["mastery"]["concept_id"], submit_response["concept"]["id"])
        self.assertEqual(
            submit_response["recommendation"]["target_concept_id"],
            submit_response["session"]["current_concept_id"],
        )

        reference_ids = {reference["id"] for reference in submit_response["evidence_references"]}
        self.assertTrue(
            set(submit_response["recommendation"]["evidence_reference_ids"]).issubset(reference_ids)
        )
        self.assertTrue(
            any(reference["id"] == submit_response["evidence"]["id"] for reference in submit_response["evidence_references"])
        )
        self.assertNotIn("answer", submit_response["item"])

    def _assert_matches_schema(
        self,
        value: Any,
        schema: dict[str, Any],
        *,
        path: str = "$",
        root_schema: dict[str, Any] | None = None,
    ) -> None:
        if root_schema is None:
            root_schema = schema
        if "$ref" in schema:
            reference = schema["$ref"]
            self.assertTrue(reference.startswith("#/$defs/"), f"unsupported reference at {path}")
            definition_name = reference.removeprefix("#/$defs/")
            self._assert_matches_schema(
                value,
                root_schema["$defs"][definition_name],
                path=path,
                root_schema=root_schema,
            )
            return

        if "const" in schema:
            self.assertEqual(value, schema["const"], path)
        if "enum" in schema:
            self.assertIn(value, schema["enum"], path)

        expected_types = schema.get("type")
        if expected_types is not None:
            allowed_types = expected_types if isinstance(expected_types, list) else [expected_types]
            self.assertTrue(
                any(self._is_json_type(value, json_type) for json_type in allowed_types),
                f"{path} has an invalid JSON type",
            )

        if isinstance(value, str):
            if "minLength" in schema:
                self.assertGreaterEqual(len(value), schema["minLength"], path)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema:
                self.assertGreaterEqual(value, schema["minimum"], path)
            if "maximum" in schema:
                self.assertLessEqual(value, schema["maximum"], path)
            if "exclusiveMinimum" in schema:
                self.assertGreater(value, schema["exclusiveMinimum"], path)

        if isinstance(value, dict):
            required = schema.get("required", [])
            for field_name in required:
                self.assertIn(field_name, value, f"missing {path}.{field_name}")
            if schema.get("additionalProperties") is False:
                self.assertTrue(
                    set(value).issubset(schema.get("properties", {})),
                    f"{path} contains an undocumented property",
                )
            for field_name, field_schema in schema.get("properties", {}).items():
                if field_name in value:
                    self._assert_matches_schema(
                        value[field_name],
                        field_schema,
                        path=f"{path}.{field_name}",
                        root_schema=root_schema,
                    )

        if isinstance(value, list) and "items" in schema:
            for index, item in enumerate(value):
                self._assert_matches_schema(
                    item,
                    schema["items"],
                    path=f"{path}[{index}]",
                    root_schema=root_schema,
                )

    @staticmethod
    def _is_json_type(value: Any, json_type: str) -> bool:
        if json_type == "object":
            return isinstance(value, dict)
        if json_type == "array":
            return isinstance(value, list)
        if json_type == "string":
            return isinstance(value, str)
        if json_type == "boolean":
            return isinstance(value, bool)
        if json_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if json_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if json_type == "null":
            return value is None
        raise AssertionError(f"unsupported JSON type in test harness: {json_type}")

    @staticmethod
    def _load_contract(filename: str) -> dict[str, Any]:
        return json.loads((CONTRACTS / filename).read_text(encoding="utf-8"))

    @staticmethod
    def _load_example(filename: str) -> dict[str, Any]:
        return json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
