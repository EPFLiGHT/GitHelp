from __future__ import annotations

from pathlib import Path

from docask.config import load_yaml
from docask.retrieval.base import RetrievalResult
from docask.rag.extractive_answerer import answer_from_sources
from docask.rag.llm_factory import create_llm_provider
from docask.rag.prompting import build_user_prompt
from docask.retrieval.retriever_factory import retrieve_documents


"""
High-level answering helpers.

This module connects retrieval with answer preparation. In the current
prototype, DocAsk can either prepare a grounded prompt for an LLM, return a
simple extractive answer from the top retrieved source, or generate an LLM-based
answer from the retrieved sources.
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

    This is a temporary non-LLM answering path. It is kept for testing retrieval
    before full LLM generation.
    """
    results = retrieve_documents(
        query=question,
        top_k=top_k,
        backend=backend,
        corpus_path=corpus_path,
    )

    answer = answer_from_sources(question, results)

    return answer, results


def answer_question_with_llm(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and generate a source-grounded LLM answer.

    The LLM provider is selected from the app configuration file.
    """
    results = retrieve_documents(
        query=question,
        top_k=top_k,
        backend=backend,
        corpus_path=corpus_path,
    )

    if not results:
        return "I could not find relevant sources in the corpus.", results

    prompt = build_user_prompt(question, results)

    config = load_yaml(config_path)
    llm_provider = create_llm_provider(config)

    answer = llm_provider.generate(prompt)

    return answer, results