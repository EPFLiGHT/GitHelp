from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml


"""
Wrapper around the MMORE indexing command.

This module keeps the command-line call to MMORE in one place. GitHelp can call
this function to build an MMORE index from a JSONL file without duplicating
subprocess logic in scripts or application code.
"""


def _is_local_milvus_uri(uri: str) -> bool:
    """Return True when a Milvus URI refers to a local file path."""
    parsed_uri = urlparse(uri)
    return parsed_uri.scheme in {"", "file"}


def _ensure_local_milvus_parent_dir(config_path: Path) -> None:
    """
    Create the parent directory for local Milvus Lite database paths.

    MMORE delegates this to pymilvus, which expects the directory to exist.
    """
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    indexer_config = config.get("indexer", {})

    if not isinstance(indexer_config, dict):
        return

    db_config = indexer_config.get("db", {})

    if not isinstance(db_config, dict):
        return

    uri = db_config.get("uri")

    if not uri:
        return

    uri = str(uri)

    if not _is_local_milvus_uri(uri):
        return

    db_path = Path(uri)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _get_local_milvus_db_path(config_path: Path) -> Path | None:
    """Return the local Milvus database path from an index config, if any."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    indexer_config = config.get("indexer", {})

    if not isinstance(indexer_config, dict):
        return None

    db_config = indexer_config.get("db", {})

    if not isinstance(db_config, dict):
        return None

    uri = db_config.get("uri")

    if not uri:
        return None

    uri = str(uri)

    if not _is_local_milvus_uri(uri):
        return None

    return Path(uri)


def _reset_local_milvus_db(config_path: Path) -> None:
    """
    Remove a generated local Milvus database before rebuilding an index.

    Previous failed MMORE runs can leave a collection with incomplete metadata,
    which later causes retrieval errors such as missing model_name fields.
    """
    db_path = _get_local_milvus_db_path(config_path)

    if db_path is None or not db_path.exists():
        return

    if db_path.is_dir():
        shutil.rmtree(db_path)
        return

    db_path.unlink()


def _has_sparse_model(config_path: Path) -> bool:
    """Return True when the MMORE index config enables a sparse model."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    indexer_config = config.get("indexer", {})

    if not isinstance(indexer_config, dict):
        return False

    return bool(indexer_config.get("sparse_model"))


def _parse_major_version(version: str) -> int | None:
    """Parse the major part of a Python package version."""
    major = version.split(".", maxsplit=1)[0]

    if not major.isdigit():
        return None

    return int(major)


def _check_sparse_model_dependencies(config_path: Path) -> None:
    """
    Fail early for known incompatible sparse-model dependency versions.

    MMORE's SPLADE sparse model path currently uses pymilvus code that calls
    tokenizer.batch_encode_plus, which is not available in Transformers 5.
    """
    if not _has_sparse_model(config_path):
        return

    try:
        transformers_version = importlib.metadata.version("transformers")
    except importlib.metadata.PackageNotFoundError:
        return

    major_version = _parse_major_version(transformers_version)

    if major_version is not None and major_version >= 5:
        raise RuntimeError(
            "MMORE sparse indexing is incompatible with Transformers "
            f"{transformers_version}. Install a Transformers 4.x version, for "
            "example: python -m pip install 'transformers>=4.51.0,<5'."
        )


def build_mmore_index(
    *,
    config_path: str | Path,
    documents_path: str | Path,
    collection_name: str,
    show_logs: bool = False,
) -> None:
    """
    Build an MMORE index from a JSONL document file.

    Parameters
    ----------
    config_path:
        Path to the MMORE indexing configuration file.
    documents_path:
        Path to the MMORE-compatible JSONL documents file.
    collection_name:
        Name of the target MMORE/Milvus collection.
    show_logs:
        Whether to show MMORE command output in the terminal.

    Raises
    ------
    FileNotFoundError
        If the config file or documents file does not exist.
    subprocess.CalledProcessError
        If the MMORE indexing command fails.
    """
    config_path = Path(config_path)
    documents_path = Path(documents_path)

    if not config_path.exists():
        raise FileNotFoundError(f"MMORE config file not found: {config_path}")

    if not documents_path.exists():
        raise FileNotFoundError(f"Documents JSONL file not found: {documents_path}")

    _check_sparse_model_dependencies(config_path)
    _reset_local_milvus_db(config_path)
    _ensure_local_milvus_parent_dir(config_path)

    stdout = None if show_logs else subprocess.DEVNULL
    stderr = None if show_logs else subprocess.DEVNULL

    subprocess.run(
        [
            sys.executable,
            "-m",
            "mmore",
            "index",
            "--config-file",
            str(config_path),
            "--documents-path",
            str(documents_path),
            "--collection-name",
            collection_name,
        ],
        check=True,
        stdout=stdout,
        stderr=stderr,
    )
