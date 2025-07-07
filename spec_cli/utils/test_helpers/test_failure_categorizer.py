"""Test failure categorization utilities for systematic analysis and prioritization.

This module provides utilities for categorizing test failures by type and priority
to enable systematic remediation and migration strategies.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from spec_cli.logging.debug import debug_logger

from ..error_utils import SpecAnalysisError


class FailureType(Enum):
    """Categories of test failures for systematic analysis."""

    RICH_COMPATIBILITY = "rich_compatibility"
    MISSING_FUNCTION = "missing_function"
    MIGRATION_ARTIFACT = "migration_artifact"
    IMPORT_ERROR = "import_error"
    FIXTURE_DEPENDENCY = "fixture_dependency"
    CONTEXT_INJECTION = "context_injection"
    REAL_LOGIC_ERROR = "real_logic_error"
    UNKNOWN = "unknown"

class FailurePriority(Enum):
    """Priority levels for test failure remediation."""

    CRITICAL = "critical"  # Blocks all testing
    HIGH = "high"  # Major functionality broken
    MEDIUM = "medium"  # Isolated feature issues
    LOW = "low"  # Minor or cosmetic issues

@dataclass
class FailureInfo:
    """Information about a single test failure."""

    test_name: str
    file_path: Path
    failure_type: FailureType
    priority: FailurePriority
    error_message: str
    stack_trace: str = ""
    remediation_notes: str = ""
    related_failures: list[str] = field(default_factory=list)

@dataclass
class FailureCategory:
    """A category of related test failures."""

    failure_type: FailureType
    priority: FailurePriority
    failure_count: int
    failures: list[FailureInfo] = field(default_factory=list)
    remediation_strategy: str = ""
    estimated_effort: str = ""

class FailureCategorizationError(SpecAnalysisError):
    """Error during test failure categorization."""

def categorize_test_failure(failure_info: dict[str, Any]) -> FailureCategory:
    """Categorize a test failure by type and priority.

    Args:
        failure_info: Dictionary containing test failure information with keys:
            - test_name: Name of the failed test
            - file_path: Path to the test file
            - error_message: Error message from test failure
            - stack_trace: Full stack trace (optional)

    Returns:
        FailureCategory with categorized failure information

    Raises:
        FailureCategorizationError: If categorization fails
    """
    try:
        test_name = failure_info.get("test_name", "")
        file_path = Path(failure_info.get("file_path", ""))
        error_message = failure_info.get("error_message", "")
        stack_trace = failure_info.get("stack_trace", "")

        # Determine failure type based on error patterns
        failure_type = _analyze_failure_type(error_message, stack_trace)

        # Assign priority based on failure type and impact
        priority = _determine_failure_priority(failure_type, test_name, file_path)

        # Create failure info object
        test_failure = FailureInfo(
            test_name=test_name,
            file_path=file_path,
            failure_type=failure_type,
            priority=priority,
            error_message=error_message,
            stack_trace=stack_trace,
            remediation_notes=_generate_remediation_notes(failure_type),
        )

        # Create category with single failure
        category = FailureCategory(
            failure_type=failure_type,
            priority=priority,
            failure_count=1,
            failures=[test_failure],
            remediation_strategy=_get_remediation_strategy(failure_type),
            estimated_effort=_estimate_remediation_effort(failure_type),
        )

        debug_logger.log(
            "DEBUG",
            "Test failure categorized successfully",
            test_name=test_name,
            failure_type=failure_type.value,
            priority=priority.value,
        )

        return category

    except Exception as e:
        raise FailureCategorizationError(
            f"Failed to categorize test failure: {e}"
        ) from e

def _analyze_failure_type(error_message: str, stack_trace: str) -> FailureType:
    """Analyze error patterns to determine failure type."""
    combined_text = f"{error_message} {stack_trace}".lower()

    # Import errors (check first, most critical)
    if any(
        pattern in combined_text
        for pattern in ["importerror", "modulenotfounderror", "no module named"]
    ):
        return FailureType.IMPORT_ERROR

    # Migration artifacts (check before general patterns)
    if any(
        pattern in combined_text
        for pattern in ["singleton", "inject_context", "with_context", "migration"]
    ):
        return FailureType.MIGRATION_ARTIFACT

    # Rich UI compatibility issues
    if any(
        pattern in combined_text
        for pattern in ["rich", "console", "terminal", "color", "style", "markup"]
    ):
        return FailureType.RICH_COMPATIBILITY

    # Context injection issues (specific patterns)
    if any(
        pattern in combined_text
        for pattern in ["context injection", "decorator", "click"]
    ):
        return FailureType.CONTEXT_INJECTION

    # Fixture dependency issues
    if any(
        pattern in combined_text
        for pattern in ["fixture", "pytest", "conftest", "dependency"]
    ):
        return FailureType.FIXTURE_DEPENDENCY

    # Missing function/attribute errors (after more specific checks)
    if any(
        pattern in combined_text
        for pattern in ["has no attribute", "not defined", "missing", "attributeerror"]
    ):
        return FailureType.MISSING_FUNCTION

    # Assertion failures and logic errors
    if any(
        pattern in combined_text
        for pattern in ["assertionerror", "assertion", "expected", "actual"]
    ):
        return FailureType.REAL_LOGIC_ERROR

    return FailureType.UNKNOWN

def _determine_failure_priority(
    failure_type: FailureType, test_name: str, file_path: Path
) -> FailurePriority:
    """Determine priority based on failure type and test context."""
    # Critical priority for import errors that block test collection
    if failure_type == FailureType.IMPORT_ERROR:
        return FailurePriority.CRITICAL

    # High priority for core functionality tests
    if any(
        keyword in str(file_path).lower()
        for keyword in ["cli", "core", "main", "command"]
    ):
        return FailurePriority.HIGH

    # High priority for migration artifacts affecting multiple tests
    if failure_type == FailureType.MIGRATION_ARTIFACT:
        return FailurePriority.HIGH

    # Medium priority for feature-specific tests
    if "integration" in str(file_path).lower():
        return FailurePriority.MEDIUM

    # Low priority for UI compatibility issues
    if failure_type == FailureType.RICH_COMPATIBILITY:
        return FailurePriority.LOW

    # Default medium priority
    return FailurePriority.MEDIUM

def _generate_remediation_notes(failure_type: FailureType) -> str:
    """Generate remediation notes based on failure type."""
    remediation_map = {
        FailureType.RICH_COMPATIBILITY: (
            "Update Rich UI compatibility layer. "
            "Consider mock console for testing or update test expectations."
        ),
        FailureType.MISSING_FUNCTION: (
            "Implement missing function or update imports. "
            "Check if function was renamed or moved during migration."
        ),
        FailureType.MIGRATION_ARTIFACT: (
            "Clean up migration artifacts. "
            "Remove old singleton patterns and update to context injection."
        ),
        FailureType.IMPORT_ERROR: (
            "Fix import paths and dependencies. "
            "Check for moved modules or missing packages."
        ),
        FailureType.FIXTURE_DEPENDENCY: (
            "Update fixture dependencies. Migrate to context-based fixtures if needed."
        ),
        FailureType.CONTEXT_INJECTION: (
            "Fix context injection patterns. "
            "Ensure decorator compatibility and proper context setup."
        ),
        FailureType.REAL_LOGIC_ERROR: (
            "Fix actual logic or update test expectations. "
            "Review implementation changes and test validity."
        ),
        FailureType.UNKNOWN: (
            "Requires manual analysis. "
            "Review error details and stack trace for root cause."
        ),
    }
    return remediation_map.get(failure_type, "No specific remediation notes available.")

def _get_remediation_strategy(failure_type: FailureType) -> str:
    """Get high-level remediation strategy for failure type."""
    strategy_map = {
        FailureType.RICH_COMPATIBILITY: "Batch update UI testing patterns",
        FailureType.MISSING_FUNCTION: "Implement missing functionality",
        FailureType.MIGRATION_ARTIFACT: "Complete migration cleanup",
        FailureType.IMPORT_ERROR: "Fix import structure",
        FailureType.FIXTURE_DEPENDENCY: "Migrate test fixtures",
        FailureType.CONTEXT_INJECTION: "Fix injection patterns",
        FailureType.REAL_LOGIC_ERROR: "Debug and fix logic",
        FailureType.UNKNOWN: "Manual investigation required",
    }
    return strategy_map.get(failure_type, "Unknown strategy")

def _estimate_remediation_effort(failure_type: FailureType) -> str:
    """Estimate effort required for remediation."""
    effort_map = {
        FailureType.RICH_COMPATIBILITY: "2-4 hours",
        FailureType.MISSING_FUNCTION: "1-8 hours",
        FailureType.MIGRATION_ARTIFACT: "4-8 hours",
        FailureType.IMPORT_ERROR: "1-2 hours",
        FailureType.FIXTURE_DEPENDENCY: "2-6 hours",
        FailureType.CONTEXT_INJECTION: "3-6 hours",
        FailureType.REAL_LOGIC_ERROR: "2-12 hours",
        FailureType.UNKNOWN: "Unknown",
    }
    return effort_map.get(failure_type, "Unknown effort")
