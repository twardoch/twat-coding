# twat-coding

[![PyPI version](https://badge.fury.io/py/twat-coding.svg)](https://badge.fury.io/py/twat-coding)
[![Python Version](https://img.shields.io/pypi/pyversions/twat-coding.svg)](https://pypi.org/project/twat-coding/)
[![License](https://img.shields.io/pypi/l/twat-coding.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI/CD Status](https://github.com/twardoch/twat-coding/actions/workflows/push.yml/badge.svg)](https://github.com/twardoch/twat-coding/actions/workflows/push.yml)
[![Coverage Status](https://codecov.io/gh/twardoch/twat-coding/branch/main/graph/badge.svg)](https://codecov.io/gh/twardoch/twat-coding)

**`twat-coding`** is a Python toolkit designed to enhance code understanding, analysis, and manipulation, particularly with Large Language Models (LLMs) in mind. Its primary component, **`pystubnik`**, generates "smart stubs" – intelligent, condensed representations of Python code.

## Rationale: Why `twat-coding` and Smart Stubs?

Modern software development, especially when interfacing with LLMs or analyzing large codebases, requires tools that can distill complex code into more digestible formats. Traditional type stubs (`.pyi` files) often lack crucial information like docstrings or key implementation details, while full source code can be too verbose for efficient processing by LLMs or quick human comprehension.

`twat-coding`, through `pystubnik`, aims to bridge this gap. Smart stubs preserve essential code structure, type hints, docstrings, and even important code snippets, while significantly reducing verbosity. This makes large Python projects more accessible for automated analysis, LLM ingestion, and faster human understanding.

## Who is This For?

*   **Developers using LLMs with code:** Prepare codebases for efficient and effective LLM analysis by reducing token count while retaining critical information.
*   **Engineers and analysts:** Quickly grasp the structure, API, and core logic of large or unfamiliar Python projects.
*   **Teams focused on code quality and documentation:** Generate readable, concise code summaries that can aid in documentation and reviews.
*   **Anyone needing a summarized yet informative view of Python code.**

## Core Features

### `pystubnik`: Smart Stub Generation
`pystubnik` is the flagship tool within `twat-coding`.
*   **Concise & Informative Representations:** Creates "smart stubs" that are an intermediate between full source and traditional `.pyi` stubs.
*   **AST-Based Analysis:** Primarily uses Python's built-in Abstract Syntax Tree (AST) module for precise control over code parsing and transformation. (Future support for other backends like MyPy may enhance type inference).
*   **Intelligent Import Analysis:** Analyzes, organizes, and simplifies import statements, grouping them by type (stdlib, third-party, local).
*   **Configurable Docstring Processing:** Preserves docstrings with options for length truncation and format consistency.
*   **Importance-Based Filtering (Conceptual):** Designed with the idea of future enhancements for importance scoring to retain critical logic and potentially filter out less relevant code sections. Current filtering includes options like excluding private members.
*   **Modern Python Support:** Handles modern Python syntax and features.

### Development Environment & Practices
`twat-coding` is developed using a modern Python stack:
*   **Project & Environment Management:** `hatch` for building, versioning, and managing development environments.
*   **Linting & Formatting:** `ruff` for high-speed linting and code formatting.
*   **Static Type Checking:** `mypy` to ensure type safety.
*   **Testing:** `pytest` for comprehensive unit and integration tests.
*   **Dependency Management:** `uv` for fast package installation and resolution.
*   **Automation:** Pre-commit hooks and GitHub Actions for CI/CD ensure code quality and automate releases.

## Installation

You can install `twat-coding` using `pip` or `uv`.

```bash
# Using pip
pip install twat-coding

# Using uv
uv pip install twat-coding
```

To include all optional dependencies for development and potentially specific features (like different backends if they evolve):
```bash
# Using pip
pip install twat-coding[all]

# Using uv
uv pip install twat-coding[all]
```
(Note: Check `pyproject.toml` for specific extras like `pystubnik` if they are defined for granular feature installation.)

## Usage

### Command-Line Interface (CLI)

The primary way to use `pystubnik` is through its command-line interface, which is also available via the `twat-coding` command (which internally calls `pystubnik`'s CLI functionality).

**Generate stubs for a single file:**
```bash
twat-coding generate path/to/your/file.py --output-path path/to/your/output_stub.pyi
```

**Generate stubs for an entire directory:**
```bash
twat-coding generate-dir path/to/your_package/ --output-dir path/to/stubs_output/
```

**Key Options:**
*   `--output-path` or `--output-dir`: Specify output location.
*   `--config-file`: Path to a TOML configuration file (details on config structure below).
*   Many other options corresponding to the `StubConfig` parameters (see Technical Details below).

For a full list of CLI options and commands, run:
```bash
twat-coding --help
```

### Python API (`StubGenerator`)

You can also use `pystubnik` programmatically for more fine-grained control or integration into other tools.

```python
from pathlib import Path
from twat_coding.pystubnik.processors.stub_generation import StubGenerator
from twat_coding.pystubnik.config import StubConfig
# StubGenConfig is nested and typically part of StubConfig's defaults or customization
# from twat_coding.pystubnik.core.config import StubGenConfig, ProcessingConfig, TruncationConfig # If direct customization is needed

# Path to the Python file you want to process
source_file_path = Path("path/to/your_module.py")
# Desired path for the generated stub file
output_stub_path = Path("path/to/stubs/your_module.pyi")

# Ensure output directory exists
output_stub_path.parent.mkdir(parents=True, exist_ok=True)

# Basic configuration:
# - input_path: The root directory from which 'source_file_path' is considered.
#   Often, this is the project root or a specific source directory.
# - output_path: The root directory where stubs will be placed, mirroring the input structure.
# - files: A list of specific files to process (optional if processing whole directories via CLI).
#   The StubGenerator API for single files primarily needs the source_file path directly.
#   StubConfig is more for directory-level or batch processing configuration.

# Configure the StubGenerator
# For generating a single file programmatically, you often pass a simplified config
# focusing on generation options, as input/output paths are handled more directly.
# The StubConfig class from pystubnik.config is comprehensive.
# Here's an example focusing on a single file generation context:

# This configuration focuses on how the stub for a *single given file* should be generated.
# The StubGenerator itself doesn't require 'input_path' or 'output_path' in its config
# when 'generate_stub' is called with a specific file, as those are implicit.
# However, some settings in StubConfig might still influence its behavior.
# For a more direct approach for a single file, one might initialize StubGenerator
# with a default or minimal StubConfig and rely on its generate_stub method.

# Example of a minimal config for the generator instance:
stub_processing_config = StubConfig(
    input_path=source_file_path.parent, # Dummy or actual parent for context
    # output_path=output_stub_path.parent, # Not directly used by generate_stub's internal logic for output location
    # --- Customize generation parameters as needed ---
    include_private=False, # Example: Exclude private members
    add_header=True,       # Example: Add a "Generated by pystubnik" header
    # To customize StubGenConfig parameters like docstring length:
    # stub_gen_config=StubGenConfig(
    #     processing_config=ProcessingConfig(include_docstrings=True),
    #     truncation_config=TruncationConfig(max_docstring_length=100)
    # )
    # Note: The exact structure for nested configs (StubGenConfig, ProcessingConfig, etc.)
    # should be referenced from twat_coding.pystubnik.core.config if deep customization is needed.
    # Often, the defaults provided by StubConfig are sufficient.
)

generator = StubGenerator(config=stub_processing_config)

try:
    # Generate the stub content for the specified source file
    stub_content = generator.generate_stub(source_file_path)

    # Write the generated stub content to the output file
    with open(output_stub_path, "w", encoding="utf-8") as f:
        f.write(stub_content)

    print(f"Smart stub generated successfully at: {output_stub_path}")

except FileNotFoundError:
    print(f"Error: Source file not found at {source_file_path}")
except Exception as e:
    print(f"An error occurred during stub generation: {e}")

```
For more advanced configuration options, refer to the "How `pystubnik` Works / Configuration System" section below.

---

## Technical Details and Contributing

This section provides a deeper dive into `pystubnik`'s architecture and how to contribute to `twat-coding`.

### How `pystubnik` Works (Architecture)

#### Smart Stubs Explained
Smart stubs are `.py` or `.pyi` files that intelligently summarize Python code. They include:
*   All function and class signatures with type hints.
*   Organized and optimized import statements.
*   Docstrings (configurable inclusion and length).
*   Important/relevant code sections (e.g., assignments of constants, class variables if configured).
*   Function bodies are typically reduced to `pass` or a minimal representation, focusing on the interface and structure.

The goal is to create a representation that is significantly more informative than traditional `.pyi` stubs (which often only contain signatures) but far more concise than the original source code.

#### Core Stub Generation Process (AST Backend)
`pystubnik` primarily uses Python's built-in `ast` module.
1.  **Parsing:** The source Python file is parsed into an Abstract Syntax Tree (AST).
2.  **AST Traversal (`StubVisitor`):**
    *   A custom visitor (`src/twat_coding/pystubnik/processors/stub_generation.py::StubVisitor`) traverses the AST.
    *   It collects relevant nodes: imports, class definitions, function definitions (including methods), and top-level assignments.
    *   It applies filtering rules, such as excluding private members (e.g., names starting with `_`) if `include_private` is `False`.
3.  **Stub Orchestration (`StubGenerator`):**
    *   The `StubGenerator` class (`src/twat_coding/pystubnik/processors/stub_generation.py::StubGenerator`) orchestrates the stubbing process.
    *   It takes the collected AST nodes and applies various transformations based on the provided configuration (`StubConfig`).
    *   **Import Processing:** Imports are collected, categorized (stdlib, pathlib, typing, local/project), and sorted. Duplicate imports are handled.
    *   **Docstring Handling:** Docstrings for modules, classes, and functions are preserved. Their maximum length can be controlled (e.g., `max_docstring_length` in `StubGenConfig` via `StubConfig`).
    *   **Code Element Formatting:** Class and function definitions are reconstructed with their signatures. Function bodies are typically replaced with `pass`. Assignments might be kept, potentially with truncated values if `preserve_literals` is False or for complex literals.
    *   **Output Generation:** The processed elements are assembled into the final stub content string.

#### Configuration System (`pystubnik.config`)
`pystubnik` uses Pydantic for robust and type-safe configuration management.
*   **`StubConfig` (`src/twat_coding/pystubnik/config.py`):** The main configuration class. It orchestrates settings for file paths, processing behavior, and output formatting.
    *   **Key `StubConfig` fields:**
        *   `input_path: Path`: Path to Python source files or directory.
        *   `output_path: Path | None`: Path to output directory for stubs.
        *   `files: list[Path]`: Specific files to process.
        *   `include_patterns: list[str]`: Glob patterns for file inclusion (default: `["*.py"]`).
        *   `exclude_patterns: list[str]`: Glob patterns for file exclusion (default: `["test_*.py", "*_test.py"]`).
        *   `backend: Literal["ast", "mypy"]`: Backend for stub generation (default: `"ast"`).
        *   `include_private: bool`: Whether to include private members (default: `False`).
        *   `add_header: bool`: Add a "Generated by pystubnik" header (default: `True`).
        *   `sort_imports: bool`: Sort imports (default: `True`).
        *   `line_length: int`: Target line length for formatting (default: `88`).
    *   **Nested `StubGenConfig` (`src/twat_coding/pystubnik/core/config.py::StubGenConfig`):** `StubConfig` often instantiates or holds a `StubGenConfig` object (usually via defaults or direct initialization) which contains more granular settings for the generation process itself, such as:
        *   `processing_config`: Controls aspects like `include_docstrings`, `importance_patterns`.
        *   `truncation_config`: Manages `max_docstring_length`, `max_sequence_length` for literals.
*   CLI options and programmatic parameters map to these Pydantic models. Configuration can also be loaded from a TOML file via the CLI.

### Codebase Structure

*   `src/twat_coding/`: Main source code for the `twat-coding` package.
    *   `pystubnik/`: Core logic for the `pystubnik` smart stub generator.
        *   `cli.py`: Command-Line Interface logic using `python-fire`.
        *   `config.py`: Pydantic models for `StubConfig`, `RuntimeConfig`.
        *   `core/config.py`: Contains `StubGenConfig` and related detailed configuration models.
        *   `processors/stub_generation.py`: Home of `StubGenerator` and `StubVisitor`, the heart of the AST-based stubbing.
        *   `utils/`: Utility functions, e.g., for AST manipulation.
        *   `backends/`: (Potentially for different stubbing backends like MyPy if further developed).
*   `tests/`: Unit and integration tests for the package.
*   `docs/`: Source files for Sphinx documentation (if present and maintained).
*   `pyproject.toml`: Project metadata, dependencies, and configurations for tools like `hatch`, `ruff`, `mypy`.
*   `.github/workflows/`: GitHub Actions for CI/CD (testing, linting, publishing).

### Contributing

Contributions are highly welcome! Whether it's bug fixes, feature enhancements, or documentation improvements, your help is appreciated.

#### Initial Development Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/twardoch/twat-coding.git
    cd twat-coding
    ```
2.  **Install `uv` (recommended, fast Python package installer):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Or: pip install uv
    ```
3.  **Create and activate a virtual environment:**
    Using `uv`:
    ```bash
    uv venv .venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows
    ```
4.  **Install dependencies:**
    This project uses `hatch` for environment and project management.
    ```bash
    uv pip install hatch hatch-vcs # Install hatch and its vcs plugin
    ```
    Then, create environments and install the project with its dependencies:
    ```bash
    hatch env create default  # Creates default env with project & dev dependencies
    # Or for specific environments like test, lint:
    # hatch env create test
    # hatch env create lint
    ```
    Alternatively, to install all project dependencies (including optional ones for development) directly into your active `uv` environment:
    ```bash
    uv pip install -e ".[all]"
    ```
5.  **Install pre-commit hooks:**
    This ensures your contributions adhere to code style and quality standards before committing.
    ```bash
    pre-commit install
    ```

#### Running Tests
Tests are managed with `pytest` and typically run via Hatch environments.
```bash
hatch run test  # Runs pytest using the 'test' environment (or 'default:test')
# Check pyproject.toml for exact hatch script names, e.g., hatch run default:pytest
```
To run tests with coverage:
```bash
hatch run test:cov-report # (or similar, e.g., default:cov)
# Coverage reports will be in htmlcov/ and coverage.xml.
```

#### Linting and Formatting
The project uses `ruff` for linting and formatting, and `mypy` for static type checking.
*   **Check formatting and linting issues:**
    ```bash
    hatch run lint:check  # (or default:lint_check)
    ```
*   **Apply formatting and auto-fixes:**
    ```bash
    hatch run lint:fmt    # (or default:lint_fix)
    ```
*   **Run MyPy type checks:**
    ```bash
    hatch run lint:typing # (or default:mypy)
    ```
These checks are also part of the pre-commit hooks.

#### Versioning
Versioning is managed by `hatch-vcs`, which derives the package version from Git tags. When preparing a release, create an annotated Git tag (e.g., `v0.1.0`).

#### Committing Changes
Before committing, ensure your changes pass all pre-commit hooks. These hooks will automatically format your code and run quick checks.
```bash
git commit -m "Your descriptive commit message"
```

#### Submitting Changes
1.  Push your changes to your fork or branch on GitHub.
2.  Open a Pull Request against the `main` branch of the `twardoch/twat-coding` repository.
3.  Ensure all CI checks (GitHub Actions) pass for your PR. Your PR will be reviewed by maintainers.

### Publishing to PyPI
Publishing new versions to PyPI is automated via the `release.yml` GitHub Actions workflow. This workflow triggers when a new version tag (e.g., `vX.Y.Z`) is pushed to the repository. It handles building the sdist and wheel, and then publishing them to PyPI.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.
