"""Spec gen command implementation."""

import click
from pathlib import Path
from typing import List
from ...ui.console import get_console
from ...ui.error_display import show_message, format_data
from ...logging.debug import debug_logger
from ..options import spec_command, files_argument, force_option, dry_run_option
from ..utils import validate_file_paths, get_user_confirmation
from .generation import (
    create_generation_workflow,
    validate_generation_input,
    select_template,
    confirm_generation,
)
from ...file_processing.conflict_resolver import ConflictResolutionStrategy


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
    console = get_console()

    try:
        # Convert and validate file paths
        source_files = validate_file_paths(list(files))

        if not source_files:
            raise click.BadParameter("No valid source files provided")

        # Expand directories to individual files
        expanded_files = _expand_source_files(source_files)

        if not expanded_files:
            show_message("No processable files found in the specified paths", "warning")
            return

        show_message(f"Found {len(expanded_files)} files to process", "info")

        # Configure conflict strategy
        strategy_map = {
            "backup": ConflictResolutionStrategy.BACKUP_AND_REPLACE,
            "overwrite": ConflictResolutionStrategy.OVERWRITE,
            "skip": ConflictResolutionStrategy.SKIP,
            "fail": ConflictResolutionStrategy.FAIL,
        }
        conflict_enum = strategy_map[conflict_strategy]

        # Interactive configuration
        if interactive:
            template = select_template(template)

            # Confirm configuration
            if not confirm_generation(expanded_files, template, conflict_enum):
                show_message("Generation cancelled by user", "info")
                return

        # Validate inputs
        validation_result = validate_generation_input(
            expanded_files, template, conflict_enum
        )

        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                console.print(f"  • [red]{error}[/red]")
            return

        # Show warnings if any
        if validation_result["warnings"]:
            show_message("Warnings:", "warning")
            for warning in validation_result["warnings"]:
                console.print(f"  • [yellow]{warning}[/yellow]")

            if not force and not get_user_confirmation(
                "Continue despite warnings?", default=True
            ):
                show_message("Generation cancelled", "info")
                return

        # Dry run mode
        if dry_run:
            _show_dry_run_preview(expanded_files, template, conflict_enum)
            return

        # Set up auto-commit
        auto_commit = commit or bool(message)
        commit_message = message or "Generate documentation" if auto_commit else None

        # Create and execute workflow
        workflow = create_generation_workflow(
            template_name=template,
            conflict_strategy=conflict_enum,
            auto_commit=auto_commit,
            commit_message=commit_message,
        )

        show_message(f"Generating documentation using '{template}' template...", "info")

        result = workflow.generate(expanded_files)

        # Display results
        _display_generation_results(result)

        debug_logger.log(
            "INFO",
            "Generation command completed",
            files=len(expanded_files),
            success=result.success,
        )

    except click.BadParameter as e:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Generation command failed", error=str(e))
        raise click.ClickException(f"Generation failed: {e}")


def _expand_source_files(source_files: List[Path]) -> List[Path]:
    """Expand directories to individual source files."""
    from .generation.validation import GenerationValidator

    validator = GenerationValidator()
    expanded_files = []

    for file_path in source_files:
        if file_path.is_file():
            if validator._is_processable_file(file_path):
                expanded_files.append(file_path)
        elif file_path.is_dir():
            processable_files = validator._get_processable_files_in_directory(file_path)
            expanded_files.extend(processable_files)

    return expanded_files


def _show_dry_run_preview(
    source_files: List[Path],
    template: str,
    conflict_strategy: ConflictResolutionStrategy,
) -> None:
    """Show dry run preview of what would be generated."""
    console = get_console()

    console.print("\n[bold cyan]Dry Run Preview:[/bold cyan]")
    console.print(f"Template: [yellow]{template}[/yellow]")
    console.print(f"Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]")
    console.print(f"Files to process: [yellow]{len(source_files)}[/yellow]\n")

    # Helper to get spec files
    def get_spec_files_for_source(source_file: Path):
        relative_path = (
            source_file.relative_to(Path.cwd())
            if source_file.is_absolute()
            else source_file
        )
        spec_dir = Path(".specs") / relative_path
        return {"index": spec_dir / "index.md", "history": spec_dir / "history.md"}

    for source_file in source_files:
        spec_files = get_spec_files_for_source(source_file)

        console.print(f"[bold]{source_file}[/bold]")
        for file_type, spec_file in spec_files.items():
            status = (
                "[yellow]exists[/yellow]"
                if spec_file.exists()
                else "[green]new[/green]"
            )
            console.print(f"  • {file_type}: [path]{spec_file}[/path] ({status})")
        console.print()

    show_message("This is a dry run. No files would be modified.", "info")


def _display_generation_results(result) -> None:
    """Display generation results."""
    console = get_console()

    # Show summary
    if result.success:
        show_message(
            f"Generation completed successfully in {result.total_processing_time:.2f}s",
            "success",
        )
    else:
        show_message(
            f"Generation completed with errors in {result.total_processing_time:.2f}s",
            "warning",
        )

    # Show statistics using simple formatting
    console.print(f"\n[bold cyan]Generation Statistics:[/bold cyan]")
    console.print(f"  Generated files: [green]{len(result.generated_files)}[/green]")
    console.print(f"  Skipped files: [yellow]{len(result.skipped_files)}[/yellow]")
    console.print(f"  Failed files: [red]{len(result.failed_files)}[/red]")
    console.print(
        f"  Conflicts resolved: [blue]{len(result.conflicts_resolved)}[/blue]"
    )

    # Show generated files
    if result.generated_files:
        console.print("\n[bold green]Generated files:[/bold green]")
        for file_path in result.generated_files:
            console.print(f"  • [path]{file_path}[/path]")

    # Show failed files
    if result.failed_files:
        console.print("\n[bold red]Failed files:[/bold red]")
        for failure in result.failed_files:
            console.print(f"  • [path]{failure['file']}[/path]: {failure['error']}")

    # Show conflicts
    if result.conflicts_resolved:
        console.print("\n[bold yellow]Conflicts resolved:[/bold yellow]")
        for conflict in result.conflicts_resolved:
            if conflict["type"] == "backup":
                console.print(
                    f"  • Backed up [path]{conflict['original']}[/path] to [path]{conflict['backup']}[/path]"
                )
            elif conflict["type"] == "overwrite":
                console.print(f"  • Overwrote [path]{conflict['file']}[/path]")
