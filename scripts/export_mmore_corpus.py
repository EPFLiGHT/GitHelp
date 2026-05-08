from __future__ import annotations

from docask.indexing.mmore_format import export_corpus_to_mmore_jsonl
from docask.utils.paths import PROCESSED_DATA_DIR


"""
Export the DocAsk corpus to MMORE-compatible JSONL format.

The DocAsk corpus uses DocumentRecord objects. MMORE expects a JSONL file
containing samples with a text field, metadata, and modalities. This script
converts data/processed/corpus.jsonl into data/processed/mmore_corpus.jsonl.
"""


def main() -> None:
    """Export the processed DocAsk corpus to MMORE format."""
    corpus_path = PROCESSED_DATA_DIR / "corpus.jsonl"
    output_path = PROCESSED_DATA_DIR / "mmore_corpus.jsonl"

    print("Exporting corpus to MMORE format")
    print("-" * 80)
    print(f"corpus_path: {corpus_path}")
    print(f"corpus_exists: {corpus_path.exists()}")
    print(f"output_path: {output_path}")
    print("-" * 80)

    export_corpus_to_mmore_jsonl(
        corpus_path=corpus_path,
        output_path=output_path,
    )

    print(f"output_exists: {output_path.exists()}")
    print(f"Exported MMORE-compatible corpus to: {output_path}")


if __name__ == "__main__":
    main()