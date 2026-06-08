from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult
from githelp.utils.paths import PROJECT_ROOT, resolve_project_path


"""
MMORE retrieval backend adapter.

This module connects GitHelp to MMORE's retriever while keeping the rest of
GitHelp independent from MMORE-specific result formats. Raw MMORE results are
converted back into GitHelp RetrievalResult objects.
"""


MIN_MMORE_RAW_RESULTS = 40
DEFAULT_MMORE_INDEX_CONFIG_PATH = "configs/mmore_index_config.yaml"
DEFAULT_MMORE_CORPUS_PATH = "data/processed/mmore_corpus.jsonl"
MMORE_WORKER_RESULT_PREFIX = "GITHELP_MMORE_RESULTS="


def _get_result_field(result: dict[str, Any], field_name: str) -> Any:
    """
    Get a field from a raw MMORE result.

    Depending on the MMORE/Milvus return format, fields may appear directly at
    the top level or inside an "entity" dictionary.
    """
    if field_name in result:
        return result[field_name]

    entity = result.get("entity")
    if isinstance(entity, dict):
        return entity.get(field_name)

    return None


def _parse_githelp_header(text: str) -> tuple[dict[str, str], str]:
    """
    Parse the GitHelp metadata header added before MMORE indexing.

    The header is inserted by mmore_format.document_to_mmore_sample. It allows
    GitHelp to recover the original document ID, source type, title, section,
    module, symbol, and signature after retrieval from MMORE.
    """
    if "\n\nContent:\n" not in text:
        return {}, text

    header, content = text.split("\n\nContent:\n", maxsplit=1)

    metadata: dict[str, str] = {}

    for line in header.splitlines():
        if ": " not in line:
            continue

        key, value = line.split(": ", maxsplit=1)
        metadata[key.strip()] = value.strip()

    return metadata, content.strip()


def _mmore_result_to_retrieval_result(result: dict[str, Any]) -> RetrievalResult:
    """
    Convert one raw MMORE result into a GitHelp RetrievalResult.
    """
    raw_text = _get_result_field(result, "text") or ""
    score = float(result.get("distance", result.get("score", 0.0)))

    header_metadata, content = _parse_githelp_header(raw_text)

    doc_id = header_metadata.get("GitHelp ID", str(result.get("id", "")))
    source_type = header_metadata.get("Source type", "mmore_result")
    title = header_metadata.get("Title")
    relative_path = header_metadata.get("Relative path")
    section_title = header_metadata.get("Section")
    module_name = header_metadata.get("Module")
    symbol_name = header_metadata.get("Symbol")
    signature = header_metadata.get("Signature")

    metadata = {
        "relative_path": relative_path,
        "githelp_id": doc_id,
        "raw_mmore_id": result.get("id"),
    }

    metadata = {
        key: value
        for key, value in metadata.items()
        if value is not None
    }

    doc = DocumentRecord(
        doc_id=doc_id,
        content=content,
        source_type=source_type,
        title=title,
        file_path=relative_path,
        section_title=section_title,
        module_name=module_name,
        symbol_name=symbol_name,
        signature=signature,
        language="en",
        tags=[],
        metadata=metadata,
    )

    return RetrievalResult(document=doc, score=score)


def _rerank_for_githelp_intent(
    query: str,
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Apply small GitHelp-specific reranking heuristics.

    MMORE provides the main retrieval ranking. This function only adds a light
    preference for YAML configuration examples when the user explicitly asks
    for a config example or config structure.
    """
    query_lower = query.lower()

    wants_config_example = (
        "config" in query_lower
        and any(
            word in query_lower
            for word in ["look like", "example", "yaml", "write", "structure"]
        )
    )

    if not wants_config_example:
        return results

    reranked: list[RetrievalResult] = []

    for result in results:
        doc = result.document
        score = result.score

        if doc.source_type in {"example_config", "production_config", "yaml_config"}:
            score += 0.5

        if doc.source_type == "example_config":
            score += 0.2

        relative_path = doc.metadata.get("relative_path")
        if relative_path and "index" in relative_path.lower():
            score += 0.2

        reranked.append(RetrievalResult(document=doc, score=score))

    reranked.sort(key=lambda result: result.score, reverse=True)

    return reranked


def _load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a dictionary: {path}")

    return data


def _load_githelp_mmore_model_configs(
    index_config_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Load dense and sparse model configs from GitHelp's MMORE index config.

    MMORE tries to recover these from Milvus index metadata during retrieval,
    but Milvus Lite may not persist custom fields such as model_name. GitHelp
    keeps the source of truth in configs/mmore_index_config.yaml.
    """
    config = _load_yaml_mapping(index_config_path)
    indexer_config = config.get("indexer", {})

    if not isinstance(indexer_config, dict):
        raise ValueError("MMORE index config must define an indexer section.")

    dense_model_config = indexer_config.get("dense_model")
    sparse_model_config = indexer_config.get("sparse_model")

    if not isinstance(dense_model_config, dict):
        raise ValueError("MMORE index config must define indexer.dense_model.")

    if not isinstance(sparse_model_config, dict):
        raise ValueError("MMORE index config must define indexer.sparse_model.")

    return dense_model_config, sparse_model_config


def _create_retriever_from_githelp_configs(
    retriever_config_path: str | Path,
    index_config_path: str | Path,
):
    """
    Create a MMORE Retriever using GitHelp config files as model metadata.
    """
    from pymilvus import MilvusClient
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from mmore.rag.model.dense.base import DenseModel, DenseModelConfig
    from mmore.rag.model.sparse.base import SparseModel, SparseModelConfig
    from mmore.rag.retriever import Retriever

    retriever_config = _load_yaml_mapping(retriever_config_path)
    db_config = retriever_config.get("db", {})

    if not isinstance(db_config, dict):
        raise ValueError("MMORE retriever config must define a db section.")

    dense_model_config, sparse_model_config = _load_githelp_mmore_model_configs(
        index_config_path
    )

    collection_name = str(retriever_config.get("collection_name", "mmore_docs"))
    db_uri = resolve_project_path(
        str(db_config.get("uri", "./data/indexes/mmore/githelp.db"))
    )
    client = MilvusClient(
        uri=str(db_uri),
        db_name=str(db_config.get("name", "my_db")),
    )

    if not client.has_collection(collection_name):
        raise ValueError(
            "The Milvus database does not have collection "
            f"{collection_name}. Rebuild the MMORE index first."
        )

    reranker_model_name = retriever_config.get("reranker_model_name")

    if reranker_model_name:
        reranker_tokenizer = AutoTokenizer.from_pretrained(str(reranker_model_name))
        reranker_model = AutoModelForSequenceClassification.from_pretrained(
            str(reranker_model_name)
        )
    else:
        reranker_model = None
        reranker_tokenizer = None

    return Retriever(
        dense_model=DenseModel.from_config(DenseModelConfig(**dense_model_config)),
        sparse_model=SparseModel.from_config(SparseModelConfig(**sparse_model_config)),
        client=client,
        hybrid_search_weight=float(retriever_config.get("hybrid_search_weight", 0.5)),
        k=int(retriever_config.get("k", 5)),
        use_web=bool(retriever_config.get("use_web", False)),
        reranker_model=reranker_model,
        reranker_tokenizer=reranker_tokenizer,
    )


def _load_retriever_from_mmore_config(config_path: str | Path):
    """Load MMORE's Retriever from its own retriever config."""
    from mmore.rag.retriever import Retriever

    return Retriever.from_config(str(config_path))


def _load_collection_for_search(retriever, collection_name: str) -> None:
    """
    Load the Milvus collection before searching.

    Milvus can keep an existing collection in a released state after reopening
    a local index. In that state, search/get/query calls fail until load() is
    called.
    """
    client = getattr(retriever, "client", None)
    load_collection = getattr(client, "load_collection", None)

    if load_collection is None:
        return

    load_collection(collection_name=collection_name)


def _serialize_results(results: list[RetrievalResult]) -> list[dict[str, Any]]:
    """Serialize retrieval results for the MMORE subprocess worker."""
    return [
        {
            "score": result.score,
            "document": result.document.model_dump(),
        }
        for result in results
    ]


def deserialize_results(payload: list[dict[str, Any]]) -> list[RetrievalResult]:
    """Deserialize retrieval results produced by the MMORE subprocess worker."""
    return [
        RetrievalResult(
            document=DocumentRecord(**item["document"]),
            score=float(item["score"]),
        )
        for item in payload
    ]


def _resolve_mmore_corpus_path(corpus_path: str | Path | None) -> Path:
    """
    Resolve the MMORE-compatible corpus used by the safe MMORE fallback.

    If GitHelp is given data/projects/<project>/corpus.jsonl, prefer the sibling
    data/projects/<project>/mmore_corpus.jsonl. Otherwise use the default
    exported MMORE corpus path.
    """
    candidates: list[Path] = []

    if corpus_path is not None:
        resolved_corpus_path = resolve_project_path(corpus_path)
        if resolved_corpus_path.name == "mmore_corpus.jsonl":
            candidates.append(resolved_corpus_path)
        else:
            candidates.append(resolved_corpus_path.with_name("mmore_corpus.jsonl"))
            candidates.append(resolved_corpus_path)

    candidates.append(resolve_project_path(DEFAULT_MMORE_CORPUS_PATH))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Could not find an MMORE corpus. Export one with "
        "`python scripts/export_mmore_corpus.py`."
    )


def _load_mmore_corpus_documents(mmore_corpus_path: str | Path) -> list[DocumentRecord]:
    """Load GitHelp documents from an exported MMORE JSONL corpus."""
    documents: list[DocumentRecord] = []
    path = Path(mmore_corpus_path)

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            sample = json.loads(line)
            text = str(sample.get("text", ""))
            metadata = sample.get("metadata", {})
            raw_id = metadata.get("doc_id") if isinstance(metadata, dict) else ""
            result = _mmore_result_to_retrieval_result(
                {
                    "id": raw_id,
                    "text": text,
                    "score": 0.0,
                }
            )
            documents.append(result.document)

    return documents


def _retrieve_from_mmore_corpus(
    query: str,
    top_k: int,
    corpus_path: str | Path | None,
) -> list[RetrievalResult]:
    """
    Retrieve from the exported MMORE corpus without loading native MMORE models.
    """
    from githelp.retrieval.simple_retriever import retrieve as simple_retrieve

    mmore_corpus_path = _resolve_mmore_corpus_path(corpus_path)
    documents = _load_mmore_corpus_documents(mmore_corpus_path)
    return simple_retrieve(query, documents, top_k=top_k)


def _retrieve_with_mmore_native(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    index_config_path: str | Path = DEFAULT_MMORE_INDEX_CONFIG_PATH,
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents using MMORE.

    This function is the MMORE backend adapter for GitHelp. It hides MMORE's
    internal result format and returns standard RetrievalResult objects.
    """
    config_path = resolve_project_path(config_path)
    index_config_path = resolve_project_path(index_config_path)

    try:
        retriever = _load_retriever_from_mmore_config(config_path)
    except KeyError as error:
        if str(error).strip("'") == "model_name":
            try:
                retriever = _create_retriever_from_githelp_configs(
                    retriever_config_path=config_path,
                    index_config_path=index_config_path,
                )
            except Exception as fallback_error:
                raise RuntimeError(
                    "MMORE could not load model metadata from the Milvus index "
                    "or from GitHelp's MMORE config files."
                ) from fallback_error
        else:
            raise

    except RuntimeError as error:
        if "MMORE index metadata is incomplete" in str(error):
            try:
                retriever = _create_retriever_from_githelp_configs(
                    retriever_config_path=config_path,
                    index_config_path=index_config_path,
                )
            except Exception as fallback_error:
                raise RuntimeError(
                    "MMORE could not load model metadata from the Milvus index "
                    "or from GitHelp's MMORE config files."
                ) from fallback_error
        else:
            raise

    raw_k = max(top_k, MIN_MMORE_RAW_RESULTS)
    _load_collection_for_search(retriever, collection_name)

    raw_results = retriever.retrieve(
        query=query,
        collection_name=collection_name,
        k=raw_k,
        output_fields=["text"],
        search_type=search_type,
    )

    results = [
        _mmore_result_to_retrieval_result(result)
        for result in raw_results
    ]

    return _rerank_for_githelp_intent(query, results)


def _retrieve_with_mmore_subprocess(
    query: str,
    top_k: int,
    config_path: str | Path,
    index_config_path: str | Path,
    collection_name: str,
    search_type: str,
) -> list[RetrievalResult]:
    """
    Run native MMORE retrieval in a child process.

    MMORE/Milvus can segfault in some local environments. Running it outside
    Streamlit keeps the UI process alive and lets GitHelp fall back to the
    exported MMORE corpus.
    """
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else src_path
    )

    command = [
        sys.executable,
        "-m",
        "githelp.retrieval.mmore_worker",
        "--query",
        query,
        "--top-k",
        str(top_k),
        "--config-path",
        str(config_path),
        "--index-config-path",
        str(index_config_path),
        "--collection-name",
        collection_name,
        "--search-type",
        search_type,
    ]

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Native MMORE retrieval failed in a subprocess. "
            f"Return code: {completed.returncode}. "
            f"stderr: {completed.stderr.strip()}"
        )

    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(MMORE_WORKER_RESULT_PREFIX):
            payload = json.loads(line[len(MMORE_WORKER_RESULT_PREFIX):])
            return deserialize_results(payload)

    raise RuntimeError("Native MMORE worker did not return retrieval results.")


def retrieve_with_mmore(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    index_config_path: str | Path = DEFAULT_MMORE_INDEX_CONFIG_PATH,
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
    corpus_path: str | Path | None = None,
    use_subprocess: bool = True,
) -> list[RetrievalResult]:
    """
    Retrieve with MMORE.

    The native MMORE retriever is attempted first. If it fails in the child
    process, GitHelp retrieves from the exported MMORE corpus so the app stays
    usable instead of crashing.
    """
    if not use_subprocess:
        return _retrieve_with_mmore_native(
            query=query,
            top_k=top_k,
            config_path=config_path,
            index_config_path=index_config_path,
            collection_name=collection_name,
            search_type=search_type,
        )

    try:
        return _retrieve_with_mmore_subprocess(
            query=query,
            top_k=top_k,
            config_path=config_path,
            index_config_path=index_config_path,
            collection_name=collection_name,
            search_type=search_type,
        )
    except RuntimeError:
        return _retrieve_from_mmore_corpus(
            query=query,
            top_k=top_k,
            corpus_path=corpus_path,
        )
