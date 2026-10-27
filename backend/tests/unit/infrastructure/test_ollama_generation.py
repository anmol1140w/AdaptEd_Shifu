"""Contract checks for Ollama Cloud structured-generation output."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from backend.app.application.ports.ai import (
    AIIntegrationError,
    QuizRequest,
    RetrievedSource,
    TutorMode,
    TutorRequest,
)
from backend.app.domain.entities.learning import Difficulty
from backend.app.infrastructure.ai.llm import OllamaCloudGenerator


class _Response:
    def __init__(self, body: dict) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._body


class CloudGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RetrievedSource(
            source_id="lesson-algebra-01",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            title="Equation lesson",
            text="Undo addition before division.",
        )
        self.request = TutorRequest(
            learner_id="learner-1",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            mode=TutorMode.EXPLANATION,
        )

    @staticmethod
    def _ollama_response(content: str) -> _Response:
        return _Response({"message": {"content": content}})

    def test_ollama_rejects_invalid_json_shape_locally(self) -> None:
        invalid_ollama = {
            "message": "Response.",
            "check_question": "Question?",
            "source_ids": [self.source.source_id],
            "answer_revealed": False,
            "teacher_review_required": False,
            "unexpected": "must be rejected",
        }
        generator = OllamaCloudGenerator(api_key="test-ollama-key", model="gemma4:31b")

        with patch(
            "backend.app.infrastructure.ai.llm.ollama_cloud.httpx.post",
            return_value=self._ollama_response(json.dumps(invalid_ollama)),
        ), self.assertRaises(AIIntegrationError):
            generator.generate(request=self.request, sources=(self.source,))

    def test_quiz_schema_rejects_wrong_item_count(self) -> None:
        invalid_quiz = {
            "items": [{
                "question": "Solve x + 2 = 5.",
                "answer": "x = 3",
                "representation": "symbolic",
                "source_ids": [self.source.source_id],
                "is_transfer": False,
            }],
            "source_ids": [self.source.source_id],
            "teacher_review_required": False,
        }
        request = QuizRequest(
            learner_id="learner-1",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            difficulty=Difficulty.MEDIUM,
            item_count=2,
            include_transfer=True,
        )
        generator = OllamaCloudGenerator(api_key="test-ollama-key", model="gemma4:31b")

        with patch(
            "backend.app.infrastructure.ai.llm.ollama_cloud.httpx.post",
            return_value=self._ollama_response(json.dumps(invalid_quiz)),
        ), self.assertRaises(AIIntegrationError):
            generator.generate(request=request, sources=(self.source,))


if __name__ == "__main__":
    unittest.main()
