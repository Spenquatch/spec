"""Spec diff command implementation."""

import click

from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ...ui.tables import StatusTable
from ..options import optional_files_argument, spec_command
from ..utils import get_spec_repository
from .history import format_diff_output


@spec_command()
@optional_files_argument
@click.option("--cached", is_flag=True, help="Show diff of staged changes")
@click.option("--commit", help="Compare with specific commit (hash or reference)")
@click.option(
    "--unified",
    "-u",
    type=int,
    default=3,
    help="Number of context lines for unified diff",
)
@click.option("--no-color", is_flag=True, help="Disable color output")
@click.option("--stat", is_flag=True, help="Show diffstat summary only")
def diff_command(
    debug: bool,
    verbose: bool,
    files: tuple,
    cached: bool,
    commit: str,
    unified: int,
    no_color: bool,
    stat: bool,
) -> None:
    """Show differences between versions.

    Displays changes in spec files between different versions, working
    directory and staging area, or between commits.

    Examples:
        spec diff                           # Working directory vs staging
        spec diff --cached                  # Staging vs last commit
        spec diff --commit abc123           # Working vs specific commit
        spec diff src/main.py               # Specific file differences
        spec diff --stat                    # Summary statistics only
    """
    _console = get_console()

    try:
        # Get repository
        repo = get_spec_repository()

        # Convert file arguments
        target_files = list(files) if files else None

        # Get diff data based on options
        if cached:
            # Staged changes vs last commit
            diff_data = repo.get_staged_diff(files=target_files, unified=unified)
            context = "staged changes"
        elif commit:
            # Working directory vs specific commit
            diff_data = repo.get_commit_diff(
                commit, files=target_files, unified=unified
            )
            context = f"changes since commit {commit[:8]}"
        else:
            # Working directory vs staging area (default)
            diff_data = repo.get_working_diff(files=target_files, unified=unified)
            context = "working directory changes"

        # Display results
        if not diff_data or not diff_data.get("files"):
            show_message(f"No differences found in {context}", "info")
            return

        if stat:
            # Show summary statistics only
            _display_diff_stats(diff_data)
        else:
            # Show full diff
            show_message(f"Showing {context}:", "info")

            if no_color:
                _display_plain_diff(diff_data)
            else:
                format_diff_output(diff_data)

        debug_logger.log(
            "INFO",
            "Diff command completed",
            files=len(diff_data.get("files", [])),
            cached=cached,
            commit=commit,
        )

    except Exception as e:
        debug_logger.log("ERROR", "Diff command failed", error=str(e))
        raise click.ClickException(f"Diff failed: {e}") from e


def _display_diff_stats(diff_data: dict) -> None:
    """Display diff statistics summary."""
    console = get_console()
    files = diff_data.get("files", [])

    if not files:
        console.print("[muted]No changes found[/muted]")
        return

    # Calculate statistics
    total_insertions = 0
    total_deletions = 0
    files_changed = len(files)

    for file_data in files:
        total_insertions += file_data.get("insertions", 0)
        total_deletions += file_data.get("deletions", 0)

    # Display summary table
    stats_table = StatusTable("Diff Statistics")
    stats_table.add_status_item("Files changed", str(files_changed), status="info")
    stats_table.add_status_item("Insertions", f"+{total_insertions}", status="success")
    stats_table.add_status_item("Deletions", f"-{total_deletions}", status="warning")
    stats_table.print()

    # Show per-file statistics
    if files_changed <= 10:  # Show details for small number of files
        console.print("\n[bold cyan]File Details:[/bold cyan]")
        for file_data in files:
            filename = file_data.get("filename", "unknown")
            insertions = file_data.get("insertions", 0)
            deletions = file_data.get("deletions", 0)

            changes = f"+{insertions}/-{deletions}"
            console.print(f"  [path]{filename}[/path] ({changes})")


def _display_plain_diff(diff_data: dict) -> None:
    """Display diff without color formatting."""
    console = get_console()

    for file_data in diff_data.get("files", []):
        filename = file_data.get("filename", "unknown")
        console.print(f"\nFile: {filename}")
        console.print("=" * len(f"File: {filename}"))

        if "hunks" in file_data:
            for hunk in file_data["hunks"]:
                # Hunk header
                header = hunk.get("header", "")
                console.print(header)

                # Hunk lines
                for line in hunk.get("lines", []):
                    console.print(line)

        console.print()  # Separator
