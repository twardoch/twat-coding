"""Docstring processing for stub generation."""

import ast
from dataclasses import dataclass
from typing import Any, Sequence

from docstring_parser import parse as parse_docstring
from docstring_parser.common import DocstringParam, DocstringReturns, DocstringStyle
from loguru import logger
from mypy.stubdoc import FunctionSig, infer_sig_from_docstring, parse_all_signatures

from pystubnik.core.types import StubResult
from pystubnik.processors import Processor
from ..errors import TypeInferenceError
from ..types.type_system import TypeInfo


@dataclass
class DocstringResult:
    """Result of docstring processing."""

    docstring: str | None
    signatures: list[FunctionSig]
    param_types: dict[str, TypeInfo]
    return_type: TypeInfo | None
    yield_type: TypeInfo | None
    raises: list[tuple[TypeInfo, str]]  # (exception_type, description)


class DocstringProcessor(Processor):
    """Processor for handling docstrings in stub generation."""

    def __init__(
        self,
        max_length: int = 500,
        include_docstrings: bool = True,
        doc_format: Literal["google", "numpy", "rest"] = "google",
        doc_dir: str | None = None,
    ) -> None:
        """Initialize the docstring processor.

        Args:
            max_length: Maximum length for included docstrings
            include_docstrings: Whether to include docstrings in output
            doc_format: Docstring format to expect
            doc_dir: Path to .rst documentation directory
        """
        self.max_length = max_length
        self.include_docstrings = include_docstrings
        self.doc_format = doc_format
        self.doc_dir = doc_dir

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

    def process_docstring(
        self,
        docstring: str | None,
        context: str = "",
    ) -> DocstringResult:
        """Process docstring to extract type information and signatures.

        Args:
            docstring: Docstring to process
            context: Context for error reporting

        Returns:
            Processed docstring information

        Raises:
            TypeInferenceError: If docstring processing fails
        """
        try:
            if not docstring:
                return DocstringResult(
                    docstring=None,
                    signatures=[],
                    param_types={},
                    return_type=None,
                    yield_type=None,
                    raises=[],
                )

            # Truncate if too long
            if len(docstring) > self.max_length:
                docstring = docstring[: self.max_length] + "..."

            # Try to infer signatures from docstring
            sigs = infer_sig_from_docstring(docstring, context) or []

            # If doc_dir is specified, try to find additional signatures
            if self.doc_dir:
                try:
                    doc_sigs, _ = parse_all_signatures([docstring])
                    sigs.extend(
                        FunctionSig(name=s.name, args=s.args, ret_type=s.ret_type)
                        for s in doc_sigs
                    )
                except Exception as e:
                    logger.debug(f"Failed to parse doc signatures: {e}")

            # Parse docstring for type information
            doc = parse_docstring(docstring)

            # Extract parameter types
            param_types = {}
            for param in doc.params:
                if param.type_name:
                    try:
                        type_info = self._parse_type_string(param.type_name)
                        param_types[param.arg_name] = type_info
                    except TypeInferenceError as e:
                        logger.warning(
                            f"Failed to parse type for parameter {param.arg_name}: {e}"
                        )

            # Extract return type
            return_type = None
            if doc.returns and doc.returns.type_name:
                try:
                    return_type = self._parse_type_string(doc.returns.type_name)
                except TypeInferenceError as e:
                    logger.warning(f"Failed to parse return type: {e}")

            # Extract yield type
            yield_type = None
            if hasattr(doc, "yields") and doc.yields and doc.yields.type_name:
                try:
                    yield_type = self._parse_type_string(doc.yields.type_name)
                except TypeInferenceError as e:
                    logger.warning(f"Failed to parse yield type: {e}")

            # Extract raises information
            raises = []
            for raises_section in doc.raises:
                if raises_section.type_name:
                    try:
                        exc_type = self._parse_type_string(raises_section.type_name)
                        raises.append((exc_type, raises_section.description or ""))
                    except TypeInferenceError as e:
                        logger.warning(
                            f"Failed to parse exception type {raises_section.type_name}: {e}"
                        )

            return DocstringResult(
                docstring=docstring if self.include_docstrings else None,
                signatures=sigs,
                param_types=param_types,
                return_type=return_type,
                yield_type=yield_type,
                raises=raises,
            )

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to process docstring: {e}",
                details={"context": context, "docstring": docstring or ""},
            ) from e

    def _parse_type_string(self, type_str: str) -> TypeInfo:
        """Parse a type string from a docstring.

        Args:
            type_str: Type string to parse

        Returns:
            Parsed type information

        Raises:
            TypeInferenceError: If type string parsing fails
        """
        # TODO: Implement type string parsing
        # This will be implemented in a separate commit
        raise NotImplementedError
