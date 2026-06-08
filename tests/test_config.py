from __future__ import annotations

from pathlib import Path

from githelp.config import (
    AppConfig,
    IndexingConfig,
    LLMConfig,
    ProjectConfig,
    load_app_config,
    load_indexing_config,
    load_project_config,
)


def test_app_config_dataclass_extracts_nested_llm_and_project_path(tmp_path: Path):
    config_path = tmp_path / "app_config.yaml"
    config_path.write_text(
        "app_title: Custom GitHelp\n"
        "project_profile: mmore\n"
        "project:\n"
        "  config_path: data/projects/mmore/project_config.yaml\n"
        "llm:\n"
        "  provider: qwen\n"
        "  model_name: Qwen/Test\n"
        "  max_new_tokens: 64\n"
        "  temperature: 0.2\n"
        "  enable_thinking: true\n",
        encoding="utf-8",
    )

    config = load_app_config(config_path)

    assert config == AppConfig(
        app_title="Custom GitHelp",
        project_profile="mmore",
        project_config_path="data/projects/mmore/project_config.yaml",
        llm=LLMConfig(
            provider="qwen",
            model_name="Qwen/Test",
            max_new_tokens=64,
            temperature=0.2,
            enable_thinking=True,
        ),
    )


def test_project_config_dataclass_normalizes_lists(tmp_path: Path):
    config_path = tmp_path / "project_config.yaml"
    config_path.write_text(
        "project_name: example\n"
        "package_name: example_pkg\n"
        "repo_path: /tmp/example\n"
        "docs_path: /tmp/example/docs\n"
        "code_path: /tmp/example/src/example_pkg\n"
        "include_yaml_configs: true\n"
        "yaml_config_paths:\n"
        "  - /tmp/example/configs\n"
        "include_repo_structure: true\n"
        "repo_structure_max_depth: 3\n"
        "include_extensions:\n"
        "  - .md\n"
        "exclude_patterns:\n"
        "  - .git\n",
        encoding="utf-8",
    )

    config = load_project_config(config_path)

    assert config == ProjectConfig(
        project_name="example",
        package_name="example_pkg",
        repo_path="/tmp/example",
        docs_path="/tmp/example/docs",
        code_path="/tmp/example/src/example_pkg",
        include_yaml_configs=True,
        yaml_config_paths=["/tmp/example/configs"],
        include_repo_structure=True,
        repo_structure_max_depth=3,
        include_extensions=[".md"],
        exclude_patterns=[".git"],
    )


def test_indexing_config_dataclass_uses_defaults_for_missing_fields(tmp_path: Path):
    config_path = tmp_path / "indexing_config.yaml"
    config_path.write_text("collection_name: docs\n", encoding="utf-8")

    config = load_indexing_config(config_path)

    assert config == IndexingConfig(collection_name="docs")
