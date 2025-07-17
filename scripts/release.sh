#!/bin/bash
# this_file: scripts/release.sh

set -euo pipefail

# Release script for twat-coding
echo "🚀 Preparing release for twat-coding..."

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "❌ Error: Must be on main branch to release. Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Get version from user input
if [[ $# -eq 0 ]]; then
    echo "📝 Please provide a version number (e.g., 1.0.0):"
    read -r VERSION
else
    VERSION=$1
fi

# Validate version format (basic semver check)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
    echo "❌ Error: Invalid version format. Expected format: X.Y.Z or X.Y.Z-suffix"
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^v$VERSION$"; then
    echo "❌ Error: Tag v$VERSION already exists"
    exit 1
fi

# Run tests
echo "🧪 Running tests before release..."
./scripts/test.sh

# Build packages
echo "🏗️  Building packages..."
./scripts/build.sh

# Create and push tag
echo "🏷️  Creating and pushing tag v$VERSION..."
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin "v$VERSION"

echo "✅ Release v$VERSION created successfully!"
echo "📦 GitHub Actions will automatically:"
echo "  - Build multiplatform binaries"
echo "  - Publish to PyPI"
echo "  - Create GitHub release with artifacts"
echo ""
echo "🔗 Monitor the release at: https://github.com/twardoch/twat-coding/actions"