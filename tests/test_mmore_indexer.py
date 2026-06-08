from __future__ import annotations

import sys
from pathlib import Path

from githelp.indexing.mmore_indexer import build_mmore_index


def test_build_mmore_index_creates_local_milvus_parent_dir(
    monkeypatch,
    tmp_path: Path,
):
    config_path = tmp_path / "configs" / "mmore_index_config.yaml"
    documents_path = tmp_path / "corpus.jsonl"
    calls = []

    config_path.parent.mkdir()
    config_path.write_text(
        "indexer:\n"
        "  db:\n"
        "    uri: ./data/indexes/mmore/githelp.db\n"
        "    name: my_db\n",
        encoding="utf-8",
    )
    documents_path.write_text('{"text": "example"}\n', encoding="utf-8")

    def fake_run(command, check, stdout, stderr):
        calls.append(
            {
                "command": command,
                "check": check,
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "githelp.indexing.mmore_indexer.subprocess.run",
        fake_run,
    )

    build_mmore_index(
        config_path=config_path,
        documents_path=documents_path,
        collection_name="mmore_docs",
        show_logs=True,
    )

    assert (tmp_path / "data" / "indexes" / "mmore").is_dir()
    assert calls[0]["command"] == [
        sys.executable,
        "-m",
        "mmore",
        "index",
        "--config-file",
        str(config_path),
        "--documents-path",
        str(documents_path),
        "--collection-name",
        "mmore_docs",
    ]


def test_build_mmore_index_removes_stale_local_milvus_db_before_rebuild(
    monkeypatch,
    tmp_path: Path,
):
    config_path = tmp_path / "configs" / "mmore_index_config.yaml"
    documents_path = tmp_path / "corpus.jsonl"
    stale_collection = tmp_path / "data" / "indexes" / "mmore" / "githelp.db" / "collections" / "mmore_docs"

    config_path.parent.mkdir()
    stale_collection.mkdir(parents=True)
    (stale_collection / "partial").write_text("stale", encoding="utf-8")
    config_path.write_text(
        "indexer:\n"
        "  db:\n"
        "    uri: ./data/indexes/mmore/githelp.db\n"
        "    name: my_db\n",
        encoding="utf-8",
    )
    documents_path.write_text('{"text": "example"}\n', encoding="utf-8")

    def fake_run(command, check, stdout, stderr):
        return None

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "githelp.indexing.mmore_indexer.subprocess.run",
        fake_run,
    )

    build_mmore_index(
        config_path=config_path,
        documents_path=documents_path,
        collection_name="mmore_docs",
        show_logs=True,
    )

    assert not stale_collection.exists()
    assert (tmp_path / "data" / "indexes" / "mmore").is_dir()


def test_build_mmore_index_rejects_transformers_5_with_sparse_model(
    monkeypatch,
    tmp_path: Path,
):
    config_path = tmp_path / "mmore_index_config.yaml"
    documents_path = tmp_path / "corpus.jsonl"

    config_path.write_text(
        "indexer:\n"
        "  sparse_model:\n"
        "    model_name: splade\n"
        "  db:\n"
        "    uri: ./data/indexes/mmore/githelp.db\n"
        "    name: my_db\n",
        encoding="utf-8",
    )
    documents_path.write_text('{"text": "example"}\n', encoding="utf-8")

    monkeypatch.setattr(
        "githelp.indexing.mmore_indexer.importlib.metadata.version",
        lambda package_name: "5.3.0",
    )

    try:
        build_mmore_index(
            config_path=config_path,
            documents_path=documents_path,
            collection_name="mmore_docs",
        )
    except RuntimeError as error:
        assert "Transformers 5.3.0" in str(error)
        assert "transformers>=4.51.0,<5" in str(error)
    else:
        raise AssertionError("Expected incompatible Transformers version to fail")
