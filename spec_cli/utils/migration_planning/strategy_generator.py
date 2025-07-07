"""Strategy generation utilities for singleton pattern elimination.

This module provides focused strategy generation functionality using existing
pipeline data structures and migration utilities.
"""

from typing import Any

from ...exceptions import SpecError
from ...logging.debug import debug_logger

class StrategyGenerationError(SpecError):
    """Exception raised when strategy generation fails."""

    pass

def generate_elimination_strategy(pattern: Any) -> dict[str, Any]:
    """Generate appropriate elimination strategy for a classified singleton pattern.

    Args:
        pattern: ClassifiedSingletonPattern from slice_3_2_pattern_analysis

    Returns:
        Dictionary containing strategy information

    Raises:
        StrategyGenerationError: If strategy generation fails

    Example:
        strategy = generate_elimination_strategy(classified_pattern)
        print(f"Strategy: {strategy['strategy_type']}")
    """
    debug_logger.log(
        "INFO",
        "Generating elimination strategy",
        pattern_type=pattern.original_violation.pattern_type,
        complexity_score=pattern.complexity_assessment.complexity_score,
    )

    try:
        # Get base strategy for pattern type
        base_strategy = _get_base_strategy(pattern.original_violation.pattern_type)

        # Customize based on complexity assessment
        customized_strategy = _customize_strategy_for_pattern(base_strategy, pattern)

        debug_logger.log(
            "INFO",
            "Strategy generated successfully",
            strategy_type=customized_strategy["strategy_type"],
            effort_hours=customized_strategy["effort_estimate_hours"],
        )

        return customized_strategy

    except Exception as e:
        debug_logger.log(
            "ERROR",
            "Strategy generation failed",
            pattern_type=pattern.original_violation.pattern_type,
            error=str(e),
        )
        raise StrategyGenerationError(f"Failed to generate strategy: {e}") from e

def _get_base_strategy(pattern_type: str) -> dict[str, Any]:
    """Get base strategy template for singleton pattern type."""
    strategies = {
        "metaclass_singleton": {
            "strategy_type": "dependency_injection_replacement",
            "description": "Replace metaclass singleton with dependency injection container",
            "implementation_steps": [
                "Remove metaclass singleton implementation",
                "Create factory function for instance creation",
                "Update all instantiation sites to use dependency injection",
                "Configure application context for instance management",
                "Add unit tests for new injection pattern",
            ],
            "base_effort_hours": 8,
            "risk_level": "medium",
            "prerequisites": ["dependency_injection_framework"],
            "tools_required": ["ast_refactoring", "test_coverage_tools"],
        },
        "decorator_singleton": {
            "strategy_type": "decorator_removal",
            "description": "Remove singleton decorator and implement factory pattern",
            "implementation_steps": [
                "Remove singleton decorator from class",
                "Create factory function for controlled instantiation",
                "Update all usage sites to use factory",
                "Implement proper lifecycle management",
                "Add tests for new instantiation pattern",
            ],
            "base_effort_hours": 6,
            "risk_level": "low",
            "prerequisites": [],
            "tools_required": ["ast_refactoring"],
        },
        "import_singleton": {
            "strategy_type": "import_refactoring",
            "description": "Refactor singleton imports to use dependency injection",
            "implementation_steps": [
                "Identify all 
                "Create dependency injection points",
                "Update import statements across modules",
                "Configure dependency injection container",
                "Update tests to use injection",
            ],
            "base_effort_hours": 5,
            "risk_level": "low",
            "prerequisites": ["dependency_injection_framework"],
            "tools_required": ["import_analyzer", "dependency_injection_tools"],
        },
        "global_variable_singleton": {
            "strategy_type": "global_refactoring",
            "description": "Replace global singleton variable with controlled access",
            "implementation_steps": [
                "Analyze global variable usage patterns",
                "Design replacement access pattern",
                "Implement controlled access mechanism",
                "Migrate all usage sites systematically",
                "Add comprehensive tests",
            ],
            "base_effort_hours": 10,
            "risk_level": "medium",
            "prerequisites": [],
            "tools_required": ["ast_refactoring", "usage_analyzer"],
        },
    }

    return strategies.get(pattern_type, _get_generic_strategy())

def _get_generic_strategy() -> dict[str, Any]:
    """Get generic strategy for unknown singleton pattern types."""
    return {
        "strategy_type": "general_refactoring",
        "description": "Analyze and refactor singleton pattern using best practices",
        "implementation_steps": [
            "Perform detailed pattern analysis",
            "Determine most appropriate replacement strategy",
            "Implement replacement pattern gradually",
            "Test migration at each step",
            "Complete full migration with validation",
        ],
        "base_effort_hours": 12,
        "risk_level": "medium",
        "prerequisites": ["pattern_analysis_tools"],
        "tools_required": ["ast_refactoring", "pattern_analyzer"],
    }

def _customize_strategy_for_pattern(
    base_strategy: dict[str, Any], pattern: Any
) -> dict[str, Any]:
    """Customize base strategy based on pattern complexity and dependencies."""
    # Get complexity data from existing assessment
    complexity_score = pattern.complexity_assessment.complexity_score
    dependency_count = len(pattern.dependent_files)
    effort_hours = pattern.complexity_assessment.estimated_effort_hours

    # Use existing effort estimate if available, otherwise calculate
    if effort_hours > 0:
        final_effort = effort_hours
    else:
        final_effort = _calculate_effort_with_dependencies(
            base_strategy["base_effort_hours"], complexity_score, dependency_count
        )

    # Determine final risk level based on complexity
    final_risk = _determine_risk_level(
        base_strategy["risk_level"], complexity_score, dependency_count
    )

    # Add migration notes from pattern analysis
    implementation_steps = base_strategy["implementation_steps"].copy()
    if pattern.migration_notes:
        implementation_steps.extend(
            [f"Note: {note}" for note in pattern.migration_notes]
        )

    return {
        "strategy_type": base_strategy["strategy_type"],
        "description": base_strategy["description"],
        "implementation_steps": implementation_steps,
        "effort_estimate_hours": final_effort,
        "risk_level": final_risk,
        "prerequisites": base_strategy["prerequisites"],
        "tools_required": base_strategy["tools_required"],
        "pattern_file": str(pattern.original_violation.file_path),
        "dependency_count": dependency_count,
        "complexity_score": complexity_score,
    }

def _calculate_effort_with_dependencies(
    base_hours: int, complexity_score: int, dependency_count: int
) -> int:
    """Calculate total effort including complexity and dependency factors."""
    # Complexity multiplier (score 1-10, multiply by 0.8-1.5)
    complexity_multiplier = 0.8 + (complexity_score - 1) * 0.07

    # Add 2 hours per dependency
    dependency_hours = dependency_count * 2

    total_effort = int(base_hours * complexity_multiplier) + dependency_hours

    # Minimum effort is 2 hours
    return max(2, total_effort)

def _determine_risk_level(
    base_risk: str, complexity_score: int, dependency_count: int
) -> str:
    """Determine final risk level based on complexity and dependencies."""
    # High complexity or many dependencies = higher risk
    if complexity_score >= 8 or dependency_count >= 5:
        return "high"
    elif complexity_score >= 6 or dependency_count >= 3:
        return "medium"
    else:
        return base_risk
