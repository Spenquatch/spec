"""Complexity analysis utilities for singleton pattern classification.

This module provides complexity assessment functionality for singleton patterns
to support migration planning and priority ranking.
"""

from dataclasses import dataclass

from ...core.context_bridge import debug_logger
from ...exceptions import SpecError
from ..singleton_detection import SingletonViolation


class ComplexityAnalysisError(SpecError):
    """Exception raised when complexity analysis fails."""

    pass


@dataclass
class ComplexityAssessment:
    """Assessment of singleton pattern complexity for migration planning."""

    complexity_score: int  # 1-10 scale (1=simple, 10=complex)
    migration_priority: str  # "low", "medium", "high", "critical"
    risk_factors: list[str]  # List of specific complexity risk factors
    estimated_effort_hours: int  # Rough estimate for migration effort
    dependency_count: int  # Number of dependencies on this pattern


def analyze_pattern_complexity(
    pattern: SingletonViolation, dependency_count: int = 0
) -> ComplexityAssessment:
    """Analyze complexity of a singleton pattern for migration planning.

    Args:
        pattern: Singleton violation to analyze
        dependency_count: Number of dependencies on this pattern

    Returns:
        Complexity assessment with scores and migration guidance

    Raises:
        ComplexityAnalysisError: If analysis fails

    Example:
        >>> from pathlib import Path
        >>> pattern = SingletonViolation(Path("test.py"), 1, 0, "metaclass", "desc", "code")
        >>> assessment = analyze_pattern_complexity(pattern, dependency_count=5)
        >>> print(f"Complexity: {assessment.complexity_score}/10")
    """
    debug_logger.log(
        "DEBUG",
        "Starting complexity analysis",
        pattern_type=pattern.pattern_type,
        file_path=str(pattern.file_path),
    )

    try:
        # Base complexity score based on pattern type
        complexity_score = _calculate_base_complexity(pattern)

        # Adjust for dependency count
        complexity_score += min(dependency_count // 2, 3)  # Cap dependency bonus at 3

        # Ensure score stays within bounds
        complexity_score = max(1, min(complexity_score, 10))

        # Determine migration priority
        migration_priority = _determine_migration_priority(
            complexity_score, dependency_count
        )

        # Identify risk factors
        risk_factors = _identify_risk_factors(pattern, dependency_count)

        # Estimate effort
        estimated_effort_hours = _estimate_effort_hours(
            complexity_score, dependency_count
        )

        assessment = ComplexityAssessment(
            complexity_score=complexity_score,
            migration_priority=migration_priority,
            risk_factors=risk_factors,
            estimated_effort_hours=estimated_effort_hours,
            dependency_count=dependency_count,
        )

        debug_logger.log(
            "INFO",
            "Complexity analysis completed",
            complexity_score=complexity_score,
            migration_priority=migration_priority,
            estimated_effort_hours=estimated_effort_hours,
        )

        return assessment

    except Exception as e:
        raise ComplexityAnalysisError(
            f"Failed to analyze pattern complexity: {e}"
        ) from e


def _calculate_base_complexity(pattern: SingletonViolation) -> int:
    """Calculate base complexity score based on pattern type."""
    complexity_map = {
        "metaclass_singleton": 8,  # Metaclass patterns are most complex
        "decorator_singleton": 6,  # Decorators are moderately complex
        "import_singleton": 4,  # Imports are simpler to migrate
        "import_from_singleton": 4,
        "import_singleton_name": 3,
        "function_decorator_singleton": 5,
    }

    return complexity_map.get(pattern.pattern_type, 5)  # Default to medium complexity


def _determine_migration_priority(complexity_score: int, dependency_count: int) -> str:
    """Determine migration priority based on complexity and dependencies."""
    if complexity_score >= 8 or dependency_count >= 10:
        return "critical"
    elif complexity_score >= 6 or dependency_count >= 5:
        return "high"
    elif complexity_score >= 4 or dependency_count >= 2:
        return "medium"
    else:
        return "low"


def _identify_risk_factors(
    pattern: SingletonViolation, dependency_count: int
) -> list[str]:
    """Identify specific risk factors for the pattern migration."""
    risk_factors = []

    # Pattern-specific risks
    if pattern.pattern_type == "metaclass_singleton":
        risk_factors.extend(
            [
                "Metaclass implementation requires careful refactoring",
                "May affect class inheritance hierarchy",
            ]
        )

    if pattern.pattern_type.startswith("decorator"):
        risk_factors.append("Decorator removal may break existing APIs")

    if "import" in pattern.pattern_type:
        risk_factors.append("Import changes may affect multiple modules")

    # Dependency-based risks
    if dependency_count >= 10:
        risk_factors.append("High dependency count increases migration risk")
    elif dependency_count >= 5:
        risk_factors.append("Multiple dependencies require careful coordination")

    # Code location risks
    if "test" in str(pattern.file_path).lower():
        risk_factors.append(
            "Test-related pattern may require test infrastructure changes"
        )

    # Default risk if none identified
    if not risk_factors:
        risk_factors.append("Standard migration complexity")

    return risk_factors


def _estimate_effort_hours(complexity_score: int, dependency_count: int) -> int:
    """Estimate migration effort in hours."""
    # Base effort based on complexity
    base_hours = complexity_score * 2

    # Additional hours for dependencies
    dependency_hours = min(dependency_count * 1, 10)  # Cap at 10 hours

    return base_hours + dependency_hours
