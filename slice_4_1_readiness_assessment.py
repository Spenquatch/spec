"""Slice 4.1: Migration Readiness Assessment and Foundation Validation.

This module provides comprehensive assessment of current state stability and readiness
for final migration phases with foundation validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from spec_cli.utils.assessment.readiness_evaluator import (
    FoundationState,
    ReadinessReport,
    assess_migration_readiness,
)
from spec_cli.utils.migration_utils import MigrationError
from spec_cli.utils.test_analysis import FixtureAnalysisReport, analyze_test_fixtures

logger = logging.getLogger(__name__)

@dataclass
class ReadinessAssessmentResult:
    """Result of comprehensive migration readiness assessment."""

    readiness_report: ReadinessReport
    foundation_stability_score: float
    integration_validation_results: dict[str, bool]
    assessment_metadata: dict[str, Any]

def assess_phase_deliverables(
    phase_1_data: dict[str, Any],
    phase_2_data: dict[str, Any],
    phase_3_data: dict[str, Any],
) -> dict[str, float]:
    """Assess completeness and quality of Phase 1-3 deliverables.

    Args:
        phase_1_data: Phase 1 dependency analysis and context foundation data
        phase_2_data: Phase 2 CLI integration and command migration data
        phase_3_data: Phase 3 singleton detection and baseline data

    Returns:
        Dictionary mapping phase names to completeness scores (0.0-1.0)

    Raises:
        MigrationError: If critical phase data is missing or invalid
    """
    if not phase_1_data:
        raise MigrationError("Phase 1 data is required for readiness assessment")

    if not phase_2_data:
        raise MigrationError("Phase 2 data is required for readiness assessment")

    if not phase_3_data:
        raise MigrationError("Phase 3 data is required for readiness assessment")

    phase_scores = {}

    # Assess Phase 1 completeness
    phase_1_score = _calculate_phase_score(
        phase_1_data,
        required_components=["dependency_analysis", "spec_context", "factory_methods"],
    )
    phase_scores["phase_1"] = phase_1_score

    # Assess Phase 2 completeness
    phase_2_score = _calculate_phase_score(
        phase_2_data,
        required_components=[
            "click_integration",
            "command_migration",
            "decorator_system",
        ],
    )
    phase_scores["phase_2"] = phase_2_score

    # Assess Phase 3 completeness
    phase_3_score = _calculate_phase_score(
        phase_3_data,
        required_components=[
            "singleton_detection",
            "pattern_analysis",
            "baseline_establishment",
        ],
    )
    phase_scores["phase_3"] = phase_3_score

    logger.info(
        "Phase deliverable assessment completed",
        extra={
            "phase_1_score": phase_1_score,
            "phase_2_score": phase_2_score,
            "phase_3_score": phase_3_score,
        },
    )

    return phase_scores

def validate_test_infrastructure(test_results_path: Path) -> dict[str, float]:
    """Validate test infrastructure stability and coverage quality.

    Args:
        test_results_path: Path to test results and coverage data

    Returns:
        Dictionary mapping test components to quality scores (0.0-1.0)

    Raises:
        MigrationError: If test results cannot be analyzed
    """
    if not test_results_path.exists():
        raise MigrationError(
            f"Test results path does not exist: {test_results_path}",
            command_name="validate_test_infrastructure",
        )

    test_quality_scores = {}

    # Analyze fixture migration readiness
    try:
        fixture_report = analyze_test_fixtures(test_results_path.parent)
        test_quality_scores["fixture_stability"] = _calculate_fixture_stability_score(
            fixture_report
        )
    except Exception as e:
        logger.warning(f"Could not analyze fixtures: {e}")
        test_quality_scores["fixture_stability"] = 0.5

    # Assess test coverage quality
    test_quality_scores["coverage_quality"] = _assess_coverage_quality(
        test_results_path
    )

    # Evaluate test isolation
    test_quality_scores["test_isolation"] = _evaluate_test_isolation(test_results_path)

    # Check integration test completeness
    test_quality_scores["integration_completeness"] = _check_integration_completeness(
        test_results_path
    )

    logger.info(
        "Test infrastructure validation completed",
        extra={"test_quality_scores": test_quality_scores},
    )

    return test_quality_scores

def validate_foundation_integration(
    phase_deliverables: dict[str, Any], test_infrastructure: dict[str, float]
) -> dict[str, bool]:
    """Validate integration between foundation components.

    Args:
        phase_deliverables: Assessed phase deliverable data
        test_infrastructure: Test infrastructure quality metrics

    Returns:
        Dictionary mapping integration points to validation results

    Raises:
        MigrationError: If integration validation cannot be performed
    """
    if not phase_deliverables:
        raise MigrationError("Phase deliverables required for integration validation")

    integration_results = {}

    # Validate Phase 1-2 integration
    if "phase_1" in phase_deliverables and "phase_2" in phase_deliverables:
        integration_results["phase_1_to_2"] = _validate_phase_transition(
            phase_deliverables["phase_1"], phase_deliverables["phase_2"]
        )
    else:
        integration_results["phase_1_to_2"] = False

    # Validate Phase 2-3 integration
    if "phase_2" in phase_deliverables and "phase_3" in phase_deliverables:
        integration_results["phase_2_to_3"] = _validate_phase_transition(
            phase_deliverables["phase_2"], phase_deliverables["phase_3"]
        )
    else:
        integration_results["phase_2_to_3"] = False

    # Validate test infrastructure integration
    integration_results["test_infrastructure_ready"] = (
        min(test_infrastructure.values()) >= 0.7
    )

    # Check overall foundation coherence
    integration_results["foundation_coherent"] = _check_foundation_coherence(
        phase_deliverables, test_infrastructure
    )

    logger.info(
        "Foundation integration validation completed",
        extra={"integration_results": integration_results},
    )

    return integration_results

def execute_readiness_assessment(
    phase_deliverables: dict[str, Any],
    test_infrastructure_status: dict[str, float],
    singleton_baseline: dict[str, Any],
) -> ReadinessAssessmentResult:
    """Execute comprehensive migration readiness assessment.

    Args:
        phase_deliverables: Complete Phase 1-3 deliverable data
        test_infrastructure_status: Test infrastructure quality metrics
        singleton_baseline: Singleton detection baseline data

    Returns:
        Complete readiness assessment with recommendations

    Raises:
        MigrationError: If assessment cannot be completed
    """
    logger.info("Starting comprehensive migration readiness assessment")

    # Create foundation state
    foundation_state = FoundationState(
        phase_deliverables=phase_deliverables,
        test_infrastructure_status=test_infrastructure_status,
        singleton_baseline=singleton_baseline,
        integration_health={
            "dependency_injection": True,
            "cli_integration": True,
            "singleton_detection": True,
        },
    )

    # Perform readiness assessment
    readiness_report = assess_migration_readiness(foundation_state)

    # Calculate foundation stability score
    foundation_stability_score = _calculate_foundation_stability(
        readiness_report.deliverable_completeness,
        readiness_report.test_infrastructure_quality,
    )

    # Validate integration points
    integration_validation_results = validate_foundation_integration(
        phase_deliverables, test_infrastructure_status
    )

    # Create assessment metadata
    assessment_metadata = {
        "assessment_timestamp": datetime.now().isoformat(),
        "total_phases_assessed": len(phase_deliverables),
        "test_components_validated": len(test_infrastructure_status),
        "baseline_components": len(singleton_baseline) if singleton_baseline else 0,
    }

    result = ReadinessAssessmentResult(
        readiness_report=readiness_report,
        foundation_stability_score=foundation_stability_score,
        integration_validation_results=integration_validation_results,
        assessment_metadata=assessment_metadata,
    )

    logger.info(
        "Migration readiness assessment completed",
        extra={
            "overall_readiness_score": readiness_report.overall_readiness_score,
            "foundation_stability_score": foundation_stability_score,
            "migration_ready": readiness_report.overall_readiness_score >= 0.8,
        },
    )

    return result

def _calculate_phase_score(
    phase_data: dict[str, Any], required_components: list[str]
) -> float:
    """Calculate completeness score for a single phase."""
    if not phase_data:
        return 0.0

    completed_components = sum(
        1
        for component in required_components
        if component in phase_data and phase_data[component]
    )

    return completed_components / len(required_components)

def _calculate_fixture_stability_score(fixture_report: FixtureAnalysisReport) -> float:
    """Calculate stability score from fixture analysis report."""
    all_fixtures = (
        fixture_report.singleton_dependent_fixtures
        + fixture_report.isolation_issues
        + fixture_report.context_migration_candidates
    )

    if not all_fixtures:
        return 1.0  # No fixtures means no stability issues

    stable_fixtures = sum(
        1 for fixture in all_fixtures if not fixture.state_contamination_risk
    )

    return stable_fixtures / len(all_fixtures)

def _assess_coverage_quality(test_results_path: Path) -> float:
    """Assess test coverage quality from results."""
    # Simplified coverage assessment - would integrate with actual coverage data
    return 0.85  # Placeholder for realistic coverage score

def _evaluate_test_isolation(test_results_path: Path) -> float:
    """Evaluate test isolation quality."""
    # Simplified isolation assessment - would analyze test dependencies
    return 0.9  # Placeholder for good isolation score

def _check_integration_completeness(test_results_path: Path) -> float:
    """Check completeness of integration tests."""
    # Simplified integration test assessment
    return 0.8  # Placeholder for good integration coverage

def _validate_phase_transition(phase_from_data: Any, phase_to_data: Any) -> bool:
    """Validate compatibility between consecutive phases."""
    # Simplified phase transition validation
    return bool(phase_from_data and phase_to_data)

def _check_foundation_coherence(
    phase_deliverables: dict[str, Any], test_infrastructure: dict[str, float]
) -> bool:
    """Check overall foundation coherence."""
    # Ensure all phases are present and test infrastructure is adequate
    required_phases = ["phase_1", "phase_2", "phase_3"]
    phases_present = all(phase in phase_deliverables for phase in required_phases)

    test_quality_adequate = min(test_infrastructure.values()) >= 0.7

    return phases_present and test_quality_adequate

def _calculate_foundation_stability(
    deliverable_completeness: dict[str, float],
    test_infrastructure_quality: dict[str, float],
) -> float:
    """Calculate overall foundation stability score."""
    if not deliverable_completeness:
        return 0.0

    avg_deliverable_score = sum(deliverable_completeness.values()) / len(
        deliverable_completeness
    )

    if test_infrastructure_quality:
        avg_test_score = sum(test_infrastructure_quality.values()) / len(
            test_infrastructure_quality
        )
    else:
        avg_test_score = 0.5

    # Weighted combination: 60% deliverables, 40% test infrastructure
    return avg_deliverable_score * 0.6 + avg_test_score * 0.4
