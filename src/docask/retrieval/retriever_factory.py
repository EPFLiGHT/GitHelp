from __future__ import annotations

from pathlib import Path

from docask.retrieval.simple_retriever import load_corpus, retrieve as simple_retrieve
from docask.retrieval.simple_retriever import RetrievalResult


def retrieve_documents(
    *,
    query: str,
    top_k: int,
    backend: str = "simple",
    corpus_path: str | Path = "data/processed/corpus.jsonl",
) -> list[RetrievalResult]:
    if backend == "simple":
        documents = load_corpus(corpus_path)
        return simple_retrieve(query, documents, top_k=top_k)

    if backend == "mmore":
        from docask.retrieval.mmore_retriever import retrieve_with_mmore

        return retrieve_with_mmore(query=query, top_k=top_k)

    raise ValueError(f"Unknown retrieval backend: {backend}")