"""Unit tests for test failure categorizer utilities."""

from pathlib import Path

import pytest

from spec_cli.utils.test_helpers.test_failure_categorizer import (
    FailureCategorizationError,
    FailureCategory,
    FailureInfo,
    FailurePriority,
    FailureType,
    _analyze_failure_type,
    _determine_failure_priority,
    _estimate_remediation_effort,
    _generate_remediation_notes,
    _get_remediation_strategy,
    categorize_test_failure,
)

# Test constants
SAMPLE_TEST_NAME = "tests/unit/test_example.py::TestClass::test_method"
SAMPLE_FILE_PATH = "tests/unit/test_example.py"
RICH_ERROR_MESSAGE = "rich.console.Console object has no attribute 'print_text'"
IMPORT_ERROR_MESSAGE = "ModuleNotFoundError: No module named 'missing_module'"
MIGRATION_ERROR_MESSAGE = "inject_context decorator not found"
ATTRIBUTE_ERROR_MESSAGE = "AttributeError: 'NoneType' object has no attribute 'method'"
FIXTURE_ERROR_MESSAGE = "fixture 'test_fixture' not found"
CONTEXT_ERROR_MESSAGE = "context injection failed in decorator"
ASSERTION_ERROR_MESSAGE = "AssertionError: expected 5, got 3"

class TestCategorizeTestFailure:
    """Test the main categorize_test_failure function."""

    def test_categorize_test_failure_when_valid_failure_info_then_returns_category(
        self,
    ):
        """Test categorize_test_failure with valid failure information."""
        failure_info = {
            "test_name": SAMPLE_TEST_NAME,
            "file_path": SAMPLE_FILE_PATH,
            "error_message": ATTRIBUTE_ERROR_MESSAGE,
            "stack_trace": "Traceback with AttributeError details",
        }

        result = categorize_test_failure(failure_info)

        assert isinstance(result, FailureCategory)
        assert result.failure_type == FailureType.MISSING_FUNCTION
        assert result.failure_count == 1
        assert len(result.failures) == 1
        assert result.failures[0].test_name == SAMPLE_TEST_NAME
        assert result.failures[0].file_path == Path(SAMPLE_FILE_PATH)

    def test_categorize_test_failure_when_rich_error_then_categorizes_as_rich_compatibility(
        self,
    ):
        """Test categorize_test_failure correctly identifies Rich compatibility issues."""
        failure_info = {
            "test_name": SAMPLE_TEST_NAME,
            "file_path": SAMPLE_FILE_PATH,
            "error_message": RICH_ERROR_MESSAGE,
            "stack_trace": "",
        }

        result = categorize_test_failure(failure_info)

        assert result.failure_type == FailureType.RICH_COMPATIBILITY
        assert result.priority == FailurePriority.LOW

    def test_categorize_test_failure_when_import_error_then_categorizes_as_import_error(
        self,
    ):
        """Test categorize_test_failure correctly identifies import errors."""
        failure_info = {
            "test_name": SAMPLE_TEST_NAME,
            "file_path": SAMPLE_FILE_PATH,
            "error_message": IMPORT_ERROR_MESSAGE,
            "stack_trace": "",
        }

        result = categorize_test_failure(failure_info)

        assert result.failure_type == FailureType.IMPORT_ERROR
        assert result.priority == FailurePriority.CRITICAL

    def test_categorize_test_failure_when_migration_artifact_then_categorizes_correctly(
        self,
    ):
        """Test categorize_test_failure correctly identifies migration artifacts."""
        failure_info = {
            "test_name": SAMPLE_TEST_NAME,
            "file_path": SAMPLE_FILE_PATH,
            "error_message": MIGRATION_ERROR_MESSAGE,
            "stack_trace": "",
        }

        result = categorize_test_failure(failure_info)

        assert result.failure_type == FailureType.MIGRATION_ARTIFACT
        assert result.priority == FailurePriority.HIGH

    def test_categorize_test_failure_when_missing_keys_then_uses_defaults(self):
        """Test categorize_test_failure handles missing keys gracefully."""
        failure_info = {
            "test_name": SAMPLE_TEST_NAME,
            # Missing file_path, error_message, stack_trace
        }

        result = categorize_test_failure(failure_info)

        assert isinstance(result, FailureCategory)
        assert result.failures[0].file_path == Path("")
        assert result.failures[0].error_message == ""

    def test_categorize_test_failure_when_categorization_error_then_raises_exception(
        self,
    ):
        """Test categorize_test_failure raises exception on internal error."""
        # Invalid failure_info that causes internal error
        failure_info = None

        with pytest.raises(
            FailureCategorizationError, match="Failed to categorize test failure"
        ):
            categorize_test_failure(failure_info)

class TestAnalyzeFailureType:
    """Test the _analyze_failure_type function."""

    def test_analyze_failure_type_when_rich_patterns_then_returns_rich_compatibility(
        self,
    ):
        """Test _analyze_failure_type identifies Rich compatibility patterns."""
        error_message = "rich.console error occurred"
        stack_trace = "Console.print_text() failed"

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.RICH_COMPATIBILITY

    def test_analyze_failure_type_when_attribute_error_then_returns_missing_function(
        self,
    ):
        """Test _analyze_failure_type identifies missing function patterns."""
        error_message = "AttributeError: object has no attribute 'method'"
        stack_trace = ""

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.MISSING_FUNCTION

    def test_analyze_failure_type_when_import_error_then_returns_import_error(self):
        """Test _analyze_failure_type identifies import error patterns."""
        error_message = "ImportError: cannot import name"
        stack_trace = ""

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.IMPORT_ERROR

    def test_analyze_failure_type_when_migration_patterns_then_returns_migration_artifact(
        self,
    ):
        """Test _analyze_failure_type identifies migration artifact patterns."""
        error_message = "singleton pattern not found"
        stack_trace = "inject_context decorator missing"

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.MIGRATION_ARTIFACT

    def test_analyze_failure_type_when_fixture_patterns_then_returns_fixture_dependency(
        self,
    ):
        """Test _analyze_failure_type identifies fixture dependency patterns."""
        error_message = "pytest fixture not found"
        stack_trace = ""

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.FIXTURE_DEPENDENCY

    def test_analyze_failure_type_when_context_patterns_then_returns_context_injection(
        self,
    ):
        """Test _analyze_failure_type identifies context injection patterns."""
        error_message = "context injection failed"
        stack_trace = "decorator compatibility issue"

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.CONTEXT_INJECTION

    def test_analyze_failure_type_when_assertion_error_then_returns_real_logic_error(
        self,
    ):
        """Test _analyze_failure_type identifies real logic errors."""
        error_message = "AssertionError: expected 5, got 3"
        stack_trace = ""

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.REAL_LOGIC_ERROR

    def test_analyze_failure_type_when_unknown_pattern_then_returns_unknown(self):
        """Test _analyze_failure_type returns UNKNOWN for unrecognized patterns."""
        error_message = "Some completely unknown error"
        stack_trace = "Random stack trace"

        result = _analyze_failure_type(error_message, stack_trace)

        assert result == FailureType.UNKNOWN

class TestDetermineFailurePriority:
    """Test the _determine_failure_priority function."""

    def test_determine_failure_priority_when_import_error_then_returns_critical(self):
        """Test _determine_failure_priority returns CRITICAL for import errors."""
        priority = _determine_failure_priority(
            FailureType.IMPORT_ERROR, SAMPLE_TEST_NAME, Path(SAMPLE_FILE_PATH)
        )

        assert priority == FailurePriority.CRITICAL

    def test_determine_failure_priority_when_core_cli_test_then_returns_high(self):
        """Test _determine_failure_priority returns HIGH for core CLI tests."""
        core_file_path = Path("tests/unit/cli/test_main.py")

        priority = _determine_failure_priority(
            FailureType.MISSING_FUNCTION, SAMPLE_TEST_NAME, core_file_path
        )

        assert priority == FailurePriority.HIGH

    def test_determine_failure_priority_when_migration_artifact_then_returns_high(self):
        """Test _determine_failure_priority returns HIGH for migration artifacts."""
        priority = _determine_failure_priority(
            FailureType.MIGRATION_ARTIFACT, SAMPLE_TEST_NAME, Path(SAMPLE_FILE_PATH)
        )

        assert priority == FailurePriority.HIGH

    def test_determine_failure_priority_when_integration_test_then_returns_medium(self):
        """Test _determine_failure_priority returns MEDIUM for integration tests."""
        integration_file_path = Path("tests/integration/test_feature.py")

        priority = _determine_failure_priority(
            FailureType.MISSING_FUNCTION, SAMPLE_TEST_NAME, integration_file_path
        )

        assert priority == FailurePriority.MEDIUM

    def test_determine_failure_priority_when_rich_compatibility_then_returns_low(self):
        """Test _determine_failure_priority returns LOW for Rich compatibility."""
        priority = _determine_failure_priority(
            FailureType.RICH_COMPATIBILITY, SAMPLE_TEST_NAME, Path(SAMPLE_FILE_PATH)
        )

        assert priority == FailurePriority.LOW

    def test_determine_failure_priority_when_default_case_then_returns_medium(self):
        """Test _determine_failure_priority returns MEDIUM for default case."""
        priority = _determine_failure_priority(
            FailureType.UNKNOWN, SAMPLE_TEST_NAME, Path(SAMPLE_FILE_PATH)
        )

        assert priority == FailurePriority.MEDIUM

class TestGenerateRemediationNotes:
    """Test the _generate_remediation_notes function."""

    def test_generate_remediation_notes_when_rich_compatibility_then_returns_ui_guidance(
        self,
    ):
        """Test _generate_remediation_notes provides UI-specific guidance for Rich issues."""
        notes = _generate_remediation_notes(FailureType.RICH_COMPATIBILITY)

        assert "Rich UI compatibility" in notes
        assert "mock console" in notes

    def test_generate_remediation_notes_when_missing_function_then_returns_implementation_guidance(
        self,
    ):
        """Test _generate_remediation_notes provides implementation guidance."""
        notes = _generate_remediation_notes(FailureType.MISSING_FUNCTION)

        assert "Implement missing function" in notes
        assert "renamed or moved" in notes

    def test_generate_remediation_notes_when_migration_artifact_then_returns_cleanup_guidance(
        self,
    ):
        """Test _generate_remediation_notes provides migration cleanup guidance."""
        notes = _generate_remediation_notes(FailureType.MIGRATION_ARTIFACT)

        assert "Clean up migration artifacts" in notes
        assert "context injection" in notes

    def test_generate_remediation_notes_when_unknown_type_then_returns_manual_analysis(
        self,
    ):
        """Test _generate_remediation_notes suggests manual analysis for unknown types."""
        notes = _generate_remediation_notes(FailureType.UNKNOWN)

        assert "manual analysis" in notes.lower()
        assert "stack trace" in notes.lower()

class TestGetRemediationStrategy:
    """Test the _get_remediation_strategy function."""

    def test_get_remediation_strategy_when_each_failure_type_then_returns_appropriate_strategy(
        self,
    ):
        """Test _get_remediation_strategy returns appropriate strategy for each type."""
        strategies = {
            FailureType.RICH_COMPATIBILITY: "Batch update UI testing patterns",
            FailureType.MISSING_FUNCTION: "Implement missing functionality",
            FailureType.MIGRATION_ARTIFACT: "Complete migration cleanup",
            FailureType.IMPORT_ERROR: "Fix import structure",
            FailureType.FIXTURE_DEPENDENCY: "Migrate test fixtures",
            FailureType.CONTEXT_INJECTION: "Fix injection patterns",
            FailureType.REAL_LOGIC_ERROR: "Debug and fix logic",
            FailureType.UNKNOWN: "Manual investigation required",
        }

        for failure_type, expected_strategy in strategies.items():
            result = _get_remediation_strategy(failure_type)
            assert result == expected_strategy

class TestEstimateRemediationEffort:
    """Test the _estimate_remediation_effort function."""

    def test_estimate_remediation_effort_when_each_failure_type_then_returns_time_estimate(
        self,
    ):
        """Test _estimate_remediation_effort returns time estimates for each type."""
        efforts = {
            FailureType.RICH_COMPATIBILITY: "2-4 hours",
            FailureType.MISSING_FUNCTION: "1-8 hours",
            FailureType.MIGRATION_ARTIFACT: "4-8 hours",
            FailureType.IMPORT_ERROR: "1-2 hours",
            FailureType.FIXTURE_DEPENDENCY: "2-6 hours",
            FailureType.CONTEXT_INJECTION: "3-6 hours",
            FailureType.REAL_LOGIC_ERROR: "2-12 hours",
            FailureType.UNKNOWN: "Unknown",
        }

        for failure_type, expected_effort in efforts.items():
            result = _estimate_remediation_effort(failure_type)
            assert result == expected_effort

class TestDataClasses:
    """Test the data class definitions."""

    def test_test_failure_info_creation_when_all_fields_then_creates_successfully(self):
        """Test FailureInfo can be created with all fields."""
        failure_info = FailureInfo(
            test_name=SAMPLE_TEST_NAME,
            file_path=Path(SAMPLE_FILE_PATH),
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            error_message=ATTRIBUTE_ERROR_MESSAGE,
            stack_trace="Sample stack trace",
            remediation_notes="Sample notes",
            related_failures=["test1", "test2"],
        )

        assert failure_info.test_name == SAMPLE_TEST_NAME
        assert failure_info.file_path == Path(SAMPLE_FILE_PATH)
        assert failure_info.failure_type == FailureType.MISSING_FUNCTION
        assert failure_info.priority == FailurePriority.HIGH
        assert len(failure_info.related_failures) == 2

    def test_test_failure_category_creation_when_all_fields_then_creates_successfully(
        self,
    ):
        """Test FailureCategory can be created with all fields."""
        sample_failure = FailureInfo(
            test_name=SAMPLE_TEST_NAME,
            file_path=Path(SAMPLE_FILE_PATH),
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            error_message=ATTRIBUTE_ERROR_MESSAGE,
        )

        category = FailureCategory(
            failure_type=FailureType.MISSING_FUNCTION,
            priority=FailurePriority.HIGH,
            failure_count=1,
            failures=[sample_failure],
            remediation_strategy="Implement missing functionality",
            estimated_effort="1-8 hours",
        )

        assert category.failure_type == FailureType.MISSING_FUNCTION
        assert category.priority == FailurePriority.HIGH
        assert category.failure_count == 1
        assert len(category.failures) == 1

class TestEnumDefinitions:
    """Test the enum definitions."""

    def test_failure_type_enum_when_all_values_then_accessible(self):
        """Test FailureType enum has all expected values."""
        expected_values = [
            "rich_compatibility",
            "missing_function",
            "migration_artifact",
            "import_error",
            "fixture_dependency",
            "context_injection",
            "real_logic_error",
            "unknown",
        ]

        for expected_value in expected_values:
            assert any(ft.value == expected_value for ft in FailureType)

    def test_failure_priority_enum_when_all_values_then_accessible(self):
        """Test FailurePriority enum has all expected values."""
        expected_values = ["critical", "high", "medium", "low"]

        for expected_value in expected_values:
            assert any(fp.value == expected_value for fp in FailurePriority)
