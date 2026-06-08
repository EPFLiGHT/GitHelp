from githelp.data_models import DocumentRecord


def test_document_record_creation():
    record = DocumentRecord(
        doc_id="test::1",
        content="This is a test document.",
        source_type="markdown",
        title="Test document",
        file_path="docs/test.md",
        section_title="Introduction",
        module_name=None,
        symbol_name=None,
        metadata={"key": "value"},
    )

    assert record.doc_id == "test::1"
    assert record.content == "This is a test document."
    assert record.source_type == "markdown"
    assert record.title == "Test document"
    assert record.file_path == "docs/test.md"
    assert record.section_title == "Introduction"
    assert record.metadata["key"] == "value"


def test_document_record_model_dump():
    record = DocumentRecord(
        doc_id="test::2",
        content="Another test document.",
        source_type="python_function",
        title="my_function",
        file_path="src/example.py",
        section_title=None,
        module_name="example",
        symbol_name="my_function",
        metadata={},
    )

    data = record.model_dump()

    assert data["doc_id"] == "test::2"
    assert data["content"] == "Another test document."
    assert data["source_type"] == "python_function"
    assert data["module_name"] == "example"
    assert data["symbol_name"] == "my_function"