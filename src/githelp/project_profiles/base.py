from __future__ import annotations

from abc import ABC
from githelp.retrieval.base import RetrievalResult


class ProjectProfile(ABC):
    """Base class for project-specific retrieval and answering behavior."""

    def expand_query(self, question: str) -> str:
        return question

    def filter_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        return results

    def rerank_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        return results

    def answer_directly(
        self,
        question: str,
        results: list[RetrievalResult],
    ) -> str | None:
        return None
