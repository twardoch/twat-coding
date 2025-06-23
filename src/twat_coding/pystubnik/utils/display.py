"""Display utilities for file trees and progress indicators."""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.tree import Tree

console = Console()


def print_file_tree(paths: list[Path]) -> None:
    """Print a tree representation of file paths.

    Args:
        paths: List of paths to display

    """
    tree: dict[str, Any] = {}
    for path in sorted(paths):
        add_to_tree(tree, path.parts)

    root = Tree("📁 Project")
    build_rich_tree(root, tree)
    console.print(root)


def add_to_tree(tree: dict[str, Any], components: list[str] | tuple[str, ...]) -> None:
    """Add a path to the tree structure.

    Args:
        tree: Tree dictionary to update
        components: Path components

    """
    current = tree
    for component in components:
        if component not in current:
            current[component] = {}
        current = current[component]


def build_rich_tree(tree: Tree, data: dict[str, Any], prefix: str = "") -> None:
    """Build a rich Tree from the tree dictionary.

    Args:
        tree: Rich Tree to update
        data: Tree dictionary
        prefix: Current path prefix

    """
    for name, subtree in sorted(data.items()):
        icon = "📁" if subtree else "📄"
        branch = tree.add(f"{icon} {name}")
        if subtree:
            build_rich_tree(branch, subtree, f"{prefix}/{name}" if prefix else name)


def print_progress(message: str, current: int, total: int) -> None:
    """Print progress information.

    Args:
        message: Progress message
        current: Current progress value
        total: Total progress value

    """
    percentage = (current / total) * 100 if total > 0 else 0
    console.print(f"{message}: [{current}/{total}] {percentage:.1f}%")
