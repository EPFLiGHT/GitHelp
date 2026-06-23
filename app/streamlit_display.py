from __future__ import annotations

from typing import Any

import streamlit as st

from githelp.retrieval.mmore_result_mapping import (
    MMORE_RETRIEVAL_MODE_METADATA_KEY,
)


def get_retrieval_mode(results: list[Any]) -> str | None:
    """Return the retrieval mode attached to the first result, if available."""
    for result in results:
        metadata = getattr(result.document, "metadata", {})
        mode = metadata.get(MMORE_RETRIEVAL_MODE_METADATA_KEY)
        if mode:
            return str(mode)

    return None


def format_backend_label(backend: str, retrieval_mode: str | None) -> str:
    """Format the backend label shown in Streamlit."""
    if backend != "mmore" or not retrieval_mode:
        return backend

    return f"{backend} ({retrieval_mode})"


def display_sources(results: list[Any], show_full_sources: bool = False) -> None:
    """Display retrieved sources in expandable sections."""
    if not results:
        st.info("No sources were retrieved.")
        return

    st.subheader("Retrieved sources")

    for index, result in enumerate(results, start=1):
        doc = result.document

        source_type = doc.source_type or "unknown"
        relative_path = (
            doc.metadata.get("relative_path")
            or doc.file_path
            or "unknown"
        )
        title = doc.title or doc.section_title or doc.symbol_name or "unknown"
        content = (doc.content or "").strip()
        retrieval_mode = doc.metadata.get(MMORE_RETRIEVAL_MODE_METADATA_KEY)

        label = f"Source {index} - {source_type} - {relative_path}"

        with st.expander(label):
            st.markdown(f"**Title:** `{title}`")
            st.markdown(f"**Score:** `{result.score:.4f}`")

            if retrieval_mode:
                st.markdown(f"**Retrieval mode:** `{retrieval_mode}`")

            if doc.section_title:
                st.markdown(f"**Section:** `{doc.section_title}`")

            if doc.module_name:
                st.markdown(f"**Module:** `{doc.module_name}`")

            if doc.symbol_name:
                st.markdown(f"**Symbol:** `{doc.symbol_name}`")

            st.markdown("**Content:**")

            if show_full_sources:
                st.code(content)
                st.caption(f"Showing full source content: {len(content)} characters.")
                continue

            preview = content[:3000]
            st.code(preview)

            if len(content) > 3000:
                st.caption(
                    f"Preview truncated to 3000 characters. "
                    f"Full source length: {len(content)} characters."
                )
            else:
                st.caption(
                    f"Full source is already shorter than 3000 characters "
                    f"({len(content)} characters), so preview and full view are identical."
                )


def display_debug_information(
    question: str,
    corpus_path: str,
    config_path: str,
    backend: str,
    retrieval_mode: str | None,
    top_k: int,
    use_llm: bool,
    config: dict[str, Any] | None,
    retrieval_query: str | None = None,
    is_followup: bool = False,
    followup_ambiguous: bool = False,
) -> None:
    """Display debug information for development."""
    st.subheader("Debug information")

    st.markdown(f"**Original user question:** `{question}`")
    st.markdown(f"**Rewritten retrieval query:** `{retrieval_query or question}`")
    st.markdown(f"**Detected as follow-up:** `{is_followup}`")
    st.markdown(f"**Follow-up ambiguous:** `{followup_ambiguous}`")
    st.markdown(f"**Corpus path:** `{corpus_path}`")
    st.markdown(f"**Config path:** `{config_path}`")
    st.markdown(f"**Backend:** `{backend}`")
    st.markdown(f"**Retrieval mode:** `{retrieval_mode or 'unknown'}`")
    st.markdown(f"**Top K:** `{top_k}`")
    st.markdown(f"**Use LLM:** `{use_llm}`")
    if config is not None:
        st.markdown("**Loaded app config:**")
        st.json(config)
