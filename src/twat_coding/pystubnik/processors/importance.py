"""Importance scoring for stub generation."""

import ast
import re
from typing import cast

from pystubnik.core.types import StubResult
from pystubnik.processors import Processor


class ImportanceProcessor(Processor):
    """Processor for calculating importance scores in stub generation."""

    def __init__(
        self,
        min_importance: float = 0.0,
        importance_patterns: dict[str, float] | None = None,
    ):
        self.min_importance = min_importance
        self.importance_patterns = importance_patterns or {}
        self._compile_patterns()

    def process(self, stub_result: StubResult) -> StubResult:
        """Process importance scores in the stub result.

        Args:
            stub_result: The stub generation result to process

        Returns:
            The processed stub result with importance scores
        """
        tree = cast(ast.Module, ast.parse(stub_result.stub_content))

        # Calculate importance scores for all nodes
        scores = self._calculate_scores(tree)

        # Filter out low-importance nodes
        if self.min_importance > 0:
            tree = cast(ast.Module, self._filter_nodes(tree, scores))
            stub_result.stub_content = ast.unparse(tree)

        # Store the overall importance score
        stub_result.importance_score = max(scores.values()) if scores else 0.0

        return stub_result

    def _compile_patterns(self) -> None:
        """Compile regex patterns for importance scoring."""
        self._compiled_patterns = [
            (re.compile(pattern), score)
            for pattern, score in self.importance_patterns.items()
        ]

    def _calculate_scores(self, tree: ast.AST) -> dict[ast.AST, float]:
        """Calculate importance scores for all nodes in the AST.

        Args:
            tree: The AST to analyze

        Returns:
            Dictionary mapping nodes to their importance scores
        """
        scores: dict[ast.AST, float] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.ClassDef):
                scores[node] = self._calculate_node_score(node)

        return scores

    def _calculate_node_score(self, node: ast.FunctionDef | ast.ClassDef) -> float:
        """Calculate importance score for a single node.

        Args:
            node: The AST node to score

        Returns:
            The importance score for the node
        """
        score = 0.0

        # Base score from node type
        if isinstance(node, ast.ClassDef):
            score += 0.5
        elif isinstance(node, ast.FunctionDef):
            score += 0.3

        # Score from name patterns
        for pattern, pattern_score in self._compiled_patterns:
            if pattern.search(node.name):
                score = max(score, pattern_score)

        # Score from decorators
        score += len(node.decorator_list) * 0.1

        # Score from docstring
        docstring = ast.get_docstring(node)
        if docstring:
            score += 0.2

            # Additional score for type hints in docstring
            if ":type" in docstring or ":rtype:" in docstring:
                score += 0.1

        # Score from type annotations
        if isinstance(node, ast.FunctionDef):
            if node.returns:
                score += 0.2
            score += sum(1 for arg in node.args.args if arg.annotation) * 0.1

        return min(1.0, score)

    def _filter_nodes(
        self, tree: ast.Module, scores: dict[ast.AST, float]
    ) -> ast.Module:
        """Filter out nodes with low importance scores.

        Args:
            tree: The AST to filter
            scores: Dictionary of node scores

        Returns:
            Filtered AST
        """

        class ImportanceFilter(ast.NodeTransformer):
            def __init__(self, min_importance: float):
                self.min_importance = min_importance

            def visit_FunctionDef(
                self, node: ast.FunctionDef
            ) -> ast.FunctionDef | None:
                if scores.get(node, 0.0) < self.min_importance:
                    return None
                return node

            def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef | None:
                if scores.get(node, 0.0) < self.min_importance:
                    return None
                return node

        filter_transformer = ImportanceFilter(self.min_importance)
        return cast(ast.Module, filter_transformer.visit(tree))
