from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from docask.data_models import DocumentRecord
from docask.retrieval.simple_retriever import RetrievalResult


def retrieve_with_mmore(
    query: str,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents using MMORE.

    This function is the internal MMORE adapter.
    The rest of DocAsk should not depend directly on MMORE.
    """
    raise NotImplementedError("MMORE retrieval integration not implemented yet.")