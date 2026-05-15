from __future__ import annotations

from docask.rag.dummy_provider import DummyLLMProvider
from docask.rag.llm_provider import LLMProvider


def create_llm_provider(config: dict) -> LLMProvider:
    """Create an LLM provider from a configuration dictionary."""
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "dummy")

    if provider == "dummy":
        return DummyLLMProvider()

    if provider == "qwen":
        from docask.rag.qwen_provider import QwenLLMProvider

        return QwenLLMProvider(
            model_name=llm_config.get("model_name", "Qwen/Qwen3-8B"),
            max_new_tokens=llm_config.get("max_new_tokens", 512),
            temperature=llm_config.get("temperature", 0.0),
            enable_thinking=llm_config.get("enable_thinking", False),
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")