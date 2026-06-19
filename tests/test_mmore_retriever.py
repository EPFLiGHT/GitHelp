from __future__ import annotations

import json
from pathlib import Path

from githelp.retrieval import mmore_native, mmore_retriever
from githelp.retrieval.mmore_errors import MMoreRetrievalError


class FakeMmoreClient:
    def __init__(self):
        self.loaded_collections = []

    def load_collection(self, collection_name):
        self.loaded_collections.append(collection_name)


class FakeMmoreRetriever:
    def __init__(self):
        self.calls = []
        self.client = FakeMmoreClient()

    def retrieve(
        self,
        query,
        collection_name,
        k,
        output_fields,
        search_type,
    ):
        self.calls.append(
            {
                "query": query,
                "collection_name": collection_name,
                "k": k,
                "output_fields": output_fields,
                "search_type": search_type,
            }
        )
        return [
            {
                "id": "raw-1",
                "distance": 0.8,
                "text": (
                    "GitHelp ID: doc-1\n"
                    "Source type: markdown\n"
                    "Title: GitHub loading\n"
                    "Relative path: docs/github_loading.md\n\n"
                    "Content:\n"
                    "Clone a GitHub repository before building the corpus."
                ),
            }
        ]


def test_retrieve_with_mmore_uses_githelp_configs_when_mmore_metadata_is_missing(
    monkeypatch,
    tmp_path: Path,
):
    retriever = FakeMmoreRetriever()
    fallback_calls = []

    def raise_missing_model_name(config_path):
        raise KeyError("model_name")

    def fake_create_retriever_from_githelp_configs(
        retriever_config_path,
        index_config_path,
    ):
        fallback_calls.append(
            {
                "retriever_config_path": retriever_config_path,
                "index_config_path": index_config_path,
            }
        )
        return retriever

    retriever_config_path = tmp_path / "mmore_retriever_config.yaml"
    index_config_path = tmp_path / "mmore_index_config.yaml"

    monkeypatch.setattr(
        mmore_native,
        "load_retriever_from_mmore_config",
        raise_missing_model_name,
    )
    monkeypatch.setattr(
        mmore_native,
        "create_retriever_from_githelp_configs",
        fake_create_retriever_from_githelp_configs,
    )

    results = mmore_retriever.retrieve_with_mmore(
        query="How do I load a GitHub repo?",
        top_k=3,
        config_path=retriever_config_path,
        index_config_path=index_config_path,
        collection_name="mmore_docs",
        use_subprocess=False,
    )

    assert len(results) == 1
    assert results[0].document.doc_id == "doc-1"
    assert results[0].document.metadata["relative_path"] == "docs/github_loading.md"
    assert fallback_calls == [
        {
            "retriever_config_path": retriever_config_path,
            "index_config_path": index_config_path,
        }
    ]
    assert retriever.calls[0]["k"] == mmore_native.MIN_MMORE_RAW_RESULTS
    assert retriever.calls[0]["search_type"] == "hybrid"
    assert retriever.client.loaded_collections == ["mmore_docs"]


def test_load_collection_for_search_ignores_retrievers_without_milvus_client():
    class RetrieverWithoutClient:
        pass

    mmore_native.load_collection_for_search(
        RetrieverWithoutClient(),
        "mmore_docs",
    )


def test_retrieve_with_mmore_reports_config_fallback_failure(monkeypatch, tmp_path: Path):
    def raise_missing_model_name(config_path):
        raise KeyError("model_name")

    def raise_fallback_error(retriever_config_path, index_config_path):
        raise ValueError("bad config")

    monkeypatch.setattr(
        mmore_native,
        "load_retriever_from_mmore_config",
        raise_missing_model_name,
    )
    monkeypatch.setattr(
        mmore_native,
        "create_retriever_from_githelp_configs",
        raise_fallback_error,
    )

    try:
        mmore_retriever.retrieve_with_mmore(
            query="question",
            config_path=tmp_path / "mmore_retriever_config.yaml",
            index_config_path=tmp_path / "mmore_index_config.yaml",
            use_subprocess=False,
        )
    except RuntimeError as error:
        assert "GitHelp's MMORE config files" in str(error)
        assert isinstance(error.__cause__, ValueError)
    else:
        raise AssertionError("Expected fallback construction to fail")


def test_load_githelp_mmore_model_configs_reads_dense_and_sparse_models(
    tmp_path: Path,
):
    index_config_path = tmp_path / "mmore_index_config.yaml"
    index_config_path.write_text(
        "indexer:\n"
        "  dense_model:\n"
        "    model_name: dense-test\n"
        "    is_multimodal: false\n"
        "  sparse_model:\n"
        "    model_name: sparse-test\n"
        "    is_multimodal: false\n",
        encoding="utf-8",
    )

    dense_model_config, sparse_model_config = (
        mmore_native.load_githelp_mmore_model_configs(index_config_path)
    )

    assert dense_model_config["model_name"] == "dense-test"
    assert sparse_model_config["model_name"] == "sparse-test"


def test_retrieve_with_mmore_falls_back_to_exported_mmore_corpus(
    monkeypatch,
    tmp_path: Path,
):
    project_corpus_path = tmp_path / "corpus.jsonl"
    mmore_corpus_path = tmp_path / "mmore_corpus.jsonl"

    project_corpus_path.write_text("", encoding="utf-8")
    mmore_corpus_path.write_text(
        json.dumps(
            {
                "text": (
                    "GitHelp ID: markdown::setup\n"
                    "Source type: markdown_section\n"
                    "Title: Setup guide\n"
                    "Relative path: docs/setup.md\n"
                    "Section: Setup\n\n"
                    "Content:\n"
                    "Use the setup command to build the MMORE corpus."
                ),
                "modalities": [],
                "metadata": {"doc_id": "markdown::setup"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_native_subprocess(*args, **kwargs):
        raise MMoreRetrievalError("native MMORE crashed")

    monkeypatch.setattr(
        mmore_retriever,
        "_retrieve_with_mmore_subprocess",
        fail_native_subprocess,
    )

    results = mmore_retriever.retrieve_with_mmore(
        query="setup command",
        top_k=1,
        corpus_path=project_corpus_path,
    )

    assert len(results) == 1
    assert results[0].document.doc_id == "markdown::setup"
    assert results[0].document.metadata["relative_path"] == "docs/setup.md"
