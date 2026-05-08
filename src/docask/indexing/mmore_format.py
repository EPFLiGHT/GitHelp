from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docask.data_models import DocumentRecord
from docask.retrieval.simple_retriever import load_corpus


"""
Utilities for exporting a DocAsk corpus to MMORE-compatible JSONL.

DocAsk uses DocumentRecord internally. MMORE expects input samples with a
"text" field, optional modalities, and metadata. This module bridges the two
formats so that a DocAsk corpus can be indexed with MMORE.
"""


def document_to_mmore_sample(doc: DocumentRecord) -> dict[str, Any]:
    """
    Convert one DocumentRecord into one MMORE indexing sample.

    The text field contains a small DocAsk metadata header followed by the
    actual document content. The header is intentionally stored in text so it
    can be recovered after MMORE retrieval.
    """
    metadata = {
        **doc.metadata,
        "doc_id": doc.doc_id,
        "source_type": doc.source_type,
        "title": doc.title,
        "file_path": doc.file_path,
        "section_title": doc.section_title,
        "module_name": doc.module_name,
        "symbol_name": doc.symbol_name,
        "signature": doc.signature,
        "language": doc.language,
        "tags": doc.tags,
    }

    metadata = {
        key: value
        for key, value in metadata.items()
        if value is not None
    }

    source_header = "\n".join(
        part
        for part in [
            f"DocAsk ID: {doc.doc_id}",
            f"Source type: {doc.source_type}",
            f"Title: {doc.title}" if doc.title else None,
            (
                f"Relative path: {doc.metadata.get('relative_path')}"
                if doc.metadata.get("relative_path")
                else None
            ),
            f"Section: {doc.section_title}" if doc.section_title else None,
            f"Module: {doc.module_name}" if doc.module_name else None,
            f"Symbol: {doc.symbol_name}" if doc.symbol_name else None,
            f"Signature: {doc.signature}" if doc.signature else None,
        ]
        if part
    )

    text = f"{source_header}\n\nContent:\n{doc.content}"

    return {
        "text": text,
        "modalities": [],
        "metadata": metadata,
    }


def export_corpus_to_mmore_jsonl(
    *,
    corpus_path: str | Path,
    output_path: str | Path,
) -> None:
    """
    Export a DocAsk JSONL corpus to MMORE's JSONL input format.

    Parameters
    ----------
    corpus_path:
        Path to the DocAsk corpus JSONL file.
    output_path:
        Path where the MMORE-compatible JSONL file will be written.
    """
    corpus_path = Path(corpus_path)
    output_path = Path(output_path)

    documents = load_corpus(corpus_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for doc in documents:
            sample = document_to_mmore_sample(doc)
            file.write(json.dumps(sample, ensure_ascii=False) + "\n")