from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from docask.data_models import DocumentRecord

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

def iter_doc_files(
    base_path: str | Path,
    extensions: tuple[str, ...] = (".md", ".rst"),
) -> Iterable[Path]:
    base_path = Path(base_path)
    for path in base_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def _clean_heading(text: str) -> str:
    return text.strip().strip("#").strip()


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s/]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or "section"


def _split_markdown_sections(content: str) -> list[dict]:
    lines = content.splitlines()

    sections: list[dict] = []
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
    return stem.replace("_", " ").replace("-", " ").strip().title()

def _extract_page_title(sections: list[dict], fallback_title: str) -> str:
    for section in sections:
        if section["heading_level"] == 1 and section["section_title"]:
            return section["section_title"]
    return fallback_title


def load_markdown_documents(base_path: str | Path) -> list[DocumentRecord]:
    base_path = Path(base_path)
    documents: list[DocumentRecord] = []

    for path in iter_doc_files(base_path):
        content = path.read_text(encoding="utf-8")
        rel_path = str(path.relative_to(base_path))
        doc_domain = Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else "root"

        sections = _split_markdown_sections(content)
        page_title = _extract_page_title(sections, _humanize_filename(path.stem))

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
                        "project_name": "mmore",
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

            if section_title:
                doc_id_suffix = _slugify(section_title)
            else:
                doc_id_suffix = f"section-{idx}"

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
                        "project_name": "mmore",
                        "doc_domain": doc_domain,
                        "heading_level": heading_level,
                        "page_title": page_title,
                    },
                )
            )

    return documents