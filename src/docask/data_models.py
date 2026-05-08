# Internal format of our documents
# For now, a unique model : DocumentRecord

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    """
    Normalized representation of one documentation unit in DocAsk.

    A DocumentRecord is the internal format used to represent any piece of
    documentation, regardless of its original source. It can come from a
    Markdown section, a README file, a Python module docstring, a class
    docstring, a function signature, or another future source.

    The goal of this model is to provide a common structure before indexing,
    retrieval, and answer generation.
    """

    doc_id: str
    """
    Unique identifier for the document record.

    Examples:
    - markdown::getting_started/install.md::installation
    - code::mmore.process.pdf_processor.PDFProcessor
    """

    content: str
    """
    Main textual content that will be indexed and retrieved.
    """

    source_type: str
    """
    Type of source used to create this record.

    Examples:
    - markdown_section
    - readme_section
    - python_module
    - python_class
    - python_function
    - python_method
    - example_config
    - yaml_config
    """

    title: str | None = None
    """
    Human-readable title for the record.

    For Markdown sections, this can be the page or section title.
    For Python symbols, this can be the full symbol name.
    """

    file_path: str | None = None
    """
    Original file path from which this record was extracted.
    """

    section_title: str | None = None
    """
    Markdown section title, when the record comes from a structured document.
    """

    module_name: str | None = None
    """
    Python module name, when the record comes from Python source code.
    """

    symbol_name: str | None = None
    """
    Name of the Python symbol, such as a class, function, or method.
    """

    signature: str | None = None
    """
    Function or method signature, when available.
    """

    language: str | None = "en"
    """
    Language of the document content.
    """

    tags: list[str] = Field(default_factory=list)
    """
    Optional tags used to classify or filter records.
    """

    metadata: dict[str, Any] = Field(default_factory=dict)
    """
    Additional source-specific metadata.
    """