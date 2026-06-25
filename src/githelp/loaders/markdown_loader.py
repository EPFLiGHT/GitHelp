from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from githelp.data_models import DocumentRecord


"""
Loader for Markdown and reStructuredText documentation files.

This module converts human-written documentation files into DocumentRecord
objects. Markdown files are split by headings so that each section can be
indexed and retrieved independently.
"""


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def iter_doc_files(
    base_path: str | Path,
    extensions: tuple[str, ...] = (".md", ".rst"),
) -> Iterable[Path]:
    """
    Iterate over documentation files under a base directory.

    Parameters
    ----------
    base_path:
        Directory containing documentation files.
    extensions:
        File extensions to include.

    Yields
    ------
    Path
        Documentation file paths found recursively.
    """
    base_path = Path(base_path)

    for path in base_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def _clean_heading(text: str) -> str:
    """
    Normalize a Markdown heading text.
    """
    return text.strip().strip("#").strip()


def _slugify(text: str) -> str:
    """
    Convert a section title into a stable identifier fragment.

    The slug is used in DocumentRecord IDs to make them readable and mostly
    stable across corpus builds.
    """
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s/]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)

    return slug.strip("-") or "section"


def _split_markdown_sections(content: str) -> list[dict[str, Any]]:
    """
    Split Markdown content into sections based on Markdown headings.

    Each returned section contains:
    - section_title
    - heading_level
    - content

    Text before the first heading is also kept as a section with no title.
    """
    lines = content.splitlines()

    sections: list[dict[str, Any]] = []
    current_title: str | None = None
    current_level: int | None = None
    current_lines: list[str] = []

    for line in lines:
        match = HEADING_RE.match(line)

        if match:
            if current_title is not None or current_lines:
                sections.append(
                    {
                        "section_title": current_title,
                        "heading_level": current_level,
                        "content": "\n".join(current_lines).strip(),
                    }
                )

            current_level = len(match.group(1))
            current_title = _clean_heading(match.group(2))
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is not None or current_lines:
        sections.append(
            {
                "section_title": current_title,
                "heading_level": current_level,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return [section for section in sections if section["content"]]


def _humanize_filename(stem: str) -> str:
    """
    Convert a file stem into a readable fallback title.
    """
    return stem.replace("_", " ").replace("-", " ").strip().title()


def _extract_page_title(sections: list[dict[str, Any]], fallback_title: str) -> str:
    """
    Extract the page title from the first level-1 heading when available.
    """
    for section in sections:
        if section["heading_level"] == 1 and section["section_title"]:
            return section["section_title"]

    return fallback_title


def load_markdown_documents(
    base_path: str | Path,
    *,
    project_name: str = "project",
) -> list[DocumentRecord]:
    """
    Load Markdown and reStructuredText files as DocumentRecord objects.

    Markdown files are split into sections to improve retrieval precision.
    If a file has no detected section, the whole file is stored as one record.

    Parameters
    ----------
    base_path:
        Directory containing documentation files.
    project_name:
        Name of the project. Stored in metadata for traceability.

    Returns
    -------
    list[DocumentRecord]
        Documentation records extracted from the files.
    """
    base_path = Path(base_path)
    documents: list[DocumentRecord] = []

    for path in iter_doc_files(base_path):
        content = path.read_text(encoding="utf-8")
        rel_path = str(path.relative_to(base_path))
        rel_parts = Path(rel_path).parts

        doc_domain = rel_parts[0] if len(rel_parts) > 1 else "root"

        sections = _split_markdown_sections(content)
        page_title = _extract_page_title(
            sections,
            fallback_title=_humanize_filename(path.stem),
        )

        if not sections:
            documents.append(
                DocumentRecord(
                    doc_id=f"markdown::{rel_path}",
                    content=content.strip(),
                    source_type="markdown_doc",
                    title=page_title,
                    file_path=str(path),
                    section_title=None,
                    metadata={
                        "relative_path": rel_path,
                        "project_name": project_name,
                        "doc_domain": doc_domain,
                        "heading_level": None,
                    },
                )
            )
            continue

        for idx, section in enumerate(sections):
            section_title = section["section_title"]
            heading_level = section["heading_level"]
            section_content = section["content"].strip()

            if not section_content:
                continue

            doc_id_suffix = (
                _slugify(section_title) if section_title else f"section-{idx}"
            )

            full_title = page_title
            if section_title and section_title != page_title:
                full_title = f"{page_title} - {section_title}"

            documents.append(
                DocumentRecord(
                    doc_id=f"markdown::{rel_path}::{idx}-{doc_id_suffix}",
                    content=section_content,
                    source_type="markdown_section",
                    title=full_title,
                    file_path=str(path),
                    section_title=section_title,
                    metadata={
                        "relative_path": rel_path,
                        "project_name": project_name,
                        "doc_domain": doc_domain,
                        "heading_level": heading_level,
                        "page_title": page_title,
                    },
                )
            )

    return documents
