"""Main CLI application with Click framework."""

import os
import sys
import types
import warnings
from pathlib import Path
from typing import Any

import click

from ..core.context import SpecContext
from ..ui.console import get_console
from ..utils.cli_setup_utils import (
    CLISetupError,
    initialize_cli_context,
    setup_click_context_storage,
)
from .commands import help_command, init_command, status_command
from .commands.add import add_command
from .commands.agent_scope import agent_scope_command
from .commands.commit import commit_command
from .commands.diff import diff_command
from .commands.gen import gen_command
from .commands.log import log_command
from .commands.regen import regen_command
from .commands.show import show_command
from .utils import handle_cli_error

# Suppress noisy logs early in the application startup
os.environ["TORCH_DISTRIBUTED_DETAIL"] = "ERROR"
warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")
warnings.filterwarnings(
    "ignore", message=".*found in sys.modules.*", category=RuntimeWarning
)

try:
    import rich_click

    click_impl: types.ModuleType = rich_click
    click_impl.rich_click.USE_MARKDOWN = True
    click_impl.rich_click.SHOW_ARGUMENTS = True
    click_impl.rich_click.GROUP_ARGUMENTS_OPTIONS = True
except ImportError:
    # Fallback to regular click if rich-click not available
    click_impl = click


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def app(ctx: click.Context, version: bool) -> None:
    """Spec CLI - Versioned Documentation for AI-Assisted Development.

    Manage documentation specs for your codebase with Git integration.

    Examples:
        spec init                    # Initialize repository
        spec status                  # Show repository status
        spec help init               # Get help for init command
    """
    # Initialize SpecContext for CLI operations
    try:
        # Determine root path from current working directory
        root_path = Path.cwd()

        # Initialize CLI context using P1.2b factory
        spec_context = initialize_cli_context(root_path)

        # Setup Click context storage using P2.1b integration
        setup_click_context_storage(ctx, spec_context)

    except CLISetupError as e:
        # Handle context setup failures gracefully
        handle_cli_error(e, "CLI context initialization failed")
        return
    except Exception as e:
        # Handle unexpected errors during context setup
        handle_cli_error(e, "Unexpected error during CLI initialization")
        return

    if version:
        click.echo("Spec CLI v0.1.0")
        return

    if ctx.invoked_subcommand is None:
        # No subcommand provided, show help
        from .commands.help import _display_main_help

        # Get SpecContext from Click context storage
        stored_context: Any = ctx.meta.get("spec_context")
        if isinstance(stored_context, SpecContext):
            _display_main_help(stored_context)
        else:
            # Fallback to simple message if context not available
            click.echo("Spec CLI - Use 'spec help' for command information")


# Add commands to the main group
app.add_command(init_command, name="init")
app.add_command(status_command, name="status")
app.add_command(help_command, name="help")
app.add_command(gen_command, name="gen")
app.add_command(regen_command, name="regen")
app.add_command(add_command, name="add")
app.add_command(agent_scope_command, name="agent-scope")
app.add_command(diff_command, name="diff")
app.add_command(log_command, name="log")
app.add_command(show_command, name="show")
app.add_command(commit_command, name="commit")


def create_cli_app(root_path: Path | None = None) -> click.Group:
    """Create CLI application with context setup for testing.

    Args:
        root_path: Root path for CLI operations (uses current directory if None)

    Returns:
        Click Group configured for CLI operations

    Raises:
        CLISetupError: If CLI app creation fails
    """
    if root_path is None:
        root_path = Path.cwd()

    # Create a copy of the app with context for the specified root
    @click.group(
        invoke_without_command=True,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.option("--version", is_flag=True, help="Show version information")
    @click.pass_context
    def cli_app(ctx: click.Context, version: bool) -> None:
        """Spec CLI with configurable root path."""
        # Initialize SpecContext for CLI operations
        try:
            # Initialize CLI context using P1.2b factory
            spec_context = initialize_cli_context(root_path)

            # Setup Click context storage using P2.1b integration
            setup_click_context_storage(ctx, spec_context)

        except CLISetupError as e:
            # Handle context setup failures gracefully
            handle_cli_error(e, "CLI context initialization failed")
            return
        except Exception as e:
            # Handle unexpected errors during context setup
            handle_cli_error(e, "Unexpected error during CLI initialization")
            return

        if version:
            click.echo("Spec CLI v0.1.0")
            return

        if ctx.invoked_subcommand is None:
            # No subcommand provided, show help
            from .commands.help import _display_main_help

            # Get SpecContext from Click context storage
            stored_context: Any = ctx.meta.get("spec_context")
            if isinstance(stored_context, SpecContext):
                _display_main_help(stored_context)
            else:
                # Fallback to simple message if context not available
                click.echo("Spec CLI - Use 'spec help' for command information")

    # Add all commands to the CLI app
    cli_app.add_command(init_command, name="init")
    cli_app.add_command(status_command, name="status")
    cli_app.add_command(help_command, name="help")
    cli_app.add_command(gen_command, name="gen")
    cli_app.add_command(regen_command, name="regen")
    cli_app.add_command(add_command, name="add")
    cli_app.add_command(agent_scope_command, name="agent-scope")
    cli_app.add_command(diff_command, name="diff")
    cli_app.add_command(log_command, name="log")
    cli_app.add_command(show_command, name="show")
    cli_app.add_command(commit_command, name="commit")

    return cli_app


def _invoke_app(args: list[str] | None = None) -> None:
    """Invoke the CLI app with given arguments.

    This function is separated to make testing easier.

    Args:
        args: Command line arguments (uses sys.argv if None)
    """
    app(args=args, standalone_mode=False)


def main(args: list[str] | None = None) -> None:
    """Run the main CLI entry point.

    Args:
        args: Command line arguments (uses sys.argv if None)
    """
    try:
        # Handle keyboard interrupt gracefully
        _invoke_app(args)
    except KeyboardInterrupt:
        console = get_console()
        console.print_status("Operation cancelled by user.", "warning")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except click.ClickException as e:
        # Click exceptions are already formatted
        e.show()
        sys.exit(e.exit_code)
    except Exception as e:
        # Handle unexpected errors
        handle_cli_error(e, "CLI execution failed")


if __name__ == "__main__":
    main()
