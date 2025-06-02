"""Shared CLI options and decorators."""

from functools import update_wrapper
from typing import Any, Callable, Optional

import click

from ..logging.debug import debug_logger


# Common option decorators
def debug_option(f: Callable) -> Callable:
    """Add debug mode option."""

    def callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
        if value:
            debug_logger.log("INFO", "Debug mode enabled via CLI")
        return value

    return click.option(
        "--debug",
        is_flag=True,
        help="Enable debug output and detailed logging",
        callback=callback,
        expose_value=True,
    )(f)


def verbose_option(f: Callable) -> Callable:
    """Add verbose mode option."""
    return click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output",
    )(f)


def dry_run_option(f: Callable) -> Callable:
    """Add dry run option."""
    return click.option(
        "--dry-run",
        is_flag=True,
        help="Show what would be done without making changes",
    )(f)


def force_option(f: Callable) -> Callable:
    """Add force option."""
    return click.option(
        "--force",
        is_flag=True,
        help="Force operation even if conflicts or warnings exist",
    )(f)


def message_option(required: bool = False) -> Callable:
    """Add commit message option."""

    def decorator(f: Callable) -> Callable:
        return click.option(
            "--message",
            "-m",
            required=required,
            help="Commit message" + (" (required)" if required else ""),
        )(f)

    return decorator


def files_argument(f: Callable) -> Callable:
    """Add files argument."""
    return click.argument(
        "files",
        nargs=-1,
        type=click.Path(exists=False),  # Allow non-existent files for generation
        required=True,
    )(f)


def optional_files_argument(f: Callable) -> Callable:
    """Add optional files argument."""
    return click.argument(
        "files",
        nargs=-1,
        type=click.Path(exists=False),
        required=False,
    )(f)


def common_options(f: Callable) -> Callable:
    """Apply common options to a command."""
    f = debug_option(f)
    f = verbose_option(f)
    return f


def spec_command(name: Optional[str] = None, **kwargs: Any) -> Callable[..., Any]:
    """Decorator for spec commands with common setup."""

    def decorator(f: Callable) -> Any:
        # Apply common options
        f_with_options = common_options(f)

        # Add error handling wrapper
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from .utils import handle_cli_error

            try:
                return f_with_options(*args, **kwargs)
            except click.ClickException:
                # Re-raise Click exceptions to preserve exit codes
                raise
            except Exception as e:
                handle_cli_error(e, f"Command '{name or f.__name__}' failed")

        # Preserve command metadata
        wrapper = update_wrapper(wrapper, f)

        # Create click command with the wrapper
        cmd = click.command(name, **kwargs)(wrapper)

        return cmd

    return decorator


# Validation helpers
def validate_spec_repository(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Any:
    """Validate that we're in a spec repository."""
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    try:
        repo = SpecGitRepository()
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return value
    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository error: {e}") from e


def validate_file_exists(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """Validate that file exists."""
    if value and not click.Path(exists=True).convert(value, param, ctx):
        raise click.BadParameter(f"File '{value}' does not exist")
    return value
