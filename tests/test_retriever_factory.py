import json
from pathlib import Path

import pytest

from docask.retrieval.retriever_factory import retrieve_documents


def test_retriever_factory_uses_simple_backend(tmp_path: Path):
    corpus_path = tmp_path / "corpus.jsonl"

    records = [
        {
            "doc_id": "doc::install",
            "content": "This document explains how to install the package.",
            "source_type": "markdown_section",
            "title": "Installation",
            "file_path": "docs/install.md",
            "section_title": "Installation",
            "module_name": None,
            "symbol_name": None,
            "signature": None,
            "language": "en",
            "tags": [],
            "metadata": {},
        },
        {
            "doc_id": "doc::run",
            "content": "This document explains how to run the app.",
            "source_type": "markdown_section",
            "title": "Run app",
            "file_path": "docs/run.md",
            "section_title": "Usage",
            "module_name": None,
            "symbol_name": None,
            "signature": None,
            "language": "en",
            "tags": [],
            "metadata": {},
        },
    ]

    corpus_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    results = retrieve_documents(
        query="How do I install the package?",
        top_k=1,
        backend="simple",
        corpus_path=corpus_path,
    )

    assert len(results) == 1
    assert results[0].document.doc_id == "doc::install"


def test_retriever_factory_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unknown retrieval backend"):
        retrieve_documents(
            query="test query",
            top_k=1,
            backend="unknown",
        )