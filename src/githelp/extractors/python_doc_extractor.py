from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from githelp.data_models import DocumentRecord


"""
These functions are useful to transform Python code in textual 
documents using ast, usable by the repository.

For example, a processing class PDFProcessor can be represented as:
# Symbol: mmore.process.pdf_processor.PDFProcessor
# Type: class
# Docstring: Processor used to extract text and metadata from PDF files.
# Metadata: {
#    "symbol_type": "class",
#    "relative_path": "process/pdf_processor.py",
#    "project_name": "mmore",
# }

It extracts:
- modules docstrings
- classes docstrings
- function docstrings
- methods docstrings
- functions and methods signatures
- origin file
- some useful metadata
"""


def iter_python_files(base_path: str | Path) -> Iterable[Path]:
    """
    Iterate over all Python files under a base directory.

    Parameters
    ----------
    base_path:
        Root directory to scan.

    Yields
    ------
    Path
        Path to each Python file found recursively.
    """
    base_path = Path(base_path)

    for path in base_path.rglob("*.py"):
        if path.is_file():
            yield path


def _safe_unparse(node: ast.AST | None) -> str | None:
    """
    Convert an AST node back to source-like Python code when possible.

    This is used mainly for type annotations, default argument values, and
    return annotations. If unparsing fails, the function returns None instead
    of interrupting extraction.
    """
    if node is None:
        return None

    try:
        return ast.unparse(node)
    except Exception:
        return None


def _format_arg(arg: ast.arg, default: ast.AST | None = None) -> str:
    """
    Format one function argument with its optional annotation and default value.
    """
    text = arg.arg

    annotation = _safe_unparse(arg.annotation)
    if annotation:
        text += f": {annotation}"

    if default is not None:
        default_text = _safe_unparse(default)
        if default_text:
            text += f" = {default_text}"

    return text


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """
    Build a readable function or method signature from an AST node.

    The implementation handles positional arguments, keyword-only arguments,
    *args, **kwargs, default values, and return annotations.
    """
    args = node.args
    parts: list[str] = []

    posonly = getattr(args, "posonlyargs", [])
    regular = args.args

    defaults = list(args.defaults)
    n_regular_defaults = len(defaults)
    regular_no_defaults = len(regular) - n_regular_defaults

    for arg in posonly:
        parts.append(_format_arg(arg))

    if posonly:
        parts.append("/")

    for i, arg in enumerate(regular):
        default = None
        if i >= regular_no_defaults:
            default = defaults[i - regular_no_defaults]

        parts.append(_format_arg(arg, default))

    if args.vararg:
        vararg = f"*{args.vararg.arg}"
        annotation = _safe_unparse(args.vararg.annotation)

        if annotation:
            vararg += f": {annotation}"

        parts.append(vararg)

    elif args.kwonlyargs:
        parts.append("*")

    for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
        parts.append(_format_arg(kwarg, default))

    if args.kwarg:
        kwarg = f"**{args.kwarg.arg}"
        annotation = _safe_unparse(args.kwarg.annotation)

        if annotation:
            kwarg += f": {annotation}"

        parts.append(kwarg)

    returns = _safe_unparse(node.returns)

    signature = f"{node.name}({', '.join(parts)})"
    if returns:
        signature += f" -> {returns}"

    return signature


def _module_name_from_path(
    path: Path,
    base_path: Path,
    package_name: str | None = None,
) -> str:
    """
    Infer a Python module name from a file path.

    Examples
    --------
    If base_path is src/mmore and path is src/mmore/process/pdf_processor.py,
    the inferred module name is process.pdf_processor.

    If package_name="mmore", the inferred module name becomes
    mmore.process.pdf_processor.
    """
    rel = path.relative_to(base_path)
    parts = list(rel.with_suffix("").parts)

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if package_name:
        parts = [package_name, *parts]

    return ".".join(parts)


def _is_public_name(name: str) -> bool:
    """
    Return whether a Python symbol should be considered public.

    By convention, names starting with an underscore are treated as private.
    """
    return not name.startswith("_")


def _build_code_content(
    *,
    full_name: str,
    symbol_type: str,
    docstring: str,
    signature: str | None = None,
    parent_class: str | None = None,
) -> str:
    """
    Build the text content indexed for a Python symbol.

    The content intentionally includes structured information such as the
    symbol name, type, parent class, signature, and docstring. This makes
    retrieval easier because the LLM can see both the natural-language
    documentation and the code context.
    """
    parts: list[str] = [
        f"Symbol: {full_name}",
        f"Type: {symbol_type}",
    ]

    if parent_class:
        parts.append(f"Parent class: {parent_class}")

    if signature:
        parts.append(f"Signature: {signature}")

    parts.extend(
        [
            "",
            "Docstring:",
            docstring.strip(),
        ]
    )

    return "\n".join(parts)


def extract_python_docs_from_file(
    path: str | Path,
    base_path: str | Path,
    package_name: str | None = None,
    project_name: str | None = None,
) -> list[DocumentRecord]:
    """
    Extract documentation records from one Python file.

    This function parses the file with Python's ast module and extracts
    documentation from:
    - module-level docstrings;
    - class docstrings;
    - method docstrings;
    - function docstrings.

    Only symbols with docstrings are converted into DocumentRecord objects.

    Parameters
    ----------
    path:
        Python file to parse.
    base_path:
        Root source directory. It is used to compute relative paths and module
        names.
    package_name:
        Optional package prefix to add to inferred module names.
    project_name:
        Optional project name stored in metadata.

    Returns
    -------
    list[DocumentRecord]
        Documentation records extracted from the file.
    """
    path = Path(path)
    base_path = Path(base_path)

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    module_name = _module_name_from_path(path, base_path, package_name=package_name)
    rel_path = str(path.relative_to(base_path))

    common_metadata = {
        "relative_path": rel_path,
        "project_name": project_name,
    }

    documents: list[DocumentRecord] = []

    module_docstring = ast.get_docstring(tree)
    if module_docstring:
        documents.append(
            DocumentRecord(
                doc_id=f"code::{module_name}",
                content=_build_code_content(
                    full_name=module_name,
                    symbol_type="module",
                    docstring=module_docstring,
                ),
                source_type="python_module",
                title=module_name,
                file_path=str(path),
                module_name=module_name,
                symbol_name=None,
                signature=None,
                metadata={
                    **common_metadata,
                    "symbol_type": "module",
                },
            )
        )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            full_class_name = f"{module_name}.{class_name}"
            class_docstring = ast.get_docstring(node)

            if class_docstring:
                documents.append(
                    DocumentRecord(
                        doc_id=f"code::{full_class_name}",
                        content=_build_code_content(
                            full_name=full_class_name,
                            symbol_type="class",
                            docstring=class_docstring,
                        ),
                        source_type="python_class",
                        title=full_class_name,
                        file_path=str(path),
                        module_name=module_name,
                        symbol_name=class_name,
                        signature=None,
                        metadata={
                            **common_metadata,
                            "symbol_type": "class",
                            "is_public": _is_public_name(class_name),
                        },
                    )
                )

            for child in node.body:
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                method_name = child.name
                method_docstring = ast.get_docstring(child)

                if not method_docstring:
                    continue

                full_method_name = f"{full_class_name}.{method_name}"
                signature = _build_signature(child)

                documents.append(
                    DocumentRecord(
                        doc_id=f"code::{full_method_name}",
                        content=_build_code_content(
                            full_name=full_method_name,
                            symbol_type="method",
                            signature=signature,
                            docstring=method_docstring,
                            parent_class=class_name,
                        ),
                        source_type="python_method",
                        title=full_method_name,
                        file_path=str(path),
                        module_name=module_name,
                        symbol_name=method_name,
                        signature=signature,
                        metadata={
                            **common_metadata,
                            "symbol_type": "method",
                            "parent_class": class_name,
                            "is_public": _is_public_name(method_name),
                        },
                    )
                )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_name = node.name
            function_docstring = ast.get_docstring(node)

            if not function_docstring:
                continue

            full_function_name = f"{module_name}.{function_name}"
            signature = _build_signature(node)

            documents.append(
                DocumentRecord(
                    doc_id=f"code::{full_function_name}",
                    content=_build_code_content(
                        full_name=full_function_name,
                        symbol_type="function",
                        signature=signature,
                        docstring=function_docstring,
                    ),
                    source_type="python_function",
                    title=full_function_name,
                    file_path=str(path),
                    module_name=module_name,
                    symbol_name=function_name,
                    signature=signature,
                    metadata={
                        **common_metadata,
                        "symbol_type": "function",
                        "is_public": _is_public_name(function_name),
                    },
                )
            )

    return documents


def extract_python_docs(
    base_path: str | Path,
    package_name: str | None = None,
    project_name: str | None = None,
) -> list[DocumentRecord]:
    """
    Extract Python documentation records from all Python files in a directory.

    Files are parsed recursively. Files with syntax errors are skipped for now
    so that one broken file does not stop the whole extraction pipeline.

    Parameters
    ----------
    base_path:
        Root directory containing Python source files.
    package_name:
        Optional package prefix used to build fully qualified module names.
    project_name:
        Optional project name stored in each record metadata.

    Returns
    -------
    list[DocumentRecord]
        All extracted Python documentation records.
    """
    base_path = Path(base_path)
    documents: list[DocumentRecord] = []

    for path in iter_python_files(base_path):
        try:
            documents.extend(
                extract_python_docs_from_file(
                    path=path,
                    base_path=base_path,
                    package_name=package_name,
                    project_name=project_name,
                )
            )
        except SyntaxError:
            # Some files may use unsupported or invalid syntax.
            # For the prototype, we skip them instead of stopping the pipeline.
            continue

    return documents