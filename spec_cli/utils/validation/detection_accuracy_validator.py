"""Detection accuracy validation utilities for singleton detection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class AccuracyReport:
    """Report containing detection accuracy metrics and validation results."""

    true_positives: int
    false_positives: int
    false_negatives: int
    total_known_patterns: int
    total_detected_patterns: int
    precision: float
    recall: float
    f1_score: float
    accuracy_percentage: float
    validation_passed: bool
    accuracy_threshold_met: bool
    false_positive_details: list[dict[str, Any]]
    false_negative_details: list[dict[str, Any]]
    baseline_approved: bool

@dataclass
class SingletonPattern:
    """Represents a detected singleton pattern for accuracy validation."""

    file_path: Path
    pattern_type: str
    line_number: int
    confidence_score: float
    description: str

    def __hash__(self) -> int:
        """Make pattern hashable for set operations."""
        return hash((str(self.file_path), self.pattern_type, self.line_number))

    def __eq__(self, other: object) -> bool:
        """Check equality based on location (file, type, line)."""
        if not isinstance(other, SingletonPattern):
            return False
        return (
            str(self.file_path) == str(other.file_path)
            and self.pattern_type == other.pattern_type
            and self.line_number == other.line_number
        )

def validate_detection_accuracy(
    detected_patterns: list[SingletonPattern],
    known_patterns: list[str],
    accuracy_threshold: float = 0.95,
) -> AccuracyReport:
    """Validate detection accuracy against known singleton patterns.

    Args:
        detected_patterns: List of detected singleton patterns from detection system
        known_patterns: List of known singleton pattern locations (file:line format)
        accuracy_threshold: Minimum accuracy required for validation (default: 0.95)

    Returns:
        AccuracyReport containing detailed accuracy metrics and validation results

    Raises:
        ValueError: If accuracy_threshold is not between 0 and 1
        TypeError: If inputs are not of expected types
    """
    if not (0 <= accuracy_threshold <= 1):
        raise ValueError("Accuracy threshold must be between 0 and 1")

    if not isinstance(detected_patterns, list):
        raise TypeError("detected_patterns must be a list")

    if not isinstance(known_patterns, list):
        raise TypeError("known_patterns must be a list")

    logger.info(
        "Starting detection accuracy validation: total_detected=%d, total_known=%d, accuracy_threshold=%f",
        len(detected_patterns),
        len(known_patterns),
        accuracy_threshold,
    )

    # Convert known patterns to comparable format
    known_locations = _parse_known_pattern_locations(known_patterns)
    detected_locations = _extract_detected_locations(detected_patterns)

    # Calculate accuracy metrics
    true_positives = len(detected_locations.intersection(known_locations))
    false_positives = len(detected_locations - known_locations)
    false_negatives = len(known_locations - detected_locations)

    total_known = len(known_locations)
    total_detected = len(detected_locations)

    # Calculate precision, recall, and F1 score
    precision = true_positives / total_detected if total_detected > 0 else 0.0
    recall = true_positives / total_known if total_known > 0 else 0.0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # Calculate overall accuracy
    total_possible = max(total_known, total_detected)
    accuracy_percentage = true_positives / total_possible if total_possible > 0 else 0.0

    # Check if accuracy threshold is met
    accuracy_threshold_met = accuracy_percentage >= accuracy_threshold

    # Generate detailed false positive/negative information
    false_positive_details = _generate_false_positive_details(
        detected_patterns, detected_locations - known_locations
    )
    false_negative_details = _generate_false_negative_details(
        known_patterns, known_locations - detected_locations
    )

    # Determine if validation passed (accuracy threshold met and no critical issues)
    validation_passed = accuracy_threshold_met and false_positives <= total_known * 0.1

    # Baseline approval requires high accuracy and low false positive rate
    baseline_approved = validation_passed and accuracy_percentage >= 0.95

    logger.info(
        "Detection accuracy validation completed: true_positives=%d, false_positives=%d, false_negatives=%d, precision=%f, recall=%f, f1_score=%f, accuracy_percentage=%f, threshold_met=%s, validation_passed=%s, baseline_approved=%s",
        true_positives,
        false_positives,
        false_negatives,
        precision,
        recall,
        f1_score,
        accuracy_percentage,
        accuracy_threshold_met,
        validation_passed,
        baseline_approved,
    )

    return AccuracyReport(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        total_known_patterns=total_known,
        total_detected_patterns=total_detected,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        accuracy_percentage=accuracy_percentage,
        validation_passed=validation_passed,
        accuracy_threshold_met=accuracy_threshold_met,
        false_positive_details=false_positive_details,
        false_negative_details=false_negative_details,
        baseline_approved=baseline_approved,
    )

def _parse_known_pattern_locations(known_patterns: list[str]) -> set[str]:
    """Parse known pattern locations into standardized format."""
    locations = set()
    for pattern in known_patterns:
        if ":" in pattern:
            # Format: "file_path:line_number"
            file_part, line_part = pattern.rsplit(":", 1)
            try:
                line_num = int(line_part)
                normalized_location = f"{Path(file_part).as_posix()}:{line_num}"
                locations.add(normalized_location)
            except ValueError:
                logger.warning("Invalid known pattern format: %s", pattern)
                continue
        else:
            logger.warning("Known pattern missing line number: %s", pattern)

    return locations

def _extract_detected_locations(detected_patterns: list[SingletonPattern]) -> set[str]:
    """Extract detected pattern locations in standardized format."""
    locations = set()
    for pattern in detected_patterns:
        normalized_location = f"{pattern.file_path.as_posix()}:{pattern.line_number}"
        locations.add(normalized_location)

    return locations

def _generate_false_positive_details(
    detected_patterns: list[SingletonPattern], false_positive_locations: set[str]
) -> list[dict[str, Any]]:
    """Generate detailed information about false positive detections."""
    details = []

    for pattern in detected_patterns:
        location = f"{pattern.file_path.as_posix()}:{pattern.line_number}"
        if location in false_positive_locations:
            details.append(
                {
                    "file_path": str(pattern.file_path),
                    "line_number": pattern.line_number,
                    "pattern_type": pattern.pattern_type,
                    "confidence_score": pattern.confidence_score,
                    "description": pattern.description,
                    "issue": "Not a known singleton pattern",
                }
            )

    return details

def _generate_false_negative_details(
    known_patterns: list[str], false_negative_locations: set[str]
) -> list[dict[str, Any]]:
    """Generate detailed information about false negative detections."""
    details = []

    for pattern in known_patterns:
        if ":" in pattern:
            file_part, line_part = pattern.rsplit(":", 1)
            try:
                line_num = int(line_part)
                location = f"{Path(file_part).as_posix()}:{line_num}"
                if location in false_negative_locations:
                    details.append(
                        {
                            "file_path": file_part,
                            "line_number": line_num,
                            "pattern": pattern,
                            "issue": "Known singleton pattern not detected",
                        }
                    )
            except ValueError:
                continue

    return details

def calculate_baseline_completeness(
    accuracy_report: AccuracyReport,
    migration_coverage: float,
    pattern_diversity_score: float,
) -> dict[str, Any]:
    """Calculate completeness metrics for singleton baseline finalization.

    Args:
        accuracy_report: Detection accuracy validation results
        migration_coverage: Percentage of codebase covered by migration planning
        pattern_diversity_score: Score indicating variety of singleton patterns detected

    Returns:
        Dictionary containing baseline completeness metrics and approval status
    """
    # Weight different factors for baseline completeness
    accuracy_weight = 0.5
    coverage_weight = 0.3
    diversity_weight = 0.2

    # Calculate weighted completeness score
    completeness_score = (
        accuracy_report.accuracy_percentage * accuracy_weight
        + migration_coverage * coverage_weight
        + pattern_diversity_score * diversity_weight
    )

    # Baseline approval criteria
    baseline_ready = (
        accuracy_report.baseline_approved
        and migration_coverage >= 0.80
        and pattern_diversity_score >= 0.70
        and completeness_score >= 0.85
    )

    logger.info(
        "Baseline completeness calculated: completeness_score=%f, migration_coverage=%f, pattern_diversity_score=%f, baseline_ready=%s",
        completeness_score,
        migration_coverage,
        pattern_diversity_score,
        baseline_ready,
    )

    return {
        "completeness_score": completeness_score,
        "accuracy_component": accuracy_report.accuracy_percentage * accuracy_weight,
        "coverage_component": migration_coverage * coverage_weight,
        "diversity_component": pattern_diversity_score * diversity_weight,
        "baseline_ready": baseline_ready,
        "approval_criteria": {
            "accuracy_approved": accuracy_report.baseline_approved,
            "coverage_sufficient": migration_coverage >= 0.80,
            "diversity_sufficient": pattern_diversity_score >= 0.70,
            "overall_score_sufficient": completeness_score >= 0.85,
        },
    }
