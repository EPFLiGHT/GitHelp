from pathlib import Path

from githelp.corpus.builder import build_corpus


def test_build_corpus_with_markdown_and_python(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    code_dir = tmp_path / "src"

    docs_dir.mkdir()
    code_dir.mkdir()

    (docs_dir / "intro.md").write_text(
        "# Introduction\n\nThis is the project documentation.",
        encoding="utf-8",
    )

    (code_dir / "example.py").write_text(
        '''
def hello(name: str) -> str:
    """Return a greeting message."""
    return f"Hello {name}"
''',
        encoding="utf-8",
    )

    corpus = build_corpus(
        docs_path=docs_dir,
        code_path=code_dir,
    )

    assert len(corpus) >= 2

    source_types = {doc.source_type for doc in corpus}

    assert "markdown_section" in source_types or "markdown" in source_types
    assert "python_function" in source_types
