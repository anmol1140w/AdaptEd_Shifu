"""Mock and provider-specific language-model adapters."""

from .mock import (
    CuratedQuizFallback,
    CuratedTutorFallback,
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from .ollama_cloud import OllamaCloudGenerator

__all__ = [
    "CuratedQuizFallback",
    "CuratedTutorFallback",
    "DeterministicQuizGenerator",
    "DeterministicTutorGenerator",
    "OllamaCloudGenerator",
]
