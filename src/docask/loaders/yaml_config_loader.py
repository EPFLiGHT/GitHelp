from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docask.data_models import DocumentRecord


"""
Loader for YAML configuration files.

This module converts YAML files into DocumentRecord objects so that DocAsk can
answer questions about project configuration examples. This is especially
useful for projects where indexing, retrieval, and RAG behavior are often 
controlled through YAML files.
"""


YAML_EXTENSIONS = (".yaml", ".yml")


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".ipynb_checkpoints",
}


def iter_yaml_files(
    base_path: str | Path,
    extensions: tuple[str, ...] = YAML_EXTENSIONS,
) -> Iterable[Path]:
    """
    Iterate over YAML files under a base directory.

    Common generated or environment directories are excluded to avoid indexing
    irrelevant configuration files.
    """
    base_path = Path(base_path)

    if not base_path.exists():
        return

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in extensions:
            continue

        if any(part in DEFAULT_EXCLUDED_DIRS for part in path.parts):
            continue

        yield path


def _detect_config_type(relative_path: str) -> str:
    """
    Infer the type of YAML configuration from its relative path.

    The type is used as the DocumentRecord source_type, which makes it possible
    to filter or explain retrieved configuration documents.
    """
    parts = Path(relative_path).parts
    lower_path = relative_path.lower()

    if "examples" in parts:
        return "example_config"

    if "production-config" in parts:
        return "production_config"

    if "configs" in parts or "config" in lower_path:
        return "yaml_config"

    return "yaml_config"


def _build_yaml_content(
    *,
    relative_path: str,
    config_type: str,
    raw_content: str,
) -> str:
    """
    Build the text content indexed for a YAML configuration file.

    Additional hints are added for common MMORE configuration files so that
    retrieval can better match user questions about indexing, RAG, or retrieval.
    """
    lower_path = relative_path.lower()
    hints: list[str] = []

    if "index" in lower_path:
        hints.extend(
            [
                "This is an indexing configuration example.",
                "Use this config to understand what an indexing config should look like.",
                "Relevant concepts: indexer, dense_model, sparse_model, db, collection_name, documents_path.",
            ]
        )

    if "rag" in lower_path:
        hints.extend(
            [
                "This is a RAG configuration example.",
                "Use this config to understand what a RAG config should look like.",
                "Relevant concepts: llm, retriever, hybrid_search_weight, k, system_prompt, mode.",
            ]
        )

    if "retriever" in lower_path:
        hints.extend(
            [
                "This is a retriever configuration example.",
                "Use this config to understand what a retriever config should look like.",
                "Relevant concepts: db, hybrid_search_weight, k, collection_name.",
            ]
        )

    return "\n".join(
        [
            f"Configuration file: {relative_path}",
            f"Configuration type: {config_type}",
            *hints,
            "",
            "YAML content:",
            raw_content.strip(),
        ]
    )


def load_yaml_documents_from_path(
    base_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    project_name: str = "project",
) -> list[DocumentRecord]:
    """
    Load YAML files from one path and convert them to DocumentRecord objects.

    Parameters
    ----------
    base_path:
        Directory to scan for YAML files.
    repo_root:
        Optional repository root used to compute stable relative paths.
    project_name:
        Project name stored in metadata.

    Returns
    -------
    list[DocumentRecord]
        YAML configuration documents.
    """
    base_path = Path(base_path)

    if not base_path.exists():
        return []

    repo_root_path = Path(repo_root) if repo_root is not None else base_path

    documents: list[DocumentRecord] = []

    for path in iter_yaml_files(base_path):
        try:
            relative_path = str(path.relative_to(repo_root_path))
        except ValueError:
            relative_path = str(path)

        raw_content = path.read_text(encoding="utf-8").strip()

        if not raw_content:
            continue

        config_type = _detect_config_type(relative_path)

        documents.append(
            DocumentRecord(
                doc_id=f"yaml::{relative_path}",
                content=_build_yaml_content(
                    relative_path=relative_path,
                    config_type=config_type,
                    raw_content=raw_content,
                ),
                source_type=config_type,
                title=f"{project_name} config - {relative_path}",
                file_path=str(path),
                section_title=None,
                language="yaml",
                metadata={
                    "relative_path": relative_path,
                    "project_name": project_name,
                    "config_type": config_type,
                },
            )
        )

    return documents


def load_yaml_documents(
    paths: list[str | Path],
    *,
    repo_root: str | Path | None = None,
    project_name: str = "project",
) -> list[DocumentRecord]:
    """
    Load YAML documents from several paths while avoiding duplicate records.

    Parameters
    ----------
    paths:
        List of directories to scan.
    repo_root:
        Optional repository root used to compute stable relative paths.
    project_name:
        Project name stored in metadata.

    Returns
    -------
    list[DocumentRecord]
        Deduplicated YAML configuration documents.
    """
    documents: list[DocumentRecord] = []
    seen_doc_ids: set[str] = set()

    for path in paths:
        path_documents = load_yaml_documents_from_path(
            path,
            repo_root=repo_root,
            project_name=project_name,
        )

        for doc in path_documents:
            if doc.doc_id in seen_doc_ids:
                continue

            seen_doc_ids.add(doc.doc_id)
            documents.append(doc)

    return documents