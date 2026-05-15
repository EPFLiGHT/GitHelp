from __future__ import annotations


def build_prompt(question: str, sources: list[dict]) -> str:
    """Build a source-grounded prompt for the LLM."""

    formatted_sources = []

    for i, source in enumerate(sources, start=1):
        title = source.get("title") or "Untitled source"
        file_path = source.get("file_path") or "Unknown path"
        source_type = source.get("source_type") or "unknown"
        section_title = source.get("section_title") or ""
        module_name = source.get("module_name") or ""
        symbol_name = source.get("symbol_name") or ""
        signature = source.get("signature") or ""
        content = source.get("content") or ""

        metadata_lines = [
            f"Title: {title}",
            f"Path: {file_path}",
            f"Type: {source_type}",
        ]

        if section_title:
            metadata_lines.append(f"Section: {section_title}")

        if module_name:
            metadata_lines.append(f"Module: {module_name}")

        if symbol_name:
            metadata_lines.append(f"Symbol: {symbol_name}")

        if signature:
            metadata_lines.append(f"Signature: {signature}")

        formatted_sources.append(
            f"[Source {i}]\n"
            + "\n".join(metadata_lines)
            + f"\nContent:\n{content}\n"
        )

    sources_text = "\n\n".join(formatted_sources)

    return f"""
You are DocAsk, a documentation assistant for a software repository.

Your task is to answer the user's question using only the provided sources.

Rules:
- Use only the information contained in the sources.
- Do not invent commands, file paths, function names, classes, arguments, or configuration keys.
- If the sources do not contain enough information, say that the available documentation is not sufficient.
- Cite the sources you use with [Source 1], [Source 2], etc.
- Do not cite a source if you did not use it.
- If the answer involves code, explain only what is supported by the provided docstrings, signatures, or documentation.
- Be concise but precise.

User question:
{question}

Sources:
{sources_text}

Answer:
""".strip()