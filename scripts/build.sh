#!/bin/bash
# this_file: scripts/build.sh

set -euo pipefail

# Build script for twat-coding
echo "🏗️  Building twat-coding..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/twat_coding.egg-info/ src/twat_coding/_version.py

# Install build dependencies
echo "📦 Installing build dependencies..."
uv pip install build hatchling hatch-vcs

# Build distributions
echo "🔨 Building distributions..."
uv run python -m build --outdir dist

# Verify build
echo "✅ Verifying build..."
ls -la dist/
test -n "$(find dist -name '*.whl')" || (echo "❌ Wheel file missing" && exit 1)
test -n "$(find dist -name '*.tar.gz')" || (echo "❌ Source distribution missing" && exit 1)

echo "✅ Build completed successfully!"
echo "📄 Generated files:"
find dist -type f -exec basename {} \; | sort