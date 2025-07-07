"""Unit tests for Slice 2.4: Migration Test Marking and Core Test Validation."""

from pathlib import Path
from unittest.mock import patch

import pytest

from slice_2_4_test_marking import (
    DEFAULT_FAILURE_THRESHOLD,
    MarkingResult,
    analyze_test_suite_composition,
    execute_test_marking_workflow,
    generate_reliability_report,
    mark_migration_tests,
    validate_core_test_reliability,
)

# Test constants
TEST_FAILURE_RATE_LOW = 0.02
TEST_FAILURE_RATE_HIGH = 0.08
SAMPLE_TEST_FILES = [
    "tests/unit/test_core_functionality.py",
    "tests/unit/test_migration_helper.py",
    "tests/integration/test_slice_migration.py",
]
SAMPLE_CATEGORIZATION = {
    "tests/unit/test_migration_helper.py": "migration_related",
    "tests/integration/test_slice_migration.py": "migration_integration",
}
SAMPLE_CORE_TESTS = [
    "tests/unit/test_core_functionality.py",
    "tests/unit/test_basic_operations.py",
]


class TestMarkingResult:
    """Test cases for TestMarkingResult class."""

    def test_test_marking_result_initialization(self):
        """Test TestMarkingResult initialization with valid data."""
        marked_tests = {"test1.py": "migration_reason"}
        core_validation = {"test2.py": TEST_FAILURE_RATE_LOW}
        reliability_score = TEST_FAILURE_RATE_LOW

        result = MarkingResult(marked_tests, core_validation, reliability_score)

        assert result.marked_tests == marked_tests
        assert result.core_test_validation == core_validation
        assert result.overall_reliability_score == reliability_score

    def test_meets_reliability_target_pass(self):
        """Test meets_reliability_target returns True for good reliability."""
        result = MarkingResult({}, {}, TEST_FAILURE_RATE_LOW)

        assert result.meets_reliability_target() is True
        assert result.meets_reliability_target(DEFAULT_FAILURE_THRESHOLD) is True

    def test_meets_reliability_target_fail(self):
        """Test meets_reliability_target returns False for poor reliability."""
        result = MarkingResult({}, {}, TEST_FAILURE_RATE_HIGH)

        assert result.meets_reliability_target() is False
        assert result.meets_reliability_target(DEFAULT_FAILURE_THRESHOLD) is False

    def test_meets_reliability_target_custom_threshold(self):
        """Test meets_reliability_target with custom threshold."""
        result = MarkingResult({}, {}, 0.06)

        assert result.meets_reliability_target(0.1) is True
        assert result.meets_reliability_target(0.05) is False

    def test_get_failing_core_tests_empty(self):
        """Test get_failing_core_tests returns empty list when all pass."""
        core_validation = {
            "test1.py": TEST_FAILURE_RATE_LOW,
            "test2.py": TEST_FAILURE_RATE_LOW,
        }
        result = MarkingResult({}, core_validation, TEST_FAILURE_RATE_LOW)

        failing_tests = result.get_failing_core_tests()

        assert failing_tests == []

    def test_get_failing_core_tests_with_failures(self):
        """Test get_failing_core_tests returns failing tests."""
        core_validation = {
            "test1.py": TEST_FAILURE_RATE_LOW,
            "test2.py": TEST_FAILURE_RATE_HIGH,
            "test3.py": TEST_FAILURE_RATE_HIGH,
        }
        result = MarkingResult({}, core_validation, TEST_FAILURE_RATE_LOW)

        failing_tests = result.get_failing_core_tests()

        assert len(failing_tests) == 2
        assert "test2.py" in failing_tests
        assert "test3.py" in failing_tests
        assert "test1.py" not in failing_tests

    def test_get_failing_core_tests_custom_threshold(self):
        """Test get_failing_core_tests with custom threshold."""
        core_validation = {"test1.py": 0.06}
        result = MarkingResult({}, core_validation, 0.06)

        # With default threshold (0.05), should fail
        failing_default = result.get_failing_core_tests()
        assert "test1.py" in failing_default

        # With higher threshold (0.1), should pass
        failing_custom = result.get_failing_core_tests(0.1)
        assert failing_custom == []


class TestMarkMigrationTests:
    """Test cases for mark_migration_tests function."""

    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("slice_2_4_test_marking.mark_migration_test")
    def test_mark_migration_tests_success(self, mock_mark, mock_identify):
        """Test successful migration test marking."""
        mock_identify.return_value = {"test_migrate.py": "pattern_migration"}
        mock_mark.return_value = True

        # Create temporary test files
        with patch("pathlib.Path.exists", return_value=True):
            result = mark_migration_tests(SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION)

        assert len(result) >= 2  # At least categorized tests
        assert mock_mark.call_count >= 2

    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("slice_2_4_test_marking.mark_migration_test")
    def test_mark_migration_tests_with_categorization(self, mock_mark, mock_identify):
        """Test marking tests that are already categorized."""
        mock_identify.return_value = {}
        mock_mark.return_value = True

        with patch("pathlib.Path.exists", return_value=True):
            result = mark_migration_tests(SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION)

        # Should mark the categorized migration tests
        assert len(result) == 2
        expected_calls = [
            ("tests/unit/test_migration_helper.py", "categorized_as_migration_related"),
            ("tests/integration/test_slice_migration.py", "categorized_as_migration_integration"),
        ]

        for call in expected_calls:
            mock_mark.assert_any_call(call[0], call[1])

    def test_mark_migration_tests_empty_input(self):
        """Test mark_migration_tests raises ValueError for empty input."""
        with pytest.raises(ValueError, match="test_files cannot be empty"):
            mark_migration_tests([], {})

    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("slice_2_4_test_marking.mark_migration_test")
    def test_mark_migration_tests_missing_files(self, mock_mark, mock_identify):
        """Test handling of missing test files."""
        mock_identify.return_value = {}

        with patch("pathlib.Path.exists", return_value=False):
            result = mark_migration_tests(SAMPLE_TEST_FILES, {})

        # Should handle missing files gracefully
        assert result == {}
        assert not mock_mark.called

    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("slice_2_4_test_marking.mark_migration_test")
    def test_mark_migration_tests_marking_failure(self, mock_mark, mock_identify):
        """Test handling of marking failures."""
        mock_identify.return_value = {"test_fail.py": "pattern_test"}
        mock_mark.return_value = False  # Simulate marking failure

        with patch("pathlib.Path.exists", return_value=True):
            result = mark_migration_tests(["test_file.py"], {})

        # Should not include failed markings in result
        assert "test_fail.py" not in result


class TestValidateCoreTestReliability:
    """Test cases for validate_core_test_reliability function."""

    @patch("slice_2_4_test_marking.validate_test_reliability")
    def test_validate_core_test_reliability_success(self, mock_validate):
        """Test successful core test reliability validation."""
        mock_validate.return_value = {
            "test1.py": TEST_FAILURE_RATE_LOW,
            "test2.py": TEST_FAILURE_RATE_LOW,
        }

        validation, score = validate_core_test_reliability(SAMPLE_CORE_TESTS)

        assert len(validation) == 2
        assert score == TEST_FAILURE_RATE_LOW
        mock_validate.assert_called_once_with(SAMPLE_CORE_TESTS, DEFAULT_FAILURE_THRESHOLD)

    def test_validate_core_test_reliability_empty_input(self):
        """Test validate_core_test_reliability raises ValueError for empty input."""
        with pytest.raises(ValueError, match="core_test_definitions cannot be empty"):
            validate_core_test_reliability([])

    @patch("slice_2_4_test_marking.validate_test_reliability")
    def test_validate_core_test_reliability_insufficient_tests(self, mock_validate):
        """Test handling of insufficient number of core tests."""
        mock_validate.return_value = {"test1.py": TEST_FAILURE_RATE_LOW}
        few_tests = ["test1.py"]  # Less than MIN_CORE_TESTS_COUNT

        validation, score = validate_core_test_reliability(few_tests)

        assert len(validation) == 1
        assert score == TEST_FAILURE_RATE_LOW

    @patch("slice_2_4_test_marking.validate_test_reliability")
    def test_validate_core_test_reliability_no_tests_validated(self, mock_validate):
        """Test handling when no tests are validated."""
        mock_validate.return_value = {}

        validation, score = validate_core_test_reliability(["test1.py"])

        assert validation == {}
        assert score == 1.0  # 100% failure rate

    @patch("slice_2_4_test_marking.validate_test_reliability")
    def test_validate_core_test_reliability_mixed_results(self, mock_validate):
        """Test reliability calculation with mixed failure rates."""
        mixed_results = {
            "test1.py": 0.01,
            "test2.py": 0.05,
            "test3.py": 0.02,
        }
        mock_validate.return_value = mixed_results

        validation, score = validate_core_test_reliability(["test1.py", "test2.py", "test3.py"])

        expected_average = (0.01 + 0.05 + 0.02) / 3
        assert validation == mixed_results
        assert abs(score - expected_average) < 0.001

    @patch("slice_2_4_test_marking.validate_test_reliability")
    def test_validate_core_test_reliability_custom_threshold(self, mock_validate):
        """Test reliability validation with custom threshold."""
        mock_validate.return_value = {"test1.py": TEST_FAILURE_RATE_LOW}
        custom_threshold = 0.1

        validation, score = validate_core_test_reliability(["test1.py"], custom_threshold)

        mock_validate.assert_called_once_with(["test1.py"], custom_threshold)


class TestExecuteTestMarkingWorkflow:
    """Test cases for execute_test_marking_workflow function."""

    @patch("slice_2_4_test_marking.validate_core_test_reliability")
    @patch("slice_2_4_test_marking.mark_migration_tests")
    def test_execute_test_marking_workflow_success(self, mock_mark, mock_validate):
        """Test successful execution of complete workflow."""
        mock_mark.return_value = {"test_migrate.py": "migration_reason"}
        mock_validate.return_value = ({"test_core.py": TEST_FAILURE_RATE_LOW}, TEST_FAILURE_RATE_LOW)

        result = execute_test_marking_workflow(
            SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION, SAMPLE_CORE_TESTS
        )

        assert isinstance(result, MarkingResult)
        assert len(result.marked_tests) == 1
        assert len(result.core_test_validation) == 1
        assert result.overall_reliability_score == TEST_FAILURE_RATE_LOW
        assert result.meets_reliability_target() is True

    @patch("slice_2_4_test_marking.validate_core_test_reliability")
    @patch("slice_2_4_test_marking.mark_migration_tests")
    def test_execute_test_marking_workflow_poor_reliability(self, mock_mark, mock_validate):
        """Test workflow with poor reliability results."""
        mock_mark.return_value = {}
        mock_validate.return_value = ({"test_core.py": TEST_FAILURE_RATE_HIGH}, TEST_FAILURE_RATE_HIGH)

        result = execute_test_marking_workflow(
            SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION, SAMPLE_CORE_TESTS
        )

        assert result.overall_reliability_score == TEST_FAILURE_RATE_HIGH
        assert result.meets_reliability_target() is False

    @patch("slice_2_4_test_marking.validate_core_test_reliability")
    @patch("slice_2_4_test_marking.mark_migration_tests")
    def test_execute_test_marking_workflow_calls_functions(self, mock_mark, mock_validate):
        """Test workflow calls required functions with correct parameters."""
        mock_mark.return_value = {}
        mock_validate.return_value = ({}, 0.0)

        execute_test_marking_workflow(
            SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION, SAMPLE_CORE_TESTS
        )

        mock_mark.assert_called_once_with(SAMPLE_TEST_FILES, SAMPLE_CATEGORIZATION)
        mock_validate.assert_called_once_with(SAMPLE_CORE_TESTS)


class TestAnalyzeTestSuiteComposition:
    """Test cases for analyze_test_suite_composition function."""

    @patch("slice_2_4_test_marking.identify_core_tests")
    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("pathlib.Path.rglob")
    def test_analyze_test_suite_composition_complete(self, mock_rglob, mock_migration, mock_core):
        """Test complete test suite composition analysis."""
        # Mock file discovery
        mock_files = [
            Path("tests/test_core.py"),
            Path("tests/test_migration.py"),
            Path("tests/test_other.py"),
        ]
        mock_rglob.return_value = mock_files

        # Mock categorization
        mock_migration.return_value = {"tests/test_migration.py": "migration_reason"}
        mock_core.return_value = ["tests/test_core.py"]

        result = analyze_test_suite_composition("tests")

        assert len(result["migration"]) == 1
        assert len(result["core"]) == 1
        assert len(result["unclassified"]) == 1
        assert "tests/test_migration.py" in result["migration"]
        assert "tests/test_core.py" in result["core"]
        assert "tests/test_other.py" in result["unclassified"]

    @patch("slice_2_4_test_marking.identify_core_tests")
    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("pathlib.Path.rglob")
    def test_analyze_test_suite_composition_empty_directory(self, mock_rglob, mock_migration, mock_core):
        """Test composition analysis with empty test directory."""
        mock_rglob.return_value = []
        mock_migration.return_value = {}
        mock_core.return_value = []

        result = analyze_test_suite_composition("empty_tests")

        assert len(result["migration"]) == 0
        assert len(result["core"]) == 0
        assert len(result["unclassified"]) == 0

    @patch("slice_2_4_test_marking.identify_core_tests")
    @patch("slice_2_4_test_marking.identify_migration_tests")
    @patch("pathlib.Path.rglob")
    def test_analyze_test_suite_composition_all_classified(self, mock_rglob, mock_migration, mock_core):
        """Test composition analysis when all tests are classified."""
        mock_files = [Path("tests/test1.py"), Path("tests/test2.py")]
        mock_rglob.return_value = mock_files
        mock_migration.return_value = {"tests/test1.py": "reason"}
        mock_core.return_value = ["tests/test2.py"]

        result = analyze_test_suite_composition("tests")

        assert len(result["unclassified"]) == 0


class TestGenerateReliabilityReport:
    """Test cases for generate_reliability_report function."""

    def test_generate_reliability_report_passing(self):
        """Test report generation for passing reliability."""
        result = MarkingResult(
            marked_tests={"test_migrate.py": "migration_reason"},
            core_test_validation={"test_core.py": TEST_FAILURE_RATE_LOW},
            overall_reliability_score=TEST_FAILURE_RATE_LOW,
        )

        report = generate_reliability_report(result)

        assert "# Test Reliability Report" in report
        assert f"{TEST_FAILURE_RATE_LOW:.2%}" in report
        assert "PASS" in report
        assert "test_migrate.py" in report
        assert "test_core.py" in report

    def test_generate_reliability_report_failing(self):
        """Test report generation for failing reliability."""
        result = MarkingResult(
            marked_tests={},
            core_test_validation={"test_core.py": TEST_FAILURE_RATE_HIGH},
            overall_reliability_score=TEST_FAILURE_RATE_HIGH,
        )

        report = generate_reliability_report(result)

        assert "FAIL" in report
        assert f"{TEST_FAILURE_RATE_HIGH:.2%}" in report
        assert "## Tests Exceeding Failure Threshold" in report
        assert "test_core.py" in report

    def test_generate_reliability_report_empty_results(self):
        """Test report generation with empty results."""
        result = MarkingResult(
            marked_tests={},
            core_test_validation={},
            overall_reliability_score=1.0,
        )

        report = generate_reliability_report(result)

        assert "No core tests validated" in report
        assert "No migration tests marked" in report
        assert "100.00%" in report  # 100% failure rate

    def test_generate_reliability_report_mixed_results(self):
        """Test report generation with mixed pass/fail results."""
        core_validation = {
            "test_good.py": TEST_FAILURE_RATE_LOW,
            "test_bad.py": TEST_FAILURE_RATE_HIGH,
        }
        result = MarkingResult(
            marked_tests={"test_migrate.py": "reason"},
            core_test_validation=core_validation,
            overall_reliability_score=0.05,  # Exactly at threshold
        )

        report = generate_reliability_report(result)

        assert "test_good.py" in report
        assert "test_bad.py" in report
        assert "PASS" in report
        assert "FAIL" in report
