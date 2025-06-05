"""Git output formatting utilities."""

from datetime import datetime
from typing import Any

from ....ui.console import get_console

# DataFormatter not used in this module
from ....ui.tables import SpecTable


class GitLogFormatter:
    """Formats Git log output with Rich styling."""

    def __init__(self) -> None:
        """Initialize Git log formatter with Rich console."""
        self.console = get_console()

    # No need for data formatter in this class

    def format_commit_log(
        self, commits: list[dict[str, Any]], compact: bool = False
    ) -> None:
        """Format and display commit log.

        Args:
            commits: List of commit dictionaries
            compact: Whether to use compact format
        """
        if not commits:
            self.console.print("[muted]No commits found[/muted]")
            return

        if compact:
            self._format_compact_log(commits)
        else:
            self._format_detailed_log(commits)

    def _format_compact_log(self, commits: list[dict[str, Any]]) -> None:
        """Format compact commit log as table."""
        table = SpecTable(title="Commit History (Compact)")
        table.add_column("Hash", style="yellow", width=10)
        table.add_column("Date", style="dim", width=12)
        table.add_column("Author", style="cyan", width=15)
        table.add_column("Message", style="white")

        for commit in commits:
            # Format date
            try:
                date_obj = datetime.fromisoformat(
                    commit.get("date", "").replace("Z", "+00:00")
                )
                date_str = date_obj.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                date_str = commit.get("date", "Unknown")[:10]

            # Truncate long messages
            message = commit.get("message", "").split("\n")[0]
            if len(message) > 50:
                message = message[:47] + "..."

            table.add_row(
                commit.get("hash", "Unknown")[:8],
                date_str,
                commit.get("author", "Unknown"),
                message,
            )

        table.print()

    def _format_detailed_log(self, commits: list[dict[str, Any]]) -> None:
        """Format detailed commit log."""
        for i, commit in enumerate(commits):
            if i > 0:
                self.console.print()  # Separator between commits

            self._format_single_commit(commit)

    def _format_single_commit(self, commit: dict[str, Any]) -> None:
        """Format a single commit entry."""
        # Commit header
        commit_hash = commit.get("hash", "Unknown")
        self.console.print(f"[bold yellow]commit {commit_hash}[/bold yellow]")

        # Author and date
        author = commit.get("author", "Unknown")
        date = commit.get("date", "Unknown")
        self.console.print(f"[cyan]Author:[/cyan] {author}")
        self.console.print(f"[cyan]Date:[/cyan]   {date}")

        # Message
        message = commit.get("message", "")
        self.console.print()
        for line in message.split("\n"):
            self.console.print(f"    {line}")

        # File changes if available
        if "files" in commit:
            self.console.print()
            self.console.print(f"[dim]Changed files: {len(commit['files'])}[/dim]")
            for file_info in commit["files"][:5]:  # Show first 5 files
                status = file_info.get("status", "M")
                filename = file_info.get("filename", "unknown")

                # Color code status
                if status == "A":
                    status_color = "green"
                elif status == "D":
                    status_color = "red"
                else:
                    status_color = "yellow"

                self.console.print(
                    f"    [{status_color}]{status}[/{status_color}] {filename}"
                )

            if len(commit["files"]) > 5:
                self.console.print(
                    f"    [dim]... and {len(commit['files']) - 5} more files[/dim]"
                )


class GitDiffFormatter:
    """Formats Git diff output with Rich styling."""

    def __init__(self) -> None:
        """Initialize Git diff formatter with Rich console."""
        self.console = get_console()

    def format_diff_output(self, diff_data: dict[str, Any]) -> None:
        """Format and display diff output.

        Args:
            diff_data: Diff data from Git
        """
        if not diff_data or not diff_data.get("files"):
            self.console.print("[muted]No differences found[/muted]")
            return

        # Summary header
        files_changed = len(diff_data["files"])
        self.console.print(
            f"[bold cyan]Diff Summary: {files_changed} files changed[/bold cyan]\n"
        )

        # Format each file's diff
        for file_diff in diff_data["files"]:
            self._format_file_diff(file_diff)

    def _format_file_diff(self, file_diff: dict[str, Any]) -> None:
        """Format diff for a single file."""
        filename = file_diff.get("filename", "unknown")
        status = file_diff.get("status", "modified")

        # File header
        if status == "added":
            self.console.print(f"[bold green]+ {filename}[/bold green] (new file)")
        elif status == "deleted":
            self.console.print(f"[bold red]- {filename}[/bold red] (deleted)")
        else:
            self.console.print(f"[bold yellow]~ {filename}[/bold yellow] (modified)")

        # Diff content
        if "hunks" in file_diff:
            for hunk in file_diff["hunks"]:
                self._format_diff_hunk(hunk)

        self.console.print()  # Separator

    def _format_diff_hunk(self, hunk: dict[str, Any]) -> None:
        """Format a diff hunk."""
        # Hunk header
        header = hunk.get("header", "")
        self.console.print(f"[bold cyan]{header}[/bold cyan]")

        # Hunk lines
        for line in hunk.get("lines", []):
            self._format_diff_line(line)

    def _format_diff_line(self, line: str) -> None:
        """Format a single diff line."""
        if line.startswith("+"):
            self.console.print(f"[green]{line}[/green]")
        elif line.startswith("-"):
            self.console.print(f"[red]{line}[/red]")
        elif line.startswith("@"):
            self.console.print(f"[cyan]{line}[/cyan]")
        else:
            self.console.print(f"[dim]{line}[/dim]")


class CommitFormatter:
    """Formats commit information and statistics."""

    def __init__(self) -> None:
        """Initialize commit formatter with Rich console."""
        self.console = get_console()

    def format_commit_info(self, commit_data: dict[str, Any]) -> None:
        """Format detailed commit information.

        Args:
            commit_data: Commit data from Git
        """
        # Basic commit info
        table = SpecTable(title="Commit Information")
        table.add_column("Property", style="label", ratio=1)
        table.add_column("Value", style="value", ratio=2)

        table.add_row("Hash", commit_data.get("hash", "Unknown"))
        table.add_row("Author", commit_data.get("author", "Unknown"))
        table.add_row("Date", commit_data.get("date", "Unknown"))
        table.add_row("Message", commit_data.get("message", "").split("\n")[0])

        if "parent" in commit_data:
            table.add_row("Parent", commit_data["parent"][:8])

        table.print()

        # Full message if multi-line
        message = commit_data.get("message", "")
        if "\n" in message:
            self.console.print("\n[bold cyan]Full Message:[/bold cyan]")
            for line in message.split("\n"):
                self.console.print(f"  {line}")

        # File statistics
        if "stats" in commit_data:
            self._format_commit_stats(commit_data["stats"])

    def _format_commit_stats(self, stats: dict[str, Any]) -> None:
        """Format commit statistics."""
        self.console.print("\n[bold cyan]Statistics:[/bold cyan]")

        stats_table = SpecTable()
        stats_table.add_column("Metric", style="label")
        stats_table.add_column("Count", style="value")

        stats_table.add_row("Files changed", str(stats.get("files_changed", 0)))
        stats_table.add_row("Insertions", f"+{stats.get('insertions', 0)}")
        stats_table.add_row("Deletions", f"-{stats.get('deletions', 0)}")

        stats_table.print()


# Convenience functions
def format_commit_log(commits: list[dict[str, Any]], compact: bool = False) -> None:
    """Format commit log with Rich styling."""
    formatter = GitLogFormatter()
    formatter.format_commit_log(commits, compact)


def format_diff_output(diff_data: dict[str, Any]) -> None:
    """Format diff output with Rich styling."""
    formatter = GitDiffFormatter()
    formatter.format_diff_output(diff_data)


def format_commit_info(commit_data: dict[str, Any]) -> None:
    """Format commit information with Rich styling."""
    formatter = CommitFormatter()
    formatter.format_commit_info(commit_data)
