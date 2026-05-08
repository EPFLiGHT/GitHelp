"""
Configuration loading utilities for DocAsk.

This module loads the YAML configuration files used by the project.
DocAsk currently uses separate configuration files for project settings,
indexing settings, and application settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


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


def load_all_configs(config_dir: str | Path = "configs") -> dict[str, dict[str, Any]]:
    """
    Load all configuration files used by DocAsk.

    Parameters
    ----------
    config_dir:
        Directory containing the YAML configuration files.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary containing project, indexing, and app configuration.
    """
    config_dir = Path(config_dir)

    return {
        "project": load_yaml(config_dir / "project_config.yaml"),
        "indexing": load_yaml(config_dir / "indexing_config.yaml"),
        "app": load_yaml(config_dir / "app_config.yaml"),
    }