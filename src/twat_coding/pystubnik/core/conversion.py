#!/usr/bin/env python3
"""Conversion utilities for configuration types."""

from ..config import StubConfig
from .config import PathConfig, RuntimeConfig, StubGenConfig


def convert_to_stub_gen_config(config: StubConfig | None = None) -> StubGenConfig:
    """Convert a StubConfig to a StubGenConfig.

    Args:
        config: The StubConfig to convert. If None, creates a default configuration.

    Returns:
        A StubGenConfig instance with equivalent settings.
    """
    if config is None:
        return StubGenConfig(
            path_config=PathConfig(),
            runtime_config=RuntimeConfig(),
        )

    return StubGenConfig(
        path_config=PathConfig(
            source_path=config.source_path,
            output_path=config.output_path,
            importance_patterns=config.importance_patterns,
        ),
        runtime_config=RuntimeConfig(
            backend=config.backend,
            docstring_style=config.docstring_style,
            importance_level=config.importance_level,
            truncation=config.truncation,
        ),
    )
