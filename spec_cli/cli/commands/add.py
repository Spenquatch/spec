"""Spec add command implementation."""

import click

from ..options import dry_run_option, files_argument, force_option, spec_command
from ..utils import validate_file_paths
from .add_command import AddCommand


@spec_command()
@files_argument
@force_option
@dry_run_option
def add_command(
    debug: bool, verbose: bool, files: tuple, force: bool, dry_run: bool
) -> None:
    """Add spec files to Git tracking.

    Adds specification files to the spec repository for version control.
    Files must be in the .specs/ directory to be added.

    Examples:
        spec add .specs/src/main.py/index.md  # Add specific spec file
        spec add .specs/                      # Add all spec files
        spec add .specs/ --force              # Force add ignored files
        spec add .specs/ --dry-run            # Preview what would be added
    """
    try:
        # Convert and validate file paths
        file_paths = validate_file_paths(list(files))

        if not file_paths:
            raise click.BadParameter("No valid file paths provided")

        # Create and execute command
        command = AddCommand()
        result = command.safe_execute(files=file_paths, force=force, dry_run=dry_run)

        # Exit with appropriate code
        if not result["success"]:
            raise click.ClickException(result["message"])

    except click.BadParameter:
        raise  # Re-raise click parameter errors
    except click.ClickException:
        raise  # Re-raise click exceptions
    except Exception as e:
        raise click.ClickException(f"Add failed: {e}") from e
