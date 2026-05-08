from __future__ import annotations

import subprocess
from pathlib import Path


def build_mmore_index(
    *,
    config_path: str | Path,
    documents_path: str | Path,
    collection_name: str,
    show_logs: bool = False,
) -> None:
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