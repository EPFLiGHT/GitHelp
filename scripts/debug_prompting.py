from __future__ import annotations

import argparse

from docask.rag.answering import prepare_answer_prompt


"""
Debug prompt construction through the normal DocAsk answering pipeline.

This script retrieves sources, applies the selected project profile, builds the
LLM prompt, and prints it without calling an LLM.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Debug DocAsk prompt construction."
    )

    parser.add_argument(
        "question",
        help="Question used to retrieve sources and build the prompt.",
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
    """Retrieve sources and print the corresponding prompt."""
    args = parse_args()

    prompt, _ = prepare_answer_prompt(
        question=args.question,
        corpus_path=args.corpus_path,
        top_k=args.top_k,
        backend=args.backend,
        config_path=args.config_path,
    )

    print(prompt)


if __name__ == "__main__":
    main()