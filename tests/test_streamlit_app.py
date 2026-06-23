from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

import streamlit_app
from streamlit_app import (
    _is_incomplete_mmore_index_error,
    render_chat_history,
    render_last_answer,
)
from streamlit_display import (
    display_debug_information,
    format_backend_label,
    get_retrieval_mode,
)

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_result_mapping import (
    MMORE_RETRIEVAL_MODE_METADATA_KEY,
)


def test_streamlit_app_import_smoke():
    """Importing the refactored UI should expose its entry point."""
    assert callable(streamlit_app.main)


def test_is_incomplete_mmore_index_error_detects_known_message():
    error = RuntimeError("The MMORE index metadata is incomplete. Rebuild it.")

    assert _is_incomplete_mmore_index_error(error) is True


def test_is_incomplete_mmore_index_error_ignores_other_errors():
    error = RuntimeError("Something else failed.")

    assert _is_incomplete_mmore_index_error(error) is False


def test_format_backend_label_includes_mmore_retrieval_mode():
    assert format_backend_label("mmore", "corpus_fallback") == (
        "mmore (corpus_fallback)"
    )
    assert format_backend_label("simple", None) == "simple"


def test_get_retrieval_mode_reads_first_tagged_result():
    result = RetrievalResult(
        document=DocumentRecord(
            doc_id="doc-1",
            content="content",
            source_type="markdown_section",
            metadata={MMORE_RETRIEVAL_MODE_METADATA_KEY: "native_index"},
        ),
        score=1.0,
    )

    assert get_retrieval_mode([result]) == "native_index"


def test_debug_information_shows_query_rewrite_decision(monkeypatch):
    rendered: list[str] = []
    monkeypatch.setattr("streamlit_display.st.subheader", lambda _text: None)
    monkeypatch.setattr("streamlit_display.st.markdown", rendered.append)

    display_debug_information(
        question="How do I configure it?",
        retrieval_query="How is MMORE indexing configured?",
        is_followup=True,
        followup_ambiguous=False,
        corpus_path="corpus.jsonl",
        config_path="app_config.yaml",
        backend="simple",
        retrieval_mode=None,
        top_k=5,
        use_llm=True,
        config=None,
    )

    assert "**Original user question:** `How do I configure it?`" in rendered
    assert (
        "**Rewritten retrieval query:** `How is MMORE indexing configured?`"
        in rendered
    )
    assert "**Detected as follow-up:** `True`" in rendered


def test_chat_history_renders_messages_in_chronological_chat_bubbles(monkeypatch):
    roles: list[str] = []
    rendered: list[str] = []
    monkeypatch.setattr(
        "streamlit_app.st.session_state",
        {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Follow-up"},
            ]
        },
    )
    monkeypatch.setattr(
        "streamlit_app.st.chat_message",
        lambda role: roles.append(role) or nullcontext(),
    )
    monkeypatch.setattr("streamlit_app.st.markdown", rendered.append)

    render_chat_history()

    assert roles == ["user", "assistant", "user"]
    assert rendered == ["First question", "First answer", "Follow-up"]


def test_latest_answer_details_are_collapsed_secondary_content(monkeypatch):
    expander_calls: list[tuple[str, bool]] = []
    source_calls: list[tuple[list, bool]] = []
    monkeypatch.setattr(
        "streamlit_app.st.session_state",
        {
            "last_answer": "Answer",
            "last_results": ["source"],
            "last_metadata": {
                "backend": "simple",
                "top_k": 1,
                "use_llm": True,
            },
        },
    )
    monkeypatch.setattr(
        "streamlit_app.st.expander",
        lambda label, expanded: (
            expander_calls.append((label, expanded)) or nullcontext()
        ),
    )
    monkeypatch.setattr("streamlit_app.st.caption", lambda _text: None)
    monkeypatch.setattr(
        "streamlit_app.display_sources",
        lambda results, show_full_sources: source_calls.append(
            (results, show_full_sources)
        ),
    )

    render_last_answer(
        {
            "show_sources": True,
            "show_full_sources": False,
            "show_debug": False,
        }
    )

    assert expander_calls == [("Latest answer sources and diagnostics", False)]
    assert source_calls == [(["source"], False)]


def test_main_renders_chat_history_before_bottom_chat_input(monkeypatch, tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("", encoding="utf-8")
    events: list[str] = []
    options = {
        "show_sources": False,
        "show_full_sources": False,
        "show_debug": False,
    }

    monkeypatch.setattr("streamlit_app.initialize_session_state", lambda _path: None)
    monkeypatch.setattr("streamlit_app.apply_pending_state_updates", lambda: None)
    monkeypatch.setattr("streamlit_app.st.session_state", {"corpus_path": str(corpus)})
    monkeypatch.setattr("streamlit_app.st.title", lambda _text: None)
    monkeypatch.setattr("streamlit_app.st.caption", lambda _text: None)
    monkeypatch.setattr("streamlit_app.render_sidebar", lambda **_kwargs: options)
    monkeypatch.setattr("streamlit_app.render_project_setup", lambda **_kwargs: None)
    monkeypatch.setattr(
        "streamlit_app.render_conversation_header",
        lambda: events.append("header"),
    )
    monkeypatch.setattr(
        "streamlit_app.render_chat_history",
        lambda: events.append("history"),
    )

    def fake_chat_input(_placeholder, disabled):
        assert disabled is False
        events.append("input")
        return None

    monkeypatch.setattr("streamlit_app.st.chat_input", fake_chat_input)
    monkeypatch.setattr(
        "streamlit_app.render_last_answer",
        lambda _options: events.append("details"),
    )

    streamlit_app.main()

    assert events == ["header", "history", "input", "details"]
