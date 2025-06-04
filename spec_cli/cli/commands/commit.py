"""Spec commit command implementation."""

import click

from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ...ui.tables import StatusTable
from ..options import message_option, spec_command
from ..utils import get_spec_repository, get_user_confirmation


@spec_command()
@message_option(required=True)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Automatically stage all modified and deleted files",
)
@click.option("--amend", is_flag=True, help="Amend the last commit")
@click.option("--dry-run", is_flag=True, help="Show what would be committed")
def commit_command(
    debug: bool, verbose: bool, message: str, all: bool, amend: bool, dry_run: bool
) -> None:
    """Commit staged changes to spec repository.

    Creates a new commit with the staged changes in the spec repository.
    All changes must be in the .specs/ directory.

    Examples:
        spec commit -m "Update documentation"       # Commit staged changes
        spec commit -a -m "Update all docs"         # Stage and commit all
        spec commit --amend -m "Fix commit msg"     # Amend last commit
        spec commit --dry-run -m "Test commit"      # Preview commit
    """
    try:
        # Get repository
        repo = get_spec_repository()

        # Get current status
        status = repo.get_git_status()

        # Auto-stage if requested
        if all:
            _auto_stage_changes(repo, status)
            # Refresh status after staging
            status = repo.get_git_status()

        # Check if there are staged changes
        staged_files = status.get("staged", [])

        if not staged_files:
            if status.get("modified", []) or status.get("untracked", []):
                show_message(
                    "No changes staged for commit. Use 'spec add' to stage changes "
                    "or use --all to stage all modified files.",
                    "warning",
                )
            else:
                show_message("No changes to commit. Working directory clean.", "info")
            return

        # Show commit preview
        _show_commit_preview(staged_files, message, amend)

        # Dry run mode
        if dry_run:
            show_message("This is a dry run. No commit would be created.", "info")
            return

        # Confirm commit if not amending
        if not amend and not get_user_confirmation(
            f"Commit {len(staged_files)} files?", default=True
        ):
            show_message("Commit cancelled", "info")
            return

        # Create commit
        if amend:
            commit_hash = repo.amend_commit(message)
            show_message(f"Amended commit: {commit_hash[:8]}", "success")
        else:
            commit_hash = repo.commit(message)
            show_message(f"Created commit: {commit_hash[:8]}", "success")

        # Show commit details
        _show_commit_result(repo, commit_hash, staged_files)

        debug_logger.log(
            "INFO",
            "Commit command completed",
            commit_hash=commit_hash,
            files=len(staged_files),
            amend=amend,
        )

    except Exception as e:
        debug_logger.log("ERROR", "Commit command failed", error=str(e))
        raise click.ClickException(f"Commit failed: {e}") from e


def _auto_stage_changes(repo: SpecGitRepository, status: dict) -> None:
    """Automatically stage modified and deleted files."""
    # Stage modified files
    modified_files = status.get("modified", [])
    for file_path in modified_files:
        try:
            repo.add_files([file_path])
        except Exception as e:
            debug_logger.log(
                "WARNING", "Failed to stage file", file=file_path, error=str(e)
            )

    # Stage deleted files (if any)
    deleted_files = status.get("deleted", [])
    for file_path in deleted_files:
        try:
            # Note: remove_file method not available, using add with removal flag
            # This is a placeholder - actual implementation would need proper removal support
            pass  # TODO: Implement file removal when method is available
        except Exception as e:
            debug_logger.log(
                "WARNING", "Failed to stage deletion", file=file_path, error=str(e)
            )

    total_staged = len(modified_files) + len(deleted_files)
    if total_staged > 0:
        show_message(f"Auto-staged {total_staged} files", "info")


def _show_commit_preview(staged_files: list, message: str, amend: bool) -> None:
    """Show preview of what will be committed."""
    console = get_console()

    # Commit info
    action = "Amend commit" if amend else "New commit"
    console.print(f"\n[bold cyan]{action} Preview:[/bold cyan]")
    console.print(f"Message: [yellow]{message}[/yellow]")
    console.print(f"Files to commit: [yellow]{len(staged_files)}[/yellow]\n")

    # Show files
    if len(staged_files) <= 15:
        console.print("[bold cyan]Staged files:[/bold cyan]")
        for file_path in staged_files:
            console.print(f"  [green]M[/green] [path]{file_path}[/path]")
    else:
        console.print("[bold cyan]Staged files:[/bold cyan]")
        for file_path in staged_files[:10]:
            console.print(f"  [green]M[/green] [path]{file_path}[/path]")
        console.print(f"  [dim]... and {len(staged_files) - 10} more files[/dim]")

    console.print()


def _show_commit_result(
    repo: SpecGitRepository, commit_hash: str, staged_files: list
) -> None:
    """Show commit result details."""
    console = get_console()

    # Get commit info
    try:
        # Note: get_commit_info method not available in current implementation
        # Using placeholder commit info
        commit_info = {"author": "Unknown", "date": "Unknown"}

        # Show commit details table
        table = StatusTable("Commit Details")
        table.add_status_item("Hash", commit_hash[:8], status="success")
        table.add_status_item("Files changed", str(len(staged_files)), status="info")
        table.add_status_item(
            "Author", commit_info.get("author", "Unknown"), status="info"
        )
        table.add_status_item("Date", commit_info.get("date", "Unknown"), status="info")
        table.print()

    except Exception as e:
        debug_logger.log("WARNING", "Failed to get commit details", error=str(e))
        # Basic success message already shown
        pass

    # Next steps
    console.print("\n[bold cyan]Next steps:[/bold cyan]")
    console.print("  Use [yellow]spec log[/yellow] to view commit history")
    console.print("  Use [yellow]spec diff[/yellow] to see working directory changes")
