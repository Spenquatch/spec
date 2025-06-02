# Slice 13C: Diff & History Suite

## Goal

Implement the `diff`, `log`, `show`, and `commit` commands on top of the Git adapter with integration tests for version control workflows.

## Context

Completing the CLI implementation with commands that provide visibility into the spec repository's history and changes. These commands leverage the Git operations from slice-9 to provide powerful version control features for documentation tracking.

## Scope

**Included in this slice:**
- `diff` command for showing changes between versions
- `log` command for displaying commit history
- `show` command for displaying spec content
- `commit` command for committing staged changes
- Git integration with rich diff formatting
- History navigation and content display
- Integration tests for version control workflows

**NOT included in this slice:**
- Advanced Git operations (branching, merging)
- Interactive Git workflows (rebase, etc.)
- External diff tools integration
- Complex history rewriting

## Prerequisites

**Required modules that must exist:**
- `spec_cli.cli.app` (CLI application from slice-13a)
- `spec_cli.cli.options` (Shared CLI options from slice-13a)
- `spec_cli.cli.commands.generation` (Generation workflows from slice-13b)
- `spec_cli.git.repository` (GitRepository from slice-9)
- `spec_cli.ui.formatters` (Data formatters from slice-12c)
- `spec_cli.ui.tables` (Table formatters from slice-12c)

**Required functions/classes:**
- `app`, CLI framework from slice-13a-core-cli-scaffold
- `spec_command`, `optional_files_argument`, `message_option` from slice-13a-core-cli-scaffold
- `GitRepository` from slice-9-git-operations
- `DataFormatter`, `MessageFormatter` from slice-12c-formatter-error-views
- `SpecTable`, `create_simple_table` from slice-12c-formatter-error-views

## Files to Create

```
spec_cli/cli/commands/
├── diff.py             # spec diff command
├── log.py              # spec log command
├── show.py             # spec show command
├── commit.py           # spec commit command
└── history/
    ├── __init__.py     # History utilities
    ├── formatters.py   # Git output formatting
    ├── diff_viewer.py  # Rich diff display
    └── content_viewer.py # Content display utilities
```

## Implementation Steps

### Step 1: Create spec_cli/cli/commands/history/__init__.py

```python
"""History and version control utilities.

This package provides utilities for displaying Git history, diffs,
and content with Rich formatting.
"""

from .formatters import (
    GitLogFormatter, GitDiffFormatter, CommitFormatter,
    format_commit_log, format_diff_output, format_commit_info
)
from .diff_viewer import (
    DiffViewer, create_diff_view, display_file_diff,
    display_unified_diff
)
from .content_viewer import (
    ContentViewer, display_spec_content, display_file_content,
    create_content_display
)

__all__ = [
    "GitLogFormatter",
    "GitDiffFormatter",
    "CommitFormatter",
    "format_commit_log",
    "format_diff_output",
    "format_commit_info",
    "DiffViewer",
    "create_diff_view",
    "display_file_diff",
    "display_unified_diff",
    "ContentViewer",
    "display_spec_content",
    "display_file_content",
    "create_content_display",
]
```

### Step 2: Create spec_cli/cli/commands/history/formatters.py

```python
"""Git output formatting utilities."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....ui.console import get_console
from ....ui.tables import SpecTable, create_simple_table
from ....ui.formatters import DataFormatter
from ....logging.debug import debug_logger

class GitLogFormatter:
    """Formats Git log output with Rich styling."""
    
    def __init__(self):
        self.console = get_console()
        self.data_formatter = DataFormatter()
    
    def format_commit_log(self, commits: List[Dict[str, Any]], 
                         compact: bool = False) -> None:
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
    
    def _format_compact_log(self, commits: List[Dict[str, Any]]) -> None:
        """Format compact commit log as table."""
        table = SpecTable(title="Commit History (Compact)")
        table.add_column("Hash", style="yellow", width=10)
        table.add_column("Date", style="dim", width=12)
        table.add_column("Author", style="cyan", width=15)
        table.add_column("Message", style="white")
        
        for commit in commits:
            # Format date
            try:
                date_obj = datetime.fromisoformat(commit.get('date', '').replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                date_str = commit.get('date', 'Unknown')[:10]
            
            # Truncate long messages
            message = commit.get('message', '').split('\n')[0]
            if len(message) > 50:
                message = message[:47] + "..."
            
            table.add_row(
                commit.get('hash', 'Unknown')[:8],
                date_str,
                commit.get('author', 'Unknown'),
                message
            )
        
        table.print()
    
    def _format_detailed_log(self, commits: List[Dict[str, Any]]) -> None:
        """Format detailed commit log."""
        for i, commit in enumerate(commits):
            if i > 0:
                self.console.print()  # Separator between commits
            
            self._format_single_commit(commit)
    
    def _format_single_commit(self, commit: Dict[str, Any]) -> None:
        """Format a single commit entry."""
        # Commit header
        commit_hash = commit.get('hash', 'Unknown')
        self.console.print(f"[bold yellow]commit {commit_hash}[/bold yellow]")
        
        # Author and date
        author = commit.get('author', 'Unknown')
        date = commit.get('date', 'Unknown')
        self.console.print(f"[cyan]Author:[/cyan] {author}")
        self.console.print(f"[cyan]Date:[/cyan]   {date}")
        
        # Message
        message = commit.get('message', '')
        self.console.print()
        for line in message.split('\n'):
            self.console.print(f"    {line}")
        
        # File changes if available
        if 'files' in commit:
            self.console.print()
            self.console.print(f"[dim]Changed files: {len(commit['files'])}[/dim]")
            for file_info in commit['files'][:5]:  # Show first 5 files
                status = file_info.get('status', 'M')
                filename = file_info.get('filename', 'unknown')
                
                # Color code status
                if status == 'A':
                    status_color = "green"
                elif status == 'D':
                    status_color = "red"
                else:
                    status_color = "yellow"
                
                self.console.print(f"    [{status_color}]{status}[/{status_color}] {filename}")
            
            if len(commit['files']) > 5:
                self.console.print(f"    [dim]... and {len(commit['files']) - 5} more files[/dim]")

class GitDiffFormatter:
    """Formats Git diff output with Rich styling."""
    
    def __init__(self):
        self.console = get_console()
    
    def format_diff_output(self, diff_data: Dict[str, Any]) -> None:
        """Format and display diff output.
        
        Args:
            diff_data: Diff data from Git
        """
        if not diff_data or not diff_data.get('files'):
            self.console.print("[muted]No differences found[/muted]")
            return
        
        # Summary header
        files_changed = len(diff_data['files'])
        self.console.print(f"[bold cyan]Diff Summary: {files_changed} files changed[/bold cyan]\n")
        
        # Format each file's diff
        for file_diff in diff_data['files']:
            self._format_file_diff(file_diff)
    
    def _format_file_diff(self, file_diff: Dict[str, Any]) -> None:
        """Format diff for a single file."""
        filename = file_diff.get('filename', 'unknown')
        status = file_diff.get('status', 'modified')
        
        # File header
        if status == 'added':
            self.console.print(f"[bold green]+ {filename}[/bold green] (new file)")
        elif status == 'deleted':
            self.console.print(f"[bold red]- {filename}[/bold red] (deleted)")
        else:
            self.console.print(f"[bold yellow]~ {filename}[/bold yellow] (modified)")
        
        # Diff content
        if 'hunks' in file_diff:
            for hunk in file_diff['hunks']:
                self._format_diff_hunk(hunk)
        
        self.console.print()  # Separator
    
    def _format_diff_hunk(self, hunk: Dict[str, Any]) -> None:
        """Format a diff hunk."""
        # Hunk header
        header = hunk.get('header', '')
        self.console.print(f"[bold cyan]{header}[/bold cyan]")
        
        # Hunk lines
        for line in hunk.get('lines', []):
            self._format_diff_line(line)
    
    def _format_diff_line(self, line: str) -> None:
        """Format a single diff line."""
        if line.startswith('+'):
            self.console.print(f"[green]{line}[/green]")
        elif line.startswith('-'):
            self.console.print(f"[red]{line}[/red]")
        elif line.startswith('@'):
            self.console.print(f"[cyan]{line}[/cyan]")
        else:
            self.console.print(f"[dim]{line}[/dim]")

class CommitFormatter:
    """Formats commit information and statistics."""
    
    def __init__(self):
        self.console = get_console()
    
    def format_commit_info(self, commit_data: Dict[str, Any]) -> None:
        """Format detailed commit information.
        
        Args:
            commit_data: Commit data from Git
        """
        # Basic commit info
        table = SpecTable(title="Commit Information")
        table.add_column("Property", style="label", ratio=1)
        table.add_column("Value", style="value", ratio=2)
        
        table.add_row("Hash", commit_data.get('hash', 'Unknown'))
        table.add_row("Author", commit_data.get('author', 'Unknown'))
        table.add_row("Date", commit_data.get('date', 'Unknown'))
        table.add_row("Message", commit_data.get('message', '').split('\n')[0])
        
        if 'parent' in commit_data:
            table.add_row("Parent", commit_data['parent'][:8])
        
        table.print()
        
        # Full message if multi-line
        message = commit_data.get('message', '')
        if '\n' in message:
            self.console.print("\n[bold cyan]Full Message:[/bold cyan]")
            for line in message.split('\n'):
                self.console.print(f"  {line}")
        
        # File statistics
        if 'stats' in commit_data:
            self._format_commit_stats(commit_data['stats'])
    
    def _format_commit_stats(self, stats: Dict[str, Any]) -> None:
        """Format commit statistics."""
        self.console.print("\n[bold cyan]Statistics:[/bold cyan]")
        
        stats_table = SpecTable()
        stats_table.add_column("Metric", style="label")
        stats_table.add_column("Count", style="value")
        
        stats_table.add_row("Files changed", str(stats.get('files_changed', 0)))
        stats_table.add_row("Insertions", f"+{stats.get('insertions', 0)}")
        stats_table.add_row("Deletions", f"-{stats.get('deletions', 0)}")
        
        stats_table.print()

# Convenience functions
def format_commit_log(commits: List[Dict[str, Any]], compact: bool = False) -> None:
    """Format commit log with Rich styling."""
    formatter = GitLogFormatter()
    formatter.format_commit_log(commits, compact)

def format_diff_output(diff_data: Dict[str, Any]) -> None:
    """Format diff output with Rich styling."""
    formatter = GitDiffFormatter()
    formatter.format_diff_output(diff_data)

def format_commit_info(commit_data: Dict[str, Any]) -> None:
    """Format commit information with Rich styling."""
    formatter = CommitFormatter()
    formatter.format_commit_info(commit_data)
```

### Step 3: Create spec_cli/cli/commands/history/diff_viewer.py

```python
"""Rich diff display utilities."""

from typing import List, Dict, Any, Optional
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns
from ....ui.console import get_console
from ....ui.formatters import DataFormatter
from ....logging.debug import debug_logger

class DiffViewer:
    """Rich-based diff viewer with syntax highlighting."""
    
    def __init__(self):
        self.console = get_console()
    
    def display_file_diff(self, 
                         filename: str,
                         old_content: Optional[str] = None,
                         new_content: Optional[str] = None,
                         diff_lines: Optional[List[str]] = None,
                         syntax: str = "text") -> None:
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
        self.console.print("─" * min(80, self.console.width))
        
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
            if line.startswith('+++') or line.startswith('---'):
                self.console.print(f"[bold]{line}[/bold]")
            elif line.startswith('@@'):
                self.console.print(f"[cyan]{line}[/cyan]")
            elif line.startswith('+'):
                self.console.print(f"[green]{line}[/green]")
            elif line.startswith('-'):
                self.console.print(f"[red]{line}[/red]")
            else:
                self.console.print(f"[dim]{line}[/dim]")
    
    def _display_side_by_side_diff(self, 
                                  old_content: str,
                                  new_content: str,
                                  syntax: str) -> None:
        """Display side-by-side diff with syntax highlighting."""
        try:
            # Split content into lines
            old_lines = old_content.split('\n')
            new_lines = new_content.split('\n')
            
            # Simple line-by-line comparison
            max_lines = max(len(old_lines), len(new_lines))
            
            # Create panels for old and new content
            old_panel_content = []
            new_panel_content = []
            
            for i in range(max_lines):
                old_line = old_lines[i] if i < len(old_lines) else ""
                new_line = new_lines[i] if i < len(new_lines) else ""
                
                # Add line numbers and content
                old_line_num = f"{i+1:4d}" if old_line else "    "
                new_line_num = f"{i+1:4d}" if new_line else "    "
                
                if old_line != new_line:
                    if old_line:
                        old_panel_content.append(f"[red]{old_line_num}[/red] [red]{old_line}[/red]")
                    else:
                        old_panel_content.append(f"[dim]{old_line_num}[/dim]")
                    
                    if new_line:
                        new_panel_content.append(f"[green]{new_line_num}[/green] [green]{new_line}[/green]")
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
                border_style="red"
            )
            
            new_panel = Panel(
                "\n".join(new_panel_content),
                title="[green]After[/green]",
                border_style="green"
            )
            
            # Display side by side
            columns = Columns([old_panel, new_panel], equal=True)
            self.console.print(columns)
            
        except Exception as e:
            debug_logger.log("WARNING", "Failed to display side-by-side diff", error=str(e))
            # Fallback to simple display
            self.console.print("[yellow]Content comparison unavailable[/yellow]")
    
    def display_diff_summary(self, diff_summary: Dict[str, Any]) -> None:
        """Display diff summary statistics.
        
        Args:
            diff_summary: Summary data about the diff
        """
        from ....ui.tables import StatusTable
        
        table = StatusTable("Diff Summary")
        
        files_changed = diff_summary.get('files_changed', 0)
        insertions = diff_summary.get('insertions', 0)
        deletions = diff_summary.get('deletions', 0)
        
        table.add_status("Files changed", str(files_changed), 
                        status_type="info" if files_changed > 0 else "muted")
        table.add_status("Insertions", f"+{insertions}",
                        status_type="success" if insertions > 0 else "muted")
        table.add_status("Deletions", f"-{deletions}",
                        status_type="warning" if deletions > 0 else "muted")
        
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

def display_file_diff(filename: str, 
                     old_content: Optional[str] = None,
                     new_content: Optional[str] = None,
                     diff_lines: Optional[List[str]] = None,
                     syntax: str = "text") -> None:
    """Display a file diff with Rich formatting."""
    viewer = DiffViewer()
    viewer.display_file_diff(filename, old_content, new_content, diff_lines, syntax)

def display_unified_diff(diff_lines: List[str]) -> None:
    """Display unified diff format."""
    viewer = DiffViewer()
    viewer._display_unified_diff(diff_lines)
```

### Step 4: Create spec_cli/cli/commands/history/content_viewer.py

```python
"""Content display utilities."""

from typing import Optional, Dict, Any
from pathlib import Path
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown
from ....ui.console import get_console
from ....ui.formatters import DataFormatter
from ....logging.debug import debug_logger

class ContentViewer:
    """Rich-based content viewer with syntax highlighting."""
    
    def __init__(self):
        self.console = get_console()
        self.data_formatter = DataFormatter()
    
    def display_file_content(self, 
                           file_path: Path,
                           content: Optional[str] = None,
                           line_numbers: bool = True,
                           syntax_highlight: bool = True) -> None:
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
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with fallback encoding
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
            
            # Determine file type for syntax highlighting
            file_extension = file_path.suffix.lower()
            language = self._get_syntax_language(file_extension)
            
            # Display file header
            self.console.print(f"\n[bold cyan]Content of {file_path}[/bold cyan]")
            self.console.print("─" * min(80, self.console.width))
            
            # Display content based on type
            if file_extension == '.md' and syntax_highlight:
                # Special handling for Markdown
                self._display_markdown_content(content)
            elif syntax_highlight and language != "text":
                # Syntax highlighted content
                self._display_syntax_highlighted_content(content, language, line_numbers)
            else:
                # Plain text content
                self._display_plain_content(content, line_numbers)
        
        except Exception as e:
            debug_logger.log("ERROR", "Failed to display file content", 
                           file=str(file_path), error=str(e))
            self.console.print(f"[red]Error displaying file: {e}[/red]")
    
    def display_spec_content(self, 
                           spec_data: Dict[str, Any],
                           show_metadata: bool = True) -> None:
        """Display spec file content with metadata.
        
        Args:
            spec_data: Spec file data
            show_metadata: Whether to show metadata
        """
        # Show metadata if requested
        if show_metadata and 'metadata' in spec_data:
            self._display_spec_metadata(spec_data['metadata'])
        
        # Show content sections
        content = spec_data.get('content', '')
        
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
            panel = Panel(
                markdown,
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(panel)
        except Exception as e:
            debug_logger.log("WARNING", "Failed to render Markdown", error=str(e))
            # Fallback to plain text
            self._display_plain_content(content)
    
    def _display_syntax_highlighted_content(self, 
                                          content: str,
                                          language: str,
                                          line_numbers: bool) -> None:
        """Display syntax highlighted content."""
        try:
            syntax = Syntax(
                content,
                language,
                theme="monokai",
                line_numbers=line_numbers,
                word_wrap=True
            )
            
            panel = Panel(
                syntax,
                border_style="green",
                padding=(0, 1)
            )
            
            self.console.print(panel)
        
        except Exception as e:
            debug_logger.log("WARNING", "Failed to apply syntax highlighting", 
                           language=language, error=str(e))
            # Fallback to plain text
            self._display_plain_content(content, line_numbers)
    
    def _display_plain_content(self, content: str, line_numbers: bool = True) -> None:
        """Display plain text content."""
        if line_numbers:
            lines = content.split('\n')
            numbered_content = []
            
            for i, line in enumerate(lines, 1):
                line_num = f"{i:4d}"
                numbered_content.append(f"[dim]{line_num}[/dim] {line}")
            
            content = "\n".join(numbered_content)
        
        panel = Panel(
            content,
            border_style="white",
            padding=(0, 1)
        )
        
        self.console.print(panel)
    
    def _display_spec_metadata(self, metadata: Dict[str, Any]) -> None:
        """Display spec file metadata."""
        from ....ui.tables import create_key_value_table
        
        metadata_table = create_key_value_table(
            metadata,
            "Spec Metadata"
        )
        metadata_table.print()
        self.console.print()
    
    def _get_syntax_language(self, file_extension: str) -> str:
        """Get syntax highlighting language from file extension."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.md': 'markdown',
            '.rst': 'rst',
        }
        
        return language_map.get(file_extension, 'text')
    
    def _looks_like_markdown(self, content: str) -> bool:
        """Check if content looks like Markdown."""
        # Simple heuristic to detect Markdown
        markdown_indicators = [
            '# ',     # Headers
            '## ',
            '### ',
            '- ',     # Lists
            '* ',
            '1. ',    # Numbered lists
            '```',    # Code blocks
            '**',     # Bold
            '*',      # Italic
            '[',      # Links
            '|',      # Tables
        ]
        
        return any(indicator in content for indicator in markdown_indicators)

# Convenience functions
def display_spec_content(spec_data: Dict[str, Any], show_metadata: bool = True) -> None:
    """Display spec file content with metadata."""
    viewer = ContentViewer()
    viewer.display_spec_content(spec_data, show_metadata)

def display_file_content(file_path: Path, 
                        content: Optional[str] = None,
                        line_numbers: bool = True,
                        syntax_highlight: bool = True) -> None:
    """Display file content with Rich formatting."""
    viewer = ContentViewer()
    viewer.display_file_content(file_path, content, line_numbers, syntax_highlight)

def create_content_display() -> ContentViewer:
    """Create a new content viewer instance."""
    return ContentViewer()
```

### Step 5: Create spec_cli/cli/commands/diff.py

```python
"""Spec diff command implementation."""

import click
from pathlib import Path
from typing import List, Optional
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...logging.debug import debug_logger
from ..options import spec_command, optional_files_argument
from ..utils import get_spec_repository
from .history import format_diff_output, create_diff_view

@spec_command()
@optional_files_argument
@click.option(
    '--cached',
    is_flag=True,
    help='Show diff of staged changes'
)
@click.option(
    '--commit',
    help='Compare with specific commit (hash or reference)'
)
@click.option(
    '--unified', '-u',
    type=int,
    default=3,
    help='Number of context lines for unified diff'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable color output'
)
@click.option(
    '--stat',
    is_flag=True,
    help='Show diffstat summary only'
)
def diff_command(debug: bool, verbose: bool, files: tuple,
                cached: bool, commit: str, unified: int,
                no_color: bool, stat: bool) -> None:
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
    console = get_console()
    
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
            diff_data = repo.get_commit_diff(commit, files=target_files, unified=unified)
            context = f"changes since commit {commit[:8]}"
        else:
            # Working directory vs staging area (default)
            diff_data = repo.get_working_diff(files=target_files, unified=unified)
            context = "working directory changes"
        
        # Display results
        if not diff_data or not diff_data.get('files'):
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
        
        debug_logger.log("INFO", "Diff command completed",
                        files=len(diff_data.get('files', [])),
                        cached=cached, commit=commit)
        
    except Exception as e:
        debug_logger.log("ERROR", "Diff command failed", error=str(e))
        raise click.ClickException(f"Diff failed: {e}")

def _display_diff_stats(diff_data: dict) -> None:
    """Display diff statistics summary."""
    from ....ui.tables import StatusTable
    
    console = get_console()
    files = diff_data.get('files', [])
    
    if not files:
        console.print("[muted]No changes found[/muted]")
        return
    
    # Calculate statistics
    total_insertions = 0
    total_deletions = 0
    files_changed = len(files)
    
    for file_data in files:
        total_insertions += file_data.get('insertions', 0)
        total_deletions += file_data.get('deletions', 0)
    
    # Display summary table
    stats_table = StatusTable("Diff Statistics")
    stats_table.add_status("Files changed", str(files_changed), status_type="info")
    stats_table.add_status("Insertions", f"+{total_insertions}", status_type="success")
    stats_table.add_status("Deletions", f"-{total_deletions}", status_type="warning")
    stats_table.print()
    
    # Show per-file statistics
    if files_changed <= 10:  # Show details for small number of files
        console.print("\n[bold cyan]File Details:[/bold cyan]")
        for file_data in files:
            filename = file_data.get('filename', 'unknown')
            insertions = file_data.get('insertions', 0)
            deletions = file_data.get('deletions', 0)
            
            changes = f"+{insertions}/-{deletions}"
            console.print(f"  [path]{filename}[/path] ({changes})")

def _display_plain_diff(diff_data: dict) -> None:
    """Display diff without color formatting."""
    console = get_console()
    
    for file_data in diff_data.get('files', []):
        filename = file_data.get('filename', 'unknown')
        console.print(f"\nFile: {filename}")
        console.print("=" * len(f"File: {filename}"))
        
        if 'hunks' in file_data:
            for hunk in file_data['hunks']:
                # Hunk header
                header = hunk.get('header', '')
                console.print(header)
                
                # Hunk lines
                for line in hunk.get('lines', []):
                    console.print(line)
        
        console.print()  # Separator
```

### Step 6: Create spec_cli/cli/commands/log.py

```python
"""Spec log command implementation."""

import click
from typing import List, Optional
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...logging.debug import debug_logger
from ..options import spec_command, optional_files_argument
from ..utils import get_spec_repository
from .history import format_commit_log

@spec_command()
@optional_files_argument
@click.option(
    '--limit', '-n',
    type=int,
    default=10,
    help='Limit number of commits to show'
)
@click.option(
    '--oneline',
    is_flag=True,
    help='Show compact one-line format'
)
@click.option(
    '--since',
    help='Show commits since date (YYYY-MM-DD)'
)
@click.option(
    '--until',
    help='Show commits until date (YYYY-MM-DD)'
)
@click.option(
    '--author',
    help='Filter commits by author'
)
@click.option(
    '--grep',
    help='Filter commits by message content'
)
@click.option(
    '--stat',
    is_flag=True,
    help='Show file change statistics'
)
def log_command(debug: bool, verbose: bool, files: tuple,
               limit: int, oneline: bool, since: str, until: str,
               author: str, grep: str, stat: bool) -> None:
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
    console = get_console()
    
    try:
        # Get repository
        repo = get_spec_repository()
        
        # Convert file arguments
        target_files = list(files) if files else None
        
        # Build filter options
        filter_options = {
            'limit': limit,
            'since': since,
            'until': until,
            'author': author,
            'grep': grep,
            'files': target_files,
            'include_stats': stat
        }
        
        # Remove None values
        filter_options = {k: v for k, v in filter_options.items() if v is not None}
        
        # Get commit history
        commits = repo.get_commit_history(**filter_options)
        
        if not commits:
            if target_files:
                show_message(f"No commits found for files: {', '.join(target_files)}", "info")
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
        
        debug_logger.log("INFO", "Log command completed",
                        commits=len(commits), files=target_files)
        
    except Exception as e:
        debug_logger.log("ERROR", "Log command failed", error=str(e))
        raise click.ClickException(f"Log failed: {e}")
```

### Step 7: Create spec_cli/cli/commands/show.py

```python
"""Spec show command implementation."""

import click
from pathlib import Path
from typing import Optional
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...logging.debug import debug_logger
from ..options import spec_command, files_argument
from ..utils import validate_file_paths, get_spec_repository
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
        
    except click.BadParameter as e:
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
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # Fallback encoding
            with open(file_path, 'r', encoding='latin-1') as f:
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
```

### Step 8: Create spec_cli/cli/commands/commit.py

```python
"""Spec commit command implementation."""

import click
from typing import Optional
from ...ui.console import get_console
from ...ui.formatters import show_message
from ...ui.tables import StatusTable
from ...logging.debug import debug_logger
from ..options import spec_command, message_option
from ..utils import get_spec_repository, get_user_confirmation

@spec_command()
@message_option(required=True)
@click.option(
    '--all', '-a',
    is_flag=True,
    help='Automatically stage all modified and deleted files'
)
@click.option(
    '--amend',
    is_flag=True,
    help='Amend the last commit'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be committed'
)
def commit_command(debug: bool, verbose: bool, message: str,
                  all: bool, amend: bool, dry_run: bool) -> None:
    """Commit staged changes to spec repository.
    
    Creates a new commit with the staged changes in the spec repository.
    All changes must be in the .specs/ directory.
    
    Examples:
        spec commit -m "Update documentation"       # Commit staged changes
        spec commit -a -m "Update all docs"         # Stage and commit all
        spec commit --amend -m "Fix commit msg"     # Amend last commit
        spec commit --dry-run -m "Test commit"      # Preview commit
    """
    console = get_console()
    
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
        staged_files = status.get('staged', [])
        
        if not staged_files:
            if status.get('modified', []) or status.get('untracked', []):
                show_message(
                    "No changes staged for commit. Use 'spec add' to stage changes "
                    "or use --all to stage all modified files.",
                    "warning"
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
        
        debug_logger.log("INFO", "Commit command completed",
                        commit_hash=commit_hash,
                        files=len(staged_files),
                        amend=amend)
        
    except Exception as e:
        debug_logger.log("ERROR", "Commit command failed", error=str(e))
        raise click.ClickException(f"Commit failed: {e}")

def _auto_stage_changes(repo, status: dict) -> None:
    """Automatically stage modified and deleted files."""
    console = get_console()
    
    # Stage modified files
    modified_files = status.get('modified', [])
    for file_path in modified_files:
        try:
            repo.add_file(file_path)
        except Exception as e:
            debug_logger.log("WARNING", "Failed to stage file",
                           file=file_path, error=str(e))
    
    # Stage deleted files (if any)
    deleted_files = status.get('deleted', [])
    for file_path in deleted_files:
        try:
            repo.remove_file(file_path)
        except Exception as e:
            debug_logger.log("WARNING", "Failed to stage deletion",
                           file=file_path, error=str(e))
    
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

def _show_commit_result(repo, commit_hash: str, staged_files: list) -> None:
    """Show commit result details."""
    console = get_console()
    
    # Get commit info
    try:
        commit_info = repo.get_commit_info(commit_hash)
        
        # Show commit details table
        table = StatusTable("Commit Details")
        table.add_status("Hash", commit_hash[:8], status_type="success")
        table.add_status("Files changed", str(len(staged_files)), status_type="info")
        table.add_status("Author", commit_info.get('author', 'Unknown'), status_type="info")
        table.add_status("Date", commit_info.get('date', 'Unknown'), status_type="info")
        table.print()
        
    except Exception as e:
        debug_logger.log("WARNING", "Failed to get commit details", error=str(e))
        # Basic success message already shown
        pass
    
    # Next steps
    console.print("\n[bold cyan]Next steps:[/bold cyan]")
    console.print("  Use [yellow]spec log[/yellow] to view commit history")
    console.print("  Use [yellow]spec diff[/yellow] to see working directory changes")
```

### Step 9: Update spec_cli/cli/app.py

```python
"""Main CLI application with Click framework."""

# Add imports for new history commands
from .commands.diff import diff_command
from .commands.log import log_command
from .commands.show import show_command
from .commands.commit import commit_command

# Add commands to the main group (after existing commands)
app.add_command(diff_command, name="diff")
app.add_command(log_command, name="log")
app.add_command(show_command, name="show")
app.add_command(commit_command, name="commit")

# (rest of the file remains the same)
```

## Test Requirements

Create integration tests for diff and history commands:

### Test Cases (16 tests total)

**Diff Command Tests:**
1. **test_diff_command_shows_working_directory_changes**
2. **test_diff_command_shows_staged_changes**
3. **test_diff_command_compares_with_commit**
4. **test_diff_command_stat_summary_only**

**Log Command Tests:**
5. **test_log_command_shows_commit_history**
6. **test_log_command_filters_by_date_and_author**
7. **test_log_command_shows_file_specific_history**
8. **test_log_command_oneline_format**

**Show Command Tests:**
9. **test_show_command_displays_current_file_content**
10. **test_show_command_displays_file_from_commit**
11. **test_show_command_handles_spec_file_formatting**
12. **test_show_command_raw_output_mode**

**Commit Command Tests:**
13. **test_commit_command_creates_new_commit**
14. **test_commit_command_auto_stages_changes**
15. **test_commit_command_amends_last_commit**
16. **test_commit_command_dry_run_preview**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/cli/commands/test_diff.py tests/unit/cli/commands/test_log.py tests/unit/cli/commands/test_show.py tests/unit/cli/commands/test_commit.py tests/unit/cli/commands/history/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/cli/commands/ --cov=spec_cli.cli.commands --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/cli/commands/

# Check code formatting
poetry run ruff check spec_cli/cli/commands/
poetry run ruff format spec_cli/cli/commands/

# Test diff and history commands
python -m spec_cli diff --help
python -m spec_cli log --help
python -m spec_cli show --help
python -m spec_cli commit --help

# Test CLI functionality (in test directory with some commits)
cd test_area
python -m spec_cli init
echo "print('hello')" > test.py
python -m spec_cli gen test.py
python -m spec_cli add .specs/
python -m spec_cli commit -m "Initial documentation"
echo "print('world')" > test.py
python -m spec_cli gen test.py
python -m spec_cli diff
python -m spec_cli diff --cached
python -m spec_cli add .specs/
python -m spec_cli commit -m "Update documentation"
python -m spec_cli log
python -m spec_cli log --oneline
python -m spec_cli show .specs/test.py/index.md

# Test history formatting
python -c "
from spec_cli.cli.commands.history import format_commit_log

# Test commit log formatting
commits = [
    {
        'hash': 'abc123def456',
        'author': 'Test User',
        'date': '2023-12-01T10:00:00Z',
        'message': 'Test commit message'
    }
]

format_commit_log(commits, compact=False)
print('Commit log formatting works')
"

# Test diff viewer
python -c "
from spec_cli.cli.commands.history.diff_viewer import DiffViewer

viewer = DiffViewer()
print('Diff viewer initialized successfully')

# Test content viewer
from spec_cli.cli.commands.history.content_viewer import ContentViewer

content_viewer = ContentViewer()
print('Content viewer initialized successfully')
"

# Test Git integration
python -c "
from spec_cli.cli.commands.history.formatters import GitLogFormatter

formatter = GitLogFormatter()
print('Git log formatter created successfully')
"
```

## Definition of Done

- [ ] Diff command with working directory, staged, and commit comparisons
- [ ] Log command with filtering and formatting options
- [ ] Show command with syntax highlighting and commit history support
- [ ] Commit command with staging and amend functionality
- [ ] Rich diff formatting with syntax highlighting
- [ ] Git history navigation and content display
- [ ] Integration with Git operations from slice-9
- [ ] Comprehensive error handling and user feedback
- [ ] All 16 integration tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Complete version control workflow support

## Next Steps

This completes the **CLI Implementation** with all 24 slices! The spec CLI now provides:

### Complete Feature Set:
1. **Repository Management**: `init`, `status` commands
2. **Content Generation**: `gen`, `regen` commands with template system
3. **Version Control**: `add`, `commit`, `diff`, `log`, `show` commands
4. **Rich UI**: Beautiful terminal output, progress tracking, error display
5. **Advanced Features**: Conflict resolution, batch processing, interactive prompts

### Architecture Achievements:
- **24 focused slices** across 5 phases
- **316+ comprehensive tests** with 80%+ coverage
- **Complete modular architecture** with dependency injection
- **Rich terminal UI** replacing all emoji usage
- **Git integration** with isolated repository pattern
- **Template system** ready for AI integration
- **Error handling** with user-friendly messages
- **Type safety** with full mypy compliance

The refactored spec CLI is now production-ready with a maintainable, extensible architecture!