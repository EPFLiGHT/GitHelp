import json
from pathlib import Path

from githelp.retrieval.simple_retriever import load_corpus


def test_load_corpus_from_jsonl(tmp_path: Path):
    corpus_path = tmp_path / "corpus.jsonl"

    record = {
        "doc_id": "doc::1",
        "content": "Example content.",
        "source_type": "markdown_section",
        "title": "Example",
        "file_path": "docs/example.md",
        "section_title": "Intro",
        "module_name": None,
        "symbol_name": None,
        "signature": None,
        "language": "en",
        "tags": [],
        "metadata": {},
    }

    corpus_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    documents = load_corpus(corpus_path)

    assert len(documents) == 1
    assert documents[0].doc_id == "doc::1"
    assert documents[0].content == "Example content."
    assert documents[0].source_type == "markdown_section"
