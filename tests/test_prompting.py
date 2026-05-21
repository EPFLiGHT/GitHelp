from __future__ import annotations

from docask.data_models import DocumentRecord
from docask.rag.prompting import build_user_prompt, format_source_label
from docask.retrieval.base import RetrievalResult


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
    assert "Every bullet point must include at least one inline citation" in prompt
    assert "Do not include unrelated configuration fields" in prompt