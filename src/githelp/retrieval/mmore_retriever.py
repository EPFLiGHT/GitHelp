from __future__ import annotations

from pathlib import Path

from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_corpus import (
    DEFAULT_MMORE_CORPUS_PATH,
    load_mmore_corpus_documents as _load_mmore_corpus_documents,
    resolve_mmore_corpus_path as _resolve_mmore_corpus_path,
    retrieve_from_mmore_corpus as _retrieve_from_mmore_corpus,
)
from githelp.retrieval.mmore_errors import MMoreRetrievalError
from githelp.retrieval.mmore_native import (
    DEFAULT_MMORE_INDEX_CONFIG_PATH,
    MIN_MMORE_RAW_RESULTS,
    create_retriever_from_githelp_configs as _create_retriever_from_githelp_configs,
    load_collection_for_search as _load_collection_for_search,
    load_githelp_mmore_model_configs as _load_githelp_mmore_model_configs,
    load_retriever_from_mmore_config as _load_retriever_from_mmore_config,
    retrieve_with_mmore_native as _retrieve_with_mmore_native,
)
from githelp.retrieval.mmore_result_mapping import (
    MMORE_CORPUS_FALLBACK_MODE,
    MMORE_NATIVE_MODE,
    MMORE_RETRIEVAL_MODE_METADATA_KEY,
    get_result_field as _get_result_field,
    mmore_result_to_retrieval_result as _mmore_result_to_retrieval_result,
    parse_githelp_header as _parse_githelp_header,
)
from githelp.retrieval.mmore_subprocess import (
    MMORE_WORKER_RESULT_PREFIX,
    deserialize_results,
    retrieve_with_mmore_subprocess as _retrieve_with_mmore_subprocess,
    serialize_results as _serialize_results,
)


__all__ = [
    "DEFAULT_MMORE_CORPUS_PATH",
    "DEFAULT_MMORE_INDEX_CONFIG_PATH",
    "MIN_MMORE_RAW_RESULTS",
    "MMORE_CORPUS_FALLBACK_MODE",
    "MMORE_NATIVE_MODE",
    "MMORE_RETRIEVAL_MODE_METADATA_KEY",
    "MMORE_WORKER_RESULT_PREFIX",
    "_create_retriever_from_githelp_configs",
    "_get_result_field",
    "_load_collection_for_search",
    "_load_githelp_mmore_model_configs",
    "_load_mmore_corpus_documents",
    "_load_retriever_from_mmore_config",
    "_mmore_result_to_retrieval_result",
    "_parse_githelp_header",
    "_resolve_mmore_corpus_path",
    "_serialize_results",
    "deserialize_results",
    "retrieve_with_mmore",
]


"""
MMORE retrieval backend adapter.

This module keeps GitHelp's public MMORE retrieval entry point small:

1. try native MMORE retrieval in a subprocess;
2. if the native process fails, retrieve from the exported mmore_corpus.jsonl;
3. return standard RetrievalResult objects tagged with the actual MMORE mode.

The helper imports are intentionally re-exported with their previous private
names so existing tests and scripts keep working while the implementation is
split into focused modules.
"""


def retrieve_with_mmore(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    index_config_path: str | Path = DEFAULT_MMORE_INDEX_CONFIG_PATH,
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
    corpus_path: str | Path | None = None,
    use_subprocess: bool = True,
) -> list[RetrievalResult]:
    """
    Retrieve with MMORE.

    The native MMORE retriever is attempted first. If it fails in the child
    process, GitHelp retrieves from the exported MMORE corpus so the app stays
    usable instead of crashing.
    """
    if not use_subprocess:
        return _retrieve_with_mmore_native(
            query=query,
            top_k=top_k,
            config_path=config_path,
            index_config_path=index_config_path,
            collection_name=collection_name,
            search_type=search_type,
        )

    try:
        return _retrieve_with_mmore_subprocess(
            query=query,
            top_k=top_k,
            config_path=config_path,
            index_config_path=index_config_path,
            collection_name=collection_name,
            search_type=search_type,
        )
    except MMoreRetrievalError:
        return _retrieve_from_mmore_corpus(
            query=query,
            top_k=top_k,
            corpus_path=corpus_path,
        )
