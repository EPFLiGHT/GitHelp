from __future__ import annotations

from pathlib import Path

from githelp.corpus.builder import build_corpus, save_corpus_jsonl
from githelp.rag.answering import prepare_answer_prompt
from githelp.retrieval.retriever_factory import retrieve_documents


def test_tiny_repo_pipeline_builds_retrieves_and_prepares_prompt(tmp_path: Path):
    target_repo = tmp_path / "tiny_repo"
    docs_path = target_repo / "docs"
    code_path = target_repo / "src" / "tiny_repo"
    examples_path = target_repo / "examples"

    docs_path.mkdir(parents=True)
    code_path.mkdir(parents=True)
    examples_path.mkdir(parents=True)

    (docs_path / "usage.md").write_text(
        "# Usage\n\nRun `python -m tiny_repo` to start Tiny Repo.",
        encoding="utf-8",
    )

    (code_path / "math_tools.py").write_text(
        '''
def calculate_answer(value: int) -> int:
    """Calculate the answer for a value."""
    return value + 42
''',
        encoding="utf-8",
    )

    (examples_path / "app_config.yaml").write_text(
        "runner:\n  command: python -m tiny_repo\n",
        encoding="utf-8",
    )

    documents = build_corpus(
        docs_path=docs_path,
        code_path=code_path,
        project_name="tiny_repo",
        package_name="tiny_repo",
        repo_path=target_repo,
        include_yaml_configs=True,
        yaml_config_paths=[examples_path],
        include_repo_structure=True,
        repo_structure_max_depth=3,
    )

    source_types = {document.source_type for document in documents}

    assert "markdown_section" in source_types
    assert "python_function" in source_types
    assert "example_config" in source_types
    assert "repo_structure" in source_types

    corpus_path = tmp_path / "corpus.jsonl"
    save_corpus_jsonl(documents, corpus_path)

    retrieval_results = retrieve_documents(
        query="How do I run tiny_repo?",
        top_k=2,
        backend="simple",
        corpus_path=corpus_path,
    )

    assert retrieval_results
    assert retrieval_results[0].document.source_type == "markdown_section"
    assert "python -m tiny_repo" in retrieval_results[0].document.content

    app_config_path = tmp_path / "app_config.yaml"
    app_config_path.write_text(
        "project_name: tiny_repo\n"
        "project_profile: generic\n"
        "llm:\n"
        "  provider: dummy\n",
        encoding="utf-8",
    )

    prompt, prompt_results = prepare_answer_prompt(
        question="How do I run tiny_repo?",
        corpus_path=corpus_path,
        top_k=2,
        backend="simple",
        config_path=app_config_path,
    )

    assert prompt_results
    assert "How do I run tiny_repo?" in prompt
    assert "python -m tiny_repo" in prompt
    assert "tiny_repo" in prompt
