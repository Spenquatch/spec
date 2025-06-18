"""Context extraction and processing for AI agent scope."""

import re
from pathlib import Path
from typing import Any

try:
    import structlog  # type: ignore
except ImportError:
    structlog = None

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import AIConfig
from spec_cli.logging.debug import debug_logger as default_debug_logger
from spec_cli.utils.path_utils import normalize_path_separators

if structlog:
    logger = structlog.get_logger()
else:
    import logging

    logger = logging.getLogger(__name__)


class ContextExtractor:
    """Extracts and processes contextual information from code files."""

    def __init__(
        self,
        ai_config: AIConfig | None = None,
        sanitizer: CodeSanitizer | None = None,
        debug_logger: Any | None = None,
    ):
        """Initialize the context extractor.

        Args:
            ai_config: AI configuration for processing settings
            sanitizer: Code sanitizer for cleaning sensitive data
            debug_logger: Debug logger for structured logging
        """
        self.ai_config = ai_config or AIConfig()
        self.sanitizer = sanitizer or CodeSanitizer()
        self.debug_logger = debug_logger or default_debug_logger

        # Compile regex patterns for efficiency
        self._compile_patterns()

        logger.info("Context extractor initialized", config_loaded=bool(ai_config))

    def _compile_patterns(self) -> None:
        """Compile regex patterns for context extraction."""
        self.import_pattern = re.compile(
            r"^(?:from\s+[\w.]+\s+)?import\s+[^\n]+", re.MULTILINE
        )
        self.class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)
        self.function_pattern = re.compile(r"^def\s+(\w+)", re.MULTILINE)
        self.comment_pattern = re.compile(r"#.*$", re.MULTILINE)
        self.docstring_pattern = re.compile(r'"""[\s\S]*?"""', re.MULTILINE | re.DOTALL)

    def extract_context(
        self, file_path: Path, content: str, query: str
    ) -> dict[str, Any]:
        """Extract contextual information from file content.

        Args:
            file_path: Path to the source file
            content: File content to analyze
            query: User query for context relevance

        Returns:
            Dictionary containing extracted context information

        Raises:
            ValueError: If file_path or content is invalid
        """
        if not file_path or str(file_path).strip() == "" or str(file_path) == ".":
            raise ValueError("File path cannot be empty")
        if not content:
            raise ValueError("Content cannot be empty")

        normalized_path = normalize_path_separators(str(file_path))

        # Sanitize content for security
        sanitized_content = self.sanitizer.sanitize(content, Path(normalized_path))

        # Extract structural elements
        imports = self._extract_imports(sanitized_content)
        classes = self._extract_classes(sanitized_content)
        functions = self._extract_functions(sanitized_content)
        comments = self._extract_comments(sanitized_content)
        docstrings = self._extract_docstrings(sanitized_content)

        # Calculate relevance scores
        relevance_score = self._calculate_relevance(
            sanitized_content, query, imports, classes, functions
        )

        context = {
            "file_path": normalized_path,
            "file_size": len(content),
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "comments": comments[:5],  # Limit for performance
            "docstrings": docstrings[:3],  # Limit for performance
            "relevance_score": relevance_score,
            "sanitized": len(sanitized_content) != len(content),
        }

        if hasattr(self.debug_logger, "log"):
            self.debug_logger.log(
                "DEBUG",
                "Context extracted",
                file_path=normalized_path,
                relevance_score=relevance_score,
                elements_found={
                    "imports": len(imports),
                    "classes": len(classes),
                    "functions": len(functions),
                },
            )

        return context

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements from content."""
        imports = self.import_pattern.findall(content)
        return [imp.strip() for imp in imports if imp.strip()]

    def _extract_classes(self, content: str) -> list[str]:
        """Extract class names from content."""
        classes = self.class_pattern.findall(content)
        return [cls.strip() for cls in classes if cls.strip()]

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function names from content."""
        functions = self.function_pattern.findall(content)
        return [func.strip() for func in functions if func.strip()]

    def _extract_comments(self, content: str) -> list[str]:
        """Extract comment lines from content."""
        comments = self.comment_pattern.findall(content)
        return [comment.strip() for comment in comments if comment.strip()]

    def _extract_docstrings(self, content: str) -> list[str]:
        """Extract docstring content from content."""
        docstrings = self.docstring_pattern.findall(content)
        return [doc.replace('"""', "").strip() for doc in docstrings if doc.strip()]

    def _calculate_relevance(
        self,
        content: str,
        query: str,
        imports: list[str],
        classes: list[str],
        functions: list[str],
    ) -> float:
        """Calculate relevance score for content against query.

        Args:
            content: File content to analyze
            query: User query terms
            imports: Extracted import statements
            classes: Extracted class names
            functions: Extracted function names

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not query.strip():
            return 0.5  # Neutral score for empty query

        query_terms = self._extract_query_terms(query)
        if not query_terms:
            return 0.5

        # Score different aspects
        content_score = self._score_content_matches(content, query_terms)
        structure_score = self._score_structure_matches(
            query_terms, imports, classes, functions
        )

        # Weighted combination
        total_score = (content_score * 0.6) + (structure_score * 0.4)
        return min(max(total_score, 0.0), 1.0)  # Clamp to [0.0, 1.0]

    def _extract_query_terms(self, query: str) -> set[str]:
        """Extract meaningful terms from query."""
        # Simple term extraction - split and filter
        terms = set()
        for word in query.lower().split():
            # Remove common words and keep meaningful terms
            if len(word) > 2 and word not in {"the", "and", "for", "with"}:
                terms.add(word)
        return terms

    def _score_content_matches(self, content: str, query_terms: set[str]) -> float:
        """Score content based on query term matches."""
        if not query_terms:
            return 0.0

        content_lower = content.lower()
        matches = sum(1 for term in query_terms if term in content_lower)
        return matches / len(query_terms)

    def _score_structure_matches(
        self,
        query_terms: set[str],
        imports: list[str],
        classes: list[str],
        functions: list[str],
    ) -> float:
        """Score structural elements based on query term matches."""
        if not query_terms:
            return 0.0

        # Combine all structural elements
        all_elements = " ".join(imports + classes + functions).lower()

        if not all_elements:
            return 0.0

        matches = sum(1 for term in query_terms if term in all_elements)
        return matches / len(query_terms)

    def get_extraction_summary(self) -> dict[str, Any]:
        """Get summary of extraction configuration.

        Returns:
            Dictionary containing extraction settings and status
        """
        sanitizer_enabled = getattr(self.sanitizer, "config", None)
        if sanitizer_enabled:
            sanitizer_enabled = getattr(sanitizer_enabled, "enabled", True)
        else:
            sanitizer_enabled = True

        return {
            "sanitizer_enabled": sanitizer_enabled,
            "ai_config_loaded": bool(self.ai_config),
            "patterns_compiled": True,
            "supported_extractions": [
                "imports",
                "classes",
                "functions",
                "comments",
                "docstrings",
            ],
        }
