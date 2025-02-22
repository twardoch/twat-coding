#!/usr/bin/env -S uv run
"""AST manipulation utilities."""

import ast
from dataclasses import dataclass
from typing import cast
from weakref import WeakKeyDictionary

# Global dict to store parent references
_parent_refs: WeakKeyDictionary[ast.AST, ast.AST] = WeakKeyDictionary()


@dataclass(frozen=True)
class TruncationConfig:
    """Configuration for AST literal truncation."""

    max_sequence_length: int = 4  # For lists, dicts, sets, tuples
    max_string_length: int = 17  # For strings except docstrings
    max_docstring_length: int = 150  # Default max length for docstrings
    max_file_size: int = 3_000  # Default max file size before removing all docstrings
    truncation_marker: str = "..."


def _get_parent(node: ast.AST) -> ast.AST | None:
    """Get parent node if it exists.

    Args:
        node: AST node

    Returns:
        Parent node if it exists, None otherwise
    """
    return _parent_refs.get(node)


def _truncate_string(s: str, config: TruncationConfig) -> str:
    """Truncate a string value according to config.

    Args:
        s: String to truncate
        config: Truncation configuration

    Returns:
        Truncated string
    """
    if len(s) <= config.max_string_length:
        return s
    return f"{s[: config.max_string_length]}{config.truncation_marker}"


def _truncate_bytes(b: bytes, config: TruncationConfig) -> bytes:
    """Truncate a bytes value according to config.

    Args:
        b: Bytes to truncate
        config: Truncation configuration

    Returns:
        Truncated bytes
    """
    if len(b) <= config.max_string_length:
        return b
    return b[: config.max_string_length] + b"..."


def _truncate_sequence(
    node: ast.List | ast.Set | ast.Tuple, config: TruncationConfig
) -> ast.AST:
    """Truncate a sequence (list, set, tuple) according to config.

    Args:
        node: AST node representing the sequence
        config: Truncation configuration

    Returns:
        Truncated AST node
    """
    truncated_elts = []
    for i, e in enumerate(node.elts):
        if i < config.max_sequence_length:
            truncated_elts.append(cast(ast.expr, truncate_literal(e, config)))
        else:
            truncated_elts.append(ast.Constant(value=config.truncation_marker))
            break
    return type(node)(elts=truncated_elts)


def _truncate_dict(node: ast.Dict, config: TruncationConfig) -> ast.Dict:
    """Truncate a dictionary according to config.

    Args:
        node: AST node representing the dictionary
        config: Truncation configuration

    Returns:
        Truncated AST node
    """
    pairs = []
    for i, (k, v) in enumerate(zip(node.keys, node.values, strict=False)):
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
            parent = _get_parent(node)
            parent_parent = _get_parent(parent) if parent else None
            if isinstance(parent, ast.Expr) and isinstance(
                parent_parent,
                ast.Module | ast.ClassDef | ast.FunctionDef,
            ):
                return node
            return ast.Constant(value=_truncate_string(s, config))

        case ast.Constant(value=bytes() as b):
            return ast.Constant(value=_truncate_bytes(b, config))

        case ast.List() | ast.Set() | ast.Tuple():
            node_cast = cast(ast.List | ast.Set | ast.Tuple, node)
            return _truncate_sequence(node_cast, config)

        case ast.Dict():
            return _truncate_dict(cast(ast.Dict, node), config)

        case _:
            return node


def attach_parents(node: ast.AST) -> None:
    """Attach parent references to all nodes in an AST.

    Args:
        node: Root AST node
    """
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            _parent_refs[child] = parent


def get_docstring(
    node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module,
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
