from __future__ import annotations

from pathlib import Path

import streamlit as st

from githelp.projects.project_state import load_app_state, save_app_state


def initialize_session_state(app_state_path: str | Path) -> None:
    """Initialize Streamlit session state values."""
    app_state = load_app_state(app_state_path)

    defaults = {
        "question": "",
        "last_answer": None,
        "last_results": [],
        "last_metadata": {},
        "project_name": app_state.get("project_name", ""),
        "project_path": app_state.get("project_path", ""),
        "corpus_path": app_state.get("corpus_path", ""),
        "project_config_path": app_state.get("project_config_path", ""),
        "mmore_corpus_path": app_state.get("mmore_corpus_path", ""),
        "collection_name": app_state.get("collection_name", ""),
        "indexing_mode": app_state.get("indexing_mode", "mmore"),
        "backend": app_state.get("backend", "mmore"),
        "top_k": app_state.get("top_k", 5),
        "use_llm": app_state.get("use_llm", True),
        "show_sources": app_state.get("show_sources", True),
        "show_full_sources": app_state.get("show_full_sources", False),
        "show_debug": app_state.get("show_debug", False),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_pending_state_updates() -> None:
    """
    Apply state updates that must happen before widgets are instantiated.

    Streamlit does not allow modifying a session_state key after a widget
    using the same key has already been created in the current run.
    """
    pending_backend = st.session_state.pop("pending_backend", None)

    if pending_backend is not None:
        st.session_state["backend"] = pending_backend


def persist_current_state(app_state_path: str | Path) -> None:
    """Persist the current app settings to disk."""
    state = {
        "project_name": st.session_state.get("project_name", ""),
        "project_path": st.session_state.get("project_path", ""),
        "corpus_path": st.session_state.get("corpus_path", ""),
        "project_config_path": st.session_state.get("project_config_path", ""),
        "mmore_corpus_path": st.session_state.get("mmore_corpus_path", ""),
        "collection_name": st.session_state.get("collection_name", ""),
        "indexing_mode": st.session_state.get("indexing_mode", "mmore"),
        "backend": st.session_state.get("backend", "mmore"),
        "top_k": st.session_state.get("top_k", 5),
        "use_llm": st.session_state.get("use_llm", True),
        "show_sources": st.session_state.get("show_sources", True),
        "show_full_sources": st.session_state.get("show_full_sources", False),
        "show_debug": st.session_state.get("show_debug", False),
    }

    save_app_state(app_state_path, state)


def clear_question() -> None:
    """Clear the current question input."""
    st.session_state["question"] = ""


def clear_results() -> None:
    """Clear the last displayed answer and sources."""
    st.session_state["last_answer"] = None
    st.session_state["last_results"] = []
    st.session_state["last_metadata"] = {}
