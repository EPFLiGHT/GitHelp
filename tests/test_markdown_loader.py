from pathlib import Path

from githelp.loaders.markdown_loader import load_markdown_documents


def test_load_markdown_documents_from_single_file(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    markdown_file = docs_dir / "intro.md"
    markdown_file.write_text(
        "# Introduction\n\nThis is the intro.\n\n## Installation\n\nRun pip install.",
        encoding="utf-8",
    )

    documents = load_markdown_documents(docs_dir)

    assert len(documents) > 0

    contents = [doc.content for doc in documents]

    assert any("This is the intro" in content for content in contents)
    assert any("Run pip install" in content for content in contents)


def test_load_markdown_documents_ignores_non_markdown_files(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "intro.md").write_text("# Intro\n\nMarkdown content.", encoding="utf-8")
    (docs_dir / "notes.txt").write_text("This should be ignored.", encoding="utf-8")

    documents = load_markdown_documents(docs_dir)

    assert len(documents) > 0
    assert all(doc.file_path.endswith(".md") for doc in documents)