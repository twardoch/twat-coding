#!/bin/bash
# this_file: scripts/test.sh

set -euo pipefail

# Test script for twat-coding
echo "🧪 Testing twat-coding..."

# Install test dependencies
echo "📦 Installing test dependencies..."
uv pip install --system -e ".[all]"

# Run code quality checks
echo "🔍 Running code quality checks..."

# Linting
echo "  📋 Running ruff linting..."
uv run ruff check --output-format=github src/twat_coding tests

# Formatting
echo "  🎨 Running ruff formatting check..."
uv run ruff format --check --respect-gitignore src/twat_coding tests

# Type checking
echo "  🔍 Running mypy type checking..."
uv run mypy src/twat_coding tests

# Run tests
echo "🧪 Running tests..."
uv run pytest -n auto --maxfail=1 --disable-warnings \
  --cov-report=term-missing --cov-report=xml --cov-report=html \
  --cov-config=pyproject.toml --cov=src/twat_coding tests/

# Test coverage report
echo "📊 Test coverage report:"
uv run coverage report --show-missing

echo "✅ All tests passed!"