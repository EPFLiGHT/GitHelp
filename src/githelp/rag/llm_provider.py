from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base interface for all LLM providers used by GitHelp."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate an answer from a prompt."""
        raise NotImplementedError