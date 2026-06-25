from __future__ import annotations


def expand_query(query: str) -> str:
    """
    Expand natural-language queries with project-specific retrieval terms.

    This lightweight rewriting step helps the simple retriever match user
    questions with the vocabulary used in documentation and configuration files.
    """
    normalized_query = query.lower()

    if "colpali" in normalized_query and "milvus" in normalized_query:
        return (
            query
            + " colpali examples/colpali/config_index.yml config_index.yml "
            + "milvus db_path collection_name create_collection dim metric_type "
            + "parquet_path yaml configuration"
        )

    if "colpali" in normalized_query:
        return (
            query
            + " colpali examples/colpali/config_index.yml config_index.yml "
            + "parquet_path milvus db_path collection_name create_collection dim metric_type "
            + "yaml configuration"
        )

    indexing_terms = [
        "indexing",
        "index",
        "configuration",
        "config",
        "config file",
        "indexer",
        "dense_model",
        "sparse_model",
        "db",
        "collection_name",
        "documents_path",
    ]

    if "index" in normalized_query or "indexing" in normalized_query:
        return query + " " + " ".join(indexing_terms)

    return query
