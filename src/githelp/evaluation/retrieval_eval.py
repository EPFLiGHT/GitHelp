from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from githelp.retrieval.retriever_factory import retrieve_documents


class RetrievalEvaluationResult(TypedDict):
    """Compact retrieval result for one evaluation question."""

    question: str
    rank: int
    score: float
    doc_id: str
    source_type: str
    relative_path: str
    title: str


class ExpectedSource(TypedDict, total=False):
    """Expected source match criteria for one evaluation question."""

    doc_id: str
    source_type: str
    relative_path: str
    title: str


class RetrievalExpectationCheck(TypedDict):
    """Pass/fail result for expected source checks."""

    question: str
    expected: ExpectedSource
    matched: bool
    matched_rank: int | None


class RetrievalEvaluationSummary(TypedDict):
    """Aggregate expected-source evaluation summary."""

    total: int
    matched: int
    missed: int
    accuracy: float


def load_eval_questions(path: str | Path) -> list[str]:
    """
    Load evaluation questions from a plain text file.

    Blank lines and simple shell paste artifacts are ignored so the file can be
    cleaned up gradually without breaking the evaluator.
    """
    path = Path(path)
    questions: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line == "EOF" or line.startswith("cat >"):
            continue

        questions.append(line)

    return questions


def load_expected_sources(path: str | Path) -> dict[str, list[ExpectedSource]]:
    """
    Load expected retrieval source checks from JSON.

    Supported JSON shape:

    {
      "Question text": [
        {"relative_path": "docs/index.md"},
        {"source_type": "example_config", "title": "config_index.yml"}
      ]
    }
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Expected sources file must contain a JSON object.")

    expected_sources: dict[str, list[ExpectedSource]] = {}

    for question, raw_expectations in data.items():
        if not isinstance(question, str):
            raise ValueError("Expected source question keys must be strings.")

        if not isinstance(raw_expectations, list):
            raise ValueError(
                f"Expected sources for question must be a list: {question}"
            )

        expectations: list[ExpectedSource] = []

        for raw_expectation in raw_expectations:
            if not isinstance(raw_expectation, dict):
                raise ValueError(
                    f"Expected source entries must be objects: {question}"
                )

            expectation: ExpectedSource = {}

            for key in ["doc_id", "source_type", "relative_path", "title"]:
                value = raw_expectation.get(key)

                if value is not None:
                    expectation[key] = str(value)

            if not expectation:
                raise ValueError(
                    f"Expected source entry must define at least one field: {question}"
                )

            expectations.append(expectation)

        expected_sources[question] = expectations

    return expected_sources


def evaluate_retrieval_questions(
    questions: list[str],
    *,
    corpus_path: str | Path,
    backend: str = "simple",
    top_k: int = 5,
) -> dict[str, list[RetrievalEvaluationResult]]:
    """
    Retrieve top-k sources for each question and return compact records.
    """
    evaluation: dict[str, list[RetrievalEvaluationResult]] = {}

    for question in questions:
        results = retrieve_documents(
            query=question,
            top_k=top_k,
            backend=backend,
            corpus_path=corpus_path,
        )

        evaluation[question] = [
            {
                "question": question,
                "rank": rank,
                "score": result.score,
                "doc_id": result.document.doc_id,
                "source_type": result.document.source_type,
                "relative_path": str(
                    result.document.metadata.get("relative_path")
                    or result.document.file_path
                    or ""
                ),
                "title": result.document.title or "",
            }
            for rank, result in enumerate(results, start=1)
        ]

    return evaluation


def _result_matches_expectation(
    result: RetrievalEvaluationResult,
    expectation: ExpectedSource,
) -> bool:
    """Return True when a retrieved result satisfies all expected fields."""
    for key, expected_value in expectation.items():
        actual_value = str(result.get(key, ""))

        if expected_value not in actual_value:
            return False

    return True


def check_expected_sources(
    evaluation: dict[str, list[RetrievalEvaluationResult]],
    expected_sources: dict[str, list[ExpectedSource]],
) -> list[RetrievalExpectationCheck]:
    """
    Check whether each expected source appears in the retrieved top-k results.
    """
    checks: list[RetrievalExpectationCheck] = []

    for question, expectations in expected_sources.items():
        results = evaluation.get(question, [])

        for expectation in expectations:
            matched_rank: int | None = None

            for result in results:
                if _result_matches_expectation(result, expectation):
                    matched_rank = result["rank"]
                    break

            checks.append(
                {
                    "question": question,
                    "expected": expectation,
                    "matched": matched_rank is not None,
                    "matched_rank": matched_rank,
                }
            )

    return checks


def summarize_expectation_checks(
    checks: list[RetrievalExpectationCheck],
) -> RetrievalEvaluationSummary:
    """Summarize expected-source match checks."""
    total = len(checks)
    matched = sum(1 for check in checks if check["matched"])
    missed = total - matched
    accuracy = matched / total if total else 0.0

    return {
        "total": total,
        "matched": matched,
        "missed": missed,
        "accuracy": accuracy,
    }
