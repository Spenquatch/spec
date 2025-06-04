"""Spec regen command implementation."""

from pathlib import Path

import click

from ...file_processing.conflict_resolver import ConflictResolutionStrategy
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..options import (
    dry_run_option,
    force_option,
    optional_files_argument,
    spec_command,
)
from ..utils import get_user_confirmation, validate_file_paths
from .generation import create_regeneration_workflow, validate_generation_input


@spec_command()
@optional_files_argument
@click.option("--all", is_flag=True, help="Regenerate all existing spec files")
@click.option(
    "--template",
    "-t",
    help="Template to use for regeneration (keeps existing if not specified)",
)
@click.option(
    "--preserve-history",
    is_flag=True,
    default=True,
    help="Preserve history.md files during regeneration",
)
@click.option("--commit", is_flag=True, help="Automatically commit regenerated files")
@click.option("--message", "-m", help="Commit message (implies --commit)")
@force_option
@dry_run_option
def regen_command(
    debug: bool,
    verbose: bool,
    files: tuple,
    all: bool,
    template: str,
    preserve_history: bool,
    commit: bool,
    message: str,
    force: bool,
    dry_run: bool,
) -> None:
    """Regenerate existing spec documentation.

    Updates existing spec files with fresh content while preserving history.
    Can target specific files or regenerate all existing specs.

    Examples:
        spec regen                           # Regenerate all specs
        spec regen src/main.py               # Regenerate specific file
        spec regen --template comprehensive  # Use different template
        spec regen --no-preserve-history     # Recreate history files
    """
    console = get_console()

    try:
        # Determine source files
        if all:
            if files:
                raise click.BadParameter("Cannot specify both --all and file paths")
            source_files = _find_all_spec_sources()
        elif files:
            source_files = validate_file_paths(list(files))
        else:
            # Default to all if no files specified
            source_files = _find_all_spec_sources()

        if not source_files:
            show_message("No source files with existing specs found", "warning")
            return

        # Filter to only files with existing specs
        files_with_specs = _filter_files_with_specs(source_files)

        if not files_with_specs:
            show_message("No existing spec files found for regeneration", "warning")
            if not all:
                show_message("Use 'spec gen' to create new documentation", "info")
            return

        show_message(f"Found {len(files_with_specs)} files with existing specs", "info")

        # Use default template if not specified
        if not template:
            template = "default"

        # Regeneration always overwrites (that's the point)
        conflict_strategy = ConflictResolutionStrategy.OVERWRITE

        # Validate inputs
        validation_result = validate_generation_input(
            files_with_specs, template, conflict_strategy
        )

        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                console.print(f"  • [red]{error}[/red]")
            return

        # Show what will be regenerated
        console.print("\n[bold cyan]Regeneration Preview:[/bold cyan]")
        console.print(f"Template: [yellow]{template}[/yellow]")
        console.print(f"Preserve history: [yellow]{preserve_history}[/yellow]")
        console.print(f"Files to regenerate: [yellow]{len(files_with_specs)}[/yellow]")

        if len(files_with_specs) <= 10:
            console.print("\nFiles:")
            for file_path in files_with_specs:
                console.print(f"  • [path]{file_path}[/path]")
        else:
            console.print("\nFiles:")
            for file_path in files_with_specs[:5]:
                console.print(f"  • [path]{file_path}[/path]")
            console.print(f"  ... and {len(files_with_specs) - 5} more")

        # Confirmation
        if not force and not dry_run:
            if not get_user_confirmation(
                "\nProceed with regeneration? This will overwrite existing content.",
                default=False,
            ):
                show_message("Regeneration cancelled", "info")
                return

        # Dry run mode
        if dry_run:
            _show_regen_dry_run_preview(files_with_specs, template, preserve_history)
            return

        # Set up auto-commit
        auto_commit = commit or bool(message)
        commit_message = message or "Regenerate documentation" if auto_commit else None

        # Create and execute workflow
        workflow = create_regeneration_workflow(
            template_name=template,
            conflict_strategy=conflict_strategy,
            auto_commit=auto_commit,
            commit_message=commit_message,
        )

        show_message(
            f"Regenerating documentation using '{template}' template...", "info"
        )

        result = workflow.regenerate(
            files_with_specs, preserve_history=preserve_history
        )

        # Display results
        if result.success:
            if result.generated_files:
                click.echo(
                    f"✅ Regenerated {len(result.generated_files)} files successfully"
                )
                for gen_file in result.generated_files[:5]:
                    click.echo(f"  - {gen_file}")
                if len(result.generated_files) > 5:
                    click.echo(f"  ... and {len(result.generated_files) - 5} more")
        else:
            click.echo("❌ Regeneration failed")
            if result.failed_files:
                click.echo(f"Failed to regenerate {len(result.failed_files)} files")
                for failed_file in result.failed_files[:3]:
                    click.echo(f"  - {failed_file}")
                if len(result.failed_files) > 3:
                    click.echo(f"  ... and {len(result.failed_files) - 3} more")

        debug_logger.log(
            "INFO",
            "Regeneration command completed",
            files=len(files_with_specs),
            success=result.success,
        )

    except click.BadParameter:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Regeneration command failed", error=str(e))
        raise click.ClickException(f"Regeneration failed: {e}") from e


def _find_all_spec_sources() -> list[Path]:
    """Find all source files that have existing specs."""
    source_files = []
    specs_dir = Path(".specs")

    if not specs_dir.exists():
        return []

    # Find all index.md files and derive source paths
    for index_file in specs_dir.rglob("index.md"):
        try:
            # Convert spec path back to source path
            relative_path = index_file.parent.relative_to(specs_dir)
            potential_source = Path(relative_path)

            if potential_source.exists():
                source_files.append(potential_source)
        except (ValueError, OSError):
            # Skip invalid paths
            continue

    return source_files


def _filter_files_with_specs(source_files: list[Path]) -> list[Path]:
    """Filter files to only those with existing specs."""
    files_with_specs = []

    def get_spec_files_for_source(source_file: Path) -> dict[str, Path]:
        relative_path = (
            source_file.relative_to(Path.cwd())
            if source_file.is_absolute()
            else source_file
        )
        spec_dir = Path(".specs") / relative_path
        return {"index": spec_dir / "index.md", "history": spec_dir / "history.md"}

    for source_file in source_files:
        spec_files = get_spec_files_for_source(source_file)
        if any(f.exists() for f in spec_files.values()):
            files_with_specs.append(source_file)

    return files_with_specs


def _show_regen_dry_run_preview(
    source_files: list[Path], template: str, preserve_history: bool
) -> None:
    """Show dry run preview of regeneration."""
    console = get_console()

    def get_spec_files_for_source(source_file: Path) -> dict[str, Path]:
        relative_path = (
            source_file.relative_to(Path.cwd())
            if source_file.is_absolute()
            else source_file
        )
        spec_dir = Path(".specs") / relative_path
        return {"index": spec_dir / "index.md", "history": spec_dir / "history.md"}

    console.print("\n[bold cyan]Regeneration Dry Run Preview:[/bold cyan]")
    console.print(f"Template: [yellow]{template}[/yellow]")
    console.print(f"Preserve history: [yellow]{preserve_history}[/yellow]")
    console.print(f"Files to regenerate: [yellow]{len(source_files)}[/yellow]\n")

    for source_file in source_files:
        spec_files = get_spec_files_for_source(source_file)

        console.print(f"[bold]{source_file}[/bold]")
        for file_type, spec_file in spec_files.items():
            if spec_file.exists():
                if file_type == "history" and preserve_history:
                    action = "[green]preserve[/green]"
                else:
                    action = "[yellow]regenerate[/yellow]"
                console.print(f"  • {file_type}: [path]{spec_file}[/path] ({action})")
        console.print()

    show_message("This is a dry run. No files would be modified.", "info")
