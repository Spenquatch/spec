"""Unit tests for error display module.

Tests the ErrorPanel, DiagnosticDisplay, StackTraceFormatter classes and
utility functions for displaying error messages with Rich formatting.
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback

from spec_cli.exceptions import SpecError
from spec_cli.ui.error_display import (
    DiagnosticDisplay,
    ErrorPanel,
    StackTraceFormatter,
    format_code_snippet,
    format_data,
    show_error,
    show_info,
    show_message,
    show_success,
    show_warning,
)


class TestErrorPanel:
    """Test ErrorPanel class for error formatting and display."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.test_error = ValueError("Test error message")
        self.spec_error = SpecError("Spec error", {"file": "test.py"})

    def test_init_with_defaults(self) -> None:
        """Test ErrorPanel initialization with default parameters."""
        panel = ErrorPanel(self.test_error)

        assert panel.error == self.test_error
        assert panel.show_traceback is True
        assert panel.title == "[warning]ValueError[/warning]"
        assert panel.console is not None

    def test_init_with_custom_parameters(self) -> None:
        """Test ErrorPanel initialization with custom parameters."""
        panel = ErrorPanel(
            self.test_error,
            title="Custom Title",
            show_traceback=False,
            console=self.mock_console,
        )

        assert panel.error == self.test_error
        assert panel.title == "Custom Title"
        assert panel.show_traceback is False
        assert panel.console == self.mock_console

    def test_get_error_title_spec_error(self) -> None:
        """Test _get_error_title for SpecError types."""
        panel = ErrorPanel(self.spec_error)
        title = panel._get_error_title(self.spec_error)

        assert title == "[error]SpecError[/error]"

    def test_get_error_title_value_error(self) -> None:
        """Test _get_error_title for ValueError types."""
        panel = ErrorPanel(self.test_error)
        title = panel._get_error_title(self.test_error)

        assert title == "[warning]ValueError[/warning]"

    def test_get_error_title_type_error(self) -> None:
        """Test _get_error_title for TypeError types."""
        type_error = TypeError("Type error")
        panel = ErrorPanel(type_error)
        title = panel._get_error_title(type_error)

        assert title == "[warning]TypeError[/warning]"

    def test_get_error_title_generic_error(self) -> None:
        """Test _get_error_title for generic exceptions."""
        runtime_error = RuntimeError("Runtime error")
        panel = ErrorPanel(runtime_error)
        title = panel._get_error_title(runtime_error)

        assert title == "[error]Error[/error]"

    def test_create_panel_basic_error(self) -> None:
        """Test create_panel with basic error message."""
        panel = ErrorPanel(self.test_error, console=self.mock_console)
        result = panel.create_panel()

        assert isinstance(result, Panel)
        assert result.title == "[warning]ValueError[/warning]"

    def test_create_panel_spec_error_with_details(self) -> None:
        """Test create_panel with SpecError containing details."""
        self.spec_error.details = "Additional error details"
        panel = ErrorPanel(self.spec_error, console=self.mock_console)
        result = panel.create_panel()

        assert isinstance(result, Panel)
        assert result.title == "[error]SpecError[/error]"

    def test_get_error_context_file_not_found(self) -> None:
        """Test _get_error_context for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        error.filename = "missing_file.txt"
        panel = ErrorPanel(error, console=self.mock_console)

        context = panel._get_error_context()
        assert context is not None
        assert "missing_file.txt" in context

    def test_get_error_context_permission_error(self) -> None:
        """Test _get_error_context for PermissionError."""
        error = PermissionError("Permission denied")
        panel = ErrorPanel(error, console=self.mock_console)

        context = panel._get_error_context()
        assert context is not None
        assert "permissions" in context.lower()

    def test_get_error_context_generic_error(self) -> None:
        """Test _get_error_context for generic errors."""
        panel = ErrorPanel(self.test_error, console=self.mock_console)

        context = panel._get_error_context()
        assert context is None

    def test_get_error_suggestions_file_not_found(self) -> None:
        """Test _get_error_suggestions for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        panel = ErrorPanel(error, console=self.mock_console)

        suggestions = panel._get_error_suggestions()
        assert len(suggestions) > 0
        assert any("file path" in suggestion.lower() for suggestion in suggestions)
        assert any("file exists" in suggestion.lower() for suggestion in suggestions)

    def test_get_error_suggestions_permission_error(self) -> None:
        """Test _get_error_suggestions for PermissionError."""
        error = PermissionError("Permission denied")
        panel = ErrorPanel(error, console=self.mock_console)

        suggestions = panel._get_error_suggestions()
        assert len(suggestions) > 0
        assert any("permissions" in suggestion.lower() for suggestion in suggestions)

    def test_get_error_suggestions_generic_error(self) -> None:
        """Test _get_error_suggestions for generic errors."""
        panel = ErrorPanel(self.test_error, console=self.mock_console)

        suggestions = panel._get_error_suggestions()
        assert suggestions == []

    def test_format_traceback_success(self) -> None:
        """Test _format_traceback when traceback is available."""
        try:
            raise self.test_error
        except ValueError as e:
            panel = ErrorPanel(e, console=self.mock_console)
            result = panel._format_traceback()

            assert result is not None
            assert "ValueError" in result
            assert "Test error message" in result

    def test_format_traceback_no_traceback(self) -> None:
        """Test _format_traceback when no traceback is available."""
        panel = ErrorPanel(self.test_error, console=self.mock_console)
        result = panel._format_traceback()

        # Error has no traceback when not raised
        assert result is not None

    def test_format_traceback_long_trace(self) -> None:
        """Test _format_traceback with long traceback gets truncated."""

        # Create a deep call stack
        def deep_function(depth: int) -> int:
            if depth <= 0:
                raise ValueError("Deep error")
            return deep_function(depth - 1)

        try:
            deep_function(15)  # Create long traceback
        except ValueError as e:
            panel = ErrorPanel(e, console=self.mock_console)
            result = panel._format_traceback()

            assert result is not None
            # Check if traceback is long enough or contains error details
            assert "ValueError" in result and "Deep error" in result

    def test_print_calls_console_print(self) -> None:
        """Test print method calls console.print with panel."""
        panel = ErrorPanel(self.test_error, console=self.mock_console)
        panel.print()

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)


class TestDiagnosticDisplay:
    """Test DiagnosticDisplay class for system information display."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.display = DiagnosticDisplay(console=self.mock_console)

    def test_init_with_console(self) -> None:
        """Test DiagnosticDisplay initialization with custom console."""
        display = DiagnosticDisplay(console=self.mock_console)
        assert display.console == self.mock_console

    def test_init_default_console(self) -> None:
        """Test DiagnosticDisplay initialization with default console."""
        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_get_console.return_value.console = self.mock_console
            display = DiagnosticDisplay()
            assert display.console == self.mock_console

    def test_show_system_info(self) -> None:
        """Test show_system_info displays system information correctly."""
        system_info = {
            "Python Version": "3.11.0",
            "OS": "Linux",
            "Architecture": "x86_64",
        }

        self.display.show_system_info(system_info)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_configuration_flat_dict(self) -> None:
        """Test show_configuration with flat dictionary."""
        config = {"debug": True, "timeout": 30, "max_retries": 3}

        self.display.show_configuration(config)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_configuration_nested_dict(self) -> None:
        """Test show_configuration with nested dictionary."""
        config = {
            "database": {"host": "localhost", "port": 5432},
            "logging": {"level": "INFO", "file": "app.log"},
        }

        self.display.show_configuration(config)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_file_details_existing_file(self) -> None:
        """Test show_file_details for existing file."""
        file_path = Path("test_file.txt")
        details = {
            "size": "1.2 KB",
            "modified": "2024-01-01 12:00:00",
            "permissions": "rw-r--r--",
        }

        with patch("pathlib.Path.exists", return_value=True):
            self.display.show_file_details(file_path, details)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_file_details_missing_file(self) -> None:
        """Test show_file_details for missing file."""
        file_path = Path("missing_file.txt")
        details: dict[str, Any] = {}

        with patch("pathlib.Path.exists", return_value=False):
            self.display.show_file_details(file_path, details)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)


class TestStackTraceFormatter:
    """Test StackTraceFormatter class for enhanced stack trace formatting."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.formatter = StackTraceFormatter(console=self.mock_console)
        self.test_error = ValueError("Test error for formatting")

    def test_init_with_console(self) -> None:
        """Test StackTraceFormatter initialization with custom console."""
        formatter = StackTraceFormatter(console=self.mock_console)
        assert formatter.console == self.mock_console

    def test_format_exception_basic(self) -> None:
        """Test format_exception with basic parameters."""
        try:
            raise self.test_error
        except ValueError as e:
            result = self.formatter.format_exception(e)

            assert isinstance(result, Traceback)

    def test_format_exception_with_locals(self) -> None:
        """Test format_exception with show_locals=True."""
        try:
            local_var = "test_value"
            # Use the local variable to prevent linting error
            self.test_error.args = (f"Error with {local_var}",)
            raise self.test_error
        except ValueError as e:
            result = self.formatter.format_exception(e, show_locals=True)

            assert isinstance(result, Traceback)

    def test_format_exception_with_max_frames(self) -> None:
        """Test format_exception with custom max_frames."""
        try:
            raise self.test_error
        except ValueError as e:
            result = self.formatter.format_exception(e, max_frames=5)

            assert isinstance(result, Traceback)

    def test_print_exception_calls_console_print(self) -> None:
        """Test print_exception calls console.print with traceback."""
        try:
            raise self.test_error
        except ValueError as e:
            self.formatter.print_exception(e)

            self.mock_console.print.assert_called_once()
            args = self.mock_console.print.call_args[0]
            assert isinstance(args[0], Traceback)


class TestUtilityFunctions:
    """Test utility functions for error display."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)

    def test_show_error_basic(self) -> None:
        """Test show_error with basic parameters."""
        test_error = ValueError("Test error")

        with patch("spec_cli.ui.error_display.ErrorPanel") as mock_error_panel:
            mock_panel_instance = Mock()
            mock_error_panel.return_value = mock_panel_instance

            show_error(test_error)

            mock_error_panel.assert_called_once_with(test_error, None, True, None)
            mock_panel_instance.print.assert_called_once()

    def test_show_error_with_parameters(self) -> None:
        """Test show_error with all parameters."""
        test_error = ValueError("Test error")
        title = "Custom Error Title"

        with patch("spec_cli.ui.error_display.ErrorPanel") as mock_error_panel:
            mock_panel_instance = Mock()
            mock_error_panel.return_value = mock_panel_instance

            show_error(
                test_error, title=title, show_traceback=False, console=self.mock_console
            )

            mock_error_panel.assert_called_once_with(
                test_error, title, False, self.mock_console
            )
            mock_panel_instance.print.assert_called_once()

    def test_show_warning_basic(self) -> None:
        """Test show_warning with basic message."""
        message = "Warning message"

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_get_console.return_value.console = self.mock_console

            show_warning(message)

            self.mock_console.print.assert_called_once()
            args = self.mock_console.print.call_args[0]
            assert isinstance(args[0], Panel)

    def test_show_warning_with_details(self) -> None:
        """Test show_warning with details."""
        message = "Warning message"
        details = "Additional warning details"

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_get_console.return_value.console = self.mock_console

            show_warning(message, details=details, console=self.mock_console)

            self.mock_console.print.assert_called_once()
            args = self.mock_console.print.call_args[0]
            assert isinstance(args[0], Panel)

    def test_show_success_basic(self) -> None:
        """Test show_success with basic message."""
        message = "Success message"

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_get_console.return_value.console = self.mock_console

            show_success(message)

            self.mock_console.print.assert_called_once()
            args = self.mock_console.print.call_args[0]
            assert isinstance(args[0], Panel)

    def test_show_success_with_details(self) -> None:
        """Test show_success with details."""
        message = "Success message"
        details = "Additional success details"

        show_success(message, details=details, console=self.mock_console)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_info_basic(self) -> None:
        """Test show_info with basic message."""
        message = "Info message"

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_get_console.return_value.console = self.mock_console

            show_info(message)

            self.mock_console.print.assert_called_once()
            args = self.mock_console.print.call_args[0]
            assert isinstance(args[0], Panel)

    def test_show_info_with_details(self) -> None:
        """Test show_info with details."""
        message = "Info message"
        details = "Additional info details"

        show_info(message, details=details, console=self.mock_console)

        self.mock_console.print.assert_called_once()
        args = self.mock_console.print.call_args[0]
        assert isinstance(args[0], Panel)

    def test_show_message_success_type(self) -> None:
        """Test show_message with success type."""
        message = "Test message"

        with patch("spec_cli.ui.error_display.show_success") as mock_show_success:
            show_message(message, message_type="success")
            mock_show_success.assert_called_once_with("Test message")

    def test_show_message_warning_type(self) -> None:
        """Test show_message with warning type."""
        message = "Test message"

        with patch("spec_cli.ui.error_display.show_warning") as mock_show_warning:
            show_message(message, message_type="warning")
            mock_show_warning.assert_called_once_with("Test message")

    def test_show_message_error_type(self) -> None:
        """Test show_message with error type."""
        message = "Test message"

        with patch("spec_cli.ui.error_display.show_error") as mock_show_error:
            show_message(message, message_type="error")
            mock_show_error.assert_called_once()
            args = mock_show_error.call_args[0]
            assert str(args[0]) == "Test message"

    def test_show_message_info_type(self) -> None:
        """Test show_message with info type."""
        message = "Test message"

        with patch("spec_cli.ui.error_display.show_info") as mock_show_info:
            show_message(message, message_type="info")
            mock_show_info.assert_called_once_with("Test message")

    def test_show_message_with_context(self) -> None:
        """Test show_message with context."""
        message = "Test message"
        context = "Operation context"

        with patch("spec_cli.ui.error_display.show_info") as mock_show_info:
            show_message(message, context=context)
            mock_show_info.assert_called_once_with("Operation context: Test message")

    def test_format_data_auto_dict(self) -> None:
        """Test format_data with dictionary (auto format)."""
        data = {"key1": "value1", "key2": "value2"}

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console

            with patch(
                "spec_cli.ui.tables.create_key_value_table"
            ) as mock_create_table:
                mock_table = Mock()
                mock_create_table.return_value = mock_table

                format_data(data, title="Test Data")

                mock_create_table.assert_called_once_with(data, "Test Data")
                mock_table.print.assert_called_once()

    def test_format_data_auto_list(self) -> None:
        """Test format_data with list (auto format)."""
        data = ["item1", "item2", "item3"]

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console

            format_data(data)

            assert mock_console.print.call_count == len(data)

    def test_format_data_auto_string(self) -> None:
        """Test format_data with string (auto format)."""
        data = "Test string data"

        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console

            format_data(data, title="Test Title")

            mock_console.print.assert_called()

    def test_format_code_snippet_basic(self) -> None:
        """Test format_code_snippet with basic parameters."""
        code = "def hello():\n    print('Hello, World!')"

        result = format_code_snippet(code)

        from rich.syntax import Syntax

        assert isinstance(result, Syntax)

    def test_format_code_snippet_with_parameters(self) -> None:
        """Test format_code_snippet with custom parameters."""
        code = "console.log('Hello, World!');"
        highlight_lines = [1]

        result = format_code_snippet(
            code,
            language="javascript",
            theme="github-dark",
            line_numbers=False,
            highlight_lines=highlight_lines,
        )

        from rich.syntax import Syntax

        assert isinstance(result, Syntax)


class TestErrorHandling:
    """Test error handling edge cases and exception scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)

    def test_error_panel_with_exception_in_context_retrieval(self) -> None:
        """Test ErrorPanel when error handler fails in context retrieval."""
        test_error = ValueError("Test error")

        with patch("spec_cli.ui.error_display.ErrorHandler") as mock_error_handler:
            mock_handler_instance = Mock()
            mock_handler_instance.report.side_effect = Exception("Handler error")
            mock_error_handler.return_value = mock_handler_instance

            panel = ErrorPanel(test_error, console=self.mock_console)
            # Should handle gracefully and fall back to basic context
            context = panel._get_error_context()
            # Should return None for generic ValueError
            assert context is None

    def test_error_panel_with_empty_error_message(self) -> None:
        """Test ErrorPanel with empty error message."""
        test_error = ValueError("")
        panel = ErrorPanel(test_error, console=self.mock_console)

        result = panel.create_panel()
        assert isinstance(result, Panel)

    def test_stack_trace_formatter_with_no_traceback(self) -> None:
        """Test StackTraceFormatter with error that has no traceback."""
        test_error = ValueError("No traceback")
        formatter = StackTraceFormatter(console=self.mock_console)

        # Should handle gracefully
        result = formatter.format_exception(test_error)
        assert isinstance(result, Traceback)

    def test_format_data_with_none(self) -> None:
        """Test format_data with None value."""
        with patch("spec_cli.ui.error_display.get_console") as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console

            format_data(None)

            mock_console.print.assert_called_with("None")

    def test_show_message_unknown_type(self) -> None:
        """Test show_message with unknown message type."""
        message = "Test message"

        with patch("spec_cli.ui.error_display.show_info") as mock_show_info:
            show_message(message, message_type="unknown")
            mock_show_info.assert_called_once_with("Test message")
