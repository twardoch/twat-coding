#!/usr/bin/env -S uv run
"""Importance scoring for symbols and code elements."""

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from ..core.types import StubResult
from . import Processor
from .file_importance import FileImportanceConfig, prioritize_files


@dataclass
class ImportanceConfig:
    """Configuration for importance scoring."""

    patterns: dict[str, float] = field(default_factory=dict)
    keywords: set[str] = field(
        default_factory=lambda: {
            "important",
            "critical",
            "essential",
            "main",
            "key",
        }
    )
    min_score: float = 0.5
    docstring_weight: float = 0.01  # Per word in docstring
    public_weight: float = 1.1
    special_weight: float = 1.2

    # File-level importance settings
    file_importance: FileImportanceConfig = field(default_factory=FileImportanceConfig)


class ImportanceProcessor(Processor):
    """Calculate importance scores for code elements."""

    def __init__(self, config: ImportanceConfig | None = None) -> None:
        """Initialize the importance processor.

        Args:
            config: Configuration for importance scoring
        """
        self.config = config or ImportanceConfig()
        self._file_scores: dict[str, float] = {}

    def process(self, stub_result: StubResult) -> StubResult:
        """Process a stub result to calculate importance scores.

        This method combines both symbol-level and file-level importance scoring:
        1. First, it calculates file-level importance if not already done
        2. Then, it adjusts symbol scores based on their containing file's importance
        3. Finally, it applies symbol-specific scoring rules

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result with importance scores
        """
        # Calculate file-level importance if needed
        if not self._file_scores:
            try:
                package_dir = str(stub_result.source_path.parent)
                prioritize_files(package_dir, self.config.file_importance)
            except Exception as e:
                logger.warning(f"Failed to calculate file importance: {e}")

        # Get file importance score
        file_score = self._file_scores.get(str(stub_result.source_path), 0.5)

        # Adjust stub result's importance score
        stub_result.importance_score = file_score

        # Process each symbol in the stub result
        # TODO: Traverse AST to find and score individual symbols
        # For now, we'll just use the file score as a base

        return stub_result

    def calculate_importance(
        self,
        name: str,
        docstring: str | None = None,
        is_public: bool = True,
        is_special: bool = False,
        extra_info: dict[str, Any] | None = None,
    ) -> float:
        """Calculate importance score for a symbol.

        Args:
            name: Symbol name
            docstring: Associated docstring
            is_public: Whether the symbol is public
            is_special: Whether it's a special method
            extra_info: Additional information for scoring

        Returns:
            Importance score between 0 and 1
        """
        try:
            score = 1.0

            # Get file-level base score if available
            if extra_info and "file_path" in extra_info:
                file_path = extra_info["file_path"]
                score *= self._file_scores.get(str(file_path), 1.0)

            # Check against importance patterns
            for pattern, weight in self.config.patterns.items():
                if re.search(pattern, name):
                    score *= weight

            # Docstring-based importance
            if docstring:
                # More detailed docstrings might indicate importance
                word_count = len(docstring.split())
                score *= 1 + (word_count * self.config.docstring_weight)

                # Check for specific keywords indicating importance
                if any(
                    keyword in docstring.lower() for keyword in self.config.keywords
                ):
                    score *= 1.5

            # Name-based importance
            if is_special:
                score *= (
                    self.config.special_weight
                )  # Special methods are usually important
            elif is_public:
                score *= (
                    self.config.public_weight
                )  # Public methods are usually more important

            # Extra information
            if extra_info:
                # Handle inheritance
                if extra_info.get("is_override"):
                    score *= 1.1  # Overridden methods are often important
                if extra_info.get("is_abstract"):
                    score *= 1.2  # Abstract methods define interfaces

                # Handle usage
                usage_count = extra_info.get("usage_count", 0)
                if usage_count > 0:
                    score *= 1 + (min(usage_count, 10) / 10)  # Cap at 2x for usage

            # Normalize score to 0-1 range
            return min(max(score / 2, 0), 1)  # Divide by 2 since we multiply a lot

        except Exception as e:
            logger.warning(f"Failed to calculate importance for {name}: {e}")
            return 0.5  # Return neutral score on error

    def should_include(
        self,
        name: str,
        score: float | None = None,
        docstring: str | None = None,
        is_public: bool = True,
        is_special: bool = False,
        extra_info: dict[str, Any] | None = None,
    ) -> bool:
        """Determine if a symbol should be included based on importance.

        Args:
            name: Symbol name
            score: Pre-calculated importance score
            docstring: Associated docstring
            is_public: Whether the symbol is public
            is_special: Whether it's a special method
            extra_info: Additional information for scoring

        Returns:
            True if the symbol should be included
        """
        if score is None:
            score = self.calculate_importance(
                name,
                docstring,
                is_public,
                is_special,
                extra_info,
            )
        return score >= self.config.min_score
