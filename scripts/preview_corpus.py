from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


"""
Preview records from the GitHelp corpus.

This script is useful for quickly inspecting the JSONL corpus and checking
whether Markdown sections, code docstrings, YAML configs, or repository
structure documents were extracted correctly.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Preview documents from the GitHelp JSONL corpus."
    )
    parser.add_argument(
        "--source-type",
        default=None,
        help="Optional source_type filter, for example markdown_section or python_function.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of documents to display.",
    )
    parser.add_argument(
        "--corpus-path",
        default="data/processed/corpus.jsonl",
        help="Path to the GitHelp corpus JSONL file.",
    )
    return parser.parse_args()


def print_document_preview(doc: dict[str, Any]) -> None:
    """Print a readable preview of one corpus document."""
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


def main() -> None:
    """Preview selected records from the corpus."""
    args = parse_args()

    corpus_path = Path(args.corpus_path)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    shown = 0

    with corpus_path.open("r", encoding="utf-8") as file:
        for line in file:
            doc = json.loads(line)

            if args.source_type and doc.get("source_type") != args.source_type:
                continue

            print_document_preview(doc)

            shown += 1
            if shown >= args.limit:
                break


if __name__ == "__main__":
    main()