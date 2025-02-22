#!/usr/bin/env -S uv run
"""Type system implementation with support for advanced type features."""

import ast
import inspect
import sys
import types
import typing
from dataclasses import dataclass
from typing import (
    Any,
    Annotated,
    Generic,
    Protocol,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from loguru import logger

from ..errors import ErrorCode, StubGenerationError


class TypeInferenceError(StubGenerationError):
    """Error during type inference."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.TYPE_INFERENCE_ERROR,
        details: dict[str, Any] | None = None,
        *,
        source: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Initialize type inference error.

        Args:
            message: Error message
            code: Error code
            details: Additional details
            source: Source code or file
            line_number: Line number
        """
        super().__init__(message, code, details, source=source, line_number=line_number)


@dataclass
class TypeInfo:
    """Information about a type annotation."""

    annotation: Any  # The type annotation itself
    source: str  # Where the type came from (annotation, docstring, inference)
    confidence: float  # Confidence score (0-1)
    metadata: dict[str, Any]  # Additional type metadata


class TypeRegistry:
    """Registry for type information and aliases."""

    def __init__(self) -> None:
        """Initialize the type registry."""
        self._type_aliases: dict[str, Any] = {}
        self._type_vars: dict[str, TypeVar] = {}
        self._protocols: dict[str, type[Protocol]] = {}
        self._type_cache: dict[tuple[Any, str], TypeInfo] = {}

    def register_alias(self, name: str, target: Any) -> None:
        """Register a type alias.

        Args:
            name: Alias name
            target: Target type
        """
        self._type_aliases[name] = target

    def register_type_var(self, name: str, type_var: TypeVar) -> None:
        """Register a type variable.

        Args:
            name: Type variable name
            type_var: Type variable
        """
        self._type_vars[name] = type_var

    def register_protocol(self, protocol_class: type[Protocol]) -> None:
        """Register a Protocol class.

        Args:
            protocol_class: Protocol class to register
        """
        self._protocols[protocol_class.__name__] = protocol_class

    def resolve_type(self, type_hint: Any, context: str = "") -> TypeInfo:
        """Resolve and normalize a type hint.

        Args:
            type_hint: Type hint to resolve
            context: Context for caching

        Returns:
            Resolved type information

        Raises:
            TypeInferenceError: If type resolution fails
        """
        cache_key = (type_hint, context)
        if cache_key in self._type_cache:
            return self._type_cache[cache_key]

        try:
            # Handle type aliases
            if isinstance(type_hint, str) and type_hint in self._type_aliases:
                resolved = self._type_aliases[type_hint]
            else:
                resolved = type_hint

            # Handle Annotated types
            origin = get_origin(resolved)
            if origin is Annotated:
                args = get_args(resolved)
                if not args:
                    raise TypeInferenceError("Empty Annotated type")
                base_type, *metadata = args
                type_info = TypeInfo(
                    annotation=base_type,
                    source="annotation",
                    confidence=1.0,
                    metadata={"annotations": metadata},
                )
            # Handle TypeVar
            elif isinstance(resolved, TypeVar):
                type_info = TypeInfo(
                    annotation=resolved,
                    source="typevar",
                    confidence=1.0,
                    metadata={
                        "name": resolved.__name__,
                        "bound": resolved.__bound__,
                        "constraints": resolved.__constraints__,
                    },
                )
            # Handle Protocol
            elif (
                isinstance(resolved, type)
                and issubclass(resolved, Protocol)
                and resolved is not Protocol
            ):
                type_info = TypeInfo(
                    annotation=resolved,
                    source="protocol",
                    confidence=1.0,
                    metadata={
                        "attributes": {
                            name: get_type_hints(resolved)[name]
                            for name in dir(resolved)
                            if not name.startswith("_")
                        }
                    },
                )
            # Handle generic types
            elif origin is not None:
                args = get_args(resolved)
                type_info = TypeInfo(
                    annotation=resolved,
                    source="generic",
                    confidence=1.0,
                    metadata={
                        "origin": origin,
                        "args": [self.resolve_type(arg).annotation for arg in args],
                    },
                )
            # Handle simple types
            else:
                type_info = TypeInfo(
                    annotation=resolved,
                    source="direct",
                    confidence=1.0,
                    metadata={},
                )

            self._type_cache[cache_key] = type_info
            return type_info

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to resolve type {type_hint}: {e}",
                details={"context": context},
            ) from e

    def merge_types(
        self,
        types: list[TypeInfo],
        *,
        prefer_explicit: bool = True,
    ) -> TypeInfo:
        """Merge multiple type information entries.

        Args:
            types: List of type information to merge
            prefer_explicit: Whether to prefer explicit annotations over inferred ones

        Returns:
            Merged type information

        Raises:
            TypeInferenceError: If type merging fails
        """
        if not types:
            raise TypeInferenceError("No types to merge")
        if len(types) == 1:
            return types[0]

        try:
            # Sort by confidence and source preference
            sorted_types = sorted(
                types,
                key=lambda t: (
                    t.confidence,
                    1 if t.source == "annotation" and prefer_explicit else 0,
                ),
                reverse=True,
            )

            # Use the highest confidence type as base
            base = sorted_types[0]

            # Merge metadata from all types
            merged_metadata = {}
            for type_info in sorted_types:
                merged_metadata.update(type_info.metadata)

            return TypeInfo(
                annotation=base.annotation,
                source=base.source,
                confidence=base.confidence,
                metadata=merged_metadata,
            )

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to merge types: {e}",
                details={"types": [str(t.annotation) for t in types]},
            ) from e


def extract_type_from_docstring(docstring: str) -> TypeInfo | None:
    """Extract type information from a docstring.

    Args:
        docstring: Docstring to parse

    Returns:
        Extracted type information or None if no type found
    """
    # TODO: Implement docstring type extraction
    # This will be implemented in a separate commit
    return None


def infer_type_from_usage(node: ast.AST) -> TypeInfo | None:
    """Infer type information from usage patterns.

    Args:
        node: AST node to analyze

    Returns:
        Inferred type information or None if inference not possible
    """
    # TODO: Implement type inference from usage
    # This will be implemented in a separate commit
    return None
