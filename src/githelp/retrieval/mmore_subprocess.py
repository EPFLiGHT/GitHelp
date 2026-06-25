from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult
from githelp.retrieval.mmore_errors import MMoreRetrievalError
from githelp.utils.paths import PROJECT_ROOT


MMORE_WORKER_RESULT_PREFIX = "GITHELP_MMORE_RESULTS="


def serialize_results(results: list[RetrievalResult]) -> list[dict[str, Any]]:
    """Serialize retrieval results for the MMORE subprocess worker."""
    return [
        {
            "score": result.score,
            "document": result.document.model_dump(),
        }
        for result in results
    ]


def deserialize_results(payload: list[dict[str, Any]]) -> list[RetrievalResult]:
    """Deserialize retrieval results produced by the MMORE subprocess worker."""
    return [
        RetrievalResult(
            document=DocumentRecord(**item["document"]),
            score=float(item["score"]),
        )
        for item in payload
    ]


def retrieve_with_mmore_subprocess(
    query: str,
    top_k: int,
    config_path: str | Path,
    index_config_path: str | Path,
    collection_name: str,
    search_type: str,
) -> list[RetrievalResult]:
    """
    Run native MMORE retrieval in a child process.

    MMORE/Milvus can segfault in some local environments. Running it outside
    Streamlit keeps the UI process alive and lets GitHelp fall back to the
    exported MMORE corpus.
    """
    command = [
        sys.executable,
        "-m",
        "githelp.retrieval.mmore_worker",
        "--query",
        query,
        "--top-k",
        str(top_k),
        "--config-path",
        str(config_path),
        "--index-config-path",
        str(index_config_path),
        "--collection-name",
        collection_name,
        "--search-type",
        search_type,
    ]

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise MMoreRetrievalError(
            "Native MMORE retrieval failed in a subprocess. "
            f"Return code: {completed.returncode}. "
            f"stderr: {completed.stderr.strip()}"
        )

    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(MMORE_WORKER_RESULT_PREFIX):
            payload = json.loads(line[len(MMORE_WORKER_RESULT_PREFIX) :])
            return deserialize_results(payload)

    raise MMoreRetrievalError("Native MMORE worker did not return retrieval results.")
