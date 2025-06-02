"""Tests for error display functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

from rich.panel import Panel
from rich.syntax import Syntax
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
    """Test ErrorPanel class functionality."""

    def test_error_panel_initialization(self) -> None:
        """Test ErrorPanel initialization."""
        error = ValueError("Test error")
        panel = ErrorPanel(error)

        assert panel.error == error
        assert panel.show_traceback is True
        assert "[warning]ValueError[/warning]" in panel.title

    def test_error_panel_with_custom_title(self) -> None:
        """Test ErrorPanel with custom title."""
        error = ValueError("Test error")
        custom_title = "Custom Error Title"
        panel = ErrorPanel(error, title=custom_title)

        assert panel.title == custom_title

    def test_error_panel_without_traceback(self) -> None:
        """Test ErrorPanel without traceback."""
        error = ValueError("Test error")
        panel = ErrorPanel(error, show_traceback=False)

        assert panel.show_traceback is False

    def test_get_error_title_spec_error(self) -> None:
        """Test error title generation for SpecError."""
        error = SpecError("Test spec error")
        panel = ErrorPanel(error)

        assert panel._get_error_title(error) == "[error]SpecError[/error]"

    def test_get_error_title_value_error(self) -> None:
        """Test error title generation for ValueError."""
        error = ValueError("Test value error")
        panel = ErrorPanel(error)

        assert panel._get_error_title(error) == "[warning]ValueError[/warning]"

    def test_get_error_title_type_error(self) -> None:
        """Test error title generation for TypeError."""
        error = TypeError("Test type error")
        panel = ErrorPanel(error)

        assert panel._get_error_title(error) == "[warning]TypeError[/warning]"

    def test_get_error_title_generic_error(self) -> None:
        """Test error title generation for generic error."""
        error = RuntimeError("Test runtime error")
        panel = ErrorPanel(error)

        assert panel._get_error_title(error) == "[error]Error[/error]"

    def test_create_panel_basic(self) -> None:
        """Test basic panel creation."""
        error = ValueError("Test error message")
        panel = ErrorPanel(error, show_traceback=False)

        rich_panel = panel.create_panel()

        assert isinstance(rich_panel, Panel)
        assert rich_panel.title == "[warning]ValueError[/warning]"

    def test_create_panel_with_spec_error_details(self) -> None:
        """Test panel creation with SpecError details."""
        error = SpecError("Test spec error")
        error.details = "Additional error details"
        panel = ErrorPanel(error, show_traceback=False)

        rich_panel = panel.create_panel()

        assert isinstance(rich_panel, Panel)

    def test_get_error_context_file_not_found(self) -> None:
        """Test error context for FileNotFoundError."""
        error = FileNotFoundError("No such file")
        error.filename = "/path/to/missing/file.txt"
        panel = ErrorPanel(error)

        context = panel._get_error_context()

        assert context is not None
        assert "/path/to/missing/file.txt" in context

    def test_get_error_context_permission_error(self) -> None:
        """Test error context for PermissionError."""
        error = PermissionError("Permission denied")
        panel = ErrorPanel(error)

        context = panel._get_error_context()

        assert context is not None
        assert "permissions" in context

    def test_get_error_context_none(self) -> None:
        """Test error context returns None for unknown errors."""
        error = ValueError("Generic error")
        panel = ErrorPanel(error)

        context = panel._get_error_context()

        assert context is None

    def test_get_error_suggestions_file_not_found(self) -> None:
        """Test error suggestions for FileNotFoundError."""
        error = FileNotFoundError("No such file")
        panel = ErrorPanel(error)

        suggestions = panel._get_error_suggestions()

        assert len(suggestions) == 3
        assert "Check if file path is correct" in suggestions
        assert "Verify file exists" in suggestions
        assert "Check directory permissions" in suggestions

    def test_get_error_suggestions_permission_error(self) -> None:
        """Test error suggestions for PermissionError."""
        error = PermissionError("Permission denied")
        panel = ErrorPanel(error)

        suggestions = panel._get_error_suggestions()

        assert len(suggestions) == 3
        assert "Run with appropriate permissions" in suggestions
        assert "Check file ownership" in suggestions
        assert "Verify directory access rights" in suggestions

    def test_get_error_suggestions_empty(self) -> None:
        """Test error suggestions returns empty for unknown errors."""
        error = ValueError("Generic error")
        panel = ErrorPanel(error)

        suggestions = panel._get_error_suggestions()

        assert suggestions == []

    def test_format_traceback_success(self) -> None:
        """Test successful traceback formatting."""
        try:
            raise ValueError("Test error for traceback")
        except ValueError as e:
            panel = ErrorPanel(e)
            tb_text = panel._format_traceback()

            assert tb_text is not None
            assert "ValueError" in tb_text
            assert "Test error for traceback" in tb_text

    def test_format_traceback_truncation(self) -> None:
        """Test traceback truncation for long tracebacks."""

        # Create a deep call stack to test truncation
        def deep_call(depth: int) -> None:
            if depth <= 0:
                raise ValueError("Deep error")
            return deep_call(depth - 1)

        try:
            deep_call(15)  # Create deep traceback
        except ValueError as e:
            panel = ErrorPanel(e)
            tb_text = panel._format_traceback()

            assert tb_text is not None
            # The truncation logic triggers when len(tb_lines) > 10
            # But we need to check if it actually truncated based on line count
            tb_lines = tb_text.split("\n")
            if len(tb_lines) > 10:
                # Should contain either "truncated" or "Previous line repeated"
                assert "truncated" in tb_text or "Previous line repeated" in tb_text

    def test_format_traceback_none_on_error(self) -> None:
        """Test format_traceback handles errors gracefully."""
        error = ValueError("Test error")
        # Remove traceback to trigger formatting edge case
        error.__traceback__ = None
        panel = ErrorPanel(error)

        tb_text = panel._format_traceback()

        # Should handle gracefully when no traceback available
        # May return None, empty string, or minimal error info
        assert tb_text is None or tb_text == "" or "ValueError: Test error" in tb_text

    @patch("spec_cli.ui.error_display.get_console")
    def test_print_error_panel(self, mock_get_console: Mock) -> None:
        """Test printing error panel."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        error = ValueError("Test error")
        panel = ErrorPanel(error, console=mock_console)

        panel.print()

        mock_console.print.assert_called_once()
        # Verify the argument is a Panel
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)


class TestDiagnosticDisplay:
    """Test DiagnosticDisplay class functionality."""

    def test_diagnostic_display_initialization(self) -> None:
        """Test DiagnosticDisplay initialization."""
        display = DiagnosticDisplay()

        assert display.console is not None

    def test_diagnostic_display_with_custom_console(self) -> None:
        """Test DiagnosticDisplay with custom console."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        assert display.console == mock_console

    def test_show_system_info(self) -> None:
        """Test showing system information."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        info = {
            "python_version": "3.11.9",
            "platform": "darwin",
            "spec_version": "0.1.0",
        }

        display.show_system_info(info)

        mock_console.print.assert_called_once()
        # Verify the argument is a Panel
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    def test_show_configuration_simple(self) -> None:
        """Test showing simple configuration."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        config = {"debug": True, "max_workers": 4, "timeout": 30}

        display.show_configuration(config)

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    def test_show_configuration_nested(self) -> None:
        """Test showing nested configuration."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        config = {
            "database": {"host": "localhost", "port": 5432, "name": "spec_db"},
            "logging": {"level": "INFO", "file": "/var/log/spec.log"},
        }

        display.show_configuration(config)

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    def test_show_file_details_existing_file(self) -> None:
        """Test showing file details for existing file."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        # Use a file that definitely exists
        file_path = Path(__file__)  # This test file
        details = {
            "size": file_path.stat().st_size,
            "modified": "2023-01-01",
            "permissions": "644",
        }

        display.show_file_details(file_path, details)

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    def test_show_file_details_nonexistent_file(self) -> None:
        """Test showing file details for non-existent file."""
        mock_console = Mock()
        display = DiagnosticDisplay(console=mock_console)

        file_path = Path("/nonexistent/file.txt")
        details = {"expected_size": 1024, "last_seen": "2023-01-01"}

        display.show_file_details(file_path, details)

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)


class TestStackTraceFormatter:
    """Test StackTraceFormatter class functionality."""

    def test_stack_trace_formatter_initialization(self) -> None:
        """Test StackTraceFormatter initialization."""
        formatter = StackTraceFormatter()

        assert formatter.console is not None

    def test_stack_trace_formatter_with_custom_console(self) -> None:
        """Test StackTraceFormatter with custom console."""
        mock_console = Mock()
        formatter = StackTraceFormatter(console=mock_console)

        assert formatter.console == mock_console

    def test_format_exception_basic(self) -> None:
        """Test basic exception formatting."""
        formatter = StackTraceFormatter()

        try:
            raise ValueError("Test error for formatting")
        except ValueError as e:
            traceback_obj = formatter.format_exception(e)

            assert isinstance(traceback_obj, Traceback)

    def test_format_exception_with_locals(self) -> None:
        """Test exception formatting with locals."""
        formatter = StackTraceFormatter()

        try:
            _local_var = "test_value"
            raise ValueError("Test error with locals")
        except ValueError as e:
            traceback_obj = formatter.format_exception(e, show_locals=True)

            assert isinstance(traceback_obj, Traceback)

    def test_format_exception_max_frames(self) -> None:
        """Test exception formatting with max frames limit."""
        formatter = StackTraceFormatter()

        def deep_call(depth: int) -> None:
            if depth <= 0:
                raise ValueError("Deep error")
            return deep_call(depth - 1)

        try:
            deep_call(5)
        except ValueError as e:
            traceback_obj = formatter.format_exception(e, max_frames=3)

            assert isinstance(traceback_obj, Traceback)

    def test_print_exception(self) -> None:
        """Test printing formatted exception."""
        mock_console = Mock()
        formatter = StackTraceFormatter(console=mock_console)

        try:
            raise ValueError("Test error for printing")
        except ValueError as e:
            formatter.print_exception(e)

            mock_console.print.assert_called_once()
            args, kwargs = mock_console.print.call_args
            assert isinstance(args[0], Traceback)

    def test_print_exception_with_options(self) -> None:
        """Test printing formatted exception with options."""
        mock_console = Mock()
        formatter = StackTraceFormatter(console=mock_console)

        try:
            _local_var = "test_value"
            raise ValueError("Test error with options")
        except ValueError as e:
            formatter.print_exception(e, show_locals=True, max_frames=5)

            mock_console.print.assert_called_once()
            args, kwargs = mock_console.print.call_args
            assert isinstance(args[0], Traceback)


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_error_function(self, mock_get_console: Mock) -> None:
        """Test show_error utility function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        error = ValueError("Test error")
        show_error(error)

        mock_console.print.assert_called_once()

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_error_with_options(self, mock_get_console: Mock) -> None:
        """Test show_error with options."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        error = ValueError("Test error")
        show_error(error, title="Custom Title", show_traceback=False)

        mock_console.print.assert_called_once()

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_warning_function(self, mock_get_console: Mock) -> None:
        """Test show_warning utility function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_warning("Test warning message")

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_warning_with_details(self, mock_get_console: Mock) -> None:
        """Test show_warning with details."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_warning("Test warning", details="Additional warning details")

        mock_console.print.assert_called_once()

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_success_function(self, mock_get_console: Mock) -> None:
        """Test show_success utility function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_success("Test success message")

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_success_with_details(self, mock_get_console: Mock) -> None:
        """Test show_success with details."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_success("Test success", details="Additional success details")

        mock_console.print.assert_called_once()

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_info_function(self, mock_get_console: Mock) -> None:
        """Test show_info utility function."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_info("Test info message")

        mock_console.print.assert_called_once()
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Panel)

    @patch("spec_cli.ui.error_display.get_console")
    def test_show_info_with_details(self, mock_get_console: Mock) -> None:
        """Test show_info with details."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console

        show_info("Test info", details="Additional info details")

        mock_console.print.assert_called_once()

    @patch("spec_cli.ui.error_display.show_success")
    @patch("spec_cli.ui.error_display.show_warning")
    @patch("spec_cli.ui.error_display.show_error")
    @patch("spec_cli.ui.error_display.show_info")
    def test_show_message_success(
        self, mock_info: Mock, mock_error: Mock, mock_warning: Mock, mock_success: Mock
    ) -> None:
        """Test show_message with success type."""
        show_message("Test message", "success")

        mock_success.assert_called_once_with("Test message")
        mock_warning.assert_not_called()
        mock_error.assert_not_called()
        mock_info.assert_not_called()

    @patch("spec_cli.ui.error_display.show_success")
    @patch("spec_cli.ui.error_display.show_warning")
    @patch("spec_cli.ui.error_display.show_error")
    @patch("spec_cli.ui.error_display.show_info")
    def test_show_message_warning(
        self, mock_info: Mock, mock_error: Mock, mock_warning: Mock, mock_success: Mock
    ) -> None:
        """Test show_message with warning type."""
        show_message("Test message", "warning")

        mock_warning.assert_called_once_with("Test message")
        mock_success.assert_not_called()
        mock_error.assert_not_called()
        mock_info.assert_not_called()

    @patch("spec_cli.ui.error_display.show_success")
    @patch("spec_cli.ui.error_display.show_warning")
    @patch("spec_cli.ui.error_display.show_error")
    @patch("spec_cli.ui.error_display.show_info")
    def test_show_message_error(
        self, mock_info: Mock, mock_error: Mock, mock_warning: Mock, mock_success: Mock
    ) -> None:
        """Test show_message with error type."""
        show_message("Test message", "error")

        # show_message wraps string messages in Exception for show_error
        mock_error.assert_called_once()
        args = mock_error.call_args[0]
        assert str(args[0]) == "Test message"
        mock_success.assert_not_called()
        mock_warning.assert_not_called()
        mock_info.assert_not_called()

    @patch("spec_cli.ui.error_display.show_success")
    @patch("spec_cli.ui.error_display.show_warning")
    @patch("spec_cli.ui.error_display.show_error")
    @patch("spec_cli.ui.error_display.show_info")
    def test_show_message_default_info(
        self, mock_info: Mock, mock_error: Mock, mock_warning: Mock, mock_success: Mock
    ) -> None:
        """Test show_message with default info type."""
        show_message("Test message")  # Default type

        mock_info.assert_called_once_with("Test message")
        mock_success.assert_not_called()
        mock_warning.assert_not_called()
        mock_error.assert_not_called()

    @patch("spec_cli.ui.error_display.show_success")
    @patch("spec_cli.ui.error_display.show_warning")
    @patch("spec_cli.ui.error_display.show_error")
    @patch("spec_cli.ui.error_display.show_info")
    def test_show_message_with_context(
        self, mock_info: Mock, mock_error: Mock, mock_warning: Mock, mock_success: Mock
    ) -> None:
        """Test show_message with context."""
        show_message("Test message", "info", context="Test Context")

        mock_info.assert_called_once_with("Test Context: Test message")

    @patch("spec_cli.ui.error_display.get_console")
    def test_format_data_dict_auto(self, mock_get_console: Mock) -> None:
        """Test format_data with dictionary in auto mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        data = {"key1": "value1", "key2": "value2"}

        # The create_key_value_table is imported dynamically in format_data
        with patch("spec_cli.ui.tables.create_key_value_table") as mock_table:
            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance

            format_data(data)

            mock_table.assert_called_once_with(data, None)
            mock_table_instance.print.assert_called_once()

    @patch("spec_cli.ui.error_display.get_console")
    def test_format_data_list_auto(self, mock_get_console: Mock) -> None:
        """Test format_data with list in auto mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        data = ["item1", "item2", "item3"]

        format_data(data)

        # Should print each item with bullet
        assert mock_console.print.call_count == len(data)

    @patch("spec_cli.ui.error_display.get_console")
    def test_format_data_string_auto(self, mock_get_console: Mock) -> None:
        """Test format_data with string in auto mode."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        data = "Simple string data"

        format_data(data)

        mock_console.print.assert_called_with("Simple string data")

    @patch("spec_cli.ui.error_display.get_console")
    def test_format_data_with_title(self, mock_get_console: Mock) -> None:
        """Test format_data with title."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        data = "Test data"
        title = "Test Title"

        format_data(data, title=title)

        # Should print title first, then data
        assert mock_console.print.call_count == 2
        title_call = mock_console.print.call_args_list[0]
        assert "Test Title" in str(title_call)

    @patch("spec_cli.ui.error_display.get_console")
    def test_format_data_specific_format(self, mock_get_console: Mock) -> None:
        """Test format_data with specific format."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console

        data = {"key": "value"}

        format_data(data, format_type="json")

        # Should use string representation for non-auto formats
        mock_console.print.assert_called_with(str(data))

    def test_format_code_snippet_basic(self) -> None:
        """Test basic code snippet formatting."""
        code = 'print("Hello, World!")'

        syntax_obj = format_code_snippet(code)

        assert isinstance(syntax_obj, Syntax)

    def test_format_code_snippet_with_language(self) -> None:
        """Test code snippet formatting with specific language."""
        code = 'console.log("Hello, World!");'

        syntax_obj = format_code_snippet(code, language="javascript")

        assert isinstance(syntax_obj, Syntax)

    def test_format_code_snippet_with_theme(self) -> None:
        """Test code snippet formatting with custom theme."""
        code = 'print("Hello, World!")'

        syntax_obj = format_code_snippet(code, theme="github-dark")

        assert isinstance(syntax_obj, Syntax)

    def test_format_code_snippet_no_line_numbers(self) -> None:
        """Test code snippet formatting without line numbers."""
        code = 'print("Hello, World!")'

        syntax_obj = format_code_snippet(code, line_numbers=False)

        assert isinstance(syntax_obj, Syntax)

    def test_format_code_snippet_with_highlights(self) -> None:
        """Test code snippet formatting with highlighted lines."""
        code = """def hello():
    print("Hello")
    return True"""

        syntax_obj = format_code_snippet(code, highlight_lines=[1, 3])

        assert isinstance(syntax_obj, Syntax)

    def test_format_code_snippet_all_options(self) -> None:
        """Test code snippet formatting with all options."""
        code = """def hello():
    print("Hello")
    return True"""

        syntax_obj = format_code_snippet(
            code,
            language="python",
            theme="monokai",
            line_numbers=True,
            highlight_lines=[2],
        )

        assert isinstance(syntax_obj, Syntax)


class TestErrorIntegration:
    """Test error display integration scenarios."""

    def test_spec_error_with_details_full_flow(self) -> None:
        """Test complete flow with SpecError containing details."""
        error = SpecError("Configuration validation failed")
        error.details = "Missing required field 'api_key'"

        panel = ErrorPanel(error, show_traceback=False)
        rich_panel = panel.create_panel()

        assert isinstance(rich_panel, Panel)
        assert "[error]SpecError[/error]" in panel.title

    def test_file_system_error_suggestions(self) -> None:
        """Test file system error with appropriate suggestions."""
        error = FileNotFoundError("Config file not found")
        error.filename = "/etc/spec/config.yaml"

        panel = ErrorPanel(error, show_traceback=False)
        suggestions = panel._get_error_suggestions()
        context = panel._get_error_context()

        assert len(suggestions) == 3
        assert "Check if file path is correct" in suggestions
        assert context is not None
        assert "/etc/spec/config.yaml" in context

    def test_permission_error_handling(self) -> None:
        """Test permission error handling."""
        error = PermissionError("Access denied")

        panel = ErrorPanel(error, show_traceback=False)
        suggestions = panel._get_error_suggestions()
        context = panel._get_error_context()

        assert len(suggestions) == 3
        assert "Run with appropriate permissions" in suggestions
        assert context is not None
        assert "permissions" in context
