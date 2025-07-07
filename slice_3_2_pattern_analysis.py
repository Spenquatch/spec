"""Slice 3.2: Pattern Analysis and Classification.

This module analyzes detected singleton patterns to classify by type, complexity,
and elimination priority with dependency mapping.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from spec_cli.exceptions import SpecError
from spec_cli.logging.debug import debug_logger
from spec_cli.utils.dependency_analysis import analyze_current_usage
from spec_cli.utils.pattern_analysis import SingletonUsage
from spec_cli.utils.pattern_classification.complexity_analyzer import (
    ComplexityAssessment,
    analyze_pattern_complexity,
)
from spec_cli.utils.singleton_detection import SingletonViolation

class PatternAnalysisError(SpecError):
    """Exception raised when pattern analysis fails."""

    pass

@dataclass
class ClassifiedSingletonPattern:
    """Classified singleton pattern with analysis metadata."""

    original_violation: SingletonViolation
    pattern_category: str  # "simple", "moderate", "complex", "critical"
    complexity_assessment: ComplexityAssessment
    dependent_files: list[Path]  # Files that depend on this pattern
    usage_patterns: list[SingletonUsage]  # How this pattern is used
    migration_notes: list[str]  # Specific migration guidance

@dataclass
class PatternAnalysisResult:
    """Complete analysis result for all detected patterns."""

    classified_patterns: list[ClassifiedSingletonPattern]
    dependency_graph: dict[str, list[str]]  # File dependencies
    complexity_distribution: dict[str, int]  # Count by complexity category
    migration_priority_order: list[str]  # Ordered list of patterns by priority

def analyze_singleton_patterns(
    detected_patterns: list[SingletonViolation], codebase_structure: dict[str, Any]
) -> PatternAnalysisResult:
    """Analyze detected singleton patterns for classification and dependency mapping.

    Args:
        detected_patterns: List of detected singleton violations
        codebase_structure: Structure information about the codebase

    Returns:
        Complete pattern analysis with classifications and dependencies

    Raises:
        PatternAnalysisError: If analysis fails

    Example:
        >>> patterns = [SingletonViolation(...)]
        >>> structure = {"files": ["file1.py", "file2.py"]}
        >>> result = analyze_singleton_patterns(patterns, structure)
        >>> print(f"Found {len(result.classified_patterns)} classified patterns")
    """
    debug_logger.log(
        "INFO",
        "Starting singleton pattern analysis",
        pattern_count=len(detected_patterns),
    )

    try:
        classified_patterns = []
        dependency_graph: dict[str, list[str]] = {}
        all_files = _extract_all_files(codebase_structure)

        # Process each detected pattern
        for pattern in detected_patterns:
            classified_pattern = _classify_single_pattern(pattern, all_files)
            classified_patterns.append(classified_pattern)

            # Build dependency graph
            file_key = str(pattern.file_path)
            if file_key not in dependency_graph:
                dependency_graph[file_key] = []

            # Add dependencies from this pattern
            for dep_file in classified_pattern.dependent_files:
                dep_key = str(dep_file)
                if dep_key not in dependency_graph[file_key]:
                    dependency_graph[file_key].append(dep_key)

        # Calculate complexity distribution
        complexity_distribution = _calculate_complexity_distribution(
            classified_patterns
        )

        # Determine migration priority order
        migration_priority_order = _determine_migration_order(classified_patterns)

        result = PatternAnalysisResult(
            classified_patterns=classified_patterns,
            dependency_graph=dependency_graph,
            complexity_distribution=complexity_distribution,
            migration_priority_order=migration_priority_order,
        )

        debug_logger.log(
            "INFO",
            "Pattern analysis completed",
            classified_count=len(classified_patterns),
            complexity_categories=len(complexity_distribution),
        )

        return result

    except Exception as e:
        raise PatternAnalysisError(f"Failed to analyze singleton patterns: {e}") from e

def _extract_all_files(codebase_structure: dict[str, Any]) -> list[Path]:
    """Extract all file paths from codebase structure."""
    files = []

    if "files" in codebase_structure:
        for file_path in codebase_structure["files"]:
            files.append(Path(file_path))

    if "python_files" in codebase_structure:
        for file_path in codebase_structure["python_files"]:
            files.append(Path(file_path))

    return files

def _classify_single_pattern(
    pattern: SingletonViolation, all_files: list[Path]
) -> ClassifiedSingletonPattern:
    """Classify a single singleton pattern with detailed analysis."""
    debug_logger.log(
        "DEBUG",
        "Classifying pattern",
        pattern_type=pattern.pattern_type,
        file_path=str(pattern.file_path),
    )

    # Find files that depend on this pattern
    dependent_files = _find_dependent_files(pattern, all_files)

    # Analyze complexity
    complexity_assessment = analyze_pattern_complexity(
        pattern, dependency_count=len(dependent_files)
    )

    # Determine pattern category
    pattern_category = _determine_pattern_category(complexity_assessment)

    # Generate usage patterns (simplified for now)
    usage_patterns = _analyze_usage_patterns(pattern)

    # Generate migration notes
    migration_notes = _generate_migration_notes(pattern, complexity_assessment)

    return ClassifiedSingletonPattern(
        original_violation=pattern,
        pattern_category=pattern_category,
        complexity_assessment=complexity_assessment,
        dependent_files=dependent_files,
        usage_patterns=usage_patterns,
        migration_notes=migration_notes,
    )

def _find_dependent_files(
    pattern: SingletonViolation, all_files: list[Path]
) -> list[Path]:
    """Find files that depend on the given singleton pattern."""
    dependent_files = []

    # Use dependency analysis helper to find dependencies
    try:
        for file_path in all_files:
            if file_path == pattern.file_path:
                continue  # Skip self

            # Check if this file depends on the pattern file
            # For now, we'll use a simplified dependency check
            # In a full implementation, this would use AST analysis
            dependency_files = analyze_current_usage(
                pattern.file_path.stem, file_path.parent
            )
            if str(pattern.file_path) in dependency_files:
                dependent_files.append(file_path)

    except Exception as e:
        debug_logger.log(
            "WARNING",
            "Failed to analyze some file dependencies",
            error=str(e),
            pattern_file=str(pattern.file_path),
        )

    return dependent_files

def _determine_pattern_category(complexity_assessment: ComplexityAssessment) -> str:
    """Determine pattern category based on complexity assessment."""
    score = complexity_assessment.complexity_score

    if score >= 8:
        return "critical"
    elif score >= 6:
        return "complex"
    elif score >= 4:
        return "moderate"
    else:
        return "simple"

def _analyze_usage_patterns(pattern: SingletonViolation) -> list[SingletonUsage]:
    """Analyze usage patterns for the singleton (simplified implementation)."""
    # This is a simplified implementation for the slice
    # In a full implementation, this would analyze actual usage across files
    usage = SingletonUsage(
        file_path=pattern.file_path,
        line_number=pattern.line_number,
        usage_type=pattern.pattern_type,
        singleton_name=_extract_singleton_name(pattern),
        context=pattern.code_snippet,
    )

    return [usage]

def _extract_singleton_name(pattern: SingletonViolation) -> str:
    """Extract singleton name from pattern description or code."""
    # Try to extract from description first
    if ":" in pattern.description:
        parts = pattern.description.split(":")
        if len(parts) > 1:
            return parts[1].strip()

    # Fall back to parsing code snippet
    if "class " in pattern.code_snippet:
        class_part = pattern.code_snippet.split("class ")[1]
        name = class_part.split("(")[0].split(":")[0].strip()
        return name

    # Default fallback
    return "unknown_singleton"

def _generate_migration_notes(
    pattern: SingletonViolation, complexity_assessment: ComplexityAssessment
) -> list[str]:
    """Generate specific migration notes for the pattern."""
    notes = []

    # Add pattern-specific notes
    if pattern.pattern_type == "metaclass_singleton":
        notes.extend(
            [
                "Replace metaclass with dependency injection container",
                "Update all class instantiations to use factory pattern",
                "Ensure thread safety during migration",
            ]
        )
    elif pattern.pattern_type == "decorator_singleton":
        notes.extend(
            [
                "Remove singleton decorator",
                "Update calling code to use injected instances",
                "Preserve existing API surface during transition",
            ]
        )
    elif "import" in pattern.pattern_type:
        notes.extend(
            [
                "Update import statements across dependent modules",
                "Replace singleton imports with container configuration",
            ]
        )

    # Add priority-based notes
    if complexity_assessment.migration_priority == "critical":
        notes.append("CRITICAL: Migrate as soon as possible due to high complexity")
    elif complexity_assessment.migration_priority == "high":
        notes.append("HIGH PRIORITY: Schedule for early migration phase")

    # Add effort-based notes
    if complexity_assessment.estimated_effort_hours > 20:
        notes.append(
            f"Large effort required: ~{complexity_assessment.estimated_effort_hours} hours"
        )

    return notes

def _calculate_complexity_distribution(
    classified_patterns: list[ClassifiedSingletonPattern],
) -> dict[str, int]:
    """Calculate distribution of patterns by complexity category."""
    distribution = {"simple": 0, "moderate": 0, "complex": 0, "critical": 0}

    for pattern in classified_patterns:
        category = pattern.pattern_category
        if category in distribution:
            distribution[category] += 1

    return distribution

def _determine_migration_order(
    classified_patterns: list[ClassifiedSingletonPattern],
) -> list[str]:
    """Determine optimal migration order based on complexity and dependencies."""
    # Sort patterns by priority and complexity
    sorted_patterns = sorted(
        classified_patterns,
        key=lambda p: (
            _priority_score(p.complexity_assessment.migration_priority),
            -p.complexity_assessment.complexity_score,  # Higher complexity first within priority
        ),
    )

    return [str(p.original_violation.file_path) for p in sorted_patterns]

def _priority_score(priority: str) -> int:
    """Convert priority string to numeric score for sorting."""
    priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return priority_map.get(priority, 3)
