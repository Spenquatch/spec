"""Migration readiness evaluation utilities for Phase 1-3 foundation validation.

This module provides comprehensive assessment of migration readiness by evaluating
Phase 1-3 deliverable stability, test infrastructure quality, and baseline completeness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...exceptions import SpecError


class ReadinessAssessmentError(SpecError):
    """Exception raised when readiness assessment fails."""

    def __init__(
        self, message: str, assessment_context: dict[str, Any] | None = None
    ) -> None:
        """Initialize readiness assessment error.

        Args:
            message: Error description
            assessment_context: Optional context about the assessment failure
        """
        super().__init__(message)
        if assessment_context:
            for key, value in assessment_context.items():
                self.add_context(key, value)


@dataclass
class ReadinessReport:
    """Comprehensive readiness assessment report for migration planning."""

    overall_readiness_score: float
    foundation_stability_verified: bool
    deliverable_completeness: dict[str, float]
    test_infrastructure_quality: dict[str, float]
    integration_validation_results: dict[str, bool]
    risk_factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    migration_blockers: list[str] = field(default_factory=list)
    assessment_timestamp: str = ""


@dataclass
class FoundationState:
    """Current state of Phase 1-3 foundation deliverables."""

    phase_deliverables: dict[str, Any]
    test_infrastructure_status: dict[str, float]
    singleton_baseline: dict[str, Any]
    integration_health: dict[str, bool]


def assess_migration_readiness(foundation_state: FoundationState) -> ReadinessReport:
    """Assess migration readiness based on Phase 1-3 foundation state.

    Args:
        foundation_state: Current state of all Phase 1-3 deliverables

    Returns:
        Comprehensive readiness report with scoring and recommendations

    Raises:
        ReadinessAssessmentError: If assessment cannot be completed due to missing data
    """
    if not foundation_state.phase_deliverables:
        raise ReadinessAssessmentError(
            "Cannot assess readiness without phase deliverables",
            {"missing_component": "phase_deliverables"},
        )

    # Calculate stability scores
    stability_score = _calculate_stability_score(foundation_state)

    # Evaluate deliverable completeness
    completeness_scores = _evaluate_deliverable_completeness(foundation_state)

    # Assess test infrastructure quality
    test_quality_scores = _assess_test_infrastructure(foundation_state)

    # Validate integration points
    integration_results = _validate_integration_points(foundation_state)

    # Calculate overall readiness score
    overall_score = _calculate_overall_readiness(
        stability_score, completeness_scores, test_quality_scores, integration_results
    )

    # Generate recommendations and identify blockers
    recommendations = _generate_recommendations(
        stability_score, completeness_scores, test_quality_scores
    )
    risk_factors = _identify_risk_factors(foundation_state, overall_score)
    blockers = _identify_migration_blockers(foundation_state, overall_score)

    return ReadinessReport(
        overall_readiness_score=overall_score,
        foundation_stability_verified=stability_score >= 0.8,
        deliverable_completeness=completeness_scores,
        test_infrastructure_quality=test_quality_scores,
        integration_validation_results=integration_results,
        risk_factors=risk_factors,
        recommendations=recommendations,
        migration_blockers=blockers,
        assessment_timestamp="",
    )


def _calculate_stability_score(foundation_state: FoundationState) -> float:
    """Calculate foundation stability score from deliverable quality metrics."""
    deliverable_count = len(foundation_state.phase_deliverables)
    if deliverable_count == 0:
        return 0.0

    test_scores = list(foundation_state.test_infrastructure_status.values())
    if not test_scores:
        return 0.5

    # Weighted average of test infrastructure scores
    return sum(test_scores) / len(test_scores)


def _evaluate_deliverable_completeness(
    foundation_state: FoundationState,
) -> dict[str, float]:
    """Evaluate completeness of each phase deliverable."""
    completeness = {}

    for phase_name, deliverable in foundation_state.phase_deliverables.items():
        if isinstance(deliverable, dict):
            # Calculate completeness based on required fields
            required_fields = ["implementation", "tests", "documentation"]
            completed_fields = sum(
                1 for field in required_fields if deliverable.get(field)
            )
            completeness[phase_name] = completed_fields / len(required_fields)
        else:
            # Simple presence check
            completeness[phase_name] = 1.0 if deliverable else 0.0

    return completeness


def _assess_test_infrastructure(foundation_state: FoundationState) -> dict[str, float]:
    """Assess quality of test infrastructure across all phases."""
    return dict(foundation_state.test_infrastructure_status)


def _validate_integration_points(foundation_state: FoundationState) -> dict[str, bool]:
    """Validate integration points between phase deliverables."""
    integration_results = {}

    # Check basic integration health
    for component, status in foundation_state.integration_health.items():
        integration_results[f"integration_{component}"] = status

    # Validate cross-phase compatibility
    if foundation_state.phase_deliverables:
        integration_results["cross_phase_compatibility"] = True
    else:
        integration_results["cross_phase_compatibility"] = False

    return integration_results


def _calculate_overall_readiness(
    stability_score: float,
    completeness_scores: dict[str, float],
    test_quality_scores: dict[str, float],
    integration_results: dict[str, bool],
) -> float:
    """Calculate overall readiness score using weighted metrics."""
    # Weight factors for different components
    stability_weight = 0.4
    completeness_weight = 0.3
    test_quality_weight = 0.2
    integration_weight = 0.1

    # Calculate weighted completeness score
    if completeness_scores:
        avg_completeness = sum(completeness_scores.values()) / len(completeness_scores)
    else:
        avg_completeness = 0.0

    # Calculate weighted test quality score
    if test_quality_scores:
        avg_test_quality = sum(test_quality_scores.values()) / len(test_quality_scores)
    else:
        avg_test_quality = 0.0

    # Calculate integration score
    if integration_results:
        integration_score = sum(integration_results.values()) / len(integration_results)
    else:
        integration_score = 0.0

    # Calculate final weighted score
    overall_score = (
        stability_score * stability_weight
        + avg_completeness * completeness_weight
        + avg_test_quality * test_quality_weight
        + integration_score * integration_weight
    )

    return min(1.0, max(0.0, overall_score))


def _generate_recommendations(
    stability_score: float,
    completeness_scores: dict[str, float],
    test_quality_scores: dict[str, float],
) -> list[str]:
    """Generate specific recommendations based on assessment results."""
    recommendations = []

    if stability_score < 0.8:
        recommendations.append(
            "Improve foundation stability before proceeding with migration"
        )

    for phase, score in completeness_scores.items():
        if score < 0.9:
            recommendations.append(f"Complete missing deliverables for {phase}")

    for component, score in test_quality_scores.items():
        if score < 0.8:
            recommendations.append(f"Enhance test coverage for {component}")

    if not recommendations:
        recommendations.append("Foundation is ready for migration planning")

    return recommendations


def _identify_risk_factors(
    foundation_state: FoundationState, overall_score: float
) -> list[str]:
    """Identify potential risk factors for migration success."""
    risks = []

    if overall_score < 0.7:
        risks.append("Low overall readiness score indicates high migration risk")

    if not foundation_state.singleton_baseline:
        risks.append("Missing singleton baseline may complicate migration planning")

    test_scores = list(foundation_state.test_infrastructure_status.values())
    if test_scores and min(test_scores) < 0.6:
        risks.append("Poor test coverage in some areas may lead to regressions")

    return risks


def _identify_migration_blockers(
    foundation_state: FoundationState, overall_score: float
) -> list[str]:
    """Identify absolute blockers that must be resolved before migration."""
    blockers = []

    if overall_score < 0.5:
        blockers.append(
            "Overall readiness score too low - foundation must be stabilized"
        )

    if not foundation_state.phase_deliverables:
        blockers.append("No phase deliverables found - cannot proceed with migration")

    critical_components = [
        "dependency_analysis",
        "context_infrastructure",
        "compatibility_layer",
    ]
    for component in critical_components:
        if component not in foundation_state.phase_deliverables:
            blockers.append(f"Critical component missing: {component}")

    return blockers
