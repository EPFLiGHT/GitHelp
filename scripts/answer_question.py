from __future__ import annotations

import argparse

from docask.rag.answering import answer_question


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    args = parser.parse_args()

    answer, results = answer_question(
        question=args.question,
        corpus_path=args.corpus_path,
        top_k=args.top_k,
    )

    print("Answer:")
    print(answer)
    print()
    print("=" * 80)
    print("Sources:")
    for i, result in enumerate(results, start=1):
        doc = result.document
        print(f"{i}. {doc.source_type} | {doc.metadata.get('relative_path')} | {doc.title}")


if __name__ == "__main__":
    main()