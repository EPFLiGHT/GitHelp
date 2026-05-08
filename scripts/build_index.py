from __future__ import annotations

from docask.config import load_all_configs
from docask.indexing.mmore_indexer import build_mmore_index
from docask.utils.paths import PROCESSED_DATA_DIR


def main() -> None:
    configs = load_all_configs()
    indexing_config = configs["indexing"]

    config_path = indexing_config["mmore_index_config_path"]
    collection_name = indexing_config.get("collection_name", "docask_docs")

    # For now this may need to become mmore_corpus.jsonl after conversion.
    documents_path = PROCESSED_DATA_DIR / "mmore_corpus.jsonl"

    print("Building MMORE index")
    print(f"config_path = {config_path}")
    print(f"documents_path = {documents_path}")
    print(f"collection_name = {collection_name}")

    build_mmore_index(
        config_path=config_path,
        documents_path=documents_path,
        collection_name=collection_name,
        show_logs=True,
    )

    print("MMORE index built successfully")


if __name__ == "__main__":
    main()