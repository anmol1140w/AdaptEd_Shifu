"""Mock and provider-specific language-model adapters."""

from .mock import (
    CuratedQuizFallback,
    CuratedTutorFallback,
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from .ollama_cloud import OllamaCloudGenerator
from .grok import GrokGenerator
from .primary_fallback import PrimaryFallbackGenerator

__all__ = [
    "CuratedQuizFallback",
    "CuratedTutorFallback",
    "DeterministicQuizGenerator",
    "DeterministicTutorGenerator",
    "GrokGenerator",
    "OllamaCloudGenerator",
    "PrimaryFallbackGenerator",
]
