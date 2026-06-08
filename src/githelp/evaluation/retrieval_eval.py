from __future__ import annotations

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
