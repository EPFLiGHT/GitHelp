# Internal format of our documents
# For now, a unique model : DocumentRecord

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    doc_id: str
    content: str
    source_type: str        # can be mardown_docs, readme_section, docstring, ...
                            # useful to filter the sources, and explain from where this answer comes from
    title: str | None = None
    file_path: str | None = None
    section_title: str | None = None

    module_name: str | None = None
    symbol_name: str | None = None
    signature: str | None = None

    language: str | None = "en"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)