from __future__ import annotations

import argparse
from pathlib import Path

from githelp.indexing.mmore_format import export_corpus_to_mmore_jsonl
from githelp.utils.paths import PROJECT_ROOT, PROCESSED_DATA_DIR


"""
Export the GitHelp corpus to MMORE-compatible JSONL format.

The GitHelp corpus uses DocumentRecord objects. MMORE expects a JSONL file
containing samples with a text field, metadata, and modalities.

By default, it keeps the original behavior:
    data/processed/corpus.jsonl -> data/processed/mmore_corpus.jsonl

It can also be used dynamically:
    python scripts/export_mmore_corpus.py \
        --corpus-path data/projects/mmore/corpus.jsonl \
        --output-path data/projects/mmore/mmore_corpus.jsonl
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export a GitHelp corpus to MMORE-compatible JSONL format."
    )

    parser.add_argument(
        "--corpus-path",
        type=Path,
        default=PROCESSED_DATA_DIR / "corpus.jsonl",
        help="Path to the GitHelp corpus JSONL file.",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=PROCESSED_DATA_DIR / "mmore_corpus.jsonl",
        help="Path where the MMORE-compatible JSONL file should be written.",
    )

    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    """
    Resolve a path relative to the GitHelp project root if it is not absolute.
    """
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> None:
    """Export the processed GitHelp corpus to MMORE format."""
    args = parse_args()

    corpus_path = resolve_path(args.corpus_path)
    output_path = resolve_path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Exporting corpus to MMORE format")
    print("-" * 80)
    print(f"corpus_path: {corpus_path}")
    print(f"corpus_exists: {corpus_path.exists()}")
    print(f"output_path: {output_path}")
    print("-" * 80)

    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    export_corpus_to_mmore_jsonl(
        corpus_path=corpus_path,
        output_path=output_path,
    )

    print(f"output_exists: {output_path.exists()}")
    print(f"Exported MMORE-compatible corpus to: {output_path}")


if __name__ == "__main__":
    main()