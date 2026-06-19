from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_errors import MMoreRetrievalError
from githelp.retrieval.mmore_result_mapping import (
    MMORE_NATIVE_MODE,
    mmore_result_to_retrieval_result,
    tag_results_with_mmore_mode,
)
from githelp.utils.paths import resolve_project_path


MIN_MMORE_RAW_RESULTS = 40
DEFAULT_MMORE_INDEX_CONFIG_PATH = "configs/mmore_index_config.yaml"


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a dictionary: {path}")

    return data


def load_githelp_mmore_model_configs(
    index_config_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Load dense and sparse model configs from GitHelp's MMORE index config.

    MMORE tries to recover these from Milvus index metadata during retrieval,
    but Milvus Lite may not persist custom fields such as model_name. GitHelp
    keeps the source of truth in configs/mmore_index_config.yaml.
    """
    config = load_yaml_mapping(index_config_path)
    indexer_config = config.get("indexer", {})

    if not isinstance(indexer_config, dict):
        raise ValueError("MMORE index config must define an indexer section.")

    dense_model_config = indexer_config.get("dense_model")
    sparse_model_config = indexer_config.get("sparse_model")

    if not isinstance(dense_model_config, dict):
        raise ValueError("MMORE index config must define indexer.dense_model.")

    if not isinstance(sparse_model_config, dict):
        raise ValueError("MMORE index config must define indexer.sparse_model.")

    return dense_model_config, sparse_model_config


def create_retriever_from_githelp_configs(
    retriever_config_path: str | Path,
    index_config_path: str | Path,
):
    """
    Create a MMORE Retriever using GitHelp config files as model metadata.
    """
    from pymilvus import MilvusClient
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from mmore.rag.model.dense.base import DenseModel, DenseModelConfig
    from mmore.rag.model.sparse.base import SparseModel, SparseModelConfig
    from mmore.rag.retriever import Retriever

    retriever_config = load_yaml_mapping(retriever_config_path)
    db_config = retriever_config.get("db", {})

    if not isinstance(db_config, dict):
        raise ValueError("MMORE retriever config must define a db section.")

    dense_model_config, sparse_model_config = load_githelp_mmore_model_configs(
        index_config_path
    )

    collection_name = str(retriever_config.get("collection_name", "mmore_docs"))
    db_uri = resolve_project_path(
        str(db_config.get("uri", "./data/indexes/mmore/githelp.db"))
    )
    client = MilvusClient(
        uri=str(db_uri),
        db_name=str(db_config.get("name", "my_db")),
    )

    if not client.has_collection(collection_name):
        raise ValueError(
            "The Milvus database does not have collection "
            f"{collection_name}. Rebuild the MMORE index first."
        )

    reranker_model_name = retriever_config.get("reranker_model_name")

    if reranker_model_name:
        reranker_tokenizer = AutoTokenizer.from_pretrained(str(reranker_model_name))
        reranker_model = AutoModelForSequenceClassification.from_pretrained(
            str(reranker_model_name)
        )
    else:
        reranker_model = None
        reranker_tokenizer = None

    return Retriever(
        dense_model=DenseModel.from_config(DenseModelConfig(**dense_model_config)),
        sparse_model=SparseModel.from_config(SparseModelConfig(**sparse_model_config)),
        client=client,
        hybrid_search_weight=float(retriever_config.get("hybrid_search_weight", 0.5)),
        k=int(retriever_config.get("k", 5)),
        use_web=bool(retriever_config.get("use_web", False)),
        reranker_model=reranker_model,
        reranker_tokenizer=reranker_tokenizer,
    )


def load_retriever_from_mmore_config(config_path: str | Path):
    """Load MMORE's Retriever from its own retriever config."""
    from mmore.rag.retriever import Retriever

    return Retriever.from_config(str(config_path))


def load_collection_for_search(retriever, collection_name: str) -> None:
    """
    Load the Milvus collection before searching.

    Milvus can keep an existing collection in a released state after reopening
    a local index. In that state, search/get/query calls fail until load() is
    called.
    """
    client = getattr(retriever, "client", None)
    load_collection = getattr(client, "load_collection", None)

    if load_collection is None:
        return

    load_collection(collection_name=collection_name)


def rerank_for_githelp_intent(
    query: str,
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Apply small GitHelp-specific reranking heuristics.

    MMORE provides the main retrieval ranking. This function only adds a light
    preference for YAML configuration examples when the user explicitly asks
    for a config example or config structure.
    """
    query_lower = query.lower()

    wants_config_example = (
        "config" in query_lower
        and any(
            word in query_lower
            for word in ["look like", "example", "yaml", "write", "structure"]
        )
    )

    if not wants_config_example:
        return results

    reranked: list[RetrievalResult] = []

    for result in results:
        doc = result.document
        score = result.score

        if doc.source_type in {"example_config", "production_config", "yaml_config"}:
            score += 0.5

        if doc.source_type == "example_config":
            score += 0.2

        relative_path = doc.metadata.get("relative_path")
        if relative_path and "index" in relative_path.lower():
            score += 0.2

        reranked.append(RetrievalResult(document=doc, score=score))

    reranked.sort(key=lambda result: result.score, reverse=True)

    return reranked


def retrieve_with_mmore_native(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    index_config_path: str | Path = DEFAULT_MMORE_INDEX_CONFIG_PATH,
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents using MMORE's native retriever.
    """
    config_path = resolve_project_path(config_path)
    index_config_path = resolve_project_path(index_config_path)

    try:
        retriever = load_retriever_from_mmore_config(config_path)
    except KeyError as error:
        if str(error).strip("'") == "model_name":
            try:
                retriever = create_retriever_from_githelp_configs(
                    retriever_config_path=config_path,
                    index_config_path=index_config_path,
                )
            except Exception as fallback_error:
                raise MMoreRetrievalError(
                    "MMORE could not load model metadata from the Milvus index "
                    "or from GitHelp's MMORE config files."
                ) from fallback_error
        else:
            raise

    except RuntimeError as error:
        if "MMORE index metadata is incomplete" in str(error):
            try:
                retriever = create_retriever_from_githelp_configs(
                    retriever_config_path=config_path,
                    index_config_path=index_config_path,
                )
            except Exception as fallback_error:
                raise MMoreRetrievalError(
                    "MMORE could not load model metadata from the Milvus index "
                    "or from GitHelp's MMORE config files."
                ) from fallback_error
        else:
            raise

    raw_k = max(top_k, MIN_MMORE_RAW_RESULTS)
    load_collection_for_search(retriever, collection_name)

    raw_results = retriever.retrieve(
        query=query,
        collection_name=collection_name,
        k=raw_k,
        output_fields=["text"],
        search_type=search_type,
    )

    results = [
        mmore_result_to_retrieval_result(result)
        for result in raw_results
    ]

    reranked_results = rerank_for_githelp_intent(query, results)
    return tag_results_with_mmore_mode(reranked_results, MMORE_NATIVE_MODE)
