from __future__ import annotations

import argparse

from docask.retrieval.answering import prepare_answer_prompt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    args = parser.parse_args()

    prompt, results = prepare_answer_prompt(
        question=args.question,
        corpus_path=args.corpus_path,
        top_k=args.top_k,
    )

    print(prompt)
    print()
    print("=" * 80)
    print("Retrieved sources:")
    for i, result in enumerate(results, start=1):
        doc = result.document
        print(f"{i}. {doc.source_type} | {doc.metadata.get('relative_path')} | {doc.title}")


if __name__ == "__main__":
    main()