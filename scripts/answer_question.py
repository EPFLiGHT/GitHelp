from __future__ import annotations

import argparse
from pathlib import Path

from githelp.rag.answering import answer_question, answer_question_with_llm


"""
Answer a question using GitHelp.

By default, this script uses the current non-LLM extractive answerer.
With --llm, it retrieves relevant sources, builds a grounded prompt, and sends
it to the configured LLM provider.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Answer a question using GitHelp.")

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
        "--project-name",
        default="mmore",
        help="Name of the indexed project.",
    )

    parser.add_argument(
        "--corpus-path",
        default=None,
        help="Path to the GitHelp corpus. If omitted, uses data/projects/{project_name}/corpus.jsonl.",
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
    project_name = args.project_name

    corpus_path = (
        Path(args.corpus_path)
        if args.corpus_path is not None
        else Path("data") / "projects" / project_name / "corpus.jsonl"
    )

    if args.llm:
        answer, results = answer_question_with_llm(
            question=args.question,
            corpus_path=corpus_path,
            top_k=args.top_k,
            backend=args.backend,
            config_path=args.config_path,
        )
    else:
        answer, results = answer_question(
            question=args.question,
            corpus_path=corpus_path,
            top_k=args.top_k,
            backend=args.backend,
            config_path=args.config_path,
        )

    print("Answer:")
    print(answer)
    print()
    print("=" * 80)
    print("Sources:")

    for index, result in enumerate(results, start=1):
        doc = result.document
        print(
            f"{index}. score={result.score:.4f} | "
            f"{doc.source_type} | "
            f"{doc.metadata.get('relative_path')} | "
            f"{doc.title}"
        )


if __name__ == "__main__":
    main()
