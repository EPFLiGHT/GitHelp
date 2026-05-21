from __future__ import annotations

from pathlib import Path

from docask.projects.project_state import (
    DEFAULT_APP_STATE,
    load_app_state,
    save_app_state,
)


def test_load_app_state_returns_defaults_when_file_missing(tmp_path: Path):
    state_path = tmp_path / "app_state.json"

    state = load_app_state(state_path)

    assert state["backend"] == DEFAULT_APP_STATE["backend"]
    assert state["top_k"] == DEFAULT_APP_STATE["top_k"]
    assert state["use_llm"] == DEFAULT_APP_STATE["use_llm"]


def test_save_and_load_app_state(tmp_path: Path):
    state_path = tmp_path / "app_state.json"

    expected_state = {
        "project_name": "mmore",
        "project_path": "/tmp/mmore",
        "corpus_path": "/tmp/docask/data/projects/mmore/corpus.jsonl",
        "project_config_path": "/tmp/docask/data/projects/mmore/project_config.yaml",
        "backend": "simple",
        "top_k": 3,
        "use_llm": False,
        "show_sources": True,
        "show_full_sources": False,
        "show_debug": True,
    }

    save_app_state(state_path, expected_state)

    loaded_state = load_app_state(state_path)

    assert loaded_state["project_name"] == "mmore"
    assert loaded_state["project_path"] == "/tmp/mmore"
    assert loaded_state["backend"] == "simple"
    assert loaded_state["top_k"] == 3
    assert loaded_state["use_llm"] is False
    assert loaded_state["show_debug"] is True


def test_load_app_state_merges_missing_fields_with_defaults(tmp_path: Path):
    state_path = tmp_path / "app_state.json"

    save_app_state(
        state_path,
        {
            "project_name": "custom-project",
        },
    )

    loaded_state = load_app_state(state_path)

    assert loaded_state["project_name"] == "custom-project"
    assert loaded_state["backend"] == DEFAULT_APP_STATE["backend"]
    assert loaded_state["top_k"] == DEFAULT_APP_STATE["top_k"]