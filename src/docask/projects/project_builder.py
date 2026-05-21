from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def slugify_project_name(name: str) -> str:
    """
    Convert a project name into a safe folder name.
    """
    normalized = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9_-]+", "-", normalized)
    normalized = normalized.strip("-")

    return normalized or "project"


def infer_project_name(project_path: str | Path) -> str:
    """
    Infer a project name from the local repository folder name.
    """
    return slugify_project_name(Path(project_path).resolve().name)


def infer_package_name(project_path: str | Path, project_name: str) -> str:
    """
    Infer the Python package name.

    Prefer src/<project_name> when available. Otherwise, fall back to the
    project name with dashes replaced by underscores.
    """
    project_path = Path(project_path).resolve()
    candidate = project_path / "src" / project_name.replace("-", "_")

    if candidate.exists():
        return candidate.name

    return project_name.replace("-", "_")


def infer_docs_path(project_path: str | Path) -> Path:
    """
    Infer the documentation path of a project.

    Common layouts:
    - docs/source
    - docs
    """
    project_path = Path(project_path).resolve()

    docs_source = project_path / "docs" / "source"
    docs = project_path / "docs"

    if docs_source.exists():
        return docs_source

    if docs.exists():
        return docs

    return project_path


def infer_code_path(
    project_path: str | Path,
    package_name: str,
) -> Path:
    """
    Infer the code path of a Python project.

    Common layouts:
    - src/<package_name>
    - src
    - project root
    """
    project_path = Path(project_path).resolve()

    src_package = project_path / "src" / package_name
    src = project_path / "src"

    if src_package.exists():
        return src_package

    if src.exists():
        return src

    return project_path


def infer_yaml_config_paths(project_path: str | Path) -> list[str]:
    """
    Infer likely folders containing YAML configuration examples.
    """
    project_path = Path(project_path).resolve()

    candidates = [
        project_path / "examples",
        project_path / "configs",
        project_path / "config",
        project_path / "production-config",
    ]

    return [
        str(path)
        for path in candidates
        if path.exists() and path.is_dir()
    ]


def build_project_config(
    project_path: str | Path,
    project_name: str | None = None,
) -> dict[str, Any]:
    """
    Build a DocAsk project configuration dictionary for a local project.
    """
    project_path = Path(project_path).resolve()

    if not project_path.exists():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")

    if not project_path.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {project_path}")

    final_project_name = slugify_project_name(
        project_name or infer_project_name(project_path)
    )

    package_name = infer_package_name(
        project_path=project_path,
        project_name=final_project_name,
    )

    docs_path = infer_docs_path(project_path)
    code_path = infer_code_path(project_path, package_name)
    yaml_config_paths = infer_yaml_config_paths(project_path)

    return {
        "project_name": final_project_name,
        "package_name": package_name,
        "repo_path": str(project_path),
        "docs_path": str(docs_path),
        "code_path": str(code_path),
        "include_yaml_configs": bool(yaml_config_paths),
        "yaml_config_paths": yaml_config_paths,
        "include_repo_structure": True,
        "repo_structure_max_depth": 4,
        "include_extensions": [
            ".md",
            ".rst",
            ".py",
            ".yaml",
            ".yml",
        ],
        "exclude_patterns": [
            "__pycache__",
            ".ipynb_checkpoints",
            ".DS_Store",
            ".git",
            "build",
            "dist",
            ".venv",
            "venv",
        ],
    }


def write_project_config(
    config: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """
    Write a project_config.yaml file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            config,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    return output_path


def prepare_project_paths(
    docask_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> dict[str, Path | str]:
    """
    Prepare output paths for a DocAsk project.
    """
    docask_root = Path(docask_root).resolve()

    config = build_project_config(
        project_path=project_path,
        project_name=project_name,
    )

    final_project_name = config["project_name"]
    project_dir = docask_root / "data" / "projects" / final_project_name

    project_config_path = project_dir / "project_config.yaml"
    corpus_path = project_dir / "corpus.jsonl"

    return {
        "project_name": final_project_name,
        "project_dir": project_dir,
        "project_config_path": project_config_path,
        "corpus_path": corpus_path,
        "config": config,
    }


def build_corpus_for_project(
    docask_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> dict[str, str]:
    """
    Generate a project config and run the DocAsk corpus builder.

    This function expects scripts/build_corpus.py to support:
    --config <project_config_path>
    --output-path <corpus_path>
    """
    docask_root = Path(docask_root).resolve()

    prepared = prepare_project_paths(
        docask_root=docask_root,
        project_path=project_path,
        project_name=project_name,
    )

    project_config_path = Path(prepared["project_config_path"])
    corpus_path = Path(prepared["corpus_path"])
    config = prepared["config"]

    write_project_config(
        config=config,
        output_path=project_config_path,
    )

    env_pythonpath = str(docask_root / "src")

    command = [
        sys.executable,
        str(docask_root / "scripts" / "build_corpus.py"),
        "--config",
        str(project_config_path),
        "--output-path",
        str(corpus_path),
    ]

    environment = os.environ.copy()
    environment["PYTHONPATH"] = env_pythonpath

    completed_process = subprocess.run(
        command,
        cwd=str(docask_root),
        text=True,
        capture_output=True,
        env=environment,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            "Corpus build failed.\n\n"
            f"Command:\n{' '.join(command)}\n\n"
            f"stdout:\n{completed_process.stdout}\n\n"
            f"stderr:\n{completed_process.stderr}"
        )

    return {
        "project_name": str(prepared["project_name"]),
        "project_dir": str(prepared["project_dir"]),
        "project_config_path": str(project_config_path),
        "corpus_path": str(corpus_path),
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }


def export_mmore_corpus_for_project(
    docask_root: str | Path,
    corpus_path: str | Path,
    output_path: str | Path,
) -> dict[str, str]:
    """
    Export a project-specific DocAsk corpus to MMORE-compatible JSONL format.
    """
    docask_root = Path(docask_root).resolve()
    corpus_path = Path(corpus_path).resolve()
    output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(docask_root / "src")

    command = [
        sys.executable,
        str(docask_root / "scripts" / "export_mmore_corpus.py"),
        "--corpus-path",
        str(corpus_path),
        "--output-path",
        str(output_path),
    ]

    completed_process = subprocess.run(
        command,
        cwd=str(docask_root),
        text=True,
        capture_output=True,
        env=environment,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            "MMORE corpus export failed.\n\n"
            f"Command:\n{' '.join(command)}\n\n"
            f"stdout:\n{completed_process.stdout}\n\n"
            f"stderr:\n{completed_process.stderr}"
        )

    return {
        "mmore_corpus_path": str(output_path),
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }


def build_mmore_index_for_project(
    docask_root: str | Path,
    documents_path: str | Path,
    collection_name: str = "mmore_docs",
) -> dict[str, str]:
    """
    Build the MMORE index for a project-specific MMORE corpus.
    """
    docask_root = Path(docask_root).resolve()
    documents_path = Path(documents_path).resolve()

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(docask_root / "src")

    command = [
        sys.executable,
        str(docask_root / "scripts" / "build_index.py"),
        "--documents-path",
        str(documents_path),
        "--collection-name",
        collection_name,
    ]

    completed_process = subprocess.run(
        command,
        cwd=str(docask_root),
        text=True,
        capture_output=True,
        env=environment,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            "MMORE index build failed.\n\n"
            f"Command:\n{' '.join(command)}\n\n"
            f"stdout:\n{completed_process.stdout}\n\n"
            f"stderr:\n{completed_process.stderr}"
        )

    return {
        "collection_name": collection_name,
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }


def prepare_project_with_simple_index(
    docask_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> dict[str, str]:
    """
    Prepare a project for the simple backend.

    This builds only the DocAsk JSONL corpus.
    """
    result = build_corpus_for_project(
        docask_root=docask_root,
        project_path=project_path,
        project_name=project_name,
    )

    result["indexing_mode"] = "simple"
    result["backend"] = "simple"

    return result


def prepare_project_with_mmore_index(
    docask_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
    collection_name: str = "mmore_docs",
) -> dict[str, str]:
    """
    Prepare a project for the MMORE backend.

    This builds the DocAsk corpus, exports it to MMORE format, and builds the
    MMORE index.
    """
    corpus_result = build_corpus_for_project(
        docask_root=docask_root,
        project_path=project_path,
        project_name=project_name,
    )

    project_dir = Path(corpus_result["project_dir"])
    corpus_path = Path(corpus_result["corpus_path"])
    mmore_corpus_path = project_dir / "mmore_corpus.jsonl"

    export_result = export_mmore_corpus_for_project(
        docask_root=docask_root,
        corpus_path=corpus_path,
        output_path=mmore_corpus_path,
    )

    index_result = build_mmore_index_for_project(
        docask_root=docask_root,
        documents_path=mmore_corpus_path,
        collection_name=collection_name,
    )

    return {
        "project_name": corpus_result["project_name"],
        "project_dir": corpus_result["project_dir"],
        "project_config_path": corpus_result["project_config_path"],
        "corpus_path": corpus_result["corpus_path"],
        "mmore_corpus_path": export_result["mmore_corpus_path"],
        "collection_name": index_result["collection_name"],
        "indexing_mode": "mmore",
        "backend": "mmore",
        "build_corpus_stdout": corpus_result.get("stdout", ""),
        "build_corpus_stderr": corpus_result.get("stderr", ""),
        "export_mmore_stdout": export_result.get("stdout", ""),
        "export_mmore_stderr": export_result.get("stderr", ""),
        "build_index_stdout": index_result.get("stdout", ""),
        "build_index_stderr": index_result.get("stderr", ""),
    }