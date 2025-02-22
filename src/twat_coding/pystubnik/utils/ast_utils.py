#!/usr/bin/env -S uv run
"""AST manipulation utilities."""

import ast
from dataclasses import dataclass
from typing import Any, cast, Union

from loguru import logger


@dataclass(frozen=True)
class TruncationConfig:
    """Configuration for AST literal truncation."""

    max_sequence_length: int = 4  # For lists, dicts, sets, tuples
    max_string_length: int = 17  # For strings except docstrings
    max_docstring_length: int = 150  # Default max length for docstrings
    max_file_size: int = 3_000  # Default max file size before removing all docstrings
    truncation_marker: str = "..."


def truncate_literal(node: ast.AST, config: TruncationConfig) -> ast.AST:
    """Truncate literal values to keep them small in the generated shadow file.

    Args:
        node: AST node to truncate
        config: Truncation configuration

    Returns:
        Truncated AST node
    """
    match node:
        case ast.Constant(value=str() as s):
            # Skip docstrings (handled separately in _preserve_docstring)
            parent = getattr(node, "parent", None)
            parent_parent = getattr(parent, "parent", None)
            if isinstance(parent, ast.Expr) and isinstance(
                parent_parent,
                ast.Module | ast.ClassDef | ast.FunctionDef,
            ):
                return node
            if len(s) <= config.max_string_length:
                return node
            trunc = f"{s[: config.max_string_length]}{config.truncation_marker}"
            return ast.Constant(value=trunc)

        case ast.Constant(value=bytes() as b):
            if len(b) <= config.max_string_length:
                return node
            # For bytes, show partial bytes plus b"..."
            trunc = b"".join([b[: config.max_string_length], b"..."])
            return ast.Constant(value=trunc)

        case ast.List(elts=elts) | ast.Set(elts=elts) | ast.Tuple(elts=elts):
            truncated_elts = []
            for i, e in enumerate(elts):
                if i < config.max_sequence_length:
                    truncated_elts.append(cast(ast.expr, truncate_literal(e, config)))
                else:
                    truncated_elts.append(ast.Constant(value=config.truncation_marker))
                    break
            return type(node)(elts=truncated_elts)

        case ast.Dict(keys=keys, values=values):
            pairs = []
            for i, (k, v) in enumerate(zip(keys, values, strict=False)):
                if i < config.max_sequence_length:
                    new_v = cast(ast.expr, truncate_literal(v, config))
                    pairs.append((k, new_v))
                else:
                    pairs.append(
                        (
                            ast.Constant(value="..."),
                            ast.Constant(value="..."),
                        )
                    )
                    break
            return ast.Dict(
                keys=[k for k, _ in pairs],
                values=[cast(ast.expr, v) for _, v in pairs],
            )

        case _:
            return node


def attach_parents(node: ast.AST) -> None:
    """Attach parent references to all nodes in an AST.

    Args:
        node: Root AST node
    """
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)


def get_docstring(
    node: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module],
) -> str | None:
    """Get docstring from an AST node.

    Args:
        node: AST node to extract docstring from (must be a module, class, or function)

    Returns:
        Docstring if found, None otherwise
    """
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.strip()
    return None


def is_empty_expr(node: ast.AST) -> bool:
    """Check if a node is an empty or whitespace-only expression.

    Args:
        node: AST node to check

    Returns:
        True if node is an empty expression
    """
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and (not node.value.value or str(node.value.value).isspace())
    )
