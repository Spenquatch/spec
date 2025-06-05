"""Tests for Slice 1c: Error Message Sanitization.

Tests the sanitize_error_message function and its integration with error_handler.
"""

import subprocess
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecError
from spec_cli.utils.error_handler import ErrorHandler
from spec_cli.utils.security_validators import sanitize_error_message


class TestSanitizeErrorMessage:
    """Test the sanitize_error_message function."""

    def test_sanitize_error_message_when_valid_string_then_returns_string(self):
        """Test basic functionality with clean error message."""
        result = sanitize_error_message("Simple error message")
        assert result == "Simple error message"
        assert isinstance(result, str)

    def test_sanitize_error_message_when_invalid_type_then_raises_type_error(self):
        """Test type validation for error_message parameter."""
        with pytest.raises(TypeError, match="error_message must be str"):
            sanitize_error_message(123)  # type: ignore

        with pytest.raises(TypeError, match="error_message must be str"):
            sanitize_error_message(None)  # type: ignore

    def test_sanitize_error_message_when_absolute_paths_then_sanitizes_paths(self):
        """Test sanitization of absolute Unix paths."""
        message = "fatal: repository '/Users/secret/project/.git' does not exist"
        result = sanitize_error_message(message)
        # Should sanitize the home directory and the .git part
        assert "/Users/secret/project/.git" not in result
        assert "fatal: repository" in result
        assert "does not exist" in result

    def test_sanitize_error_message_when_windows_paths_then_sanitizes_paths(self):
        """Test sanitization of Windows absolute paths."""
        message = "error: cannot access 'C:\\Users\\secret\\project\\file.txt'"
        result = sanitize_error_message(message)
        assert result == "error: cannot access '<path>'"

    def test_sanitize_error_message_when_home_paths_then_sanitizes_home(self):
        """Test sanitization of home directory paths."""
        test_cases = [
            ("error in ~/secret/project", "error in <home>/<path>"),
            ("failed /Users/username/file", "failed <home>/file"),
            ("issue /home/user/project", "issue <home>/project"),
        ]
        for input_msg, expected in test_cases:
            result = sanitize_error_message(input_msg)
            assert result == expected

    def test_sanitize_error_message_when_sensitive_args_with_context_then_filters(self):
        """Test sanitization of sensitive command arguments."""
        message = "git clone --password=secret123 --token abc456 repo.git"
        result = sanitize_error_message(message, command_context="git")
        assert "--password=secret123" not in result
        assert "--token abc456" not in result
        assert "<filtered>" in result

    def test_sanitize_error_message_when_credentials_then_sanitizes_tokens(self):
        """Test sanitization of credential-like strings."""
        message = "API key abcdef1234567890abcdef1234567890 invalid"
        result = sanitize_error_message(message)
        assert "abcdef1234567890abcdef1234567890" not in result
        assert "<token>" in result

    def test_sanitize_error_message_when_base64_strings_then_sanitizes_encoded(self):
        """Test sanitization of base64-encoded strings."""
        message = "Token dGVzdEBleGFtcGxlLmNvbTpwYXNzd29yZA== expired"
        result = sanitize_error_message(message)
        assert "dGVzdEBleGFtcGxlLmNvbTpwYXNzd29yZA==" not in result
        assert "<encoded>" in result

    def test_sanitize_error_message_when_env_vars_then_sanitizes_variables(self):
        """Test sanitization of environment variable references."""
        test_cases = [
            ("error with ${SECRET_KEY} value", "error with <env_var> value"),
            ("command $(cat /secret) failed", "command <command> failed"),
        ]
        for input_msg, expected in test_cases:
            result = sanitize_error_message(input_msg)
            assert result == expected

    def test_sanitize_error_message_when_no_context_then_skips_command_filtering(self):
        """Test that command filtering only applies with context."""
        message = "git clone --password=secret123 repo.git"
        result = sanitize_error_message(message)  # No command_context
        # Should not filter command args without context
        assert "--password=secret123" in result

    def test_sanitize_error_message_when_multiple_patterns_then_sanitizes_all(self):
        """Test comprehensive sanitization with multiple sensitive patterns."""
        message = (
            "fatal: could not access /Users/dev/project/.git "
            "with token abcdef1234567890abcdef1234567890 "
            "and env ${SECRET_PATH}/config"
        )
        result = sanitize_error_message(message)

        # Check all patterns are sanitized
        assert "/Users/dev/project/.git" not in result
        assert "abcdef1234567890abcdef1234567890" not in result
        assert "${SECRET_PATH}" not in result
        assert "<path>" in result
        assert "<token>" in result
        assert "<env_var>" in result

    def test_sanitize_error_message_when_empty_string_then_returns_empty(self):
        """Test edge case with empty error message."""
        result = sanitize_error_message("")
        assert result == ""

    def test_sanitize_error_message_when_only_whitespace_then_preserves_whitespace(
        self,
    ):
        """Test edge case with whitespace-only message."""
        result = sanitize_error_message("   \n\t  ")
        assert result == "   \n\t  "


class TestErrorHandlerSanitizationIntegration:
    """Test sanitization integration with ErrorHandler."""

    @pytest.fixture
    def mock_debug_logger(self):
        """Mock debug logger to capture log calls."""
        with patch("spec_cli.utils.error_handler.debug_logger") as mock:
            yield mock

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance for testing."""
        return ErrorHandler()

    def test_error_handler_report_when_subprocess_error_then_sanitizes_log(
        self, error_handler, mock_debug_logger
    ):
        """Test that subprocess errors are sanitized in log output."""
        # Create a subprocess error with sensitive information
        exc = subprocess.CalledProcessError(
            1, ["git", "clone"], stderr="fatal: '/Users/secret/repo/.git' not found"
        )

        error_handler.report(exc, "git operation")

        # Verify log was called with sanitized message
        mock_debug_logger.log.assert_called_once()
        call_args = mock_debug_logger.log.call_args

        # Check that logged message is sanitized
        logged_message = call_args[0][1]  # Second positional arg is message
        assert "/Users/secret/repo/.git" not in logged_message
        assert "<path>" in logged_message

        # Check that original message is preserved in context
        logged_kwargs = call_args[1]  # Keyword arguments
        assert "original_message" in logged_kwargs
        assert "/Users/secret/repo/.git" in logged_kwargs["original_message"]

    def test_error_handler_report_when_os_error_then_sanitizes_paths(
        self, error_handler, mock_debug_logger
    ):
        """Test that OS errors with paths are sanitized."""
        exc = FileNotFoundError("No such file or directory: '/Users/secret/file.txt'")

        error_handler.report(exc, "file operation")

        mock_debug_logger.log.assert_called_once()
        call_args = mock_debug_logger.log.call_args
        logged_message = call_args[0][1]

        # Verify path sanitization
        assert "/Users/secret/file.txt" not in logged_message
        # Should contain sanitized form (home or path placeholder)
        assert any(
            placeholder in logged_message for placeholder in ["<home>", "<path>"]
        )

    def test_error_handler_report_when_command_context_then_filters_args(
        self, error_handler, mock_debug_logger
    ):
        """Test command argument filtering with context."""
        exc = subprocess.CalledProcessError(
            1, ["git", "push"], stderr="failed: --token=secret123 invalid"
        )

        error_handler.report(exc, "git push", command_context="git")

        mock_debug_logger.log.assert_called_once()
        call_args = mock_debug_logger.log.call_args
        logged_message = call_args[0][1]

        # Verify sensitive args are filtered
        assert "--token=secret123" not in logged_message
        assert "<filtered>" in logged_message

    def test_error_handler_log_and_raise_when_reraise_then_sanitizes_exception(
        self, error_handler
    ):
        """Test that re-raised exceptions have sanitized messages."""
        original_exc = OSError("Permission denied: /Users/secret/protected.txt")

        with pytest.raises(SpecError) as exc_info:
            error_handler.log_and_raise(
                original_exc, "file access", reraise_as=SpecError
            )

        # Verify raised exception has sanitized message
        raised_message = str(exc_info.value)
        assert "/Users/secret/protected.txt" not in raised_message
        # Should contain sanitized form (home or path placeholder)
        assert any(
            placeholder in raised_message for placeholder in ["<home>", "<path>"]
        )

    def test_error_handler_log_and_raise_when_command_context_then_sanitizes_args(
        self, error_handler
    ):
        """Test re-raised exceptions sanitize command arguments."""
        original_exc = subprocess.CalledProcessError(
            1, ["cmd"], stderr="error with --password=secret"
        )

        with pytest.raises(SpecError) as exc_info:
            error_handler.log_and_raise(
                original_exc,
                "command execution",
                reraise_as=SpecError,
                command_context="cmd",
            )

        raised_message = str(exc_info.value)
        assert "--password=secret" not in raised_message
        assert "<filtered>" in raised_message

    def test_error_handler_log_and_raise_when_no_reraise_then_preserves_original(
        self, error_handler, mock_debug_logger
    ):
        """Test that original exception is preserved when not re-raising."""
        original_exc = OSError("Permission denied: /Users/secret/file.txt")

        with pytest.raises(OSError) as exc_info:
            error_handler.log_and_raise(original_exc, "file operation")

        # Should be the exact same exception object
        assert exc_info.value is original_exc


class TestSlice1cIntegration:
    """Integration tests for error message sanitization."""

    def test_git_error_sanitization_integration(self):
        """Test end-to-end error sanitization with git-like errors."""
        error_handler = ErrorHandler()

        # Simulate git command failure with sensitive path
        test_cases = [
            {
                "error": subprocess.CalledProcessError(
                    128,
                    ["git", "status"],
                    stderr="fatal: not a git repository: /Users/developer/secret-project/.git",
                ),
                "operation": "git status check",
                "should_not_contain": ["/Users/developer/secret-project/.git"],
                "should_contain": ["<home>", "<path>"],
            },
            {
                "error": FileNotFoundError(
                    "No such file or directory: '/home/user/private/config.json'"
                ),
                "operation": "config file access",
                "should_not_contain": ["/home/user/private/config.json"],
                "should_contain": ["<home>", "<path>"],
            },
        ]

        with patch("spec_cli.utils.error_handler.debug_logger") as mock_logger:
            for case in test_cases:
                mock_logger.reset_mock()

                error_handler.report(case["error"], case["operation"])

                # Verify log call
                assert mock_logger.log.called
                call_args = mock_logger.log.call_args
                logged_message = call_args[0][1]

                # Check sanitization worked
                for sensitive in case["should_not_contain"]:
                    assert sensitive not in logged_message, (
                        f"Sensitive data '{sensitive}' found in: {logged_message}"
                    )

                # Check that at least one of the expected placeholders is present
                assert any(
                    expected in logged_message for expected in case["should_contain"]
                ), (
                    f"None of expected placeholders {case['should_contain']} found in: {logged_message}"
                )

    def test_error_sanitization_preserves_actionable_information(self):
        """Test that sanitization preserves useful debugging information."""
        test_cases = [
            {
                "input": "fatal: repository '/Users/dev/project/.git' does not exist",
                "expected_preserved": ["fatal", "repository", "does not exist"],
                "expected_removed": ["/Users/dev/project/.git"],
            },
            {
                "input": "Permission denied (errno 13): /home/user/file.txt",
                "expected_preserved": ["Permission denied", "errno 13"],
                "expected_removed": ["/home/user/file.txt"],
            },
        ]

        for case in test_cases:
            result = sanitize_error_message(case["input"])

            # Check preserved information
            for preserved in case["expected_preserved"]:
                assert preserved in result, (
                    f"Expected '{preserved}' to be preserved in: {result}"
                )

            # Check removed information
            for removed in case["expected_removed"]:
                assert removed not in result, (
                    f"Expected '{removed}' to be removed from: {result}"
                )

    def test_sanitization_is_idempotent(self):
        """Test that sanitization produces consistent results on repeated calls."""
        test_messages = [
            "fatal: '/Users/secret/project/.git' not found",
            "error with token abcdef1234567890abcdef1234567890",
            "failed to access ${SECRET_PATH}/config",
        ]

        for message in test_messages:
            first_result = sanitize_error_message(message)
            second_result = sanitize_error_message(first_result)
            third_result = sanitize_error_message(second_result)

            assert first_result == second_result == third_result, (
                f"Sanitization not idempotent for: {message}"
            )
