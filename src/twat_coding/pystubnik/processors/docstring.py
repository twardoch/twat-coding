"""Docstring processing for stub generation."""

import ast

from pystubnik.core.types import StubResult
from pystubnik.processors import Processor


class DocstringProcessor(Processor):
    """Processor for handling docstrings in stub generation."""

    def __init__(self, include_docstrings: bool = True, doc_format: str = "plain"):
        self.include_docstrings = include_docstrings
        self.doc_format = doc_format

    def process(self, stub_result: StubResult) -> StubResult:
        """Process docstrings in the stub result.

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result with modified docstrings
        """
        if not self.include_docstrings:
            # Remove all docstrings from the stub content
            tree = ast.parse(stub_result.stub_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef):
                    node.body = [
                        n
                        for n in node.body
                        if not isinstance(n, ast.Expr)
                        or not isinstance(n.value, ast.Str)
                    ]
            stub_result.stub_content = ast.unparse(tree)
        elif self.doc_format != "plain":
            # TODO: Implement docstring format conversion (e.g., Google style to NumPy style)
            pass

        return stub_result

    def _format_docstring(self, docstring: str | None) -> str | None:
        """Format a docstring according to the configured format.

        Args:
            docstring: The docstring to format

        Returns:
            The formatted docstring
        """
        if not docstring:
            return None

        # TODO: Implement docstring format conversion
        return docstring
