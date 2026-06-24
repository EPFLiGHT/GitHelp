from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Literal, TypedDict

import yaml

from githelp.projects.project_commands import (
    ProjectCommandError as ProjectCommandError,
    run_project_command,
)


class GeneratedProjectConfig(TypedDict):
    """Configuration generated for one target project."""

    project_name: str
    package_name: str
    repo_path: str
    docs_path: str
    code_path: str
    include_yaml_configs: bool
    yaml_config_paths: list[str]
    include_repo_structure: bool
    repo_structure_max_depth: int
    include_extensions: list[str]
    exclude_patterns: list[str]


class PreparedProjectPaths(TypedDict):
    """Generated project paths before running indexing commands."""

    project_name: str
    project_dir: Path
    project_config_path: Path
    corpus_path: Path
    config: GeneratedProjectConfig


class CorpusBuildResult(TypedDict):
    """Result returned after building a GitHelp JSONL corpus."""

    project_name: str
    project_dir: str
    project_config_path: str
    corpus_path: str
    stdout: str
    stderr: str


class SimpleIndexProjectResult(CorpusBuildResult):
    """Project preparation result for the simple retrieval backend."""

    indexing_mode: Literal["simple"]
    backend: Literal["simple"]


class MmoreCorpusExportResult(TypedDict):
    """Result returned after exporting a corpus to MMORE JSONL format."""

    mmore_corpus_path: str
    stdout: str
    stderr: str


class MmoreIndexBuildResult(TypedDict):
    """Result returned after building a MMORE index."""

    collection_name: str
    stdout: str
    stderr: str


class MmoreIndexProjectResult(TypedDict):
    """Project preparation result for the MMORE retrieval backend."""

    project_name: str
    project_dir: str
    project_config_path: str
    corpus_path: str
    mmore_corpus_path: str
    collection_name: str
    indexing_mode: Literal["mmore"]
    backend: Literal["mmore"]
    build_corpus_stdout: str
    build_corpus_stderr: str
    export_mmore_stdout: str
    export_mmore_stderr: str
    build_index_stdout: str
    build_index_stderr: str


def _run_script(
    *,
    githelp_root: Path,
    script_name: str,
    arguments: list[str],
    error_label: str,
) -> subprocess.CompletedProcess[str]:
    """Run one GitHelp script with consistent command and error handling."""
    command = [
        sys.executable,
        str(githelp_root / "scripts" / script_name),
        *arguments,
    ]

    return run_project_command(
        label=error_label,
        command=command,
        cwd=githelp_root,
    )


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
) -> GeneratedProjectConfig:
    """
    Build a GitHelp project configuration dictionary for a local project.
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
    config: GeneratedProjectConfig,
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
    githelp_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> PreparedProjectPaths:
    """
    Prepare output paths for a GitHelp project.
    """
    githelp_root = Path(githelp_root).resolve()

    config = build_project_config(
        project_path=project_path,
        project_name=project_name,
    )

    final_project_name = config["project_name"]
    project_dir = githelp_root / "data" / "projects" / final_project_name

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
    githelp_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> CorpusBuildResult:
    """
    Generate a project config and run the GitHelp corpus builder.

    This function expects scripts/build_corpus.py to support:
    --config <project_config_path>
    --output-path <corpus_path>
    """
    githelp_root = Path(githelp_root).resolve()

    prepared = prepare_project_paths(
        githelp_root=githelp_root,
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

    completed_process = _run_script(
        githelp_root=githelp_root,
        script_name="build_corpus.py",
        error_label="Corpus build failed",
        arguments=[
            "--config",
            str(project_config_path),
            "--output-path",
            str(corpus_path),
        ],
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
    githelp_root: str | Path,
    corpus_path: str | Path,
    output_path: str | Path,
) -> MmoreCorpusExportResult:
    """
    Export a project-specific GitHelp corpus to MMORE-compatible JSONL format.
    """
    githelp_root = Path(githelp_root).resolve()
    corpus_path = Path(corpus_path).resolve()
    output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    completed_process = _run_script(
        githelp_root=githelp_root,
        script_name="export_mmore_corpus.py",
        error_label="MMORE corpus export failed",
        arguments=[
            "--corpus-path",
            str(corpus_path),
            "--output-path",
            str(output_path),
        ],
    )

    return {
        "mmore_corpus_path": str(output_path),
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }


def build_mmore_index_for_project(
    githelp_root: str | Path,
    documents_path: str | Path,
    collection_name: str = "mmore_docs",
) -> MmoreIndexBuildResult:
    """
    Build the MMORE index for a project-specific MMORE corpus.
    """
    githelp_root = Path(githelp_root).resolve()
    documents_path = Path(documents_path).resolve()

    completed_process = _run_script(
        githelp_root=githelp_root,
        script_name="build_index.py",
        error_label="MMORE index build failed",
        arguments=[
            "--documents-path",
            str(documents_path),
            "--collection-name",
            collection_name,
        ],
    )

    return {
        "collection_name": collection_name,
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }


def prepare_project_with_simple_index(
    githelp_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
) -> SimpleIndexProjectResult:
    """
    Prepare a project for the simple backend.

    This builds only the GitHelp JSONL corpus.
    """
    corpus_result = build_corpus_for_project(
        githelp_root=githelp_root,
        project_path=project_path,
        project_name=project_name,
    )

    return {
        **corpus_result,
        "indexing_mode": "simple",
        "backend": "simple",
    }


def prepare_project_with_mmore_index(
    githelp_root: str | Path,
    project_path: str | Path,
    project_name: str | None = None,
    collection_name: str = "mmore_docs",
) -> MmoreIndexProjectResult:
    """
    Prepare a project for the MMORE backend.

    This builds the GitHelp corpus, exports it to MMORE format, and builds the
    MMORE index.
    """
    corpus_result = build_corpus_for_project(
        githelp_root=githelp_root,
        project_path=project_path,
        project_name=project_name,
    )

    project_dir = Path(corpus_result["project_dir"])
    corpus_path = Path(corpus_result["corpus_path"])
    mmore_corpus_path = project_dir / "mmore_corpus.jsonl"

    export_result = export_mmore_corpus_for_project(
        githelp_root=githelp_root,
        corpus_path=corpus_path,
        output_path=mmore_corpus_path,
    )

    index_result = build_mmore_index_for_project(
        githelp_root=githelp_root,
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
