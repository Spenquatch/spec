"""Rich diff display utilities."""

from typing import Any, Dict, List, Optional

from rich.columns import Columns
from rich.panel import Panel

from ....logging.debug import debug_logger
from ....ui.console import get_console


class DiffViewer:
    """Rich-based diff viewer with syntax highlighting."""

    def __init__(self) -> None:
        self.console = get_console()

    def display_file_diff(
        self,
        filename: str,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
        diff_lines: Optional[List[str]] = None,
        syntax: str = "text",
    ) -> None:
        """Display a file diff with Rich formatting.

        Args:
            filename: Name of the file
            old_content: Original file content
            new_content: New file content
            diff_lines: Pre-formatted diff lines
            syntax: Syntax highlighting language
        """
        # File header
        self.console.print(f"\n[bold cyan]Diff for {filename}[/bold cyan]")
        self.console.print("─" * min(80, self.console.console.width))

        if diff_lines:
            # Use pre-formatted diff lines
            self._display_unified_diff(diff_lines)
        elif old_content is not None and new_content is not None:
            # Generate side-by-side diff
            self._display_side_by_side_diff(old_content, new_content, syntax)
        else:
            self.console.print("[yellow]No diff content available[/yellow]")

    def _display_unified_diff(self, diff_lines: List[str]) -> None:
        """Display unified diff format."""
        for line in diff_lines:
            if line.startswith("+++") or line.startswith("---"):
                self.console.print(f"[bold]{line}[/bold]")
            elif line.startswith("@@"):
                self.console.print(f"[cyan]{line}[/cyan]")
            elif line.startswith("+"):
                self.console.print(f"[green]{line}[/green]")
            elif line.startswith("-"):
                self.console.print(f"[red]{line}[/red]")
            else:
                self.console.print(f"[dim]{line}[/dim]")

    def _display_side_by_side_diff(
        self, old_content: str, new_content: str, syntax: str
    ) -> None:
        """Display side-by-side diff with syntax highlighting."""
        try:
            # Split content into lines
            old_lines = old_content.split("\n")
            new_lines = new_content.split("\n")

            # Simple line-by-line comparison
            max_lines = max(len(old_lines), len(new_lines))

            # Create panels for old and new content
            old_panel_content = []
            new_panel_content = []

            for i in range(max_lines):
                old_line = old_lines[i] if i < len(old_lines) else ""
                new_line = new_lines[i] if i < len(new_lines) else ""

                # Add line numbers and content
                old_line_num = f"{i + 1:4d}" if old_line else "    "
                new_line_num = f"{i + 1:4d}" if new_line else "    "

                if old_line != new_line:
                    if old_line:
                        old_panel_content.append(
                            f"[red]{old_line_num}[/red] [red]{old_line}[/red]"
                        )
                    else:
                        old_panel_content.append(f"[dim]{old_line_num}[/dim]")

                    if new_line:
                        new_panel_content.append(
                            f"[green]{new_line_num}[/green] [green]{new_line}[/green]"
                        )
                    else:
                        new_panel_content.append(f"[dim]{new_line_num}[/dim]")
                else:
                    # Unchanged lines
                    old_panel_content.append(f"[dim]{old_line_num}[/dim] {old_line}")
                    new_panel_content.append(f"[dim]{new_line_num}[/dim] {new_line}")

            # Create side-by-side panels
            old_panel = Panel(
                "\n".join(old_panel_content),
                title="[red]Before[/red]",
                border_style="red",
            )

            new_panel = Panel(
                "\n".join(new_panel_content),
                title="[green]After[/green]",
                border_style="green",
            )

            # Display side by side
            columns = Columns([old_panel, new_panel], equal=True)
            self.console.print(columns)

        except Exception as e:
            debug_logger.log(
                "WARNING", "Failed to display side-by-side diff", error=str(e)
            )
            # Fallback to simple display
            self.console.print("[yellow]Content comparison unavailable[/yellow]")

    def display_diff_summary(self, diff_summary: Dict[str, Any]) -> None:
        """Display diff summary statistics.

        Args:
            diff_summary: Summary data about the diff
        """
        from ....ui.tables import StatusTable

        table = StatusTable("Diff Summary")

        files_changed = diff_summary.get("files_changed", 0)
        insertions = diff_summary.get("insertions", 0)
        deletions = diff_summary.get("deletions", 0)

        table.add_status_item(
            "Files changed",
            str(files_changed),
            status="info" if files_changed > 0 else "muted",
        )
        table.add_status_item(
            "Insertions",
            f"+{insertions}",
            status="success" if insertions > 0 else "muted",
        )
        table.add_status_item(
            "Deletions",
            f"-{deletions}",
            status="warning" if deletions > 0 else "muted",
        )

        table.print()

    def display_no_diff_message(self, context: str = "") -> None:
        """Display message when no differences are found.

        Args:
            context: Additional context for the message
        """
        message = "No differences found"
        if context:
            message += f" {context}"

        self.console.print(f"[muted]{message}[/muted]")


# Convenience functions
def create_diff_view() -> DiffViewer:
    """Create a new diff viewer instance."""
    return DiffViewer()


def display_file_diff(
    filename: str,
    old_content: Optional[str] = None,
    new_content: Optional[str] = None,
    diff_lines: Optional[List[str]] = None,
    syntax: str = "text",
) -> None:
    """Display a file diff with Rich formatting."""
    viewer = DiffViewer()
    viewer.display_file_diff(filename, old_content, new_content, diff_lines, syntax)


def display_unified_diff(diff_lines: List[str]) -> None:
    """Display unified diff format."""
    viewer = DiffViewer()
    viewer._display_unified_diff(diff_lines)
