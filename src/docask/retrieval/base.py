from __future__ import annotations

from dataclasses import dataclass

from docask.data_models import DocumentRecord


@dataclass
class RetrievalResult:
    """
    Result returned by any DocAsk retrieval backend.

    This class is intentionally backend-agnostic. It can represent a result
    produced by the local simple retriever, by MMORE, or by another retrieval
    system added later.
    """

    document: DocumentRecord
    score: float