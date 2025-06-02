"""Tests for CLI exception handling (cli/exceptions.py)."""

import click
import pytest

from spec_cli.cli.exceptions import (
    CLIConfigurationError,
    CLIError,
    CLIOperationError,
    CLIValidationError,
    convert_to_click_exception,
    handle_validation_error,
)
from spec_cli.exceptions import SpecError


class TestCLIExceptions:
    """Test cases for CLI exception classes."""

    def test_cli_error_inheritance(self):
        """Test that CLIError inherits from SpecError."""
        error = CLIError("Test error")
        assert isinstance(error, SpecError)
        assert isinstance(error, CLIError)
        assert str(error) == "Test error"

    def test_cli_validation_error_with_parameter(self):
        """Test CLIValidationError with parameter and suggestions."""
        suggestions = ["Try option A", "Try option B"]
        error = CLIValidationError(
            "Invalid parameter", parameter="test_param", suggestions=suggestions
        )
        
        assert isinstance(error, CLIError)
        assert str(error) == "Invalid parameter"
        assert error.parameter == "test_param"
        assert error.suggestions == suggestions

    def test_cli_validation_error_without_suggestions(self):
        """Test CLIValidationError without suggestions."""
        error = CLIValidationError("Invalid parameter", parameter="test_param")
        
        assert str(error) == "Invalid parameter"
        assert error.parameter == "test_param"
        assert error.suggestions == []

    def test_cli_configuration_error(self):
        """Test CLIConfigurationError."""
        error = CLIConfigurationError("Configuration error")
        assert isinstance(error, CLIError)
        assert str(error) == "Configuration error"

    def test_cli_operation_error(self):
        """Test CLIOperationError."""
        error = CLIOperationError("Operation failed")
        assert isinstance(error, CLIError)
        assert str(error) == "Operation failed"


class TestExceptionConversion:
    """Test cases for exception conversion utilities."""

    def test_convert_click_exception_unchanged(self):
        """Test that ClickException is returned unchanged."""
        original_error = click.ClickException("Original error")
        converted = convert_to_click_exception(original_error)
        
        assert converted is original_error
        assert str(converted) == "Original error"

    def test_convert_cli_error(self):
        """Test conversion of CLIError to ClickException."""
        cli_error = CLIError("CLI error message")
        converted = convert_to_click_exception(cli_error)
        
        assert isinstance(converted, click.ClickException)
        assert converted.message == "CLI error message"

    def test_convert_spec_error(self):
        """Test conversion of SpecError to ClickException."""
        spec_error = SpecError("Spec error message")
        converted = convert_to_click_exception(spec_error)
        
        assert isinstance(converted, click.ClickException)
        assert converted.message == "Spec error: Spec error message"

    def test_convert_generic_error(self):
        """Test conversion of generic Exception to ClickException."""
        generic_error = ValueError("Generic error message")
        converted = convert_to_click_exception(generic_error)
        
        assert isinstance(converted, click.ClickException)
        assert converted.message == "Unexpected error: Generic error message"


class TestValidationErrorHandling:
    """Test cases for validation error handling."""

    def test_handle_validation_error_without_suggestions(self):
        """Test handling validation error without suggestions."""
        with pytest.raises(click.BadParameter) as exc_info:
            handle_validation_error("test_param", "Invalid value")
        
        assert str(exc_info.value) == "Invalid value"

    def test_handle_validation_error_with_suggestions(self):
        """Test handling validation error with suggestions."""
        suggestions = ["Use --force option", "Check file permissions"]
        
        with pytest.raises(click.BadParameter) as exc_info:
            handle_validation_error("test_param", "Invalid value", suggestions)
        
        error_msg = str(exc_info.value)
        assert "Invalid value" in error_msg
        assert "Suggestions:" in error_msg
        assert "Use --force option" in error_msg
        assert "Check file permissions" in error_msg

    def test_handle_validation_error_with_empty_suggestions(self):
        """Test handling validation error with empty suggestions list."""
        with pytest.raises(click.BadParameter) as exc_info:
            handle_validation_error("test_param", "Invalid value", [])
        
        assert str(exc_info.value) == "Invalid value"