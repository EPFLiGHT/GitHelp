from __future__ import annotations

from docask.config import load_all_configs
from docask.corpus.builder import (
    build_corpus_from_markdown,
    save_corpus_jsonl,
    summarize_corpus,
)
from docask.utils.paths import PROCESSED_DATA_DIR


def main() -> None:
    configs = load_all_configs()
    docs_path = configs["project"]["docs_path"]

    documents = build_corpus_from_markdown(docs_path)

    output_path = PROCESSED_DATA_DIR / "corpus.jsonl"
    save_corpus_jsonl(documents, output_path)

    summary = summarize_corpus(documents)

    print(f"Built corpus with {len(documents)} documents")
    print(f"Saved to: {output_path}")
    print("Breakdown by source_type:")
    for source_type, count in summary.items():
        print(f"  - {source_type}: {count}")


if __name__ == "__main__":
    main()