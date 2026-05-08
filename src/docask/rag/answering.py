from __future__ import annotations

from pathlib import Path

from docask.retrieval.base import RetrievalResult
from docask.rag.extractive_answerer import answer_from_sources
from docask.rag.prompting import build_user_prompt
from docask.retrieval.retriever_factory import retrieve_documents


"""
High-level answering helpers.

This module connects retrieval with answer preparation. In the current
prototype, DocAsk can either prepare a grounded prompt for an LLM or return a
simple extractive answer from the top retrieved source.
"""


def prepare_answer_prompt(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and build a prompt for LLM answer generation.

    This function does not call an LLM. It only prepares the prompt and returns
    the retrieved sources for inspection.
    """
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
    """
    Retrieve sources and produce a simple extractive answer.

    This is a temporary non-LLM answering path. The final RAG version should
    use prepare_answer_prompt followed by an LLM call.
    """
    results = retrieve_documents(
        query=question,
        top_k=top_k,
        backend=backend,
        corpus_path=corpus_path,
    )

    answer = answer_from_sources(question, results)

    return answer, results