from __future__ import annotations

import argparse
import json
from pathlib import Path

from githelp.retrieval.mmore_native import retrieve_with_mmore_native
from githelp.retrieval.mmore_subprocess import (
    MMORE_WORKER_RESULT_PREFIX,
    serialize_results,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for one native MMORE retrieval call."""
    parser = argparse.ArgumentParser(
        description="Run native MMORE retrieval in an isolated process."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--config-path", type=Path, required=True)
    parser.add_argument("--index-config-path", type=Path, required=True)
    parser.add_argument("--collection-name", default="mmore_docs")
    parser.add_argument("--search-type", default="hybrid")
    return parser.parse_args()


def main() -> None:
    """Run native MMORE retrieval and print serialized results."""
    args = parse_args()
    results = retrieve_with_mmore_native(
        query=args.query,
        top_k=args.top_k,
        config_path=args.config_path,
        index_config_path=args.index_config_path,
        collection_name=args.collection_name,
        search_type=args.search_type,
    )
    payload = json.dumps(serialize_results(results), ensure_ascii=False)
    print(f"{MMORE_WORKER_RESULT_PREFIX}{payload}")


if __name__ == "__main__":
    main()
