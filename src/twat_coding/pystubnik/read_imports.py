#!/usr/bin/env python3

import ast
from pathlib import Path

import fire


def extract_imports_from_py_code(py_content: str) -> str:
    def extract_imports_ast(py_content: str) -> list[ast.stmt]:
        tree = ast.parse(py_content)
        return [
            node for node in tree.body if isinstance(node, ast.Import | ast.ImportFrom)
        ]

    def ast_to_source(node: ast.Import | ast.ImportFrom) -> str:
        if isinstance(node, ast.Import):
            names = ", ".join(
                alias.name + (" as " + alias.asname if alias.asname else "")
                for alias in node.names
            )
            return f"import {names}"
        if isinstance(node, ast.ImportFrom):
            names = ", ".join(
                alias.name + (" as " + alias.asname if alias.asname else "")
                for alias in node.names
            )
            level = "." * node.level
            module = (
                f"from {level}{node.module or ''} " if node.module else f"from {level}"
            )
            return f"{module}import {names}"
        return ""

    import_nodes = extract_imports_ast(py_content)
    return "\n".join(ast_to_source(node) for node in import_nodes)


def process_py_file(py_file: str | Path):
    pass


if __name__ == "__main__":
    fire.Fire(process_py_file)
