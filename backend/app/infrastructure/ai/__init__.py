"""AdaptEd AI Subsystem Package (R1 - R5)."""

from backend.app.application.ports.ai_ports import (
    BaseSchema,
    LLMPort,
    QuizGeneratorPort,
    QuizItem,
    QuizRequest,
    QuizResponse,
    RetrievedChunk,
    RetrieverPort,
    TutorPort,
    TutorRequest,
    TutorResponse,
    ValidationError,
    ValidationResult,
    ValidatorPort,
)
from backend.app.infrastructure.ai.llm.base import BaseLLMClient, LLMProviderError, LLMResponse
from backend.app.infrastructure.ai.llm.live_llm import LiveLLMClient
from backend.app.infrastructure.ai.llm.mock_llm import MockLLMClient
from backend.app.infrastructure.ai.quiz_generator import WeakAreaQuizGenerator
from backend.app.infrastructure.ai.retrieval.mock_retriever import MockKnowledgeRetriever
from backend.app.infrastructure.ai.tutor import GroundedRAGTutor
from backend.app.infrastructure.ai.validators.validator import (
    AntiSpoilerViolation,
    ComprehensiveAIValidator,
    GroundingViolation,
    QuizValidator,
    TutorValidator,
)

__all__ = [
    # Top-Level AI Services
    "GroundedRAGTutor",
    "WeakAreaQuizGenerator",
    # Retrieval
    "MockKnowledgeRetriever",
    # LLM Adapters
    "BaseLLMClient",
    "MockLLMClient",
    "LiveLLMClient",
    "LLMResponse",
    "LLMProviderError",
    # Validators
    "TutorValidator",
    "QuizValidator",
    "ComprehensiveAIValidator",
    "AntiSpoilerViolation",
    "GroundingViolation",
    # Schemas & Types
    "BaseSchema",
    "RetrievedChunk",
    "TutorRequest",
    "TutorResponse",
    "QuizRequest",
    "QuizItem",
    "QuizResponse",
    "ValidationResult",
    "ValidationError",
    # Ports
    "LLMPort",
    "RetrieverPort",
    "TutorPort",
    "QuizGeneratorPort",
    "ValidatorPort",
]
