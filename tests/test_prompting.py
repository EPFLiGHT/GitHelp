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
    assert "Begin with 1 or 2 short sentences" in prompt
    assert 'For a "how to" question, give numbered, actionable steps' in prompt
    assert "files to edit, commands, and verification" in prompt
    assert "identify that gap instead of guessing" in prompt
    assert "Cite each source-grounded factual claim" in prompt
    assert "Omit unrelated files, parameters, and details" in prompt


def test_build_user_prompt_requests_grouped_non_repetitive_parameter_answers():
    prompt = build_user_prompt(
        question="What do these configuration parameters do?",
        results=[make_result()],
    )

    assert "group the relevant items by functional role" in prompt
    assert "Explain the shared purpose once" in prompt
    assert "Do not default to one repetitive bullet per parameter" in prompt
    assert "do not repeat the same sentence pattern" in prompt


def test_build_user_prompt_distinguishes_partial_evidence_and_inference():
    prompt = build_user_prompt(
        question="How is the application deployed?",
        results=[make_result()],
    )

    assert "retrieved sources only partially answer this question" in prompt
    assert "what remains unknown" in prompt
    assert "State safe inferences as inferences" in prompt
    assert "Use a citation only when that source supports the claim" in prompt
    assert "Never add a citation to make an unsupported claim look grounded" in prompt


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
    assert "without adding new facts" in prompt
    assert "facts needed to answer" in prompt


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
        {"role": "user", "content": f"old question {index}"} for index in range(8)
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


def test_build_user_prompt_treats_history_as_light_context_only():
    prompt = build_user_prompt(
        question="How does Docker deployment work?",
        results=[make_result()],
        chat_history=[
            {"role": "user", "content": "How does indexing work?"},
            {"role": "assistant", "content": "It creates a searchable index."},
        ],
    )

    assert "Treat the current question as the primary request" in prompt
    assert "Do not assume it continues the previous topic" in prompt
    assert (
        "If the current question is standalone, ignore unrelated earlier topics"
        in prompt
    )
    assert "Do not repeat the previous answer unless the user explicitly asks" in prompt
    assert "follow-up is ambiguous and ask the user" in prompt
