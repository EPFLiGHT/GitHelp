from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from docask.data_models import DocumentRecord


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass
class RetrievalResult:
    document: DocumentRecord
    score: float


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def load_corpus(corpus_path: str | Path) -> list[DocumentRecord]:
    corpus_path = Path(corpus_path)

    documents: list[DocumentRecord] = []
    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            documents.append(DocumentRecord(**data))

    return documents


def retrieve(
    query: str,
    documents: list[DocumentRecord],
    top_k: int = 5,
) -> list[RetrievalResult]:
    query_lower = query.lower()
    query_tokens = _tokenize(query)

    if not query_tokens:
        return []

    query_token_set = set(query_tokens)
    query_identifiers = {
        token
        for token in query_tokens
        if "_" in token or "." in token
    }

    user_doc_words = {"how", "install", "run", "use", "start", "setup", "configure", "command"}

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
            is_specific_identifier = "_" in symbol_lower or len(symbol_lower) >= 8

            # Strong boost only for explicit code-like identifiers.
            # Examples: get_latest_reports, build_rag_pipeline, PDFProcessor
            if symbol_lower in query_lower:
                exact_symbol_match = True
                score += 10.0 if is_specific_identifier else 1.5

            # Handles "get latest reports" instead of "get_latest_reports".
            symbol_parts = symbol_lower.split("_")
            if len(symbol_parts) > 1 and all(part in query_token_set for part in symbol_parts):
                exact_symbol_match = True
                score += 6.0

            # Handles explicit identifier tokens.
            if symbol_lower in query_identifiers:
                exact_symbol_match = True
                score += 8.0 if is_specific_identifier else 1.5

        if doc.signature and doc.signature.lower() in query_lower:
            score += 4.0

        if doc.module_name and doc.module_name.lower() in query_lower:
            score += 3.0

        if doc.title and doc.title.lower() in query_lower:
            score += 2.0

        if query_lower in searchable_lower:
            score += 1.0

        # If the user asks for a signature, prefer the exact symbol match.
        if "signature" in query_token_set and doc.source_type.startswith("python") and not exact_symbol_match:
            score -= 3.0

        # Prefer user-facing documentation for user-facing questions.
        if doc.source_type.startswith("markdown") and query_token_set & user_doc_words:
            score += 2.0

        results.append(RetrievalResult(document=doc, score=score))

    results.sort(key=lambda result: result.score, reverse=True)
    return results[:top_k]