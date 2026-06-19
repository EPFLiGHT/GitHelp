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
