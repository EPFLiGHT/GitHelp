from __future__ import annotations

from pathlib import Path

from docask.config import load_yaml
from docask.retrieval.base import RetrievalResult
from docask.rag.extractive_answerer import answer_from_sources
from docask.rag.llm_factory import create_llm_provider
from docask.rag.prompting import build_user_prompt
from docask.retrieval.retriever_factory import retrieve_documents
from docask.retrieval.query_expansion import expand_query

"""
High-level answering helpers.

This module connects retrieval with answer preparation. In the current
prototype, DocAsk can either prepare a grounded prompt for an LLM, return a
simple extractive answer from the top retrieved source, or generate an LLM-based
answer from the retrieved sources.
"""

def is_subjective_recommendation_question(question: str) -> bool:
    """Detect recommendation questions that cannot be answered from docs alone."""
    normalized_question = question.lower()

    asks_for_recommendation = any(
        term in normalized_question
        for term in [
            "best",
            "recommend",
            "which model should i use",
            "what model should i use",
            "which embedding model",
            "what embedding model",
        ]
    )

    mentions_user_dataset = any(
        term in normalized_question
        for term in [
            "my dataset",
            "private dataset",
            "own dataset",
            "custom dataset",
        ]
    )

    return asks_for_recommendation and mentions_user_dataset

def filter_low_value_results(
    results: list[RetrievalResult],
    question: str = "",
) -> list[RetrievalResult]:
    """
    Remove low-value or overly specific sources that are usually not useful for
    answer generation.
    """
    filtered: list[RetrievalResult] = []
    normalized_question = question.lower()

    question_mentions_colpali = "colpali" in normalized_question
    question_mentions_websearch = (
        "websearch" in normalized_question
        or "web search" in normalized_question
    )

    for result in results:
        doc = result.document

        title = (doc.title or "").lower()
        section_title = (doc.section_title or "").lower()
        content = (doc.content or "").strip()
        relative_path = (
            doc.metadata.get("relative_path")
            or doc.file_path
            or ""
        ).lower()

        is_see_also = "see also" in title or "see also" in section_title
        is_too_short = len(content) < 40

        is_colpali_source = (
            "colpali" in relative_path
            or "colpali" in title
            or "colpali" in section_title
        )

        is_websearch_source = (
            "websearch" in relative_path
            or "websearch" in title
            or "websearch" in section_title
        )

        if is_see_also or is_too_short:
            continue

        if is_colpali_source and not question_mentions_colpali:
            continue

        if is_websearch_source and not question_mentions_websearch:
            continue

        filtered.append(result)

    return filtered


def rerank_config_parameter_results(
    results: list[RetrievalResult],
    question: str,
) -> list[RetrievalResult]:
    """
    Boost configuration-like sources when the question asks about config
    parameters.
    """
    normalized_question = question.lower()

    asks_about_config_parameters = any(
        term in normalized_question
        for term in [
            "parameters",
            "config",
            "configuration",
            "fields",
            "contain",
        ]
    )

    if not asks_about_config_parameters:
        return results

    def bonus(result: RetrievalResult) -> int:
        doc = result.document

        title = (doc.title or "").lower()
        content = (doc.content or "").lower()
        relative_path = (
            doc.metadata.get("relative_path")
            or doc.file_path
            or ""
        ).lower()
        source_type = (doc.source_type or "").lower()

        score = 0

        if "config" in relative_path or "config" in title:
            score += 4

        if source_type in {"example_config", "production_config"}:
            score += 4

        for key in [
            "db_path",
            "collection_name",
            "create_collection",
            "dim",
            "metric_type",
            "milvus:",
        ]:
            if key in content:
                score += 2

        return score

    return sorted(
        results,
        key=lambda result: (bonus(result), result.score),
        reverse=True,
    )


def filter_exact_symbol_results(
    results: list[RetrievalResult],
    question: str,
) -> list[RetrievalResult]:
    """
    Keep only exact symbol matches when the question explicitly mentions a
    fully qualified symbol.

    This avoids treating generic words such as "indexing" as a match for the
    Python symbol "index".
    """
    normalized_question = question.lower()

    exact_matches: list[RetrievalResult] = []

    for result in results:
        doc = result.document

        candidates = []

        if doc.title and "." in doc.title:
            candidates.append(doc.title)

        if doc.module_name and doc.symbol_name:
            candidates.append(f"{doc.module_name}.{doc.symbol_name}")

        for candidate in candidates:
            if candidate.lower() in normalized_question:
                exact_matches.append(result)
                break

    if exact_matches:
        return exact_matches

    return results


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
    expanded_question = expand_query(question)

    results = retrieve_documents(
        query=expanded_question,
        top_k=top_k * 4,
        backend=backend,
        corpus_path=corpus_path,
    )

    results = filter_exact_symbol_results(results, question)
    results = filter_low_value_results(results, question=question)
    results = rerank_config_parameter_results(results, question)[:top_k]

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
    expanded_question = expand_query(question)

    results = retrieve_documents(
        query=expanded_question,
        top_k=top_k * 4,
        backend=backend,
        corpus_path=corpus_path,
    )

    results = filter_exact_symbol_results(results, question)
    results = filter_low_value_results(results, question=question)
    results = rerank_config_parameter_results(results, question)[:top_k]

    if is_subjective_recommendation_question(question):
        return (
            "The available sources do not provide enough information to determine "
            "the best embedding model for a private dataset. They show example "
            "models and configuration patterns, but they do not establish a general "
            "recommendation for an unseen dataset.",
            results,
        )

    if not results:
        return "I could not find relevant sources in the corpus.", results

    prompt = build_user_prompt(question, results)

    config = load_yaml(config_path)
    llm_provider = create_llm_provider(config)

    answer = llm_provider.generate(prompt)

    return answer, results