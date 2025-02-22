"""Shared types for pystubnik."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TruncationConfig:
    """Configuration for code truncation."""

    max_sequence_length: int = 4  # For lists, dicts, sets, tuples
    max_string_length: int = 17  # For strings except docstrings
    max_docstring_length: int = 150  # Default max length for docstrings
    max_file_size: int = 3_000  # Default max file size before removing all docstrings
    truncation_marker: str = "..."
