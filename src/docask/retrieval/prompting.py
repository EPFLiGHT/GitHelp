from __future__ import annotations

from docask.retrieval.simple_retriever import RetrievalResult


SYSTEM_PROMPT = """You are DocAsk, an assistant that answers questions about a software project's documentation and code documentation.

Use only the provided sources to answer.
If the sources are insufficient, say that you do not know from the available sources.
Always cite the sources you used.
Be concise, technical, and precise.
"""


def format_source_label(result: RetrievalResult, index: int) -> str:
    doc = result.document

    source_type = doc.source_type
    relative_path = doc.metadata.get("relative_path") or doc.file_path or "unknown"

    if doc.symbol_name:
        location = doc.title or doc.symbol_name
    elif doc.section_title:
        location = doc.section_title
    else:
        location = doc.title or "unknown"

    return f"[Source {index}] {source_type} — {relative_path} — {location}"


def format_context(results: list[RetrievalResult]) -> str:
    blocks: list[str] = []

    for index, result in enumerate(results, start=1):
        doc = result.document
        label = format_source_label(result, index)

        blocks.append(
            "\n".join(
                [
                    label,
                    f"score: {result.score:.4f}",
                    "",
                    doc.content.strip(),
                ]
            )
        )

    return "\n\n---\n\n".join(blocks)


def build_user_prompt(question: str, results: list[RetrievalResult]) -> str:
    context = format_context(results)

    return f"""Question:
{question}

Sources:
{context}

Answer the question using only the sources above.
Cite sources inline using [Source 1], [Source 2], etc.
"""