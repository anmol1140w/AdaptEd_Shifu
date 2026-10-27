"""Smoke tests for the synthetic assessment demo command."""

from __future__ import annotations

import json
import unittest

from scripts.run_assessment_demo import run_demo


class AssessmentDemoTests(unittest.TestCase):
    def test_demo_runs_both_synthetic_paths_and_is_json_serializable(self) -> None:
        result = run_demo()
        encoded = json.dumps(result, default=self._json_default)
        decoded = json.loads(encoded)

        self.assertTrue(decoded["demo"]["synthetic"])
        self.assertEqual(decoded["learners"]["riya"]["persisted_attempt_count"], 2)
        self.assertEqual(decoded["learners"]["arjun"]["persisted_attempt_count"], 4)
        self.assertEqual(
            decoded["learners"]["riya"]["submissions"][-1]["recommendation"]["action_type"],
            "targeted_practice",
        )
        self.assertTrue(
            decoded["learners"]["riya"]["submissions"][-1]["recommendation"][
                "teacher_review_required"
            ]
        )
        self.assertEqual(
            decoded["learners"]["arjun"]["submissions"][-1]["gap_status"],
            "secure",
        )
        self.assertEqual(
            decoded["learners"]["arjun"]["submissions"][-1]["recommendation"]["action_type"],
            "transfer_practice",
        )

        for learner in decoded["learners"].values():
            self.assertNotIn("answer", learner["start"]["item"])
            for submission in learner["submissions"]:
                self.assertNotIn("answer", submission["item"])

    @staticmethod
    def _json_default(value: object) -> object:
        if hasattr(value, "value"):
            return value.value
        raise TypeError(type(value).__name__)


if __name__ == "__main__":
    unittest.main()
