"""Centralized Rich library imports and configuration for spec-cli UI."""

from typing import Any, List, Optional, Union

# Console and display components
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

# Progress and interactive components
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner
from rich.style import Style
from rich.syntax import Syntax

# Table components
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback


def create_console(
    theme: Optional[Theme] = None,
    width: Optional[int] = None,
    force_terminal: Optional[bool] = None,
    **kwargs: Any,
) -> Console:
    """Create Rich console with consistent configuration.

    Args:
        theme: Rich theme to use
        width: Console width override
        force_terminal: Force terminal detection
        **kwargs: Additional console options

    Returns:
        Configured Rich console instance

    Example:
        console = create_console(width=120, force_terminal=True)
        console.print("Hello, world!", style="bold green")
    """
    console_kwargs = {
        "theme": theme,
        "width": width,
        "force_terminal": force_terminal,
        **kwargs,
    }

    # Remove None values to use Rich defaults
    console_kwargs = {k: v for k, v in console_kwargs.items() if v is not None}

    return Console(**console_kwargs)


def create_progress_bar(
    show_spinner: bool = True,
    show_elapsed: bool = True,
    show_remaining: bool = True,
    **kwargs: Any,
) -> Progress:
    """Create Rich progress bar with standard configuration.

    Args:
        show_spinner: Whether to show spinner column
        show_elapsed: Whether to show elapsed time
        show_remaining: Whether to show remaining time
        **kwargs: Additional progress options

    Returns:
        Configured Rich progress bar

    Example:
        progress = create_progress_bar(show_remaining=False)
        task = progress.add_task("Processing...", total=100)
    """
    columns: List[Any] = []

    if show_spinner:
        columns.append(SpinnerColumn())

    columns.extend(
        [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
        ]
    )

    if show_elapsed:
        columns.append(TimeElapsedColumn())

    if show_remaining:
        columns.append(TimeRemainingColumn())

    return Progress(*columns, **kwargs)


def create_table(
    title: Optional[str] = None,
    show_header: bool = True,
    show_lines: bool = False,
    **kwargs: Any,
) -> Table:
    """Create Rich table with standard configuration.

    Args:
        title: Table title
        show_header: Whether to show header row
        show_lines: Whether to show lines between rows
        **kwargs: Additional table options

    Returns:
        Configured Rich table

    Example:
        table = create_table(title="Results", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
    """
    return Table(title=title, show_header=show_header, show_lines=show_lines, **kwargs)


def create_panel(
    content: Any,
    title: Optional[str] = None,
    style: Optional[Union[str, Style]] = None,
    border_style: Optional[Union[str, Style]] = None,
    **kwargs: Any,
) -> Panel:
    """Create Rich panel with standard configuration.

    Args:
        content: Panel content
        title: Panel title
        style: Panel style
        border_style: Border style
        **kwargs: Additional panel options

    Returns:
        Configured Rich panel

    Example:
        panel = create_panel("Error message", title="Error", style="red")
        console.print(panel)
    """
    panel_kwargs = {"title": title, **kwargs}
    if style is not None:
        panel_kwargs["style"] = style
    if border_style is not None:
        panel_kwargs["border_style"] = border_style

    return Panel(content, **panel_kwargs)


def create_syntax(
    code: str,
    lexer: str = "python",
    theme: str = "monokai",
    line_numbers: bool = True,
    **kwargs: Any,
) -> Syntax:
    """Create Rich syntax highlighter with standard configuration.

    Args:
        code: Code to highlight
        lexer: Syntax lexer to use
        theme: Syntax theme
        line_numbers: Whether to show line numbers
        **kwargs: Additional syntax options

    Returns:
        Configured Rich syntax highlighter

    Example:
        syntax = create_syntax('def hello(): pass', lexer="python")
        console.print(syntax)
    """
    return Syntax(code, lexer=lexer, theme=theme, line_numbers=line_numbers, **kwargs)


def create_spinner(
    name: str = "dots", text: Optional[str] = None, style: Optional[str] = None
) -> Spinner:
    """Create Rich spinner with standard configuration.

    Args:
        name: Spinner animation name
        text: Spinner text (not supported in direct Spinner creation)
        style: Spinner style

    Returns:
        Configured Rich spinner

    Example:
        spinner = create_spinner("dots")
        # Note: text is handled separately when used with Live/Console
    """
    # Rich Spinner constructor is very simple - just takes name and style
    if style is not None:
        return Spinner(name, style=style)
    else:
        return Spinner(name)


# Common Rich components for direct import
__all__ = [
    # Factory functions
    "create_console",
    "create_progress_bar",
    "create_table",
    "create_panel",
    "create_syntax",
    "create_spinner",
    # Direct imports
    "Console",
    "Live",
    "Panel",
    "Progress",
    "Spinner",
    "Style",
    "Syntax",
    "Table",
    "Text",
    "Theme",
    "Traceback",
    # Progress components
    "BarColumn",
    "MofNCompleteColumn",
    "SpinnerColumn",
    "TaskID",
    "TextColumn",
    "TimeElapsedColumn",
    "TimeRemainingColumn",
]
