from __future__ import annotations

from githelp.data_models import DocumentRecord
from githelp.project_profiles.generic import GenericProjectProfile
from githelp.retrieval.base import RetrievalResult


def make_result(
    *,
    doc_id: str,
    content: str = "Detailed documentation content that is useful for answering.",
    source_type: str = "markdown_section",
    score: float = 1.0,
    relative_path: str = "docs/guide.md",
    title: str = "Guide",
    module_name: str | None = None,
    symbol_name: str | None = None,
    signature: str | None = None,
) -> RetrievalResult:
    document = DocumentRecord(
        doc_id=doc_id,
        content=content,
        source_type=source_type,
        title=title,
        file_path=relative_path,
        section_title=None,
        module_name=module_name,
        symbol_name=symbol_name,
        signature=signature,
        language="en",
        tags=[],
        metadata={"relative_path": relative_path},
    )
    return RetrievalResult(document=document, score=score)


def test_generic_profile_keeps_query_project_agnostic():
    profile = GenericProjectProfile()
    question = "How is the corpus built?"

    assert profile.expand_query(question) == question
    assert profile.answer_directly(question, []) is None


def test_generic_profile_filters_empty_and_tiny_fragments():
    profile = GenericProjectProfile()
    empty = make_result(doc_id="empty", content="   ")
    tiny = make_result(doc_id="tiny", content="Too small")
    useful = make_result(doc_id="useful")

    assert profile.filter_results([empty, tiny, useful], "What is this?") == [useful]


def test_generic_profile_boosts_exact_python_symbol_for_code_question():
    profile = GenericProjectProfile()
    generic = make_result(doc_id="generic", score=8.0)
    symbol = make_result(
        doc_id="symbol",
        source_type="python_function",
        score=1.0,
        relative_path="src/githelp/corpus/builder.py",
        title="build_corpus",
        module_name="githelp.corpus.builder",
        symbol_name="build_corpus",
        signature="build_corpus(config)",
    )

    reranked = profile.rerank_results(
        [generic, symbol],
        "What does the build_corpus function do?",
    )

    assert reranked[0] == symbol


def test_generic_profile_prioritizes_cli_source_for_command_question():
    profile = GenericProjectProfile()
    guide = make_result(doc_id="guide", score=5.0)
    cli = make_result(
        doc_id="cli",
        source_type="python_function",
        score=1.0,
        relative_path="src/package/cli.py",
        module_name="package.cli",
        symbol_name="index",
    )

    reranked = profile.rerank_results(
        [guide, cli],
        "Which CLI command runs indexing?",
    )

    assert reranked[0] == cli


def test_generic_profile_limits_config_dominance_for_code_question():
    profile = GenericProjectProfile()
    first_config = make_result(
        doc_id="config-1",
        source_type="yaml_config",
        score=100.0,
        relative_path="configs/first.yml",
    )
    second_config = make_result(
        doc_id="config-2",
        source_type="example_config",
        score=99.0,
        relative_path="configs/second.yml",
    )
    code = make_result(
        doc_id="code",
        source_type="python_function",
        score=1.0,
        relative_path="src/package/indexer.py",
        symbol_name="build_index",
    )

    reranked = profile.rerank_results(
        [first_config, second_config, code],
        "Which function implements indexing?",
    )

    assert reranked.index(code) < reranked.index(second_config)
    assert sum(
        result.document.source_type in profile.CONFIG_SOURCE_TYPES
        for result in reranked[:2]
    ) == 1


def test_generic_profile_boosts_yaml_for_configuration_question():
    profile = GenericProjectProfile()
    guide = make_result(doc_id="guide", score=3.0)
    config = make_result(
        doc_id="config",
        source_type="yaml_config",
        score=1.0,
        relative_path="configs/app_config.yaml",
        title="Application config",
    )

    reranked = profile.rerank_results(
        [guide, config],
        "Which configuration fields are available?",
    )

    assert reranked[0] == config
