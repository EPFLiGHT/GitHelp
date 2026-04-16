from __future__ import annotations

import json
from pathlib import Path

from docask.data_models import DocumentRecord
from docask.loaders.markdown_loader import load_markdown_documents

# takes several sources and produces an unique corpus
def build_corpus_from_markdown(docs_path: str | Path) -> list[DocumentRecord]:
    return load_markdown_documents(docs_path)


def save_corpus_jsonl(documents: list[DocumentRecord], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")