from githelp.data_models import DocumentRecord
from githelp.retrieval.simple_retriever import retrieve


def test_simple_retriever_boosts_exact_python_symbol_match():
    documents = [
        DocumentRecord(
            doc_id="doc::generic",
            content="This function processes a document.",
            source_type="python_function",
            title="process",
            file_path="src/example.py",
            section_title=None,
            module_name="example",
            symbol_name="process",
            signature="process(document)",
            language="en",
            tags=[],
            metadata={},
        ),
        DocumentRecord(
            doc_id="doc::extract_python_docs",
            content="Extract Python documentation from source files.",
            source_type="python_function",
            title="extract_python_docs",
            file_path="src/githelp/extractors/python_doc_extractor.py",
            section_title=None,
            module_name="githelp.extractors.python_doc_extractor",
            symbol_name="extract_python_docs",
            signature="extract_python_docs(code_path: str)",
            language="en",
            tags=[],
            metadata={},
        ),
    ]

    results = retrieve(
        query="What does extract_python_docs do?",
        documents=documents,
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].document.symbol_name == "extract_python_docs"
