from __future__ import annotations

import json
from pathlib import Path

from githelp.evaluation.retrieval_eval import (
    check_expected_sources,
    evaluate_retrieval_questions,
    load_expected_sources,
    load_eval_questions,
    summarize_expectation_checks,
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


def test_load_expected_sources_reads_json_mapping(tmp_path: Path):
    expected_path = tmp_path / "expected.json"
    expected_path.write_text(
        '{"How do I install it?": [{"relative_path": "docs/install.md"}]}',
        encoding="utf-8",
    )

    assert load_expected_sources(expected_path) == {
        "How do I install it?": [{"relative_path": "docs/install.md"}]
    }


def test_check_expected_sources_reports_matches_and_misses():
    evaluation = {
        "How do I install it?": [
            {
                "question": "How do I install it?",
                "rank": 1,
                "score": 1.0,
                "doc_id": "doc::install",
                "source_type": "markdown_section",
                "relative_path": "docs/install.md",
                "title": "Installation",
            }
        ]
    }

    checks = check_expected_sources(
        evaluation,
        {
            "How do I install it?": [
                {"relative_path": "docs/install.md"},
                {"relative_path": "docs/missing.md"},
            ]
        },
    )
    summary = summarize_expectation_checks(checks)

    assert checks == [
        {
            "question": "How do I install it?",
            "expected": {"relative_path": "docs/install.md"},
            "matched": True,
            "matched_rank": 1,
        },
        {
            "question": "How do I install it?",
            "expected": {"relative_path": "docs/missing.md"},
            "matched": False,
            "matched_rank": None,
        },
    ]
    assert summary == {
        "total": 2,
        "matched": 1,
        "missed": 1,
        "accuracy": 0.5,
    }
