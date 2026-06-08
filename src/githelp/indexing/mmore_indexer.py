from __future__ import annotations

import subprocess
from pathlib import Path


"""
Wrapper around the MMORE indexing command.

This module keeps the command-line call to MMORE in one place. GitHelp can call
this function to build an MMORE index from a JSONL file without duplicating
subprocess logic in scripts or application code.
"""


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

    stdout = None if show_logs else subprocess.DEVNULL
    stderr = None if show_logs else subprocess.DEVNULL

    subprocess.run(
        [
            "python",
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