#!/usr/bin/env -S uv run
"""Type inference processor for stub generation."""

import ast
import re
from typing import Any, ClassVar

from loguru import logger

from ..types.type_system import TypeInferenceError, TypeInfo, TypeRegistry


class TypeInferenceProcessor:
    """Processor for inferring types from code analysis."""

    # Common type patterns in variable names
    TYPE_PATTERNS: ClassVar[dict[re.Pattern[str], type]] = {
        re.compile(r"_str$|_string$"): str,
        re.compile(r"_int$|_count$|_index$"): int,
        re.compile(r"_float$|_ratio$|_rate$"): float,
        re.compile(r"_bool$|_flag$|is_|has_|can_"): bool,
        re.compile(r"_list$|_array$"): list,
        re.compile(r"_dict$|_map$"): dict,
        re.compile(r"_set$"): set,
        re.compile(r"_tuple$"): tuple,
    }

    def __init__(
        self,
        type_registry: TypeRegistry | None = None,
        confidence_threshold: float = 0.5,
        infer_from_usage: bool = True,
        infer_from_assignments: bool = True,
        infer_from_returns: bool = True,
        infer_from_defaults: bool = True,
    ) -> None:
        """Initialize the type inference processor.

        Args:
            type_registry: Registry for type resolution
            confidence_threshold: Minimum confidence for inferred types
            infer_from_usage: Whether to infer types from usage patterns
            infer_from_assignments: Whether to infer types from assignments
            infer_from_returns: Whether to infer types from return statements
            infer_from_defaults: Whether to infer types from default values
        """
        self.type_registry = type_registry or TypeRegistry()
        self.confidence_threshold = confidence_threshold
        self.infer_from_usage = infer_from_usage
        self.infer_from_assignments = infer_from_assignments
        self.infer_from_returns = infer_from_returns
        self.infer_from_defaults = infer_from_defaults

    def infer_types(self, node: ast.AST) -> dict[str, TypeInfo]:
        """Infer types for variables and expressions in an AST.

        Args:
            node: AST node to analyze

        Returns:
            Dictionary mapping names to inferred type information

        Raises:
            TypeInferenceError: If type inference fails
        """
        try:
            inferred_types: dict[str, TypeInfo] = {}

            # Collect type information from different sources
            if self.infer_from_assignments:
                self._infer_from_assignments(node, inferred_types)
            if self.infer_from_usage:
                self._infer_from_usage(node, inferred_types)
            if self.infer_from_returns:
                self._infer_from_returns(node, inferred_types)

            # Filter by confidence threshold
            return {
                name: type_info
                for name, type_info in inferred_types.items()
                if type_info.confidence >= self.confidence_threshold
            }

        except Exception as e:
            raise TypeInferenceError(
                f"Failed to infer types: {e}",
                details={"node_type": type(node).__name__},
            ) from e

    def _infer_from_assignments(
        self, node: ast.AST, types: dict[str, TypeInfo]
    ) -> None:
        """Infer types from assignment statements.

        Args:
            node: AST node to analyze
            types: Dictionary to update with inferred types
        """
        for child in ast.walk(node):
            match child:
                case ast.AnnAssign(target=ast.Name(id=name), annotation=annotation):
                    # Handle explicitly annotated assignments
                    try:
                        type_info = self.type_registry.resolve_type(
                            annotation, f"annotation:{name}"
                        )
                        types[name] = type_info
                    except Exception as e:
                        logger.warning(
                            f"Failed to resolve type annotation for {name}: {e}"
                        )

                case ast.Assign(targets=[ast.Name(id=name)], value=value):
                    # Infer from assigned value
                    if self.infer_from_defaults and isinstance(value, ast.Constant):
                        type_info = TypeInfo(
                            annotation=type(value.value),
                            source="default",
                            confidence=0.7,
                            metadata={"value": value.value},
                        )
                        types[name] = type_info

                    # Infer from variable name patterns
                    for pattern, typ in self.TYPE_PATTERNS.items():
                        if pattern.search(name):
                            types[name] = TypeInfo(
                                annotation=typ,
                                source="pattern",
                                confidence=0.6,
                                metadata={"pattern": pattern.pattern},
                            )

    def _infer_from_usage(self, node: ast.AST, types: dict[str, TypeInfo]) -> None:
        """Infer types from usage patterns.

        Args:
            node: AST node to analyze
            types: Dictionary to update with inferred types
        """
        # Track attribute access
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    name = child.value.id
                    # Record attribute access for potential type inference
                    if name not in types:
                        types[name] = TypeInfo(
                            annotation=Any,
                            source="usage",
                            confidence=0.3,
                            metadata={"attributes": {child.attr}},
                        )
                    else:
                        attrs = types[name].metadata.get("attributes", set())
                        attrs.add(child.attr)
                        types[name].metadata["attributes"] = attrs

    def _infer_from_returns(self, node: ast.AST, types: dict[str, TypeInfo]) -> None:
        """Infer return types from return statements.

        Args:
            node: AST node to analyze
            types: Dictionary to update with inferred types
        """
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                return_types = set()
                for return_node in ast.walk(child):
                    if isinstance(return_node, ast.Return) and return_node.value:
                        if isinstance(return_node.value, ast.Constant):
                            return_types.add(type(return_node.value.value))
                        elif isinstance(return_node.value, ast.Name):
                            name = return_node.value.id
                            if name in types:
                                return_types.add(types[name].annotation)

                if return_types:
                    types[child.name] = TypeInfo(
                        annotation=next(iter(return_types))
                        if len(return_types) == 1
                        else Any,
                        source="returns",
                        confidence=0.5,
                        metadata={"return_types": list(return_types)},
                    )
