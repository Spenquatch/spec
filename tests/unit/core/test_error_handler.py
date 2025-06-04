"""Tests for ErrorHandler class."""

import errno
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.core.error_handler import ErrorHandler, default_error_handler
from spec_cli.exceptions import SpecError, SpecFileError


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_error_handler_when_wrap_function_then_catches_exceptions(self):
        """Test that wrap decorator catches and reports exceptions."""
        # Create mock logger to capture calls
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler()

            @handler.wrap
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            # Verify error was reported
            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "ERROR"
            assert "Error in execute failing_function" in call_args[0][1]

    def test_error_handler_when_wrap_successful_function_then_returns_result(self):
        """Test that wrap decorator doesn't interfere with successful execution."""
        handler = ErrorHandler()

        @handler.wrap
        def successful_function(x: int, y: int) -> int:
            return x + y

        result = successful_function(3, 4)
        assert result == 7

    def test_error_handler_when_wrap_function_then_preserves_metadata(self):
        """Test that wrap decorator preserves function metadata."""
        handler = ErrorHandler()

        @handler.wrap
        def test_function():
            """Test docstring."""
            pass

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    def test_error_handler_when_report_called_then_logs_with_context(self):
        """Test that report method logs errors with context."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler({"default_key": "default_value"})
            exc = ValueError("Test error")

            handler.report(exc, "test operation", custom_key="custom_value", number=42)

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args

            # Check log level and message
            assert call_args[0][0] == "ERROR"
            assert "Error in test operation: Test error" in call_args[0][1]

            # Check context was included
            kwargs = call_args[1]
            assert kwargs["default_key"] == "default_value"
            assert kwargs["custom_key"] == "custom_value"
            assert kwargs["number"] == 42
            assert kwargs["operation"] == "test operation"
            assert kwargs["error_type"] == "generic_error"

    def test_error_handler_when_os_error_then_uses_handle_os_error(self):
        """Test that OSError uses handle_os_error utility."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            with patch(
                "spec_cli.core.error_handler.handle_os_error"
            ) as mock_handle_os_error:
                mock_handle_os_error.return_value = "Formatted OS error"

                handler = ErrorHandler()
                exc = OSError(errno.ENOENT, "No such file")

                handler.report(exc, "file operation")

                # Verify handle_os_error was called
                mock_handle_os_error.assert_called_once_with(exc)

                # Verify log message includes formatted error
                call_args = mock_logger.log.call_args
                assert "Formatted OS error" in call_args[0][1]
                assert call_args[1]["error_type"] == "os_error"

    def test_error_handler_when_subprocess_error_then_uses_handle_subprocess_error(
        self,
    ):
        """Test that SubprocessError uses handle_subprocess_error utility."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            with patch(
                "spec_cli.core.error_handler.handle_subprocess_error"
            ) as mock_handle_subprocess_error:
                mock_handle_subprocess_error.return_value = "Formatted subprocess error"

                handler = ErrorHandler()
                exc = subprocess.CalledProcessError(1, ["cmd"])

                handler.report(exc, "subprocess operation")

                # Verify handle_subprocess_error was called
                mock_handle_subprocess_error.assert_called_once_with(exc)

                # Verify log message includes formatted error
                call_args = mock_logger.log.call_args
                assert "Formatted subprocess error" in call_args[0][1]
                assert call_args[1]["error_type"] == "subprocess_error"

    def test_error_handler_when_spec_error_then_uses_spec_error_context(self):
        """Test that SpecError uses its own context and user message."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler()
            exc = SpecError("Test spec error", {"spec_key": "spec_value"})

            handler.report(exc, "spec operation")

            call_args = mock_logger.log.call_args

            # Check that SpecError's user message is used
            assert "Test spec error" in call_args[0][1]
            assert call_args[1]["error_type"] == "spec_error"

            # Check that SpecError's context is included
            assert call_args[1]["spec_key"] == "spec_value"

    def test_error_handler_when_code_path_provided_then_includes_path_context(self):
        """Test that code_path parameter adds path context."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            with patch(
                "spec_cli.core.error_handler.create_error_context"
            ) as mock_create_context:
                mock_create_context.return_value = {
                    "file_path": "/test/path",
                    "file_exists": True,
                }

                handler = ErrorHandler()
                exc = ValueError("Test error")
                test_path = Path("/test/path")

                handler.report(exc, "path operation", code_path=test_path)

                # Verify create_error_context was called
                mock_create_context.assert_called_once_with(test_path)

                # Verify path context was included
                call_args = mock_logger.log.call_args
                kwargs = call_args[1]
                assert kwargs["file_path"] == "/test/path"
                assert kwargs["file_exists"] is True

    def test_error_handler_when_path_context_fails_then_continues_gracefully(self):
        """Test that errors in path context creation don't break error reporting."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            with patch(
                "spec_cli.core.error_handler.create_error_context"
            ) as mock_create_context:
                mock_create_context.side_effect = Exception("Context creation failed")

                handler = ErrorHandler()
                exc = ValueError("Test error")
                test_path = Path("/test/path")

                handler.report(exc, "path operation", code_path=test_path)

                # Verify error reporting continued
                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args
                kwargs = call_args[1]

                # Should have fallback path context
                assert kwargs["path_context_error"] == "/test/path"

    def test_error_handler_when_log_and_raise_with_reraise_then_converts_exception(
        self,
    ):
        """Test log_and_raise with reraise_as parameter."""
        with patch("spec_cli.core.error_handler.debug_logger"):
            handler = ErrorHandler()
            exc = OSError(errno.ENOENT, "No such file")

            with pytest.raises(SpecFileError) as exc_info:
                handler.log_and_raise(exc, "file operation", reraise_as=SpecFileError)

            # Check that original exception is preserved as cause
            assert exc_info.value.__cause__ is exc
            assert "Failed to file operation" in str(exc_info.value)

    def test_error_handler_when_log_and_raise_without_reraise_then_preserves_exception(
        self,
    ):
        """Test log_and_raise without reraise_as preserves original exception."""
        with patch("spec_cli.core.error_handler.debug_logger"):
            handler = ErrorHandler()
            exc = ValueError("Original error")

            with pytest.raises(ValueError, match="Original error"):
                handler.log_and_raise(exc, "test operation")

    def test_error_handler_when_initialized_with_default_context_then_includes_in_reports(
        self,
    ):
        """Test that default context is included in all error reports."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            default_context = {"module": "test_module", "version": "1.0"}
            handler = ErrorHandler(default_context)

            exc = ValueError("Test error")
            handler.report(exc, "test operation")

            call_args = mock_logger.log.call_args
            kwargs = call_args[1]
            assert kwargs["module"] == "test_module"
            assert kwargs["version"] == "1.0"

    def test_error_handler_when_additional_context_overlaps_default_then_overrides(
        self,
    ):
        """Test that additional context overrides default context."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            default_context = {"key": "default_value", "static": "unchanged"}
            handler = ErrorHandler(default_context)

            exc = ValueError("Test error")
            handler.report(exc, "test operation", key="override_value")

            call_args = mock_logger.log.call_args
            kwargs = call_args[1]
            assert kwargs["key"] == "override_value"  # Overridden
            assert kwargs["static"] == "unchanged"  # Preserved


class TestDefaultErrorHandler:
    """Test default error handler instance."""

    def test_default_error_handler_when_accessed_then_is_error_handler_instance(self):
        """Test that default_error_handler is an ErrorHandler instance."""
        assert isinstance(default_error_handler, ErrorHandler)

    def test_default_error_handler_when_used_then_works_correctly(self):
        """Test that default error handler works correctly."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            exc = ValueError("Test error")
            default_error_handler.report(exc, "test operation")

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "ERROR"
            assert "Test error" in call_args[0][1]


class TestErrorHandlerIntegration:
    """Integration tests for ErrorHandler with real scenarios."""

    def test_error_handler_when_real_os_error_then_formats_correctly(self):
        """Test ErrorHandler with real OSError."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler()

            try:
                # Try to open a file that doesn't exist
                with open("/nonexistent/file"):
                    pass
            except OSError as e:
                handler.report(e, "file read operation")

            # Verify the error was logged with proper formatting
            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "ERROR"
            assert "file read operation" in call_args[0][1]
            assert call_args[1]["error_type"] == "os_error"

    def test_error_handler_when_real_subprocess_error_then_formats_correctly(self):
        """Test ErrorHandler with real subprocess error."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler()

            try:
                # Try to run a command that should fail
                subprocess.run(["false"], check=True)
            except subprocess.CalledProcessError as e:
                handler.report(e, "subprocess execution")

            # Verify the error was logged with proper formatting
            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == "ERROR"
            assert "subprocess execution" in call_args[0][1]
            assert call_args[1]["error_type"] == "subprocess_error"

    def test_error_handler_when_wrapped_function_with_args_then_includes_args_in_context(
        self,
    ):
        """Test that wrapped function arguments are included in context."""
        with patch("spec_cli.core.error_handler.debug_logger") as mock_logger:
            handler = ErrorHandler()

            @handler.wrap
            def function_with_args(arg1: str, arg2: int, kwarg1: str = "default"):
                raise ValueError("Function failed")

            with pytest.raises(ValueError):
                function_with_args("test", 42, kwarg1="custom")

            call_args = mock_logger.log.call_args
            kwargs = call_args[1]
            assert kwargs["args"] == ("test", 42)
            assert kwargs["kwargs"] == {"kwarg1": "custom"}
