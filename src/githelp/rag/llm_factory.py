from __future__ import annotations

from githelp.config import AppConfig, LLMConfig
from githelp.rag.dummy_provider import DummyLLMProvider
from githelp.rag.llm_provider import LLMProvider


def _coerce_llm_config(config: AppConfig | LLMConfig | dict) -> LLMConfig:
    """Return a typed LLM config from app, LLM, or legacy dictionary config."""
    if isinstance(config, LLMConfig):
        return config

    if isinstance(config, AppConfig):
        return config.llm

    return LLMConfig.from_mapping(config.get("llm", {}))


def create_llm_provider(config: AppConfig | LLMConfig | dict) -> LLMProvider:
    """Create an LLM provider from a configuration dictionary."""
    llm_config = _coerce_llm_config(config)
    provider = llm_config.provider

    if provider == "dummy":
        return DummyLLMProvider()

    if provider == "qwen":
        from githelp.rag.qwen_provider import QwenLLMProvider

        return QwenLLMProvider(
            model_name=llm_config.model_name,
            max_new_tokens=llm_config.max_new_tokens,
            temperature=llm_config.temperature,
            enable_thinking=llm_config.enable_thinking,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")
