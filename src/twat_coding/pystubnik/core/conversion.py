"""Conversion utilities for configuration types."""

from pathlib import Path

from twat_coding.pystubnik.config import StubConfig
from twat_coding.pystubnik.core.config import (
    Backend,
    PathConfig,
    ProcessingConfig,
    RuntimeConfig,
    StubGenConfig,
)
from twat_coding.pystubnik.core.shared_types import TruncationConfig


def convert_to_stub_gen_config(config: StubConfig | None = None) -> StubGenConfig:
    """Convert a StubConfig to a StubGenConfig.

    Args:
        config: The StubConfig to convert. If None, creates a default configuration.

    Returns:
        A StubGenConfig instance with equivalent settings.

    """
    if config is None:
        return StubGenConfig(
            paths=PathConfig(),
            runtime=RuntimeConfig(),
            processing=ProcessingConfig(),
            truncation=TruncationConfig(),
        )

    # Convert paths
    paths = PathConfig(
        output_dir=config.output_path or Path("out"),
        doc_dir=Path(config.doc_dir) if config.doc_dir else None,
        search_paths=[Path(p) for p in config.search_paths],
        modules=list(config.modules),
        packages=list(config.packages),
        files=[Path(f) for f in config.files],
    )

    # Convert runtime config
    runtime = RuntimeConfig(
        backend=Backend.AST if config.backend == "ast" else Backend.MYPY,
        python_version=config.python_version,
        interpreter=Path(config.interpreter)
        if isinstance(config.interpreter, str)
        else config.interpreter,
        no_import=config.no_import,
        inspect=config.inspect,
        parse_only=config.parse_only,
        ignore_errors=config.ignore_errors,
        verbose=config.verbose,
        quiet=config.quiet,
        parallel=config.parallel,
        max_workers=config.max_workers,
    )

    # Convert processing config
    processing = ProcessingConfig(
        include_docstrings=config.docstring_type_hints,
        include_private=config.include_private,
        include_type_comments=config.include_type_comments,
        infer_property_types=config.infer_property_types,
        export_less=config.export_less,
        importance_patterns=dict(config.importance_patterns),
    )

    # Convert truncation config
    truncation = TruncationConfig(
        max_docstring_length=config.max_docstring_length,
    )

    return StubGenConfig(
        paths=paths,
        runtime=runtime,
        processing=processing,
        truncation=truncation,
    )
