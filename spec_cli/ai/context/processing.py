"""Main processing function for agent scope context extraction."""

from pathlib import Path
from typing import Any

try:
    import structlog  # type: ignore
except ImportError:
    structlog = None

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.extractor import ContextExtractor
from spec_cli.ai.context.ranking import RelevanceRanker
from spec_cli.logging.debug import debug_logger as default_debug_logger
from spec_cli.utils.path_utils import normalize_path_separators

if structlog:
    logger = structlog.get_logger()
else:
    import logging

    logger = logging.getLogger(__name__)


def discover_project_files(params: dict[str, Any]) -> list[str]:
    """Discover project files based on given parameters.

    Args:
        params: Discovery parameters containing base_path

    Returns:
        List of discovered file paths
    """
    base_path = params.get("base_path", Path.cwd())
    if not isinstance(base_path, Path):
        base_path = Path(base_path)

    # Simple file discovery - just find Python files for now
    files: list[str] = []
    for suffix in [".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"]:
        files.extend(str(f) for f in base_path.rglob(f"*{suffix}"))

    return files[:50]  # Limit for performance


class AgentScopeValidator:
    """Simple validator for agent scope files."""

    def validate_file_inclusion(self, file_path: Path, base_path: Path) -> bool:
        """Validate if file should be included.

        Args:
            file_path: File to validate
            base_path: Base project path

        Returns:
            True if file should be included
        """
        # Simple validation - exclude common non-source directories
        path_str = str(file_path)
        exclude_patterns = [
            "__pycache__",
            ".git",
            ".spec",
            ".venv",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ]

        return not any(pattern in path_str for pattern in exclude_patterns)


def process_agent_scope_context(
    base_path: Path,
    query: str,
    max_results: int = 20,
    ai_config: AIConfig | None = None,
) -> dict[str, Any]:
    """Process and rank contextually relevant files for AI agent scope.

    This function orchestrates the complete context processing pipeline:
    1. Discovers project files using existing discovery logic
    2. Validates and filters files based on security and scope rules
    3. Extracts contextual information from each file
    4. Ranks files by relevance to the query
    5. Returns structured results for AI consumption

    Args:
        base_path: Base directory path to search for files
        query: User query for determining relevance
        max_results: Maximum number of results to return
        ai_config: Optional AI configuration for processing settings

    Returns:
        Dictionary containing:
        - ranked_files: List of ranked file contexts
        - processing_summary: Summary of processing statistics
        - query_analysis: Analysis of query processing

    Raises:
        ValueError: If base_path doesn't exist or query is empty
        RuntimeError: If processing fails due to system issues
    """
    # Input validation
    if not base_path.exists():
        raise ValueError(f"Base path does not exist: {base_path}")
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    debug_logger = default_debug_logger
    normalized_base = normalize_path_separators(str(base_path))

    logger.info(
        "Starting agent scope context processing",
        base_path=normalized_base,
        query_length=len(query),
        max_results=max_results,
    )

    try:
        # Initialize components
        config = ai_config or AIConfig()
        sanitizer = CodeSanitizer(config.security)
        extractor = ContextExtractor(
            ai_config=config, sanitizer=sanitizer, debug_logger=debug_logger
        )
        ranker = RelevanceRanker(
            max_results=max_results, min_relevance_score=0.1, debug_logger=debug_logger
        )

        # Step 1: Discover project files
        discovery_params = _build_discovery_params(base_path, query)
        discovered_files = discover_project_files(discovery_params)

        debug_logger.log(
            "DEBUG",
            "Files discovered",
            total_files=len(discovered_files),
            base_path=normalized_base,
        )

        # Step 2: Validate and filter files
        validator = AgentScopeValidator()
        validated_files = []
        for file_path in discovered_files:
            if validator.validate_file_inclusion(Path(file_path), base_path):
                validated_files.append(file_path)

        debug_logger.log(
            "DEBUG",
            "Files validated",
            validated_count=len(validated_files),
            filtered_out=len(discovered_files) - len(validated_files),
        )

        # Step 3: Extract context from each file
        contexts = []
        processing_errors = []

        for file_path in validated_files:
            try:
                context = _extract_file_context(Path(file_path), query, extractor)
                if context:
                    contexts.append(context)
            except Exception as e:
                processing_errors.append(
                    {"file_path": normalize_path_separators(file_path), "error": str(e)}
                )
                debug_logger.log(
                    "ERROR",
                    "Context extraction failed",
                    file_path=file_path,
                    error=str(e),
                )

        # Step 4: Rank contexts by relevance
        if contexts:
            ranked_contexts = ranker.rank_contexts(contexts, query)
        else:
            ranked_contexts = []

        # Step 5: Build comprehensive response
        processing_summary = _build_processing_summary(
            discovered_files=len(discovered_files),
            validated_files=len(validated_files),
            processed_files=len(contexts),
            final_results=len(ranked_contexts),
            errors=len(processing_errors),
        )

        query_analysis = _analyze_query_processing(query, contexts)
        ranking_stats = ranker.get_ranking_summary(ranked_contexts)

        result: dict[str, Any] = {
            "ranked_files": ranked_contexts,
            "processing_summary": processing_summary,
            "query_analysis": query_analysis,
            "ranking_statistics": ranking_stats,
            "processing_errors": processing_errors[:5],  # Limit error details
        }

        logger.info(
            "Agent scope context processing completed",
            final_results=len(ranked_contexts),
            processing_time_info="completed_successfully",
        )

        return result

    except Exception as e:
        logger.error(
            "Agent scope context processing failed: %s (base_path: %s)",
            str(e),
            normalized_base,
        )
        raise RuntimeError(f"Context processing failed: {e}") from e


def _build_discovery_params(base_path: Path, query: str) -> dict[str, Any]:
    """Build parameters for file discovery based on query and path."""
    return {
        "base_path": base_path,
        "query": query.strip(),
        "include_env_info": True,
        "max_file_size": 1024 * 1024,  # 1MB limit
        "respect_gitignore": True,
    }


def _extract_file_context(
    file_path: Path, query: str, extractor: ContextExtractor
) -> dict[str, Any] | None:
    """Extract context from a single file safely."""
    try:
        if not file_path.exists() or not file_path.is_file():
            return None

        # Read file content with encoding fallback
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
            except UnicodeDecodeError:
                return None  # Skip files that can't be decoded

        # Skip empty files
        if not content.strip():
            return None

        # Extract context using the extractor
        context = extractor.extract_context(file_path, content, query)
        return context

    except Exception:
        # Return None for any extraction errors - logged by caller
        return None


def _build_processing_summary(
    discovered_files: int,
    validated_files: int,
    processed_files: int,
    final_results: int,
    errors: int,
) -> dict[str, Any]:
    """Build comprehensive processing summary."""
    return {
        "pipeline_stages": {
            "discovered": discovered_files,
            "validated": validated_files,
            "processed": processed_files,
            "ranked": final_results,
        },
        "processing_efficiency": {
            "validation_rate": validated_files / max(discovered_files, 1),
            "processing_rate": processed_files / max(validated_files, 1),
            "error_rate": errors / max(validated_files, 1),
        },
        "quality_metrics": {
            "files_with_errors": errors,
            "successful_extractions": processed_files,
            "final_result_ratio": final_results / max(processed_files, 1),
        },
    }


def _analyze_query_processing(
    query: str, contexts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Analyze query processing effectiveness."""
    query_terms = set(query.lower().split())

    if not contexts:
        return {
            "query_terms": list(query_terms),
            "term_coverage": {},
            "average_relevance": 0.0,
            "query_effectiveness": 0.0,
        }

    # Calculate term coverage across all contexts
    term_coverage: dict[str, int] = {}
    total_relevance = 0.0

    for context in contexts:
        relevance_raw = context.get("relevance_score", 0.0)
        relevance = (
            float(relevance_raw)
            if isinstance(relevance_raw, int | float | str)
            else 0.0
        )
        total_relevance += relevance

        # Check which query terms appear in this context
        classes = context.get("classes", [])
        functions = context.get("functions", [])
        imports = context.get("imports", [])

        classes_str = (
            " ".join(str(item) for item in classes)
            if isinstance(classes, list | tuple)
            else ""
        )
        functions_str = (
            " ".join(str(item) for item in functions)
            if isinstance(functions, list | tuple)
            else ""
        )
        imports_str = (
            " ".join(str(item) for item in imports)
            if isinstance(imports, list | tuple)
            else ""
        )

        all_text = " ".join(
            [str(context.get("file_path", "")), classes_str, functions_str, imports_str]
        ).lower()

        for term in query_terms:
            if term in all_text:
                term_coverage[term] = term_coverage.get(term, 0) + 1

    # Calculate effectiveness metrics
    average_relevance = total_relevance / len(contexts)
    coverage_ratio = len(term_coverage) / max(len(query_terms), 1)

    return {
        "query_terms": list(query_terms),
        "term_coverage": term_coverage,
        "average_relevance": average_relevance,
        "query_effectiveness": (average_relevance + coverage_ratio) / 2.0,
    }
