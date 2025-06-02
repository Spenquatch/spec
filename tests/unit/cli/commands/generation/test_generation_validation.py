"""Tests for generation validation module."""

from spec_cli.cli.commands.generation.validation import (
    GenerationValidator,
    validate_file_paths,
    validate_template_selection,
)


class TestGenerationValidator:
    """Test the GenerationValidator class."""

    def test_validate_file_paths_when_no_files_provided_then_returns_invalid_with_error(
        self
    ):
        """Test that validation fails when no source files are provided."""
        validator = GenerationValidator()

        result = validator.validate_file_paths([])

        assert result["valid"] is False
        assert "No source files provided" in result["errors"]
        assert result["warnings"] == []
        assert result["analysis"] == []

    def test_validate_template_selection_when_valid_template_then_returns_valid(self):
        """Test that validation succeeds for valid template names."""
        validator = GenerationValidator()

        result = validator.validate_template_selection("default")

        assert result["valid"] is True
        assert result["template"] == "default"
        assert "default" in result["available"]
        assert "minimal" in result["available"]
        assert "comprehensive" in result["available"]


class TestConvenienceFunctions:
    """Test the standalone convenience functions."""

    def test_validate_file_paths_function_when_empty_list_then_returns_invalid(self):
        """Test the validate_file_paths convenience function with empty input."""
        result = validate_file_paths([])

        assert result["valid"] is False
        assert "No source files provided" in result["errors"]

    def test_validate_template_selection_function_when_invalid_template_then_returns_invalid(
        self
    ):
        """Test the validate_template_selection convenience function with invalid template."""
        result = validate_template_selection("nonexistent")

        assert result["valid"] is False
        assert "Template 'nonexistent' not found" in result["error"]
        assert "default" in result["available"]
