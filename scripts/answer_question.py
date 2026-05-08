from __future__ import annotations

import argparse

from docask.rag.answering import answer_question


"""
Answer a question using the current non-LLM extractive answerer.

This script retrieves relevant sources and returns a simple answer from the
top retrieved document. It is mainly useful for testing retrieval before full
LLM generation is connected.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Answer a question using DocAsk's current extractive answerer."
    )
    parser.add_argument("question", help="Question to ask about the indexed project.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    parser.add_argument("--backend", default="simple", choices=["simple", "mmore"])
    return parser.parse_args()


def main() -> None:
    """Retrieve sources and print a simple answer."""
    args = parse_args()

    answer, results = answer_question(
        question=args.question,
        corpus_path=args.corpus_path,
        top_k=args.top_k,
        backend=args.backend,
    )

    print("Answer:")
    print(answer)
    print()
    print("=" * 80)
    print("Sources:")

    for index, result in enumerate(results, start=1):
        doc = result.document
        print(
            f"{index}. {doc.source_type} | "
            f"{doc.metadata.get('relative_path')} | "
            f"{doc.title}"
        )


if __name__ == "__main__":
    main()