from __future__ import annotations

from pathlib import Path

from docask.data_models import DocumentRecord


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
    "htmlcov",
    ".ipynb_checkpoints",
    ".tox",
    ".cache",
}


DEFAULT_INCLUDED_SUFFIXES = {
    ".py",
    ".md",
    ".rst",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".txt",
}


def _should_skip(path: Path, repo_root: Path) -> bool:
    try:
        relative_parts = path.relative_to(repo_root).parts
    except ValueError:
        return True

    return any(part in DEFAULT_EXCLUDED_DIRS for part in relative_parts)


def _is_visible_file(path: Path) -> bool:
    return path.suffix.lower() in DEFAULT_INCLUDED_SUFFIXES


def build_repo_tree(
    repo_path: str | Path,
    *,
    max_depth: int = 4,
    max_entries_per_dir: int = 80,
) -> str:
    repo_root = Path(repo_path)

    if not repo_root.exists():
        return ""

    lines: list[str] = [f"{repo_root.name}/"]

    def visit(directory: Path, prefix: str = "", depth: int = 0) -> None:
        if depth >= max_depth:
            return

        children = [
            child
            for child in directory.iterdir()
            if not _should_skip(child, repo_root)
        ]

        visible_children = [
            child
            for child in children
            if child.is_dir() or (child.is_file() and _is_visible_file(child))
        ]

        visible_children = sorted(
            visible_children,
            key=lambda p: (p.is_file(), p.name.lower()),
        )

        if len(visible_children) > max_entries_per_dir:
            visible_children = visible_children[:max_entries_per_dir]
            truncated = True
        else:
            truncated = False

        for index, child in enumerate(visible_children):
            is_last = index == len(visible_children) - 1 and not truncated
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if child.is_dir():
                lines.append(f"{prefix}{connector}{child.name}/")
                visit(child, next_prefix, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{child.name}")

        if truncated:
            lines.append(f"{prefix}└── ...")

    visit(repo_root)

    return "\n".join(lines)


def load_repo_structure_document(
    repo_path: str | Path,
    *,
    project_name: str = "project",
    max_depth: int = 4,
) -> list[DocumentRecord]:
    repo_path = Path(repo_path)

    if not repo_path.exists():
        return []

    tree = build_repo_tree(repo_path, max_depth=max_depth)

    if not tree.strip():
        return []

    content = "\n".join(
        [
            f"Repository structure for project: {project_name}",
            "",
            "This document summarizes the repository layout. It is useful for answering navigation questions such as where modules, examples, configs, tests, or documentation files are located.",
            "",
            "Repository tree:",
            "```text",
            tree,
            "```",
        ]
    )

    return [
        DocumentRecord(
            doc_id=f"repo_structure::{project_name}",
            content=content,
            source_type="repo_structure",
            title=f"{project_name} repository structure",
            file_path=str(repo_path),
            section_title=None,
            language="text",
            metadata={
                "relative_path": ".",
                "project_name": project_name,
                "max_depth": max_depth,
            },
        )
    ]