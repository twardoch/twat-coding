#!/usr/bin/env python3
"""
Generate shadow Python files containing only signatures and imports,
while truncating large literal strings, bytes, lists, dicts, etc.
"""

import ast
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from loguru import logger
from pydantic import BaseModel
from rich.console import Console

# Constants
MAX_WORKERS = os.cpu_count() or 1
MAX_SEQUENCE_LENGTH: int = 4  # For lists, dicts, sets, tuples
MAX_STRING_LENGTH: int = 17  # For strings except docstrings
MAX_DOCSTRING_LENGTH: int = 150  # Default max length for docstrings
MAX_FILE_SIZE: int = 3_000  # Default max file size before removing all docstrings
TRUNCATION_MARKER: str = "..."

console = Console()


@dataclass(frozen=True)
class Config:
    """Configuration settings."""

    max_sequence_length: int = MAX_SEQUENCE_LENGTH
    max_string_length: int = MAX_STRING_LENGTH
    max_docstring_length: int = MAX_DOCSTRING_LENGTH
    max_file_size: int = MAX_FILE_SIZE
    truncation_marker: str = TRUNCATION_MARKER


class FileLocations(BaseModel):
    """File locations for shadow file generation."""

    py_path: Path
    in_dir: Path
    out_dir: Path

    class Config:
        arbitrary_types_allowed = True

    @property
    def output_path(self) -> Path:
        """Calculate output path based on input path and bases."""
        rel_path = self.py_path.relative_to(self.in_dir)
        return self.out_dir / rel_path

    def check_paths(self) -> None:
        """Validate file locations and create output directories."""
        if not self.py_path.exists():
            msg = f"Input file not found: {self.py_path}"
            raise FileNotFoundError(msg)
        if not self.py_path.is_relative_to(self.in_dir):
            base = self.in_dir
            msg = f"Input file {self.py_path} is not within base {base}"
            raise ValueError(msg)

        # Create output directory and verify permissions
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        if not os.access(self.output_path.parent, os.W_OK):
            msg = f"No write permission: {self.output_path.parent}"
            raise PermissionError(msg)


def truncate_literal(node: ast.AST, config: Config) -> ast.AST:
    """Truncate literal values to keep them small in the generated shadow file."""
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
            trunc = bytes(b[: config.max_string_length]) + b"..."
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


class SignatureExtractor(ast.NodeTransformer):
    """
    Transform AST to preserve:
      - imports
      - docstrings (subject to length constraints)
      - function & method signatures
      - class-level assignments
    But replace function bodies with an ellipsis.
    """

    def __init__(self, config: Config, file_size: int = 0):
        super().__init__()
        self.config = config
        self.file_size = file_size

    def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """
        If the first statement is a docstring, keep it if it meets size constraints.
        Return that docstring statement (list of 1) or an empty list.
        """
        if not body:
            return []

        # Skip all docstrings if file is too large
        if self.file_size > self.config.max_file_size:
            return []

        match body[0]:
            case ast.Expr(value=ast.Constant(value=str() as docstring)):
                # Skip if docstring is too long
                if len(docstring) > self.config.max_docstring_length:
                    return []
                return [body[0]]
            case _:
                return []

    def _make_ellipsis_expr(self, node: ast.AST, indent: int = 0) -> ast.Expr:
        """Create an ellipsis node with the same location offsets."""
        return ast.Expr(
            value=ast.Constant(value=Ellipsis),
            lineno=getattr(node, "lineno", 1),
            col_offset=getattr(node, "col_offset", 0) + indent,
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Keep:
         - function name
         - decorators
         - signature (args, returns)
         - docstring
        Replace body with '...'
        """
        preserved_doc = self._preserve_docstring(node.body)
        ellipsis_body = [self._make_ellipsis_expr(node, indent=4)]
        return ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=preserved_doc + ellipsis_body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_params=[],  # For Python 3.12+
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Preserve:
         - class name
         - decorators
         - docstring
         - definitions inside (methods, nested classes, assignments)
        But transform method bodies to ellipses via visit_FunctionDef.
        """
        preserved_doc = self._preserve_docstring(node.body)
        remainder = node.body[len(preserved_doc) :]
        new_body: list[ast.stmt] = []

        for item in remainder:
            match item:
                case ast.FunctionDef():
                    new_body.append(self.visit_FunctionDef(item))
                case _:
                    # Visit child nodes to truncate large literals
                    new_body.append(self.visit(item))

        return ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=preserved_doc + new_body,
            decorator_list=node.decorator_list,
            type_params=[],  # For Python 3.12+
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process top-level statements."""
        body: list[ast.stmt] = []
        for item in node.body:
            # Skip empty or purely whitespace expressions
            is_empty_expr = (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Constant)
                and (not item.value.value or item.value.value.isspace())
            )
            if is_empty_expr:
                continue
            body.append(self.visit(item))

        return ast.Module(body=body, type_ignores=[])

    def generic_visit(self, node: ast.AST) -> ast.AST:
        """
        Recurse into all child nodes, then apply literal truncation.
        This ensures we handle nested dictionaries, strings, bytes, etc.
        """
        new_node = super().generic_visit(node)
        return truncate_literal(new_node, self.config)


def generate_shadow_file(
    py_path: Path | str,
    in_dir: Path | str,
    out_dir: Path | str,
    config: Config | None = None,
) -> None:
    """Generate a shadow file with signatures, docstrings, and imports."""
    try:
        locations = FileLocations(
            py_path=Path(py_path),
            in_dir=Path(in_dir),
            out_dir=Path(out_dir),
        )
        locations.check_paths()

        config = config or Config()
        source = locations.py_path.read_text(encoding="utf-8")
        file_size = len(source)
        tree = ast.parse(source)

        # Add parent references for docstring detection
        def _attach_parents(curr: ast.AST, parent: ast.AST | None = None) -> None:
            for child in ast.iter_child_nodes(curr):
                child.parent = curr
                _attach_parents(child, curr)

        _attach_parents(tree)

        transformed_tree = SignatureExtractor(config, file_size).visit(tree)

        output_code = ast.unparse(transformed_tree)
        locations.output_path.write_text(output_code, encoding="utf-8")
        logger.debug(f"> {locations.output_path.relative_to(locations.out_dir)}")

    except Exception as exc:
        logger.error(f"Failed to process {py_path}: {exc!s}")
        raise


def process_directory(
    input_dir: Path | str,
    in_dir: Path | str,
    out_dir: Path | str,
    config: Config | None = None,
) -> None:
    """
    Recursively process all .py files in the given directory, generating shadow files.
    Builds a sorted structure of relative paths and processes them concurrently.
    Failed files are logged and skipped.
    """
    input_dir = Path(input_dir)
    in_dir = Path(in_dir)

    # Build sorted structure of relative paths
    files = sorted(input_dir.rglob("*.py"))
    [f.relative_to(in_dir) for f in files]
    total = len(files)

    if not total:
        logger.warning(f"No Python files found in {input_dir}")
        return

    logger.debug(f"Found {total} Python files to process")
    config = config or Config()

    # Process files concurrently
    successful_paths = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(generate_shadow_file, f, in_dir, out_dir, config): f
            for f in files
        }

        for future in as_completed(futures):
            file = futures[future]
            try:
                future.result()
                successful_paths.append(file.relative_to(in_dir))
            except Exception as exc:
                logger.error(f"Failed to process {file}: {exc!s}")

    # Print tree structure of processed files
    if successful_paths:
        logger.debug("Successfully processed files:")
        print_file_tree(successful_paths)
    else:
        logger.error("No files were processed successfully")


def print_file_tree(paths: list[Path]) -> None:
    """Print a tree structure of the given file paths."""

    def add_to_tree(tree: dict, components: list[str]) -> None:
        """Add path components to tree structure."""
        if not components:
            return
        head, *tail = components
        if tail:
            tree[head] = tree.get(head, {})
            add_to_tree(tree[head], tail)
        else:
            tree[head] = None

    def print_tree(tree: dict, prefix: str = "", is_last: bool = True) -> None:
        """Print the tree structure recursively."""
        items = list(tree.items())
        for i, (_name, subtree) in enumerate(items):
            is_last_item = i == len(items) - 1
            if subtree is not None:
                extension = "    " if is_last_item else "│   "
                print_tree(subtree, prefix + extension, is_last_item)

    # Build tree structure
    tree: dict[str, Any] = {}
    for path in sorted(paths):
        components = str(path).split("/")
        add_to_tree(tree, components)

    # Print root and tree
    print_tree(tree)


def cli(
    in_dir: str | Path,
    out_dir: str | Path,
    py_path: str | Path | None = None,
    verbose: bool = False,
) -> None:
    """
    Generate shadow Python files (signatures, imports, docstrings),
    truncating large literals. Writes files to the corresponding
    directory under out_dir.
    """
    logger.remove()
    logger.add(
        console.out,
        format="<blue>{level}</blue> {message}",
        level="DEBUG" if verbose else "INFO",
    )

    try:
        config = Config()
        if py_path is not None:
            path = Path(py_path)
            if path.is_dir():
                process_directory(path, in_dir, out_dir, config)
            else:
                generate_shadow_file(path, in_dir, out_dir, config)
        else:
            process_directory(in_dir, in_dir, out_dir, config)

    except Exception as exc:
        logger.error(f"Application error: {exc!s}")
        raise


if __name__ == "__main__":
    try:
        import fire

        fire.Fire(cli)
    except ImportError:
        logger.error("Please install python-fire: pip install fire")
