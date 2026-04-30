from __future__ import annotations

import json

from docask.config import load_all_configs
from docask.extractors.python_doc_extractor import extract_python_docs
from docask.utils.paths import EXTRACTED_CODE_DOCS_DIR


def main() -> None:
    configs = load_all_configs()
    code_path = configs["project"]["code_path"]

    documents = extract_python_docs(code_path)

    output_path = EXTRACTED_CODE_DOCS_DIR / "code_docs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc.model_dump(), ensure_ascii=False) + "\n")

    print(f"Extracted {len(documents)} code documents")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()