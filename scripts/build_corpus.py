from __future__ import annotations

from docask.config import load_all_configs
from docask.corpus.builder import build_corpus_from_markdown, save_corpus_jsonl
from docask.utils.paths import PROCESSED_DATA_DIR


def main() -> None:
    configs = load_all_configs()
    docs_path = configs["project"]["docs_path"]

    documents = build_corpus_from_markdown(docs_path)

    output_path = PROCESSED_DATA_DIR / "corpus.jsonl"
    save_corpus_jsonl(documents, output_path)

    print(f"Built corpus with {len(documents)} documents")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()