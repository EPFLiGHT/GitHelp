from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    corpus_path = Path("data/processed/corpus.jsonl")
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    shown = 0

    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)

            if args.source_type and doc.get("source_type") != args.source_type:
                continue

            print("=" * 80)
            print(f"doc_id: {doc['doc_id']}")
            print(f"title: {doc.get('title')}")
            print(f"section_title: {doc.get('section_title')}")
            print(f"source_type: {doc.get('source_type')}")
            print(f"relative_path: {doc.get('metadata', {}).get('relative_path')}")
            print(f"module_name: {doc.get('module_name')}")
            print(f"symbol_name: {doc.get('symbol_name')}")
            print(f"signature: {doc.get('signature')}")
            print()
            print(doc["content"][:1000])
            print()

            shown += 1
            if shown >= args.limit:
                break


if __name__ == "__main__":
    main()