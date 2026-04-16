from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a dictionary: {path}")

    return data


def load_all_configs(config_dir: str | Path = "configs") -> dict[str, dict[str, Any]]:
    config_dir = Path(config_dir)

    return {
        "project": load_yaml(config_dir / "project_config.yaml"),
        "indexing": load_yaml(config_dir / "indexing_config.yaml"),
        "app": load_yaml(config_dir / "app_config.yaml"),
    }