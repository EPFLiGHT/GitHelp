from __future__ import annotations

from pathlib import Path
from typing import Any

from docask.data_models import DocumentRecord
from docask.retrieval.simple_retriever import RetrievalResult
from docask.utils.paths import PROJECT_ROOT


def _get_result_field(result: dict[str, Any], field_name: str) -> Any:
    """
    Milvus/MMORE results may store fields either at the top level
    or inside an 'entity' dictionary.
    """
    if field_name in result:
        return result[field_name]

    entity = result.get("entity")
    if isinstance(entity, dict):
        return entity.get(field_name)

    return None


def _parse_docask_header(text: str) -> tuple[dict[str, str], str]:
    """
    Parse the metadata header inserted by DocAsk before MMORE indexing.

    Expected format:

    DocAsk ID: ...
    Source type: ...
    Title: ...
    Relative path: ...
    Section: ...
    Module: ...
    Symbol: ...
    Signature: ...

    Content:
    ...
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
    raw_text = _get_result_field(result, "text") or ""
    score = float(result.get("distance", result.get("score", 0.0)))

    header_metadata, content = _parse_docask_header(raw_text)

    doc_id = header_metadata.get("DocAsk ID", str(result.get("id", "")))
    source_type = header_metadata.get("Source type", "mmore_result")
    title = header_metadata.get("Title")
    relative_path = header_metadata.get("Relative path")
    section_title = header_metadata.get("Section")
    module_name = header_metadata.get("Module")
    symbol_name = header_metadata.get("Symbol")
    signature = header_metadata.get("Signature")

    metadata = {
        "relative_path": relative_path,
        "docask_id": doc_id,
        "raw_mmore_id": result.get("id"),
    }

    metadata = {key: value for key, value in metadata.items() if value is not None}

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


def retrieve_with_mmore(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents using the internal MMORE index.

    This adapter keeps MMORE hidden behind DocAsk.
    The rest of DocAsk only receives RetrievalResult objects.
    """
    from mmore.rag.retriever import Retriever

    config_path = PROJECT_ROOT / config_path

    retriever = Retriever.from_config(str(config_path))

    raw_results = retriever.retrieve(
        query=query,
        collection_name=collection_name,
        k=top_k,
        output_fields=["text"],
        search_type=search_type,
    )

    return [_mmore_result_to_retrieval_result(result) for result in raw_results]