"""Spec gen command implementation."""

import click

from ..options import dry_run_option, files_argument, force_option, spec_command
from ..utils import validate_file_paths
from .gen_command import GenCommand


@spec_command()
@files_argument
@click.option(
    "--template", "-t", default="default", help="Template to use for generation"
)
@click.option(
    "--conflict-strategy",
    type=click.Choice(["backup", "overwrite", "skip", "fail"]),
    default="backup",
    help="How to handle existing spec files",
)
@click.option("--commit", is_flag=True, help="Automatically commit generated files")
@click.option("--message", "-m", help="Commit message (implies --commit)")
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Enable interactive prompts for configuration",
)
@force_option
@dry_run_option
def gen_command(
    debug: bool,
    verbose: bool,
    files: tuple,
    template: str,
    conflict_strategy: str,
    commit: bool,
    message: str,
    interactive: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Generate documentation for source files.

    Creates spec documentation (index.md and history.md) for the specified
    source files using the selected template. Files can be individual source
    files or directories containing source files.

    Examples:
        spec gen src/main.py                    # Generate for single file
        spec gen src/ --template comprehensive  # Generate for directory
        spec gen src/ --interactive             # Interactive configuration
        spec gen src/ --commit -m "Add docs"    # Generate and commit
    """
    try:
        # Convert and validate file paths
        source_files = validate_file_paths(list(files))

        if not source_files:
            raise click.BadParameter("No valid source files provided")

        # Create and execute command
        command = GenCommand()
        result = command.safe_execute(
            files=source_files,
            template=template,
            conflict_strategy=conflict_strategy,
            commit=commit,
            message=message,
            interactive=interactive,
            force=force,
            dry_run=dry_run,
        )

        # Exit with appropriate code
        if not result["success"]:
            raise click.ClickException(result["message"])

    except click.BadParameter:
        raise  # Re-raise click parameter errors
    except click.ClickException:
        raise  # Re-raise click exceptions
    except Exception as e:
        raise click.ClickException(f"Generation failed: {e}") from e
