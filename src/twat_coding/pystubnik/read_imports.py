#!/usr/bin/env python3
"""Extract imports from Python files."""

import ast
from pathlib import Path

import fire


def ast_to_source(node: ast.Import | ast.ImportFrom) -> str:
    """Convert an AST import node to source code.

    Args:
        node: The AST import node

    Returns:
        The source code representation of the import

    """
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
        return f"import {', '.join(names)}"
    if isinstance(node, ast.ImportFrom):
        names = [alias.name for alias in node.names]
        module = node.module or ""
        level = "." * node.level
        return f"from {level}{module} import {', '.join(names)}"
    msg = f"Unexpected node type: {type(node)}"
    raise ValueError(msg)


def extract_imports(source: str) -> list[ast.Import | ast.ImportFrom]:
    """Extract import statements from Python source code.

    Args:
        source: Python source code

    Returns:
        List of import nodes

    """
    tree = ast.parse(source)
    imports: list[ast.Import | ast.ImportFrom] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            imports.append(node)

    return imports


def process_py_file(file_path: str | Path) -> None:
    """Process a Python file to extract imports.

    Args:
        file_path: Path to the Python file

    """
    file_path = Path(file_path)
    source = file_path.read_text()
    imports = extract_imports(source)

    for _node in imports:
        pass


def main() -> None:
    """Main entry point."""
    fire.Fire(process_py_file)


if __name__ == "__main__":
    main()
