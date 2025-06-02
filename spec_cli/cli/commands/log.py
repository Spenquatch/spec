"""Spec log command implementation."""


import click

from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..options import optional_files_argument, spec_command
from ..utils import get_spec_repository
from .history import format_commit_log


@spec_command()
@optional_files_argument
@click.option(
    "--limit", "-n", type=int, default=10, help="Limit number of commits to show"
)
@click.option("--oneline", is_flag=True, help="Show compact one-line format")
@click.option("--since", help="Show commits since date (YYYY-MM-DD)")
@click.option("--until", help="Show commits until date (YYYY-MM-DD)")
@click.option("--author", help="Filter commits by author")
@click.option("--grep", help="Filter commits by message content")
@click.option("--stat", is_flag=True, help="Show file change statistics")
def log_command(
    debug: bool,
    verbose: bool,
    files: tuple,
    limit: int,
    oneline: bool,
    since: str,
    until: str,
    author: str,
    grep: str,
    stat: bool,
) -> None:
    """Show commit history.

    Displays the commit history for the spec repository with various
    filtering and formatting options.

    Examples:
        spec log                        # Show recent commits
        spec log --limit 20             # Show 20 commits
        spec log --oneline              # Compact format
        spec log --since 2023-01-01     # Since specific date
        spec log --author "John Doe"     # By specific author
        spec log src/main.py            # History for specific file
    """
    _console = get_console()

    try:
        # Get repository
        repo = get_spec_repository()

        # Convert file arguments
        target_files = list(files) if files else None

        # Build filter options
        filter_options = {
            "limit": limit,
            "since": since,
            "until": until,
            "author": author,
            "grep": grep,
            "files": target_files,
            "include_stats": stat,
        }

        # Remove None values
        filter_options = {k: v for k, v in filter_options.items() if v is not None}

        # Get commit history
        commits = repo.get_commit_history(**filter_options)

        if not commits:
            if target_files:
                show_message(
                    f"No commits found for files: {', '.join(target_files)}", "info"
                )
            else:
                show_message("No commits found in repository", "info")
            return

        # Display header
        if target_files:
            context = f"for {', '.join(target_files)}"
        else:
            context = "for repository"

        filter_desc = []
        if since:
            filter_desc.append(f"since {since}")
        if until:
            filter_desc.append(f"until {until}")
        if author:
            filter_desc.append(f"by {author}")
        if grep:
            filter_desc.append(f"containing '{grep}'")

        if filter_desc:
            context += f" ({', '.join(filter_desc)})"

        show_message(f"Showing {len(commits)} commits {context}:", "info")

        # Format and display commits
        format_commit_log(commits, compact=oneline)

        debug_logger.log(
            "INFO", "Log command completed", commits=len(commits), files=target_files
        )

    except Exception as e:
        debug_logger.log("ERROR", "Log command failed", error=str(e))
        raise click.ClickException(f"Log failed: {e}") from e
