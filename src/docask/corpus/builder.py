from __future__ import annotations

import json
from pathlib import Path

from docask.data_models import DocumentRecord
from docask.extractors.python_doc_extractor import extract_python_docs
from docask.loaders.markdown_loader import load_markdown_documents
from docask.loaders.repo_structure_loader import load_repo_structure_document
from docask.loaders.yaml_loader import load_yaml_documents


def build_corpus(
    docs_path: str | Path,
    code_path: str | Path | None = None,
    *,
    project_name: str = "project",
    repo_path: str | Path | None = None,
    include_yaml_configs: bool = False,
    yaml_config_paths: list[str | Path] | None = None,
    include_repo_structure: bool = False,
    repo_structure_max_depth: int = 4,
) -> list[DocumentRecord]:
    documents: list[DocumentRecord] = []

    markdown_docs = load_markdown_documents(docs_path)
    print(f"Loaded {len(markdown_docs)} markdown documents")
    documents.extend(markdown_docs)

    if code_path is not None:
        code_docs = extract_python_docs(code_path)
        print(f"Loaded {len(code_docs)} code documents")
        documents.extend(code_docs)

    if include_yaml_configs:
        yaml_paths = yaml_config_paths or []
        yaml_docs = load_yaml_documents(
            yaml_paths,
            repo_root=repo_path,
            project_name=project_name,
        )
        print(f"Loaded {len(yaml_docs)} YAML config documents")
        documents.extend(yaml_docs)

    if include_repo_structure and repo_path is not None:
        repo_structure_docs = load_repo_structure_document(
            repo_path,
            project_name=project_name,
            max_depth=repo_structure_max_depth,
        )
        print(f"Loaded {len(repo_structure_docs)} repo structure documents")
        documents.extend(repo_structure_docs)

    return documents


def save_corpus_jsonl(documents: list[DocumentRecord], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")


def summarize_corpus(documents: list[DocumentRecord]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for doc in documents:
        summary[doc.source_type] = summary.get(doc.source_type, 0) + 1
    return summary