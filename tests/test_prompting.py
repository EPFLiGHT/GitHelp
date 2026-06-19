from __future__ import annotations

from githelp.data_models import DocumentRecord
from githelp.rag.prompting import (
    build_user_prompt,
    format_chat_history,
    format_source_label,
)
from githelp.retrieval.base import RetrievalResult


def make_result() -> RetrievalResult:
    document = DocumentRecord(
        doc_id="doc::prompt",
        content="Run `python -m example` to start the application.",
        source_type="markdown_section",
        title="Usage",
        file_path="docs/usage.md",
        section_title="Usage",
        module_name=None,
        symbol_name=None,
        signature=None,
        language="en",
        tags=[],
        metadata={"relative_path": "docs/usage.md"},
    )

    return RetrievalResult(document=document, score=0.75)


def test_format_source_label_uses_relative_path_and_section():
    result = make_result()

    label = format_source_label(result, 1)

    assert label == "[Source 1] markdown_section — docs/usage.md — Usage"


def test_build_user_prompt_contains_question_sources_and_rules():
    result = make_result()

    prompt = build_user_prompt(
        question="How do I start the app?",
        results=[result],
    )

    assert "How do I start the app?" in prompt
    assert "[Source 1] markdown_section — docs/usage.md — Usage" in prompt
    assert "Run `python -m example`" in prompt
    assert "Start with 1 or 2 short context sentences" in prompt
    assert 'For "how to" questions, act like a practical repository guide' in prompt
    assert '"Files involved" followed by "Steps"' in prompt
    assert "prepare or locate required files" in prompt
    assert "which detail is not available" in prompt
    assert "what output/result to expect if available" in prompt
    assert "short practical takeaway" in prompt
    assert "Every paragraph, bullet, or numbered step" in prompt
    assert "Do not include unrelated configuration fields" in prompt


def test_build_user_prompt_allows_source_grounded_simplification():
    result = make_result()

    prompt = build_user_prompt(
        question="Explain more simply",
        results=[result],
        chat_history=[
            {"role": "user", "content": "How do I start the app?"},
            {"role": "assistant", "content": "Run the documented command."},
        ],
    )

    assert "You may simplify, summarize, clarify, and rephrase" in prompt
    assert "do not need to contain a simplified explanation already" in prompt
    assert "Do not require a source to already contain the simplified wording" in prompt
    assert "factual content needed" in prompt


def test_format_chat_history_keeps_only_user_and_assistant_messages():
    history = [
        {"role": "system", "content": "hidden"},
        {"role": "user", "content": "How do I install it?"},
        {"role": "assistant", "content": "Use the install guide. [Source 1]"},
    ]

    formatted = format_chat_history(history)

    assert "hidden" not in formatted
    assert "User: How do I install it?" in formatted
    assert "Assistant: Use the install guide. [Source 1]" in formatted


def test_build_user_prompt_includes_recent_chat_history_only():
    result = make_result()
    history = [
        {"role": "user", "content": f"old question {index}"}
        for index in range(8)
    ]

    prompt = build_user_prompt(
        question="And how do I run it?",
        results=[result],
        chat_history=history,
    )

    assert "Recent conversation context:" in prompt
    assert "old question 0" not in prompt
    assert "old question 1" not in prompt
    assert "old question 2" in prompt
    assert "old question 7" in prompt
    assert "And how do I run it?" in prompt
