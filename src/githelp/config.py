"""
Configuration loading utilities for GitHelp.

This module loads the YAML configuration files used by the project.
GitHelp currently uses separate configuration files for project settings,
indexing settings, and application settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

import yaml


class GitHelpConfigs(TypedDict):
    """Configuration sections loaded from the default config directory."""

    project: dict[str, Any]
    indexing: dict[str, Any]
    app: dict[str, Any]


@dataclass(frozen=True)
class LLMConfig:
    """Typed application LLM configuration."""

    provider: str = "dummy"
    model_name: str = "Qwen/Qwen3-8B"
    max_new_tokens: int = 512
    temperature: float = 0.0
    enable_thinking: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> LLMConfig:
        data = data or {}

        return cls(
            provider=str(data.get("provider", cls.provider)),
            model_name=str(data.get("model_name", cls.model_name)),
            max_new_tokens=int(data.get("max_new_tokens", cls.max_new_tokens)),
            temperature=float(data.get("temperature", cls.temperature)),
            enable_thinking=bool(data.get("enable_thinking", cls.enable_thinking)),
        )


@dataclass(frozen=True)
class AppConfig:
    """Typed application configuration."""

    app_title: str = "GitHelp"
    app_subtitle: str = "Ask questions about a project's documentation"
    show_sources: bool = True
    default_top_k: int = 5
    project_profile: str = "generic"
    project_config_path: str | None = None
    llm: LLMConfig = field(default_factory=LLMConfig)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> AppConfig:
        project = data.get("project")
        project_config_path = None

        if isinstance(project, dict):
            path = project.get("config_path") or project.get("project_config_path")
            if path:
                project_config_path = str(path)

        return cls(
            app_title=str(data.get("app_title", cls.app_title)),
            app_subtitle=str(data.get("app_subtitle", cls.app_subtitle)),
            show_sources=bool(data.get("show_sources", cls.show_sources)),
            default_top_k=int(data.get("default_top_k", cls.default_top_k)),
            project_profile=str(data.get("project_profile", cls.project_profile)),
            project_config_path=project_config_path,
            llm=LLMConfig.from_mapping(data.get("llm")),
        )


@dataclass(frozen=True)
class ProjectConfig:
    """Typed target project configuration."""

    project_name: str = "project"
    package_name: str | None = None
    repo_path: str | None = None
    docs_path: str = "."
    code_path: str | None = None
    include_yaml_configs: bool = False
    yaml_config_paths: list[str] = field(default_factory=list)
    include_repo_structure: bool = False
    repo_structure_max_depth: int = 4
    include_extensions: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ProjectConfig:
        return cls(
            project_name=str(data.get("project_name", cls.project_name)),
            package_name=(
                str(data["package_name"]) if data.get("package_name") else None
            ),
            repo_path=str(data["repo_path"]) if data.get("repo_path") else None,
            docs_path=str(data["docs_path"]),
            code_path=str(data["code_path"]) if data.get("code_path") else None,
            include_yaml_configs=bool(
                data.get("include_yaml_configs", cls.include_yaml_configs)
            ),
            yaml_config_paths=[str(path) for path in data.get("yaml_config_paths", [])],
            include_repo_structure=bool(
                data.get("include_repo_structure", cls.include_repo_structure)
            ),
            repo_structure_max_depth=int(
                data.get("repo_structure_max_depth", cls.repo_structure_max_depth)
            ),
            include_extensions=[
                str(extension) for extension in data.get("include_extensions", [])
            ],
            exclude_patterns=[
                str(pattern) for pattern in data.get("exclude_patterns", [])
            ],
        )


@dataclass(frozen=True)
class IndexingConfig:
    """Typed indexing configuration."""

    top_k: int = 5
    retrieval_backend: str = "simple"
    collection_name: str = "githelp_docs"
    mmore_index_config_path: str = "configs/mmore_index_config.yaml"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> IndexingConfig:
        return cls(
            top_k=int(data.get("top_k", cls.top_k)),
            retrieval_backend=str(data.get("retrieval_backend", cls.retrieval_backend)),
            collection_name=str(data.get("collection_name", cls.collection_name)),
            mmore_index_config_path=str(
                data.get("mmore_index_config_path", cls.mmore_index_config_path)
            ),
        )


def load_yaml(path: str | Path) -> dict[str, Any]:
    """
    Load a YAML file and validate that it contains a dictionary.

    Parameters
    ----------
    path:
        Path to the YAML file.

    Returns
    -------
    dict[str, Any]
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the YAML file does not exist.
    ValueError
        If the YAML file does not contain a dictionary at the top level.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a dictionary: {path}")

    return data


def load_all_configs(config_dir: str | Path = "configs") -> GitHelpConfigs:
    """
    Load all configuration files used by GitHelp.

    Parameters
    ----------
    config_dir:
        Directory containing the YAML configuration files.

    Returns
    -------
    GitHelpConfigs
        Dictionary containing project, indexing, and app configuration.
    """
    config_dir = Path(config_dir)

    return {
        "project": load_yaml(config_dir / "project_config.yaml"),
        "indexing": load_yaml(config_dir / "indexing_config.yaml"),
        "app": load_yaml(config_dir / "app_config.yaml"),
    }


def load_app_config(path: str | Path = "configs/app_config.yaml") -> AppConfig:
    """Load the typed application configuration."""
    return AppConfig.from_mapping(load_yaml(path))


def load_project_config(
    path: str | Path = "configs/project_config.yaml",
) -> ProjectConfig:
    """Load the typed target project configuration."""
    return ProjectConfig.from_mapping(load_yaml(path))


def load_indexing_config(
    path: str | Path = "configs/indexing_config.yaml",
) -> IndexingConfig:
    """Load the typed indexing configuration."""
    return IndexingConfig.from_mapping(load_yaml(path))
