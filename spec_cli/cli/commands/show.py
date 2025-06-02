"""Spec show command implementation."""

from pathlib import Path
from typing import Optional

import click

from ...logging.debug import debug_logger
from ...ui.console import get_console
from ...ui.error_display import show_message
from ..options import files_argument, spec_command
from ..utils import get_spec_repository, validate_file_paths
from .history import display_file_content, display_spec_content


@spec_command()
@files_argument
@click.option(
    '--commit',
    help='Show content from specific commit'
)
@click.option(
    '--no-syntax',
    is_flag=True,
    help='Disable syntax highlighting'
)
@click.option(
    '--no-line-numbers',
    is_flag=True,
    help='Hide line numbers'
)
@click.option(
    '--raw',
    is_flag=True,
    help='Show raw content without formatting'
)
def show_command(debug: bool, verbose: bool, files: tuple,
                commit: str, no_syntax: bool, no_line_numbers: bool,
                raw: bool) -> None:
    """Display spec file content.

    Shows the content of spec files with syntax highlighting and formatting.
    Can display current version or content from specific commits.

    Examples:
        spec show .specs/src/main.py/index.md     # Show current content
        spec show .specs/ --commit abc123          # Show from commit
        spec show .specs/file.md --raw             # Show without formatting
    """
    console = get_console()

    try:
        # Validate file paths
        file_paths = validate_file_paths(list(files))

        if not file_paths:
            raise click.BadParameter("No valid file paths provided")

        # Get repository if commit is specified
        repo = None
        if commit:
            repo = get_spec_repository()

        # Process each file
        for i, file_path in enumerate(file_paths):
            if i > 0:
                console.print("\n" + "═" * min(80, console.width))  # Separator

            try:
                if commit:
                    _show_file_from_commit(repo, file_path, commit, no_syntax, no_line_numbers, raw)
                else:
                    _show_current_file(file_path, no_syntax, no_line_numbers, raw)

            except Exception as e:
                debug_logger.log("ERROR", "Failed to show file",
                               file=str(file_path), error=str(e))
                show_message(f"Error showing {file_path}: {e}", "error")

        debug_logger.log("INFO", "Show command completed",
                        files=len(file_paths), commit=commit)

    except click.BadParameter:
        raise  # Re-raise click parameter errors
    except Exception as e:
        debug_logger.log("ERROR", "Show command failed", error=str(e))
        raise click.ClickException(f"Show failed: {e}")

def _show_current_file(file_path: Path,
                      no_syntax: bool,
                      no_line_numbers: bool,
                      raw: bool) -> None:
    """Show current file content."""
    console = get_console()

    if not file_path.exists():
        show_message(f"File not found: {file_path}", "error")
        return

    try:
        # Read file content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # Fallback encoding
            with open(file_path, encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            show_message(f"Error reading file {file_path}: {e}", "error")
            return
    except Exception as e:
        show_message(f"Error reading file {file_path}: {e}", "error")
        return

    if raw:
        # Raw output
        console.print(content)
    else:
        # Check if it's a spec file
        if _is_spec_file(file_path):
            _show_spec_file_content(file_path, content, no_syntax, no_line_numbers)
        else:
            # Regular file display
            display_file_content(
                file_path,
                content=content,
                line_numbers=not no_line_numbers,
                syntax_highlight=not no_syntax
            )

def _show_file_from_commit(repo, file_path: Path, commit: str,
                          no_syntax: bool, no_line_numbers: bool, raw: bool) -> None:
    """Show file content from specific commit."""
    console = get_console()

    try:
        # Get file content from commit
        content = repo.get_file_content_at_commit(str(file_path), commit)

        if content is None:
            show_message(f"File {file_path} not found in commit {commit[:8]}", "warning")
            return

        # Show commit info header
        console.print(f"[bold cyan]File {file_path} at commit {commit[:8]}[/bold cyan]")

        if raw:
            # Raw output
            console.print(content)
        else:
            # Formatted display
            if _is_spec_file(file_path):
                _show_spec_file_content(file_path, content, no_syntax, no_line_numbers)
            else:
                display_file_content(
                    file_path,
                    content=content,
                    line_numbers=not no_line_numbers,
                    syntax_highlight=not no_syntax
                )

    except Exception as e:
        show_message(f"Error retrieving file from commit: {e}", "error")

def _show_spec_file_content(file_path: Path, content: str,
                           no_syntax: bool, no_line_numbers: bool) -> None:
    """Show spec file with special formatting."""
    # Parse spec file metadata if present
    spec_data = _parse_spec_content(content)

    if spec_data and not no_syntax:
        # Use spec-specific display
        display_spec_content(spec_data, show_metadata=True)
    else:
        # Regular file display
        display_file_content(
            file_path,
            content=content,
            line_numbers=not no_line_numbers,
            syntax_highlight=not no_syntax
        )

def _is_spec_file(file_path: Path) -> bool:
    """Check if file is a spec file."""
    try:
        # Check if file is in .specs directory
        file_path.relative_to(Path(".specs"))
        return file_path.suffix == '.md'
    except ValueError:
        return False

def _parse_spec_content(content: str) -> Optional[dict]:
    """Parse spec file content for metadata."""
    try:
        # Simple parsing - look for frontmatter
        lines = content.split('\n')

        if len(lines) > 0 and lines[0].strip() == '---':
            # YAML frontmatter detected
            metadata_lines = []
            content_start = 1

            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    content_start = i + 1
                    break
                metadata_lines.append(line)

            if content_start < len(lines):
                # Parse metadata (simplified)
                metadata = {}
                for line in metadata_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

                return {
                    'metadata': metadata,
                    'content': '\n'.join(lines[content_start:])
                }

        # No frontmatter, return as plain content
        return {
            'metadata': {},
            'content': content
        }

    except Exception:
        # Fallback to None if parsing fails
        return None
