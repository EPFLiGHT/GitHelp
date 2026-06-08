from __future__ import annotations

from githelp.rag.llm_provider import LLMProvider


class DummyLLMProvider(LLMProvider):
    """Fake LLM provider used for testing the pipeline without loading a real model."""

    def generate(self, prompt: str) -> str:
        return (
            "Dummy answer generated successfully.\n\n"
            "This means the retrieval, prompt construction, and LLM interface are connected. "
            "Replace the dummy provider with Qwen to generate real answers."
        )