"""AST-based stub generation backend.

This module implements stub generation using Python's ast module,
based on the original make_stubs_ast.py implementation.
"""

import ast
from pathlib import Path
from typing import cast

from loguru import logger

from pystubnik.backends import StubBackend
from pystubnik.core.config import PathConfig, StubGenConfig, TruncationConfig
from pystubnik.core.types import StubResult
from pystubnik.core.utils import read_source_file


def truncate_literal(node: ast.AST, config: TruncationConfig) -> ast.AST:
    """Truncate literal values to keep them small in the generated shadow file.

    Args:
        node: AST node to potentially truncate
        config: Truncation configuration

    Returns:
        Potentially truncated AST node
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
            return ast.Constant(value=b[: config.max_string_length])

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
                            ast.Constant(value=config.truncation_marker),
                            ast.Constant(value=config.truncation_marker),
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
    """Transform AST to preserve signatures while truncating implementation details.

    This transformer preserves:
    - imports
    - docstrings (subject to length constraints)
    - function & method signatures
    - class-level assignments
    But replaces function bodies with an ellipsis.
    """

    def __init__(self, config: StubGenConfig, file_size: int = 0):
        super().__init__()
        self.config = config
        self.file_size = file_size

    def _preserve_docstring(self, body: list[ast.stmt]) -> list[ast.stmt]:
        """If the first statement is a docstring, keep it if it meets size constraints.

        Args:
            body: List of statements to check for docstring

        Returns:
            List containing the docstring statement if it should be preserved,
            otherwise an empty list
        """
        if not body:
            return []

        # Skip all docstrings if file is too large
        if self.file_size > self.config.truncation.max_file_size:
            return []

        match body[0]:
            case ast.Expr(value=ast.Constant(value=str() as docstring)):
                # Skip if docstring is too long
                if len(docstring) > self.config.truncation.max_docstring_length:
                    return []
                return [body[0]]
            case _:
                return []

    def _make_ellipsis_expr(self, node: ast.AST, indent: int = 0) -> ast.Expr:
        """Create an ellipsis node with the same location offsets.

        Args:
            node: Node to copy location from
            indent: Additional indentation to add

        Returns:
            Ellipsis expression node
        """
        return ast.Expr(
            value=ast.Constant(value=Ellipsis),
            lineno=getattr(node, "lineno", 1),
            col_offset=getattr(node, "col_offset", 0) + indent,
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Keep function signature and docstring, replace body with ellipsis."""
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
        """Preserve class structure but transform method bodies."""
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
                and (not item.value.value or str(item.value.value).isspace())
            )
            if is_empty_expr:
                continue
            body.append(self.visit(item))

        return ast.Module(body=body, type_ignores=[])

    def generic_visit(self, node: ast.AST) -> ast.AST:
        """Recurse into all child nodes, then apply literal truncation."""
        new_node = super().generic_visit(node)
        return truncate_literal(new_node, self.config.truncation)


class AstBackend(StubBackend):
    """AST-based stub generation backend."""

    def __init__(self, config: StubGenConfig | None = None):
        self.config = config or StubGenConfig(
            paths=PathConfig(
                output_dir=Path("out"),
                doc_dir=None,
                search_paths=[],
                modules=[],
                packages=[],
                files=[],
            )
        )

    def generate_stub(
        self, source_path: Path, output_path: Path | None = None
    ) -> StubResult:
        """Generate stub for the given source file using AST analysis.

        Args:
            source_path: Path to the source file
            output_path: Optional path to write the stub file

        Returns:
            The generated stub content as a string
        """
        try:
            # Read and parse source file
            source, encoding = read_source_file(source_path)
            if not source:
                msg = f"Failed to read source file: {source_path}"
                raise ValueError(msg)

            tree = ast.parse(source)
            file_size = len(source)

            # Add parent references for docstring detection
            def _attach_parents(curr: ast.AST, parent: ast.AST | None = None) -> None:
                for child in ast.iter_child_nodes(curr):
                    child.parent = curr
                    _attach_parents(child, curr)

            _attach_parents(tree)

            # Transform AST to generate stub
            transformed = SignatureExtractor(self.config, file_size).visit(tree)
            stub_content = ast.unparse(transformed)

            # Create stub result
            result = StubResult(
                source_path=source_path,
                stub_content=stub_content,
                imports=[],  # Will be filled by ImportProcessor
                errors=[],
            )

            # Write output if requested
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(stub_content, encoding=encoding or "utf-8")
                logger.debug(f"Wrote stub to {output_path}")

            return result

        except Exception as e:
            logger.error(f"Failed to generate stub for {source_path}: {e}")
            if self.config.runtime.verbose:
                import traceback

                logger.debug(traceback.format_exc())
            if not self.config.runtime.ignore_errors:
                raise
            return StubResult(
                source_path=source_path,
                stub_content="",
                imports=[],
                errors=[str(e)],
            )
