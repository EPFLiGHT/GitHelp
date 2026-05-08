from __future__ import annotations

from docask.retrieval.mmore_format import export_corpus_to_mmore_jsonl
from docask.utils.paths import PROCESSED_DATA_DIR


def main() -> None:
    corpus_path = PROCESSED_DATA_DIR / "corpus.jsonl"
    output_path = PROCESSED_DATA_DIR / "mmore_corpus.jsonl"

    print(f"corpus_path = {corpus_path}")
    print(f"corpus_exists = {corpus_path.exists()}")
    print(f"output_path = {output_path}")

    export_corpus_to_mmore_jsonl(
        corpus_path=corpus_path,
        output_path=output_path,
    )

    print(f"output_exists = {output_path.exists()}")
    print(f"Exported MMORE-compatible corpus to: {output_path}")


if __name__ == "__main__":
    main()