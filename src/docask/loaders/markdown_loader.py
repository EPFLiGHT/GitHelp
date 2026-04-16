from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docask.data_models import DocumentRecord


def iter_doc_files(base_path: str | Path, extensions: tuple[str, ...] = (".md", ".rst")) -> Iterable[Path]:
    base_path = Path(base_path)
    for path in base_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def load_markdown_documents(base_path: str | Path) -> list[DocumentRecord]:
    base_path = Path(base_path)
    documents: list[DocumentRecord] = []

    for path in iter_doc_files(base_path):
        content = path.read_text(encoding="utf-8")
        rel_path = str(path.relative_to(base_path))

        documents.append(
            DocumentRecord(
                doc_id=f"markdown::{rel_path}",
                content=content,
                source_type="markdown_doc",
                title=path.stem,
                file_path=str(path),
                metadata={"relative_path": rel_path},
            )
        )

    return documents