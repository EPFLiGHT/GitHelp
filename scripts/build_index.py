from __future__ import annotations

import argparse
from pathlib import Path

from githelp.config import load_all_configs
from githelp.indexing.mmore_indexer import build_mmore_index
from githelp.utils.paths import PROJECT_ROOT, PROCESSED_DATA_DIR


"""
Build an MMORE index from the GitHelp MMORE-compatible corpus.

By default, it keeps the original behavior:
    data/processed/mmore_corpus.jsonl

It can also be used dynamically:
    python scripts/build_index.py \
        --documents-path data/projects/mmore/mmore_corpus.jsonl \
        --collection-name mmore_docs
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build an MMORE index from a GitHelp MMORE-compatible corpus."
    )

    parser.add_argument(
        "--documents-path",
        type=Path,
        default=PROCESSED_DATA_DIR / "mmore_corpus.jsonl",
        help="Path to the MMORE-compatible corpus JSONL file.",
    )

    parser.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help=(
            "Path to the MMORE index config file. "
            "If omitted, the value from configs/indexing_config.yaml is used."
        ),
    )

    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help=(
            "Name of the MMORE/Milvus collection. "
            "If omitted, the value from configs/indexing_config.yaml is used."
        ),
    )

    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    """
    Resolve a path relative to the GitHelp project root if it is not absolute.
    """
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> None:
    """Build the configured MMORE index."""
    args = parse_args()

    configs = load_all_configs()
    indexing_config = configs["indexing"]

    config_path = args.config_path or Path(indexing_config["mmore_index_config_path"])
    config_path = resolve_path(config_path)

    collection_name = (
        args.collection_name
        or indexing_config.get("collection_name", "githelp_docs")
    )

    documents_path = resolve_path(args.documents_path)

    print("Building MMORE index")
    print("-" * 80)
    print(f"config_path: {config_path}")
    print(f"documents_path: {documents_path}")
    print(f"documents_exists: {documents_path.exists()}")
    print(f"collection_name: {collection_name}")
    print("-" * 80)

    if not documents_path.exists():
        raise FileNotFoundError(f"MMORE corpus file not found: {documents_path}")

    build_mmore_index(
        config_path=config_path,
        documents_path=documents_path,
        collection_name=collection_name,
        show_logs=True,
    )

    print("MMORE index built successfully")


if __name__ == "__main__":
    main()