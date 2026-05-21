from __future__ import annotations

import argparse

from docask.rag.answering import answer_question, answer_question_with_llm


"""
Answer a question using DocAsk.

By default, this script uses the current non-LLM extractive answerer.
With --llm, it retrieves relevant sources, builds a grounded prompt, and sends
it to the configured LLM provider.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Answer a question using DocAsk."
    )

    parser.add_argument(
        "question",
        help="Question to ask about the indexed project.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of retrieved sources.",
    )

    parser.add_argument(
        "--corpus-path",
        default="data/processed/corpus.jsonl",
        help="Path to the DocAsk corpus.",
    )

    parser.add_argument(
        "--backend",
        default="mmore",
        choices=["simple", "mmore"],
        help="Retrieval backend to use.",
    )

    parser.add_argument(
        "--config-path",
        default="configs/app_config.yaml",
        help="Path to the app config file.",
    )

    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use the configured LLM provider instead of the extractive answerer.",
    )

    return parser.parse_args()


def main() -> None:
    """Retrieve sources and print an answer."""
    args = parse_args()

    if args.llm:
        answer, results = answer_question_with_llm(
            question=args.question,
            corpus_path=args.corpus_path,
            top_k=args.top_k,
            backend=args.backend,
            config_path=args.config_path,
        )
    else:
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