from __future__ import annotations

import json
from pathlib import Path

# to quickly inspect the corpus
def main() -> None:
    corpus_path = Path("data/processed/corpus.jsonl")
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    with corpus_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            doc = json.loads(line)
            print("=" * 80)
            print(f"doc_id: {doc['doc_id']}")
            print(f"title: {doc.get('title')}")
            print(f"section_title: {doc.get('section_title')}")
            print(f"source_type: {doc.get('source_type')}")
            print(f"relative_path: {doc.get('metadata', {}).get('relative_path')}")
            print()
            print(doc["content"][:500])
            print()

            if i >= 4:
                break


if __name__ == "__main__":
    main()