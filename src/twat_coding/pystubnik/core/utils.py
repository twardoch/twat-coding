"""Utility functions for pystubnik."""

import ast
import os
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TypeVar

from loguru import logger

T = TypeVar("T")
U = TypeVar("U")


def process_parallel(
    items: Iterable[T],
    process_func: Callable[[T], U],
    max_workers: int | None = None,
    desc: str = "",
) -> list[U]:
    """Process items in parallel using ThreadPoolExecutor.

    Args:
        items: Items to process
        process_func: Function to process each item
        max_workers: Maximum number of worker threads
        desc: Description for progress reporting

    Returns:
        List of processed results

    """
    if max_workers is None:
        max_workers = os.cpu_count() or 1

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_func, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                results.append(result)
                if desc:
                    logger.debug(f"{desc}: Processed {item}")
            except Exception as e:
                logger.error(f"Failed to process {item}: {e}")
                if not isinstance(e, KeyboardInterrupt):
                    logger.debug(f"Error details: {type(e).__name__}: {e}")
                else:
                    raise
    return results


def find_python_files(
    path: Path | str,
    exclude_patterns: Sequence[str] = (".*", "*_test.py", "test_*.py"),
) -> list[Path]:
    """Find Python files in directory recursively.

    Args:
        path: Directory to search
        exclude_patterns: Glob patterns to exclude

    Returns:
        List of Python file paths

    """
    path = Path(path)
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise FileNotFoundError(msg)

    def is_excluded(p: Path) -> bool:
        return any(p.match(pattern) for pattern in exclude_patterns)

    if path.is_file():
        return [path] if path.suffix == ".py" and not is_excluded(path) else []

    result = []
    for root, _, files in os.walk(path):
        root_path = Path(root)
        if is_excluded(root_path):
            continue
        for file in files:
            file_path = root_path / file
            if file_path.suffix == ".py" and not is_excluded(file_path):
                result.append(file_path)
    return sorted(result)


def normalize_docstring(docstring: str | None) -> str | None:
    """Normalize a docstring by fixing indentation and removing redundant whitespace.

    Args:
        docstring: Raw docstring

    Returns:
        Normalized docstring or None if input is None

    """
    if not docstring:
        return None

    # Remove common leading whitespace from every line
    lines = docstring.expandtabs().splitlines()

    # Find minimum indentation (first line doesn't count)
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))

    # Remove indentation (but don't strip first line)
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())

    # Strip trailing empty lines
    while trimmed and not trimmed[-1]:
        trimmed.pop()

    # Return normalized docstring
    return "\n".join(trimmed)


def get_qualified_name(node: ast.AST) -> str:
    """Get qualified name from an AST node.

    Args:
        node: AST node (typically Name or Attribute)

    Returns:
        Qualified name as string

    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{get_qualified_name(node.value)}.{node.attr}"
    return ""


def parse_type_string(type_str: str) -> str:
    """Parse and normalize a type string.

    Args:
        type_str: Type string to parse

    Returns:
        Normalized type string

    """
    # Remove redundant spaces
    type_str = re.sub(r"\s+", " ", type_str.strip())

    # Handle union types (both new and old syntax)
    type_str = re.sub(r"Union\[(.*?)\]", r"(\1)", type_str)
    type_str = re.sub(r"\s*\|\s*", " | ", type_str)

    # Handle optional types
    type_str = re.sub(r"Optional\[(.*?)\]", r"\1 | None", type_str)

    # Normalize nested brackets
    depth = 0
    result = []
    for char in type_str:
        if char == "[":
            if depth > 0:
                result.append(" ")
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == "," and depth > 0:
            result.append(", ")
            continue
        result.append(char)

    return "".join(result)


class ImportTracker:
    """Track and manage imports in a module."""

    def __init__(self) -> None:
        self.imports: dict[str, set[str]] = {}  # module -> names
        self.import_froms: dict[
            str, dict[str, str | None]
        ] = {}  # module -> {name -> alias}
        self.explicit_imports: set[str] = set()  # Explicitly requested imports

    def add_import(self, module: str, name: str | None = None) -> None:
        """Add an import."""
        if name:
            self.imports.setdefault(module, set()).add(name)
        else:
            self.imports.setdefault(module, set())
        self.explicit_imports.add(module)

    def add_import_from(
        self, module: str, names: Sequence[tuple[str, str | None]]
    ) -> None:
        """Add a from-import."""
        self.import_froms.setdefault(module, {}).update(dict(names))

    def get_import_lines(self) -> list[str]:
        """Get sorted import lines."""
        lines = []

        # Regular imports
        for module in sorted(self.imports):
            names = sorted(self.imports[module])
            if names:
                items = ", ".join(names)
                lines.append(f"from {module} import {items}")
            else:
                lines.append(f"import {module}")

        # From-imports
        for module in sorted(self.import_froms):
            name_map = self.import_froms[module]
            if name_map:
                items = ", ".join(
                    f"{name} as {alias}" if alias else name
                    for name, alias in sorted(name_map.items())
                )
                lines.append(f"from {module} import {items}")

        return lines


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the package."""
    logger.remove()  # Remove default handler
    logger.add(
        lambda msg: print(msg),
        level=level,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


def read_source_file(path: str | Path) -> tuple[str, str | None]:
    """Read a Python source file and detect its encoding.

    Args:
        path: Path to the source file

    Returns:
        Tuple of (source_code, encoding)

    """
    path = Path(path)
    try:
        with path.open("rb") as f:
            source = f.read()

        # Try to detect encoding from first two lines
        encoding = "utf-8"  # default
        for line in source.split(b"\n")[:2]:
            if line.startswith(b"#") and b"coding:" in line:
                encoding = line.split(b"coding:")[-1].strip().decode("ascii")
                break

        return source.decode(encoding), encoding
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return "", None


def parse_source(source: str) -> ast.AST | None:
    """Parse Python source code into an AST.

    Args:
        source: Python source code string

    Returns:
        AST if parsing successful, None otherwise

    """
    try:
        return ast.parse(source)
    except SyntaxError as e:
        logger.error(f"Failed to parse source: {e}")
        return None


def normalize_path(path: str | Path) -> Path:
    """Normalize a path to an absolute Path object.

    Args:
        path: Path-like object to normalize

    Returns:
        Normalized absolute Path

    """
    return Path(path).resolve()
