"""Main CLI application with Click framework."""

import sys

# Configure rich-click for beautiful help
from typing import Optional

import click

from ..ui.console import get_console
from .commands import help_command, init_command, status_command
from .commands.add import add_command
from .commands.commit import commit_command
from .commands.diff import diff_command
from .commands.gen import gen_command
from .commands.log import log_command
from .commands.regen import regen_command
from .commands.show import show_command
from .utils import handle_cli_error

try:
    import rich_click as click_impl

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
    if version:
        click.echo("Spec CLI v0.1.0")
        return

    if ctx.invoked_subcommand is None:
        # No subcommand provided, show help
        from .commands.help import _display_main_help

        _display_main_help()


# Add commands to the main group
app.add_command(init_command, name="init")
app.add_command(status_command, name="status")
app.add_command(help_command, name="help")
app.add_command(gen_command, name="gen")
app.add_command(regen_command, name="regen")
app.add_command(add_command, name="add")
app.add_command(diff_command, name="diff")
app.add_command(log_command, name="log")
app.add_command(show_command, name="show")
app.add_command(commit_command, name="commit")


def main(args: Optional[list] = None) -> None:
    """Main CLI entry point.

    Args:
        args: Command line arguments (uses sys.argv if None)
    """
    try:
        # Handle keyboard interrupt gracefully
        app(args=args, standalone_mode=False)
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
