#!/usr/bin/env -S uv run
"""Docstring type extraction and processing."""

import ast
import re
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Union, cast

from docstring_parser import parse as parse_docstring
from docstring_parser.common import DocstringParam, DocstringReturns, DocstringStyle
from loguru import logger

from ..types.type_system import TypeInfo, TypeInferenceError, TypeRegistry


@dataclass
class DocstringTypeInfo:
    """Type information extracted from docstrings."""

    param_types: dict[str, TypeInfo]
    return_type: TypeInfo | None
    yield_type: TypeInfo | None
    raises: list[tuple[TypeInfo, str]]  # (exception_type, description)


class DocstringTypeExtractor:
    """Extract type information from docstrings."""

    # Common type mappings for docstring type names
    TYPE_MAPPINGS: ClassVar[dict[str, Any]] = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "None": type(None),
        "any": Any,
        # Add more mappings as needed
    }

    def __init__(self, type_registry: TypeRegistry) -> None:
        """Initialize the docstring type extractor.

        Args:
            type_registry: Type registry for resolving types
        """
        self.type_registry = type_registry
        self._param_pattern = re.compile(
            r":param\s+(\w+)\s*:\s*(?:\(([^)]+)\))?\s*([^\n]+)"
        )
        self._type_pattern = re.compile(r":type\s+(\w+)\s*:\s*([^\n]+)")
        self._rtype_pattern = re.compile(r":rtype:\s*([^\n]+)")
        self._returns_pattern = re.compile(r":returns?:\s*([^\n]+)")
        self._yields_pattern = re.compile(r":yields?:\s*([^\n]+)")
        self._raises_pattern = re.compile(r":raises?\s+([^:]+):\s*([^\n]+)")

    def extract_types(
        self,
        node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module,
    ) -> DocstringTypeInfo | None:
        """Extract type information from an AST node's docstring.

        Args:
            node: AST node to process

        Returns:
            Extracted type information or None if no docstring found

        Raises:
            TypeInferenceError: If docstring parsing fails
        """
        docstring: str | None = None
        try:
            # Get docstring from node
            docstring = ast.get_docstring(node)
            if not docstring:
                return None

            # Parse docstring
            doc = parse_docstring(docstring)

            # Extract parameter types
            param_types = {}
            for param in doc.params:
                if param.type_name:
                    try:
                        type_info = self._parse_type_string(param.type_name)
                        param_types[param.arg_name] = type_info
                    except TypeInferenceError as e:
                        # Log but don't fail for individual parameter errors
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

            return DocstringTypeInfo(
                param_types=param_types,
                return_type=return_type,
                yield_type=yield_type,
                raises=raises,
            )

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to extract types from docstring: {e}",
                details={"docstring": docstring or ""},
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
        try:
            # Clean up type string
            type_str = type_str.strip()

            # Handle simple types
            if type_str in self.TYPE_MAPPINGS:
                return TypeInfo(
                    annotation=self.TYPE_MAPPINGS[type_str],
                    source="docstring",
                    confidence=0.8,
                    metadata={"original": type_str},
                )

            # Handle union types (e.g., "str or None")
            if " or " in type_str:
                types = [
                    self._parse_type_string(t.strip()) for t in type_str.split(" or ")
                ]
                if not types:
                    raise TypeInferenceError("Empty union type")
                if len(types) == 1:
                    return types[0]
                return TypeInfo(
                    annotation=Union[tuple(t.annotation for t in types)],  # type: ignore
                    source="docstring",
                    confidence=0.7,
                    metadata={"original": type_str, "union_types": types},
                )

            # Handle generic types (e.g., "List[str]")
            match = re.match(r"(\w+)\[(.*)\]", type_str)
            if match:
                container, content = match.groups()
                if container.lower() in ("list", "set", "tuple"):
                    elem_type = self._parse_type_string(content)
                    container_type = self.TYPE_MAPPINGS.get(container.lower(), list)
                    return TypeInfo(
                        annotation=container_type[elem_type.annotation],  # type: ignore
                        source="docstring",
                        confidence=0.7,
                        metadata={
                            "original": type_str,
                            "container": container,
                            "element_type": elem_type,
                        },
                    )
                elif container.lower() == "dict":
                    key_type, value_type = map(str.strip, content.split(","))
                    key_info = self._parse_type_string(key_type)
                    value_info = self._parse_type_string(value_type)
                    return TypeInfo(
                        annotation=dict[
                            cast(type, key_info.annotation),
                            cast(type, value_info.annotation),
                        ],
                        source="docstring",
                        confidence=0.7,
                        metadata={
                            "original": type_str,
                            "key_type": key_info,
                            "value_type": value_info,
                        },
                    )

            # Try to resolve as a type alias or fall back to Any
            if type_str in self.type_registry._type_aliases:
                return TypeInfo(
                    annotation=self.type_registry._type_aliases[type_str],
                    source="docstring",
                    confidence=0.6,
                    metadata={"original": type_str, "is_alias": True},
                )

            # If all else fails, return Any with low confidence
            return TypeInfo(
                annotation=Any,
                source="docstring",
                confidence=0.1,
                metadata={"original": type_str, "unresolved": True},
            )

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to parse type string '{type_str}': {e}"
            ) from e
