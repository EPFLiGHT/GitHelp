from __future__ import annotations

from docask.retrieval.base import RetrievalResult


"""
Prompt construction utilities for DocAsk.

This module formats retrieved documents into a source-grounded prompt that can
be sent to an LLM. The prompt instructs the model to answer only from the
retrieved sources and to cite them.
"""


SYSTEM_PROMPT = """You are DocAsk, an assistant that answers questions about a software project's documentation and code documentation.

Use only the provided sources to answer.

Important rules:
- Do not infer missing setup steps.
- Do not invent commands, configuration keys, file paths, APIs, modules, or workflows.
- If the retrieved sources only mention a topic indirectly, say that the available sources are insufficient.
- If the sources do not explain the requested procedure, say so clearly.
- Cite every factual statement with [Source 1], [Source 2], etc.
- Do not quote or paraphrase a source as if it contained information that is not actually present.
- Be concise, technical, and precise.
"""


def format_source_label(result: RetrievalResult, index: int) -> str:
    """
    Build a readable label for one retrieved source.

    The label is shown before each source in the LLM context and is also used
    for inline citations such as [Source 1].
    """
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
    """
    Format retrieved documents as context blocks for the LLM.
    """
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
    """
    Build the user prompt sent to the LLM.

    The prompt includes instructions, the original question, and the retrieved
    sources.
    """
    context = format_context(results)

    return f"""{SYSTEM_PROMPT}

Question:
{question}

Sources:
{context}

Answer:
"""