import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.traceback import Traceback

from ..core.error_handler import ErrorHandler
from ..exceptions import SpecError
from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles


class ErrorPanel:
    """Rich panel for displaying error information with formatting."""

    def __init__(
        self,
        error: Exception,
        title: Optional[str] = None,
        show_traceback: bool = True,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize error panel.

        Args:
            error: Exception to display
            title: Optional panel title
            show_traceback: Whether to show full traceback
            console: Console to use for display
        """
        self.error = error
        self.title = title or self._get_error_title(error)
        self.show_traceback = show_traceback
        self.console = console or get_console().console
        self.error_handler = ErrorHandler({"component": "ui_display"})

        debug_logger.log(
            "INFO", "ErrorPanel initialized", error_type=type(error).__name__
        )

    def _get_error_title(self, error: Exception) -> str:
        """Get appropriate title for error type.

        Args:
            error: Exception instance

        Returns:
            Formatted title string
        """
        error_type = type(error).__name__
        if isinstance(error, SpecError):
            return f"[error]{error_type}[/error]"
        elif isinstance(error, (ValueError, TypeError)):
            return f"[warning]{error_type}[/warning]"
        else:
            return "[error]Error[/error]"

    def create_panel(self) -> Panel:
        """Create Rich panel with error information.

        Returns:
            Rich Panel with formatted error display
        """
        content_parts = []

        # Error message
        error_message = str(self.error)
        if error_message:
            content_parts.append(SpecStyles.error(error_message))

        # Error details for SpecError types
        if isinstance(self.error, SpecError) and hasattr(self.error, "details"):
            details = self.error.details
            if details:
                content_parts.append("\n" + SpecStyles.muted("Details:"))
                content_parts.append(SpecStyles.value(str(details)))

        # Context information for specific error types
        context = self._get_error_context()
        if context:
            content_parts.append("\n" + SpecStyles.muted("Context:"))
            content_parts.append(context)

        # Suggestions for resolution
        suggestions = self._get_error_suggestions()
        if suggestions:
            content_parts.append("\n" + SpecStyles.muted("Suggestions:"))
            for suggestion in suggestions:
                content_parts.append(f"• {suggestion}")

        # Traceback (if requested and available)
        if self.show_traceback:
            tb_text = self._format_traceback()
            if tb_text:
                content_parts.append("\n" + SpecStyles.muted("Traceback:"))
                content_parts.append(tb_text)

        content = (
            "\n".join(content_parts)
            if content_parts
            else SpecStyles.error("Unknown error occurred")
        )

        return Panel(
            content,
            title=self.title,
            border_style="error",
            padding=(1, 2),
            expand=False,
        )

    def _get_error_context(self) -> Optional[str]:
        """Get contextual information for the error.

        Returns:
            Formatted context string or None
        """
        try:
            # Use ErrorHandler for consistent context creation
            self.error_handler.report(
                self.error, "display error context", display_mode="ui"
            )

            if isinstance(self.error, FileNotFoundError):
                return SpecStyles.path(
                    str(getattr(self.error, "filename", "Unknown file"))
                )
            elif isinstance(self.error, PermissionError):
                return SpecStyles.warning("Check file and directory permissions")
            return None
        except Exception:
            # Fallback for UI display
            if isinstance(self.error, FileNotFoundError):
                return SpecStyles.path(
                    str(getattr(self.error, "filename", "Unknown file"))
                )
            elif isinstance(self.error, PermissionError):
                return SpecStyles.warning("Check file and directory permissions")
            return None

    def _get_error_suggestions(self) -> List[str]:
        """Get suggestions for resolving the error.

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if isinstance(self.error, FileNotFoundError):
            suggestions.extend(
                [
                    "Check if file path is correct",
                    "Verify file exists",
                    "Check directory permissions",
                ]
            )
        elif isinstance(self.error, PermissionError):
            suggestions.extend(
                [
                    "Run with appropriate permissions",
                    "Check file ownership",
                    "Verify directory access rights",
                ]
            )

        return suggestions

    def _format_traceback(self) -> Optional[str]:
        """Format traceback for display.

        Returns:
            Formatted traceback string or None
        """
        try:
            tb_lines = traceback.format_exception(
                type(self.error), self.error, self.error.__traceback__
            )
            # Limit traceback length for readability
            if len(tb_lines) > 10:
                tb_lines = tb_lines[:5] + ["  ... (truncated) ...\n"] + tb_lines[-3:]

            return "".join(tb_lines).strip()
        except Exception as e:
            # Use ErrorHandler for consistent error reporting
            self.error_handler.report(
                e,
                "format traceback for display",
                original_error=str(self.error),
                formatting_stage="traceback_formatting",
            )
            return None

    def print(self) -> None:
        """Print the error panel to console."""
        panel = self.create_panel()
        self.console.print(panel)

        debug_logger.log("DEBUG", "Error panel printed")


class DiagnosticDisplay:
    """Display diagnostic information in formatted panels."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize diagnostic display.

        Args:
            console: Console to use for output
        """
        self.console = console or get_console().console
        self.error_handler = ErrorHandler({"component": "diagnostic_display"})

    def show_system_info(self, info: Dict[str, Any]) -> None:
        """Display system information.

        Args:
            info: Dictionary of system information
        """
        content_parts = []

        for key, value in info.items():
            formatted_key = SpecStyles.label(f"{key}:")
            formatted_value = SpecStyles.value(str(value))
            content_parts.append(f"{formatted_key} {formatted_value}")

        content = "\n".join(content_parts)

        panel = Panel(
            content,
            title=SpecStyles.title("System Information"),
            border_style="info",
            padding=(1, 2),
        )

        self.console.print(panel)

    def show_configuration(self, config: Dict[str, Any]) -> None:
        """Display configuration information.

        Args:
            config: Configuration dictionary
        """
        content_parts = []

        for section, values in config.items():
            content_parts.append(SpecStyles.subtitle(f"{section}:"))

            if isinstance(values, dict):
                for key, value in values.items():
                    formatted_key = SpecStyles.muted(f"  {key}:")
                    formatted_value = SpecStyles.value(str(value))
                    content_parts.append(f"{formatted_key} {formatted_value}")
            else:
                formatted_value = SpecStyles.value(str(values))
                content_parts.append(f"  {formatted_value}")

            content_parts.append("")  # Empty line between sections

        content = "\n".join(content_parts).rstrip()

        panel = Panel(
            content,
            title=SpecStyles.title("Configuration"),
            border_style="config",
            padding=(1, 2),
        )

        self.console.print(panel)

    def show_file_details(self, file_path: Path, details: Dict[str, Any]) -> None:
        """Display file details.

        Args:
            file_path: Path to the file
            details: Dictionary of file details
        """
        content_parts = [
            f"{SpecStyles.label('Path:')} {SpecStyles.path(file_path)}",
            f"{SpecStyles.label('Exists:')} {SpecStyles.success('Yes') if file_path.exists() else SpecStyles.error('No')}",
        ]

        for key, value in details.items():
            formatted_key = SpecStyles.label(f"{key}:")
            formatted_value = SpecStyles.value(str(value))
            content_parts.append(f"{formatted_key} {formatted_value}")

        content = "\n".join(content_parts)

        panel = Panel(
            content,
            title=SpecStyles.title("File Details"),
            border_style="file",
            padding=(1, 2),
        )

        self.console.print(panel)


class StackTraceFormatter:
    """Enhanced stack trace formatting with syntax highlighting."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize stack trace formatter.

        Args:
            console: Console for output
        """
        self.console = console or get_console().console
        self.error_handler = ErrorHandler({"component": "stack_trace_formatter"})

    def format_exception(
        self,
        error: Exception,
        show_locals: bool = False,
        max_frames: int = 10,
    ) -> Traceback:
        """Format exception with Rich traceback.

        Args:
            error: Exception to format
            show_locals: Whether to show local variables
            max_frames: Maximum number of frames to show

        Returns:
            Rich Traceback object
        """
        return Traceback.from_exception(
            type(error),
            error,
            error.__traceback__,
            show_locals=show_locals,
            max_frames=max_frames,
            suppress=[],  # Don't suppress any modules
        )

    def print_exception(
        self,
        error: Exception,
        show_locals: bool = False,
        max_frames: int = 10,
    ) -> None:
        """Print formatted exception.

        Args:
            error: Exception to print
            show_locals: Whether to show local variables
            max_frames: Maximum number of frames to show
        """
        traceback_obj = self.format_exception(error, show_locals, max_frames)
        self.console.print(traceback_obj)


# Utility functions
def show_error(
    error: Exception,
    title: Optional[str] = None,
    show_traceback: bool = True,
    console: Optional[Console] = None,
) -> None:
    """Show an error with formatted panel.

    Args:
        error: Exception to display
        title: Optional panel title
        show_traceback: Whether to show traceback
        console: Console to use
    """
    error_panel = ErrorPanel(error, title, show_traceback, console)
    error_panel.print()


def show_warning(
    message: str,
    details: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Show a warning message.

    Args:
        message: Warning message
        details: Optional additional details
        console: Console to use
    """
    console = console or get_console().console

    content = SpecStyles.warning(message)
    if details:
        content += "\n" + SpecStyles.muted(details)

    panel = Panel(
        content,
        title=SpecStyles.warning("Warning"),
        border_style="warning",
        padding=(1, 2),
    )

    console.print(panel)


def show_success(
    message: str,
    details: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Show a success message.

    Args:
        message: Success message
        details: Optional additional details
        console: Console to use
    """
    console = console or get_console().console

    content = SpecStyles.success(message)
    if details:
        content += "\n" + SpecStyles.muted(details)

    panel = Panel(
        content,
        title=SpecStyles.success("Success"),
        border_style="success",
        padding=(1, 2),
    )

    console.print(panel)


def show_info(
    message: str,
    details: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Show an info message.

    Args:
        message: Info message
        details: Optional additional details
        console: Console to use
    """
    console = console or get_console().console

    content = SpecStyles.info(message)
    if details:
        content += "\n" + SpecStyles.muted(details)

    panel = Panel(
        content,
        title=SpecStyles.info("Information"),
        border_style="info",
        padding=(1, 2),
    )

    console.print(panel)


def show_message(
    message: str, message_type: str = "info", context: Optional[str] = None
) -> None:
    """Show a message with appropriate styling.

    Args:
        message: Message to display
        message_type: Type of message (success, warning, error, info)
        context: Optional context information
    """
    _console = get_console()

    if context:
        full_message = f"{context}: {message}"
    else:
        full_message = message

    if message_type == "success":
        show_success(full_message)
    elif message_type == "warning":
        show_warning(full_message)
    elif message_type == "error":
        show_error(Exception(full_message))
    else:  # info or default
        show_info(full_message)


def format_data(
    data: Any, title: Optional[str] = None, format_type: str = "auto"
) -> None:
    """Format and display data using Rich formatting.

    Args:
        data: Data to display
        title: Optional title for the data
        format_type: Format type (auto, table, json)
    """
    console = get_console()

    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")

    if format_type == "auto":
        # Auto-detect format based on data type
        if isinstance(data, dict):
            from .tables import create_key_value_table

            table = create_key_value_table(data, title)
            table.print()
        elif isinstance(data, list):
            for item in data:
                console.print(f"  • {item}")
        else:
            console.print(str(data))
    else:
        # Use specific format
        console.print(str(data))


def format_code_snippet(
    code: str,
    language: str = "python",
    theme: str = "monokai",
    line_numbers: bool = True,
    highlight_lines: Optional[List[int]] = None,
) -> Syntax:
    """Format code snippet with syntax highlighting.

    Args:
        code: Code to format
        language: Programming language
        theme: Syntax highlighting theme
        line_numbers: Whether to show line numbers
        highlight_lines: Optional lines to highlight

    Returns:
        Rich Syntax object
    """
    return Syntax(
        code,
        language,
        theme=theme,
        line_numbers=line_numbers,
        highlight_lines=set(highlight_lines) if highlight_lines else None,
        word_wrap=True,
    )
