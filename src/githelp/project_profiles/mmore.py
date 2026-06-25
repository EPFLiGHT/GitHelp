from __future__ import annotations

from githelp.project_profiles.generic import GenericProjectProfile
from githelp.retrieval.base import RetrievalResult


class MMoreProjectProfile(GenericProjectProfile):
    """Project-specific profile for MMORE documentation."""

    def expand_query(self, question: str) -> str:
        normalized_question = question.lower()

        if "colpali" in normalized_question and "milvus" in normalized_question:
            return (
                question
                + " colpali examples/colpali/config_index.yml config_index.yml "
                + "milvus db_path collection_name create_collection dim metric_type "
                + "parquet_path yaml configuration"
            )

        if "colpali" in normalized_question:
            return (
                question
                + " colpali examples/colpali/config_index.yml config_index.yml "
                + "parquet_path milvus db_path collection_name create_collection "
                + "dim metric_type yaml configuration"
            )

        if "index" in normalized_question or "indexing" in normalized_question:
            if self._is_code_or_symbol_question(question):
                return (
                    question
                    + " cli.py python function method class signature "
                    + "mmore.cli index command run indexer"
                )

            return (
                question
                + " indexing index configuration config config file indexer "
                + "dense_model sparse_model db collection_name documents_path"
            )

        return question

    def filter_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        results = super().filter_results(results, question)

        filtered: list[RetrievalResult] = []
        normalized_question = question.lower()

        question_mentions_colpali = "colpali" in normalized_question
        question_mentions_websearch = (
            "websearch" in normalized_question or "web search" in normalized_question
        )

        for result in results:
            doc = result.document

            title = (doc.title or "").lower()
            section_title = (doc.section_title or "").lower()
            relative_path = (
                doc.metadata.get("relative_path") or doc.file_path or ""
            ).lower()

            is_colpali_source = (
                "colpali" in relative_path
                or "colpali" in title
                or "colpali" in section_title
            )

            is_websearch_source = (
                "websearch" in relative_path
                or "websearch" in title
                or "websearch" in section_title
            )

            if is_colpali_source and not question_mentions_colpali:
                continue

            if is_websearch_source and not question_mentions_websearch:
                continue

            filtered.append(result)

        return filtered

    def rerank_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        """
        Apply generic code-aware reranking, then add MMORE-specific config
        boosts for Milvus, ColPali, and indexing configuration questions.
        """
        results = super().rerank_results(results, question)

        normalized_question = question.lower()

        asks_about_config_parameters = any(
            term in normalized_question
            for term in [
                "parameters",
                "config",
                "configuration",
                "fields",
                "contain",
            ]
        )

        if not asks_about_config_parameters:
            return results

        def bonus(result: RetrievalResult) -> int:
            doc = result.document

            title = (doc.title or "").lower()
            content = (doc.content or "").lower()
            relative_path = (
                doc.metadata.get("relative_path") or doc.file_path or ""
            ).lower()
            source_type = (doc.source_type or "").lower()

            score = 0

            if "config" in relative_path or "config" in title:
                score += 4

            if source_type in {"example_config", "production_config", "yaml_config"}:
                score += 4

            if "colpali" in normalized_question and "colpali" in relative_path:
                score += 6

            if "milvus" in normalized_question and "milvus" in content:
                score += 6

            for key in [
                "db_path",
                "collection_name",
                "create_collection",
                "dim",
                "metric_type",
                "milvus:",
            ]:
                if key in content:
                    score += 2

            return score

        return sorted(
            results,
            key=lambda result: (bonus(result), result.score),
            reverse=True,
        )

    def answer_directly(
        self,
        question: str,
        results: list[RetrievalResult],
    ) -> str | None:
        """
        Answer some MMORE-specific structured questions without calling the LLM.

        This avoids hallucinations for questions that ask for exact configuration
        parameters, where deterministic extraction is more reliable than generation.
        """
        if self._is_milvus_parameter_question(question):
            return self._answer_milvus_parameter_question(results)

        return None

    def _is_milvus_parameter_question(self, question: str) -> bool:
        """Detect questions asking for Milvus configuration parameters."""
        normalized_question = question.lower()

        mentions_milvus = "milvus" in normalized_question

        asks_for_parameters = any(
            term in normalized_question
            for term in [
                "parameter",
                "parameters",
                "field",
                "fields",
                "key",
                "keys",
            ]
        )

        return mentions_milvus and asks_for_parameters

    def _answer_milvus_parameter_question(
        self,
        results: list[RetrievalResult],
    ) -> str:
        """
        Return a deterministic answer for known Milvus configuration parameters.
        """
        allowed_keys = [
            "db_path",
            "collection_name",
            "create_collection",
            "dim",
            "metric_type",
        ]

        found: list[tuple[str, int]] = []
        seen_keys: set[str] = set()

        for source_index, result in enumerate(results, start=1):
            content = result.document.content or ""

            if "milvus" not in content.lower():
                continue

            for key in allowed_keys:
                if key in content and key not in seen_keys:
                    found.append((key, source_index))
                    seen_keys.add(key)

        if not found:
            return (
                "The retrieved sources mention Milvus, but they do not provide enough "
                "information to identify explicit Milvus parameters."
            )

        lines = []

        for key, source_index in found:
            lines.append(
                f"- `{key}` is used as a Milvus configuration parameter. "
                f"[Source {source_index}]"
            )

        return "\n".join(lines)
