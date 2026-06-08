from __future__ import annotations

import argparse
import json
from pathlib import Path

from githelp.config import load_all_configs, load_yaml
from githelp.extractors.python_doc_extractor import extract_python_docs
from githelp.utils.paths import EXTRACTED_CODE_DOCS_DIR, PROJECT_ROOT


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


def resolve_path(path: Path) -> Path:
    """Resolve a path relative to the GitHelp project root if needed."""
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_project_config(config_path: Path | None) -> dict:
    """Load the project configuration."""
    if config_path is None:
        configs = load_all_configs()
        return configs["project"]

    return load_yaml(resolve_path(config_path))


def main() -> None:
    """Extract Python docstrings and signatures from the configured code path."""
    args = parse_args()

    project_config = load_project_config(args.config)

    code_path = project_config["code_path"]
    project_name = project_config.get("project_name", "project")
    package_name = project_config.get("package_name")

    output_path = resolve_path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Extracting Python documentation")
    print("-" * 80)

    if args.config is None:
        print("project_config: default configs/project_config.yaml")
    else:
        print(f"project_config: {resolve_path(args.config)}")

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