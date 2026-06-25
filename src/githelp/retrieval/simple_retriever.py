from __future__ import annotations

import json
import math
import re
from pathlib import Path

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult


"""
Simple local retrieval backend used during early prototyping.

This retriever loads the JSONL corpus and ranks documents with lightweight
token-overlap heuristics. It does not use embeddings or MMORE. Its purpose is
to make GitHelp usable before the final MMORE retrieval backend is connected.
"""


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")

LONG_IDENTIFIER_MIN_LENGTH = 8

STRONG_EXACT_SYMBOL_BOOST = 10.0
WEAK_EXACT_SYMBOL_BOOST = 1.5
SYMBOL_PARTS_BOOST = 6.0
IDENTIFIER_QUERY_BOOST = 8.0
WEAK_IDENTIFIER_QUERY_BOOST = 1.5
SIGNATURE_MATCH_BOOST = 4.0
MODULE_MATCH_BOOST = 3.0
TITLE_MATCH_BOOST = 2.0
FULL_QUERY_MATCH_BOOST = 1.0
UNRELATED_SIGNATURE_PENALTY = 3.0
USER_DOC_MARKDOWN_BOOST = 2.0
USER_DOC_QUERY_WORDS = {
    "how",
    "install",
    "run",
    "use",
    "start",
    "setup",
    "configure",
    "command",
}


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase code-friendly tokens.

    The pattern keeps Python-like identifiers such as function_name or
    ClassName, which are important for code documentation retrieval.
    """
    return [token.lower() for token in TOKEN_RE.findall(text)]


def load_corpus(corpus_path: str | Path) -> list[DocumentRecord]:
    """
    Load a GitHelp corpus from a JSONL file.

    Each line is expected to contain one serialized DocumentRecord.
    """
    corpus_path = Path(corpus_path)

    documents: list[DocumentRecord] = []

    with corpus_path.open("r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            documents.append(DocumentRecord(**data))

    return documents


def retrieve(
    query: str,
    documents: list[DocumentRecord],
    top_k: int = 5,
) -> list[RetrievalResult]:
    """
    Retrieve the most relevant documents with heuristic token matching.

    The score combines:
    - token overlap between the query and the document;
    - boosts for exact symbol, signature, module, or title matches;
    - a small preference for Markdown documentation when the query looks
      user-facing.
    """
    query_lower = query.lower()
    query_tokens = _tokenize(query)

    if not query_tokens:
        return []

    query_token_set = set(query_tokens)

    query_identifiers = {
        token for token in query_tokens if "_" in token or "." in token
    }

    results: list[RetrievalResult] = []

    for doc in documents:
        searchable_parts = [
            doc.title,
            doc.section_title,
            doc.module_name,
            doc.symbol_name,
            doc.signature,
            doc.content,
        ]

        searchable_text = " ".join(part for part in searchable_parts if part)
        searchable_lower = searchable_text.lower()

        doc_tokens = _tokenize(searchable_text)
        if not doc_tokens:
            continue

        doc_token_set = set(doc_tokens)

        overlap = len(query_token_set & doc_token_set)
        if overlap == 0:
            continue

        score = overlap / math.sqrt(len(doc_token_set))
        exact_symbol_match = False

        if doc.symbol_name:
            symbol_lower = doc.symbol_name.lower()
            is_specific_identifier = (
                "_" in symbol_lower or len(symbol_lower) >= LONG_IDENTIFIER_MIN_LENGTH
            )

            # Strongly boost explicit code symbol matches.
            if symbol_lower in query_lower:
                exact_symbol_match = True
                score += (
                    STRONG_EXACT_SYMBOL_BOOST
                    if is_specific_identifier
                    else WEAK_EXACT_SYMBOL_BOOST
                )

            # Also match queries written with spaces instead of underscores.
            symbol_parts = symbol_lower.split("_")
            if len(symbol_parts) > 1 and all(
                part in query_token_set for part in symbol_parts
            ):
                exact_symbol_match = True
                score += SYMBOL_PARTS_BOOST

            if symbol_lower in query_identifiers:
                exact_symbol_match = True
                score += (
                    IDENTIFIER_QUERY_BOOST
                    if is_specific_identifier
                    else WEAK_IDENTIFIER_QUERY_BOOST
                )

        if doc.signature and doc.signature.lower() in query_lower:
            score += SIGNATURE_MATCH_BOOST

        if doc.module_name and doc.module_name.lower() in query_lower:
            score += MODULE_MATCH_BOOST

        if doc.title and doc.title.lower() in query_lower:
            score += TITLE_MATCH_BOOST

        if query_lower in searchable_lower:
            score += FULL_QUERY_MATCH_BOOST

        # If the user asks for a signature, avoid returning unrelated code docs.
        if (
            "signature" in query_token_set
            and doc.source_type.startswith("python")
            and not exact_symbol_match
        ):
            score -= UNRELATED_SIGNATURE_PENALTY

        # For user-facing questions, prefer human-written documentation.
        if (
            doc.source_type.startswith("markdown")
            and query_token_set & USER_DOC_QUERY_WORDS
        ):
            score += USER_DOC_MARKDOWN_BOOST
        results.append(RetrievalResult(document=doc, score=score))

    results.sort(key=lambda result: result.score, reverse=True)

    return results[:top_k]
