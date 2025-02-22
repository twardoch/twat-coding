#!/usr/bin/env -S uv run
"""Error handling system for stub generation."""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for stub generation."""

    # AST-related errors (AST*)
    AST_PARSE_ERROR = "AST001"  # Failed to parse Python source
    AST_VISIT_ERROR = "AST002"  # Error during AST node visitation
    AST_TRANSFORM_ERROR = "AST003"  # Error transforming AST to stub

    # Type inference errors (TYPE*)
    TYPE_INFERENCE_ERROR = "TYPE001"  # Failed to infer type
    TYPE_CONFLICT_ERROR = "TYPE002"  # Conflicting type information
    TYPE_VALIDATION_ERROR = "TYPE003"  # Invalid type annotation

    # Configuration errors (CFG*)
    CONFIG_PARSE_ERROR = "CFG001"  # Failed to parse configuration
    CONFIG_VALIDATION_ERROR = "CFG002"  # Invalid configuration
    CONFIG_IO_ERROR = "CFG003"  # Configuration file I/O error

    # Backend errors (BACKEND*)
    BACKEND_ERROR = "BACKEND001"  # Generic backend error
    BACKEND_NOT_FOUND = "BACKEND002"  # Backend not available
    BACKEND_CONFIG_ERROR = "BACKEND003"  # Backend configuration error

    # I/O errors (IO*)
    IO_READ_ERROR = "IO001"  # Failed to read source file
    IO_WRITE_ERROR = "IO002"  # Failed to write stub file
    IO_PERMISSION_ERROR = "IO003"  # Permission denied

    # Processing errors (PROC*)
    PROC_TIMEOUT_ERROR = "PROC001"  # Processing timeout
    PROC_MEMORY_ERROR = "PROC002"  # Out of memory
    PROC_INTERRUPT_ERROR = "PROC003"  # Processing interrupted


class StubGenerationError(Exception):
    """Base class for all stub generation errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str,
        details: dict[str, Any] | None = None,
        *,
        source: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message
            code: Error code from ErrorCode enum or string
            details: Additional error details
            source: Source code or file where error occurred
            line_number: Line number where error occurred
        """
        self.code = ErrorCode(code) if isinstance(code, str) else code
        self.details = details or {}
        self.source = source
        self.line_number = line_number
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        msg = f"[{self.code}] {super().__str__()}"
        if self.source and self.line_number:
            msg = f"{msg}\nAt {self.source}:{self.line_number}"
        if self.details:
            msg = f"{msg}\nDetails: {self.details}"
        return msg


class ASTError(StubGenerationError):
    """AST processing errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str = ErrorCode.AST_PARSE_ERROR,
        details: dict[str, Any] | None = None,
        *,
        source: str | None = None,
        line_number: int | None = None,
        node_type: str | None = None,
    ) -> None:
        """Initialize AST error.

        Args:
            message: Error message
            code: Error code
            details: Additional details
            source: Source code or file
            line_number: Line number
            node_type: Type of AST node where error occurred
        """
        if node_type:
            details = details or {}
            details["node_type"] = node_type
        super().__init__(message, code, details, source=source, line_number=line_number)


class MyPyError(StubGenerationError):
    """MyPy backend errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str = ErrorCode.BACKEND_ERROR,
        details: dict[str, Any] | None = None,
        *,
        source: str | None = None,
        line_number: int | None = None,
        mypy_error_code: str | None = None,
    ) -> None:
        """Initialize MyPy error.

        Args:
            message: Error message
            code: Error code
            details: Additional details
            source: Source code or file
            line_number: Line number
            mypy_error_code: Original MyPy error code
        """
        if mypy_error_code:
            details = details or {}
            details["mypy_error_code"] = mypy_error_code
        super().__init__(message, code, details, source=source, line_number=line_number)


class ConfigError(StubGenerationError):
    """Configuration errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str = ErrorCode.CONFIG_PARSE_ERROR,
        details: dict[str, Any] | None = None,
        *,
        source: str | None = None,
        config_key: str | None = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            code: Error code
            details: Additional details
            source: Configuration file path
            config_key: Key in configuration that caused error
        """
        if config_key:
            details = details or {}
            details["config_key"] = config_key
        super().__init__(message, code, details, source=source)
