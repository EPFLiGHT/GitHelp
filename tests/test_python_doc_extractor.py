from pathlib import Path

from docask.extractors.python_doc_extractor import extract_python_docs


def test_extract_python_function_docstring(tmp_path: Path):
    code_dir = tmp_path / "src"
    code_dir.mkdir()

    python_file = code_dir / "example.py"
    python_file.write_text(
        '''
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
''',
        encoding="utf-8",
    )

    documents = extract_python_docs(code_dir)

    assert len(documents) > 0

    function_docs = [doc for doc in documents if doc.source_type == "python_function"]

    assert len(function_docs) == 1
    assert function_docs[0].symbol_name == "add"
    assert "Add two integers" in function_docs[0].content


def test_extract_python_class_and_method_docstrings(tmp_path: Path):
    code_dir = tmp_path / "src"
    code_dir.mkdir()

    python_file = code_dir / "example.py"
    python_file.write_text(
        '''
class Calculator:
    """Simple calculator."""

    def multiply(self, a: int, b: int) -> int:
        """Multiply two integers."""
        return a * b
''',
        encoding="utf-8",
    )

    documents = extract_python_docs(code_dir)

    class_docs = [doc for doc in documents if doc.source_type == "python_class"]
    method_docs = [doc for doc in documents if doc.source_type == "python_method"]

    assert len(class_docs) == 1
    assert class_docs[0].symbol_name == "Calculator"
    assert "Simple calculator" in class_docs[0].content

    assert len(method_docs) == 1
    assert method_docs[0].symbol_name == "multiply"
    assert "Multiply two integers" in method_docs[0].content