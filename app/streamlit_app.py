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
    answer_question_with_provider_from_results,
    is_reformulation_followup,
    rewrite_query_with_history,
)
from streamlit_display import (  # noqa: E402
    display_debug_information,
    display_sources,
    format_backend_label,
    get_retrieval_mode,
)
from streamlit_project_setup import render_project_setup  # noqa: E402
from streamlit_sidebar import get_llm_provider, render_sidebar  # noqa: E402
from streamlit_state import (  # noqa: E402
    apply_pending_state_updates,
    clear_chat,
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

    col_ask, col_clear_question, col_clear_chat = st.columns([1, 1, 1])

    with col_ask:
        ask_button = st.button("Ask", type="primary")

    with col_clear_question:
        st.button("Clear question", on_click=clear_question)

    with col_clear_chat:
        st.button("Clear chat", on_click=clear_chat)

    return question, ask_button


def get_recent_chat_context(max_messages: int = 6) -> list[dict[str, str]]:
    """Return only the latest messages used as lightweight LLM context."""
    messages = st.session_state.get("messages", [])
    return messages[-max_messages:]


def render_chat_history() -> None:
    """Display the in-memory conversation with a markdown fallback."""
    messages = st.session_state.get("messages", [])

    if not messages:
        return

    st.subheader("Chat")

    for message in messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")

        if hasattr(st, "chat_message"):
            with st.chat_message(role):
                st.markdown(content)
        else:
            label = "User" if role == "user" else "Assistant"
            st.markdown(f"**{label}:** {content}")


def _is_incomplete_mmore_index_error(error: Exception) -> bool:
    """Detect the known partial-MMORE-index failure."""
    return "MMORE index metadata is incomplete" in str(error)


def _answer_with_backend(
    question: str,
    corpus: Path,
    options: dict,
    backend: str,
    chat_history: list[dict[str, str]] | None = None,
):
    """Answer a question with a selected backend."""
    if options["use_llm"]:
        llm_provider = get_llm_provider(options["config_path"])
        retrieval_query = rewrite_query_with_history(
            question=question,
            chat_history=chat_history,
            llm_provider=llm_provider,
        )
        previous_results = st.session_state.get("last_results", [])

        # Pure reformulations can reuse the previous sources safely.
        if previous_results and is_reformulation_followup(question):
            answer, results = answer_question_with_provider_from_results(
                question=question,
                llm_provider=llm_provider,
                results=previous_results,
                config_path=options["config_path"],
                chat_history=chat_history,
            )
            return answer, results, retrieval_query, True

        answer, results = answer_question_with_provider(
            question=question,
            llm_provider=llm_provider,
            corpus_path=corpus,
            top_k=options["top_k"],
            backend=backend,
            config_path=options["config_path"],
            chat_history=chat_history,
            retrieval_query=retrieval_query,
        )
        return answer, results, retrieval_query, False

    answer, results = answer_question(
        question=question,
        corpus_path=corpus,
        top_k=options["top_k"],
        backend=backend,
        config_path=options["config_path"],
    )
    return answer, results, question, False


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
        backend_used = options["backend"]
        # Retrieval uses the current question; only generation receives recent chat.
        chat_history = get_recent_chat_context()

        try:
            (
                answer,
                results,
                retrieval_query,
                used_previous_sources,
            ) = _answer_with_backend(
                question=question,
                corpus=corpus,
                options=options,
                backend=backend_used,
                chat_history=chat_history,
            )

        except RuntimeError as error:
            if backend_used == "mmore" and _is_incomplete_mmore_index_error(error):
                st.warning(
                    "The MMORE index is incomplete, so GitHelp answered with "
                    "the simple backend from the current corpus. Rebuild the "
                    "MMORE index after fixing the MMORE dependencies to use "
                    "`mmore` retrieval again."
                )
                backend_used = "simple"
                st.session_state["pending_backend"] = "simple"

                try:
                    (
                        answer,
                        results,
                        retrieval_query,
                        used_previous_sources,
                    ) = _answer_with_backend(
                        question=question,
                        corpus=corpus,
                        options=options,
                        backend=backend_used,
                        chat_history=chat_history,
                    )
                except Exception as fallback_error:
                    st.error("An error occurred while answering with the fallback backend.")
                    st.exception(fallback_error)
                    return
            else:
                st.error("An error occurred while answering the question.")
                st.exception(error)
                return

        except Exception as error:
            st.error("An error occurred while answering the question.")
            st.exception(error)
            return

    st.session_state["last_answer"] = answer
    st.session_state["last_results"] = results
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    st.session_state["messages"].extend(
        [
            {"role": "user", "content": question.strip()},
            {"role": "assistant", "content": answer},
        ]
    )
    retrieval_mode = get_retrieval_mode(results)
    st.session_state["last_metadata"] = {
        "question": question,
        "backend": backend_used,
        "retrieval_mode": retrieval_mode,
        "top_k": options["top_k"],
        "use_llm": options["use_llm"],
        "corpus_path": corpus_path,
        "config_path": options["config_path"],
        "retrieval_query": retrieval_query,
        "used_previous_sources": used_previous_sources,
    }

    persist_app_state()


def render_last_answer(options: dict) -> None:
    """Render latest answer metadata, sources, and optional debug information."""
    if st.session_state["last_answer"] is None:
        return

    metadata = st.session_state["last_metadata"]

    st.subheader("Latest answer details")
    backend_label = format_backend_label(
        str(metadata.get("backend", "")),
        metadata.get("retrieval_mode"),
    )

    st.caption(
        f"Backend: `{backend_label}` | "
        f"top_k: `{metadata.get('top_k')}` | "
        f"LLM: `{metadata.get('use_llm')}`"
    )

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
            retrieval_mode=metadata.get("retrieval_mode"),
            top_k=metadata.get("top_k", 0),
            use_llm=metadata.get("use_llm", False),
            config=options["config"],
            retrieval_query=metadata.get("retrieval_query"),
            used_previous_sources=metadata.get("used_previous_sources", False),
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

    render_chat_history()
    render_last_answer(options)


if __name__ == "__main__":
    main()
