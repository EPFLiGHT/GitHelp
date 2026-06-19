from __future__ import annotations

import json
from pathlib import Path

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_result_mapping import (
    MMORE_CORPUS_FALLBACK_MODE,
    mmore_result_to_retrieval_result,
    tag_results_with_mmore_mode,
)
from githelp.utils.paths import resolve_project_path


DEFAULT_MMORE_CORPUS_PATH = "data/processed/mmore_corpus.jsonl"


def resolve_mmore_corpus_path(corpus_path: str | Path | None) -> Path:
    """
    Resolve the MMORE-compatible corpus used by the safe MMORE fallback.

    If GitHelp is given data/projects/<project>/corpus.jsonl, prefer the sibling
    data/projects/<project>/mmore_corpus.jsonl. Otherwise use the default
    exported MMORE corpus path.
    """
    candidates: list[Path] = []

    if corpus_path is not None:
        resolved_corpus_path = resolve_project_path(corpus_path)
        if resolved_corpus_path.name == "mmore_corpus.jsonl":
            candidates.append(resolved_corpus_path)
        else:
            candidates.append(resolved_corpus_path.with_name("mmore_corpus.jsonl"))
            candidates.append(resolved_corpus_path)

    candidates.append(resolve_project_path(DEFAULT_MMORE_CORPUS_PATH))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Could not find an MMORE corpus. Export one with "
        "`python scripts/export_mmore_corpus.py`."
    )


def load_mmore_corpus_documents(mmore_corpus_path: str | Path) -> list[DocumentRecord]:
    """Load GitHelp documents from an exported MMORE JSONL corpus."""
    documents: list[DocumentRecord] = []
    path = Path(mmore_corpus_path)

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            sample = json.loads(line)
            text = str(sample.get("text", ""))
            metadata = sample.get("metadata", {})
            raw_id = metadata.get("doc_id") if isinstance(metadata, dict) else ""
            result = mmore_result_to_retrieval_result(
                {
                    "id": raw_id,
                    "text": text,
                    "score": 0.0,
                }
            )
            documents.append(result.document)

    return documents


def retrieve_from_mmore_corpus(
    query: str,
    top_k: int,
    corpus_path: str | Path | None,
) -> list[RetrievalResult]:
    """
    Retrieve from the exported MMORE corpus without loading native MMORE models.
    """
    from githelp.retrieval.simple_retriever import retrieve as simple_retrieve

    mmore_corpus_path = resolve_mmore_corpus_path(corpus_path)
    documents = load_mmore_corpus_documents(mmore_corpus_path)
    results = simple_retrieve(query, documents, top_k=top_k)
    return tag_results_with_mmore_mode(results, MMORE_CORPUS_FALLBACK_MODE)
