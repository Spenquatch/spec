"""Relevance ranking system for context processing."""

from pathlib import Path
from typing import Any, cast

try:
    import structlog
except ImportError:
    structlog = None

from spec_cli.logging.debug import debug_logger as default_debug_logger
from spec_cli.utils.path_utils import normalize_path_separators

if structlog:
    logger = structlog.get_logger()
else:
    import logging

    logger = logging.getLogger(__name__)


class RelevanceRanker:
    """Ranks files and contexts by relevance to query."""

    def __init__(
        self,
        max_results: int = 20,
        min_relevance_score: float = 0.1,
        debug_logger: Any | None = None,
    ):
        """Initialize the relevance ranker.

        Args:
            max_results: Maximum number of results to return
            min_relevance_score: Minimum relevance score to include
            debug_logger: Debug logger for structured logging

        Raises:
            ValueError: If max_results <= 0 or min_relevance_score invalid
        """
        if max_results <= 0:
            raise ValueError("max_results must be positive")
        if not 0.0 <= min_relevance_score <= 1.0:
            raise ValueError("min_relevance_score must be between 0.0 and 1.0")

        self.max_results = max_results
        self.min_relevance_score = min_relevance_score
        self.debug_logger = debug_logger or default_debug_logger

        # Ranking weights for different criteria
        self.weights = {
            "relevance_score": 0.4,
            "file_type": 0.2,
            "file_size": 0.1,
            "structure_complexity": 0.2,
            "query_match_density": 0.1,
        }

        logger.info(
            "Relevance ranker initialized",
            max_results=max_results,
            min_score=min_relevance_score,
        )

    def rank_contexts(
        self, contexts: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """Rank contexts by relevance to query.

        Args:
            contexts: List of context dictionaries from ContextExtractor
            query: User query for ranking relevance

        Returns:
            List of contexts ranked by relevance (highest first)

        Raises:
            ValueError: If contexts is empty or query is invalid
        """
        if not contexts:
            raise ValueError("Contexts list cannot be empty")
        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        query_normalized = query.strip().lower()

        # Calculate composite scores for each context
        scored_contexts = []
        for context in contexts:
            composite_score = self._calculate_composite_score(context, query_normalized)

            if composite_score >= self.min_relevance_score:
                context_with_score = context.copy()
                context_with_score["composite_score"] = composite_score
                scored_contexts.append(context_with_score)

        # Sort by composite score (descending)
        ranked_contexts = sorted(
            scored_contexts,
            key=lambda x: cast(float, x["composite_score"]),
            reverse=True,
        )

        # Limit to max_results
        final_results = ranked_contexts[: self.max_results]

        if hasattr(self.debug_logger, "log"):
            self.debug_logger.log(
                "DEBUG",
                "Contexts ranked",
                total_contexts=len(contexts),
                above_threshold=len(scored_contexts),
                final_results=len(final_results),
                query_length=len(query),
            )

        return final_results

    def _calculate_composite_score(self, context: dict[str, Any], query: str) -> float:
        """Calculate composite relevance score for context.

        Args:
            context: Context dictionary with extracted information
            query: Normalized query string

        Returns:
            Composite score between 0.0 and 1.0
        """
        scores = {}

        # Base relevance score from context extraction
        try:
            scores["relevance_score"] = float(context.get("relevance_score", 0.0))
        except (ValueError, TypeError):
            scores["relevance_score"] = 0.0

        # File type preference score
        scores["file_type"] = self._score_file_type(str(context.get("file_path", "")))

        # File size score (prefer moderate sizes)
        file_size_raw = context.get("file_size", 0)
        scores["file_size"] = self._score_file_size(
            int(file_size_raw) if isinstance(file_size_raw, int | float | str) else 0
        )

        # Structural complexity score
        scores["structure_complexity"] = self._score_structure_complexity(context)

        # Query match density in extracted elements
        scores["query_match_density"] = self._score_query_match_density(context, query)

        # Calculate weighted composite score
        composite_score = sum(
            scores[criterion] * self.weights[criterion] for criterion in self.weights
        )

        return min(max(composite_score, 0.0), 1.0)  # Clamp to [0.0, 1.0]

    def _score_file_type(self, file_path: str) -> float:
        """Score based on file type preferences."""
        normalized_path = normalize_path_separators(file_path)
        path_obj = Path(normalized_path)
        extension = path_obj.suffix.lower()

        # Preference scores for different file types
        type_scores = {
            ".py": 1.0,  # Python files - highest priority
            ".js": 0.9,  # JavaScript files
            ".ts": 0.9,  # TypeScript files
            ".java": 0.8,  # Java files
            ".cpp": 0.8,  # C++ files
            ".c": 0.8,  # C files
            ".md": 0.7,  # Markdown files
            ".txt": 0.5,  # Text files
            ".json": 0.6,  # JSON files
            ".yaml": 0.6,  # YAML files
            ".yml": 0.6,  # YAML files
        }

        return type_scores.get(extension, 0.3)  # Default for unknown types

    def _score_file_size(self, file_size: int) -> float:
        """Score based on file size (prefer moderate sizes)."""
        if file_size <= 0:
            return 0.0

        # Optimal size range: 1KB to 50KB
        if 1000 <= file_size <= 50000:
            return 1.0
        elif file_size < 1000:
            # Small files - moderate score
            return 0.7
        elif file_size <= 100000:
            # Large but manageable files
            return 0.8
        else:
            # Very large files - lower score
            return 0.4

    def _score_structure_complexity(self, context: dict[str, Any]) -> float:
        """Score based on structural complexity."""
        # Count structural elements
        classes = context.get("classes", [])
        functions = context.get("functions", [])
        imports = context.get("imports", [])

        num_classes = len(classes) if isinstance(classes, list | tuple) else 0
        num_functions = len(functions) if isinstance(functions, list | tuple) else 0
        num_imports = len(imports) if isinstance(imports, list | tuple) else 0

        # Calculate complexity score
        complexity = num_classes * 0.4 + num_functions * 0.3 + num_imports * 0.3

        # Normalize to 0-1 range (optimal complexity around 5-15 elements)
        if 5 <= complexity <= 15:
            return 1.0
        elif complexity < 5:
            return complexity / 5.0  # Scale up small complexity
        else:
            return max(0.3, 15.0 / complexity)  # Scale down high complexity

    def _score_query_match_density(self, context: dict[str, Any], query: str) -> float:
        """Score based on query term density in extracted elements."""
        if not query:
            return 0.5  # Neutral score for empty query

        query_terms = set(query.split())
        if not query_terms:
            return 0.5

        # Combine all extracted text elements
        all_elements: list[str] = []

        classes = context.get("classes", [])
        if isinstance(classes, list | tuple):
            all_elements.extend(str(item) for item in classes)

        functions = context.get("functions", [])
        if isinstance(functions, list | tuple):
            all_elements.extend(str(item) for item in functions)

        imports = context.get("imports", [])
        if isinstance(imports, list | tuple):
            all_elements.extend(str(item) for item in imports)

        comments = context.get("comments", [])
        if isinstance(comments, list | tuple):
            all_elements.extend(str(item) for item in comments)

        if not all_elements:
            return 0.0

        # Calculate match density
        all_text = " ".join(all_elements).lower()
        matches = sum(1 for term in query_terms if term in all_text)

        return matches / len(query_terms)

    def get_ranking_summary(
        self, ranked_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Get summary of ranking results.

        Args:
            ranked_results: List of ranked context results

        Returns:
            Dictionary containing ranking statistics
        """
        if not ranked_results:
            return {
                "total_results": 0,
                "average_score": 0.0,
                "score_distribution": {},
                "file_types": {},
            }

        scores = [
            float(result.get("composite_score", 0.0)) for result in ranked_results
        ]

        # Calculate score distribution
        score_ranges = {
            "0.8-1.0": sum(1 for s in scores if 0.8 <= s <= 1.0),
            "0.6-0.8": sum(1 for s in scores if 0.6 <= s < 0.8),
            "0.4-0.6": sum(1 for s in scores if 0.4 <= s < 0.6),
            "0.2-0.4": sum(1 for s in scores if 0.2 <= s < 0.4),
            "0.0-0.2": sum(1 for s in scores if 0.0 <= s < 0.2),
        }

        # Count file types
        file_types: dict[str, int] = {}
        for result in ranked_results:
            path = str(result.get("file_path", ""))
            extension = Path(path).suffix.lower()
            file_types[extension] = file_types.get(extension, 0) + 1

        return {
            "total_results": len(ranked_results),
            "average_score": sum(scores) / len(scores),
            "score_distribution": score_ranges,
            "file_types": file_types,
            "ranking_weights": self.weights.copy(),
        }
