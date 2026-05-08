from __future__ import annotations

from pathlib import Path

from docask.retrieval.extractive_answerer import answer_from_sources
from docask.retrieval.prompting import build_user_prompt
from docask.retrieval.retriever_factory import retrieve_documents
from docask.retrieval.simple_retriever import RetrievalResult


def prepare_answer_prompt(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
) -> tuple[str, list[RetrievalResult]]:
    results = retrieve_documents(
        query=question,
        top_k=top_k,
        backend=backend,
        corpus_path=corpus_path,
    )

    prompt = build_user_prompt(question, results)
    return prompt, results


def answer_question(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
) -> tuple[str, list[RetrievalResult]]:
    results = retrieve_documents(
        query=question,
        top_k=top_k,
        backend=backend,
        corpus_path=corpus_path,
    )

    answer = answer_from_sources(question, results)
    return answer, results