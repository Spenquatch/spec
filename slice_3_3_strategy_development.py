"""Slice 3.3: Migration Strategy Development and Planning.

This module consumes PatternAnalysisResult from Slice 3.2 and generates comprehensive
migration strategies for eliminating singleton patterns.
"""

from typing import Any

from slice_3_2_pattern_analysis import (
    PatternAnalysisResult,
)
from spec_cli.exceptions import SpecError
from spec_cli.logging.debug import debug_logger
from spec_cli.utils.migration_planning.strategy_generator import (
    generate_elimination_strategy,
)

class StrategyDevelopmentError(SpecError):
    """Exception raised when strategy development fails."""

    pass

def develop_migration_strategies(
    pattern_analysis_result: PatternAnalysisResult,
    project_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Develop comprehensive migration strategies for all classified patterns.

    Args:
        pattern_analysis_result: Complete pattern analysis from Slice 3.2
        project_constraints: Optional project-specific constraints

    Returns:
        Dictionary containing migration strategies, implementation order, and effort estimates

    Raises:
        StrategyDevelopmentError: If strategy development fails

    Example:
        >>> result = analyze_singleton_patterns(patterns, structure)
        >>> strategies = develop_migration_strategies(result)
        >>> print(f"Total patterns to migrate: {len(strategies['migration_strategies'])}")
    """
    debug_logger.log(
        "INFO",
        "Starting migration strategy development",
        pattern_count=len(pattern_analysis_result.classified_patterns),
        complexity_distribution=pattern_analysis_result.complexity_distribution,
    )

    if project_constraints is None:
        project_constraints = {}

    try:
        # Generate strategies for each classified pattern
        migration_strategies = {}
        for pattern in pattern_analysis_result.classified_patterns:
            pattern_key = str(pattern.original_violation.file_path)
            strategy = generate_elimination_strategy(pattern)
            migration_strategies[pattern_key] = strategy

        # Use existing migration priority order from Slice 3.2
        implementation_order = pattern_analysis_result.migration_priority_order

        # Calculate effort estimates
        effort_estimates = _calculate_effort_estimates(migration_strategies)

        # Generate implementation phases
        implementation_phases = _generate_implementation_phases(
            migration_strategies, implementation_order, effort_estimates
        )

        result = {
            "migration_strategies": migration_strategies,
            "implementation_order": implementation_order,
            "effort_estimates": effort_estimates,
            "implementation_phases": implementation_phases,
            "dependency_graph": pattern_analysis_result.dependency_graph,
            "total_patterns": len(pattern_analysis_result.classified_patterns),
            "complexity_distribution": pattern_analysis_result.complexity_distribution,
        }

        debug_logger.log(
            "INFO",
            "Migration strategy development completed",
            total_strategies=len(migration_strategies),
            total_effort_hours=effort_estimates["total_effort_hours"],
            phases=len(implementation_phases),
        )

        return result

    except Exception as e:
        raise StrategyDevelopmentError(
            f"Failed to develop migration strategies: {e}"
        ) from e

def _calculate_effort_estimates(
    migration_strategies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Calculate effort estimates for all migration strategies."""
    effort_by_pattern = {}
    effort_by_risk = {"low": 0, "medium": 0, "high": 0}
    effort_by_strategy = {}

    total_effort = 0

    for pattern_key, strategy in migration_strategies.items():
        effort_hours = strategy["effort_estimate_hours"]
        risk_level = strategy["risk_level"]
        strategy_type = strategy["strategy_type"]

        effort_by_pattern[pattern_key] = effort_hours
        effort_by_risk[risk_level] += effort_hours

        if strategy_type not in effort_by_strategy:
            effort_by_strategy[strategy_type] = 0
        effort_by_strategy[strategy_type] += effort_hours

        total_effort += effort_hours

    return {
        "total_effort_hours": total_effort,
        "effort_by_pattern": effort_by_pattern,
        "effort_by_risk_level": effort_by_risk,
        "effort_by_strategy_type": effort_by_strategy,
        "average_effort_per_pattern": total_effort / len(migration_strategies)
        if migration_strategies
        else 0,
    }

def _generate_implementation_phases(
    migration_strategies: dict[str, dict[str, Any]],
    implementation_order: list[str],
    effort_estimates: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate implementation phases based on risk levels and effort estimates."""
    phases = []

    # Phase 1: Critical and high-risk patterns (parallel execution where possible)
    critical_patterns = []
    for pattern_key in implementation_order:
        if pattern_key in migration_strategies:
            strategy = migration_strategies[pattern_key]
            if (
                strategy["risk_level"] in ["high"]
                or strategy["effort_estimate_hours"] > 15
            ):
                critical_patterns.append(pattern_key)

    if critical_patterns:
        phases.append(
            {
                "phase_number": 1,
                "phase_name": "Critical Pattern Migration",
                "description": "High-risk and complex patterns requiring focused attention",
                "patterns": critical_patterns,
                "estimated_effort_hours": sum(
                    migration_strategies[p]["effort_estimate_hours"]
                    for p in critical_patterns
                ),
                "execution_strategy": "sequential",
                "dependencies": [],
            }
        )

    # Phase 2: Medium-risk patterns (can be parallelized)
    medium_patterns = []
    for pattern_key in implementation_order:
        if pattern_key in migration_strategies and pattern_key not in critical_patterns:
            strategy = migration_strategies[pattern_key]
            if strategy["risk_level"] == "medium":
                medium_patterns.append(pattern_key)

    if medium_patterns:
        phases.append(
            {
                "phase_number": 2,
                "phase_name": "Medium Priority Migration",
                "description": "Medium-risk patterns with moderate effort requirements",
                "patterns": medium_patterns,
                "estimated_effort_hours": sum(
                    migration_strategies[p]["effort_estimate_hours"]
                    for p in medium_patterns
                ),
                "execution_strategy": "parallel",
                "dependencies": critical_patterns,
            }
        )

    # Phase 3: Low-risk patterns (batch processing)
    low_patterns = []
    for pattern_key in implementation_order:
        if (
            pattern_key in migration_strategies
            and pattern_key not in critical_patterns
            and pattern_key not in medium_patterns
        ):
            low_patterns.append(pattern_key)

    if low_patterns:
        phases.append(
            {
                "phase_number": 3,
                "phase_name": "Low Priority Migration",
                "description": "Low-risk patterns suitable for batch processing",
                "patterns": low_patterns,
                "estimated_effort_hours": sum(
                    migration_strategies[p]["effort_estimate_hours"]
                    for p in low_patterns
                ),
                "execution_strategy": "batch",
                "dependencies": critical_patterns + medium_patterns,
            }
        )

    return phases

def generate_migration_plan_document(
    strategy_result: dict[str, Any], output_format: str = "markdown"
) -> str:
    """Generate comprehensive migration plan document.

    Args:
        strategy_result: Result from develop_migration_strategies
        output_format: Output format ("markdown", "text", "json")

    Returns:
        Formatted migration plan document

    Raises:
        StrategyDevelopmentError: If document generation fails
    """
    try:
        if output_format == "markdown":
            return _generate_markdown_plan(strategy_result)
        elif output_format == "text":
            return _generate_text_plan(strategy_result)
        elif output_format == "json":
            import json

            return json.dumps(strategy_result, indent=2)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    except Exception as e:
        raise StrategyDevelopmentError(
            f"Failed to generate migration plan document: {e}"
        ) from e

def _generate_markdown_plan(strategy_result: dict[str, Any]) -> str:
    """Generate markdown format migration plan."""
    lines = [
        "# Singleton Pattern Migration Plan",
        "",
        "## Overview",
        f"- **Total Patterns**: {strategy_result['total_patterns']}",
        f"- **Total Effort**: {strategy_result['effort_estimates']['total_effort_hours']} hours",
        f"- **Implementation Phases**: {len(strategy_result['implementation_phases'])}",
        "",
        "## Complexity Distribution",
    ]

    for category, count in strategy_result["complexity_distribution"].items():
        lines.append(f"- **{category.title()}**: {count} patterns")

    lines.extend(
        [
            "",
            "## Implementation Phases",
            "",
        ]
    )

    for phase in strategy_result["implementation_phases"]:
        lines.extend(
            [
                f"### Phase {phase['phase_number']}: {phase['phase_name']}",
                f"**Description**: {phase['description']}",
                f"**Estimated Effort**: {phase['estimated_effort_hours']} hours",
                f"**Execution Strategy**: {phase['execution_strategy']}",
                f"**Pattern Count**: {len(phase['patterns'])}",
                "",
            ]
        )

    lines.extend(
        [
            "## Strategy Types",
            "",
        ]
    )

    for strategy_type, effort in strategy_result["effort_estimates"][
        "effort_by_strategy_type"
    ].items():
        lines.append(f"- **{strategy_type.replace('_', ' ').title()}**: {effort} hours")

    return "\n".join(lines)

def _generate_text_plan(strategy_result: dict[str, Any]) -> str:
    """Generate plain text format migration plan."""
    lines = [
        "SINGLETON PATTERN MIGRATION PLAN",
        "=" * 40,
        "",
        "OVERVIEW:",
        f"  Total Patterns: {strategy_result['total_patterns']}",
        f"  Total Effort: {strategy_result['effort_estimates']['total_effort_hours']} hours",
        f"  Implementation Phases: {len(strategy_result['implementation_phases'])}",
        "",
        "COMPLEXITY DISTRIBUTION:",
    ]

    for category, count in strategy_result["complexity_distribution"].items():
        lines.append(f"  {category.upper()}: {count} patterns")

    lines.extend(
        [
            "",
            "IMPLEMENTATION PHASES:",
            "",
        ]
    )

    for phase in strategy_result["implementation_phases"]:
        lines.extend(
            [
                f"Phase {phase['phase_number']}: {phase['phase_name']}",
                f"  Description: {phase['description']}",
                f"  Estimated Effort: {phase['estimated_effort_hours']} hours",
                f"  Execution: {phase['execution_strategy']}",
                f"  Patterns: {len(phase['patterns'])}",
                "",
            ]
        )

    return "\n".join(lines)
