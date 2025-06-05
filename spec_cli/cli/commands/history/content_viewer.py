"""Content display utilities."""

from pathlib import Path
from typing import Any

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from ....logging.debug import debug_logger
from ....ui.console import get_console

# DataFormatter not used in this module


class ContentViewer:
    """Rich-based content viewer with syntax highlighting."""

    def __init__(self) -> None:
        """Initialize content viewer with Rich console."""
        self.console = get_console()

    # No need for data formatter in this class

    def display_file_content(
        self,
        file_path: Path,
        content: str | None = None,
        line_numbers: bool = True,
        syntax_highlight: bool = True,
    ) -> None:
        """Display file content with Rich formatting.

        Args:
            file_path: Path to the file
            content: File content (reads from file if None)
            line_numbers: Whether to show line numbers
            syntax_highlight: Whether to apply syntax highlighting
        """
        try:
            # Read content if not provided
            if content is None:
                if not file_path.exists():
                    self.console.print(f"[red]File not found: {file_path}[/red]")
                    return

                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with fallback encoding
                    with open(file_path, encoding="latin-1") as f:
                        content = f.read()

            # Determine file type for syntax highlighting
            file_extension = file_path.suffix.lower()
            language = self._get_syntax_language(file_extension)

            # Display file header
            self.console.print(f"\n[bold cyan]Content of {file_path}[/bold cyan]")
            self.console.print("─" * min(80, self.console.console.width))

            # Display content based on type
            if file_extension == ".md" and syntax_highlight:
                # Special handling for Markdown
                self._display_markdown_content(content)
            elif syntax_highlight and language != "text":
                # Syntax highlighted content
                self._display_syntax_highlighted_content(
                    content, language, line_numbers
                )
            else:
                # Plain text content
                self._display_plain_content(content, line_numbers)

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to display file content",
                file=str(file_path),
                error=str(e),
            )
            self.console.print(f"[red]Error displaying file: {e}[/red]")

    def display_spec_content(
        self, spec_data: dict[str, Any], show_metadata: bool = True
    ) -> None:
        """Display spec file content with metadata.

        Args:
            spec_data: Spec file data
            show_metadata: Whether to show metadata
        """
        # Show metadata if requested
        if show_metadata and "metadata" in spec_data:
            self._display_spec_metadata(spec_data["metadata"])

        # Show content sections
        content = spec_data.get("content", "")

        if content:
            # Display as Markdown if it looks like Markdown
            if self._looks_like_markdown(content):
                self._display_markdown_content(content)
            else:
                self._display_plain_content(content)
        else:
            self.console.print("[muted]No content available[/muted]")

    def _display_markdown_content(self, content: str) -> None:
        """Display Markdown content with Rich formatting."""
        try:
            markdown = Markdown(content)
            panel = Panel(markdown, border_style="blue", padding=(1, 2))
            self.console.print(panel)
        except Exception as e:
            debug_logger.log("WARNING", "Failed to render Markdown", error=str(e))
            # Fallback to plain text
            self._display_plain_content(content)

    def _display_syntax_highlighted_content(
        self, content: str, language: str, line_numbers: bool
    ) -> None:
        """Display syntax highlighted content."""
        try:
            syntax = Syntax(
                content,
                language,
                theme="monokai",
                line_numbers=line_numbers,
                word_wrap=True,
            )

            panel = Panel(syntax, border_style="green", padding=(0, 1))

            self.console.print(panel)

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Failed to apply syntax highlighting",
                language=language,
                error=str(e),
            )
            # Fallback to plain text
            self._display_plain_content(content, line_numbers)

    def _display_plain_content(self, content: str, line_numbers: bool = True) -> None:
        """Display plain text content."""
        if line_numbers:
            lines = content.split("\n")
            numbered_content = []

            for i, line in enumerate(lines, 1):
                line_num = f"{i:4d}"
                numbered_content.append(f"[dim]{line_num}[/dim] {line}")

            content = "\n".join(numbered_content)

        panel = Panel(content, border_style="white", padding=(0, 1))

        self.console.print(panel)

    def _display_spec_metadata(self, metadata: dict[str, Any]) -> None:
        """Display spec file metadata."""
        from ....ui.tables import create_key_value_table

        metadata_table = create_key_value_table(metadata, "Spec Metadata")
        metadata_table.print()
        self.console.print()

    def _get_syntax_language(self, file_extension: str) -> str:
        """Get syntax highlighting language from file extension."""
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".md": "markdown",
            ".rst": "rst",
        }

        return language_map.get(file_extension, "text")

    def _looks_like_markdown(self, content: str) -> bool:
        """Check if content looks like Markdown."""
        # Simple heuristic to detect Markdown
        markdown_indicators = [
            "# ",  # Headers
            "## ",
            "### ",
            "- ",  # Lists
            "* ",
            "1. ",  # Numbered lists
            "```",  # Code blocks
            "**",  # Bold
            "*",  # Italic
            "[",  # Links
            "|",  # Tables
        ]

        return any(indicator in content for indicator in markdown_indicators)


# Convenience functions
def display_spec_content(spec_data: dict[str, Any], show_metadata: bool = True) -> None:
    """Display spec file content with metadata."""
    viewer = ContentViewer()
    viewer.display_spec_content(spec_data, show_metadata)


def display_file_content(
    file_path: Path,
    content: str | None = None,
    line_numbers: bool = True,
    syntax_highlight: bool = True,
) -> None:
    """Display file content with Rich formatting."""
    viewer = ContentViewer()
    viewer.display_file_content(file_path, content, line_numbers, syntax_highlight)


def create_content_display() -> ContentViewer:
    """Create a new content viewer instance."""
    return ContentViewer()
