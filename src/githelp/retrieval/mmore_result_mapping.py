from __future__ import annotations

from typing import Any

from githelp.data_models import DocumentRecord
from githelp.retrieval.base import RetrievalResult


MMORE_RETRIEVAL_MODE_METADATA_KEY = "mmore_retrieval_mode"
MMORE_NATIVE_MODE = "native_index"
MMORE_CORPUS_FALLBACK_MODE = "corpus_fallback"


def get_result_field(result: dict[str, Any], field_name: str) -> Any:
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


def parse_githelp_header(text: str) -> tuple[dict[str, str], str]:
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


def mmore_result_to_retrieval_result(result: dict[str, Any]) -> RetrievalResult:
    """
    Convert one raw MMORE result into a GitHelp RetrievalResult.
    """
    raw_text = get_result_field(result, "text") or ""
    score = float(result.get("distance", result.get("score", 0.0)))

    header_metadata, content = parse_githelp_header(raw_text)

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


def tag_results_with_mmore_mode(
    results: list[RetrievalResult],
    mode: str,
) -> list[RetrievalResult]:
    """
    Add the MMORE retrieval mode to each result's metadata.
    """
    tagged_results: list[RetrievalResult] = []

    for result in results:
        doc = result.document.model_copy(deep=True)
        doc.metadata[MMORE_RETRIEVAL_MODE_METADATA_KEY] = mode
        tagged_results.append(RetrievalResult(document=doc, score=result.score))

    return tagged_results
