from __future__ import annotations

from docask.retrieval.base import RetrievalResult


"""
Temporary extractive answerer.

This module produces a simple answer directly from the retrieved sources,
without calling an LLM. It is useful for testing retrieval and for debugging
the corpus before integrating full LLM answer generation.
"""


def answer_from_sources(question: str, results: list[RetrievalResult]) -> str:
    """
    Generate a minimal answer from retrieved sources.

    The current implementation mostly returns the top retrieved document. It
    has a special case for signature questions, where returning the extracted
    Python signature is usually more useful than returning the full docstring.
    """
    if not results:
        return "I could not find relevant sources in the corpus."

    top_doc = results[0].document

    if "signature" in question.lower() and top_doc.signature:
        return (
            f"The signature of `{top_doc.symbol_name}` is:\n\n"
            f"```python\n{top_doc.signature}\n```\n\n"
            f"Source: [Source 1]"
        )

    return (
        "Based on the most relevant source, here is the answer:\n\n"
        f"{top_doc.content.strip()}\n\n"
        "Source: [Source 1]"
    )