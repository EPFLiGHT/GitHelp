from pathlib import Path

import pytest

from githelp.data_models import DocumentRecord
from githelp.rag.answering import (
    _boost_filename_matches,
    _extract_filename_tokens,
    _get_project_name,
    _prepare_llm_answer_input,
    _resolve_corpus_path,
)
from githelp.retrieval.base import RetrievalResult


def make_result(doc_id: str, relative_path: str, score: float) -> RetrievalResult:
    document = DocumentRecord(
        doc_id=doc_id,
        content="example content",
        source_type="markdown_section",
        title=Path(relative_path).name,
        file_path=relative_path,
        section_title=None,
        module_name=None,
        symbol_name=None,
        signature=None,
        language="en",
        tags=[],
        metadata={"relative_path": relative_path, "project_name": "mmore"},
    )
    return RetrievalResult(document=document, score=score)


def test_extract_filename_tokens_finds_common_extensions():
    question = "What is defined in config_index.yml and app_config.yaml?"
    assert _extract_filename_tokens(question) == [
        "config_index.yml",
        "app_config.yaml",
    ]


def test_boost_filename_matches_reorders_matching_result():
    low = make_result("doc::config", "examples/config_index.yml", 0.5)
    high = make_result("doc::other", "docs/index.md", 1.0)

    results = _boost_filename_matches(
        [high, low],
        "Explain config_index.yml",
        boost=1.0,
    )

    assert results[0].document.doc_id == "doc::config"
    assert results[0].score == pytest.approx(1.5)


def test_get_project_name_prefers_app_config():
    assert _get_project_name({"project_name": "githelp"}) == "githelp"


def test_get_project_name_falls_back_to_result_metadata():
    result = make_result("doc::one", "docs/index.md", 1.0)

    assert _get_project_name({}, [result]) == "mmore"


def test_get_project_name_uses_referenced_project_config(tmp_path: Path):
    project_config = tmp_path / "project_config.yaml"
    project_config.write_text("project_name: referenced-project\n", encoding="utf-8")

    config = {"project": {"config_path": str(project_config)}}

    assert _get_project_name(config) == "referenced-project"


def test_resolve_corpus_path_uses_explicit_path():
    path = _resolve_corpus_path("custom/corpus.jsonl", {})

    assert path == Path("custom/corpus.jsonl")


def test_resolve_corpus_path_uses_project_name_from_config():
    path = _resolve_corpus_path(None, {"project_name": "mmore"})

    assert path == Path("data") / "projects" / "mmore" / "corpus.jsonl"


def test_resolve_corpus_path_uses_referenced_project_config(tmp_path: Path):
    project_config = tmp_path / "project_config.yaml"
    project_config.write_text("project_name: referenced-project\n", encoding="utf-8")

    path = _resolve_corpus_path(
        None,
        {"project_config_path": str(project_config)},
    )

    assert path == Path("data") / "projects" / "referenced-project" / "corpus.jsonl"


def test_resolve_corpus_path_fails_when_project_name_missing():
    with pytest.raises(ValueError, match="Could not infer"):
        _resolve_corpus_path(None, {})


def test_prepare_llm_answer_input_returns_final_answer_for_empty_results():
    answer, results, should_generate = _prepare_llm_answer_input(
        question="How do I install it?",
        results=[],
        config={},
    )

    assert answer == "I could not find relevant sources in the corpus."
    assert results == []
    assert should_generate is False


def test_prepare_llm_answer_input_blocks_subjective_private_dataset_recommendation():
    result = make_result("doc::one", "docs/index.md", 1.0)

    answer, results, should_generate = _prepare_llm_answer_input(
        question="Which embedding model is best for my dataset?",
        results=[result],
        config={},
    )

    assert "private dataset" in answer
    assert results == [result]
    assert should_generate is False


def test_prepare_llm_answer_input_builds_prompt_when_generation_is_needed():
    result = make_result("doc::one", "docs/index.md", 1.0)

    prompt, results, should_generate = _prepare_llm_answer_input(
        question="How do I configure it?",
        results=[result],
        config={"project_name": "githelp"},
    )

    assert "How do I configure it?" in prompt
    assert "githelp" in prompt
    assert results == [result]
    assert should_generate is True
