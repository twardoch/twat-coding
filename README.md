# twat-coding

A collection of coding-related tools and utilities, designed to enhance code understanding and analysis.

## Packages

### pystubnik

A sophisticated tool for generating "smart stubs" - an intelligent intermediate representation between full source code and type stubs, optimized for LLM code understanding. Smart stubs preserve essential code structure, types, and documentation while reducing verbosity, making large codebases more digestible for LLMs.

Key features:
- Multiple backends (AST and MyPy) for comprehensive stub generation
- Smart import analysis and organization
- Configurable docstring processing and formatting
- Importance-based code filtering
- Support for Python 3.12+ features

[Learn more about pystubnik](src/twat_coding/pystubnik/README.md)

## Installation

```bash
# Install the base package
pip install twat-coding

# Install with pystubnik support
pip install twat-coding[pystubnik]
```

## Development

This project uses modern Python features and follows best practices:
- Type hints and dataclasses for robust data structures
- Protocol-based interfaces for flexibility
- Comprehensive error handling and logging
- Parallel processing for performance

## Contributing

Contributions are welcome! Please see our contributing guidelines for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
