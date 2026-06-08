from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import streamlit as st

from githelp.config import load_yaml
from githelp.rag.llm_factory import create_llm_provider
from streamlit_state import clear_results


@st.cache_data(show_spinner=False)
def load_app_config(config_path: str) -> dict[str, Any]:
    """Load the application config."""
    return load_yaml(config_path)


@st.cache_resource(show_spinner="Loading LLM model...")
def get_llm_provider(config_path: str):
    """Create and cache the LLM provider."""
    config = load_yaml(config_path)
    return create_llm_provider(config)


def render_sidebar(
    default_config_path: Path,
    persist_current_state: Callable[[], None],
) -> dict[str, Any]:
    """Render sidebar settings and return current options."""
    with st.sidebar:
        st.header("Settings")

        config_path = st.text_input(
            "App config path",
            value=str(default_config_path),
        )

        backend_options = ["mmore", "simple"]
        current_backend = st.session_state.get("backend", "mmore")

        if current_backend not in backend_options:
            current_backend = "mmore"

        backend = st.selectbox(
            "Retrieval backend",
            options=backend_options,
            index=backend_options.index(current_backend),
            key="backend",
        )

        top_k = st.slider(
            "Number of sources",
            min_value=1,
            max_value=10,
            value=int(st.session_state.get("top_k", 5)),
            key="top_k",
        )

        use_llm = st.toggle(
            "Use LLM",
            value=bool(st.session_state.get("use_llm", True)),
            key="use_llm",
        )

        show_sources = st.toggle(
            "Show retrieved sources",
            value=bool(st.session_state.get("show_sources", True)),
            key="show_sources",
        )

        show_full_sources = st.toggle(
            "Show full source content",
            value=bool(st.session_state.get("show_full_sources", False)),
            disabled=not show_sources,
            key="show_full_sources",
        )

        show_debug = st.toggle(
            "Show debug information",
            value=bool(st.session_state.get("show_debug", False)),
            key="show_debug",
        )

        st.divider()

        col_reload, col_clear = st.columns(2)

        with col_reload:
            if st.button("Reload config"):
                load_app_config.clear()
                get_llm_provider.clear()
                st.success("Config and LLM cache cleared.")

        with col_clear:
            if st.button("Clear results"):
                clear_results()
                st.success("Cleared.")

        config = None

        try:
            config = load_app_config(config_path)

            st.markdown("### Current config")

            project_profile = config.get("project_profile", "generic")
            st.markdown(f"**Project profile:** `{project_profile}`")

            llm_config = config.get("llm", {})
            provider = llm_config.get("provider", "unknown")
            model_name = llm_config.get("model_name", "unknown")

            st.markdown(f"**LLM provider:** `{provider}`")
            st.markdown(f"**Model:** `{model_name}`")

            with st.expander("Show raw config"):
                st.json(config)

        except Exception as error:
            st.warning(f"Could not load config: {error}")

    persist_current_state()

    return {
        "config_path": config_path,
        "backend": backend,
        "top_k": top_k,
        "use_llm": use_llm,
        "show_sources": show_sources,
        "show_full_sources": show_full_sources,
        "show_debug": show_debug,
        "config": config,
    }
