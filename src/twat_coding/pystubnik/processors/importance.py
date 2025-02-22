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

    def _get_file_score(self, extra_info: dict[str, Any] | None) -> float:
        """Get the file-level base score."""
        if extra_info and "file_path" in extra_info:
            file_path = extra_info["file_path"]
            return self._file_scores.get(str(file_path), 1.0)
        return 1.0

    def _calculate_pattern_score(self, name: str) -> float:
        """Calculate score based on importance patterns."""
        score = 1.0
        for pattern, weight in self.config.patterns.items():
            if re.search(pattern, name):
                score *= weight
        return score

    def _calculate_docstring_score(self, docstring: str | None) -> float:
        """Calculate score based on docstring quality."""
        if not docstring:
            return 1.0

        score = 1.0
        word_count = len(docstring.split())
        score += word_count * self.config.docstring_weight

        # Check for importance keywords
        for keyword in self.config.keywords:
            if keyword.lower() in docstring.lower():
                score *= 1.1  # Small boost for each importance keyword

        return score

    def _calculate_visibility_score(self, is_public: bool, is_special: bool) -> float:
        """Calculate score based on symbol visibility."""
        score = 1.0
        if is_public:
            score *= self.config.public_weight
        if is_special:
            score *= self.config.special_weight
        return score

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
            # Calculate component scores
            file_score = self._get_file_score(extra_info)
            pattern_score = self._calculate_pattern_score(name)
            docstring_score = self._calculate_docstring_score(docstring)
            visibility_score = self._calculate_visibility_score(is_public, is_special)

            # Combine scores
            final_score = (
                file_score * pattern_score * docstring_score * visibility_score
            )

            # Ensure score is between 0 and 1
            return max(min(final_score, 1.0), 0.0)

        except Exception as e:
            logger.warning(f"Error calculating importance for {name}: {e}")
            return self.config.min_score

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
