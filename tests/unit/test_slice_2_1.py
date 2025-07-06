"""Unit tests for Slice 2.1: Test Failure Analysis and Categorization."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slice_2_1_test_categorization import (
    CategorizationError,
    _categorize_all_failures,
    _create_categorization_report,
    _extract_collection_errors,
    _extract_detailed_error,
    _extract_test_failure_data,
    _generate_summary_statistics,
    _parse_pytest_output,
    analyze_test_failures,
)
from spec_cli.utils.test_helpers.test_failure_categorizer import (
    FailureCategory,
    FailureInfo,
    FailurePriority,
    FailureType,
)

# Test constants
SAMPLE_TEST_NAME = "tests/unit/test_example.py::TestClass::test_method"
SAMPLE_FILE_PATH = "tests/unit/test_example.py"
SAMPLE_ERROR_MESSAGE = "AttributeError: 'NoneType' object has no attribute 'method'"
SAMPLE_STACK_TRACE = "Traceback (most recent call last):\n  File test.py, line 10\n    result.method()\nAttributeError"

RICH_ERROR_MESSAGE = "rich.console.Console object has no attribute 'print_text'"
IMPORT_ERROR_MESSAGE = "ModuleNotFoundError: No module named 'missing_module'"
MIGRATION_ERROR_MESSAGE = "inject_context decorator not found"

PYTEST_OUTPUT_SAMPLE = """
FAILED tests/unit/test_example.py::TestClass::test_method - AttributeError: object has no attribute
FAILED tests/integration/test_rich.py::TestRich::test_console - rich.console error
PASSED tests/unit/test_working.py::TestWorking::test_success
"""

PYTEST_STDERR_SAMPLE = """
ERROR collecting tests/unit/test_broken.py - SyntaxError: invalid syntax
INTERNALERROR> Some internal pytest error
"""


class TestAnalyzeTestFailures:
    """Test the main analyze_test_failures function."""

    @patch("slice_2_1_test_categorization._extract_test_failure_data")
    @patch("slice_2_1_test_categorization._categorize_all_failures")
    def test_analyze_test_failures_when_no_failures_then_returns_empty_report(
        self, mock_categorize, mock_extract
    ):
        """Test analyze_test_failures with no failures returns empty report."""
        mock_extract.return_value = []

        result = analyze_test_failures()

        assert result["categorization_report"] == {}
        assert result["summary_stats"]["total_failures"] == 0
        assert result["summary_stats"]["categories"] == {}

    @patch("slice_2_1_test_categorization._extract_test_failure_data")
    @patch("slice_2_1_test_categorization._categorize_all_failures")
    @patch("slice_2_1_test_categorization._generate_summary_statistics")
    @patch("slice_2_1_test_categorization._create_categorization_report")
    def test_analyze_test_failures_when_failures_exist_then_returns_complete_report(
        self, mock_create_report, mock_generate_stats, mock_categorize, mock_extract
    ):
        """Test analyze_test_failures with failures returns complete report."""
        # Setup mock data
        sample_failure = {
            "test_name": SAMPLE_TEST_NAME,
            "file_path": SAMPLE_FILE_PATH,
            "error_message": SAMPLE_ERROR_MESSAGE,
        }
        mock_extract.return_value = [sample_failure]

        sample_category = FailureCategory(
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            failure_count=1,
            failures=[],
        )
        mock_categorize.return_value = {FailureType.MISSING_FUNCTION: sample_category}

        mock_generate_stats.return_value = {
            "total_failures": 1,
            "categories": {"missing_function": {"count": 1}},
        }
        mock_create_report.return_value = {"missing_function": {"count": 1}}

        result = analyze_test_failures()

        assert "categorization_report" in result
        assert "summary_stats" in result
        assert result["summary_stats"]["total_failures"] == 1

    @patch("slice_2_1_test_categorization._extract_test_failure_data")
    def test_analyze_test_failures_when_extraction_fails_then_raises_error(
        self, mock_extract
    ):
        """Test analyze_test_failures raises error when extraction fails."""
        mock_extract.side_effect = Exception("Extraction failed")

        with pytest.raises(
            CategorizationError, match="Failed to analyze test failures"
        ):
            analyze_test_failures()


class TestExtractTestFailureData:
    """Test the _extract_test_failure_data function."""

    @patch("slice_2_1_test_categorization.subprocess.run")
    @patch("slice_2_1_test_categorization._parse_pytest_output")
    def test_extract_test_failure_data_when_pytest_succeeds_then_returns_failures(
        self, mock_parse, mock_run
    ):
        """Test _extract_test_failure_data when pytest runs successfully."""
        mock_result = Mock()
        mock_result.stdout = PYTEST_OUTPUT_SAMPLE
        mock_result.stderr = PYTEST_STDERR_SAMPLE
        mock_run.return_value = mock_result

        expected_failures = [{"test_name": SAMPLE_TEST_NAME}]
        mock_parse.return_value = expected_failures

        result = _extract_test_failure_data()

        assert result == expected_failures
        mock_run.assert_called_once()
        mock_parse.assert_called_once_with(PYTEST_OUTPUT_SAMPLE, PYTEST_STDERR_SAMPLE)

    @patch("slice_2_1_test_categorization.subprocess.run")
    def test_extract_test_failure_data_when_pytest_times_out_then_raises_error(
        self, mock_run
    ):
        """Test _extract_test_failure_data raises error when pytest times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        with pytest.raises(CategorizationError, match="Pytest execution timed out"):
            _extract_test_failure_data()

    @patch("slice_2_1_test_categorization.subprocess.run")
    def test_extract_test_failure_data_when_subprocess_fails_then_raises_error(
        self, mock_run
    ):
        """Test _extract_test_failure_data raises error when subprocess fails."""
        mock_run.side_effect = Exception("Subprocess error")

        with pytest.raises(CategorizationError, match="Failed to extract test data"):
            _extract_test_failure_data()


class TestParsePytestOutput:
    """Test the _parse_pytest_output function."""

    def test_parse_pytest_output_when_failures_present_then_extracts_correctly(self):
        """Test _parse_pytest_output correctly extracts failure information."""
        stdout = "FAILED tests/unit/test_example.py::TestClass::test_method - AttributeError: object error"
        stderr = ""

        result = _parse_pytest_output(stdout, stderr)

        assert len(result) == 1
        failure = result[0]
        assert (
            failure["test_name"] == "tests/unit/test_example.py::TestClass::test_method"
        )
        assert failure["file_path"] == "tests/unit/test_example.py"
        assert "AttributeError" in failure["error_message"]

    def test_parse_pytest_output_when_collection_errors_then_extracts_errors(self):
        """Test _parse_pytest_output extracts collection errors."""
        stdout = ""
        stderr = (
            "ERROR collecting tests/unit/test_broken.py - SyntaxError: invalid syntax"
        )

        result = _parse_pytest_output(stdout, stderr)

        assert len(result) == 1
        error = result[0]
        assert "COLLECTION_ERROR" in error["test_name"]
        assert error["file_path"] == "tests/unit/test_broken.py"
        assert "SyntaxError" in error["error_message"]

    def test_parse_pytest_output_when_no_failures_then_returns_empty_list(self):
        """Test _parse_pytest_output with no failures returns empty list."""
        stdout = "PASSED tests/unit/test_working.py::TestWorking::test_success"
        stderr = ""

        result = _parse_pytest_output(stdout, stderr)

        assert result == []


class TestExtractDetailedError:
    """Test the _extract_detailed_error function."""

    def test_extract_detailed_error_when_test_found_then_returns_details(self):
        """Test _extract_detailed_error extracts detailed error information."""
        output = """
FAILED tests/unit/test_example.py::TestClass::test_method - AttributeError
    def test_method(self):
        result = None
>       result.method()
E       AttributeError: 'NoneType' object has no attribute 'method'

tests/unit/test_example.py:10: AttributeError
        """
        test_name = "test_method"

        result = _extract_detailed_error(output, test_name)

        assert "def test_method" in result
        assert "AttributeError" in result
        assert len(result.split("\n")) <= 10  # Limited to 10 lines

    def test_extract_detailed_error_when_test_not_found_then_returns_empty(self):
        """Test _extract_detailed_error returns empty when test not found."""
        output = "Some random output without the test"
        test_name = "nonexistent_test"

        result = _extract_detailed_error(output, test_name)

        assert result == ""

    def test_extract_detailed_error_when_test_ends_with_separator_then_truncates(self):
        """Test _extract_detailed_error stops at section separators."""
        output = """
FAILED tests/unit/test_example.py::TestClass::test_method - AttributeError
    def test_method(self):
        result = None
>       result.method()
E       AttributeError: 'NoneType' object has no attribute 'method'
========================================
More unrelated output
        """
        test_name = "test_method"

        result = _extract_detailed_error(output, test_name)

        assert "def test_method" in result
        assert "More unrelated output" not in result


class TestExtractCollectionErrors:
    """Test the _extract_collection_errors function."""

    def test_extract_collection_errors_when_errors_present_then_extracts_correctly(
        self,
    ):
        """Test _extract_collection_errors correctly extracts collection errors."""
        output = (
            "ERROR collecting tests/unit/test_broken.py - SyntaxError: invalid syntax"
        )

        result = _extract_collection_errors(output)

        assert len(result) == 1
        error = result[0]
        assert "COLLECTION_ERROR" in error["test_name"]
        assert error["file_path"] == "tests/unit/test_broken.py"
        assert "SyntaxError" in error["error_message"]

    def test_extract_collection_errors_when_no_errors_then_returns_empty_list(self):
        """Test _extract_collection_errors with no errors returns empty list."""
        output = "All tests collected successfully"

        result = _extract_collection_errors(output)

        assert result == []


class TestCategorizeAllFailures:
    """Test the _categorize_all_failures function."""

    @patch("slice_2_1_test_categorization.categorize_test_failure")
    def test_categorize_all_failures_when_single_failure_then_creates_category(
        self, mock_categorize
    ):
        """Test _categorize_all_failures with single failure creates correct category."""
        # Setup test data
        test_data = [
            {
                "test_name": SAMPLE_TEST_NAME,
                "file_path": SAMPLE_FILE_PATH,
                "error_message": SAMPLE_ERROR_MESSAGE,
            }
        ]

        # Setup mock category
        sample_failure = FailureInfo(
            test_name=SAMPLE_TEST_NAME,
            file_path=Path(SAMPLE_FILE_PATH),
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            error_message=SAMPLE_ERROR_MESSAGE,
        )

        mock_category = FailureCategory(
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            failure_count=1,
            failures=[sample_failure],
            remediation_strategy="Implement missing functionality",
            estimated_effort="1-8 hours",
        )
        mock_categorize.return_value = mock_category

        result = _categorize_all_failures(test_data)

        assert len(result) == 1
        assert FailureType.MISSING_FUNCTION in result
        category = result[FailureType.MISSING_FUNCTION]
        assert category.failure_count == 1
        assert len(category.failures) == 1

    @patch("slice_2_1_test_categorization.categorize_test_failure")
    def test_categorize_all_failures_when_multiple_same_type_then_groups_correctly(
        self, mock_categorize
    ):
        """Test _categorize_all_failures groups multiple failures of same type."""
        # Setup test data with two failures of same type
        test_data = [
            {
                "test_name": "test1",
                "file_path": "file1.py",
                "error_message": RICH_ERROR_MESSAGE,
            },
            {
                "test_name": "test2",
                "file_path": "file2.py",
                "error_message": RICH_ERROR_MESSAGE,
            },
        ]

        # Mock categorizer to return RICH_COMPATIBILITY for both
        def mock_categorize_side_effect(failure_data):
            return FailureCategory(
                failure_type=FailureType.RICH_COMPATIBILITY,
                priority=FailurePriority.LOW,
                failure_count=1,
                failures=[
                    FailureInfo(
                        test_name=failure_data["test_name"],
                        file_path=Path(failure_data["file_path"]),
                        failure_type=FailureType.RICH_COMPATIBILITY,
                        priority=FailurePriority.LOW,
                        error_message=failure_data["error_message"],
                    )
                ],
            )

        mock_categorize.side_effect = mock_categorize_side_effect

        result = _categorize_all_failures(test_data)

        assert len(result) == 1
        assert FailureType.RICH_COMPATIBILITY in result
        category = result[FailureType.RICH_COMPATIBILITY]
        assert category.failure_count == 2
        assert len(category.failures) == 2

    @patch("slice_2_1_test_categorization.categorize_test_failure")
    def test_categorize_all_failures_when_categorization_fails_then_adds_to_unknown(
        self, mock_categorize
    ):
        """Test _categorize_all_failures handles categorization errors gracefully."""
        test_data = [
            {
                "test_name": SAMPLE_TEST_NAME,
                "file_path": SAMPLE_FILE_PATH,
                "error_message": SAMPLE_ERROR_MESSAGE,
            }
        ]

        mock_categorize.side_effect = Exception("Categorization failed")

        result = _categorize_all_failures(test_data)

        assert len(result) == 1
        assert FailureType.UNKNOWN in result
        category = result[FailureType.UNKNOWN]
        assert category.failure_count == 1
        assert "Manual analysis required" in category.failures[0].remediation_notes


class TestGenerateSummaryStatistics:
    """Test the _generate_summary_statistics function."""

    def test_generate_summary_statistics_when_multiple_categories_then_returns_correct_stats(
        self,
    ):
        """Test _generate_summary_statistics with multiple categories."""
        categorized_failures = {
            FailureType.RICH_COMPATIBILITY: FailureCategory(
                failure_type=FailureType.RICH_COMPATIBILITY,
                priority=FailurePriority.LOW,
                failure_count=5,
                failures=[],
            ),
            FailureType.MISSING_FUNCTION: FailureCategory(
                failure_type=FailureType.MISSING_FUNCTION,
                priority=FailurePriority.HIGH,
                failure_count=3,
                failures=[],
            ),
        }

        result = _generate_summary_statistics(categorized_failures)

        assert result["total_failures"] == 8
        assert result["category_count"] == 2
        assert "rich_compatibility" in result["categories"]
        assert "missing_function" in result["categories"]
        assert result["priority_distribution"]["low"] == 5
        assert result["priority_distribution"]["high"] == 3

    def test_generate_summary_statistics_when_empty_categories_then_returns_zero_stats(
        self,
    ):
        """Test _generate_summary_statistics with empty categories."""
        categorized_failures = {}

        result = _generate_summary_statistics(categorized_failures)

        assert result["total_failures"] == 0
        assert result["category_count"] == 0
        assert result["categories"] == {}
        assert result["priority_distribution"] == {}


class TestCreateCategorizationReport:
    """Test the _create_categorization_report function."""

    def test_create_categorization_report_when_categories_exist_then_creates_serializable_report(
        self,
    ):
        """Test _create_categorization_report creates JSON-serializable report."""
        sample_failure = FailureInfo(
            test_name=SAMPLE_TEST_NAME,
            file_path=Path(SAMPLE_FILE_PATH),
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            error_message=SAMPLE_ERROR_MESSAGE,
        )

        categorized_failures = {
            FailureType.MISSING_FUNCTION: FailureCategory(
                failure_type=FailureType.MISSING_FUNCTION,
                priority=FailurePriority.HIGH,
                failure_count=1,
                failures=[sample_failure],
            ),
        }

        result = _create_categorization_report(categorized_failures)

        assert "missing_function" in result
        category_data = result["missing_function"]
        assert category_data["failure_count"] == 1
        assert len(category_data["failures"]) == 1

        # Verify Path objects are converted to strings
        failure_data = category_data["failures"][0]
        assert isinstance(failure_data["file_path"], str)
        assert failure_data["file_path"] == SAMPLE_FILE_PATH

        # Verify JSON serialization works
        json.dumps(result)  # Should not raise exception

    def test_create_categorization_report_when_empty_categories_then_returns_empty_dict(
        self,
    ):
        """Test _create_categorization_report with empty categories."""
        categorized_failures = {}

        result = _create_categorization_report(categorized_failures)

        assert result == {}


class TestCategorizationConstants:
    """Test that constants are properly defined and accessible."""

    def test_test_constants_are_properly_defined(self):
        """Test that all test constants are properly defined."""
        assert SAMPLE_TEST_NAME
        assert SAMPLE_FILE_PATH
        assert SAMPLE_ERROR_MESSAGE
        assert SAMPLE_STACK_TRACE
        assert RICH_ERROR_MESSAGE
        assert IMPORT_ERROR_MESSAGE
        assert MIGRATION_ERROR_MESSAGE
        assert PYTEST_OUTPUT_SAMPLE
        assert PYTEST_STDERR_SAMPLE

    def test_constants_contain_expected_patterns(self):
        """Test that constants contain expected error patterns."""
        assert "AttributeError" in SAMPLE_ERROR_MESSAGE
        assert "rich.console" in RICH_ERROR_MESSAGE
        assert "ModuleNotFoundError" in IMPORT_ERROR_MESSAGE
        assert "inject_context" in MIGRATION_ERROR_MESSAGE
        assert "FAILED" in PYTEST_OUTPUT_SAMPLE
        assert "ERROR collecting" in PYTEST_STDERR_SAMPLE
