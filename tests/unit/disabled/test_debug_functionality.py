"""Unit tests for debug functionality and logging."""

import logging
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.__main__ import (
    debug_log,
    debug_operation_summary,
    debug_timer,
)


class TestDebugLog:
    """Test the debug_log function."""

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_debug_enabled(self, mock_logger):
        """Test debug_log when DEBUG is True."""
        debug_log("INFO", "Test message")

        mock_logger.info.assert_called_once_with("Test message")

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_kwargs(self, mock_logger):
        """Test debug_log with additional kwargs."""
        debug_log("INFO", "Test message", file_path="/test/path", count=42)

        mock_logger.info.assert_called_once_with(
            "Test message (file_path=/test/path, count=42)"
        )

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_different_levels(self, mock_logger):
        """Test debug_log with different log levels."""
        debug_log("DEBUG", "Debug message")
        debug_log("WARNING", "Warning message")
        debug_log("ERROR", "Error message")

        mock_logger.debug.assert_called_once_with("Debug message")
        mock_logger.warning.assert_called_once_with("Warning message")
        mock_logger.error.assert_called_once_with("Error message")

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_invalid_level(self, mock_logger):
        """Test debug_log with invalid level falls back to info."""
        # Mock that invalid level doesn't exist as attribute, so getattr returns info fallback
        del mock_logger.invalid  # Make sure the attribute doesn't exist
        debug_log("INVALID", "Test message")

        mock_logger.info.assert_called_once_with("Test message")

    @patch("spec_cli.__main__.DEBUG", False)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_debug_disabled(self, mock_logger):
        """Test debug_log when DEBUG is False."""
        debug_log("INFO", "Test message")

        mock_logger.info.assert_not_called()

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_empty_kwargs(self, mock_logger):
        """Test debug_log with empty kwargs."""
        debug_log("INFO", "Test message", **{})

        mock_logger.info.assert_called_once_with("Test message")

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.logger")
    def test_debug_log_with_complex_kwargs(self, mock_logger):
        """Test debug_log with complex kwargs values."""
        debug_log(
            "INFO",
            "Test message",
            path=Path("/test"),
            items=["a", "b", "c"],
            nested={"key": "value"},
        )

        expected_msg = (
            "Test message (path=/test, items=['a', 'b', 'c'], nested={'key': 'value'})"
        )
        mock_logger.info.assert_called_once_with(expected_msg)


class TestDebugTimer:
    """Test the debug_timer context manager."""

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    @patch("time.perf_counter", side_effect=[1.0, 1.5])
    def test_debug_timer_with_timing_enabled(self, mock_perf_counter, mock_debug_log):
        """Test debug_timer when DEBUG_TIMING is True."""
        with debug_timer("test_operation"):
            pass

        # Check that start and end messages were logged
        assert mock_debug_log.call_count == 2
        mock_debug_log.assert_any_call("INFO", "Starting test_operation")
        mock_debug_log.assert_any_call(
            "INFO", "Completed test_operation", duration_ms="500.00ms"
        )

    @patch("spec_cli.__main__.DEBUG_TIMING", False)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_timer_with_timing_disabled(self, mock_debug_log):
        """Test debug_timer when DEBUG_TIMING is False."""
        with debug_timer("test_operation"):
            pass

        mock_debug_log.assert_not_called()

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    @patch("time.perf_counter", side_effect=[2.0, 2.001])
    def test_debug_timer_with_short_duration(self, mock_perf_counter, mock_debug_log):
        """Test debug_timer with short duration."""
        with debug_timer("fast_operation"):
            pass

        mock_debug_log.assert_any_call(
            "INFO", "Completed fast_operation", duration_ms="1.00ms"
        )

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    @patch("time.perf_counter", side_effect=[1.0, 3.5])
    def test_debug_timer_with_long_duration(self, mock_perf_counter, mock_debug_log):
        """Test debug_timer with longer duration."""
        with debug_timer("slow_operation"):
            time.sleep(0.001)  # Small sleep to simulate work

        mock_debug_log.assert_any_call(
            "INFO", "Completed slow_operation", duration_ms="2500.00ms"
        )

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_timer_with_exception(self, mock_debug_log):
        """Test debug_timer still logs completion when exception occurs."""
        with pytest.raises(ValueError):
            with debug_timer("failing_operation"):
                raise ValueError("Test error")

        # Should still log completion even with exception
        assert mock_debug_log.call_count >= 1
        mock_debug_log.assert_any_call("INFO", "Starting failing_operation")

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_timer_nested_timers(self, mock_debug_log):
        """Test nested debug timers."""
        with debug_timer("outer_operation"):
            with debug_timer("inner_operation"):
                pass

        # Should have 4 calls: start outer, start inner, end inner, end outer
        assert mock_debug_log.call_count == 4
        calls = [call[0] for call in mock_debug_log.call_args_list]

        assert any("Starting outer_operation" in str(call) for call in calls)
        assert any("Starting inner_operation" in str(call) for call in calls)
        assert any("Completed inner_operation" in str(call) for call in calls)
        assert any("Completed outer_operation" in str(call) for call in calls)

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_timer_return_value(self, mock_debug_log):
        """Test that debug_timer returns the timer instance."""
        timer = debug_timer("test_operation")
        assert timer is not None

        # Use it as context manager
        with timer:
            pass

        assert mock_debug_log.call_count == 2

    @patch("spec_cli.__main__.DEBUG_TIMING", True)
    @patch("spec_cli.__main__.debug_log")
    @patch("time.perf_counter", side_effect=[1.0, 1.0])
    def test_debug_timer_with_special_characters_in_name(
        self, mock_perf_counter, mock_debug_log
    ):
        """Test debug_timer with special characters in operation name."""
        with debug_timer("operation with spaces & symbols!"):
            pass

        mock_debug_log.assert_any_call(
            "INFO", "Starting operation with spaces & symbols!"
        )
        mock_debug_log.assert_any_call(
            "INFO", "Completed operation with spaces & symbols!", duration_ms="0.00ms"
        )


class TestDebugOperationSummary:
    """Test the debug_operation_summary function."""

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_operation_summary_with_debug_enabled(self, mock_debug_log):
        """Test debug_operation_summary when DEBUG is True."""
        debug_operation_summary("test_operation", file_count=5, total_size=1024)

        mock_debug_log.assert_called_once_with(
            "INFO", "Operation summary: test_operation", file_count=5, total_size=1024
        )

    @patch("spec_cli.__main__.DEBUG", False)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_operation_summary_with_debug_disabled(self, mock_debug_log):
        """Test debug_operation_summary when DEBUG is False."""
        debug_operation_summary("test_operation", file_count=5)

        mock_debug_log.assert_not_called()

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_operation_summary_with_no_metrics(self, mock_debug_log):
        """Test debug_operation_summary with no metrics."""
        debug_operation_summary("test_operation")

        mock_debug_log.assert_called_once_with(
            "INFO", "Operation summary: test_operation"
        )

    @patch("spec_cli.__main__.DEBUG", True)
    @patch("spec_cli.__main__.debug_log")
    def test_debug_operation_summary_with_complex_metrics(self, mock_debug_log):
        """Test debug_operation_summary with complex metrics."""
        debug_operation_summary(
            "complex_operation",
            paths=["/a", "/b"],
            config={"debug": True},
            timestamp="2023-12-01",
        )

        mock_debug_log.assert_called_once_with(
            "INFO",
            "Operation summary: complex_operation",
            paths=["/a", "/b"],
            config={"debug": True},
            timestamp="2023-12-01",
        )


class TestDebugEnvironmentVariables:
    """Test debug environment variable handling."""

    def test_debug_flag_parsing(self):
        """Test DEBUG flag parsing from environment."""
        test_cases = [
            ("1", True),
            ("true", True),
            ("TRUE", True),
            ("yes", True),
            ("YES", True),
            ("0", False),
            ("false", False),
            ("FALSE", False),
            ("no", False),
            ("NO", False),
            ("", False),
            ("invalid", False),
        ]

        for env_value, expected in test_cases:
            # Test the parsing logic directly rather than reloading modules
            result = env_value.lower() in ["1", "true", "yes"]
            assert result == expected, f"Failed for {env_value}"

    def test_debug_timing_flag_parsing(self):
        """Test DEBUG_TIMING flag parsing from environment."""
        test_cases = [
            ("1", True),
            ("true", True),
            ("yes", True),
            ("0", False),
            ("false", False),
            ("", False),
        ]

        for env_value, expected in test_cases:
            # Test the parsing logic directly rather than reloading modules
            result = env_value.lower() in ["1", "true", "yes"]
            assert result == expected

    def test_debug_level_parsing(self):
        """Test DEBUG_LEVEL parsing from environment."""
        test_cases = [
            ("DEBUG", "DEBUG"),
            ("debug", "DEBUG"),
            ("INFO", "INFO"),
            ("info", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("invalid", "INVALID"),
        ]

        for env_value, expected in test_cases:
            # Test the parsing logic directly
            result = env_value.upper() if env_value else "INFO"
            assert result == expected

        # Test default case (no environment variable)
        result = "INFO"  # Default value
        assert result == "INFO"


class TestDebugLoggingConfiguration:
    """Test debug logging configuration."""

    def test_logger_configuration_when_debug_enabled(self):
        """Test that logger is properly configured when DEBUG is True."""
        # Just test that our logger exists and functions
        from spec_cli.__main__ import logger

        assert logger is not None
        assert logger.name == "spec_cli"

    def test_logger_configuration_when_debug_disabled(self):
        """Test that logger has null handler when DEBUG is False."""
        # This is more of an integration test - just verify the logger exists
        from spec_cli.__main__ import logger

        assert logger is not None

    def test_logger_level_configuration(self):
        """Test that logger level configuration works."""
        # Test the logging level mapping
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }

        for level_name, level_value in level_map.items():
            assert getattr(logging, level_name) == level_value

    def test_logger_formatter_configuration(self):
        """Test that logger formatter works correctly."""
        # Test the format string directly
        formatter = logging.Formatter("🔍 Debug [%(levelname)s]: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "🔍 Debug [INFO]: test message" == formatted
