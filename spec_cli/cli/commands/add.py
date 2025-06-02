"""Spec add command implementation."""

from pathlib import Path
from typing import Dict, List

import click

from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..options import dry_run_option, files_argument, force_option, spec_command
from ..utils import get_spec_repository, validate_file_paths
from .generation import create_add_workflow


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
        # Validate we're in a spec repository
        repo = get_spec_repository()

        # Convert and validate file paths
        file_paths = validate_file_paths(list(files))

        if not file_paths:
            raise click.BadParameter("No valid file paths provided")

        # Expand directories to individual files
        expanded_files = _expand_spec_files(file_paths)

        if not expanded_files:
            show_message("No spec files found in the specified paths", "warning")
            return

        # Filter to only spec files
        spec_files = _filter_spec_files(expanded_files)

        if not spec_files:
            show_message(
                "No files in .specs/ directory found. Use 'spec gen' to create documentation first.",
                "warning",
            )
            return

        show_message(f"Found {len(spec_files)} spec files to add", "info")

        # Check Git status for these files
        git_status = _analyze_git_status(spec_files, repo)

        # Show preview
        _show_add_preview(git_status, dry_run)

        # Dry run mode
        if dry_run:
            show_message("This is a dry run. No files would be added.", "info")
            return

        # Filter to only files that need to be added
        files_to_add = [
            Path(f) for f in git_status["untracked"] + git_status["modified"]
        ]

        if not files_to_add:
            show_message(
                "All specified files are already tracked and up to date", "info"
            )
            return

        # Create and execute workflow
        workflow = create_add_workflow(force=force)

        show_message(f"Adding {len(files_to_add)} files to spec repository...", "info")

        result = workflow.add_files(files_to_add)

        # Display results
        _display_add_results(result)

        debug_logger.log(
            "INFO",
            "Add command completed",
            files=len(files_to_add),
            success=result["success"],
        )

    except click.BadParameter:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Add command failed", error=str(e))
        raise click.ClickException(f"Add failed: {e}") from e


def _expand_spec_files(file_paths: List[Path]) -> List[Path]:
    """Expand directories to individual files."""
    expanded_files = []

    for file_path in file_paths:
        if file_path.is_file():
            expanded_files.append(file_path)
        elif file_path.is_dir():
            # Find all files in directory
            for child_file in file_path.rglob("*"):
                if child_file.is_file():
                    expanded_files.append(child_file)

    return expanded_files


def _filter_spec_files(file_paths: List[Path]) -> List[Path]:
    """Filter to only files in .specs directory."""
    spec_files = []
    specs_dir = Path(".specs")

    for file_path in file_paths:
        try:
            # Check if file is in .specs directory
            file_path.relative_to(specs_dir)
            spec_files.append(file_path)
        except ValueError:
            # File is not in .specs directory
            continue

    return spec_files


def _analyze_git_status(
    spec_files: List[Path], repo: SpecGitRepository
) -> Dict[str, List[str]]:
    """Analyze Git status for spec files."""
    git_status: Dict[str, List[str]] = {
        "untracked": [],
        "modified": [],
        "staged": [],
        "up_to_date": [],
    }

    try:
        # Get overall Git status
        repo.status()

        # Categorize our files based on simple existence checks
        # This is a simplified version since we may not have full git status integration yet
        for file_path in spec_files:
            # For now, assume all files are untracked unless they're already in git
            # This is a simplification for the implementation
            git_status["untracked"].append(str(file_path))

    except Exception as e:
        debug_logger.log("WARNING", "Failed to get Git status", error=str(e))
        # If we can't get status, assume all files are untracked
        git_status["untracked"] = [str(f) for f in spec_files]

    return git_status


def _show_add_preview(git_status: dict, is_dry_run: bool = False) -> None:
    """Show preview of files to be added."""
    console = get_console()

    title = "Add Preview (Dry Run)" if is_dry_run else "Files to Add"
    console.print(f"\n[bold cyan]{title}:[/bold cyan]")

    # Show status entries
    if git_status["untracked"]:
        console.print(f"  New files: [green]{len(git_status['untracked'])}[/green]")

    if git_status["modified"]:
        console.print(
            f"  Modified files: [yellow]{len(git_status['modified'])}[/yellow]"
        )

    if git_status["staged"]:
        console.print(f"  Already staged: [blue]{len(git_status['staged'])}[/blue]")

    if git_status["up_to_date"]:
        console.print(f"  Up to date: [dim]{len(git_status['up_to_date'])}[/dim]")

    # Show file details for small lists
    total_to_add = len(git_status["untracked"]) + len(git_status["modified"])
    if total_to_add > 0 and total_to_add <= 10:
        console.print("\n[bold cyan]Files to be added:[/bold cyan]")

        for file_path in git_status["untracked"]:
            console.print(f"  [green]A[/green] [path]{file_path}[/path] (new file)")

        for file_path in git_status["modified"]:
            console.print(f"  [yellow]M[/yellow] [path]{file_path}[/path] (modified)")


def _display_add_results(result: dict) -> None:
    """Display add operation results."""
    console = get_console()

    # Show summary
    if result["success"]:
        show_message(
            f"Successfully added {len(result['added'])} files to spec repository",
            "success",
        )
    else:
        show_message(f"Add completed with {len(result['failed'])} failures", "warning")

    # Show statistics
    console.print("\n[bold cyan]Add Results:[/bold cyan]")
    console.print(f"  Added files: [green]{len(result['added'])}[/green]")
    console.print(f"  Skipped files: [yellow]{len(result['skipped'])}[/yellow]")
    console.print(f"  Failed files: [red]{len(result['failed'])}[/red]")

    # Show added files
    if result["added"]:
        console.print("\n[bold green]Added files:[/bold green]")
        for file_path in result["added"]:
            console.print(f"  • [path]{file_path}[/path]")

    # Show skipped files
    if result["skipped"]:
        console.print("\n[bold yellow]Skipped files:[/bold yellow]")
        for skip_info in result["skipped"]:
            console.print(
                f"  • [path]{skip_info['file']}[/path]: {skip_info['reason']}"
            )

    # Show failed files
    if result["failed"]:
        console.print("\n[bold red]Failed files:[/bold red]")
        for failure in result["failed"]:
            console.print(f"  • [path]{failure['file']}[/path]: {failure['error']}")

    # Next steps
    if result["added"]:
        console.print("\n[bold cyan]Next steps:[/bold cyan]")
        console.print(
            "  Use [yellow]spec commit -m 'message'[/yellow] to commit these changes"
        )
