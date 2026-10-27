"""Contract checks for schema-constrained Grok and validated Ollama backup."""

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
from backend.app.infrastructure.ai.llm import (
    GrokGenerator,
    OllamaCloudGenerator,
    PrimaryFallbackGenerator,
)
from backend.app.infrastructure.ai.validators import StructuredLearningOutputValidator


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
    def _grok_response(content: str) -> _Response:
        return _Response({
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": content}],
            }]
        })

    @staticmethod
    def _ollama_response(content: str) -> _Response:
        return _Response({"message": {"content": content}})

    def test_grok_requests_strict_schema_json_and_parses_typed_draft(self) -> None:
        result = {
            "message": "Undo the constant operation first.",
            "check_question": "What operation would you undo first?",
            "source_ids": [self.source.source_id],
            "answer_revealed": False,
            "teacher_review_required": False,
        }
        generator = GrokGenerator(api_key="test-key", model="grok-4.7")

        with patch(
            "backend.app.infrastructure.ai.llm.grok.httpx.post",
            return_value=self._grok_response(json.dumps(result)),
        ) as post:
            draft = generator.generate(request=self.request, sources=(self.source,))

        self.assertEqual(draft.provider, "grok:grok-4.7")
        self.assertEqual(draft.source_ids, (self.source.source_id,))
        schema_format = post.call_args.kwargs["json"]["text"]["format"]
        self.assertEqual(schema_format["type"], "json_schema")
        self.assertTrue(schema_format["strict"])

    def test_invalid_grok_schema_uses_ollama_and_marks_fallback(self) -> None:
        invalid_grok = {"message": "Only part of the required JSON."}
        valid_ollama = {
            "message": "Undo the constant operation first.",
            "check_question": "What operation would you undo first?",
            "source_ids": [self.source.source_id],
            "answer_revealed": False,
            "teacher_review_required": False,
        }
        grok = GrokGenerator(api_key="test-grok-key", model="grok-4.7")
        ollama = OllamaCloudGenerator(api_key="test-ollama-key", model="gemma4:31b")
        chain = PrimaryFallbackGenerator(
            primary=grok,
            fallback=ollama,
            validator=StructuredLearningOutputValidator(),
        )

        with patch(
            "backend.app.infrastructure.ai.llm.grok.httpx.post",
            return_value=self._grok_response(json.dumps(invalid_grok)),
        ), patch(
            "backend.app.infrastructure.ai.llm.ollama_cloud.httpx.post",
            return_value=self._ollama_response(json.dumps(valid_ollama)),
        ):
            draft = chain.generate(request=self.request, sources=(self.source,))

        self.assertEqual(draft.provider, "fallback:ollama-cloud:gemma4:31b")
        StructuredLearningOutputValidator().validate_tutor(
            request=self.request,
            draft=draft,
            sources=(self.source,),
        )

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
