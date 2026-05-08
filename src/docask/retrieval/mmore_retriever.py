from __future__ import annotations

from pathlib import Path
from typing import Any

from docask.data_models import DocumentRecord
from docask.retrieval.base import RetrievalResult
from docask.utils.paths import PROJECT_ROOT


"""
MMORE retrieval backend adapter.

This module connects DocAsk to MMORE's retriever while keeping the rest of
DocAsk independent from MMORE-specific result formats. Raw MMORE results are
converted back into DocAsk RetrievalResult objects.
"""


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


def _parse_docask_header(text: str) -> tuple[dict[str, str], str]:
    """
    Parse the DocAsk metadata header added before MMORE indexing.

    The header is inserted by mmore_format.document_to_mmore_sample. It allows
    DocAsk to recover the original document ID, source type, title, section,
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
    Convert one raw MMORE result into a DocAsk RetrievalResult.
    """
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


def _rerank_for_docask_intent(
    query: str,
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """
    Apply small DocAsk-specific reranking heuristics.

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


def retrieve_with_mmore(
    query: str,
    top_k: int = 5,
    config_path: str | Path = "configs/mmore_retriever_config.yaml",
    collection_name: str = "mmore_docs",
    search_type: str = "hybrid",
) -> list[RetrievalResult]:
    """
    Retrieve relevant documents using MMORE.

    This function is the MMORE backend adapter for DocAsk. It hides MMORE's
    internal result format and returns standard RetrievalResult objects.

    Petit doute à garder en tête : si MMORE renvoie une distance où plus 
    petit = meilleur, alors reranking avec score += peut être faux. 
    Si dans ton test les meilleurs résultats ont les scores les plus hauts, OK. 
    Sinon il faudra inverser.
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

    results = [
        _mmore_result_to_retrieval_result(result)
        for result in raw_results
    ]

    return _rerank_for_docask_intent(query, results)