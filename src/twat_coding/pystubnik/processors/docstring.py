"""Docstring processing functionality."""

from dataclasses import dataclass
from typing import Literal

from docstring_parser import parse
from docstring_parser.common import DocstringStyle
from loguru import logger

from twat_coding.pystubnik.core.types import (
    ClassInfo,
    FunctionInfo,
    ModuleInfo,
    StubResult,
)
from twat_coding.pystubnik.errors import StubGenerationError
from twat_coding.pystubnik.types.type_system import TypeInfo
from twat_coding.pystubnik.processors import Processor


class TypeInferenceError(StubGenerationError):
    """Error raised when type inference fails."""

    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message, "TYPE001", details)


@dataclass
class DocstringResult:
    """Result of docstring processing."""

    docstring: str | None
    signatures: list[FunctionInfo]
    param_types: dict[str, TypeInfo]
    return_type: TypeInfo | None
    yield_type: TypeInfo | None
    raises: list[tuple[TypeInfo, str]]  # (exception_type, description)


class DocstringProcessor(Processor):
    """Processes docstrings to extract type information and signatures."""

    def __init__(
        self,
        style: Literal["google", "numpy", "rest"] = "google",
        max_length: int | None = None,
        preserve_sections: list[str] | None = None,
    ) -> None:
        """Initialize docstring processor.

        Args:
            style: Docstring style to use for parsing
            max_length: Maximum length for docstrings before truncation
            preserve_sections: List of section names to always preserve

        """
        self.style = DocstringStyle.GOOGLE
        if style == "numpy":
            self.style = DocstringStyle.NUMPYDOC
        elif style == "rest":
            self.style = DocstringStyle.REST

        self.max_length = max_length
        self.preserve_sections = preserve_sections or [
            "Args",
            "Returns",
            "Yields",
            "Raises",
        ]

    def process(self, stub_result: StubResult) -> StubResult:
        """Process docstrings in a stub result.

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result

        """
        logger.debug(f"Processing docstrings for {stub_result.source_path}")

        # Process module docstring
        module_info = self._process_module_docstring(stub_result)

        # Process function docstrings
        for function in module_info.functions:
            self._process_function_docstring(function)

        # Process class docstrings
        for class_info in module_info.classes:
            self._process_class_docstring(class_info)

            # Process method docstrings
            for method in class_info.methods:
                self._process_function_docstring(method)

            # Process property docstrings
            for prop in class_info.properties:
                self._process_function_docstring(prop)

        return stub_result

    def _process_module_docstring(self, stub_result: StubResult) -> ModuleInfo:
        """Process the module-level docstring.

        Args:
            stub_result: The stub generation result

        Returns:
            The processed module info

        """
        logger.debug("Processing module docstring")
        # TODO: Implement module docstring processing
        return ModuleInfo(name="", path=stub_result.source_path)

    def _process_function_docstring(self, function: FunctionInfo) -> None:
        """Process a function or method docstring.

        Args:
            function: The function info to process

        """
        if not function.docstring:
            return

        logger.debug(f"Processing docstring for function {function.name}")

        try:
            docstring = parse(function.docstring, style=self.style)

            # Extract parameter types
            for param in docstring.params:
                if param.type_name:
                    arg = next(
                        (a for a in function.args if a.name == param.arg_name), None
                    )
                    if arg:
                        # Update arg type if found in docstring
                        object.__setattr__(arg, "type", param.type_name)

            # Extract return type
            if docstring.returns and docstring.returns.type_name:
                object.__setattr__(function, "return_type", docstring.returns.type_name)

        except Exception as e:
            logger.warning(f"Failed to parse docstring for {function.name}: {e}")

    def _process_class_docstring(self, class_info: ClassInfo) -> None:
        """Process a class docstring.

        Args:
            class_info: The class info to process

        """
        if not class_info.docstring:
            return

        logger.debug(f"Processing docstring for class {class_info.name}")

        try:
            parse(class_info.docstring, style=self.style)
            # TODO: Extract class-level type information

        except Exception as e:
            logger.warning(f"Failed to parse docstring for {class_info.name}: {e}")
