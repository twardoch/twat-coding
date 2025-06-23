"""AST manipulation utilities."""

import ast
from typing import cast
from weakref import WeakKeyDictionary

from twat_coding.pystubnik.core.shared_types import TruncationConfig

# Global dict to store parent references
_parent_refs: WeakKeyDictionary[ast.AST, ast.AST] = WeakKeyDictionary()


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
            truncated_elts.append(cast("ast.expr", truncate_literal(e, config)))
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
            new_v = cast("ast.expr", truncate_literal(v, config))
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
        values=[cast("ast.expr", v) for _, v in pairs],
    )


def truncate_literal(node: ast.AST, config: TruncationConfig) -> ast.AST:
    """Truncate literal values in AST nodes.

    Args:
        node: AST node to process
        config: Truncation configuration

    Returns:
        Processed AST node

    """
    result = node  # Default to returning the original node
    match node:
        case ast.Constant(value=str() as s):
            if len(s) > config.max_string_length:
                result = ast.Constant(
                    value=f"{s[: config.max_string_length]}{config.truncation_marker}"
                )
        case ast.Constant(value=bytes() as b):
            return ast.Constant(value=_truncate_bytes(b, config))

        case ast.List() | ast.Set() | ast.Tuple():
            if len(node.elts) > config.max_sequence_length:
                node.elts = [
                    *node.elts[: config.max_sequence_length],
                    ast.Constant(value=config.truncation_marker),
                ]
                result = node
        case ast.Dict():
            if len(node.keys) > config.max_sequence_length:
                node.keys = [
                    *node.keys[: config.max_sequence_length],
                    ast.Constant(value=config.truncation_marker),
                ]
                node.values = [
                    *node.values[: config.max_sequence_length],
                    ast.Constant(value=config.truncation_marker),
                ]
                result = node
        case _:
            return node

    return result


def attach_parents(node: ast.AST) -> None:
    """Attach parent references to AST nodes.

    Args:
        node: AST node to process

    """
    for child in ast.walk(node):
        for _field, value in ast.iter_fields(child):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        item.parent = child  # type: ignore
            elif isinstance(value, ast.AST):
                value.parent = child  # type: ignore


def get_docstring(node: ast.AST) -> str | None:
    """Get docstring from an AST node.

    Args:
        node: AST node to process

    Returns:
        Docstring if found, None otherwise

    """
    match node:
        case ast.Module() | ast.ClassDef() | ast.FunctionDef():
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                return node.body[0].value.value
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


def should_include_member(name: str, include_private: bool) -> bool:
    """Check if a member should be included in the stub.

    Args:
        name: Name of the member
        include_private: Whether to include private members

    Returns:
        True if the member should be included

    """
    # If include_private is True, include everything
    if include_private:
        return True

    # Always include special methods (dunder methods)
    if name.startswith("__") and name.endswith("__"):
        return True

    # Exclude anything that starts with underscore
    return not name.startswith("_")
