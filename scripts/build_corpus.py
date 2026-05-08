from __future__ import annotations

from docask.config import load_all_configs
from docask.corpus.builder import build_corpus, save_corpus_jsonl, summarize_corpus
from docask.utils.paths import PROCESSED_DATA_DIR


"""
Build the DocAsk corpus from the configured project sources.

This script reads the project configuration, loads documentation sources
such as Markdown files, Python docstrings, YAML configs, and repository
structure, then saves the resulting corpus as JSONL.
"""


def main() -> None:
    """Build and save the configured DocAsk corpus."""
    configs = load_all_configs()
    project_config = configs["project"]

    project_name = project_config.get("project_name", "project")
    package_name = project_config.get("package_name")
    repo_path = project_config.get("repo_path")
    docs_path = project_config["docs_path"]
    code_path = project_config.get("code_path")

    include_yaml_configs = project_config.get("include_yaml_configs", False)
    yaml_config_paths = project_config.get("yaml_config_paths", [])

    include_repo_structure = project_config.get("include_repo_structure", False)
    repo_structure_max_depth = project_config.get("repo_structure_max_depth", 4)

    print("Building DocAsk corpus")
    print("-" * 80)
    print(f"project_name: {project_name}")
    print(f"package_name: {package_name}")
    print(f"repo_path: {repo_path}")
    print(f"docs_path: {docs_path}")
    print(f"code_path: {code_path}")
    print(f"include_yaml_configs: {include_yaml_configs}")
    print(f"yaml_config_paths: {yaml_config_paths}")
    print(f"include_repo_structure: {include_repo_structure}")
    print(f"repo_structure_max_depth: {repo_structure_max_depth}")
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

    output_path = PROCESSED_DATA_DIR / "corpus.jsonl"
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