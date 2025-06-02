"""CLI interface for spec CLI.

This package provides the command-line interface with Click and Rich integration
for beautiful, modern command-line interactions.
"""

from .app import app, main
from .options import (
    common_options,
    debug_option,
    dry_run_option,
    force_option,
    message_option,
    verbose_option,
)
from .utils import (
    format_command_output,
    get_user_confirmation,
    handle_cli_error,
    setup_cli_logging,
    validate_file_paths,
)

__all__ = [
    "app",
    "main",
    "handle_cli_error",
    "setup_cli_logging",
    "validate_file_paths",
    "get_user_confirmation",
    "format_command_output",
    "debug_option",
    "verbose_option",
    "dry_run_option",
    "force_option",
    "message_option",
    "common_options",
]
