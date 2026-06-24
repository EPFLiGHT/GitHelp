from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest

from streamlit_theme import (
    GITHELP_CSS,
    apply_githelp_theme,
    render_githelp_header,
    resolve_logo_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_resolve_logo_path_uses_repository_relative_asset():
    logo_path = resolve_logo_path(PROJECT_ROOT)

    assert logo_path == PROJECT_ROOT / "docs" / "_static" / "images" / "logo.png"
    assert logo_path.is_file()


def test_resolve_logo_path_reports_checked_location(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="docs/_static/images/logo.png"):
        resolve_logo_path(tmp_path / "missing-project")


def test_apply_githelp_theme_injects_accessible_green_styles(monkeypatch):
    calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "streamlit_theme.st.markdown",
        lambda body, unsafe_allow_html: calls.append((body, unsafe_allow_html)),
    )

    apply_githelp_theme()

    assert calls == [(GITHELP_CSS, True)]
    assert "--githelp-green: #7bc89c" in GITHELP_CSS
    assert '[data-testid="stChatMessageAvatarUser"]' in GITHELP_CSS
    assert '[data-testid="stChatMessageAvatarAssistant"]' in GITHELP_CSS
    assert "prefers-color-scheme: dark" in GITHELP_CSS


def test_render_githelp_header_uses_full_resolution_repository_logo(monkeypatch):
    images: list[tuple[str, str]] = []
    titles: list[str] = []
    monkeypatch.setattr(
        "streamlit_theme.st.columns",
        lambda *_args, **_kwargs: [nullcontext(), nullcontext()],
    )
    monkeypatch.setattr(
        "streamlit_theme.st.image",
        lambda path, width: images.append((path, width)),
    )
    monkeypatch.setattr("streamlit_theme.st.title", titles.append)
    monkeypatch.setattr("streamlit_theme.st.caption", lambda _text: None)

    render_githelp_header()

    assert images == [(str(resolve_logo_path()), "stretch")]
    assert titles == ["GitHelp"]
