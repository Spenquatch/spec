"""CLI utility functions."""

import sys
from pathlib import Path
from typing import Any, Callable, List, Optional

import click

from ..core.error_handler import ErrorHandler
from ..exceptions import SpecError
from ..logging.debug import debug_logger

# Create CLI-specific error handler
cli_error_handler = ErrorHandler({"module": "cli", "component": "utils"})


def handle_cli_error(
    error: Exception, context: Optional[str] = None, exit_code: int = 1
) -> None:
    """Handle CLI errors with appropriate formatting and exit codes.

    Args:
        error: Exception that occurred
        context: Optional context information
        exit_code: Exit code to use when exiting
    """
    # Use ErrorHandler for consistent error reporting
    cli_error_handler.report(error, "CLI command execution", cli_context=context)

    # Format error message based on type
    if isinstance(error, click.ClickException):
        # Click handles its own formatting
        error.show()
    elif isinstance(error, SpecError):
        # Use our custom error formatting
        error_msg = str(error)
        if hasattr(error, "suggestions") and error.suggestions:
            error_msg += "\n\nSuggestions:"
            for suggestion in error.suggestions:
                error_msg += f"\n  • {suggestion}"

        from ..ui.error_display import show_message

        show_message(error_msg, "error", context)
    else:
        # Generic error handling
        error_msg = f"{type(error).__name__}: {error}"
        from ..ui.error_display import show_message

        show_message(error_msg, "error", context)

    # Exit with appropriate code
    sys.exit(exit_code)


def setup_cli_logging(debug_mode: bool = False, verbose: bool = False) -> None:
    """Set up CLI logging based on debug and verbose modes.

    Args:
        debug_mode: Whether debug mode is enabled
        verbose: Whether verbose mode is enabled
    """
    if debug_mode:
        debug_logger.log("INFO", "Debug mode enabled for CLI")
        # In debug mode, enable more detailed logging
    elif verbose:
        debug_logger.log("INFO", "Verbose mode enabled for CLI")
        # In verbose mode, show more user-facing information
    else:
        # In normal mode, reduce logging verbosity
        pass


def validate_file_paths(file_paths: List[str]) -> List[Path]:
    """Validate and normalize file paths from CLI input.

    Args:
        file_paths: List of file path strings

    Returns:
        List of validated Path objects

    Raises:
        click.BadParameter: If validation fails
    """
    if not file_paths:
        raise click.BadParameter("No file paths provided")

    validated_paths = []
    for path_str in file_paths:
        try:
            path = Path(path_str).resolve()
            validated_paths.append(path)
        except Exception as e:
            raise click.BadParameter(f"Invalid file path '{path_str}': {e}") from e

    return validated_paths


def get_user_confirmation(message: str, default: bool = False) -> bool:
    """Get user confirmation with Click prompt.

    Args:
        message: Confirmation message
        default: Default value

    Returns:
        True if user confirms
    """
    return click.confirm(message, default=default)


def format_command_output(data: Any, format_type: str = "auto") -> None:
    """Format and display command output using Rich UI.

    Args:
        data: Data to display
        format_type: Format type (auto, table, list, json)
    """
    from ..ui.error_display import format_data

    if format_type == "auto":
        # Auto-detect format based on data type
        format_data(data)
    else:
        # Use specific format
        format_data(data, format_type)


def echo_status(message: str, status_type: str = "info") -> None:
    """Echo a status message with styling.

    Args:
        message: Message to display
        status_type: Type of status (info, success, warning, error)
    """
    from ..ui.error_display import show_message

    show_message(message, status_type)


@cli_error_handler.wrap
def get_spec_repository() -> Any:
    """Get the spec repository instance with error handling.

    Returns:
        SpecGitRepository instance

    Raises:
        click.ClickException: If repository is not initialized
    """
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    try:
        repo = SpecGitRepository()
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return repo
    except SpecRepositoryError as e:
        cli_error_handler.log_and_raise(
            e, "get spec repository", reraise_as=click.ClickException
        )


def with_progress_context(operation_name: str) -> Callable:
    """Decorator to wrap command with progress context.

    Args:
        operation_name: Name of the operation for progress tracking
    """

    def decorator(f: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from ..ui.progress_manager import get_progress_manager

            progress_manager = get_progress_manager()
            operation_id = f"{operation_name}_{id(f)}"

            progress_manager.start_indeterminate_operation(
                operation_id, f"Running {operation_name}..."
            )

            try:
                result = f(*args, **kwargs)
                progress_manager.finish_operation(operation_id)
                return result
            except Exception:
                progress_manager.finish_operation(operation_id)
                raise

        return wrapper

    return decorator


def get_current_working_directory() -> Path:
    """Get current working directory as Path object.

    Returns:
        Current working directory
    """
    return Path.cwd()


def is_in_spec_repository() -> bool:
    """Check if current directory is in a spec repository.

    Returns:
        True if in spec repository
    """
    try:
        from ..git.repository import SpecGitRepository

        repo = SpecGitRepository()
        return repo.is_initialized()
    except Exception:
        return False
