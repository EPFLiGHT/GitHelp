from __future__ import annotations

from pathlib import Path

from docask.retrieval.extractive_answerer import answer_from_sources
from docask.retrieval.prompting import build_user_prompt
from docask.retrieval.simple_retriever import RetrievalResult, load_corpus, retrieve


def prepare_answer_prompt(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
) -> tuple[str, list[RetrievalResult]]:
    documents = load_corpus(corpus_path)
    results = retrieve(question, documents, top_k=top_k)
    prompt = build_user_prompt(question, results)

    return prompt, results


def answer_question(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
) -> tuple[str, list[RetrievalResult]]:
    documents = load_corpus(corpus_path)
    results = retrieve(question, documents, top_k=top_k)
    answer = answer_from_sources(question, results)

    return answer, results