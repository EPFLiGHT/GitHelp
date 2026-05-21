from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from docask.config import load_yaml
from docask.rag.llm_factory import create_llm_provider
from docask.rag.answering import (
    answer_question,
    answer_question_with_provider,
)

DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "processed" / "corpus.jsonl"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "app_config.yaml"


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
    if "question" not in st.session_state:
        st.session_state["question"] = ""

    if "last_answer" not in st.session_state:
        st.session_state["last_answer"] = None

    if "last_results" not in st.session_state:
        st.session_state["last_results"] = []

    if "last_metadata" not in st.session_state:
        st.session_state["last_metadata"] = {}


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
        st.markdown("**Loaded config:**")
        st.json(config)


def main() -> None:
    initialize_session_state()

    st.title("DocAsk")
    st.caption(
        "Ask questions about a software project's documentation and code documentation."
    )

    with st.sidebar:
        st.header("Settings")

        corpus_path = st.text_input(
            "Corpus path",
            value=str(DEFAULT_CORPUS_PATH),
        )

        config_path = st.text_input(
            "Config path",
            value=str(DEFAULT_CONFIG_PATH),
        )

        backend = st.selectbox(
            "Retrieval backend",
            options=["simple", "mmore"],
            index=1,
        )

        top_k = st.slider(
            "Number of sources",
            min_value=1,
            max_value=10,
            value=5,
        )

        use_llm = st.toggle(
            "Use LLM",
            value=True,
        )

        show_sources = st.toggle(
            "Show retrieved sources",
            value=True,
        )

        show_full_sources = st.toggle(
            "Show full source content",
            value=False,
            disabled=not show_sources,
        )

        show_debug = st.toggle(
            "Show debug information",
            value=False,
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

        corpus = Path(corpus_path)

        if not corpus.exists():
            st.error(f"Corpus file not found: {corpus}")
            return

        with st.spinner("Retrieving sources and generating answer..."):
            try:
                if use_llm:
                    llm_provider = get_llm_provider(config_path)

                    answer, results = answer_question_with_provider(
                        question=question,
                        llm_provider=llm_provider,
                        corpus_path=corpus,
                        top_k=top_k,
                        backend=backend,
                        config_path=config_path,
                    )
                else:
                    answer, results = answer_question(
                        question=question,
                        corpus_path=corpus,
                        top_k=top_k,
                        backend=backend,
                    )

            except Exception as error:
                st.error("An error occurred while answering the question.")
                st.exception(error)
                return

        st.session_state["last_answer"] = answer
        st.session_state["last_results"] = results
        st.session_state["last_metadata"] = {
            "question": question,
            "backend": backend,
            "top_k": top_k,
            "use_llm": use_llm,
            "corpus_path": corpus_path,
            "config_path": config_path,
        }

    if st.session_state["last_answer"] is not None:
        metadata = st.session_state["last_metadata"]

        st.subheader("Answer")

        st.caption(
            f"Backend: `{metadata.get('backend')}` | "
            f"top_k: `{metadata.get('top_k')}` | "
            f"LLM: `{metadata.get('use_llm')}`"
        )

        st.markdown(st.session_state["last_answer"])

        if show_sources:
            display_sources(
                st.session_state["last_results"],
                show_full_sources=show_full_sources,
            )

        if show_debug:
            display_debug_information(
                question=metadata.get("question", ""),
                corpus_path=metadata.get("corpus_path", ""),
                config_path=metadata.get("config_path", ""),
                backend=metadata.get("backend", ""),
                top_k=metadata.get("top_k", 0),
                use_llm=metadata.get("use_llm", False),
                config=config,
            )


if __name__ == "__main__":
    main()