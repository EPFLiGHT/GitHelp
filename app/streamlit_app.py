from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from githelp.rag.answering import (  # noqa: E402
    answer_question,
    answer_question_with_provider,
)
from streamlit_display import display_debug_information, display_sources  # noqa: E402
from streamlit_project_setup import render_project_setup  # noqa: E402
from streamlit_sidebar import get_llm_provider, render_sidebar  # noqa: E402
from streamlit_state import (  # noqa: E402
    apply_pending_state_updates,
    clear_question,
    initialize_session_state,
    persist_current_state,
)


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "app_config.yaml"
DEFAULT_APP_STATE_PATH = PROJECT_ROOT / "data" / "app_state.json"


st.set_page_config(
    page_title="GitHelp",
    page_icon="📚",
    layout="wide",
)


def persist_app_state() -> None:
    """Persist the app state in GitHelp's default state file."""
    persist_current_state(DEFAULT_APP_STATE_PATH)


def render_answer_controls() -> tuple[str, bool]:
    """Render the question input and return the submitted question."""
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

    return question, ask_button


def answer_current_question(question: str, options: dict) -> None:
    """Answer the current question and persist the displayed result."""
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
                    config_path=options["config_path"],
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

    persist_app_state()


def render_last_answer(options: dict) -> None:
    """Render the latest answer, sources, and optional debug information."""
    if st.session_state["last_answer"] is None:
        return

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


def main() -> None:
    initialize_session_state(DEFAULT_APP_STATE_PATH)
    apply_pending_state_updates()

    st.title("GitHelp")
    st.caption(
        "Ask questions about a software project's documentation and code documentation."
    )

    options = render_sidebar(
        default_config_path=DEFAULT_CONFIG_PATH,
        persist_current_state=persist_app_state,
    )

    render_project_setup(
        project_root=PROJECT_ROOT,
        persist_current_state=persist_app_state,
    )

    st.divider()

    question, ask_button = render_answer_controls()

    if ask_button:
        answer_current_question(question, options)

    render_last_answer(options)


if __name__ == "__main__":
    main()
