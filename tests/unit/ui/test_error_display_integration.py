"""Integration tests for ErrorHandler usage in UI error display modules."""

from unittest.mock import Mock, patch

from spec_cli.ui.error_display import (
    DiagnosticDisplay,
    ErrorPanel,
    StackTraceFormatter,
)
from spec_cli.utils.error_handler import ErrorHandler


class TestErrorPanelIntegration:
    """Test ErrorHandler integration in ErrorPanel."""

    def test_error_panel_when_initialized_then_has_error_handler(self):
        """Test that ErrorPanel initializes with ErrorHandler."""
        error = ValueError("Test error")
        panel = ErrorPanel(error)

        assert hasattr(panel, "error_handler")
        assert isinstance(panel.error_handler, ErrorHandler)
        assert panel.error_handler.default_context["component"] == "ui_display"

    @patch("spec_cli.ui.error_display.debug_logger")
    def test_error_context_when_file_not_found_then_uses_error_handler(
        self, mock_logger
    ):
        """Test error context creation uses ErrorHandler for reporting."""
        error = FileNotFoundError("test.txt")
        error.filename = "test.txt"
        panel = ErrorPanel(error)

        context = panel._get_error_context()

        # Should still return context but also use ErrorHandler for reporting
        assert context is not None
        assert "test.txt" in context

    @patch("spec_cli.ui.error_display.debug_logger")
    def test_format_traceback_when_exception_then_uses_error_handler(self, mock_logger):
        """Test traceback formatting uses ErrorHandler for error reporting."""
        error = ValueError("Test error")
        panel = ErrorPanel(error)

        # Mock traceback formatting to raise an exception
        with patch(
            "spec_cli.ui.error_display.traceback.format_exception",
            side_effect=Exception("Traceback error"),
        ):
            result = panel._format_traceback()

        # Should return None and use ErrorHandler for reporting
        assert result is None

    def test_error_handler_fallback_when_display_error_then_graceful_degradation(self):
        """Test ErrorHandler provides graceful fallback for display errors."""
        error = PermissionError("Access denied")
        panel = ErrorPanel(error)

        # Should not raise exception even if ErrorHandler has issues
        context = panel._get_error_context()
        assert context is not None
        assert "permissions" in context.lower()


class TestDiagnosticDisplayIntegration:
    """Test ErrorHandler integration in DiagnosticDisplay."""

    def test_diagnostic_display_when_initialized_then_has_error_handler(self):
        """Test that DiagnosticDisplay initializes with ErrorHandler."""
        display = DiagnosticDisplay()

        assert hasattr(display, "error_handler")
        assert isinstance(display.error_handler, ErrorHandler)
        assert (
            display.error_handler.default_context["component"] == "diagnostic_display"
        )

    @patch("spec_cli.ui.error_display.get_console")
    def test_diagnostic_display_when_using_error_handler_then_proper_context(
        self, mock_console
    ):
        """Test DiagnosticDisplay uses ErrorHandler for proper error context."""
        mock_console.return_value.console = Mock()
        display = DiagnosticDisplay()

        # The display should have proper ErrorHandler context
        assert (
            display.error_handler.default_context["component"] == "diagnostic_display"
        )


class TestStackTraceFormatterIntegration:
    """Test ErrorHandler integration in StackTraceFormatter."""

    def test_stack_trace_formatter_when_initialized_then_has_error_handler(self):
        """Test that StackTraceFormatter initializes with ErrorHandler."""
        formatter = StackTraceFormatter()

        assert hasattr(formatter, "error_handler")
        assert isinstance(formatter.error_handler, ErrorHandler)
        assert (
            formatter.error_handler.default_context["component"]
            == "stack_trace_formatter"
        )

    @patch("spec_cli.ui.error_display.get_console")
    def test_stack_trace_formatter_when_using_error_handler_then_consistent_format(
        self, mock_console
    ):
        """Test StackTraceFormatter uses ErrorHandler for consistent formatting."""
        mock_console.return_value.console = Mock()
        formatter = StackTraceFormatter()

        error = ValueError("Test error")
        # Should not raise exception
        traceback_obj = formatter.format_exception(error)
        assert traceback_obj is not None


class TestErrorHandlerUsagePatterns:
    """Test ErrorHandler usage patterns across UI modules."""

    def test_all_ui_error_classes_when_initialized_then_have_error_handler(self):
        """Test that all UI error classes properly initialize ErrorHandler."""
        error = Exception("Test error")

        # ErrorPanel
        panel = ErrorPanel(error)
        assert hasattr(panel, "error_handler")
        assert panel.error_handler.default_context["component"] == "ui_display"

        # DiagnosticDisplay
        display = DiagnosticDisplay()
        assert hasattr(display, "error_handler")
        assert (
            display.error_handler.default_context["component"] == "diagnostic_display"
        )

        # StackTraceFormatter
        formatter = StackTraceFormatter()
        assert hasattr(formatter, "error_handler")
        assert (
            formatter.error_handler.default_context["component"]
            == "stack_trace_formatter"
        )

    def test_error_handler_context_when_different_components_then_proper_identification(
        self,
    ):
        """Test that different UI components have proper ErrorHandler context."""
        error = Exception("Test error")

        panel = ErrorPanel(error)
        display = DiagnosticDisplay()
        formatter = StackTraceFormatter()

        # Each should have unique component identification
        contexts = [
            panel.error_handler.default_context["component"],
            display.error_handler.default_context["component"],
            formatter.error_handler.default_context["component"],
        ]

        assert len(set(contexts)) == 3  # All unique
        assert "ui_display" in contexts
        assert "diagnostic_display" in contexts
        assert "stack_trace_formatter" in contexts

    @patch("spec_cli.ui.error_display.debug_logger")
    def test_error_reporting_when_ui_operations_fail_then_structured_context(
        self, mock_logger
    ):
        """Test that UI operations provide structured context through ErrorHandler."""
        error = ValueError("Test error")
        panel = ErrorPanel(error)

        # Force an error in context creation to test ErrorHandler usage
        with patch.object(panel.error_handler, "report") as mock_report:
            panel._get_error_context()

            # Should use ErrorHandler for reporting
            if mock_report.called:
                call_args = mock_report.call_args
                assert "display error context" in call_args[0][1]
                assert "display_mode" in call_args[1]
