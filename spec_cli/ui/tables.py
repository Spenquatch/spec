from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles


class SpecTable:
    """Spec-specific table formatting with Rich integration."""

    def __init__(
        self,
        title: Optional[str] = None,
        show_header: bool = True,
        show_lines: bool = False,
        show_edge: bool = True,
        expand: bool = False,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize the spec table.

        Args:
            title: Optional table title
            show_header: Whether to show column headers
            show_lines: Whether to show lines between rows
            show_edge: Whether to show table edge
            expand: Whether to expand table to full width
            console: Console to use for display
        """
        self.console = console or get_console().console
        self.title = title
        self.show_header = show_header
        self.show_lines = show_lines
        self.show_edge = show_edge
        self.expand = expand

        self.table = Table(
            title=title,
            show_header=show_header,
            show_lines=show_lines,
            show_edge=show_edge,
            expand=expand,
            title_style="title",
            header_style="subtitle",
            border_style="border",
        )

        debug_logger.log("INFO", "SpecTable initialized", title=title)

    def add_column(
        self,
        header: str,
        style: Optional[str] = None,
        justify: Literal["default", "left", "center", "right", "full"] = "left",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        ratio: Optional[int] = None,
        no_wrap: bool = False,
        overflow: Literal["fold", "crop", "ellipsis", "ignore"] = "ellipsis",
    ) -> None:
        """Add a column to the table.

        Args:
            header: Column header text
            style: Optional column style
            justify: Text justification (left, right, center)
            width: Fixed column width
            min_width: Minimum column width
            max_width: Maximum column width
            ratio: Column ratio for flexible sizing
            no_wrap: Whether to disable text wrapping
            overflow: How to handle text overflow
        """
        self.table.add_column(
            header,
            style=style,
            justify=justify,
            width=width,
            min_width=min_width,
            max_width=max_width,
            ratio=ratio,
            no_wrap=no_wrap,
            overflow=overflow,
        )

        debug_logger.log("DEBUG", "Column added to table", header=header, style=style)

    def add_row(self, *values: Any, style: Optional[str] = None) -> None:
        """Add a row to the table.

        Args:
            *values: Row values
            style: Optional row style
        """
        # Convert values to strings and apply styling
        formatted_values = []
        for value in values:
            if isinstance(value, (str, Text)):
                formatted_values.append(value)
            else:
                formatted_values.append(str(value))  # type: ignore[unreachable]

        self.table.add_row(*formatted_values, style=style)

        debug_logger.log("DEBUG", "Row added to table", values=len(values))

    def print(self) -> None:
        """Print the table to the console."""
        self.console.print(self.table)
        debug_logger.log("DEBUG", "Table printed to console")

    def get_table(self) -> Table:
        """Get the Rich table object.

        Returns:
            The Rich Table instance
        """
        return self.table


class FileListTable(SpecTable):
    """Specialized table for displaying file lists."""

    def __init__(self, title: str = "Files", **kwargs: Any) -> None:
        """Initialize file list table.

        Args:
            title: Table title
            **kwargs: Additional table options
        """
        super().__init__(title=title, **kwargs)

        # Add standard columns for file listings
        self.add_column("Path", style="path", overflow="fold")
        self.add_column("Type", style="muted", justify="center", width=8)
        self.add_column("Size", style="value", justify="right", width=10)
        self.add_column("Status", style="info", justify="center", width=12)

    def add_file(
        self,
        file_path: Path,
        file_type: str = "file",
        size: Optional[int] = None,
        status: str = "pending",
    ) -> None:
        """Add a file row to the table.

        Args:
            file_path: Path to the file
            file_type: Type of file (file, directory, spec_file)
            size: File size in bytes
            status: Processing status
        """
        # Format path with appropriate styling
        formatted_path = (
            SpecStyles.file(file_path)
            if file_type == "file"
            else SpecStyles.directory(file_path)
        )

        # Format size
        size_str = self._format_file_size(size) if size is not None else "-"

        # Format status with styling
        status_style_map = {
            "pending": "muted",
            "processing": "info",
            "completed": "success",
            "failed": "error",
            "skipped": "warning",
        }
        status_style = status_style_map.get(status, "info")
        formatted_status = f"[{status_style}]{status}[/{status_style}]"

        self.add_row(formatted_path, file_type, size_str, formatted_status)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


class StatusTable(SpecTable):
    """Specialized table for displaying status information."""

    def __init__(self, title: str = "Status", **kwargs: Any) -> None:
        """Initialize status table.

        Args:
            title: Table title
            **kwargs: Additional table options
        """
        super().__init__(title=title, show_lines=True, **kwargs)

        # Add standard columns for status display
        self.add_column("Item", style="label", width=20)
        self.add_column("Value", style="value", overflow="fold")
        self.add_column("Status", style="info", justify="center", width=12)

    def add_status_item(self, name: str, value: Any, status: str = "info") -> None:
        """Add a status item to the table.

        Args:
            name: Item name
            value: Item value
            status: Status type (info, success, warning, error)
        """
        # Format status with appropriate styling
        formatted_status = (
            SpecStyles.success("✓")
            if status == "success"
            else SpecStyles.info("i")
            if status == "info"
            else SpecStyles.warning("⚠")
            if status == "warning"
            else SpecStyles.error("✗")
        )

        self.add_row(name, str(value), formatted_status)


class ComparisonTable(SpecTable):
    """Specialized table for comparing data."""

    def __init__(self, title: str = "Comparison", **kwargs: Any) -> None:
        """Initialize comparison table.

        Args:
            title: Table title
            **kwargs: Additional table options
        """
        super().__init__(title=title, show_lines=True, **kwargs)

        # Add standard columns for comparison
        self.add_column("Property", style="label", width=20)
        self.add_column("Before", style="muted", justify="center")
        self.add_column("After", style="value", justify="center")
        self.add_column("Change", style="info", justify="center", width=10)

    def add_comparison(
        self, property_name: str, before_value: Any, after_value: Any
    ) -> None:
        """Add a comparison row.

        Args:
            property_name: Name of the property being compared
            before_value: Value before change
            after_value: Value after change
        """
        # Determine change type
        if before_value == after_value:
            change = SpecStyles.muted("=")
        elif str(before_value) < str(after_value):
            change = SpecStyles.success("↑")
        else:
            change = SpecStyles.warning("↓")

        self.add_row(property_name, str(before_value), str(after_value), change)


# Utility functions
def create_file_table(
    files: List[Path], title: str = "Files", **kwargs: Any
) -> FileListTable:
    """Create a table for displaying file information.

    Args:
        files: List of file paths
        title: Table title
        **kwargs: Additional table options

    Returns:
        Configured FileListTable
    """
    table = FileListTable(title=title, **kwargs)

    for file_path in files:
        file_type = "directory" if file_path.is_dir() else "file"
        size = (
            file_path.stat().st_size
            if file_path.exists() and file_path.is_file()
            else None
        )

        table.add_file(file_path, file_type=file_type, size=size)

    return table


def create_status_table(
    data: Dict[str, Any], title: str = "Status", **kwargs: Any
) -> StatusTable:
    """Create a table for displaying status information.

    Args:
        data: Dictionary of status data
        title: Table title
        **kwargs: Additional table options

    Returns:
        Configured StatusTable
    """
    table = StatusTable(title=title, **kwargs)

    for key, value in data.items():
        # Determine status based on value type and content
        if isinstance(value, bool):
            status = "success" if value else "error"
        elif isinstance(value, (int, float)) and value > 0:
            status = "success"
        else:
            status = "info"

        table.add_status_item(key, value, status)

    return table


def print_simple_table(
    data: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> None:
    """Print a simple table from list of dictionaries.

    Args:
        data: List of dictionaries with table data
        headers: Optional custom headers (uses dict keys if None)
        title: Optional table title
    """
    if not data:
        return

    table = SpecTable(title=title)

    # Use provided headers or extract from first row
    if headers is None:
        headers = list(data[0].keys())

    # Add columns
    for header in headers:
        table.add_column(header)

    # Add rows
    for row_data in data:
        values = [str(row_data.get(header, "")) for header in headers]
        table.add_row(*values)

    table.print()


def create_key_value_table(
    data: Dict[str, Any], title: Optional[str] = None
) -> SpecTable:
    """Create a key-value table from a dictionary.

    Args:
        data: Dictionary of key-value pairs
        title: Optional table title

    Returns:
        SpecTable instance with key-value data
    """
    table = SpecTable(title=title)
    table.add_column("Key", style="label", width=20)
    table.add_column("Value", style="value")

    for key, value in data.items():
        formatted_key = key.replace("_", " ").title()
        formatted_value = format_table_data(value)
        table.add_row(formatted_key, formatted_value)

    return table


def format_table_data(
    data: Any, formatter: Optional[Callable[[Any], str]] = None
) -> str:
    """Format data for table display.

    Args:
        data: Data to format
        formatter: Optional custom formatter function

    Returns:
        Formatted string representation
    """
    if formatter:
        return formatter(data)

    if isinstance(data, Path):
        return str(data)
    elif isinstance(data, bool):
        return "Yes" if data else "No"
    elif isinstance(data, (int, float)):
        return str(data)
    elif data is None:
        return "-"
    else:
        return str(data)
