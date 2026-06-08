from __future__ import annotations

import argparse
import json
from pathlib import Path

from githelp.config import ProjectConfig, load_project_config
from githelp.extractors.python_doc_extractor import extract_python_docs
from githelp.utils.paths import (
    EXTRACTED_CODE_DOCS_DIR,
    ensure_parent_dir,
    resolve_project_path,
)


"""
Extract Python code documentation into a standalone JSONL file.

This script is mainly useful for debugging the Python documentation extractor
independently from the full corpus-building pipeline.

By default, it keeps the original behavior:
    configs/project_config.yaml -> data/extracted_code_docs/code_docs.jsonl

It can also be used dynamically:
    python scripts/extract_code_docs.py \
        --config data/projects/mmore/project_config.yaml \
        --output-path data/projects/mmore/code_docs.jsonl
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract Python documentation records from a project."
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
        default=EXTRACTED_CODE_DOCS_DIR / "code_docs.jsonl",
        help="Path where extracted code documentation should be written.",
    )

    return parser.parse_args()


def load_config(config_path: Path | None) -> ProjectConfig:
    """Load the project configuration."""
    if config_path is None:
        return load_project_config()

    return load_project_config(resolve_project_path(config_path))


def main() -> None:
    """Extract Python docstrings and signatures from the configured code path."""
    args = parse_args()

    project_config = load_config(args.config)

    if project_config.code_path is None:
        raise ValueError("Project config must define code_path to extract code docs.")

    code_path = project_config.code_path
    project_name = project_config.project_name
    package_name = project_config.package_name

    output_path = ensure_parent_dir(resolve_project_path(args.output_path))

    print("Extracting Python documentation")
    print("-" * 80)

    if args.config is None:
        print("project_config: default configs/project_config.yaml")
    else:
        print(f"project_config: {resolve_project_path(args.config)}")

    print(f"project_name: {project_name}")
    print(f"package_name: {package_name}")
    print(f"code_path: {code_path}")
    print(f"output_path: {output_path}")
    print("-" * 80)

    documents = extract_python_docs(
        code_path,
        package_name=package_name,
        project_name=project_name,
    )

    with output_path.open("w", encoding="utf-8") as file:
        for doc in documents:
            file.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")

    print(f"Extracted {len(documents)} code documents")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
