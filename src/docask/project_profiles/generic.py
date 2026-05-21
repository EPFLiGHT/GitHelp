from __future__ import annotations

from docask.project_profiles.base import ProjectProfile
from docask.retrieval.base import RetrievalResult


class GenericProjectProfile(ProjectProfile):
    """Default project profile with minimal assumptions."""

    def filter_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        filtered: list[RetrievalResult] = []

        for result in results:
            doc = result.document
            title = (doc.title or "").lower()
            section_title = (doc.section_title or "").lower()
            content = (doc.content or "").strip()

            is_see_also = "see also" in title or "see also" in section_title
            is_too_short = len(content) < 40

            if is_see_also or is_too_short:
                continue

            filtered.append(result)

        return filtered