from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_APP_STATE = {
    "project_name": "",
    "project_path": "",
    "corpus_path": "",
    "project_config_path": "",
    "mmore_corpus_path": "",
    "collection_name": "",
    "indexing_mode": "mmore",
    "backend": "mmore",
    "top_k": 5,
    "use_llm": True,
    "show_sources": True,
    "show_full_sources": False,
    "show_debug": False,
}


def load_app_state(state_path: str | Path) -> dict[str, Any]:
    """
    Load persisted Streamlit app state.

    This is used to restore the last selected project, corpus path, backend,
    and display settings after closing and reopening the interface.
    """
    state_path = Path(state_path)

    if not state_path.exists():
        return DEFAULT_APP_STATE.copy()

    try:
        with state_path.open("r", encoding="utf-8") as file:
            loaded_state = json.load(file)

    except json.JSONDecodeError:
        return DEFAULT_APP_STATE.copy()

    state = DEFAULT_APP_STATE.copy()
    state.update(loaded_state)

    return state


def save_app_state(
    state_path: str | Path,
    state: dict[str, Any],
) -> None:
    """
    Save Streamlit app state to disk.
    """
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with state_path.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)