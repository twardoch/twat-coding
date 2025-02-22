# pystubnik

A Python package for generating "smart stubs" - an intelligent intermediate representation between full source code and type stubs, optimized for LLM code understanding.

## 1. Overview

Pystubnik creates a "shadow" directory structure that mirrors your Python package, containing smart stubs for all Python files. These smart stubs are designed to be more informative than traditional `.pyi` stub files while being more concise than full source code.

### 1.1. What are Smart Stubs?

Smart stubs are an intermediate representation that includes:
- All function and class signatures with type hints
- All imports (organized and optimized)
- Docstrings (with configurable length limits)
- Important/relevant code sections
- Truncated versions of large data structures and strings
- Simplified function bodies for non-critical code

The verbosity level is automatically adjusted based on the code's importance and complexity.

## 2. Architecture

### 2.1. Backends

#### 2.1.1. AST Backend
- Uses Python's built-in AST module for precise control
- Preserves code structure while reducing verbosity
- Configurable truncation of large literals and sequences
- Maintains type information and docstrings
- Supports Python 3.12+ features (type parameters, etc.)

#### 2.1.2. MyPy Backend
- Leverages mypy's stubgen for type information
- Better type inference capabilities
- Handles special cases (dataclasses, properties)
- Supports type comment extraction

### 2.2. Processors

#### 2.2.1. Import Processor
- Analyzes and organizes imports
- Groups by type (stdlib, third-party, local)
- Handles relative imports
- Detects and removes duplicates

#### 2.2.2. Docstring Processor
- Configurable docstring preservation
- Format detection and conversion
- Type information extraction
- Length-based truncation

#### 2.2.3. Importance Processor
- Scores code elements by importance
- Pattern-based importance detection
- Inheritance-aware scoring
- Configurable filtering

## 3. Usage

```python
from twat_coding.pystubnik import generate_stub, StubGenConfig, PathConfig

# Basic usage
result = generate_stub(
    source_path="path/to/file.py",
    output_path="path/to/output/file.py"
)

# Advanced configuration
config = StubGenConfig(
    paths=PathConfig(
        output_dir="path/to/output",
        doc_dir="path/to/docs",
        search_paths=[],
        modules=[],
        packages=[],
        files=[],
    ),
    processing=ProcessingConfig(
        include_docstrings=True,
        include_private=False,
        include_type_comments=True,
        infer_property_types=True,
        export_less=False,
        importance_patterns={
            r"^test_": 0.5,  # Lower importance for test functions
            r"^main$": 1.0,  # High importance for main functions
        },
    ),
    truncation=TruncationConfig(
        max_sequence_length=4,
        max_string_length=17,
        max_docstring_length=150,
        max_file_size=3_000,
        truncation_marker="...",
    ),
)

result = generate_stub(
    source_path="path/to/file.py",
    output_path="path/to/output/file.py",
    config=config
)

# Process multiple files
from twat_coding.pystubnik import SmartStubGenerator

generator = SmartStubGenerator(
    output_dir="path/to/output",
    include_docstrings=True,
    include_private=False,
    verbose=True,
)

generator.generate()  # Process all configured files
```

## 4. Configuration

Smart stub generation can be customized with various settings:

### 4.1. Path Configuration
- `output_dir`: Directory for generated stubs
- `doc_dir`: Directory containing documentation
- `search_paths`: Module search paths
- `modules`: Module names to process
- `packages`: Package names to process
- `files`: Specific files to process

### 4.2. Processing Configuration
- `include_docstrings`: Whether to include docstrings
- `include_private`: Whether to include private symbols
- `include_type_comments`: Whether to include type comments
- `infer_property_types`: Whether to infer property types
- `export_less`: Whether to minimize exports
- `importance_patterns`: Regex patterns for importance scoring

### 4.3. Truncation Configuration
- `max_sequence_length`: Maximum items in sequences
- `max_string_length`: Maximum length for strings
- `max_docstring_length`: Maximum length for docstrings
- `max_file_size`: File size threshold for truncation
- `truncation_marker`: Marker for truncated content

## 5. Installation

```bash
# Install with all dependencies
pip install twat-coding[pystubnik]

# Install minimal version
pip install twat-coding
```

## 6. Use Cases

1. **LLM Code Understanding**
   - Prepare large codebases for LLM analysis
   - Reduce token usage while maintaining critical information
   - Improve LLM's understanding of code structure

2. **Code Documentation**
   - Generate readable, concise code documentation
   - Maintain type information and signatures
   - Preserve important implementation details

3. **Code Analysis**
   - Quick understanding of large codebases
   - Dependency analysis
   - API surface exploration

4. **Type Stub Generation**
   - Generate enhanced type stubs
   - Better support for documentation tools
   - IDE integration

## 7. Contributing

Contributions are welcome! Please see our contributing guidelines for more information.

## 8. License

This project is licensed under the MIT License - see the LICENSE file for details.