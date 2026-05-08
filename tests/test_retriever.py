from docask.data_models import DocumentRecord
from docask.retrieval.base import RetrievalResult
from docask.retrieval.simple_retriever import retrieve


def test_simple_retriever_returns_retrieval_results():
    documents = [
        DocumentRecord(
            doc_id="doc::install",
            content="This document explains how to install the package.",
            source_type="markdown_section",
            title="Installation",
            file_path="docs/install.md",
            section_title="Installation",
            module_name=None,
            symbol_name=None,
            signature=None,
            language="en",
            tags=[],
            metadata={},
        ),
        DocumentRecord(
            doc_id="doc::streamlit",
            content="This document explains how to run the Streamlit application.",
            source_type="markdown_section",
            title="Streamlit app",
            file_path="docs/app.md",
            section_title="Usage",
            module_name=None,
            symbol_name=None,
            signature=None,
            language="en",
            tags=[],
            metadata={},
        ),
    ]

    results = retrieve(
        query="How do I install the package?",
        documents=documents,
        top_k=1,
    )

    assert len(results) == 1
    assert isinstance(results[0], RetrievalResult)
    assert results[0].document.doc_id == "doc::install"
    assert results[0].score > 0