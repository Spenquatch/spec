"""Slice 2.4: Migration Test Marking and Core Test Validation.

This module implements test marking functionality to categorize migration-specific
tests and validate core functionality test reliability achieves <5% failure rate.
"""

import logging
import statistics
from pathlib import Path

# Decorator utilities for potential future use
from spec_cli.utils.test_helpers.migration_test_marker import (
    identify_core_tests,
    identify_migration_tests,
    mark_migration_test,
    validate_test_reliability,
)

# Test migration utilities available for future use

logger = logging.getLogger(__name__)

# Constants for reliability validation
DEFAULT_FAILURE_THRESHOLD = 0.05  # 5% maximum failure rate
MIN_CORE_TESTS_COUNT = 10  # Minimum number of core tests required
RELIABILITY_CALCULATION_RUNS = 3  # Number of test runs for reliability calculation


class MarkingResult:
    """Result of test marking operation."""

    def __init__(
        self,
        marked_tests: dict[str, str],
        core_test_validation: dict[str, float],
        overall_reliability_score: float,
    ):
        """Initialize test marking result.

        Args:
            marked_tests: Dictionary mapping test paths to marking reasons
            core_test_validation: Dictionary mapping test paths to failure rates
            overall_reliability_score: Overall reliability score (0.0-1.0)
        """
        self.marked_tests = marked_tests
        self.core_test_validation = core_test_validation
        self.overall_reliability_score = overall_reliability_score

    def meets_reliability_target(
        self, threshold: float = DEFAULT_FAILURE_THRESHOLD
    ) -> bool:
        """Check if overall reliability meets target threshold.

        Args:
            threshold: Maximum acceptable failure rate

        Returns:
            True if reliability meets target
        """
        return self.overall_reliability_score <= threshold

    def get_failing_core_tests(
        self, threshold: float = DEFAULT_FAILURE_THRESHOLD
    ) -> list[str]:
        """Get list of core tests exceeding failure threshold.

        Args:
            threshold: Maximum acceptable failure rate

        Returns:
            List of test paths exceeding threshold
        """
        return [
            test_path
            for test_path, failure_rate in self.core_test_validation.items()
            if failure_rate > threshold
        ]


def mark_migration_tests(
    test_files: list[str], categorization_results: dict[str, str]
) -> dict[str, str]:
    """Mark migration-specific tests with appropriate pytest decorators.

    Args:
        test_files: List of test file paths to analyze
        categorization_results: Dictionary mapping test paths to categories

    Returns:
        Dictionary mapping test paths to marking reasons

    Raises:
        ValueError: If test_files is empty or contains invalid paths
    """
    if not test_files:
        raise ValueError("test_files cannot be empty")

    marked_tests = {}

    # First, identify migration tests automatically
    for test_file in test_files:
        test_path = Path(test_file)
        if not test_path.exists():
            logger.warning("Test file not found: %s", test_file)
            continue

        # Check if already categorized
        if test_file in categorization_results:
            category = categorization_results[test_file]
            if "migration" in category.lower():
                reason = f"categorized_as_{category}"
                if mark_migration_test(test_file, reason):
                    marked_tests[test_file] = reason

    # Identify additional migration tests by patterns
    test_dir = str(Path(test_files[0]).parent) if test_files else "tests"
    pattern_migration_tests = identify_migration_tests(test_dir)

    for test_path_str, reason in pattern_migration_tests.items():
        if test_path_str not in marked_tests:
            if mark_migration_test(test_path_str, reason):
                marked_tests[test_path_str] = reason

    logger.info("Marked %d tests as migration-related", len(marked_tests))
    return marked_tests


def validate_core_test_reliability(
    core_test_definitions: list[str],
    failure_threshold: float = DEFAULT_FAILURE_THRESHOLD,
) -> tuple[dict[str, float], float]:
    """Validate core functionality test reliability meets target.

    Args:
        core_test_definitions: List of core test file paths
        failure_threshold: Maximum acceptable failure rate

    Returns:
        Tuple of (test_path_to_failure_rate_mapping, overall_reliability_score)

    Raises:
        ValueError: If core_test_definitions is empty or invalid
    """
    if not core_test_definitions:
        raise ValueError("core_test_definitions cannot be empty")

    if len(core_test_definitions) < MIN_CORE_TESTS_COUNT:
        logger.warning(
            "Only %d core tests found, minimum %d recommended",
            len(core_test_definitions),
            MIN_CORE_TESTS_COUNT,
        )

    # Validate each core test's reliability
    core_test_validation = validate_test_reliability(
        core_test_definitions, failure_threshold
    )

    # Calculate overall reliability score
    if core_test_validation:
        failure_rates = list(core_test_validation.values())
        overall_reliability_score = statistics.mean(failure_rates)
    else:
        overall_reliability_score = 1.0  # 100% failure rate if no tests

    logger.info(
        "Core test reliability validation: %.2f%% average failure rate",
        overall_reliability_score * 100,
    )

    return core_test_validation, overall_reliability_score


def execute_test_marking_workflow(
    test_files: list[str],
    categorization_results: dict[str, str],
    core_test_definitions: list[str],
) -> MarkingResult:
    """Execute complete test marking and validation workflow.

    Args:
        test_files: List of test file paths to analyze
        categorization_results: Dictionary mapping test paths to failure categories
        core_test_definitions: List of core test file paths

    Returns:
        TestMarkingResult containing marking results and validation data

    Raises:
        ValueError: If required inputs are invalid
    """
    logger.info("Starting test marking workflow")

    # Mark migration tests
    marked_tests = mark_migration_tests(test_files, categorization_results)

    # Validate core test reliability
    core_test_validation, overall_reliability_score = validate_core_test_reliability(
        core_test_definitions
    )

    result = MarkingResult(
        marked_tests=marked_tests,
        core_test_validation=core_test_validation,
        overall_reliability_score=overall_reliability_score,
    )

    # Log summary
    logger.info("Test marking workflow completed:")
    logger.info("  - Migration tests marked: %d", len(marked_tests))
    logger.info("  - Core tests validated: %d", len(core_test_validation))
    logger.info("  - Overall reliability: %.2f%%", overall_reliability_score * 100)
    logger.info(
        "  - Meets target: %s", "Yes" if result.meets_reliability_target() else "No"
    )

    return result


def analyze_test_suite_composition(test_directory: str) -> dict[str, list[str]]:
    """Analyze test suite composition for migration vs core tests.

    Args:
        test_directory: Directory containing test files

    Returns:
        Dictionary with 'migration' and 'core' keys mapping to test file lists
    """
    migration_tests = identify_migration_tests(test_directory)
    core_tests = identify_core_tests(test_directory)

    composition = {
        "migration": list(migration_tests.keys()),
        "core": core_tests,
        "unclassified": [],
    }

    # Find unclassified tests
    test_dir = Path(test_directory)
    all_tests = [str(f) for f in test_dir.rglob("test_*.py")]
    classified = set(composition["migration"] + composition["core"])

    composition["unclassified"] = [t for t in all_tests if t not in classified]

    logger.info("Test suite composition analysis:")
    logger.info("  - Migration tests: %d", len(composition["migration"]))
    logger.info("  - Core tests: %d", len(composition["core"]))
    logger.info("  - Unclassified tests: %d", len(composition["unclassified"]))

    return composition


def generate_reliability_report(result: MarkingResult) -> str:
    """Generate detailed reliability report.

    Args:
        result: Test marking result to report on

    Returns:
        Formatted reliability report string
    """
    report_lines = [
        "# Test Reliability Report",
        "",
        f"## Overall Reliability: {result.overall_reliability_score:.2%}",
        f"Target: <{DEFAULT_FAILURE_THRESHOLD:.0%}",
        f"Status: {'PASS' if result.meets_reliability_target() else 'FAIL'}",
        "",
        "## Core Test Validation Results",
    ]

    if result.core_test_validation:
        for test_path, failure_rate in sorted(result.core_test_validation.items()):
            status = "PASS" if failure_rate <= DEFAULT_FAILURE_THRESHOLD else "FAIL"
            report_lines.append(f"- {test_path}: {failure_rate:.2%} ({status})")
    else:
        report_lines.append("- No core tests validated")

    report_lines.extend(
        [
            "",
            "## Migration Test Marking Results",
            f"Total migration tests marked: {len(result.marked_tests)}",
        ]
    )

    if result.marked_tests:
        for test_path, reason in sorted(result.marked_tests.items()):
            report_lines.append(f"- {test_path}: {reason}")
    else:
        report_lines.append("- No migration tests marked")

    failing_tests = result.get_failing_core_tests()
    if failing_tests:
        report_lines.extend(
            [
                "",
                "## Tests Exceeding Failure Threshold",
            ]
        )
        for test_path in failing_tests:
            failure_rate = result.core_test_validation[test_path]
            report_lines.append(f"- {test_path}: {failure_rate:.2%}")

    return "\n".join(report_lines)
