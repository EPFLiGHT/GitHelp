from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from githelp.rag.answering import (  # noqa: E402
    AMBIGUOUS_FOLLOWUP_RESPONSE,
    answer_question,
    answer_question_with_provider,
    resolve_retrieval_query,
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
    initialize_session_state,
    persist_current_state,
)
from streamlit_theme import (  # noqa: E402
    apply_githelp_theme,
    render_githelp_header,
    resolve_logo_path,
)


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "app_config.yaml"
DEFAULT_APP_STATE_PATH = PROJECT_ROOT / "data" / "app_state.json"


st.set_page_config(
    page_title="GitHelp",
    page_icon=str(resolve_logo_path()),
    layout="wide",
)


def persist_app_state() -> None:
    """Persist the app state in GitHelp's default state file."""
    persist_current_state(DEFAULT_APP_STATE_PATH)


def get_recent_chat_context(max_messages: int = 6) -> list[dict[str, str]]:
    """Return only the latest messages used as lightweight LLM context."""
    messages = st.session_state.get("messages", [])
    return messages[-max_messages:]


def render_conversation_header() -> None:
    """Render a compact conversation heading and chat action."""
    heading_column, action_column = st.columns([6, 1])

    with heading_column:
        st.subheader("Conversation")

    with action_column:
        st.button(
            "Clear chat",
            on_click=clear_chat,
            use_container_width=True,
        )


def render_chat_history() -> None:
    """Display the in-memory conversation in chronological chat bubbles."""
    messages = st.session_state.get("messages", [])

    if not messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Ask me about the selected project's documentation, code, "
                "configuration, or deployment."
            )
        return

    for message in messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")

        with st.chat_message(role):
            st.markdown(content)


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
        query_decision = resolve_retrieval_query(
            question=question,
            chat_history=chat_history,
            llm_provider=llm_provider,
        )

        if query_decision.is_ambiguous:
            return (
                AMBIGUOUS_FOLLOWUP_RESPONSE,
                [],
                query_decision.retrieval_query,
                query_decision.is_followup,
                True,
            )

        answer, results = answer_question_with_provider(
            question=question,
            llm_provider=llm_provider,
            corpus_path=corpus,
            top_k=options["top_k"],
            backend=backend,
            config_path=options["config_path"],
            chat_history=chat_history,
            retrieval_query=query_decision.retrieval_query,
        )
        return (
            answer,
            results,
            query_decision.retrieval_query,
            query_decision.is_followup,
            False,
        )

    answer, results = answer_question(
        question=question,
        corpus_path=corpus,
        top_k=options["top_k"],
        backend=backend,
        config_path=options["config_path"],
    )
    return answer, results, question, False, False


def answer_current_question(question: str, options: dict) -> str | None:
    """Answer the current question, persist it, and return the answer text."""
    if not question.strip():
        st.warning("Please enter a question.")
        return None

    corpus_path = st.session_state.get("corpus_path", "")

    if not corpus_path:
        st.error("No corpus selected. Build a corpus first in Project setup.")
        return None

    corpus = Path(corpus_path)

    if not corpus.exists():
        st.error(f"Corpus file not found: {corpus}")
        return None

    with st.spinner("Retrieving sources and generating answer..."):
        backend_used = options["backend"]
        # Recent chat may resolve a vague follow-up, but it is never appended
        # wholesale to the retrieval query.
        chat_history = get_recent_chat_context()

        try:
            (
                answer,
                results,
                retrieval_query,
                is_followup,
                followup_ambiguous,
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
                        is_followup,
                        followup_ambiguous,
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
                    return None
            else:
                st.error("An error occurred while answering the question.")
                st.exception(error)
                return None

        except Exception as error:
            st.error("An error occurred while answering the question.")
            st.exception(error)
            return None

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
        "is_followup": is_followup,
        "followup_ambiguous": followup_ambiguous,
    }

    persist_app_state()
    return answer


def render_last_answer(options: dict) -> None:
    """Render latest evidence and diagnostics as secondary content."""
    if st.session_state["last_answer"] is None:
        return

    if not options["show_sources"] and not options["show_debug"]:
        return

    metadata = st.session_state["last_metadata"]
    backend_label = format_backend_label(
        str(metadata.get("backend", "")),
        metadata.get("retrieval_mode"),
    )

    with st.expander("Latest answer sources and diagnostics", expanded=False):
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
                is_followup=metadata.get("is_followup", False),
                followup_ambiguous=metadata.get("followup_ambiguous", False),
            )


def main() -> None:
    initialize_session_state(DEFAULT_APP_STATE_PATH)
    apply_pending_state_updates()
    apply_githelp_theme()

    render_githelp_header()

    options = render_sidebar(
        default_config_path=DEFAULT_CONFIG_PATH,
        persist_current_state=persist_app_state,
    )

    render_project_setup(
        project_root=PROJECT_ROOT,
        persist_current_state=persist_app_state,
    )

    render_conversation_header()
    render_chat_history()

    corpus_path = st.session_state.get("corpus_path", "")
    chat_ready = bool(corpus_path and Path(corpus_path).exists())
    placeholder = (
        "Ask a follow-up or start a new question..."
        if chat_ready
        else "Build a project index before asking a question"
    )
    question = st.chat_input(placeholder, disabled=not chat_ready)

    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            answer = answer_current_question(question, options)
            if answer is not None:
                st.markdown(answer)

    render_last_answer(options)


if __name__ == "__main__":
    main()
