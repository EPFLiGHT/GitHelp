from __future__ import annotations

import json
from pathlib import Path

from githelp.evaluation.retrieval_eval import (
    evaluate_retrieval_questions,
    load_eval_questions,
)


def test_load_eval_questions_ignores_blank_lines_and_shell_artifacts(tmp_path: Path):
    questions_path = tmp_path / "questions.txt"
    questions_path.write_text(
        "cat > githelp_eval_questions.txt << 'EOF'\n"
        "\n"
        "How do I install it?\n"
        "EOF\n",
        encoding="utf-8",
    )

    assert load_eval_questions(questions_path) == ["How do I install it?"]


def test_evaluate_retrieval_questions_returns_compact_ranked_sources(tmp_path: Path):
    corpus_path = tmp_path / "corpus.jsonl"

    records = [
        {
            "doc_id": "doc::install",
            "content": "Install the package with pip.",
            "source_type": "markdown_section",
            "title": "Installation",
            "file_path": "docs/install.md",
            "section_title": "Installation",
            "module_name": None,
            "symbol_name": None,
            "signature": None,
            "language": "en",
            "tags": [],
            "metadata": {"relative_path": "docs/install.md"},
        },
        {
            "doc_id": "doc::run",
            "content": "Run the app with streamlit.",
            "source_type": "markdown_section",
            "title": "Run",
            "file_path": "docs/run.md",
            "section_title": "Run",
            "module_name": None,
            "symbol_name": None,
            "signature": None,
            "language": "en",
            "tags": [],
            "metadata": {"relative_path": "docs/run.md"},
        },
    ]

    corpus_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    evaluation = evaluate_retrieval_questions(
        ["How do I install the package?"],
        corpus_path=corpus_path,
        backend="simple",
        top_k=1,
    )

    result = evaluation["How do I install the package?"][0]

    assert result["rank"] == 1
    assert result["doc_id"] == "doc::install"
    assert result["source_type"] == "markdown_section"
    assert result["relative_path"] == "docs/install.md"
