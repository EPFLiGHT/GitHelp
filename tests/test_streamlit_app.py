from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from streamlit_app import _is_incomplete_mmore_index_error
from streamlit_display import format_backend_label, get_retrieval_mode

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_result_mapping import (
    MMORE_RETRIEVAL_MODE_METADATA_KEY,
)


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
