from __future__ import annotations

import argparse

from docask.retrieval.simple_retriever import load_corpus, retrieve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-path", default="data/processed/corpus.jsonl")
    args = parser.parse_args()

    documents = load_corpus(args.corpus_path)
    results = retrieve(args.query, documents, top_k=args.top_k)

    print(f"Query: {args.query}")
    print(f"Results: {len(results)}")
    print()

    for i, result in enumerate(results, start=1):
        doc = result.document

        print("=" * 80)
        print(f"#{i} score={result.score:.4f}")
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