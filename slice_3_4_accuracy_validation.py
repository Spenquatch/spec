"""Slice 3.4: Detection Accuracy Validation and Baseline Finalization.

This module validates detection system accuracy at >95% against known patterns
and finalizes singleton baseline for migration planning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from spec_cli.utils.pattern_analysis 
from spec_cli.utils.singleton_detection 
from spec_cli.utils.validation.detection_accuracy_validator import (
    AccuracyReport,
    SingletonPattern,
    calculate_baseline_completeness,
    validate_detection_accuracy,
)

logger = logging.getLogger(__name__)

@dataclass
class MigrationPlan:
    """Migration plan containing strategy and pattern information."""

    patterns: list[dict[str, Any]]
    coverage_percentage: float
    estimated_effort_hours: int
    risk_assessment: str
    implementation_steps: list[str]

@dataclass
class SingletonBaseline:
    """Finalized singleton baseline for migration planning."""

    total_patterns: int
    validated_patterns: list[dict[str, Any]]
    accuracy_report: AccuracyReport
    completeness_metrics: dict[str, Any]
    migration_readiness: bool
    baseline_timestamp: str
    approval_status: bool

def validate_singleton_detection_accuracy(
    target_directory: Path,
    known_patterns: list[str],
    accuracy_threshold: float = 0.95,
) -> AccuracyReport:
    """Validate detection accuracy against known singleton patterns.

    Args:
        target_directory: Directory to scan for singleton patterns
        known_patterns: List of known singleton pattern locations
        accuracy_threshold: Minimum accuracy required for validation

    Returns:
        AccuracyReport containing detailed accuracy metrics

    Raises:
        ValueError: If target_directory doesn't exist or accuracy_threshold invalid
        RuntimeError: If detection system fails to execute
    """
    if not target_directory.exists():
        raise ValueError(f"Target directory does not exist: {target_directory}")

    if not (0 <= accuracy_threshold <= 1):
        raise ValueError("Accuracy threshold must be between 0 and 1")

    logger.info(
        "Starting singleton detection accuracy validation: target_directory=%s, known_patterns_count=%d, accuracy_threshold=%f",
        str(target_directory),
        len(known_patterns),
        accuracy_threshold,
    )

    try:
        # Use existing singleton detection utilities - scan all Python files in directory
        detected_patterns = []
        for python_file in target_directory.glob("**/*.py"):
            try:
                violations = scan_for_singleton_patterns(python_file)
                for violation in violations:
                    pattern = SingletonPattern(
                        file_path=violation.file_path,
                        pattern_type=violation.pattern_type,
                        line_number=violation.line_number,
                        confidence_score=0.85,  # Default confidence for detected patterns
                        description=violation.description,
                    )
                    detected_patterns.append(pattern)
            except Exception as e:
                logger.warning("Failed to scan file %s: %s", python_file, str(e))
                continue

        # Validate detection accuracy using helper
        accuracy_report = validate_detection_accuracy(
            detected_patterns, known_patterns, accuracy_threshold
        )

        logger.info(
            "Detection accuracy validation completed: accuracy_percentage=%f, threshold_met=%s, validation_passed=%s",
            accuracy_report.accuracy_percentage,
            accuracy_report.accuracy_threshold_met,
            accuracy_report.validation_passed,
        )

        return accuracy_report

    except Exception as e:
        logger.error("Detection accuracy validation failed: %s", str(e))
        raise RuntimeError(f"Detection system execution failed: {e}") from e

def finalize_singleton_baseline(
    accuracy_report: AccuracyReport,
    migration_plan: MigrationPlan,
    target_directory: Path,
) -> SingletonBaseline:
    """Finalize singleton baseline for approved migration planning.

    Args:
        accuracy_report: Detection accuracy validation results
        migration_plan: Migration strategy and implementation plan
        target_directory: Directory containing validated singleton patterns

    Returns:
        SingletonBaseline with finalized metrics and approval status

    Raises:
        ValueError: If accuracy report doesn't meet baseline requirements
        RuntimeError: If baseline finalization process fails
    """
    if not accuracy_report.validation_passed:
        raise ValueError(
            "Accuracy report validation must pass for baseline finalization"
        )

    logger.info(
        "Starting singleton baseline finalization: accuracy_percentage=%f, migration_coverage=%f",
        accuracy_report.accuracy_percentage,
        migration_plan.coverage_percentage,
    )

    try:
        # Calculate pattern diversity score using pattern analysis utilities
        pattern_diversity_score = _calculate_pattern_diversity(
            accuracy_report, target_directory
        )

        # Calculate baseline completeness metrics
        completeness_metrics = calculate_baseline_completeness(
            accuracy_report,
            migration_plan.coverage_percentage / 100.0,  # Convert to decimal
            pattern_diversity_score,
        )

        # Prepare validated patterns for baseline
        validated_patterns = _prepare_validated_patterns(
            accuracy_report, migration_plan
        )

        # Determine migration readiness
        migration_readiness = (
            completeness_metrics["baseline_ready"]
            and accuracy_report.accuracy_percentage >= 0.95
        )

        # Generate baseline timestamp
        from datetime import datetime

        baseline_timestamp = datetime.now().isoformat()

        # Final approval status
        approval_status = (
            migration_readiness
            and accuracy_report.baseline_approved
            and len(validated_patterns) > 0
        )

        singleton_baseline = SingletonBaseline(
            total_patterns=accuracy_report.total_detected_patterns,
            validated_patterns=validated_patterns,
            accuracy_report=accuracy_report,
            completeness_metrics=completeness_metrics,
            migration_readiness=migration_readiness,
            baseline_timestamp=baseline_timestamp,
            approval_status=approval_status,
        )

        logger.info(
            "Singleton baseline finalization completed: total_patterns=%d, migration_readiness=%s, approval_status=%s, completeness_score=%f",
            singleton_baseline.total_patterns,
            migration_readiness,
            approval_status,
            completeness_metrics["completeness_score"],
        )

        return singleton_baseline

    except Exception as e:
        logger.error("Baseline finalization failed: %s", str(e))
        raise RuntimeError(f"Baseline finalization process failed: {e}") from e

def _calculate_pattern_diversity(
    accuracy_report: AccuracyReport, target_directory: Path
) -> float:
    """Calculate pattern diversity score for baseline completeness.

    Args:
        accuracy_report: Detection accuracy results
        target_directory: Directory containing patterns

    Returns:
        Pattern diversity score between 0 and 1
    """
    try:
        # Use pattern analysis utilities to assess diversity
        pattern_types = set()
        complexity_scores = []

        # Analyze patterns from false positive details
        for fp_detail in accuracy_report.false_positive_details:
            pattern_types.add(fp_detail.get("pattern_type", "unknown"))

        # Use existing pattern analysis to get complexity data from Python files
        for python_file in target_directory.glob("**/*.py"):
            try:
                usage_results = analyze_singleton_usage(python_file)
                for usage in usage_results:
                    # Extract complexity information from usage patterns
                    if hasattr(usage, "complexity_score"):
                        complexity_scores.append(usage.complexity_score)
            except Exception:
                continue  # Skip files that can't be analyzed

        # Calculate diversity based on pattern type variety and complexity spread
        type_diversity = min(len(pattern_types) / 5.0, 1.0)  # Max 5 pattern types

        complexity_diversity = 0.5  # Default if no complexity data
        if complexity_scores:
            # Standard deviation indicates diversity
            import statistics

            if len(complexity_scores) > 1:
                std_dev = statistics.stdev(complexity_scores)
                complexity_diversity = min(std_dev / 10.0, 1.0)

        # Combined diversity score
        diversity_score = (type_diversity + complexity_diversity) / 2.0

        logger.debug(
            "Pattern diversity calculated: type_diversity=%f, complexity_diversity=%f, final_score=%f",
            type_diversity,
            complexity_diversity,
            diversity_score,
        )

        return diversity_score

    except Exception as e:
        logger.warning("Pattern diversity calculation failed: %s", str(e))
        return 0.5  # Return moderate diversity score as fallback

def _prepare_validated_patterns(
    accuracy_report: AccuracyReport, migration_plan: MigrationPlan
) -> list[dict[str, Any]]:
    """Prepare validated pattern data for baseline storage.

    Args:
        accuracy_report: Detection accuracy results
        migration_plan: Migration strategy information

    Returns:
        List of validated pattern dictionaries
    """
    validated_patterns = []

    # Include true positive patterns as validated
    for pattern_data in migration_plan.patterns:
        validated_pattern = {
            "file_path": pattern_data.get("file_path", ""),
            "line_number": pattern_data.get("line_number", 0),
            "pattern_type": pattern_data.get("pattern_type", "unknown"),
            "complexity_score": pattern_data.get("complexity_score", 0),
            "migration_strategy": pattern_data.get("migration_strategy", ""),
            "effort_estimate": pattern_data.get("effort_estimate", 0),
            "validation_status": "validated",
            "detection_confidence": pattern_data.get("confidence_score", 0.0),
        }
        validated_patterns.append(validated_pattern)

    logger.debug(
        "Validated patterns prepared: total_patterns=%d",
        len(validated_patterns),
    )

    return validated_patterns

def generate_accuracy_validation_report(
    baseline: SingletonBaseline, output_path: Path | None = None
) -> dict[str, Any]:
    """Generate comprehensive accuracy validation report.

    Args:
        baseline: Finalized singleton baseline
        output_path: Optional path to save report file

    Returns:
        Dictionary containing complete validation report

    Raises:
        ValueError: If baseline is invalid or incomplete
    """
    if not baseline.approval_status:
        raise ValueError("Baseline must be approved to generate validation report")

    logger.info(
        "Generating accuracy validation report: total_patterns=%d, output_path=%s",
        baseline.total_patterns,
        str(output_path) if output_path else "memory_only",
    )

    # Compile comprehensive report
    report = {
        "validation_summary": {
            "total_patterns_detected": baseline.total_patterns,
            "validation_passed": baseline.accuracy_report.validation_passed,
            "accuracy_percentage": baseline.accuracy_report.accuracy_percentage,
            "migration_readiness": baseline.migration_readiness,
            "baseline_approved": baseline.approval_status,
            "validation_timestamp": baseline.baseline_timestamp,
        },
        "accuracy_metrics": {
            "true_positives": baseline.accuracy_report.true_positives,
            "false_positives": baseline.accuracy_report.false_positives,
            "false_negatives": baseline.accuracy_report.false_negatives,
            "precision": baseline.accuracy_report.precision,
            "recall": baseline.accuracy_report.recall,
            "f1_score": baseline.accuracy_report.f1_score,
        },
        "completeness_analysis": baseline.completeness_metrics,
        "validated_patterns": baseline.validated_patterns,
        "quality_issues": {
            "false_positive_details": baseline.accuracy_report.false_positive_details,
            "false_negative_details": baseline.accuracy_report.false_negative_details,
        },
    }

    # Save report to file if path provided
    if output_path:
        try:
            import json

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info("Validation report saved: file_path=%s", str(output_path))
        except Exception as e:
            logger.warning("Failed to save report to file: %s", str(e))

    return report
