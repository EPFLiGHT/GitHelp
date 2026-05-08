from __future__ import annotations

import json

from docask.config import load_all_configs
from docask.extractors.python_doc_extractor import extract_python_docs
from docask.utils.paths import EXTRACTED_CODE_DOCS_DIR


"""
Extract Python code documentation into a standalone JSONL file.

This script is mainly useful for debugging the Python documentation extractor
independently from the full corpus-building pipeline.
"""


def main() -> None:
    """Extract Python docstrings and signatures from the configured code path."""
    configs = load_all_configs()
    project_config = configs["project"]

    code_path = project_config["code_path"]
    project_name = project_config.get("project_name", "project")
    package_name = project_config.get("package_name")

    documents = extract_python_docs(
        code_path,
        package_name=package_name,
        project_name=project_name,
    )

    output_path = EXTRACTED_CODE_DOCS_DIR / "code_docs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for doc in documents:
            file.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")

    print(f"Extracted {len(documents)} code documents")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()