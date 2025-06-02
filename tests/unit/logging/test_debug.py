import os
import time
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.logging.debug import DebugLogger


class TestDebugLogger:
    """Test the DebugLogger class functionality."""

    def test_debug_logger_respects_environment_variables(self) -> None:
        """Test that DebugLogger reads environment variables correctly."""
        with patch.dict(
            os.environ,
            {"SPEC_DEBUG": "1", "SPEC_DEBUG_LEVEL": "DEBUG", "SPEC_DEBUG_TIMING": "1"},
        ):
            logger = DebugLogger()
            assert logger.enabled is True
            assert logger.level == "DEBUG"
            assert logger.timing_enabled is True

    def test_debug_logger_disabled_when_spec_debug_false(self) -> None:
        """Test that DebugLogger is disabled when SPEC_DEBUG is false."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "0"}, clear=True):
            logger = DebugLogger()
            assert logger.enabled is False

            # Should not log anything when disabled
            with patch.object(logger.logger, "info") as mock_info:
                logger.log("INFO", "Test message")
                mock_info.assert_not_called()

    def test_debug_logger_formats_structured_data(self) -> None:
        """Test that DebugLogger formats structured data correctly."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1"}):
            logger = DebugLogger()

            with patch.object(logger.logger, "info") as mock_info:
                logger.log("INFO", "Test message", file_path="test.py", line_number=42)
                mock_info.assert_called_once()

                # Check the message format
                call_args = mock_info.call_args[0][0]
                assert "Test message" in call_args
                assert "file_path=test.py" in call_args
                assert "line_number=42" in call_args

    def test_debug_logger_handles_different_log_levels(self) -> None:
        """Test that DebugLogger handles different log levels correctly."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1"}):
            logger = DebugLogger()

            # Test different log levels
            with patch.object(logger.logger, "debug") as mock_debug, patch.object(
                logger.logger, "info"
            ) as mock_info, patch.object(
                logger.logger, "warning"
            ) as mock_warning, patch.object(logger.logger, "error") as mock_error:
                logger.log("DEBUG", "Debug message")
                logger.log("INFO", "Info message")
                logger.log("WARNING", "Warning message")
                logger.log("ERROR", "Error message")

                mock_debug.assert_called_once()
                mock_info.assert_called_once()
                mock_warning.assert_called_once()
                mock_error.assert_called_once()

    def test_debug_logger_timer_measures_duration(self) -> None:
        """Test that timer context manager measures duration correctly."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1", "SPEC_DEBUG_TIMING": "1"}):
            logger = DebugLogger()

            with patch.object(logger.logger, "info") as mock_info:
                with logger.timer("test_operation"):
                    time.sleep(0.01)  # Sleep for 10ms

                # Should have called info twice (start and end)
                assert mock_info.call_count == 2

                # Check that duration was logged
                start_call = mock_info.call_args_list[0][0][0]
                end_call = mock_info.call_args_list[1][0][0]

                assert "Starting operation: test_operation" in start_call
                assert "Completed operation: test_operation" in end_call
                assert "duration_ms=" in end_call

    def test_debug_logger_timer_handles_exceptions(self) -> None:
        """Test that timer handles exceptions and logs them correctly."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1", "SPEC_DEBUG_TIMING": "1"}):
            logger = DebugLogger()

            with patch.object(logger.logger, "info") as mock_info, patch.object(
                logger.logger, "error"
            ) as mock_error:
                with pytest.raises(ValueError):
                    with logger.timer("failing_operation"):
                        raise ValueError("Test error")

                # Should have start log, error log, and completion log (finally block)
                assert mock_info.call_count == 2  # start and completion
                mock_error.assert_called_once()

                error_call = mock_error.call_args[0][0]
                assert "Operation failed: failing_operation" in error_call
                assert "duration_ms=" in error_call

    def test_debug_logger_logs_spec_error_context(self) -> None:
        """Test that DebugLogger logs SpecError context information."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1"}):
            logger = DebugLogger()

            # Create SpecError with context
            error = SpecGitError(
                "Git operation failed", {"repo": ".spec", "command": "git add"}
            )

            with patch.object(logger.logger, "error") as mock_error:
                logger.log_error(error)

                mock_error.assert_called_once()
                call_args = mock_error.call_args[0][0]

                assert "Exception occurred: Git operation failed" in call_args
                assert "error_type=SpecGitError" in call_args
                assert "repo=.spec" in call_args
                assert "command=git add" in call_args

    def test_debug_logger_logs_function_calls_with_args(self) -> None:
        """Test that DebugLogger logs function calls with arguments."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1", "SPEC_DEBUG_LEVEL": "DEBUG"}):
            logger = DebugLogger()

            with patch.object(logger.logger, "debug") as mock_debug:
                # Test with args and kwargs
                logger.log_function_call(
                    "test_function",
                    args=("arg1", "arg2"),
                    kwargs={"key1": "value1", "key2": "value2"},
                )

                mock_debug.assert_called_once()
                call_args = mock_debug.call_args[0][0]

                assert "Function call: test_function" in call_args
                assert "function=test_function" in call_args
                assert "args_count=2" in call_args
                assert "kwargs_keys=['key1', 'key2']" in call_args

    def test_debug_logger_timer_disabled_when_timing_disabled(self) -> None:
        """Test that timer is disabled when SPEC_DEBUG_TIMING is not set."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1"}, clear=True):
            logger = DebugLogger()
            assert logger.timing_enabled is False

            with patch.object(logger.logger, "info") as mock_info:
                with logger.timer("test_operation"):
                    pass

                # Should not log anything when timing is disabled
                mock_info.assert_not_called()

    def test_debug_logger_log_error_with_additional_context(self) -> None:
        """Test that log_error accepts additional context."""
        with patch.dict(os.environ, {"SPEC_DEBUG": "1"}):
            logger = DebugLogger()

            error = ValueError("Standard error")
            additional_context = {"operation": "file_read", "path": "/tmp/test.txt"}

            with patch.object(logger.logger, "error") as mock_error:
                logger.log_error(error, context=additional_context)

                call_args = mock_error.call_args[0][0]
                assert "operation=file_read" in call_args
                assert "path=/tmp/test.txt" in call_args
                assert "error_type=ValueError" in call_args
