"""LLM adapter package."""

from .base import LLMAdapter
from .openai_compatible import LLMError, OpenAICompatibleLLM

__all__ = ["LLMAdapter", "OpenAICompatibleLLM", "LLMError"]

