#!/usr/bin/env -S uv run
"""Importance scoring for symbols and code elements."""

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


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


class ImportanceProcessor:
    """Calculate importance scores for code elements."""

    def __init__(self, config: ImportanceConfig | None = None) -> None:
        """Initialize the importance processor.

        Args:
            config: Configuration for importance scoring
        """
        self.config = config or ImportanceConfig()

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
