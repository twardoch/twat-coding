"""Docstring type extraction and processing."""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, ClassVar

from docstring_parser import parse as parse_docstring
from loguru import logger

from twat_coding.pystubnik.core.types import ArgInfo
from twat_coding.pystubnik.types.type_system import (
    TypeInferenceError,
    TypeInfo,
    TypeRegistry,
)


class DocstringStyle(Enum):
    """Docstring style."""

    GOOGLE = auto()
    NUMPY = auto()
    SPHINX = auto()
    EPYTEXT = auto()
    UNKNOWN = auto()


@dataclass
class DocstringInfo:
    """Information extracted from a docstring."""

    style: DocstringStyle
    description: str = ""
    args: list[ArgInfo] = field(default_factory=list)
    returns: str = ""
    raises: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    todo: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    version: str = ""
    deprecated: bool = False
    since: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


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

    def _extract_param_types(self, doc: Any) -> dict[str, TypeInfo]:
        """Extract parameter types from docstring."""
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
        return param_types

    def _extract_return_type(self, doc: Any) -> TypeInfo | None:
        """Extract return type from docstring."""
        if doc.returns and doc.returns.type_name:
            try:
                return self._parse_type_string(doc.returns.type_name)
            except TypeInferenceError as e:
                logger.warning(f"Failed to parse return type: {e}")
        return None

    def _extract_yield_type(self, doc: Any) -> TypeInfo | None:
        """Extract yield type from docstring."""
        if hasattr(doc, "yields") and doc.yields and doc.yields.type_name:
            try:
                return self._parse_type_string(doc.yields.type_name)
            except TypeInferenceError as e:
                logger.warning(f"Failed to parse yield type: {e}")
        return None

    def _extract_raises(self, doc: Any) -> list[tuple[TypeInfo, str]]:
        """Extract raises information from docstring."""
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
        return raises

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
        docstring = ast.get_docstring(node)
        if not docstring:
            return None

        # Parse docstring
        doc = parse_docstring(docstring)

        return DocstringTypeInfo(
            param_types=self._extract_param_types(doc),
            return_type=self._extract_return_type(doc),
            yield_type=self._extract_yield_type(doc),
            raises=self._extract_raises(doc),
        )

    def _parse_simple_type(self, type_str: str) -> TypeInfo | None:
        """Parse a simple type string that maps directly to a Python type.

        Args:
            type_str: Type string to parse

        Returns:
            TypeInfo if the type is found in TYPE_MAPPINGS, None otherwise

        """
        if type_str in self.TYPE_MAPPINGS:
            return TypeInfo(
                annotation=self.TYPE_MAPPINGS[type_str],
                source="docstring",
                confidence=0.8,
                metadata={"original": type_str},
            )
        return None

    def _parse_union_type(self, type_str: str) -> TypeInfo | None:
        """Parse a union type string (e.g., "str or None").

        Args:
            type_str: Type string to parse

        Returns:
            TypeInfo for the union type if valid, None otherwise

        Raises:
            TypeInferenceError: If union type parsing fails

        """
        if " or " not in type_str:
            return None

        types = [self._parse_type_string(t.strip()) for t in type_str.split(" or ")]
        if not types:
            raise TypeInferenceError("Empty union type")
        if len(types) == 1:
            return types[0]

        # Create a union of all types
        union_type = types[0].annotation
        for t in types[1:]:
            union_type = union_type | t.annotation
        return TypeInfo(
            annotation=union_type,
            source="docstring",
            confidence=0.7,
            metadata={"original": type_str, "union_types": types},
        )

    def _parse_container_type(self, container: str, content: str) -> TypeInfo | None:
        """Parse a container type like List[str] or Dict[str, int].

        Args:
            container: Container type name
            content: Content type string

        Returns:
            TypeInfo for the container type if valid, None otherwise

        """
        if container.lower() in ("list", "set", "tuple"):
            elem_type = self._parse_type_string(content)
            container_type = self.TYPE_MAPPINGS.get(container.lower(), list)
            return TypeInfo(
                annotation=container_type[elem_type.annotation],  # type: ignore
                source="docstring",
                confidence=0.7,
                metadata={
                    "original": f"{container}[{content}]",
                    "container": container,
                    "element_type": elem_type,
                },
            )
        if container.lower() == "dict":
            key_type, value_type = map(str.strip, content.split(","))
            key_info = self._parse_type_string(key_type)
            value_info = self._parse_type_string(value_type)
            return TypeInfo(
                annotation=dict[Any, Any],  # Using Any as a fallback
                source="docstring",
                confidence=0.7,
                metadata={
                    "original": f"{container}[{content}]",
                    "key_type": key_info,
                    "value_type": value_info,
                },
            )
        return None

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
            type_str = type_str.strip()

            # Try simple type first
            if result := self._parse_simple_type(type_str):
                return result

            # Try union type
            if result := self._parse_union_type(type_str):
                return result

            # Try generic container type
            if match := re.match(r"(\w+)\[(.*)\]", type_str):
                container, content = match.groups()
                if result := self._parse_container_type(container, content):
                    return result

            # Try type alias
            if type_str in self.type_registry._type_aliases:
                return TypeInfo(
                    annotation=self.type_registry._type_aliases[type_str],
                    source="docstring",
                    confidence=0.6,
                    metadata={"original": type_str, "is_alias": True},
                )

            # Fall back to Any
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
