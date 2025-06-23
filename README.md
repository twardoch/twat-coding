# twat-coding

[![PyPI version](https://badge.fury.io/py/twat-coding.svg)](https://badge.fury.io/py/twat-coding)
[![Python Version](https://img.shields.io/pypi/pyversions/twat-coding.svg)](https://pypi.org/project/twat-coding/)
[![License](https://img.shields.io/pypi/l/twat-coding.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI/CD Status](https://github.com/twardoch/twat-coding/actions/workflows/push.yml/badge.svg)](https://github.com/twardoch/twat-coding/actions/workflows/push.yml)
[![Coverage Status](https://codecov.io/gh/twardoch/twat-coding/branch/main/graph/badge.svg)](https://codecov.io/gh/twardoch/twat-coding)

**`twat-coding`** is a Python toolkit designed to enhance code understanding, analysis, and manipulation, particularly with Large Language Models (LLMs) in mind. It provides utilities for generating intelligent code representations ("smart stubs") and other development aids.

## Rationale

Modern software development, especially when interfacing with LLMs or analyzing large codebases, requires tools that can distill complex code into more digestible formats. Traditional type stubs (`.pyi` files) often lack crucial information like docstrings or key implementation details, while full source code can be too verbose. `twat-coding` aims to bridge this gap.

The primary component, `pystubnik`, generates "smart stubs" that preserve essential code structure, type hints, docstrings, and even important code snippets, while significantly reducing verbosity. This makes large Python projects more accessible for automated analysis, LLM ingestion, and quicker human understanding.

## Features

*   **Smart Stub Generation (`pystubnik`)**:
    *   Creates concise yet informative code representations.
    *   Multiple backends (AST, MyPy) for comprehensive analysis.
    *   Intelligent import analysis and organization.
    *   Configurable docstring processing and formatting.
    *   Importance-based code filtering to retain critical logic.
    *   Support for modern Python 3.12+ features.
*   **Modern Python Development Stack**:
    *   Managed with `hatch` for building, versioning, and environment management.
    *   Uses `ruff` for linting and formatting, `mypy` for static type checking.
    *   Dependency management with `uv`.
    *   Automated QA with pre-commit hooks and GitHub Actions.
    *   Semantic versioning based on git tags via `hatch-vcs`.

## Core Package: `pystubnik`

`pystubnik` is the flagship tool within `twat-coding`. It generates "smart stubs" – an intelligent intermediate representation between full source code and type stubs, optimized for LLM code understanding and human analysis.

Key features include:
- Multiple backends (AST and MyPy) for comprehensive stub generation.
- Smart import analysis and organization.
- Configurable docstring processing and formatting.
- Importance-based code filtering.

[Learn more about pystubnik's architecture and advanced configuration](src/twat_coding/pystubnik/README.md).

## Installation

You can install `twat-coding` using `pip` or `uv`:

```bash
# Using pip
pip install twat-coding

# Using uv
uv pip install twat-coding
```

To include all optional dependencies for development and specific features:
```bash
# Using pip
pip install twat-coding[all]

# Using uv
uv pip install twat-coding[all]
```

## Usage

### Command-Line (via `pystubnik` CLI)

The primary way to use `pystubnik` is through its command-line interface, which is also available as `twat-coding`:

```bash
# Generate stubs for a single file
twat-coding generate path/to/your/file.py --output-path path/to/your/output.pyi

# Generate stubs for an entire directory
twat-coding generate-dir path/to/your_package/ --output-dir path/to/stubs_output/
```

For more CLI options, run:
```bash
twat-coding --help
```

### Python API (`SmartStubGenerator`)

You can also use `pystubnik` programmatically:

```python
from pathlib import Path
from twat_coding.pystubnik import SmartStubGenerator, StubGenConfig, PathConfig, RuntimeConfig, ProcessingConfig, TruncationConfig, Backend

# Configure the generator
config = StubGenConfig(
    paths=PathConfig(
        output_dir=Path("my_stubs"),
        files=[Path("path/to/my_module.py")],
        # Add other paths like packages, search_paths as needed
    ),
    runtime=RuntimeConfig(
        backend=Backend.AST, # Or Backend.MYPY, Backend.HYBRID
        verbose=True,
    ),
    processing=ProcessingConfig(
        include_docstrings=True,
        importance_patterns={r"^_": 0.5}, # Reduce importance of private-looking members
    ),
    truncation=TruncationConfig(
        max_docstring_length=200,
    )
)

generator = SmartStubGenerator(
    output_dir=config.paths.output_dir,
    files=config.paths.files,
    backend=config.runtime.backend,
    verbose=config.runtime.verbose,
    # Pass other parameters from config as needed or let them default
    include_docstrings=config.processing.include_docstrings,
    max_docstring_length=config.truncation.max_docstring_length,
)

generator.generate()

print(f"Smart stubs generated in {config.paths.output_dir}")
```

## Development & Contributing

Contributions are highly welcome! This project uses a modern Python development setup.

### Initial Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/twardoch/twat-coding.git
    cd twat-coding
    ```

2.  **Install `uv` (if you haven't already):**
    `uv` is a fast Python package installer and resolver.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Or, on Windows/other systems: pip install uv
    ```

3.  **Create and activate a virtual environment:**
    It's recommended to use `uv` to create your environment.
    ```bash
    uv venv .venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows
    ```

4.  **Install dependencies using Hatch:**
    This project uses `hatch` for environment and project management. The necessary development dependencies, including linters, type checkers, and testing tools, are defined in `pyproject.toml`.
    ```bash
    uv pip install hatch hatch-vcs # Install hatch and hatch-vcs plugin
    hatch env create default # Creates default env with project installed
    hatch env create test    # Creates test env
    hatch env create lint    # Creates lint env
    hatch env create docs    # Creates docs env
    ```
    Alternatively, to install all project dependencies including optional ones for development into your active `uv` environment:
    ```bash
    uv pip install -e ".[all]"
    ```

5.  **Install pre-commit hooks:**
    This will ensure your contributions adhere to the project's code style and quality standards.
    ```bash
    pre-commit install
    ```

### Codebase Structure

*   `src/twat_coding/`: Main source code for the package.
    *   `pystubnik/`: Core logic for the smart stub generation.
        *   `backends/`: AST and MyPy processing backends.
        *   `core/`: Core data structures, configurations, and utilities.
        *   `processors/`: Modules for docstrings, imports, importance scoring, etc.
        *   `types/`: Type system and docstring type definitions.
*   `tests/`: Unit and integration tests.
*   `docs/`: Sphinx documentation source.
*   `pyproject.toml`: Project metadata, dependencies, and tool configurations (Hatch, Ruff, MyPy).
*   `.github/workflows/`: GitHub Actions for CI/CD.

### Running Tests

Tests are managed with `pytest` and run via Hatch environments.
```bash
hatch run test  # Runs pytest using the 'test' environment
```
To run tests with coverage:
```bash
hatch run test:cov-report # Runs tests and generates HTML/XML coverage reports
```
Coverage reports will be in `htmlcov/` and `coverage.xml`.

### Linting and Formatting

This project uses `ruff` for super-fast linting and formatting, and `mypy` for static type checking.

*   **Check formatting and linting issues:**
    ```bash
    hatch run lint:check
    ```
*   **Apply formatting and auto-fixes:**
    ```bash
    hatch run lint:fmt
    ```
*   **Run MyPy type checks:**
    ```bash
    hatch run lint:typing
    ```
These checks are also part of the pre-commit hooks.

### Versioning

Versioning is managed by `hatch-vcs`, which derives the package version from Git tags. When preparing a release, create an annotated Git tag (e.g., `v0.1.0`).

### Committing Changes

Before committing, ensure your changes pass all pre-commit hooks. These hooks will automatically format your code and run quick checks.
```bash
git commit -m "Your descriptive commit message"
```

### Submitting Changes

1.  Push your changes to your fork/branch.
2.  Open a Pull Request against the `main` branch of the `twardoch/twat-coding` repository.
3.  Ensure all CI checks (GitHub Actions) pass for your PR.

## Publishing to PyPI

Publishing is automated via the `release.yml` GitHub Actions workflow. When a new version tag (e.g., `vX.Y.Z`) is pushed to the repository:
1.  The workflow builds the sdist and wheel.
2.  It publishes these artifacts to PyPI.
3.  It creates a GitHub Release with the generated artifacts and release notes.

Manual publishing is generally not required.

## License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.
