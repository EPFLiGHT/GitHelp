from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from docask.data_models import DocumentRecord


def iter_python_files(base_path: str | Path) -> Iterable[Path]:
    base_path = Path(base_path)
    for path in base_path.rglob("*.py"):
        if path.is_file():
            yield path


def _safe_unparse(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _format_arg(arg: ast.arg, default: ast.AST | None = None) -> str:
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
    args = node.args
    parts: list[str] = []

    posonly = getattr(args, "posonlyargs", [])
    regular = args.args

    defaults = list(args.defaults)
    n_regular_defaults = len(defaults)
    regular_no_defaults = len(regular) - n_regular_defaults

    for i, arg in enumerate(posonly):
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
    rel = path.relative_to(base_path)
    parts = list(rel.with_suffix("").parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]

    if package_name:
        parts = [package_name, *parts]

    return ".".join(parts)


def _is_public_name(name: str) -> bool:
    return not name.startswith("_")


def _build_code_content(
    *,
    full_name: str,
    symbol_type: str,
    docstring: str,
    signature: str | None = None,
    parent_class: str | None = None,
) -> str:
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


def extract_python_docs_from_file(path: str | Path, base_path: str | Path) -> list[DocumentRecord]:
    path = Path(path)
    base_path = Path(base_path)

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    module_name = _module_name_from_path(path, base_path, package_name="mmore")
    rel_path = str(path.relative_to(base_path))

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
                    "relative_path": rel_path,
                    "symbol_type": "module",
                    "project_name": "mmore",
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
                            "relative_path": rel_path,
                            "symbol_type": "class",
                            "project_name": "mmore",
                        },
                    )
                )

            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
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
                                "relative_path": rel_path,
                                "symbol_type": "method",
                                "parent_class": class_name,
                                "is_public": _is_public_name(method_name),
                                "project_name": "mmore",
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
                        "relative_path": rel_path,
                        "symbol_type": "function",
                        "is_public": _is_public_name(function_name),
                        "project_name": "mmore",
                    },
                )
            )

    return documents


def extract_python_docs(base_path: str | Path) -> list[DocumentRecord]:
    base_path = Path(base_path)
    documents: list[DocumentRecord] = []

    for path in iter_python_files(base_path):
        try:
            documents.extend(extract_python_docs_from_file(path, base_path))
        except SyntaxError:
            # skip broken files for now
            continue

    return documents
