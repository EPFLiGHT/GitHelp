from __future__ import annotations

from pathlib import Path

import pytest

from githelp.projects.github_loader import (
    get_github_repository_path,
    load_github_repository,
    parse_github_repository_url,
    prepare_github_project_with_simple_index,
)
from githelp.projects.project_builder import ProjectCommandError


def test_parse_github_repository_url_accepts_https_url():
    reference = parse_github_repository_url("https://github.com/swiss-ai/mmore")

    assert reference == {
        "owner": "swiss-ai",
        "repo": "mmore",
        "project_name": "mmore",
        "clone_url": "https://github.com/swiss-ai/mmore.git",
    }


def test_parse_github_repository_url_accepts_ssh_url():
    reference = parse_github_repository_url("git@github.com:swiss-ai/mmore.git")

    assert reference["owner"] == "swiss-ai"
    assert reference["repo"] == "mmore"
    assert reference["clone_url"] == "https://github.com/swiss-ai/mmore.git"


def test_parse_github_repository_url_rejects_non_github_url():
    with pytest.raises(ValueError, match="Unsupported GitHub repository URL"):
        parse_github_repository_url("https://gitlab.com/example/project")


def test_get_github_repository_path_uses_owner_and_repo_slug(tmp_path: Path):
    reference = parse_github_repository_url("https://github.com/swiss-ai/mmore")

    repository_path = get_github_repository_path(tmp_path, reference)

    assert repository_path == tmp_path / "data" / "repositories" / "swiss-ai-mmore"


def test_load_github_repository_reuses_existing_clone(tmp_path: Path):
    reference = parse_github_repository_url("https://github.com/swiss-ai/mmore")
    repository_path = get_github_repository_path(tmp_path, reference)
    repository_path.mkdir(parents=True)
    (repository_path / "README.md").write_text("Existing clone", encoding="utf-8")

    result = load_github_repository(
        githelp_root=tmp_path,
        repository_url="https://github.com/swiss-ai/mmore",
    )

    assert result["repository_path"] == str(repository_path)
    assert result["cloned"] is False


def test_load_github_repository_clones_when_missing(monkeypatch, tmp_path: Path):
    calls = []

    class FakeCompletedProcess:
        returncode = 0
        stdout = "cloned"
        stderr = ""

    def fake_run(command, text, capture_output):
        calls.append(
            {
                "command": command,
                "text": text,
                "capture_output": capture_output,
            }
        )
        Path(command[-1]).mkdir(parents=True)
        return FakeCompletedProcess()

    monkeypatch.setattr(
        "githelp.projects.github_loader.subprocess.run",
        fake_run,
    )

    result = load_github_repository(
        githelp_root=tmp_path,
        repository_url="https://github.com/swiss-ai/mmore",
    )

    assert result["cloned"] is True
    assert result["repository_path"].endswith("data/repositories/swiss-ai-mmore")
    assert calls == [
        {
            "command": [
                "git",
                "clone",
                "--depth",
                "1",
                "https://github.com/swiss-ai/mmore.git",
                result["repository_path"],
            ],
            "text": True,
            "capture_output": True,
        }
    ]


def test_load_github_repository_raises_structured_error_on_clone_failure(
    monkeypatch,
    tmp_path: Path,
):
    class FakeCompletedProcess:
        returncode = 1
        stdout = ""
        stderr = "clone failed"

    def fake_run(command, text, capture_output):
        return FakeCompletedProcess()

    monkeypatch.setattr(
        "githelp.projects.github_loader.subprocess.run",
        fake_run,
    )

    with pytest.raises(ProjectCommandError) as error_info:
        load_github_repository(
            githelp_root=tmp_path,
            repository_url="https://github.com/swiss-ai/mmore",
        )

    error = error_info.value
    assert error.label == "GitHub repository clone failed"
    assert error.stderr == "clone failed"


def test_prepare_github_project_with_simple_index_reuses_project_builder(
    monkeypatch,
    tmp_path: Path,
):
    calls = []

    def fake_load_github_repository(githelp_root, repository_url):
        return {
            "repository_url": "https://github.com/swiss-ai/mmore.git",
            "owner": "swiss-ai",
            "repo": "mmore",
            "project_name": "mmore",
            "repository_path": str(tmp_path / "data" / "repositories" / "swiss-ai-mmore"),
            "cloned": True,
        }

    def fake_prepare_project_with_simple_index(githelp_root, project_path, project_name):
        calls.append(
            {
                "githelp_root": githelp_root,
                "project_path": project_path,
                "project_name": project_name,
            }
        )
        return {
            "project_name": project_name,
            "project_dir": str(tmp_path / "data" / "projects" / project_name),
            "project_config_path": str(tmp_path / "project_config.yaml"),
            "corpus_path": str(tmp_path / "corpus.jsonl"),
            "stdout": "built",
            "stderr": "",
            "indexing_mode": "simple",
            "backend": "simple",
        }

    monkeypatch.setattr(
        "githelp.projects.github_loader.load_github_repository",
        fake_load_github_repository,
    )
    monkeypatch.setattr(
        "githelp.projects.github_loader.prepare_project_with_simple_index",
        fake_prepare_project_with_simple_index,
    )

    result = prepare_github_project_with_simple_index(
        githelp_root=tmp_path,
        repository_url="https://github.com/swiss-ai/mmore",
    )

    assert calls == [
        {
            "githelp_root": tmp_path,
            "project_path": str(tmp_path / "data" / "repositories" / "swiss-ai-mmore"),
            "project_name": "mmore",
        }
    ]
    assert result["backend"] == "simple"
    assert result["repository_url"] == "https://github.com/swiss-ai/mmore.git"
    assert result["cloned"] is True
