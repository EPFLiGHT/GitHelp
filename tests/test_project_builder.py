from __future__ import annotations

from pathlib import Path

import pytest

from githelp.projects.project_builder import (
    build_project_config,
    infer_code_path,
    infer_docs_path,
    infer_package_name,
    prepare_project_paths,
    slugify_project_name,
    write_project_config,
    prepare_project_with_simple_index,
)


def test_slugify_project_name():
    assert slugify_project_name("MMORE") == "mmore"
    assert slugify_project_name("My Project") == "my-project"
    assert slugify_project_name("  weird__Name!! ") == "weird__name"


def test_infer_docs_path_prefers_docs_source(tmp_path: Path):
    project_path = tmp_path / "project"
    docs_source = project_path / "docs" / "source"
    docs_source.mkdir(parents=True)

    assert infer_docs_path(project_path) == docs_source.resolve()


def test_infer_docs_path_falls_back_to_docs(tmp_path: Path):
    project_path = tmp_path / "project"
    docs_path = project_path / "docs"
    docs_path.mkdir(parents=True)

    assert infer_docs_path(project_path) == docs_path.resolve()


def test_infer_code_path_prefers_src_package(tmp_path: Path):
    project_path = tmp_path / "project"
    package_path = project_path / "src" / "example"
    package_path.mkdir(parents=True)

    assert infer_code_path(project_path, "example") == package_path.resolve()


def test_infer_package_name_prefers_src_package(tmp_path: Path):
    project_path = tmp_path / "project"
    package_path = project_path / "src" / "example"
    package_path.mkdir(parents=True)

    assert infer_package_name(project_path, "example") == "example"


def test_build_project_config_for_local_project(tmp_path: Path):
    project_path = tmp_path / "my_project"
    docs_path = project_path / "docs" / "source"
    code_path = project_path / "src" / "my_project"
    examples_path = project_path / "examples"

    docs_path.mkdir(parents=True)
    code_path.mkdir(parents=True)
    examples_path.mkdir(parents=True)

    config = build_project_config(project_path)

    assert config["project_name"] == "my_project"
    assert config["package_name"] == "my_project"
    assert config["repo_path"] == str(project_path.resolve())
    assert config["docs_path"] == str(docs_path.resolve())
    assert config["code_path"] == str(code_path.resolve())
    assert config["include_yaml_configs"] is True
    assert str(examples_path.resolve()) in config["yaml_config_paths"]
    assert config["include_repo_structure"] is True


def test_build_project_config_rejects_missing_project_path(tmp_path: Path):
    missing_path = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        build_project_config(missing_path)


def test_write_project_config(tmp_path: Path):
    output_path = tmp_path / "project_config.yaml"

    config = {
        "project_name": "example",
        "package_name": "example",
        "repo_path": "/tmp/example",
        "docs_path": "/tmp/example/docs",
        "code_path": "/tmp/example/src/example",
    }

    write_project_config(config, output_path)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "project_name: example" in content
    assert "package_name: example" in content


def test_prepare_project_paths(tmp_path: Path):
    githelp_root = tmp_path / "githelp"
    project_path = tmp_path / "target_project"

    githelp_root.mkdir()
    project_path.mkdir()

    prepared = prepare_project_paths(
        githelp_root=githelp_root,
        project_path=project_path,
        project_name="Target Project",
    )

    assert prepared["project_name"] == "target-project"
    assert prepared["project_dir"] == githelp_root / "data" / "projects" / "target-project"
    assert prepared["project_config_path"] == (
        githelp_root / "data" / "projects" / "target-project" / "project_config.yaml"
    )
    assert prepared["corpus_path"] == (
        githelp_root / "data" / "projects" / "target-project" / "corpus.jsonl"
    )


def test_prepare_project_with_simple_index_uses_corpus_builder(monkeypatch, tmp_path):
    githelp_root = tmp_path / "githelp"
    project_path = tmp_path / "target_project"

    githelp_root.mkdir()
    project_path.mkdir()

    def fake_build_corpus_for_project(
        githelp_root,
        project_path,
        project_name=None,
    ):
        return {
            "project_name": "target-project",
            "project_dir": str(tmp_path / "githelp" / "data" / "projects" / "target-project"),
            "project_config_path": str(tmp_path / "project_config.yaml"),
            "corpus_path": str(tmp_path / "corpus.jsonl"),
            "stdout": "built",
            "stderr": "",
        }

    monkeypatch.setattr(
        "githelp.projects.project_builder.build_corpus_for_project",
        fake_build_corpus_for_project,
    )

    result = prepare_project_with_simple_index(
        githelp_root=githelp_root,
        project_path=project_path,
    )

    assert result["indexing_mode"] == "simple"
    assert result["backend"] == "simple"
    assert result["project_name"] == "target-project"