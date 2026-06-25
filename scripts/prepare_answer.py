from __future__ import annotations

import argparse

from githelp.rag.answering import prepare_answer_prompt


"""
Prepare a source-grounded prompt for a question.

This script retrieves relevant documents and formats them into the prompt that
would be sent to an LLM. It does not call an LLM.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare an LLM prompt from retrieved GitHelp sources."
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
        help="Path to the GitHelp corpus.",
    )

    parser.add_argument(
        "--backend",
        default="simple",
        choices=["simple", "mmore"],
        help="Retrieval backend to use.",
    )

    parser.add_argument(
        "--config-path",
        default="configs/app_config.yaml",
        help="Path to the app config file.",
    )

    return parser.parse_args()


def main() -> None:
    """Retrieve sources and print the generated LLM prompt."""
    args = parse_args()

    prompt, results = prepare_answer_prompt(
        question=args.question,
        corpus_path=args.corpus_path,
        top_k=args.top_k,
        backend=args.backend,
        config_path=args.config_path,
    )

    print(prompt)
    print()
    print("=" * 80)
    print("Retrieved sources:")

    for index, result in enumerate(results, start=1):
        doc = result.document
        print(
            f"{index}. {doc.source_type} | "
            f"{doc.metadata.get('relative_path')} | "
            f"{doc.title}"
        )


if __name__ == "__main__":
    main()
