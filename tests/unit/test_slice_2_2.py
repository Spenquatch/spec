"""Unit tests for Slice 2.2: Rich vs Plain Text Output Compatibility Resolution."""

from unittest.mock import patch

import pytest

from slice_2_2_output_compatibility import (
    OutputCompatibilityResolver,
    batch_resolve_compatibility,
    create_output_compatibility_resolver,
)
from spec_cli.utils.output_formatters.test_output_normalizer import (
    extract_formatting_metadata,
    normalize_output_for_testing,
)
from spec_cli.utils.test_helpers.cli_test_helpers import CLITestResult

# Test constants to avoid magic numbers
DEFAULT_MODE = "auto"
PLAIN_MODE = "plain"
RICH_MODE = "rich"
SAMPLE_RICH_OUTPUT = "[bold]Project initialized successfully[/bold]"
SAMPLE_PLAIN_OUTPUT = "Project initialized successfully"
SAMPLE_ANSI_OUTPUT = "\x1b[1mProject initialized successfully\x1b[0m"
INVALID_MODE = "invalid_mode"
EMPTY_STRING = ""
SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1


class TestOutputCompatibilityResolver:
    """Test OutputCompatibilityResolver class."""

    def test_init_with_valid_default_mode(self):
        """Test initialization with valid default mode."""
        resolver = OutputCompatibilityResolver(PLAIN_MODE)
        assert resolver.default_mode == PLAIN_MODE
        assert resolver.processed_outputs == []

    def test_init_with_auto_mode(self):
        """Test initialization with auto mode."""
        resolver = OutputCompatibilityResolver(DEFAULT_MODE)
        assert resolver.default_mode == DEFAULT_MODE

    def test_init_with_invalid_mode_raises_value_error(self):
        """Test initialization with invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid default_mode"):
            OutputCompatibilityResolver(INVALID_MODE)

    def test_resolve_output_compatibility_rich_to_plain(self):
        """Test resolving Rich output to plain text format."""
        resolver = OutputCompatibilityResolver()

        result = resolver.resolve_output_compatibility(SAMPLE_RICH_OUTPUT, PLAIN_MODE)

        assert result["normalized_output"] == SAMPLE_PLAIN_OUTPUT
        assert result["compatibility_status"] is True
        assert result["expected_format"] == PLAIN_MODE
        assert result["transformation_applied"] is True
        assert "original_metadata" in result

    def test_resolve_output_compatibility_plain_to_plain(self):
        """Test resolving plain output to plain text format (no transformation)."""
        resolver = OutputCompatibilityResolver()

        result = resolver.resolve_output_compatibility(SAMPLE_PLAIN_OUTPUT, PLAIN_MODE)

        assert result["normalized_output"] == SAMPLE_PLAIN_OUTPUT
        assert result["compatibility_status"] is True
        assert result["transformation_applied"] is False

    def test_resolve_output_compatibility_ansi_to_plain(self):
        """Test resolving ANSI output to plain text format."""
        resolver = OutputCompatibilityResolver()

        result = resolver.resolve_output_compatibility(SAMPLE_ANSI_OUTPUT, PLAIN_MODE)

        assert result["normalized_output"] == SAMPLE_PLAIN_OUTPUT
        assert result["compatibility_status"] is True
        assert result["transformation_applied"] is True

    def test_resolve_output_compatibility_invalid_test_output_type(self):
        """Test resolve_output_compatibility with invalid test_output type."""
        resolver = OutputCompatibilityResolver()

        with pytest.raises(TypeError, match="test_output must be a string"):
            resolver.resolve_output_compatibility(123, PLAIN_MODE)

    def test_resolve_output_compatibility_invalid_expected_format(self):
        """Test resolve_output_compatibility with invalid expected_format."""
        resolver = OutputCompatibilityResolver()

        with pytest.raises(ValueError, match="Invalid expected_format"):
            resolver.resolve_output_compatibility(SAMPLE_PLAIN_OUTPUT, INVALID_MODE)

    def test_resolve_output_compatibility_tracks_processed_outputs(self):
        """Test that resolved outputs are tracked for analysis."""
        resolver = OutputCompatibilityResolver()

        resolver.resolve_output_compatibility(SAMPLE_RICH_OUTPUT, PLAIN_MODE)
        resolver.resolve_output_compatibility(SAMPLE_PLAIN_OUTPUT, PLAIN_MODE)

        assert len(resolver.processed_outputs) == 2
        assert resolver.processed_outputs[0]["original_format"] == RICH_MODE
        assert resolver.processed_outputs[1]["original_format"] == PLAIN_MODE

    def test_validate_cli_test_result_success(self):
        """Test successful CLI test result validation."""
        resolver = OutputCompatibilityResolver()
        test_result = CLITestResult(
            exit_code=SUCCESS_EXIT_CODE,
            output=SAMPLE_RICH_OUTPUT,
            exception=None,
            command="test_command",
            args=[],
        )
        expected_outputs = [SAMPLE_PLAIN_OUTPUT]

        is_valid = resolver.validate_cli_test_result(test_result, expected_outputs)

        assert is_valid is True

    def test_validate_cli_test_result_failure_pattern_not_found(self):
        """Test CLI test result validation when expected pattern not found."""
        resolver = OutputCompatibilityResolver()
        test_result = CLITestResult(
            exit_code=SUCCESS_EXIT_CODE,
            output=SAMPLE_RICH_OUTPUT,
            exception=None,
            command="test_command",
            args=[],
        )
        expected_outputs = ["Pattern not in output"]

        is_valid = resolver.validate_cli_test_result(test_result, expected_outputs)

        assert is_valid is False

    def test_validate_cli_test_result_invalid_test_result_type(self):
        """Test validate_cli_test_result with invalid test_result type."""
        resolver = OutputCompatibilityResolver()

        with pytest.raises(TypeError, match="test_result must be CLITestResult"):
            resolver.validate_cli_test_result("invalid", ["pattern"])

    def test_validate_cli_test_result_empty_expected_outputs(self):
        """Test validate_cli_test_result with empty expected_outputs."""
        resolver = OutputCompatibilityResolver()
        test_result = CLITestResult(
            exit_code=SUCCESS_EXIT_CODE,
            output=SAMPLE_PLAIN_OUTPUT,
            exception=None,
            command="test_command",
            args=[],
        )

        with pytest.raises(ValueError, match="expected_outputs cannot be empty"):
            resolver.validate_cli_test_result(test_result, [])

    def test_validate_cli_test_result_multiple_patterns(self):
        """Test CLI test result validation with multiple expected patterns."""
        resolver = OutputCompatibilityResolver()
        test_result = CLITestResult(
            exit_code=SUCCESS_EXIT_CODE,
            output="[bold]Project[/bold] initialized [green]successfully[/green]",
            exception=None,
            command="test_command",
            args=[],
        )
        expected_outputs = ["Project", "initialized", "successfully"]

        is_valid = resolver.validate_cli_test_result(test_result, expected_outputs)

        assert is_valid is True

    def test_get_compatibility_report_no_outputs_processed(self):
        """Test compatibility report when no outputs have been processed."""
        resolver = OutputCompatibilityResolver()

        report = resolver.get_compatibility_report()

        assert report["total_processed"] == 0
        assert report["success_rate"] == 0.0
        assert report["transformations_applied"] == 0
        assert report["format_distribution"] == {}
        assert "message" in report

    def test_get_compatibility_report_with_processed_outputs(self):
        """Test compatibility report after processing outputs."""
        resolver = OutputCompatibilityResolver()

        # Process some outputs
        resolver.resolve_output_compatibility(SAMPLE_RICH_OUTPUT, PLAIN_MODE)
        resolver.resolve_output_compatibility(SAMPLE_PLAIN_OUTPUT, PLAIN_MODE)
        resolver.resolve_output_compatibility(SAMPLE_ANSI_OUTPUT, PLAIN_MODE)

        report = resolver.get_compatibility_report()

        assert report["total_processed"] == 3
        assert report["successful_resolutions"] == 3
        assert report["success_rate"] == 1.0
        assert report["transformations_applied"] == 2  # Rich and ANSI were transformed
        assert report["transformation_rate"] == 2 / 3
        assert RICH_MODE in report["format_distribution"]
        assert PLAIN_MODE in report["format_distribution"]

    def test_assess_compatibility_same_formats(self):
        """Test _assess_compatibility with same formats."""
        resolver = OutputCompatibilityResolver()
        metadata = {"detected_format": PLAIN_MODE}

        is_compatible = resolver._assess_compatibility(metadata, PLAIN_MODE)

        assert is_compatible is True

    def test_assess_compatibility_rich_to_plain(self):
        """Test _assess_compatibility for Rich to plain conversion."""
        resolver = OutputCompatibilityResolver()
        metadata = {"detected_format": RICH_MODE}

        is_compatible = resolver._assess_compatibility(metadata, PLAIN_MODE)

        assert is_compatible is True

    def test_assess_compatibility_plain_to_rich(self):
        """Test _assess_compatibility for plain to Rich conversion."""
        resolver = OutputCompatibilityResolver()
        metadata = {"detected_format": PLAIN_MODE}

        is_compatible = resolver._assess_compatibility(metadata, RICH_MODE)

        assert is_compatible is True

    @patch("slice_2_2_output_compatibility.extract_formatting_metadata")
    def test_resolve_output_compatibility_exception_handling(self, mock_extract):
        """Test exception handling in resolve_output_compatibility."""
        mock_extract.side_effect = RuntimeError("Metadata extraction failed")
        resolver = OutputCompatibilityResolver()

        with pytest.raises(RuntimeError, match="Metadata extraction failed"):
            resolver.resolve_output_compatibility(SAMPLE_PLAIN_OUTPUT, PLAIN_MODE)

    @patch(
        "slice_2_2_output_compatibility.OutputCompatibilityResolver.resolve_output_compatibility"
    )
    def test_validate_cli_test_result_exception_handling(self, mock_resolve):
        """Test exception handling in validate_cli_test_result."""
        mock_resolve.side_effect = RuntimeError("Resolution failed")
        resolver = OutputCompatibilityResolver()
        test_result = CLITestResult(
            exit_code=SUCCESS_EXIT_CODE,
            output=SAMPLE_PLAIN_OUTPUT,
            exception=None,
            command="test_command",
            args=[],
        )

        # Should return False when exception occurs
        is_valid = resolver.validate_cli_test_result(test_result, ["pattern"])
        assert is_valid is False

    def test_assess_compatibility_unsupported_format(self):
        """Test _assess_compatibility fallback for unsupported format combinations."""
        resolver = OutputCompatibilityResolver()
        # This shouldn't happen in real usage but tests the fallback path
        metadata = {"detected_format": "unsupported_format"}

        is_compatible = resolver._assess_compatibility(metadata, PLAIN_MODE)

        assert is_compatible is False


class TestCreateOutputCompatibilityResolver:
    """Test create_output_compatibility_resolver factory function."""

    def test_create_with_default_mode(self):
        """Test creating resolver with default mode."""
        resolver = create_output_compatibility_resolver()
        assert resolver.default_mode == DEFAULT_MODE

    def test_create_with_custom_mode(self):
        """Test creating resolver with custom mode."""
        resolver = create_output_compatibility_resolver(PLAIN_MODE)
        assert resolver.default_mode == PLAIN_MODE


class TestBatchResolveCompatibility:
    """Test batch_resolve_compatibility function."""

    def test_batch_resolve_empty_outputs_raises_value_error(self):
        """Test batch resolve with empty outputs list raises ValueError."""
        with pytest.raises(ValueError, match="outputs list cannot be empty"):
            batch_resolve_compatibility([])

    def test_batch_resolve_invalid_outputs_type_raises_type_error(self):
        """Test batch resolve with invalid outputs type raises TypeError."""
        with pytest.raises(TypeError, match="outputs must be a list"):
            batch_resolve_compatibility("invalid")

    def test_batch_resolve_invalid_output_format_raises_type_error(self):
        """Test batch resolve with invalid output format raises TypeError."""
        invalid_outputs = [("text", "format", "extra")]  # 3-tuple instead of 2-tuple

        with pytest.raises(TypeError, match="must be a tuple of \\(str, str\\)"):
            batch_resolve_compatibility(invalid_outputs)

    def test_batch_resolve_valid_outputs(self):
        """Test batch resolve with valid outputs."""
        outputs = [
            (SAMPLE_RICH_OUTPUT, PLAIN_MODE),
            (SAMPLE_PLAIN_OUTPUT, PLAIN_MODE),
            (SAMPLE_ANSI_OUTPUT, PLAIN_MODE),
        ]

        results = batch_resolve_compatibility(outputs)

        assert len(results) == 3
        assert all("normalized_output" in result for result in results)
        assert all(result["compatibility_status"] for result in results)

    def test_batch_resolve_with_custom_resolver(self):
        """Test batch resolve with custom resolver instance."""
        outputs = [(SAMPLE_RICH_OUTPUT, PLAIN_MODE)]
        custom_resolver = create_output_compatibility_resolver(PLAIN_MODE)

        results = batch_resolve_compatibility(outputs, custom_resolver)

        assert len(results) == 1
        assert results[0]["normalized_output"] == SAMPLE_PLAIN_OUTPUT

    @patch(
        "slice_2_2_output_compatibility.OutputCompatibilityResolver.resolve_output_compatibility"
    )
    def test_batch_resolve_handles_exceptions(self, mock_resolve):
        """Test batch resolve handles exceptions gracefully."""
        mock_resolve.side_effect = RuntimeError("Test error")
        outputs = [(SAMPLE_RICH_OUTPUT, PLAIN_MODE)]

        results = batch_resolve_compatibility(outputs)

        assert len(results) == 1
        assert (
            results[0]["normalized_output"] == SAMPLE_RICH_OUTPUT
        )  # Fallback to original
        assert results[0]["compatibility_status"] is False
        assert "error" in results[0]


class TestOutputNormalizerIntegration:
    """Test integration with output normalizer helper."""

    def test_normalize_output_for_testing_rich_markup(self):
        """Test normalize_output_for_testing with Rich markup."""
        normalized = normalize_output_for_testing(SAMPLE_RICH_OUTPUT, PLAIN_MODE)
        assert normalized == SAMPLE_PLAIN_OUTPUT

    def test_normalize_output_for_testing_ansi_codes(self):
        """Test normalize_output_for_testing with ANSI codes."""
        normalized = normalize_output_for_testing(SAMPLE_ANSI_OUTPUT, PLAIN_MODE)
        assert normalized == SAMPLE_PLAIN_OUTPUT

    def test_normalize_output_for_testing_auto_detection(self):
        """Test normalize_output_for_testing with auto detection."""
        normalized = normalize_output_for_testing(SAMPLE_RICH_OUTPUT, DEFAULT_MODE)
        # Auto mode preserves original format for Rich input
        assert (
            normalized == SAMPLE_PLAIN_OUTPUT
        )  # Rich content converted to plain when auto-detected as rich

    def test_extract_formatting_metadata_rich_output(self):
        """Test extract_formatting_metadata with Rich output."""
        metadata = extract_formatting_metadata(SAMPLE_RICH_OUTPUT)

        assert metadata["has_rich_markup"] is True
        assert metadata["detected_format"] == RICH_MODE
        assert metadata["character_count"] == len(SAMPLE_RICH_OUTPUT)
        assert len(metadata["rich_tags"]) > 0

    def test_extract_formatting_metadata_plain_output(self):
        """Test extract_formatting_metadata with plain output."""
        metadata = extract_formatting_metadata(SAMPLE_PLAIN_OUTPUT)

        assert metadata["has_rich_markup"] is False
        assert metadata["detected_format"] == PLAIN_MODE
        assert metadata["character_count"] == len(SAMPLE_PLAIN_OUTPUT)
        assert len(metadata["rich_tags"]) == 0

    def test_extract_formatting_metadata_ansi_output(self):
        """Test extract_formatting_metadata with ANSI output."""
        metadata = extract_formatting_metadata(SAMPLE_ANSI_OUTPUT)

        assert metadata["has_ansi_codes"] is True
        assert metadata["detected_format"] == RICH_MODE  # ANSI treated as Rich-like
        assert len(metadata["ansi_codes"]) > 0


# Test fixtures for reusable test data
@pytest.fixture
def sample_cli_test_result() -> CLITestResult:
    """Create sample CLI test result for testing."""
    return CLITestResult(
        exit_code=SUCCESS_EXIT_CODE,
        output=SAMPLE_RICH_OUTPUT,
        exception=None,
        command="test_command",
        args=["arg1", "arg2"],
    )


@pytest.fixture
def sample_batch_outputs() -> list[tuple[str, str]]:
    """Create sample batch outputs for testing."""
    return [
        (SAMPLE_RICH_OUTPUT, PLAIN_MODE),
        (SAMPLE_PLAIN_OUTPUT, PLAIN_MODE),
        (SAMPLE_ANSI_OUTPUT, PLAIN_MODE),
        ("[red]Error occurred[/red]", PLAIN_MODE),
        ("Simple text", PLAIN_MODE),
    ]


class TestIntegrationWithFixtures:
    """Test compatibility layer using fixtures."""

    def test_resolver_with_sample_cli_result(self, sample_cli_test_result):
        """Test resolver integration with CLI test result."""
        resolver = OutputCompatibilityResolver()
        expected_outputs = [SAMPLE_PLAIN_OUTPUT]

        is_valid = resolver.validate_cli_test_result(
            sample_cli_test_result, expected_outputs
        )

        assert is_valid is True

    def test_batch_processing_with_sample_outputs(self, sample_batch_outputs):
        """Test batch processing with sample outputs."""
        results = batch_resolve_compatibility(sample_batch_outputs)

        assert len(results) == len(sample_batch_outputs)
        assert all(result["compatibility_status"] for result in results)

        # Check specific transformations
        assert results[0]["transformation_applied"] is True  # Rich to plain
        assert results[1]["transformation_applied"] is False  # Plain to plain
        assert results[2]["transformation_applied"] is True  # ANSI to plain
