#!/bin/bash
# this_file: scripts/build-binary.sh

set -euo pipefail

# Binary build script for twat-coding
echo "🔨 Building binary for twat-coding..."

# Install build dependencies
echo "📦 Installing build dependencies..."
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  No virtual environment detected. Please activate one first."
    exit 1
fi
uv pip install -e ".[all]"

# Determine OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

# Map architecture names
case $ARCH in
    x86_64)
        ARCH="X64"
        ;;
    aarch64|arm64)
        ARCH="ARM64"
        ;;
    *)
        echo "⚠️  Unknown architecture: $ARCH, using as-is"
        ;;
esac

# Set binary name
if [[ "$OS" == "Darwin" ]]; then
    OS_NAME="macOS"
    BINARY_NAME="twat-coding-${OS_NAME}-${ARCH}"
elif [[ "$OS" == "Linux" ]]; then
    OS_NAME="Linux"
    BINARY_NAME="twat-coding-${OS_NAME}-${ARCH}"
elif [[ "$OS" == "MINGW"* || "$OS" == "CYGWIN"* || "$OS" == "MSYS"* ]]; then
    OS_NAME="Windows"
    BINARY_NAME="twat-coding-${OS_NAME}-${ARCH}.exe"
else
    echo "⚠️  Unknown OS: $OS, using as-is"
    OS_NAME="$OS"
    BINARY_NAME="twat-coding-${OS_NAME}-${ARCH}"
fi

echo "🏗️  Building binary: $BINARY_NAME"

# Create dist directory
mkdir -p dist

# Build binary
echo "🔨 Running PyInstaller..."
uv run pyinstaller --onefile --name "$BINARY_NAME" \
    --add-data "src/twat_coding:twat_coding" \
    --hidden-import twat_coding.pystubnik.cli \
    --hidden-import twat_coding.pystubnik.config \
    --hidden-import twat_coding.pystubnik.processors.stub_generation \
    --hidden-import twat_coding.pystubnik.backends.ast_backend \
    --hidden-import twat_coding.pystubnik.backends.mypy_backend \
    --hidden-import twat_coding.pystubnik.core.config \
    --hidden-import twat_coding.pystubnik.core.conversion \
    --hidden-import twat_coding.pystubnik.processors.stub_generation \
    --hidden-import twat_coding.pystubnik.utils.ast_utils \
    --hidden-import twat_coding.pystubnik.types.docstring \
    --hidden-import twat_coding.pystubnik.types.type_system \
    --distpath dist \
    src/twat_coding/pystubnik/cli.py

# Verify binary was created
if [ -f "dist/$BINARY_NAME" ]; then
    echo "✅ Binary built successfully: dist/$BINARY_NAME"
    
    # Show binary info
    echo "📊 Binary info:"
    ls -lh "dist/$BINARY_NAME"
    
    # Test binary
    echo "🧪 Testing binary..."
    if "./dist/$BINARY_NAME" --help > /dev/null 2>&1; then
        echo "✅ Binary test passed!"
    else
        echo "⚠️  Binary test failed, but binary was created"
    fi
else
    echo "❌ Binary build failed!"
    exit 1
fi

echo "🎉 Binary build completed!"
echo "📄 Run with: ./dist/$BINARY_NAME --help"