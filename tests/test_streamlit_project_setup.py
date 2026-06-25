from __future__ import annotations

import pytest

from streamlit_project_setup import _resolve_project_path


def test_resolve_project_path_returns_local_path_without_github(monkeypatch, tmp_path):
    result = _resolve_project_path(
        project_root=tmp_path,
        project_source="Local project path",
        project_path="/tmp/project",
        github_repository_url="",
    )

    assert result == ("/tmp/project", "")


def test_resolve_project_path_loads_github_repository(monkeypatch, tmp_path):
    writes = []

    def fake_load_github_repository(githelp_root, repository_url):
        return {
            "repository_url": "https://github.com/swiss-ai/mmore.git",
            "owner": "swiss-ai",
            "repo": "mmore",
            "project_name": "mmore",
            "repository_path": str(
                tmp_path / "data" / "repositories" / "swiss-ai-mmore"
            ),
            "cloned": True,
        }

    class FakeSessionState(dict):
        pass

    monkeypatch.setattr(
        "streamlit_project_setup.load_github_repository",
        fake_load_github_repository,
    )
    monkeypatch.setattr(
        "streamlit_project_setup.st.session_state",
        FakeSessionState(),
    )
    monkeypatch.setattr(
        "streamlit_project_setup.st.write",
        lambda message: writes.append(message),
    )

    result = _resolve_project_path(
        project_root=tmp_path,
        project_source="Public GitHub repository URL",
        project_path="",
        github_repository_url="https://github.com/swiss-ai/mmore",
    )

    assert result == (
        str(tmp_path / "data" / "repositories" / "swiss-ai-mmore"),
        "mmore",
    )
    assert writes == ["Cloned `https://github.com/swiss-ai/mmore.git`."]


def test_resolve_project_path_rejects_blank_github_url(tmp_path):
    with pytest.raises(ValueError, match="Please provide a GitHub repository URL"):
        _resolve_project_path(
            project_root=tmp_path,
            project_source="Public GitHub repository URL",
            project_path="",
            github_repository_url="",
        )
