from __future__ import annotations

from githelp.data_models import DocumentRecord
from githelp.project_profiles.mmore import MMoreProjectProfile
from githelp.retrieval.base import RetrievalResult


def make_result(
    content: str,
    source_type: str = "example_config",
    relative_path: str = "examples/colpali/config_index.yml",
    score: float = 1.0,
    title: str = "Example config",
    symbol_name: str | None = None,
) -> RetrievalResult:
    document = DocumentRecord(
        doc_id="doc::1",
        content=content,
        source_type=source_type,
        title=title,
        file_path=relative_path,
        section_title=None,
        module_name="mmore.index.indexer" if symbol_name else None,
        symbol_name=symbol_name,
        signature=None,
        language="en",
        tags=[],
        metadata={"relative_path": relative_path},
    )

    return RetrievalResult(document=document, score=score)


def test_mmore_profile_expands_colpali_milvus_query():
    profile = MMoreProjectProfile()

    expanded = profile.expand_query(
        "Which Milvus parameters are used in the ColPali config?"
    )

    assert "colpali" in expanded.lower()
    assert "milvus" in expanded.lower()
    assert "config_index.yml" in expanded
    assert "collection_name" in expanded


def test_mmore_profile_expands_code_oriented_indexing_query():
    profile = MMoreProjectProfile()

    expanded = profile.expand_query("Which function implements indexing?")

    assert "cli.py" in expanded
    assert "mmore.cli" in expanded
    assert "signature" in expanded


def test_mmore_profile_directly_answers_milvus_parameter_question():
    profile = MMoreProjectProfile()

    result = make_result(
        """
        milvus:
          db_path: ./output/milvus_data.db
          collection_name: pdf_pages
          create_collection: true
          dim: 128
          metric_type: IP

        model_name: vidore/colpali-v1.3
        top_k: 3
        max_workers: 4
        """
    )

    answer = profile.answer_directly(
        "Which Milvus parameters are used in the ColPali config?",
        [result],
    )

    assert answer is not None
    assert "`db_path`" in answer
    assert "`collection_name`" in answer
    assert "`create_collection`" in answer
    assert "`dim`" in answer
    assert "`metric_type`" in answer

    assert "model_name" not in answer
    assert "top_k" not in answer
    assert "max_workers" not in answer


def test_mmore_profile_returns_none_for_non_milvus_question():
    profile = MMoreProjectProfile()

    result = make_result("This source explains indexing.")

    answer = profile.answer_directly(
        "How do I configure indexing?",
        [result],
    )

    assert answer is None


def test_mmore_profile_reports_when_milvus_parameters_are_not_retrieved():
    profile = MMoreProjectProfile()
    result = make_result(
        "Milvus is the vector database used by this indexing example."
    )

    answer = profile.answer_directly("Which Milvus parameters are used?", [result])

    assert answer is not None
    assert "do not provide enough information" in answer


def test_mmore_profile_filters_colpali_sources_when_question_does_not_mention_colpali():
    profile = MMoreProjectProfile()

    colpali_result = make_result(
        content=(
            "ColPali documentation explaining how ColPali retrieval works "
            "inside the MMORE project."
        ),
        relative_path="core_features/colpali.md",
    )

    general_result = make_result(
        content=(
            "General indexing documentation explaining how to configure "
            "the indexing pipeline for a project."
        ),
        relative_path="getting_started/indexing.md",
    )

    filtered = profile.filter_results(
        [colpali_result, general_result],
        question="How do I configure indexing?",
    )

    assert general_result in filtered
    assert colpali_result not in filtered


def test_mmore_profile_filters_websearch_sources_unless_requested():
    profile = MMoreProjectProfile()
    websearch_result = make_result(
        content=(
            "Websearch documentation describing online result retrieval "
            "and its configuration in enough detail."
        ),
        relative_path="core_features/websearch.md",
    )
    general_result = make_result(
        content=(
            "General retrieval documentation describing the local pipeline "
            "and its configuration in enough detail."
        ),
        relative_path="core_features/retrieval.md",
    )

    filtered = profile.filter_results(
        [websearch_result, general_result],
        question="How does local retrieval work?",
    )
    requested = profile.filter_results(
        [websearch_result, general_result],
        question="How does web search retrieval work?",
    )

    assert filtered == [general_result]
    assert websearch_result in requested


def test_mmore_profile_reranks_milvus_config_above_generic_config():
    profile = MMoreProjectProfile()
    generic_config = make_result(
        content=(
            "General indexing configuration with model and batching settings "
            "for the complete pipeline."
        ),
        relative_path="configs/index.yml",
        score=10.0,
    )
    milvus_config = make_result(
        content=(
            "milvus:\n  db_path: ./data.db\n  collection_name: pages\n"
            "  create_collection: true\n  dim: 128\n  metric_type: IP"
        ),
        relative_path="examples/colpali/config_index.yml",
        score=1.0,
    )

    reranked = profile.rerank_results(
        [generic_config, milvus_config],
        question="Which Milvus parameters are in the ColPali config?",
    )

    assert reranked[0] == milvus_config


def test_mmore_profile_does_not_match_short_symbol_inside_longer_identifier():
    profile = MMoreProjectProfile()

    index_function = make_result(
        content="Run the indexer with a config file and documents path.",
        source_type="python_function",
        relative_path="cli.py",
        score=5.0,
        title="mmore.cli.index",
        symbol_name="index",
    )
    indexer_class = make_result(
        content="The Indexer class builds and manages indexes.",
        source_type="python_class",
        relative_path="index/indexer.py",
        score=2.0,
        title="mmore.index.indexer.Indexer",
        symbol_name="Indexer",
    )

    reranked = profile.rerank_results(
        [index_function, indexer_class],
        question="What does the Indexer class do?",
    )

    assert reranked[0] == indexer_class
