from __future__ import annotations

from pathlib import Path

from docask.config import load_yaml
from docask.project_profiles.factory import create_project_profile
from docask.rag.extractive_answerer import answer_from_sources
from docask.rag.llm_factory import create_llm_provider
from docask.rag.prompting import build_user_prompt
from docask.retrieval.base import RetrievalResult
from docask.retrieval.retriever_factory import retrieve_documents


"""
High-level answering helpers.

This module connects retrieval with answer preparation.

The core answering pipeline is intentionally project-agnostic. Project-specific
query expansion, filtering, reranking, or direct answering logic should live in
project profiles, not in this module.
"""


def is_subjective_recommendation_question(question: str) -> bool:
    """
    Detect recommendation questions that cannot be answered from retrieved
    documentation alone.
    """
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
        candidates: list[str] = []

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


def _retrieve_and_prepare_results(
    question: str,
    corpus_path: str | Path,
    top_k: int,
    backend: str,
    config_path: str | Path,
) -> tuple[list[RetrievalResult], dict]:
    """
    Shared retrieval pipeline used by prompt preparation and LLM answering.

    The retrieval pipeline is:
    1. load application configuration;
    2. create the selected project profile;
    3. expand the query using the profile;
    4. retrieve more candidates than needed;
    5. apply generic exact-symbol filtering;
    6. apply project-specific filtering and reranking;
    7. keep the final top_k results.
    """
    config = load_yaml(config_path)
    project_profile = create_project_profile(config)

    expanded_question = project_profile.expand_query(question)

    results = retrieve_documents(
        query=expanded_question,
        top_k=top_k * 4,
        backend=backend,
        corpus_path=corpus_path,
    )

    results = filter_exact_symbol_results(results, question)
    results = project_profile.filter_results(results, question)
    results = project_profile.rerank_results(results, question)[:top_k]

    return results, config


def prepare_answer_prompt(
    question: str,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and build a prompt for LLM answer generation.

    This function does not call an LLM. It only prepares the prompt and returns
    the retrieved sources for inspection.
    """
    results, _ = _retrieve_and_prepare_results(
        question=question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
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

    The LLM provider and project profile are selected from the app
    configuration file.
    """
    results, config = _retrieve_and_prepare_results(
        question=question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    project_profile = create_project_profile(config)

    if is_subjective_recommendation_question(question):
        return (
            "The available sources do not provide enough information to determine "
            "the best option for the user's private dataset. They show retrieved "
            "documentation and configuration examples, but they do not establish "
            "a general recommendation for an unseen dataset.",
            results,
        )

    if not results:
        return "I could not find relevant sources in the corpus.", results

    direct_answer = project_profile.answer_directly(question, results)

    if direct_answer is not None:
        return direct_answer, results

    prompt = build_user_prompt(question, results)

    llm_provider = create_llm_provider(config)
    answer = llm_provider.generate(prompt)

    return answer, results


def answer_question_with_provider(
    question: str,
    llm_provider,
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and generate a source-grounded LLM answer using an
    already-created LLM provider.

    This is useful for Streamlit, where the provider can be cached and reused
    across questions.
    """
    results, config = _retrieve_and_prepare_results(
        question=question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    project_profile = create_project_profile(config)

    if is_subjective_recommendation_question(question):
        return (
            "The available sources do not provide enough information to determine "
            "the best option for the user's private dataset. They show retrieved "
            "documentation and configuration examples, but they do not establish "
            "a general recommendation for an unseen dataset.",
            results,
        )

    if not results:
        return "I could not find relevant sources in the corpus.", results

    direct_answer = project_profile.answer_directly(question, results)

    if direct_answer is not None:
        return direct_answer, results

    prompt = build_user_prompt(question, results)
    answer = llm_provider.generate(prompt)

    return answer, results