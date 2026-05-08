from __future__ import annotations

import json
from pathlib import Path

from docask.data_models import DocumentRecord
from docask.retrieval.simple_retriever import load_corpus


def document_to_mmore_sample(doc: DocumentRecord) -> dict:
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

    metadata = {key: value for key, value in metadata.items() if value is not None}
    
    source_header = "\n".join(
        part
        for part in [
            f"DocAsk ID: {doc.doc_id}",
            f"Source type: {doc.source_type}",
            f"Title: {doc.title}" if doc.title else None,
            f"Relative path: {doc.metadata.get('relative_path')}" if doc.metadata.get("relative_path") else None,
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
    corpus_path = Path(corpus_path)
    output_path = Path(output_path)

    documents = load_corpus(corpus_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            sample = document_to_mmore_sample(doc)
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")