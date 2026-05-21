from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from docask.config import load_yaml
from docask.projects.project_builder import build_corpus_for_project
from docask.projects.project_state import load_app_state, save_app_state
from docask.rag.answering import (
    answer_question,
    answer_question_with_provider,
)
from docask.rag.llm_factory import create_llm_provider


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "app_config.yaml"
DEFAULT_APP_STATE_PATH = PROJECT_ROOT / "data" / "app_state.json"


st.set_page_config(
    page_title="DocAsk",
    page_icon="📚",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_app_config(config_path: str) -> dict:
    """Load the application config."""
    return load_yaml(config_path)


@st.cache_resource(show_spinner="Loading LLM model...")
def get_llm_provider(config_path: str):
    """Create and cache the LLM provider."""
    config = load_yaml(config_path)
    return create_llm_provider(config)


def initialize_session_state() -> None:
    """Initialize Streamlit session state values."""
    app_state = load_app_state(DEFAULT_APP_STATE_PATH)

    defaults = {
        "question": "",
        "last_answer": None,
        "last_results": [],
        "last_metadata": {},
        "project_name": app_state.get("project_name", ""),
        "project_path": app_state.get("project_path", ""),
        "corpus_path": app_state.get("corpus_path", ""),
        "project_config_path": app_state.get("project_config_path", ""),
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


def persist_current_state() -> None:
    """Persist the current app settings to disk."""
    state = {
        "project_name": st.session_state.get("project_name", ""),
        "project_path": st.session_state.get("project_path", ""),
        "corpus_path": st.session_state.get("corpus_path", ""),
        "project_config_path": st.session_state.get("project_config_path", ""),
        "backend": st.session_state.get("backend", "mmore"),
        "top_k": st.session_state.get("top_k", 5),
        "use_llm": st.session_state.get("use_llm", True),
        "show_sources": st.session_state.get("show_sources", True),
        "show_full_sources": st.session_state.get("show_full_sources", False),
        "show_debug": st.session_state.get("show_debug", False),
    }

    save_app_state(DEFAULT_APP_STATE_PATH, state)


def clear_question() -> None:
    """Clear the current question input."""
    st.session_state["question"] = ""


def clear_results() -> None:
    """Clear the last displayed answer and sources."""
    st.session_state["last_answer"] = None
    st.session_state["last_results"] = []
    st.session_state["last_metadata"] = {}


def display_sources(results, show_full_sources: bool = False) -> None:
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

        label = f"Source {index} — {source_type} — {relative_path}"

        with st.expander(label):
            st.markdown(f"**Title:** `{title}`")
            st.markdown(f"**Score:** `{result.score:.4f}`")

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
            else:
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
    top_k: int,
    use_llm: bool,
    config: dict | None,
) -> None:
    """Display debug information for development."""
    st.subheader("Debug information")

    st.markdown(f"**Question:** `{question}`")
    st.markdown(f"**Corpus path:** `{corpus_path}`")
    st.markdown(f"**Config path:** `{config_path}`")
    st.markdown(f"**Backend:** `{backend}`")
    st.markdown(f"**Top K:** `{top_k}`")
    st.markdown(f"**Use LLM:** `{use_llm}`")

    if config is not None:
        st.markdown("**Loaded app config:**")
        st.json(config)


def render_project_setup() -> None:
    """Render project selection and corpus build controls."""
    st.header("Project setup")

    project_source = st.radio(
        "How should DocAsk access the project?",
        options=[
            "Local project path",
            "Public GitHub repository URL",
        ],
        index=0,
        horizontal=True,
    )

    if project_source == "Public GitHub repository URL":
        st.info(
            "GitHub repository support is planned, but this MVP currently supports "
            "local project paths only."
        )

        st.text_input(
            "GitHub repository URL",
            placeholder="https://github.com/swiss-ai/mmore",
            disabled=True,
        )

        return

    project_path = st.text_input(
        "Local project path",
        value=st.session_state.get("project_path", ""),
        placeholder="/path/to/software/project",
    )

    project_name = st.text_input(
        "Project name",
        value=st.session_state.get("project_name", ""),
        placeholder="Leave empty to infer from folder name",
    )

    col_build, col_save = st.columns([1, 1])

    with col_build:
        build_button = st.button("Build corpus", type="primary")

    with col_save:
        save_button = st.button("Save project settings")

    if save_button:
        st.session_state["project_path"] = project_path
        st.session_state["project_name"] = project_name
        persist_current_state()
        st.success("Project settings saved.")

    if build_button:
        if not project_path.strip():
            st.warning("Please provide a local project path.")
            return

        with st.status("Building corpus...", expanded=True) as status:
            try:
                st.write("Preparing project configuration...")

                build_result = build_corpus_for_project(
                    docask_root=PROJECT_ROOT,
                    project_path=project_path,
                    project_name=project_name or None,
                )

                st.write("Corpus build completed.")

                st.session_state["project_name"] = build_result["project_name"]
                st.session_state["project_path"] = str(Path(project_path).resolve())
                st.session_state["project_config_path"] = build_result[
                    "project_config_path"
                ]
                st.session_state["corpus_path"] = build_result["corpus_path"]

                persist_current_state()

                status.update(
                    label="Corpus built successfully.",
                    state="complete",
                    expanded=False,
                )

                st.success(
                    f"Corpus created for project `{build_result['project_name']}`."
                )

                with st.expander("Build output"):
                    st.code(build_result.get("stdout", ""))

                    if build_result.get("stderr"):
                        st.code(build_result["stderr"])

            except Exception as error:
                status.update(
                    label="Corpus build failed.",
                    state="error",
                    expanded=True,
                )

                st.error("Could not build the corpus.")
                st.exception(error)

    current_corpus_path = st.session_state.get("corpus_path", "")

    if current_corpus_path:
        st.markdown("### Current project")
        st.markdown(f"**Project:** `{st.session_state.get('project_name', '')}`")
        st.markdown(f"**Project path:** `{st.session_state.get('project_path', '')}`")
        st.markdown(f"**Corpus path:** `{current_corpus_path}`")

        if Path(current_corpus_path).exists():
            st.success("Corpus file found.")
        else:
            st.warning("Corpus path is saved, but the file does not exist.")


def render_sidebar() -> dict:
    """Render sidebar settings and return current options."""
    with st.sidebar:
        st.header("Settings")

        config_path = st.text_input(
            "App config path",
            value=str(DEFAULT_CONFIG_PATH),
        )

        backend = st.selectbox(
            "Retrieval backend",
            options=["mmore", "simple"],
            index=0 if st.session_state.get("backend", "mmore") == "mmore" else 1,
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


def main() -> None:
    initialize_session_state()

    st.title("DocAsk")
    st.caption(
        "Ask questions about a software project's documentation and code documentation."
    )

    options = render_sidebar()

    render_project_setup()

    st.divider()

    st.header("Ask questions")

    question = st.text_area(
        "Question",
        key="question",
        placeholder="Example: Which Milvus parameters are used in the ColPali config?",
        height=100,
    )

    col_ask, col_clear_question = st.columns([1, 1])

    with col_ask:
        ask_button = st.button("Ask", type="primary")

    with col_clear_question:
        st.button("Clear question", on_click=clear_question)

    if ask_button:
        if not question.strip():
            st.warning("Please enter a question.")
            return

        corpus_path = st.session_state.get("corpus_path", "")

        if not corpus_path:
            st.error("No corpus selected. Build a corpus first in Project setup.")
            return

        corpus = Path(corpus_path)

        if not corpus.exists():
            st.error(f"Corpus file not found: {corpus}")
            return

        with st.spinner("Retrieving sources and generating answer..."):
            try:
                if options["use_llm"]:
                    llm_provider = get_llm_provider(options["config_path"])

                    answer, results = answer_question_with_provider(
                        question=question,
                        llm_provider=llm_provider,
                        corpus_path=corpus,
                        top_k=options["top_k"],
                        backend=options["backend"],
                        config_path=options["config_path"],
                    )
                else:
                    answer, results = answer_question(
                        question=question,
                        corpus_path=corpus,
                        top_k=options["top_k"],
                        backend=options["backend"],
                    )

            except Exception as error:
                st.error("An error occurred while answering the question.")
                st.exception(error)
                return

        st.session_state["last_answer"] = answer
        st.session_state["last_results"] = results
        st.session_state["last_metadata"] = {
            "question": question,
            "backend": options["backend"],
            "top_k": options["top_k"],
            "use_llm": options["use_llm"],
            "corpus_path": corpus_path,
            "config_path": options["config_path"],
        }

        persist_current_state()

    if st.session_state["last_answer"] is not None:
        metadata = st.session_state["last_metadata"]

        st.subheader("Answer")

        st.caption(
            f"Backend: `{metadata.get('backend')}` | "
            f"top_k: `{metadata.get('top_k')}` | "
            f"LLM: `{metadata.get('use_llm')}`"
        )

        st.markdown(st.session_state["last_answer"])

        if options["show_sources"]:
            display_sources(
                st.session_state["last_results"],
                show_full_sources=options["show_full_sources"],
            )

        if options["show_debug"]:
            display_debug_information(
                question=metadata.get("question", ""),
                corpus_path=metadata.get("corpus_path", ""),
                config_path=metadata.get("config_path", ""),
                backend=metadata.get("backend", ""),
                top_k=metadata.get("top_k", 0),
                use_llm=metadata.get("use_llm", False),
                config=options["config"],
            )


if __name__ == "__main__":
    main()