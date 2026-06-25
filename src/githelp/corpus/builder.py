from __future__ import annotations

import json
from pathlib import Path

from githelp.data_models import DocumentRecord
from githelp.extractors.python_doc_extractor import extract_python_docs
from githelp.loaders.markdown_loader import load_markdown_documents
from githelp.loaders.repo_structure_loader import load_repo_structure_document
from githelp.loaders.yaml_config_loader import load_yaml_documents


"""
Corpus building utilities.

This module combines all supported documentation sources into a single corpus
of DocumentRecord objects. The corpus can include human-written documentation,
Python docstrings, YAML configuration files, and a synthetic repository
structure document.
"""


def build_corpus(
    docs_path: str | Path,
    code_path: str | Path | None = None,
    *,
    project_name: str = "project",
    package_name: str | None = None,
    repo_path: str | Path | None = None,
    include_yaml_configs: bool = False,
    yaml_config_paths: list[str | Path] | None = None,
    include_repo_structure: bool = False,
    repo_structure_max_depth: int = 6,
) -> list[DocumentRecord]:
    """
    Build a unified GitHelp corpus from several documentation sources.

    Parameters
    ----------
    docs_path:
        Path to the main documentation directory.
    code_path:
        Optional path to the Python source directory.
    project_name:
        Name of the project. Stored in metadata.
    package_name:
        Optional Python package name used to build fully qualified module names.
        For example, use "mmore" when indexing src/mmore.
    repo_path:
        Optional repository root. Used for YAML relative paths and repository
        structure extraction.
    include_yaml_configs:
        Whether to include YAML configuration files in the corpus.
    yaml_config_paths:
        Paths to scan for YAML configuration files.
    include_repo_structure:
        Whether to add a synthetic document describing the repository tree.
    repo_structure_max_depth:
        Maximum depth used when building the repository tree.

    Returns
    -------
    list[DocumentRecord]
        Unified corpus ready to be saved, indexed, or inspected.
    """
    documents: list[DocumentRecord] = []

    markdown_docs = load_markdown_documents(
        docs_path,
        project_name=project_name,
    )
    print(f"Loaded {len(markdown_docs)} markdown documents")
    documents.extend(markdown_docs)

    if code_path is not None:
        code_docs = extract_python_docs(
            code_path,
            package_name=package_name,
            project_name=project_name,
        )
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


def save_corpus_jsonl(
    documents: list[DocumentRecord],
    output_path: str | Path,
) -> None:
    """
    Save a corpus as a JSONL file.

    Each line contains one serialized DocumentRecord. JSONL is convenient
    because it can be streamed, inspected manually, and consumed by indexing
    pipelines.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for doc in documents:
            file.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")


def summarize_corpus(documents: list[DocumentRecord]) -> dict[str, int]:
    """
    Count documents by source type.

    This is mainly used as a quick sanity check after corpus construction.
    """
    summary: dict[str, int] = {}

    for doc in documents:
        summary[doc.source_type] = summary.get(doc.source_type, 0) + 1

    return summary
