"""Spec commit command implementation."""


import click

from ...core.context import SpecContext
from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ...ui.tables import StatusTable
from ..decorators import context_injection
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
@context_injection
def commit_command(
    context: SpecContext,
    debug: bool,
    verbose: bool,
    message: str,
    all: bool,
    amend: bool,
    dry_run: bool,
) -> None:
    """Commit staged changes to spec repository.

    Creates a new commit with the staged changes in the spec repository.
    All changes must be in the .specs/ directory.

    Args:
        context: SpecContext with settings, console, and progress dependencies
        debug: Debug mode flag
        verbose: Verbose mode flag
        message: Commit message
        all: Auto-stage all modified files flag
        amend: Amend last commit flag
        dry_run: Dry run mode flag

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
        staged_files = repo.get_staged_files()
        unstaged_files = repo.get_unstaged_files()
        untracked_files = repo.get_untracked_files()

        # Auto-stage if requested
        if all:
            _auto_stage_changes(context, repo, unstaged_files)
            # Refresh status after staging
            staged_files = repo.get_staged_files()

        # Check if there are staged changes

        if not staged_files:
            if unstaged_files or untracked_files:
                context.console.print_warning(
                    "No changes staged for commit. Use 'spec add' to stage changes "
                    "or use --all to stage all modified files."
                )
            else:
                context.console.print_message(
                    "No changes to commit. Working directory clean.", "info"
                )
            return

        # Show commit preview
        _show_commit_preview(context, staged_files, message, amend)

        # Dry run mode
        if dry_run:
            context.console.print_message(
                "This is a dry run. No commit would be created.", "info"
            )
            return

        # Confirm commit if not amending
        if not amend and not get_user_confirmation(
            f"Commit {len(staged_files)} files?", default=True
        ):
            context.console.print_message("Commit cancelled", "info")
            return

        # Create commit
        if amend:
            commit_hash = repo.amend_commit(message)
            context.console.print_success(f"Amended commit: {commit_hash[:8]}")
        else:
            commit_hash = repo.commit(message)
            context.console.print_success(f"Created commit: {commit_hash[:8]}")

        # Show commit details
        _show_commit_result(context, repo, commit_hash, staged_files)

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


def _auto_stage_changes(
    context: SpecContext, repo: SpecGitRepository, unstaged_files: list[str]
) -> None:
    """Automatically stage modified and deleted files."""
    # Stage unstaged files
    for file_path in unstaged_files:
        try:
            repo.add_files([file_path])
        except Exception as e:
            debug_logger.log(
                "WARNING", "Failed to stage file", file=file_path, error=str(e)
            )

    total_staged = len(unstaged_files)
    if total_staged > 0:
        context.console.print_message(f"Auto-staged {total_staged} files", "info")


def _show_commit_preview(
    context: SpecContext, staged_files: list[str], message: str, amend: bool
) -> None:
    """Show preview of what will be committed."""
    # Commit info
    action = "Amend commit" if amend else "New commit"
    context.console.print_message(f"\n{action} Preview:", "info")
    context.console.print_message(f"Message: {message}")
    context.console.print_message(f"Files to commit: {len(staged_files)}\n")

    # Show files
    if len(staged_files) <= 15:
        context.console.print_message("Staged files:")
        for file_path in staged_files:
            context.console.print_message(f"  M {file_path}")
    else:
        context.console.print_message("Staged files:")
        for file_path in staged_files[:10]:
            context.console.print_message(f"  M {file_path}")
        context.console.print_message(f"  ... and {len(staged_files) - 10} more files")

    context.console.print_message("")


def _show_commit_result(
    context: SpecContext,
    repo: SpecGitRepository,
    commit_hash: str,
    staged_files: list[str],
) -> None:
    """Show commit result details."""
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
    context.console.print_message("\nNext steps:")
    context.console.print_message("  Use 'spec log' to view commit history")
    context.console.print_message("  Use 'spec diff' to see working directory changes")
