from __future__ import annotations

import argparse
from pathlib import Path

from githelp.config import ProjectConfig, load_project_config
from githelp.corpus.builder import build_corpus, save_corpus_jsonl, summarize_corpus
from githelp.utils.paths import (
    PROCESSED_DATA_DIR,
    ensure_parent_dir,
    resolve_project_path,
)


"""
Build the GitHelp corpus from configured project sources.

This script reads a project configuration, loads documentation sources such as
Markdown files, Python docstrings, YAML configs, and repository structure, then
saves the resulting corpus as JSONL.

By default, it keeps the original behavior:
    configs/project_config.yaml -> data/processed/corpus.jsonl

It can also be used dynamically:
    python scripts/build_corpus.py \
        --config data/projects/mmore/project_config.yaml \
        --output-path data/projects/mmore/corpus.jsonl
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build a GitHelp corpus from a project configuration."
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "Path to the project configuration YAML file. "
            "If omitted, GitHelp uses the default project config."
        ),
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=PROCESSED_DATA_DIR / "corpus.jsonl",
        help="Path where the generated corpus JSONL file should be written.",
    )

    return parser.parse_args()


def load_config(config_path: Path | None) -> ProjectConfig:
    """
    Load the project configuration.

    If config_path is None, keep the original behavior and load the default
    project config.
    """
    if config_path is None:
        return load_project_config()

    return load_project_config(resolve_project_path(config_path))


def main() -> None:
    """Build and save the configured GitHelp corpus."""
    args = parse_args()

    project_config = load_config(args.config)
    output_path = ensure_parent_dir(resolve_project_path(args.output_path))

    project_name = project_config.project_name
    package_name = project_config.package_name
    repo_path = project_config.repo_path
    docs_path = project_config.docs_path
    code_path = project_config.code_path
    include_yaml_configs = project_config.include_yaml_configs
    yaml_config_paths = project_config.yaml_config_paths
    include_repo_structure = project_config.include_repo_structure
    repo_structure_max_depth = project_config.repo_structure_max_depth

    print("Building GitHelp corpus")
    print("-" * 80)

    if args.config is None:
        print("project_config: default configs/project_config.yaml")
    else:
        print(f"project_config: {resolve_project_path(args.config)}")

    print(f"project_name: {project_name}")
    print(f"package_name: {package_name}")
    print(f"repo_path: {repo_path}")
    print(f"docs_path: {docs_path}")
    print(f"code_path: {code_path}")
    print(f"include_yaml_configs: {include_yaml_configs}")
    print(f"yaml_config_paths: {yaml_config_paths}")
    print(f"include_repo_structure: {include_repo_structure}")
    print(f"repo_structure_max_depth: {repo_structure_max_depth}")
    print(f"output_path: {output_path}")
    print("-" * 80)

    documents = build_corpus(
        docs_path=docs_path,
        code_path=code_path,
        project_name=project_name,
        package_name=package_name,
        repo_path=repo_path,
        include_yaml_configs=include_yaml_configs,
        yaml_config_paths=yaml_config_paths,
        include_repo_structure=include_repo_structure,
        repo_structure_max_depth=repo_structure_max_depth,
    )

    save_corpus_jsonl(documents, output_path)

    summary = summarize_corpus(documents)

    print()
    print(f"Built corpus with {len(documents)} documents")
    print(f"Saved to: {output_path}")
    print("Breakdown by source_type:")

    for source_type, count in summary.items():
        print(f"  - {source_type}: {count}")


if __name__ == "__main__":
    main()
