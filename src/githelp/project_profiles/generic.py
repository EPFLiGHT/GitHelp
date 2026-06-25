from __future__ import annotations

import re

from githelp.project_profiles.base import ProjectProfile
from githelp.retrieval.base import RetrievalResult


class GenericProjectProfile(ProjectProfile):
    """Default project profile used for project-agnostic behavior."""

    PYTHON_SOURCE_TYPES = {
        "python_module",
        "python_class",
        "python_function",
        "python_method",
    }

    CONFIG_SOURCE_TYPES = {
        "example_config",
        "production_config",
        "yaml_config",
    }

    def expand_query(self, question: str) -> str:
        """Return the query used for retrieval."""
        return question

    def filter_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        """
        Apply generic filtering.

        This removes low-value documents while keeping project-specific logic
        outside the generic profile.
        """
        filtered: list[RetrievalResult] = []

        for result in results:
            content = (result.document.content or "").strip()

            if not content:
                continue

            # Avoid tiny fragments that are usually not useful as evidence.
            if len(content) < 40:
                continue

            filtered.append(result)

        return filtered

    def rerank_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        """
        Apply generic reranking rules.

        These rules are project-agnostic and help GitHelp use Python docstrings
        when the user asks about functions, classes, methods, signatures, CLI
        commands, or implementation details.
        """
        normalized_question = question.lower()

        is_code_question = self._is_code_or_symbol_question(question)
        is_config_question = self._is_config_question(question)

        def score_result(result: RetrievalResult) -> tuple[float, float]:
            doc = result.document

            score = float(result.score or 0.0)
            bonus = 0.0

            source_type = doc.source_type or ""
            relative_path = (
                doc.metadata.get("relative_path") or doc.file_path or ""
            ).lower()

            title = (doc.title or "").lower()
            section_title = (doc.section_title or "").lower()
            module_name = (doc.module_name or "").lower()
            symbol_name = (doc.symbol_name or "").lower()
            signature = (doc.signature or "").lower()
            content = (doc.content or "").lower()

            searchable_text = " ".join(
                [
                    relative_path,
                    title,
                    section_title,
                    module_name,
                    symbol_name,
                    signature,
                    content[:1500],
                ]
            )

            if is_code_question:
                if source_type in self.PYTHON_SOURCE_TYPES:
                    bonus += 6.0

                if source_type == "python_function":
                    bonus += 2.0

                if source_type == "python_class":
                    bonus += 1.5

                if source_type == "python_method":
                    bonus += 1.5

                if "signature" in normalized_question and doc.signature:
                    bonus += 4.0

                if "cli" in normalized_question or "command" in normalized_question:
                    if "cli.py" in relative_path:
                        bonus += 5.0

                    if "cli" in relative_path:
                        bonus += 2.0

                    if "cli" in module_name:
                        bonus += 2.0

                # Boost exact symbol mentions.
                if symbol_name and self._contains_exact_identifier(
                    normalized_question,
                    symbol_name,
                ):
                    bonus += 5.0

                if doc.title and doc.title.lower() in normalized_question:
                    bonus += 4.0

                if doc.module_name and doc.module_name.lower() in normalized_question:
                    bonus += 3.0

                if doc.signature and doc.signature.lower() in normalized_question:
                    bonus += 4.0

                # Match function/class names written as natural words.
                question_tokens = set(normalized_question.replace("_", " ").split())
                symbol_tokens = set(symbol_name.replace("_", " ").split())

                if symbol_tokens and symbol_tokens <= question_tokens:
                    bonus += 3.0

                # If the question is about code and not config, avoid YAML domination.
                if source_type in self.CONFIG_SOURCE_TYPES and not is_config_question:
                    bonus -= 6.0

            if is_config_question:
                if source_type in self.CONFIG_SOURCE_TYPES:
                    bonus += 3.0

                if "config" in relative_path or "config" in title:
                    bonus += 1.5

            # Small generic semantic boost.
            for term in [
                "implementation",
                "implemented",
                "function",
                "class",
                "method",
            ]:
                if term in normalized_question and term in searchable_text:
                    bonus += 0.5

            return score + bonus, score

        reranked = sorted(results, key=score_result, reverse=True)

        if is_code_question and not is_config_question:
            reranked = self._limit_config_results(
                results=reranked,
                max_config_results=1,
            )

        return reranked

    def answer_directly(
        self,
        question: str,
        results: list[RetrievalResult],
    ) -> str | None:
        """Return a deterministic answer when possible."""
        return None

    def _is_code_or_symbol_question(self, question: str) -> bool:
        """Detect questions about code symbols or implementation."""
        normalized_question = question.lower()

        code_terms = [
            "function",
            "class",
            "method",
            "signature",
            "symbol",
            "cli",
            "command",
            "implemented",
            "implementation",
            "where is",
            "where are",
            "what does",
            "what do",
            "code",
            "module",
        ]

        return any(term in normalized_question for term in code_terms)

    def _is_config_question(self, question: str) -> bool:
        """Detect questions about configuration files or parameters."""
        normalized_question = question.lower()

        config_terms = [
            "config",
            "configure",
            "configuration",
            "parameter",
            "parameters",
            "yaml",
            "yml",
            "setting",
            "settings",
            "field",
            "fields",
        ]

        return any(term in normalized_question for term in config_terms)

    def _contains_exact_identifier(self, text: str, identifier: str) -> bool:
        """Match identifiers without treating them as arbitrary substrings."""
        if not identifier:
            return False

        pattern = rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])"
        return re.search(pattern, text) is not None

    def _limit_config_results(
        self,
        results: list[RetrievalResult],
        max_config_results: int = 1,
    ) -> list[RetrievalResult]:
        """
        Limit YAML config dominance for non-config code questions.
        """
        kept_results: list[RetrievalResult] = []
        delayed_config_results: list[RetrievalResult] = []
        config_count = 0

        for result in results:
            source_type = result.document.source_type or ""

            if source_type in self.CONFIG_SOURCE_TYPES:
                if config_count < max_config_results:
                    kept_results.append(result)
                    config_count += 1
                else:
                    delayed_config_results.append(result)
            else:
                kept_results.append(result)

        return kept_results + delayed_config_results
