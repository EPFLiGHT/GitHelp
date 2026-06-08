from __future__ import annotations

import argparse

from githelp.evaluation.retrieval_eval import (
    check_expected_sources,
    evaluate_retrieval_questions,
    load_expected_sources,
    load_eval_questions,
    summarize_expectation_checks,
)


"""
Evaluate retrieval on a small question set.

This script does not call an LLM. It prints the top retrieved sources for each
question so retrieval quality can be inspected before answer generation.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate GitHelp retrieval on a question set."
    )

    parser.add_argument(
        "--questions-path",
        default="githelp_eval_questions.txt",
        help="Plain text file with one question per line.",
    )

    parser.add_argument(
        "--corpus-path",
        default="data/processed/corpus.jsonl",
        help="Path to the GitHelp JSONL corpus.",
    )

    parser.add_argument(
        "--backend",
        default="simple",
        choices=["simple", "mmore"],
        help="Retrieval backend to evaluate.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of sources to retrieve per question.",
    )

    parser.add_argument(
        "--expected-sources-path",
        default=None,
        help=(
            "Optional JSON file mapping questions to expected source criteria. "
            "When provided, the script prints pass/fail checks."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run retrieval evaluation and print compact ranked sources."""
    args = parse_args()

    questions = load_eval_questions(args.questions_path)
    evaluation = evaluate_retrieval_questions(
        questions,
        corpus_path=args.corpus_path,
        backend=args.backend,
        top_k=args.top_k,
    )

    for question, results in evaluation.items():
        print("=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        if not results:
            print("No sources retrieved.")
            print()
            continue

        for result in results:
            print(
                f"{result['rank']}. score={result['score']:.4f} | "
                f"{result['source_type']} | {result['relative_path']} | "
                f"{result['title']}"
            )

        print()

    if args.expected_sources_path is None:
        return

    expected_sources = load_expected_sources(args.expected_sources_path)
    checks = check_expected_sources(evaluation, expected_sources)
    summary = summarize_expectation_checks(checks)

    print("=" * 80)
    print("EXPECTED SOURCE CHECKS")
    print("=" * 80)

    for check in checks:
        status = "PASS" if check["matched"] else "MISS"
        rank = check["matched_rank"] if check["matched_rank"] is not None else "-"
        print(
            f"{status} | rank={rank} | {check['question']} | "
            f"expected={check['expected']}"
        )

    print()
    print(
        f"Summary: {summary['matched']}/{summary['total']} matched "
        f"({summary['accuracy']:.2%}), {summary['missed']} missed"
    )


if __name__ == "__main__":
    main()
