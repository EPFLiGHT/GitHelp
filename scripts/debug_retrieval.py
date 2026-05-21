from __future__ import annotations

import argparse

from docask.retrieval.simple_retriever import load_corpus, retrieve


"""
Debug the local simple retriever directly.

This script bypasses project profiles, query expansion, filtering, reranking,
and MMORE retrieval. It is useful for inspecting the raw simple retriever.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Debug DocAsk simple retrieval."
    )
    parser.add_argument("query", help="Query used to retrieve documents.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    return parser.parse_args()


def main() -> None:
    """Run simple retrieval and print detailed ranked results."""
    args = parse_args()

    documents = load_corpus(args.corpus_path)
    results = retrieve(args.query, documents, top_k=args.top_k)

    print(f"Query: {args.query}")
    print(f"Results: {len(results)}")
    print()

    for index, result in enumerate(results, start=1):
        doc = result.document

        print("=" * 80)
        print(f"#{index} score={result.score:.4f}")
        print(f"doc_id: {doc.doc_id}")
        print(f"title: {doc.title}")
        print(f"source_type: {doc.source_type}")
        print(f"relative_path: {doc.metadata.get('relative_path')}")
        print(f"section_title: {doc.section_title}")
        print(f"module_name: {doc.module_name}")
        print(f"symbol_name: {doc.symbol_name}")
        print(f"signature: {doc.signature}")
        print()
        print(doc.content[:800])
        print()


if __name__ == "__main__":
    main()