#!/usr/bin/env python3
"""Enhanced MyPy-based stub generator.

Combines MyPy's stubgen with smart stub generation to provide better type information.

This module provides a more sophisticated approach to stub generation by:
1. Using MyPy's stubgen for basic stub generation
2. Enhancing the stubs with smart docstring processing
3. Adding importance-based filtering
4. Proper handling of special cases (dataclasses, properties, etc.)
"""

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple, cast

from loguru import logger
from mypy import stubgen
from mypy.stubdoc import (
    ArgSig,
    FunctionSig,
    infer_sig_from_docstring,
    parse_all_signatures,
)

# Current Python version
pyversion_current = (sys.version_info.major, sys.version_info.minor)

# Optional fire import for CLI
try:
    import fire  # type: ignore
except ImportError:
    fire = None  # type: ignore


class DocSignature(NamedTuple):
    """Signature information extracted from docstring."""

    name: str
    args: list[tuple[str, str | None, str | None]]  # (name, type, default)
    ret_type: str | None


@dataclass
class StubGenConfig:
    """Configuration for stub generation with smart defaults."""

    pyversion: tuple[int, int] = pyversion_current
    no_import: bool = False
    inspect: bool = False
    doc_dir: str = ""
    search_path: Sequence[str | Path] = field(default_factory=list)
    interpreter: str | Path = sys.executable
    ignore_errors: bool = True
    parse_only: bool = False
    include_private: bool = False
    output_dir: str | Path = ""
    modules: Sequence[str] = field(default_factory=list)
    packages: Sequence[str] = field(default_factory=list)
    files: Sequence[str | Path] = field(default_factory=list)
    verbose: bool = False
    quiet: bool = True
    export_less: bool = False
    include_docstrings: bool = True  # Changed default to True
    importance_patterns: dict[str, float] = field(default_factory=dict)
    max_docstring_length: int = 500
    include_type_comments: bool = True
    infer_property_types: bool = True

    def to_stubgen_options(self) -> stubgen.Options:
        """Convert to MyPy's stubgen.Options."""
        return stubgen.Options(
            pyversion=self.pyversion,
            no_import=self.no_import,
            inspect=self.inspect,
            doc_dir=self.doc_dir,
            search_path=[str(p) for p in self.search_path],
            interpreter=str(self.interpreter),
            ignore_errors=self.ignore_errors,
            parse_only=self.parse_only,
            include_private=self.include_private,
            output_dir=str(self.output_dir),
            modules=list(self.modules),
            packages=list(self.packages),
            files=[str(f) for f in self.files],
            verbose=self.verbose,
            quiet=self.quiet,
            export_less=self.export_less,
            include_docstrings=self.include_docstrings,
        )


class SmartStubGenerator:
    """Enhanced stub generator that combines MyPy's stubgen with smart features."""

    def __init__(self, config: StubGenConfig):
        self.config = config
        self.logger = logger.opt(colors=True)

    def _convert_function_sig(self, sig: FunctionSig | tuple[str, str]) -> DocSignature:
        """Convert FunctionSig to DocSignature.

        Args:
            sig: Function signature from mypy.stubdoc

        Returns:
            Converted signature
        """
        if not isinstance(sig, FunctionSig):
            # Handle tuple format from parse_all_signatures
            name, ret_type = sig
            return DocSignature(name=name, args=[], ret_type=ret_type)

        # Handle FunctionSig format from infer_sig_from_docstring
        args: list[tuple[str, str | None, str | None]] = []
        for arg in sig.args:
            if isinstance(arg, ArgSig):
                # ArgSig attributes are dynamically added by mypy
                arg_dict = cast(dict[str, Any], arg.__dict__)
                type_str = arg_dict.get("type_str")
                type_str = None if type_str == "Any" else type_str
                default = arg_dict.get("default")
                default = None if default == "..." else default
                args.append(
                    (
                        arg_dict.get("name", ""),
                        type_str,
                        default,
                    )
                )
            elif isinstance(arg, tuple):
                name, type_str, default = cast(tuple[str, str, str], arg)
                args.append(
                    (
                        name,
                        type_str if type_str != "Any" else None,
                        default if default != "..." else None,
                    )
                )

        return DocSignature(
            name=sig.name,
            args=args,
            ret_type=sig.ret_type if sig.ret_type != "Any" else None,
        )

    def process_docstring(
        self, docstring: str | None
    ) -> tuple[str | None, list[DocSignature]]:
        """Process docstring to extract type information and signatures.

        Args:
            docstring: The docstring to process

        Returns:
            Tuple of (processed docstring, list of extracted signatures)
        """
        if not docstring:
            return None, []

        # Truncate if too long
        if len(docstring) > self.config.max_docstring_length:
            docstring = docstring[: self.config.max_docstring_length] + "..."

        # Try to infer signatures
        sigs: list[DocSignature] = []
        try:
            inferred_sigs = infer_sig_from_docstring(docstring, "") or []
            sigs.extend(self._convert_function_sig(sig) for sig in inferred_sigs)
        except Exception as e:
            self.logger.debug(f"Failed to infer signatures from docstring: {e}")

        # If doc_dir is specified, try to find additional signatures
        if self.config.doc_dir:
            try:
                doc_sigs, _ = parse_all_signatures([docstring])
                sigs.extend(self._convert_function_sig(sig) for sig in doc_sigs)
            except Exception as e:
                self.logger.debug(f"Failed to parse doc signatures: {e}")

        return docstring, sigs

    def calculate_importance(self, name: str, docstring: str | None = None) -> float:
        """Calculate importance score for a symbol."""
        score = 1.0

        # Check against importance patterns
        for pattern, weight in self.config.importance_patterns.items():
            if pattern in name:
                score *= weight

        # Docstring-based importance
        if docstring:
            # More detailed docstrings might indicate importance
            score *= 1 + (len(docstring.split()) / 100)

            # Check for specific keywords indicating importance
            importance_keywords = {"important", "critical", "essential", "main", "key"}
            if any(keyword in docstring.lower() for keyword in importance_keywords):
                score *= 1.5

        # Name-based importance
        if name.startswith("__") and name.endswith("__"):
            score *= 1.2  # Special methods are usually important
        elif not name.startswith("_"):
            score *= 1.1  # Public methods are usually more important

        return score

    def enhance_stub(self, stub_content: str, module_name: str) -> str:
        """Enhance a generated stub with additional information."""
        # TODO: Implement stub enhancement logic
        return stub_content

    def generate_stubs(self) -> None:
        """Generate enhanced stubs using MyPy's stubgen with additional processing."""
        try:
            # First, use MyPy's stubgen
            options = self.config.to_stubgen_options()
            stubgen.generate_stubs(options)

            # Then enhance the stubs (TODO)
            self.logger.info("<green>Successfully generated stubs</green>")

        except Exception as e:
            self.logger.error(f"<red>Failed to generate stubs: {e}</red>")
            if self.config.verbose:
                import traceback

                self.logger.debug(traceback.format_exc())
            if not self.config.ignore_errors:
                raise


def generate_stubs(
    pyversion: tuple[int, int] = pyversion_current,
    no_import: bool = False,
    inspect: bool = False,
    doc_dir: str = "",
    search_path: Sequence[str | Path] = [],
    interpreter: str | Path = sys.executable,
    ignore_errors: bool = True,
    parse_only: bool = False,
    include_private: bool = False,
    output_dir: str | Path = "",
    modules: Sequence[str] = [],
    packages: Sequence[str] = [],
    files: Sequence[str | Path] = [],
    verbose: bool = False,
    quiet: bool = True,
    export_less: bool = False,
    include_docstrings: bool = True,
    importance_patterns: dict[str, float] | None = None,
    max_docstring_length: int = 500,
    include_type_comments: bool = True,
    infer_property_types: bool = True,
) -> None:
    """Generate smart stubs for modules specified in options.

    This is an enhanced version of MyPy's stub generation that adds:
    - Importance-based filtering
    - Smart docstring processing
    - Better type inference
    - Special case handling

    Args:
        pyversion: Python version as (major, minor) tuple
        no_import: Don't import modules, just parse and analyze
        inspect: Import and inspect modules instead of parsing source
        doc_dir: Path to .rst documentation directory
        search_path: List of module search directories
        interpreter: Path to Python interpreter
        ignore_errors: Ignore errors during stub generation
        parse_only: Don't do semantic analysis of source
        include_private: Include private objects in stubs
        output_dir: Directory to write stub files to
        modules: List of module names to generate stubs for
        packages: List of package names to generate stubs for recursively
        files: List of files/directories to generate stubs for
        verbose: Show more detailed output
        quiet: Show minimal output
        export_less: Don't export imported names
        include_docstrings: Include docstrings in stubs
        importance_patterns: Dict of regex patterns to importance scores
        max_docstring_length: Maximum length for included docstrings
        include_type_comments: Include type comments in stubs
        infer_property_types: Try to infer property types from docstrings

    The function will generate .pyi stub files in the specified output_dir.
    """
    config = StubGenConfig(
        pyversion=pyversion,
        no_import=no_import,
        inspect=inspect,
        doc_dir=doc_dir,
        search_path=search_path,
        interpreter=interpreter,
        ignore_errors=ignore_errors,
        parse_only=parse_only,
        include_private=include_private,
        output_dir=output_dir,
        modules=modules,
        packages=packages,
        files=files,
        verbose=verbose,
        quiet=quiet,
        export_less=export_less,
        include_docstrings=include_docstrings,
        importance_patterns=importance_patterns or {},
        max_docstring_length=max_docstring_length,
        include_type_comments=include_type_comments,
        infer_property_types=infer_property_types,
    )

    generator = SmartStubGenerator(config)
    generator.generate_stubs()


if __name__ == "__main__":
    if fire is None:
        print("Error: python-fire package is required to run this script directly")
        sys.exit(1)
    fire.Fire(generate_stubs)
