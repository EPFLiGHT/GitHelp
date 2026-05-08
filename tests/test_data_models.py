from docask.data_models import DocumentRecord


def test_document_record_minimal_fields() -> None:
    doc = DocumentRecord(
        doc_id="test::doc",
        content="Some content",
        source_type="markdown_section",
    )

    assert doc.doc_id == "test::doc"
    assert doc.content == "Some content"
    assert doc.source_type == "markdown_section"
    assert doc.tags == []
    assert doc.metadata == {}