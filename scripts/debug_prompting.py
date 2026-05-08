from __future__ import annotations

import argparse

from docask.rag.prompting import build_user_prompt
from docask.retrieval.simple_retriever import load_corpus, retrieve


"""
Debug prompt construction with the local simple retriever.

This script retrieves sources with the simple backend and prints the prompt
that would be sent to an LLM.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Debug DocAsk prompt construction."
    )
    parser.add_argument("query", help="Query used to retrieve sources.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    return parser.parse_args()


def main() -> None:
    """Retrieve sources and print the corresponding prompt."""
    args = parse_args()

    documents = load_corpus(args.corpus_path)
    results = retrieve(args.query, documents, top_k=args.top_k)

    prompt = build_user_prompt(args.query, results)

    print(prompt)


if __name__ == "__main__":
    main()