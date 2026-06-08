from __future__ import annotations

import pytest

from githelp.rag.dummy_provider import DummyLLMProvider
from githelp.rag.llm_factory import create_llm_provider
from githelp.rag.qwen_provider import remove_thinking_trace


def test_dummy_provider_returns_stable_test_answer():
    provider = DummyLLMProvider()

    answer = provider.generate("Explain the project.")

    assert "Dummy answer generated successfully" in answer
    assert "retrieval, prompt construction, and LLM interface" in answer


def test_llm_factory_defaults_to_dummy_provider():
    provider = create_llm_provider({})

    assert isinstance(provider, DummyLLMProvider)


def test_llm_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm_provider({"llm": {"provider": "unknown"}})


def test_llm_factory_creates_qwen_provider_with_config(monkeypatch):
    captured_kwargs = {}

    class FakeQwenLLMProvider:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

        def generate(self, prompt: str) -> str:
            return f"fake answer for {prompt}"

    monkeypatch.setattr(
        "githelp.rag.qwen_provider.QwenLLMProvider",
        FakeQwenLLMProvider,
    )

    provider = create_llm_provider(
        {
            "llm": {
                "provider": "qwen",
                "model_name": "Qwen/Test",
                "max_new_tokens": 64,
                "temperature": 0.2,
                "enable_thinking": True,
            }
        }
    )

    assert isinstance(provider, FakeQwenLLMProvider)
    assert captured_kwargs == {
        "model_name": "Qwen/Test",
        "max_new_tokens": 64,
        "temperature": 0.2,
        "enable_thinking": True,
    }


def test_remove_thinking_trace_removes_qwen_internal_trace():
    text = "<think>hidden reasoning</think>\nFinal answer."

    assert remove_thinking_trace(text) == "Final answer."
