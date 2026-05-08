from __future__ import annotations

import argparse

from docask.rag.prompting import build_user_prompt
from docask.retrieval.simple_retriever import load_corpus, retrieve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    args = parser.parse_args()

    documents = load_corpus(args.corpus_path)
    results = retrieve(args.query, documents, top_k=args.top_k)

    prompt = build_user_prompt(args.query, results)
    print(prompt)


if __name__ == "__main__":
    main()