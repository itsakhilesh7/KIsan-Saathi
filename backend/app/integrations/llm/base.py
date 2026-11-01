"""Abstract base interface for LLM adapters."""

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Base interface for model adapters."""

    @abstractmethod
    async def answer(
        self,
        user_text: str,
        lang: str | None = None,
        context: str | None = None,
    ) -> tuple[str, str]:
        """Generates an answer from user text and optional context.

        Returns:
            tuple[str, str]: (answer_text, model_name_disclosed)
        """

