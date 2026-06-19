from __future__ import annotations

from pathlib import Path

from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.simple_retriever import load_corpus
from githelp.retrieval.simple_retriever import retrieve as simple_retrieve


"""
Factory for selecting a retrieval backend.

GitHelp can currently retrieve documents with:
- "simple": local deterministic token-overlap retriever;
- "mmore": MMORE retrieval backend.

This module gives the rest of the application a single retrieval entry point.
"""


def retrieve_documents(
    *,
    query: str,
    top_k: int,
    backend: str = "simple",
    corpus_path: str | Path = "data/processed/corpus.jsonl",
) -> list[RetrievalResult]:
    """
    Retrieve documents using the selected backend.

    Parameters
    ----------
    query:
        User question.
    top_k:
        Number of documents to retrieve.
    backend:
        Retrieval backend name. Supported values are "simple" and "mmore".
    corpus_path:
        Path to the JSONL corpus, used by the simple backend.

    Returns
    -------
    list[RetrievalResult]
        Retrieved documents with scores.
    """
    if backend == "simple":
        documents = load_corpus(corpus_path)
        return simple_retrieve(query, documents, top_k=top_k)

    if backend == "mmore":
        from githelp.retrieval.mmore_retriever import retrieve_with_mmore

        return retrieve_with_mmore(
            query=query,
            top_k=top_k,
            corpus_path=corpus_path,
        )

    raise ValueError(f"Unknown retrieval backend: {backend}")
