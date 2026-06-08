from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

from githelp.projects.project_builder import (
    prepare_project_with_mmore_index,
    prepare_project_with_simple_index,
)


def _build_mmore_index(
    project_root: Path,
    project_path: str,
    project_name: str,
    persist_current_state: Callable[[], None],
) -> None:
    """Build the GitHelp corpus and MMORE index for the selected project."""
    if not project_path.strip():
        st.warning("Please provide a local project path.")
        return

    with st.status("Building MMORE index...", expanded=True) as status:
        try:
            st.write("Building GitHelp corpus...")
            st.write("Exporting corpus to MMORE format...")
            st.write("Building MMORE index...")

            build_result = prepare_project_with_mmore_index(
                githelp_root=project_root,
                project_path=project_path,
                project_name=project_name or None,
                collection_name="mmore_docs",
            )

            st.session_state["project_name"] = build_result["project_name"]
            st.session_state["project_path"] = str(Path(project_path).resolve())
            st.session_state["project_config_path"] = build_result[
                "project_config_path"
            ]
            st.session_state["corpus_path"] = build_result["corpus_path"]
            st.session_state["mmore_corpus_path"] = build_result[
                "mmore_corpus_path"
            ]
            st.session_state["collection_name"] = build_result["collection_name"]
            st.session_state["indexing_mode"] = "mmore"
            st.session_state["pending_backend"] = "mmore"

            persist_current_state()

            status.update(
                label="MMORE index built successfully.",
                state="complete",
                expanded=False,
            )

            st.success(
                f"Project `{build_result['project_name']}` is ready with backend `mmore`."
            )

            with st.expander("Build output"):
                st.markdown("#### Corpus build")
                st.code(build_result.get("build_corpus_stdout", ""))

                if build_result.get("build_corpus_stderr"):
                    st.code(build_result["build_corpus_stderr"])

                st.markdown("#### MMORE export")
                st.code(build_result.get("export_mmore_stdout", ""))

                if build_result.get("export_mmore_stderr"):
                    st.code(build_result["export_mmore_stderr"])

                st.markdown("#### MMORE index")
                st.code(build_result.get("build_index_stdout", ""))

                if build_result.get("build_index_stderr"):
                    st.code(build_result["build_index_stderr"])

            st.rerun()

        except Exception as error:
            status.update(
                label="MMORE index build failed.",
                state="error",
                expanded=True,
            )

            error_message = str(error)

            if "langchain_milvus" in error_message:
                st.error(
                    "MMORE indexing failed because `langchain-milvus` is not installed. "
                    "Install it with: `pip install langchain-milvus`."
                )
            else:
                st.error("Could not build the MMORE index.")

            st.exception(error)


def _build_simple_index(
    project_root: Path,
    project_path: str,
    project_name: str,
    persist_current_state: Callable[[], None],
) -> None:
    """Build only the GitHelp corpus for the selected project."""
    if not project_path.strip():
        st.warning("Please provide a local project path.")
        return

    with st.status("Building simple index...", expanded=True) as status:
        try:
            st.write("Building GitHelp corpus...")

            build_result = prepare_project_with_simple_index(
                githelp_root=project_root,
                project_path=project_path,
                project_name=project_name or None,
            )

            st.session_state["project_name"] = build_result["project_name"]
            st.session_state["project_path"] = str(Path(project_path).resolve())
            st.session_state["project_config_path"] = build_result[
                "project_config_path"
            ]
            st.session_state["corpus_path"] = build_result["corpus_path"]
            st.session_state["mmore_corpus_path"] = ""
            st.session_state["collection_name"] = ""
            st.session_state["indexing_mode"] = "simple"
            st.session_state["pending_backend"] = "simple"

            persist_current_state()

            status.update(
                label="Simple index built successfully.",
                state="complete",
                expanded=False,
            )

            st.success(
                f"Project `{build_result['project_name']}` is ready with backend `simple`."
            )

            with st.expander("Build output"):
                st.code(build_result.get("stdout", ""))

                if build_result.get("stderr"):
                    st.code(build_result["stderr"])

            st.rerun()

        except Exception as error:
            status.update(
                label="Simple index build failed.",
                state="error",
                expanded=True,
            )

            st.error("Could not build the simple index.")
            st.exception(error)


def _render_project_setup_form(
    project_root: Path,
    persist_current_state: Callable[[], None],
    default_project_path: str = "",
    default_project_name: str = "",
) -> None:
    """Render the project setup form and indexing buttons."""
    st.header("Project setup")

    project_source = st.radio(
        "How should GitHelp access the project?",
        options=[
            "Local project path",
            "Public GitHub repository URL",
        ],
        index=0,
        horizontal=True,
    )

    if project_source == "Public GitHub repository URL":
        st.info(
            "GitHub repository support is planned. GitHelp will clone or download "
            "the repository locally, then run the same indexing pipeline. For now, "
            "use a local project path."
        )

        st.text_input(
            "GitHub repository URL",
            placeholder="https://github.com/swiss-ai/mmore",
            disabled=True,
        )

        return

    project_path = st.text_input(
        "Local project path",
        value=default_project_path,
        placeholder="/path/to/software/project",
    )

    project_name = st.text_input(
        "Project name",
        value=default_project_name,
        placeholder="Leave empty to infer from folder name",
    )

    save_button = st.button("Save project settings")

    if save_button:
        st.session_state["project_path"] = project_path
        st.session_state["project_name"] = project_name
        persist_current_state()
        st.success("Project settings saved.")

    st.markdown("### Build index")

    col_mmore, col_simple = st.columns(2)

    with col_mmore:
        st.markdown("**MMORE index**")
        st.caption(
            "Recommended mode. Builds the GitHelp corpus, exports it to MMORE "
            "format, and builds the MMORE retrieval index."
        )

    with col_simple:
        st.markdown("**Simple index**")
        st.caption(
            "Fast debug mode. Builds only the GitHelp JSONL corpus and uses "
            "the local simple retriever."
        )

    col_mmore_button, col_simple_button = st.columns(2)

    with col_mmore_button:
        build_mmore_button = st.button(
            "Build MMORE index",
            type="primary",
            use_container_width=True,
        )

    with col_simple_button:
        build_simple_button = st.button(
            "Build simple index",
            use_container_width=True,
        )

    if build_mmore_button:
        _build_mmore_index(
            project_root,
            project_path,
            project_name,
            persist_current_state,
        )

    if build_simple_button:
        _build_simple_index(
            project_root,
            project_path,
            project_name,
            persist_current_state,
        )


def render_project_setup(
    project_root: Path,
    persist_current_state: Callable[[], None],
) -> None:
    """Render project setup only when needed, then keep it compact."""
    current_corpus_path = st.session_state.get("corpus_path", "")
    corpus_exists = bool(current_corpus_path and Path(current_corpus_path).exists())

    project_name = st.session_state.get("project_name", "")
    project_path = st.session_state.get("project_path", "")
    indexing_mode = st.session_state.get("indexing_mode", "mmore")
    backend = st.session_state.get("backend", "mmore")

    if corpus_exists:
        st.success(
            f"Project `{project_name or 'unknown'}` is ready "
            f"with `{indexing_mode}` indexing and `{backend}` retrieval."
        )

        with st.expander("Project settings / rebuild index", expanded=False):
            _render_project_setup_form(
                project_root=project_root,
                persist_current_state=persist_current_state,
                default_project_path=project_path,
                default_project_name=project_name,
            )

            st.markdown("### Current project")

            st.markdown(f"**Project:** `{project_name}`")
            st.markdown(f"**Project path:** `{project_path}`")
            st.markdown(f"**Indexing mode:** `{indexing_mode}`")
            st.markdown(f"**Retrieval backend:** `{backend}`")
            st.markdown(f"**Corpus path:** `{current_corpus_path}`")

            mmore_corpus_path = st.session_state.get("mmore_corpus_path", "")
            collection_name = st.session_state.get("collection_name", "")

            if mmore_corpus_path:
                st.markdown(f"**MMORE corpus path:** `{mmore_corpus_path}`")

            if collection_name:
                st.markdown(f"**MMORE collection:** `{collection_name}`")

        return

    st.warning("No project corpus found. Configure a project and build an index first.")

    _render_project_setup_form(
        project_root=project_root,
        persist_current_state=persist_current_state,
        default_project_path=project_path,
        default_project_name=project_name,
    )
