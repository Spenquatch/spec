"""Rich-based terminal UI system for spec CLI.

This package provides console theming, progress tracking, and the foundation
for error display and formatting components.
"""

from .console import SpecConsole, get_console, reset_console, set_console, spec_console
from .error_display import (
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
from .progress_bar import (
    SimpleProgressBar,
    SpecProgressBar,
    create_progress_bar,
    simple_progress,
)
from .progress_manager import (
    ProgressManager,
    ProgressState,
    get_progress_manager,
    reset_progress_manager,
    set_progress_manager,
)
from .progress_utils import (
    ProgressTracker,
    calculate_processing_speed,
    estimate_operation_time,
    format_time_duration,
    progress_context,
    show_progress_for_files,
    timed_operation,
    track_progress,
)
from .spinner import (
    SpecSpinner,
    SpinnerManager,
    TimedSpinner,
    create_spinner,
    spinner_context,
    timed_spinner,
)
from .styles import SpecStyles, create_rich_text, format_path, format_status, style_text
from .tables import (
    ComparisonTable,
    FileListTable,
    SpecTable,
    StatusTable,
    create_file_table,
    create_key_value_table,
    create_status_table,
    format_table_data,
    print_simple_table,
)
from .theme import (
    ColorScheme,
    SpecTheme,
    get_current_theme,
    reset_theme,
    set_current_theme,
)

__all__ = [
    # Console and theming
    "get_console",
    "spec_console",
    "SpecConsole",
    "set_console",
    "reset_console",
    "SpecTheme",
    "ColorScheme",
    "get_current_theme",
    "set_current_theme",
    "reset_theme",
    "SpecStyles",
    "style_text",
    "format_path",
    "format_status",
    "create_rich_text",
    # Progress components
    "SpecProgressBar",
    "SimpleProgressBar",
    "create_progress_bar",
    "simple_progress",
    "SpecSpinner",
    "TimedSpinner",
    "SpinnerManager",
    "create_spinner",
    "timed_spinner",
    "spinner_context",
    # Progress management
    "ProgressManager",
    "ProgressState",
    "get_progress_manager",
    "set_progress_manager",
    "reset_progress_manager",
    # Progress utilities
    "progress_context",
    "timed_operation",
    "ProgressTracker",
    "track_progress",
    "show_progress_for_files",
    "estimate_operation_time",
    "format_time_duration",
    "calculate_processing_speed",
    # Table formatting
    "SpecTable",
    "FileListTable",
    "StatusTable",
    "ComparisonTable",
    "create_file_table",
    "create_key_value_table",
    "create_status_table",
    "print_simple_table",
    "format_table_data",
    # Error display
    "ErrorPanel",
    "DiagnosticDisplay",
    "StackTraceFormatter",
    "show_error",
    "show_warning",
    "show_success",
    "show_info",
    "show_message",
    "format_data",
    "format_code_snippet",
]
