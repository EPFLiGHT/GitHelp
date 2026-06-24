from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from githelp.config import load_yaml
from githelp.project_profiles.factory import create_project_profile
from githelp.rag.extractive_answerer import answer_from_sources
from githelp.rag.llm_factory import create_llm_provider
from githelp.rag.prompting import build_user_prompt
from githelp.rag.retrieval_query import (
    AMBIGUOUS_FOLLOWUP_RESPONSE,
    RetrievalQueryDecision,
    is_context_dependent_question,
    is_reformulation_followup,
    resolve_retrieval_query,
    rewrite_query_with_history,
)
from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.retriever_factory import retrieve_documents


__all__ = [
    "AMBIGUOUS_FOLLOWUP_RESPONSE",
    "RetrievalQueryDecision",
    "answer_question",
    "answer_question_with_llm",
    "answer_question_with_provider",
    "answer_question_with_provider_from_results",
    "is_context_dependent_question",
    "is_reformulation_followup",
    "prepare_answer_prompt",
    "resolve_retrieval_query",
    "rewrite_query_with_history",
]


"""
High-level answering helpers.

This module connects retrieval with answer preparation.

The core answering pipeline is intentionally project-agnostic. Project-specific
query expansion, filtering, reranking, or direct answering logic should live in
project profiles, not in this module.
"""


RETRIEVAL_CANDIDATE_MULTIPLIER = 8
MIN_RETRIEVAL_CANDIDATES = 40
LEXICAL_FALLBACK_CANDIDATE_MULTIPLIER = 4
MIN_LEXICAL_FALLBACK_CANDIDATES = 20


def _extract_filename_tokens(question: str) -> list[str]:
    """
    Extract explicit filename-like tokens from the question.
    """
    pattern = r"[\w.-]+\.(?:py|md|rst|yaml|yml|json|toml|txt)"
    return re.findall(pattern, question)


def _boost_filename_matches(
    results: list[RetrievalResult],
    question: str,
    boost: float = 1.0,
) -> list[RetrievalResult]:
    """
    Boost results whose relative path or title contains filenames mentioned
    explicitly in the question.
    """
    filename_tokens = [token.lower() for token in _extract_filename_tokens(question)]

    if not filename_tokens:
        return results

    boosted_results: list[RetrievalResult] = []

    for result in results:
        doc = result.document
        relative_path = str(doc.metadata.get("relative_path") or "").lower()
        title = str(doc.title or "").lower()
        haystack = f"{relative_path} {title}"

        if any(token in haystack for token in filename_tokens):
            boosted_results.append(
                RetrievalResult(
                    document=result.document,
                    score=result.score + boost,
                )
            )
        else:
            boosted_results.append(result)

    return sorted(
        boosted_results,
        key=lambda result: result.score,
        reverse=True,
    )


def _get_project_config_path(config: dict[str, Any]) -> str | None:
    """
    Get the project config path from the app config.

    This supports several possible config layouts to keep the answering
    pipeline flexible.
    """
    if "project_config_path" in config:
        return str(config["project_config_path"])

    project = config.get("project")
    if isinstance(project, dict):
        path = project.get("config_path") or project.get("project_config_path")
        if path:
            return str(path)

    return None


def _load_project_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Load the project configuration if it is referenced by the app config.

    Returns an empty dict if no project config path is available.
    """
    project_config_path = _get_project_config_path(config)

    if not project_config_path:
        return {}

    return load_yaml(project_config_path)


def _get_project_name(
    config: dict[str, Any],
    results: list[RetrievalResult] | None = None,
) -> str:
    """
    Get the indexed project name.

    Priority:
    1. app config;
    2. project config referenced by the app config;
    3. retrieved document metadata;
    4. generic fallback.
    """
    project_name = config.get("project_name")
    if project_name:
        return str(project_name)

    project_config = _load_project_config(config)
    project_name = project_config.get("project_name")
    if project_name:
        return str(project_name)

    if results:
        project_name = results[0].document.metadata.get("project_name")
        if project_name:
            return str(project_name)

    return "the indexed project"


def _resolve_corpus_path(
    corpus_path: str | Path | None,
    config: dict[str, Any],
) -> Path:
    """
    Resolve the GitHelp corpus path.

    If a corpus path is explicitly provided, use it. Otherwise, infer it from
    the indexed project name and use data/projects/{project_name}/corpus.jsonl.
    """
    if corpus_path is not None:
        return Path(corpus_path)

    project_name = _get_project_name(config)

    if project_name == "the indexed project":
        raise ValueError(
            "Could not infer the indexed project name. Provide corpus_path "
            "explicitly or define project_name in the app/project config."
        )

    return Path("data") / "projects" / project_name / "corpus.jsonl"


def _is_code_or_symbol_question(question: str) -> bool:
    """
    Detect questions that are likely to benefit from code-aware or config-aware retrieval.
    """
    question_lower = question.lower()

    code_terms = [
        "function",
        "class",
        "method",
        "signature",
        "symbol",
        "cli",
        "command",
        "config",
        "configuration",
        "yaml",
        "yml",
        "file",
        "path",
        "implemented",
        "implementation",
        "where is",
        "where are",
        "what does",
        "what do",
    ]

    return any(term in question_lower for term in code_terms)


def _contains_filename_like_token(question: str) -> bool:
    """
    Detect questions that mention an explicit file or path-like token.
    """
    question_lower = question.lower()

    filename_markers = [
        ".py",
        ".md",
        ".rst",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".txt",
        "/",
    ]

    return any(marker in question_lower for marker in filename_markers)


def _merge_results_by_doc_id(
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Merge retrieval results while keeping the best score for duplicate records.
    """
    merged: dict[str, RetrievalResult] = {}
    order: list[str] = []

    for result in results:
        doc_id = result.document.doc_id

        if doc_id not in merged:
            merged[doc_id] = result
            order.append(doc_id)
            continue

        if result.score > merged[doc_id].score:
            merged[doc_id] = result

    return [merged[doc_id] for doc_id in order]


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
    corpus_path: str | Path | None,
    top_k: int,
    backend: str,
    config_path: str | Path,
) -> tuple[list[RetrievalResult], dict[str, Any]]:
    """
    Shared retrieval pipeline used by prompt preparation and LLM answering.

    The retrieval pipeline is:
    1. load application configuration;
    2. resolve the GitHelp corpus path;
    3. create the selected project profile;
    4. expand the query using the profile;
    5. retrieve more candidates than needed;
    6. for MMORE code-oriented questions, add simple-retriever candidates;
    7. apply generic exact-symbol filtering;
    8. apply project-specific filtering and reranking;
    9. keep the final top_k results.
    """
    config = load_yaml(config_path)
    resolved_corpus_path = _resolve_corpus_path(corpus_path, config)

    project_profile = create_project_profile(config)
    expanded_question = project_profile.expand_query(question)

    # Retrieve a wider pool before profile filtering/reranking so project
    # profiles can rescue useful sources that are not in the first few raw hits.
    retrieval_top_k = max(
        top_k * RETRIEVAL_CANDIDATE_MULTIPLIER,
        MIN_RETRIEVAL_CANDIDATES,
    )

    results = retrieve_documents(
        query=expanded_question,
        top_k=retrieval_top_k,
        backend=backend,
        corpus_path=resolved_corpus_path,
    )

    should_add_lexical_results = (
        _is_code_or_symbol_question(question)
        or _contains_filename_like_token(question)
    ) and (
        backend == "mmore"
        or expanded_question != question
    )

    if should_add_lexical_results:
        simple_results = retrieve_documents(
            query=question,
            top_k=max(
                top_k * LEXICAL_FALLBACK_CANDIDATE_MULTIPLIER,
                MIN_LEXICAL_FALLBACK_CANDIDATES,
            ),
            backend="simple",
            corpus_path=resolved_corpus_path,
        )

        results = _merge_results_by_doc_id(
            [
                *results,
                *simple_results,
            ]
        )

    results = _boost_filename_matches(results, question)
    results = filter_exact_symbol_results(results, question)
    results = project_profile.filter_results(results, question)
    results = project_profile.rerank_results(results, question)

    return results[:top_k], config


def prepare_answer_prompt(
    question: str,
    corpus_path: str | Path | None = None,
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
    chat_history: list[dict[str, Any]] | None = None,
    retrieval_query: str | None = None,
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and build a prompt for LLM answer generation.

    This function does not call an LLM. It only prepares the prompt and returns
    the retrieved sources for inspection.
    """
    results, config = _retrieve_and_prepare_results(
        question=retrieval_query or question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    project_name = _get_project_name(config, results)

    prompt = build_user_prompt(
        question=question,
        results=results,
        project_name=project_name,
        chat_history=chat_history,
    )

    return prompt, results


def answer_question(
    question: str,
    corpus_path: str | Path | None = None,
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
    retrieval_query: str | None = None,
) -> tuple[str, list[RetrievalResult]]:
    """
    Retrieve sources and produce a simple extractive answer.

    This is a temporary non-LLM answering path. It is kept for testing retrieval
    before full LLM generation.
    """
    results, config = _retrieve_and_prepare_results(
        question=retrieval_query or question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    project_profile = create_project_profile(config)
    direct_answer = project_profile.answer_directly(question, results)

    if direct_answer is not None:
        return direct_answer, results

    if is_subjective_recommendation_question(question):
        return (
            "The available sources do not provide enough information to determine "
            "the best option for the user's private dataset. They show retrieved "
            "documentation and configuration examples, but they do not establish "
            "a general recommendation for an unseen dataset.",
            results,
        )

    answer = answer_from_sources(question, results)
    return answer, results


def _prepare_llm_answer_input(
    question: str,
    results: list[RetrievalResult],
    config: dict[str, Any],
    chat_history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[RetrievalResult], bool]:
    """Apply shared pre-generation checks and build the LLM prompt.

    The boolean indicates whether the returned text should be sent to the LLM.
    If it is False, the returned text is already the final answer.
    """
    project_profile = create_project_profile(config)

    if is_subjective_recommendation_question(question):
        return (
            "The available sources do not provide enough information to determine "
            "the best option for the user's private dataset. They show retrieved "
            "documentation and configuration examples, but they do not establish "
            "a general recommendation for an unseen dataset.",
            results,
            False,
        )

    if not results:
        return "I could not find relevant sources in the corpus.", results, False

    direct_answer = project_profile.answer_directly(question, results)
    if direct_answer is not None:
        return direct_answer, results, False

    project_name = _get_project_name(config, results)
    prompt = build_user_prompt(
        question=question,
        results=results,
        project_name=project_name,
        chat_history=chat_history,
    )
    return prompt, results, True


def answer_question_with_llm(
    question: str,
    corpus_path: str | Path | None = None,
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
    chat_history: list[dict[str, Any]] | None = None,
    retrieval_query: str | None = None,
) -> tuple[str, list[RetrievalResult]]:
    """Retrieve sources and generate a source-grounded LLM answer.

    The LLM provider and project profile are selected from the app configuration file.
    """
    llm_provider = None

    if retrieval_query is None and is_context_dependent_question(question):
        rewrite_config = load_yaml(config_path)
        llm_provider = create_llm_provider(rewrite_config)
        decision = resolve_retrieval_query(
            question=question,
            chat_history=chat_history,
            llm_provider=llm_provider,
        )
        if decision.is_ambiguous:
            return AMBIGUOUS_FOLLOWUP_RESPONSE, []
        retrieval_query = decision.retrieval_query

    results, config = _retrieve_and_prepare_results(
        question=retrieval_query or question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    prompt_or_answer, results, should_generate = _prepare_llm_answer_input(
        question=question,
        results=results,
        config=config,
        chat_history=chat_history,
    )

    if not should_generate:
        return prompt_or_answer, results

    if llm_provider is None:
        llm_provider = create_llm_provider(config)
    answer = llm_provider.generate(prompt_or_answer)
    return answer, results


def answer_question_with_provider(
    question: str,
    llm_provider,
    corpus_path: str | Path | None = None,
    top_k: int = 5,
    backend: str = "simple",
    config_path: str | Path = "configs/app_config.yaml",
    chat_history: list[dict[str, Any]] | None = None,
    retrieval_query: str | None = None,
) -> tuple[str, list[RetrievalResult]]:
    """Retrieve sources and generate an answer with a provided LLM provider.

    This is useful for Streamlit, where the provider can be cached and reused
    across questions.
    """
    if retrieval_query is None:
        decision = resolve_retrieval_query(
            question=question,
            chat_history=chat_history,
            llm_provider=llm_provider,
        )
        if decision.is_ambiguous:
            return AMBIGUOUS_FOLLOWUP_RESPONSE, []
        retrieval_query = decision.retrieval_query

    results, config = _retrieve_and_prepare_results(
        question=retrieval_query or question,
        corpus_path=corpus_path,
        top_k=top_k,
        backend=backend,
        config_path=config_path,
    )

    prompt_or_answer, results, should_generate = _prepare_llm_answer_input(
        question=question,
        results=results,
        config=config,
        chat_history=chat_history,
    )

    if not should_generate:
        return prompt_or_answer, results

    answer = llm_provider.generate(prompt_or_answer)
    return answer, results


def answer_question_with_provider_from_results(
    question: str,
    llm_provider,
    results: list[RetrievalResult],
    config_path: str | Path = "configs/app_config.yaml",
    chat_history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[RetrievalResult]]:
    """
    Generate an answer from already retrieved sources.

    This is used for lightweight reformulation follow-ups where the user asks
    for the previous answer to be explained differently.
    """
    config = load_yaml(config_path)

    prompt_or_answer, results, should_generate = _prepare_llm_answer_input(
        question=question,
        results=results,
        config=config,
        chat_history=chat_history,
    )

    if not should_generate:
        return prompt_or_answer, results

    answer = llm_provider.generate(prompt_or_answer)
    return answer, results
