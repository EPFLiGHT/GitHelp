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

    return {
        "text": doc.content,
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