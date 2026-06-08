from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from streamlit_app import _is_incomplete_mmore_index_error


def test_is_incomplete_mmore_index_error_detects_known_message():
    error = RuntimeError("The MMORE index metadata is incomplete. Rebuild it.")

    assert _is_incomplete_mmore_index_error(error) is True


def test_is_incomplete_mmore_index_error_ignores_other_errors():
    error = RuntimeError("Something else failed.")

    assert _is_incomplete_mmore_index_error(error) is False
