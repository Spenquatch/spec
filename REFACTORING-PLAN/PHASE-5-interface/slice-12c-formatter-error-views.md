# Slice 12C: Formatter & Error Views

## Goal

Create table/tree render utilities and error panel with trace highlighting, providing comprehensive Rich-based formatting for data display and error presentation with isolated, testable components.

## Context

Building on the console foundation (slice-12a) and progress components (slice-12b), this slice implements sophisticated data formatting and error display capabilities. It provides the final piece of the Rich UI system, creating reusable components for displaying structured data, error information, and diagnostic output with proper styling integration.

## Scope

**Included in this slice:**
- Table formatters for structured data display
- Tree view components for hierarchical data
- Error panel system with stack trace highlighting
- Diagnostic information formatters
- Data validation and presentation utilities
- Rich markup utilities for complex formatting
- Isolated, testable formatting components

**NOT included in this slice:**
- CLI command integration (comes in slice-13)
- Interactive prompts or dialogs
- Real-time data streaming displays
- Complex animation or transitions

## Prerequisites

**Required modules that must exist:**
- `spec_cli.ui.console` (SpecConsole from slice-12a)
- `spec_cli.ui.theme` (SpecTheme from slice-12a)
- `spec_cli.ui.styles` (SpecStyles from slice-12a)
- `spec_cli.exceptions` (All exception types for error display)
- `spec_cli.logging.debug` (debug_logger for formatter tracking)

**Required functions/classes:**
- `SpecConsole` and `get_console()` from slice-12a-console-theme
- `SpecTheme`, `SpecStyles` from slice-12a-console-theme
- All exception classes from slice-1-exceptions
- Debug logging capabilities from slice-2-logging

## Files to Create

```
spec_cli/ui/
├── tables.py           # Table formatting utilities
├── trees.py           # Tree view components
├── error_display.py   # Error panels and trace formatting
└── formatters.py      # General data formatting utilities
```

## Implementation Steps

### Step 1: Create spec_cli/ui/tables.py

```python
from typing import Any, Dict, List, Optional, Union, Callable
from rich.table import Table
from rich.console import Console
from rich.text import Text
from pathlib import Path
from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles

class SpecTable:
    """Spec-specific table formatting with Rich integration."""
    
    def __init__(self,
                 title: Optional[str] = None,
                 show_header: bool = True,
                 show_lines: bool = False,
                 show_edge: bool = True,
                 expand: bool = False,
                 console: Optional[Console] = None):
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
            header_style="label",
            border_style="border"
        )
        
        self.columns: List[Dict[str, Any]] = []
        self.rows: List[List[Any]] = []
        
        debug_logger.log("INFO", "SpecTable initialized",
                        title=title, show_header=show_header)
    
    def add_column(self,
                   header: str,
                   style: Optional[str] = None,
                   justify: str = "left",
                   width: Optional[int] = None,
                   min_width: Optional[int] = None,
                   max_width: Optional[int] = None,
                   ratio: Optional[int] = None,
                   no_wrap: bool = False) -> None:
        """Add a column to the table.
        
        Args:
            header: Column header text
            style: Optional style for column content
            justify: Text justification (left, center, right)
            width: Fixed column width
            min_width: Minimum column width
            max_width: Maximum column width
            ratio: Column width ratio
            no_wrap: Whether to prevent text wrapping
        """
        column_config = {
            "header": header,
            "style": style,
            "justify": justify,
            "width": width,
            "min_width": min_width,
            "max_width": max_width,
            "ratio": ratio,
            "no_wrap": no_wrap,
        }
        
        self.columns.append(column_config)
        
        self.table.add_column(
            header,
            style=style,
            justify=justify,
            width=width,
            min_width=min_width,
            max_width=max_width,
            ratio=ratio,
            no_wrap=no_wrap
        )
        
        debug_logger.log("DEBUG", "Column added to table",
                        header=header, style=style)
    
    def add_row(self, *values: Any, style: Optional[str] = None) -> None:
        """Add a row to the table.
        
        Args:
            *values: Column values for the row
            style: Optional style for the entire row
        """
        # Convert values to strings and apply formatting
        formatted_values = []
        for i, value in enumerate(values):
            if value is None:
                formatted_values.append("[muted]—[/muted]")
            else:
                formatted_values.append(str(value))
        
        self.rows.append(formatted_values)
        self.table.add_row(*formatted_values, style=style)
        
        debug_logger.log("DEBUG", "Row added to table",
                        columns=len(formatted_values))
    
    def add_separator(self) -> None:
        """Add a separator row to the table."""
        if self.show_lines:
            # Rich will handle line separation automatically
            pass
        else:
            # Add an empty row with border styling
            empty_row = [""] * len(self.columns)
            self.table.add_row(*empty_row, style="border")
    
    def print(self) -> None:
        """Print the table to the console."""
        self.console.print(self.table)
        debug_logger.log("DEBUG", "Table printed",
                        rows=len(self.rows), columns=len(self.columns))
    
    def get_table(self) -> Table:
        """Get the Rich Table object.
        
        Returns:
            Rich Table instance
        """
        return self.table

class FileListTable(SpecTable):
    """Specialized table for displaying file lists."""
    
    def __init__(self, title: str = "Files", **kwargs):
        """Initialize file list table.
        
        Args:
            title: Table title
            **kwargs: Additional arguments for SpecTable
        """
        super().__init__(title=title, **kwargs)
        
        # Add standard file columns
        self.add_column("Path", style="path", ratio=3)
        self.add_column("Type", style="muted", width=10)
        self.add_column("Size", style="value", justify="right", width=10)
        self.add_column("Status", style="info", width=12)
    
    def add_file(self,
                file_path: Path,
                file_type: str = "file",
                size: Optional[int] = None,
                status: str = "ready") -> None:
        """Add a file to the table.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (file, directory, spec_file)
            size: File size in bytes
            status: File status
        """
        # Format path based on type
        if file_type == "directory":
            formatted_path = SpecStyles.directory(file_path)
        elif file_type == "spec_file":
            formatted_path = SpecStyles.spec_file(file_path)
        else:
            formatted_path = SpecStyles.file(file_path)
        
        # Format size
        if size is not None:
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = "—"
        
        # Format status with styling
        status_styled = SpecStyles.info(status)
        
        self.add_row(formatted_path, file_type, size_str, status_styled)

class StatusTable(SpecTable):
    """Specialized table for displaying status information."""
    
    def __init__(self, title: str = "Status", **kwargs):
        """Initialize status table.
        
        Args:
            title: Table title
            **kwargs: Additional arguments for SpecTable
        """
        super().__init__(title=title, **kwargs)
        
        # Add standard status columns
        self.add_column("Component", style="label", ratio=2)
        self.add_column("Status", style="value", width=15)
        self.add_column("Details", style="muted", ratio=3)
    
    def add_status(self,
                  component: str,
                  status: str,
                  details: str = "",
                  status_type: str = "info") -> None:
        """Add a status entry to the table.
        
        Args:
            component: Component name
            status: Status value
            details: Additional details
            status_type: Type of status (success, warning, error, info)
        """
        # Format status with appropriate styling
        if status_type == "success":
            status_styled = SpecStyles.success(status)
        elif status_type == "warning":
            status_styled = SpecStyles.warning(status)
        elif status_type == "error":
            status_styled = SpecStyles.error(status)
        else:
            status_styled = SpecStyles.info(status)
        
        self.add_row(
            SpecStyles.label(component),
            status_styled,
            details
        )

def create_simple_table(data: List[Dict[str, Any]],
                       headers: Optional[List[str]] = None,
                       title: Optional[str] = None) -> SpecTable:
    """Create a simple table from data.
    
    Args:
        data: List of dictionaries with row data
        headers: Optional list of column headers
        title: Optional table title
        
    Returns:
        Configured SpecTable
    """
    if not data:
        table = SpecTable(title=title or "Empty Table")
        table.add_column("No Data", style="muted")
        table.add_row("No data available")
        return table
    
    # Determine headers
    if headers is None:
        headers = list(data[0].keys())
    
    # Create table
    table = SpecTable(title=title)
    
    # Add columns
    for header in headers:
        table.add_column(header)
    
    # Add rows
    for row_data in data:
        row_values = [row_data.get(header, "") for header in headers]
        table.add_row(*row_values)
    
    return table

def create_key_value_table(data: Dict[str, Any],
                          title: Optional[str] = None) -> SpecTable:
    """Create a key-value table from a dictionary.
    
    Args:
        data: Dictionary with key-value pairs
        title: Optional table title
        
    Returns:
        Configured SpecTable
    """
    table = SpecTable(title=title or "Configuration")
    table.add_column("Property", style="label", ratio=1)
    table.add_column("Value", style="value", ratio=2)
    
    for key, value in data.items():
        table.add_row(str(key), str(value))
    
    return table
```

### Step 2: Create spec_cli/ui/trees.py

```python
from typing import Any, Dict, List, Optional, Union, Callable
from rich.tree import Tree
from rich.console import Console
from rich.text import Text
from pathlib import Path
from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles

class SpecTree:
    """Spec-specific tree formatting with Rich integration."""
    
    def __init__(self,
                 label: str,
                 guide_style: str = "border",
                 expanded: bool = True,
                 console: Optional[Console] = None):
        """Initialize the spec tree.
        
        Args:
            label: Root node label
            guide_style: Style for tree guides
            expanded: Whether tree starts expanded
            console: Console to use for display
        """
        self.console = console or get_console().console
        self.guide_style = guide_style
        self.expanded = expanded
        
        self.tree = Tree(
            label,
            guide_style=guide_style,
            expanded=expanded
        )
        
        self.nodes: Dict[str, Tree] = {"root": self.tree}
        
        debug_logger.log("INFO", "SpecTree initialized",
                        label=label, expanded=expanded)
    
    def add_node(self,
                parent_path: str,
                node_id: str,
                label: str,
                style: Optional[str] = None,
                expanded: bool = True) -> str:
        """Add a node to the tree.
        
        Args:
            parent_path: Path to parent node
            node_id: Unique identifier for this node
            label: Node label text
            style: Optional style for the label
            expanded: Whether node starts expanded
            
        Returns:
            Full path to the new node
        """
        parent_node = self.nodes.get(parent_path)
        if parent_node is None:
            debug_logger.log("WARNING", "Parent node not found",
                           parent_path=parent_path)
            parent_node = self.tree
        
        # Apply styling to label if specified
        if style:
            styled_label = f"[{style}]{label}[/{style}]"
        else:
            styled_label = label
        
        new_node = parent_node.add(styled_label, expanded=expanded)
        
        # Store node with full path
        full_path = f"{parent_path}/{node_id}" if parent_path != "root" else node_id
        self.nodes[full_path] = new_node
        
        debug_logger.log("DEBUG", "Node added to tree",
                        node_id=node_id, parent=parent_path)
        
        return full_path
    
    def add_leaf(self,
                parent_path: str,
                label: str,
                style: Optional[str] = None) -> None:
        """Add a leaf node (no children) to the tree.
        
        Args:
            parent_path: Path to parent node
            label: Leaf label text
            style: Optional style for the label
        """
        parent_node = self.nodes.get(parent_path)
        if parent_node is None:
            debug_logger.log("WARNING", "Parent node not found for leaf",
                           parent_path=parent_path)
            parent_node = self.tree
        
        # Apply styling to label if specified
        if style:
            styled_label = f"[{style}]{label}[/{style}]"
        else:
            styled_label = label
        
        parent_node.add_leaf(styled_label)
        
        debug_logger.log("DEBUG", "Leaf added to tree",
                        label=label, parent=parent_path)
    
    def print(self) -> None:
        """Print the tree to the console."""
        self.console.print(self.tree)
        debug_logger.log("DEBUG", "Tree printed",
                        node_count=len(self.nodes))
    
    def get_tree(self) -> Tree:
        """Get the Rich Tree object.
        
        Returns:
            Rich Tree instance
        """
        return self.tree

class DirectoryTree(SpecTree):
    """Specialized tree for displaying directory structures."""
    
    def __init__(self, root_path: Path, **kwargs):
        """Initialize directory tree.
        
        Args:
            root_path: Root directory path
            **kwargs: Additional arguments for SpecTree
        """
        label = SpecStyles.directory(root_path.name or str(root_path))
        super().__init__(label=label, **kwargs)
        
        self.root_path = root_path
    
    def add_directory(self,
                     parent_path: str,
                     dir_path: Path,
                     expanded: bool = True) -> str:
        """Add a directory to the tree.
        
        Args:
            parent_path: Path to parent node
            dir_path: Directory path
            expanded: Whether directory starts expanded
            
        Returns:
            Full path to the new directory node
        """
        dir_name = dir_path.name
        label = SpecStyles.directory(dir_name)
        return self.add_node(parent_path, dir_name, label, expanded=expanded)
    
    def add_file(self,
                parent_path: str,
                file_path: Path,
                file_type: str = "file") -> None:
        """Add a file to the tree.
        
        Args:
            parent_path: Path to parent directory node
            file_path: File path
            file_type: Type of file (file, spec_file)
        """
        file_name = file_path.name
        
        if file_type == "spec_file":
            label = SpecStyles.spec_file(file_name)
        else:
            label = SpecStyles.file(file_name)
        
        self.add_leaf(parent_path, label)
    
    def build_from_path(self,
                       max_depth: int = 3,
                       show_hidden: bool = False,
                       file_filter: Optional[Callable[[Path], bool]] = None) -> None:
        """Build tree from filesystem path.
        
        Args:
            max_depth: Maximum depth to traverse
            show_hidden: Whether to show hidden files/directories
            file_filter: Optional function to filter files
        """
        self._build_recursive("root", self.root_path, 0, max_depth, show_hidden, file_filter)
    
    def _build_recursive(self,
                        parent_path: str,
                        current_path: Path,
                        current_depth: int,
                        max_depth: int,
                        show_hidden: bool,
                        file_filter: Optional[Callable[[Path], bool]]) -> None:
        """Recursively build tree from filesystem."""
        if current_depth >= max_depth:
            return
        
        try:
            entries = list(current_path.iterdir())
            
            # Filter hidden files if requested
            if not show_hidden:
                entries = [e for e in entries if not e.name.startswith('.')]
            
            # Sort: directories first, then files
            entries.sort(key=lambda x: (x.is_file(), x.name.lower()))
            
            for entry in entries:
                if entry.is_dir():
                    dir_node_path = self.add_directory(parent_path, entry)
                    self._build_recursive(
                        dir_node_path, entry, current_depth + 1,
                        max_depth, show_hidden, file_filter
                    )
                else:
                    # Apply file filter if provided
                    if file_filter and not file_filter(entry):
                        continue
                    
                    # Determine file type
                    file_type = "spec_file" if entry.suffix == ".md" and ".specs" in str(entry) else "file"
                    self.add_file(parent_path, entry, file_type)
        
        except PermissionError:
            self.add_leaf(parent_path, "[error]Permission denied[/error]")
        except Exception as e:
            self.add_leaf(parent_path, f"[error]Error: {e}[/error]")

class StatusTree(SpecTree):
    """Specialized tree for displaying hierarchical status information."""
    
    def __init__(self, title: str = "System Status", **kwargs):
        """Initialize status tree.
        
        Args:
            title: Tree title
            **kwargs: Additional arguments for SpecTree
        """
        label = SpecStyles.title(title)
        super().__init__(label=label, **kwargs)
    
    def add_component_status(self,
                           parent_path: str,
                           component: str,
                           status: str,
                           status_type: str = "info",
                           details: Optional[List[str]] = None) -> str:
        """Add a component status to the tree.
        
        Args:
            parent_path: Path to parent node
            component: Component name
            status: Status value
            status_type: Type of status (success, warning, error, info)
            details: Optional list of detail items
            
        Returns:
            Full path to the new component node
        """
        # Format status with appropriate styling
        if status_type == "success":
            status_styled = SpecStyles.success(status)
        elif status_type == "warning":
            status_styled = SpecStyles.warning(status)
        elif status_type == "error":
            status_styled = SpecStyles.error(status)
        else:
            status_styled = SpecStyles.info(status)
        
        label = f"{SpecStyles.label(component)}: {status_styled}"
        component_path = self.add_node(parent_path, component, label)
        
        # Add details if provided
        if details:
            for detail in details:
                self.add_leaf(component_path, SpecStyles.muted(detail))
        
        return component_path

def create_simple_tree(data: Dict[str, Any],
                      label: str = "Data Tree") -> SpecTree:
    """Create a simple tree from nested dictionary data.
    
    Args:
        data: Nested dictionary data
        label: Root label
        
    Returns:
        Configured SpecTree
    """
    tree = SpecTree(label)
    _build_tree_from_dict(tree, "root", data)
    return tree

def _build_tree_from_dict(tree: SpecTree,
                         parent_path: str,
                         data: Dict[str, Any]) -> None:
    """Recursively build tree from dictionary data."""
    for key, value in data.items():
        if isinstance(value, dict):
            # Add as node with children
            node_path = tree.add_node(parent_path, key, str(key))
            _build_tree_from_dict(tree, node_path, value)
        elif isinstance(value, (list, tuple)):
            # Add as node with list items
            node_path = tree.add_node(parent_path, key, f"{key} ({len(value)} items)")
            for i, item in enumerate(value):
                tree.add_leaf(node_path, f"[{i}] {item}")
        else:
            # Add as leaf
            tree.add_leaf(parent_path, f"{SpecStyles.label(key)}: {SpecStyles.value(str(value))}")

def create_directory_tree(directory: Path,
                         max_depth: int = 3,
                         show_hidden: bool = False) -> DirectoryTree:
    """Create a directory tree from a filesystem path.
    
    Args:
        directory: Directory to display
        max_depth: Maximum depth to traverse
        show_hidden: Whether to show hidden files
        
    Returns:
        Configured DirectoryTree
    """
    tree = DirectoryTree(directory)
    tree.build_from_path(max_depth=max_depth, show_hidden=show_hidden)
    return tree
```

### Step 3: Create spec_cli/ui/error_display.py

```python
import traceback
import sys
from typing import Any, Dict, List, Optional, Union, Type
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.syntax import Syntax
from rich.traceback import Traceback
from pathlib import Path
from ..exceptions import SpecError
from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles

class ErrorPanel:
    """Rich-based error display panel with syntax highlighting."""
    
    def __init__(self,
                 title: str = "Error",
                 console: Optional[Console] = None,
                 show_locals: bool = False,
                 max_frames: int = 10):
        """Initialize error panel.
        
        Args:
            title: Panel title
            console: Console to use for display
            show_locals: Whether to show local variables in traceback
            max_frames: Maximum number of stack frames to show
        """
        self.title = title
        self.console = console or get_console().console
        self.show_locals = show_locals
        self.max_frames = max_frames
        
        debug_logger.log("INFO", "ErrorPanel initialized",
                        title=title, show_locals=show_locals)
    
    def display_exception(self,
                         exception: Exception,
                         title: Optional[str] = None,
                         show_traceback: bool = True) -> None:
        """Display an exception with formatting.
        
        Args:
            exception: Exception to display
            title: Optional custom title
            show_traceback: Whether to show full traceback
        """
        panel_title = title or self.title
        
        # Create content based on exception type
        if isinstance(exception, SpecError):
            content = self._format_spec_error(exception)
        else:
            content = self._format_generic_error(exception)
        
        # Add traceback if requested
        if show_traceback:
            content.append("")
            content.append(SpecStyles.subtitle("Traceback:"))
            content.extend(self._format_traceback(exception))
        
        # Create and display panel
        panel_content = "\n".join(content)
        panel = Panel(
            panel_content,
            title=SpecStyles.error(panel_title),
            border_style="error",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        debug_logger.log("ERROR", "Exception displayed",
                        exception_type=type(exception).__name__,
                        message=str(exception))
    
    def display_error_summary(self,
                            errors: List[Dict[str, Any]],
                            title: str = "Error Summary") -> None:
        """Display a summary of multiple errors.
        
        Args:
            errors: List of error dictionaries
            title: Panel title
        """
        if not errors:
            return
        
        content = []
        content.append(SpecStyles.subtitle(f"Found {len(errors)} error(s):"))
        content.append("")
        
        for i, error in enumerate(errors, 1):
            error_type = error.get("type", "Unknown")
            error_message = error.get("message", "No message")
            error_file = error.get("file")
            error_line = error.get("line")
            
            content.append(f"{SpecStyles.label(f'{i}.')} {SpecStyles.error(error_type)}")
            content.append(f"   {error_message}")
            
            if error_file:
                location = SpecStyles.path(error_file)
                if error_line:
                    location += f":{SpecStyles.value(str(error_line))}"
                content.append(f"   {SpecStyles.muted('Location:')} {location}")
            
            content.append("")
        
        # Create and display panel
        panel_content = "\n".join(content)
        panel = Panel(
            panel_content,
            title=SpecStyles.error(title),
            border_style="error",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        debug_logger.log("INFO", "Error summary displayed",
                        error_count=len(errors))
    
    def display_validation_errors(self,
                                errors: Dict[str, List[str]],
                                title: str = "Validation Errors") -> None:
        """Display validation errors grouped by category.
        
        Args:
            errors: Dictionary of {category: [error_messages]}
            title: Panel title
        """
        if not errors:
            return
        
        content = []
        total_errors = sum(len(error_list) for error_list in errors.values())
        content.append(SpecStyles.subtitle(f"Found {total_errors} validation error(s):"))
        content.append("")
        
        for category, error_list in errors.items():
            if not error_list:
                continue
            
            content.append(f"{SpecStyles.warning(category)}:")
            for error in error_list:
                content.append(f"  • {error}")
            content.append("")
        
        # Create and display panel
        panel_content = "\n".join(content)
        panel = Panel(
            panel_content,
            title=SpecStyles.warning(title),
            border_style="warning",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        debug_logger.log("WARNING", "Validation errors displayed",
                        categories=list(errors.keys()),
                        total_errors=total_errors)
    
    def _format_spec_error(self, exception: SpecError) -> List[str]:
        """Format a SpecError with additional context."""
        content = []
        
        # Error type and message
        content.append(f"{SpecStyles.error('Error:')} {type(exception).__name__}")
        content.append(f"{SpecStyles.label('Message:')} {str(exception)}")
        
        # Add context if available
        if hasattr(exception, 'context') and exception.context:
            content.append("")
            content.append(SpecStyles.subtitle("Context:"))
            for key, value in exception.context.items():
                content.append(f"  {SpecStyles.label(key)}: {SpecStyles.value(str(value))}")
        
        # Add suggestions if available
        if hasattr(exception, 'suggestions') and exception.suggestions:
            content.append("")
            content.append(SpecStyles.subtitle("Suggestions:"))
            for suggestion in exception.suggestions:
                content.append(f"  • {suggestion}")
        
        return content
    
    def _format_generic_error(self, exception: Exception) -> List[str]:
        """Format a generic exception."""
        content = []
        
        # Error type and message
        content.append(f"{SpecStyles.error('Error:')} {type(exception).__name__}")
        content.append(f"{SpecStyles.label('Message:')} {str(exception)}")
        
        return content
    
    def _format_traceback(self, exception: Exception) -> List[str]:
        """Format exception traceback with syntax highlighting."""
        content = []
        
        # Get traceback frames
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        
        # Limit frames if needed
        if len(tb_lines) > self.max_frames + 2:  # +2 for header and exception line
            tb_lines = tb_lines[:self.max_frames + 1] + ["  ... (truncated)\n"] + tb_lines[-1:]
        
        for line in tb_lines:
            line = line.rstrip()
            if line.startswith('  File '):
                # Highlight file references
                content.append(self._highlight_file_reference(line))
            elif line.startswith('    '):
                # Code lines - add syntax highlighting
                code = line[4:]  # Remove indentation
                if code.strip():
                    highlighted = self._highlight_code_line(code)
                    content.append(f"    {highlighted}")
                else:
                    content.append(line)
            else:
                # Other lines (exception names, etc.)
                content.append(SpecStyles.muted(line))
        
        return content
    
    def _highlight_file_reference(self, line: str) -> str:
        """Highlight file references in traceback."""
        # Parse file reference: '  File "/path/to/file.py", line 123, in function_name'
        import re
        match = re.match(r'  File "([^"]+)", line (\d+), in (.+)', line)
        if match:
            file_path, line_num, func_name = match.groups()
            return (f"  File {SpecStyles.path(file_path)}, "
                   f"line {SpecStyles.value(line_num)}, "
                   f"in {SpecStyles.code(func_name)}")
        else:
            return SpecStyles.muted(line)
    
    def _highlight_code_line(self, code: str) -> str:
        """Highlight a line of code."""
        try:
            # Use Rich syntax highlighting for Python code
            syntax = Syntax(code, "python", theme="monokai", line_numbers=False)
            # Convert to string (simplified - in real usage, Rich handles this)
            return f"[code]{code}[/code]"
        except Exception:
            # Fallback to basic styling
            return SpecStyles.code(code)

class DiagnosticDisplay:
    """Display diagnostic information with formatting."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize diagnostic display.
        
        Args:
            console: Console to use for display
        """
        self.console = console or get_console().console
        
        debug_logger.log("INFO", "DiagnosticDisplay initialized")
    
    def display_system_info(self,
                           info: Dict[str, Any],
                           title: str = "System Information") -> None:
        """Display system diagnostic information.
        
        Args:
            info: Dictionary with system information
            title: Panel title
        """
        content = []
        
        for category, data in info.items():
            content.append(SpecStyles.subtitle(category.replace('_', ' ').title()))
            
            if isinstance(data, dict):
                for key, value in data.items():
                    content.append(f"  {SpecStyles.label(key)}: {SpecStyles.value(str(value))}")
            else:
                content.append(f"  {SpecStyles.value(str(data))}")
            
            content.append("")
        
        # Remove last empty line
        if content and content[-1] == "":
            content.pop()
        
        # Create and display panel
        panel_content = "\n".join(content)
        panel = Panel(
            panel_content,
            title=SpecStyles.info(title),
            border_style="info",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        debug_logger.log("INFO", "System info displayed",
                        categories=list(info.keys()))
    
    def display_performance_stats(self,
                                stats: Dict[str, Any],
                                title: str = "Performance Statistics") -> None:
        """Display performance statistics.
        
        Args:
            stats: Dictionary with performance data
            title: Panel title
        """
        content = []
        
        # Format timing information
        if "timing" in stats:
            content.append(SpecStyles.subtitle("Timing"))
            timing_data = stats["timing"]
            for operation, duration in timing_data.items():
                formatted_duration = f"{duration:.3f}s" if isinstance(duration, (int, float)) else str(duration)
                content.append(f"  {SpecStyles.label(operation)}: {SpecStyles.value(formatted_duration)}")
            content.append("")
        
        # Format memory information
        if "memory" in stats:
            content.append(SpecStyles.subtitle("Memory"))
            memory_data = stats["memory"]
            for metric, value in memory_data.items():
                if isinstance(value, (int, float)) and metric.endswith("_bytes"):
                    # Format bytes in human-readable form
                    formatted_value = self._format_bytes(value)
                else:
                    formatted_value = str(value)
                content.append(f"  {SpecStyles.label(metric)}: {SpecStyles.value(formatted_value)}")
            content.append("")
        
        # Format other statistics
        for category, data in stats.items():
            if category in ["timing", "memory"]:
                continue  # Already handled above
            
            content.append(SpecStyles.subtitle(category.replace('_', ' ').title()))
            if isinstance(data, dict):
                for key, value in data.items():
                    content.append(f"  {SpecStyles.label(key)}: {SpecStyles.value(str(value))}")
            else:
                content.append(f"  {SpecStyles.value(str(data))}")
            content.append("")
        
        # Remove last empty line
        if content and content[-1] == "":
            content.pop()
        
        # Create and display panel
        panel_content = "\n".join(content)
        panel = Panel(
            panel_content,
            title=SpecStyles.info(title),
            border_style="info",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        debug_logger.log("INFO", "Performance stats displayed")
    
    def _format_bytes(self, bytes_value: Union[int, float]) -> str:
        """Format bytes in human-readable form."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

# Convenience functions
def display_error(exception: Exception,
                 title: Optional[str] = None,
                 show_traceback: bool = True,
                 console: Optional[Console] = None) -> None:
    """Display an exception with formatting.
    
    Args:
        exception: Exception to display
        title: Optional custom title
        show_traceback: Whether to show full traceback
        console: Optional console to use
    """
    panel = ErrorPanel(title=title or "Error", console=console)
    panel.display_exception(exception, show_traceback=show_traceback)

def display_error_summary(errors: List[Dict[str, Any]],
                         title: str = "Error Summary",
                         console: Optional[Console] = None) -> None:
    """Display a summary of multiple errors.
    
    Args:
        errors: List of error dictionaries
        title: Panel title
        console: Optional console to use
    """
    panel = ErrorPanel(console=console)
    panel.display_error_summary(errors, title)

def display_validation_errors(errors: Dict[str, List[str]],
                            title: str = "Validation Errors",
                            console: Optional[Console] = None) -> None:
    """Display validation errors grouped by category.
    
    Args:
        errors: Dictionary of {category: [error_messages]}
        title: Panel title
        console: Optional console to use
    """
    panel = ErrorPanel(console=console)
    panel.display_validation_errors(errors, title)

def display_system_info(info: Dict[str, Any],
                       title: str = "System Information",
                       console: Optional[Console] = None) -> None:
    """Display system diagnostic information.
    
    Args:
        info: Dictionary with system information
        title: Panel title
        console: Optional console to use
    """
    display = DiagnosticDisplay(console=console)
    display.display_system_info(info, title)
```

### Step 4: Create spec_cli/ui/formatters.py

```python
from typing import Any, Dict, List, Optional, Union, Callable
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.text import Text
from pathlib import Path
import json
from ..logging.debug import debug_logger
from .console import get_console
from .styles import SpecStyles
from .tables import SpecTable, create_key_value_table
from .trees import SpecTree

class DataFormatter:
    """General-purpose data formatter with Rich integration."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize data formatter.
        
        Args:
            console: Console to use for display
        """
        self.console = console or get_console().console
        debug_logger.log("INFO", "DataFormatter initialized")
    
    def format_json(self,
                   data: Union[Dict[str, Any], List[Any]],
                   title: str = "JSON Data",
                   indent: int = 2) -> None:
        """Format and display JSON data.
        
        Args:
            data: JSON-serializable data
            title: Panel title
            indent: JSON indentation level
        """
        try:
            json_str = json.dumps(data, indent=indent, default=str)
            
            # Create syntax-highlighted panel
            from rich.syntax import Syntax
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            
            panel = Panel(
                syntax,
                title=SpecStyles.info(title),
                border_style="info",
                padding=(1, 2)
            )
            
            self.console.print(panel)
            
            debug_logger.log("DEBUG", "JSON data formatted and displayed")
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to format JSON", error=str(e))
            self.console.print(SpecStyles.error(f"Failed to format JSON: {e}"))
    
    def format_config(self,
                     config: Dict[str, Any],
                     title: str = "Configuration") -> None:
        """Format and display configuration data.
        
        Args:
            config: Configuration dictionary
            title: Display title
        """
        if not config:
            self.console.print(SpecStyles.muted("No configuration data"))
            return
        
        # Use key-value table for flat config
        if all(not isinstance(v, (dict, list)) for v in config.values()):
            table = create_key_value_table(config, title)
            table.print()
        else:
            # Use tree for nested config
            from .trees import create_simple_tree
            tree = create_simple_tree(config, title)
            tree.print()
    
    def format_file_list(self,
                        files: List[Path],
                        title: str = "Files",
                        show_details: bool = True) -> None:
        """Format and display a list of files.
        
        Args:
            files: List of file paths
            title: Display title
            show_details: Whether to show file details
        """
        if not files:
            self.console.print(SpecStyles.muted("No files found"))
            return
        
        if show_details:
            from .tables import FileListTable
            table = FileListTable(title)
            
            for file_path in files:
                try:
                    if file_path.is_dir():
                        table.add_file(file_path, "directory", status="directory")
                    else:
                        size = file_path.stat().st_size
                        file_type = "spec_file" if file_path.suffix == ".md" and ".specs" in str(file_path) else "file"
                        table.add_file(file_path, file_type, size, "ready")
                except Exception:
                    table.add_file(file_path, "unknown", status="error")
            
            table.print()
        else:
            # Simple list format
            content = []
            for file_path in files:
                if file_path.is_dir():
                    content.append(SpecStyles.directory(str(file_path)))
                elif file_path.suffix == ".md" and ".specs" in str(file_path):
                    content.append(SpecStyles.spec_file(str(file_path)))
                else:
                    content.append(SpecStyles.file(str(file_path)))
            
            panel = Panel(
                "\n".join(content),
                title=SpecStyles.info(title),
                border_style="info",
                padding=(1, 2)
            )
            
            self.console.print(panel)
    
    def format_status_report(self,
                           status_data: Dict[str, Any],
                           title: str = "Status Report") -> None:
        """Format and display a status report.
        
        Args:
            status_data: Dictionary with status information
            title: Display title
        """
        from .tables import StatusTable
        table = StatusTable(title)
        
        def add_status_recursive(data: Dict[str, Any], prefix: str = ""):
            for key, value in data.items():
                component_name = f"{prefix}{key}" if prefix else key
                
                if isinstance(value, dict):
                    if "status" in value:
                        # This is a status entry
                        status = value["status"]
                        details = value.get("details", "")
                        status_type = value.get("type", "info")
                        table.add_status(component_name, status, details, status_type)
                    else:
                        # This is a nested group
                        add_status_recursive(value, f"{component_name}.")
                else:
                    # Simple key-value
                    table.add_status(component_name, str(value))
        
        add_status_recursive(status_data)
        table.print()
    
    def format_comparison(self,
                         before: Dict[str, Any],
                         after: Dict[str, Any],
                         title: str = "Comparison") -> None:
        """Format and display a before/after comparison.
        
        Args:
            before: Before data
            after: After data
            title: Display title
        """
        table = SpecTable(title=title)
        table.add_column("Property", style="label")
        table.add_column("Before", style="muted")
        table.add_column("After", style="value")
        table.add_column("Change", style="info")
        
        # Get all keys
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in sorted(all_keys):
            before_val = before.get(key, "—")
            after_val = after.get(key, "—")
            
            # Determine change type
            if key not in before:
                change = SpecStyles.success("Added")
            elif key not in after:
                change = SpecStyles.error("Removed")
            elif before_val != after_val:
                change = SpecStyles.warning("Changed")
            else:
                change = SpecStyles.muted("Unchanged")
            
            table.add_row(
                str(key),
                str(before_val),
                str(after_val),
                change
            )
        
        table.print()

class MessageFormatter:
    """Formatter for user messages and notifications."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize message formatter.
        
        Args:
            console: Console to use for display
        """
        self.console = console or get_console().console
        debug_logger.log("INFO", "MessageFormatter initialized")
    
    def success(self, message: str, details: Optional[str] = None) -> None:
        """Display a success message.
        
        Args:
            message: Success message
            details: Optional additional details
        """
        self._display_message(message, "success", details)
    
    def warning(self, message: str, details: Optional[str] = None) -> None:
        """Display a warning message.
        
        Args:
            message: Warning message
            details: Optional additional details
        """
        self._display_message(message, "warning", details)
    
    def error(self, message: str, details: Optional[str] = None) -> None:
        """Display an error message.
        
        Args:
            message: Error message
            details: Optional additional details
        """
        self._display_message(message, "error", details)
    
    def info(self, message: str, details: Optional[str] = None) -> None:
        """Display an info message.
        
        Args:
            message: Info message
            details: Optional additional details
        """
        self._display_message(message, "info", details)
    
    def _display_message(self, message: str, message_type: str, details: Optional[str] = None) -> None:
        """Display a formatted message."""
        # Get emoji replacement for message type
        from .theme import get_current_theme
        theme = get_current_theme()
        emoji_replacements = theme.get_emoji_replacements()
        
        if message_type == "success":
            icon = emoji_replacements.get("✅", "[success]✓[/success]")
            styled_message = SpecStyles.success(message)
        elif message_type == "warning":
            icon = emoji_replacements.get("⚠️", "[warning]⚠[/warning]")
            styled_message = SpecStyles.warning(message)
        elif message_type == "error":
            icon = emoji_replacements.get("❌", "[error]✗[/error]")
            styled_message = SpecStyles.error(message)
        else:  # info
            icon = emoji_replacements.get("ℹ️", "[info]i[/info]")
            styled_message = SpecStyles.info(message)
        
        display_text = f"{icon} {styled_message}"
        
        if details:
            display_text += f"\n{SpecStyles.muted(details)}"
        
        self.console.print(display_text)
        
        debug_logger.log("DEBUG", "Message displayed",
                        type=message_type, message=message)
    
    def section_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Display a section header.
        
        Args:
            title: Section title
            subtitle: Optional subtitle
        """
        self.console.print()  # Empty line
        self.console.print(SpecStyles.title(title))
        
        if subtitle:
            self.console.print(SpecStyles.subtitle(subtitle))
        
        self.console.print()  # Empty line
    
    def operation_result(self,
                        operation: str,
                        success: bool,
                        details: Optional[Dict[str, Any]] = None) -> None:
        """Display operation result.
        
        Args:
            operation: Operation description
            success: Whether operation succeeded
            details: Optional result details
        """
        if success:
            self.success(f"{operation} completed successfully")
        else:
            self.error(f"{operation} failed")
        
        if details:
            self.console.print()
            formatter = DataFormatter(self.console)
            formatter.format_config(details, "Operation Details")

# Convenience functions
def format_data(data: Any,
               title: Optional[str] = None,
               console: Optional[Console] = None) -> None:
    """Format and display data automatically based on type.
    
    Args:
        data: Data to format
        title: Optional title
        console: Optional console to use
    """
    formatter = DataFormatter(console)
    
    if isinstance(data, (dict, list)):
        if title is None:
            title = "Data"
        formatter.format_json(data, title)
    elif isinstance(data, (list, tuple)) and data and isinstance(data[0], Path):
        if title is None:
            title = "Files"
        formatter.format_file_list(list(data), title)
    else:
        # Simple text display
        console = console or get_console().console
        panel = Panel(
            str(data),
            title=SpecStyles.info(title or "Data"),
            border_style="info"
        )
        console.print(panel)

def show_message(message: str,
                message_type: str = "info",
                details: Optional[str] = None,
                console: Optional[Console] = None) -> None:
    """Show a formatted message.
    
    Args:
        message: Message text
        message_type: Type (success, warning, error, info)
        details: Optional additional details
        console: Optional console to use
    """
    formatter = MessageFormatter(console)
    
    if message_type == "success":
        formatter.success(message, details)
    elif message_type == "warning":
        formatter.warning(message, details)
    elif message_type == "error":
        formatter.error(message, details)
    else:
        formatter.info(message, details)
```

### Step 5: Update spec_cli/ui/__init__.py

```python
"""Rich-based terminal UI system for spec CLI.

This package provides comprehensive terminal UI components including console theming,
progress tracking, data formatting, and error display with Rich integration.
"""

from .console import get_console, spec_console, SpecConsole, set_console, reset_console
from .theme import SpecTheme, ColorScheme, get_current_theme, set_current_theme, reset_theme
from .styles import SpecStyles, style_text, format_path, format_status, create_rich_text
from .progress_bar import SpecProgressBar, SimpleProgressBar, create_progress_bar, simple_progress
from .spinner import SpecSpinner, TimedSpinner, SpinnerManager, create_spinner, timed_spinner, spinner_context
from .progress_manager import ProgressManager, ProgressState, get_progress_manager, set_progress_manager, reset_progress_manager
from .progress_utils import (
    progress_context, timed_operation, ProgressTracker,
    track_progress, show_progress_for_files,
    estimate_operation_time, format_time_duration, calculate_processing_speed
)
from .tables import SpecTable, FileListTable, StatusTable, create_simple_table, create_key_value_table
from .trees import SpecTree, DirectoryTree, StatusTree, create_simple_tree, create_directory_tree
from .error_display import ErrorPanel, DiagnosticDisplay, display_error, display_error_summary, display_validation_errors, display_system_info
from .formatters import DataFormatter, MessageFormatter, format_data, show_message

__all__ = [
    # Console and theming
    "get_console",
    "spec_console", 
    "SpecConsole",
    "set_console",
    "reset_console",
    "SpecTheme",
    "ColorScheme",
    "get_current_theme",
    "set_current_theme",
    "reset_theme",
    "SpecStyles",
    "style_text",
    "format_path",
    "format_status",
    "create_rich_text",
    
    # Progress components
    "SpecProgressBar",
    "SimpleProgressBar", 
    "create_progress_bar",
    "simple_progress",
    "SpecSpinner",
    "TimedSpinner",
    "SpinnerManager",
    "create_spinner",
    "timed_spinner",
    "spinner_context",
    
    # Progress management
    "ProgressManager",
    "ProgressState",
    "get_progress_manager",
    "set_progress_manager",
    "reset_progress_manager",
    
    # Progress utilities
    "progress_context",
    "timed_operation",
    "ProgressTracker",
    "track_progress",
    "show_progress_for_files",
    "estimate_operation_time",
    "format_time_duration",
    "calculate_processing_speed",
    
    # Tables and trees
    "SpecTable",
    "FileListTable",
    "StatusTable",
    "create_simple_table",
    "create_key_value_table",
    "SpecTree",
    "DirectoryTree", 
    "StatusTree",
    "create_simple_tree",
    "create_directory_tree",
    
    # Error display
    "ErrorPanel",
    "DiagnosticDisplay",
    "display_error",
    "display_error_summary",
    "display_validation_errors",
    "display_system_info",
    
    # Formatters
    "DataFormatter",
    "MessageFormatter",
    "format_data",
    "show_message",
]
```

## Test Requirements

Create comprehensive tests for formatter and error display components:

### Test Cases (16 tests total)

**Table Tests:**
1. **test_spec_table_creation_and_columns**
2. **test_file_list_table_specialized_functionality**
3. **test_status_table_with_different_status_types**
4. **test_table_convenience_functions**

**Tree Tests:**
5. **test_spec_tree_node_management**
6. **test_directory_tree_filesystem_integration**
7. **test_status_tree_hierarchical_display**
8. **test_tree_convenience_functions**

**Error Display Tests:**
9. **test_error_panel_exception_display**
10. **test_error_panel_spec_error_formatting**
11. **test_error_summary_and_validation_errors**
12. **test_diagnostic_display_system_info**

**Formatter Tests:**
13. **test_data_formatter_json_and_config**
14. **test_data_formatter_file_lists_and_comparisons**
15. **test_message_formatter_all_types**
16. **test_formatter_convenience_functions**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/ui/test_tables.py tests/unit/ui/test_trees.py tests/unit/ui/test_error_display.py tests/unit/ui/test_formatters.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/ui/ --cov=spec_cli.ui --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/ui/

# Check code formatting
poetry run ruff check spec_cli/ui/
poetry run ruff format spec_cli/ui/

# Verify imports work correctly
python -c "from spec_cli.ui import SpecTable, SpecTree, ErrorPanel, DataFormatter; print('Import successful')"

# Test table functionality
python -c "
from spec_cli.ui.tables import SpecTable, create_key_value_table
from pathlib import Path

# Create simple table
table = SpecTable('Test Table')
table.add_column('Name', style='label')
table.add_column('Value', style='value')
table.add_row('Setting 1', 'Value 1')
table.add_row('Setting 2', 'Value 2')
print('Table created with 2 rows')

# Test key-value table
config = {'debug': True, 'max_files': 100, 'timeout': 30}
kv_table = create_key_value_table(config, 'Configuration')
print(f'Key-value table created with {len(config)} items')
"

# Test tree functionality
python -c "
from spec_cli.ui.trees import SpecTree, create_simple_tree

# Create simple tree
tree = SpecTree('Root Node')
node1 = tree.add_node('root', 'branch1', 'Branch 1')
tree.add_leaf(node1, 'Leaf 1')
tree.add_leaf(node1, 'Leaf 2')
print('Tree created with branches and leaves')

# Test data tree
data = {
    'system': {'version': '1.0', 'debug': True},
    'files': ['file1.py', 'file2.py']
}
data_tree = create_simple_tree(data, 'System Data')
print('Data tree created from nested dictionary')
"

# Test error display
python -c "
from spec_cli.ui.error_display import ErrorPanel, display_error
from spec_cli.exceptions import SpecError

# Create test error
try:
    raise SpecError('Test error for display')
except SpecError as e:
    print('Error created for testing')
    # In real usage, this would display the error
    # display_error(e, show_traceback=False)
"

# Test formatters
python -c "
from spec_cli.ui.formatters import MessageFormatter, DataFormatter

# Test message formatter
formatter = MessageFormatter()
print('Message formatter initialized')

# Test data formatter  
data_formatter = DataFormatter()
test_data = {'setting1': 'value1', 'setting2': 42}
print(f'Data formatter ready for {len(test_data)} items')
"

# Test complete UI integration
python -c "
from spec_cli.ui import (
    get_console, SpecStyles, SpecTable, SpecTree, 
    MessageFormatter, format_data, show_message
)

console = get_console()
print(f'UI system initialized:')
print(f'  Console width: {console.get_width()}')
print(f'  Terminal: {console.is_terminal()}')
print(f'  All components imported successfully')
"
```

## Definition of Done

- [ ] SpecTable with specialized tables for files and status
- [ ] SpecTree with directory and status tree variants
- [ ] ErrorPanel with syntax highlighting and trace formatting
- [ ] DiagnosticDisplay for system information
- [ ] DataFormatter for structured data display
- [ ] MessageFormatter for user notifications
- [ ] Comprehensive convenience functions
- [ ] All 16 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Isolated, testable components ready for CLI integration

## Next Slice Preparation

This slice completes **PHASE-5 Rich UI System** by providing:
- Complete Rich-based UI component library
- Data formatting and error display capabilities
- Foundation for CLI command integration in slice-13
- Comprehensive styling and theming system
- Progress tracking and user feedback components

The Rich UI system is now complete and ready for integration with CLI commands in the final implementation phase.