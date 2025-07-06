"""Slice 2.1: Test Failure Analysis and Categorization

Systematically analyzes all test failures and categorizes them by type and priority
to create actionable remediation plans for the test suite.
"""

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from spec_cli.logging.debug import debug_logger
from spec_cli.utils.test_helpers.test_failure_categorizer import (
    FailureCategory,
    FailureInfo,
    FailurePriority,
    FailureType,
    categorize_test_failure,
)


class CategorizationError(Exception):
    """Error during test categorization analysis."""


def analyze_test_failures() -> dict[str, Any]:
    """Systematically analyze all test failures and categorize by type and priority.

    Returns:
        Dictionary containing categorization report and summary statistics

    Raises:
        CategorizationError: If analysis fails
    """
    try:
        debug_logger.log("INFO", "Starting comprehensive test failure analysis")

        # Extract test failure data from pytest execution
        test_results = _extract_test_failure_data()

        if not test_results:
            debug_logger.log("INFO", "No test failures found to categorize")
            return {
                "categorization_report": {},
                "summary_stats": {
                    "total_failures": 0,
                    "categories": {},
                    "priority_distribution": {},
                    "category_count": 0,
                },
            }

        # Categorize all failures
        categorized_failures = _categorize_all_failures(test_results)

        # Generate summary statistics
        summary_stats = _generate_summary_statistics(categorized_failures)

        # Create comprehensive report
        categorization_report = _create_categorization_report(categorized_failures)

        debug_logger.log(
            "INFO",
            "Test failure analysis completed",
            total_failures=summary_stats["total_failures"],
            category_count=len(categorized_failures),
        )

        return {
            "categorization_report": categorization_report,
            "summary_stats": summary_stats,
        }

    except Exception as e:
        raise CategorizationError(f"Failed to analyze test failures: {e}") from e


def _extract_test_failure_data() -> list[dict[str, Any]]:
    """Extract test failure information from pytest execution."""
    try:
        debug_logger.log("DEBUG", "Extracting test failure data from pytest")

        # Run pytest with structured output for failure analysis
        cmd = [
            "poetry",
            "run",
            "pytest",
            "tests/",
            "--tb=short",
            "--no-header",
            "--quiet",
            "-x",  # Stop on first failure for faster analysis
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        # Parse pytest output for failure information
        failures = _parse_pytest_output(result.stdout, result.stderr)

        debug_logger.log(
            "DEBUG",
            "Extracted test failure data",
            failure_count=len(failures),
        )

        return failures

    except subprocess.TimeoutExpired as e:
        raise CategorizationError(f"Pytest execution timed out: {e}") from e
    except Exception as e:
        raise CategorizationError(f"Failed to extract test data: {e}") from e


def _parse_pytest_output(stdout: str, stderr: str) -> list[dict[str, Any]]:
    """Parse pytest output to extract structured failure information."""
    failures = []
    combined_output = f"{stdout}\n{stderr}"

    # Pattern to match test failures - more flexible regex
    failure_pattern = r"FAILED\s+([^:]+(?:::(?:[^:]+::)*[^:]+)?)::(.*?)\s+-\s+(.*)"

    for match in re.finditer(failure_pattern, combined_output, re.MULTILINE):
        full_test_path = match.group(1)
        test_method = match.group(2)
        error_snippet = match.group(3)

        # Extract file path (everything before first ::)
        file_path_str = full_test_path.split("::")[0]

        # Extract more detailed error information if available
        detailed_error = _extract_detailed_error(combined_output, test_method)

        failure_info = {
            "test_name": f"{full_test_path}::{test_method}",
            "file_path": file_path_str,
            "error_message": error_snippet,
            "stack_trace": detailed_error,
        }

        failures.append(failure_info)

    # Also check for collection errors
    collection_errors = _extract_collection_errors(combined_output)
    failures.extend(collection_errors)

    return failures


def _extract_detailed_error(output: str, test_name: str) -> str:
    """Extract detailed error information for a specific test."""
    lines = output.split("\n")
    in_test_section = False
    error_lines = []

    for line in lines:
        if test_name in line and ("FAILED" in line or "ERROR" in line):
            in_test_section = True
            continue

        if in_test_section:
            if line.startswith("=") or line.startswith("_"):
                break
            if line.strip():
                error_lines.append(line)

    return "\n".join(error_lines[:10])  # Limit to first 10 lines


def _extract_collection_errors(output: str) -> list[dict[str, Any]]:
    """Extract test collection errors from pytest output."""
    collection_errors = []

    # Pattern for collection errors - more flexible
    error_pattern = r"ERROR collecting ([^\s]+).*?-\s*(.*?)(?=\n|$)"

    for match in re.finditer(error_pattern, output, re.MULTILINE):
        file_path = match.group(1)
        error_message = match.group(2).strip()

        collection_error = {
            "test_name": f"COLLECTION_ERROR::{file_path}",
            "file_path": file_path,
            "error_message": error_message,
            "stack_trace": "",
        }

        collection_errors.append(collection_error)

    return collection_errors


def _categorize_all_failures(
    test_results: list[dict[str, Any]],
) -> dict[FailureType, FailureCategory]:
    """Categorize all test failures by type and priority."""
    categorized = defaultdict(
        lambda: FailureCategory(
            failure_type=FailureType.UNKNOWN,
            priority=FailurePriority.MEDIUM,
            failure_count=0,
            failures=[],
        )
    )

    for failure_data in test_results:
        try:
            # Categorize individual failure
            category = categorize_test_failure(failure_data)
            failure_type = category.failure_type

            # Add to existing category or create new one
            if failure_type not in categorized:
                categorized[failure_type] = FailureCategory(
                    failure_type=failure_type,
                    priority=category.priority,
                    failure_count=0,
                    failures=[],
                    remediation_strategy=category.remediation_strategy,
                    estimated_effort=category.estimated_effort,
                )

            # Add failure to category
            categorized[failure_type].failures.extend(category.failures)
            categorized[failure_type].failure_count += 1

            # Update priority to highest level in category
            if category.priority.value < categorized[failure_type].priority.value:
                categorized[failure_type].priority = category.priority

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Failed to categorize individual failure",
                test_name=failure_data.get("test_name", "unknown"),
                error=str(e),
            )
            # Add to unknown category
            unknown_failure = FailureInfo(
                test_name=failure_data.get("test_name", "unknown"),
                file_path=Path(failure_data.get("file_path", "")),
                failure_type=FailureType.UNKNOWN,
                priority=FailurePriority.MEDIUM,
                error_message=failure_data.get("error_message", ""),
                stack_trace=failure_data.get("stack_trace", ""),
                remediation_notes="Manual analysis required due to categorization error",
            )

            if FailureType.UNKNOWN not in categorized:
                categorized[FailureType.UNKNOWN] = FailureCategory(
                    failure_type=FailureType.UNKNOWN,
                    priority=FailurePriority.MEDIUM,
                    failure_count=0,
                    failures=[],
                    remediation_strategy="Manual investigation required",
                    estimated_effort="Unknown",
                )

            categorized[FailureType.UNKNOWN].failures.append(unknown_failure)
            categorized[FailureType.UNKNOWN].failure_count += 1

    return dict(categorized)


def _generate_summary_statistics(
    categorized_failures: dict[FailureType, FailureCategory],
) -> dict[str, Any]:
    """Generate summary statistics for categorized failures."""
    total_failures = sum(cat.failure_count for cat in categorized_failures.values())

    categories = {}
    priority_counts: dict[str, int] = defaultdict(int)

    for failure_type, category in categorized_failures.items():
        categories[failure_type.value] = {
            "count": category.failure_count,
            "priority": category.priority.value,
            "strategy": category.remediation_strategy,
            "effort": category.estimated_effort,
        }
        priority_counts[category.priority.value] += category.failure_count

    return {
        "total_failures": total_failures,
        "categories": categories,
        "priority_distribution": dict(priority_counts),
        "category_count": len(categorized_failures),
    }


def _create_categorization_report(
    categorized_failures: dict[FailureType, FailureCategory],
) -> dict[str, Any]:
    """Create comprehensive categorization report."""
    report = {}

    # Sort categories by priority and count
    sorted_categories = sorted(
        categorized_failures.items(),
        key=lambda x: (x[1].priority.value, -x[1].failure_count),
    )

    for failure_type, category in sorted_categories:
        # Convert category to dict for JSON serialization
        category_data = asdict(category)

        # Convert enum values to strings for JSON serialization
        category_data["failure_type"] = category_data["failure_type"].value
        category_data["priority"] = category_data["priority"].value

        # Convert Path objects and enum values in failures
        for failure in category_data["failures"]:
            failure["file_path"] = str(failure["file_path"])
            failure["failure_type"] = failure["failure_type"].value
            failure["priority"] = failure["priority"].value

        report[failure_type.value] = category_data

    return report


if __name__ == "__main__":
    """Run test failure analysis when executed directly."""
    try:
        results = analyze_test_failures()

        # Print summary
        stats = results["summary_stats"]
        print("Test Failure Analysis Complete")
        print(f"Total Failures: {stats['total_failures']}")
        print(f"Categories Found: {stats.get('category_count', 0)}")
        print()
        print("Priority Distribution:")
        for priority, count in stats["priority_distribution"].items():
            print(f"  {priority.upper()}: {count}")
        print()
        print("Category Summary:")
        for category_name, category_info in stats["categories"].items():
            print(f"  {category_name}: {category_info['count']} failures")
            print(f"    Priority: {category_info['priority']}")
            print(f"    Strategy: {category_info['strategy']}")
            print(f"    Effort: {category_info['effort']}")
            print()

        # Save detailed report
        report_file = Path("test_failure_analysis_report.json")
        with report_file.open("w") as f:
            json.dump(results, f, indent=2)

        print(f"Detailed report saved to: {report_file}")

    except CategorizationError as e:
        print(f"Error during test failure analysis: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("Analysis interrupted by user")
        exit(1)
