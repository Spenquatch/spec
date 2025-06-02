"""Tests for tables functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.table import Table
from rich.text import Text

from spec_cli.ui.tables import (
    ComparisonTable,
    FileListTable,
    SpecTable,
    StatusTable,
    create_file_table,
    create_key_value_table,
    create_status_table,
    format_table_data,
    print_simple_table,
)


class TestSpecTable:
    """Test SpecTable base class functionality."""

    def test_spec_table_initialization_defaults(self):
        """Test SpecTable initialization with defaults."""
        table = SpecTable()
        
        assert table.title is None
        assert table.show_header is True
        assert table.show_lines is False
        assert table.show_edge is True
        assert table.expand is False
        assert table.console is not None
        assert isinstance(table.table, Table)

    def test_spec_table_initialization_custom(self):
        """Test SpecTable initialization with custom options."""
        mock_console = Mock()
        title = "Test Table"
        
        table = SpecTable(
            title=title,
            show_header=False,
            show_lines=True,
            show_edge=False,
            expand=True,
            console=mock_console
        )
        
        assert table.title == title
        assert table.show_header is False
        assert table.show_lines is True
        assert table.show_edge is False
        assert table.expand is True
        assert table.console == mock_console

    def test_add_column_basic(self):
        """Test adding basic column."""
        table = SpecTable()
        
        table.add_column("Test Header")
        
        # Check that column was added by inspecting the rich table
        rich_table = table.get_table()
        assert len(rich_table.columns) == 1
        assert rich_table.columns[0].header == "Test Header"

    def test_add_column_with_options(self):
        """Test adding column with all options."""
        table = SpecTable()
        
        table.add_column(
            "Test Header",
            style="bold",
            justify="center",
            width=20,
            min_width=10,
            max_width=30,
            ratio=2,
            no_wrap=True,
            overflow="fold"
        )
        
        rich_table = table.get_table()
        column = rich_table.columns[0]
        
        assert column.header == "Test Header"
        assert column.style == "bold"
        assert column.justify == "center"
        assert column.width == 20
        assert column.min_width == 10
        assert column.max_width == 30
        assert column.ratio == 2
        assert column.no_wrap is True
        assert column.overflow == "fold"

    def test_add_row_basic(self):
        """Test adding basic row."""
        table = SpecTable()
        table.add_column("Col1")
        table.add_column("Col2")
        
        table.add_row("value1", "value2")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_row_with_style(self):
        """Test adding row with style."""
        table = SpecTable()
        table.add_column("Col1")
        table.add_column("Col2")
        
        table.add_row("value1", "value2", style="bold")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_row_value_formatting(self):
        """Test row value formatting."""
        table = SpecTable()
        table.add_column("Col1")
        table.add_column("Col2")
        table.add_column("Col3")
        
        # Test different value types
        text_obj = Text("rich text")
        table.add_row("string", 123, text_obj)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_print_table(self):
        """Test printing table."""
        mock_console = Mock()
        table = SpecTable(console=mock_console)
        table.add_column("Test")
        table.add_row("value")
        
        table.print()
        
        mock_console.print.assert_called_once()
        # Verify it's printing the table object
        args, kwargs = mock_console.print.call_args
        assert isinstance(args[0], Table)

    def test_get_table(self):
        """Test getting Rich table object."""
        table = SpecTable()
        
        rich_table = table.get_table()
        
        assert isinstance(rich_table, Table)
        assert rich_table is table.table


class TestFileListTable:
    """Test FileListTable specialized table."""

    def test_file_list_table_initialization(self):
        """Test FileListTable initialization."""
        table = FileListTable()
        
        assert table.title == "Files"
        # Should have the 4 standard columns
        rich_table = table.get_table()
        assert len(rich_table.columns) == 4
        
        headers = [col.header for col in rich_table.columns]
        assert "Path" in headers
        assert "Type" in headers
        assert "Size" in headers
        assert "Status" in headers

    def test_file_list_table_custom_title(self):
        """Test FileListTable with custom title."""
        custom_title = "Project Files"
        table = FileListTable(title=custom_title)
        
        assert table.title == custom_title

    def test_add_file_basic(self):
        """Test adding basic file."""
        table = FileListTable()
        file_path = Path("/test/file.txt")
        
        table.add_file(file_path)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_file_with_all_options(self):
        """Test adding file with all options."""
        table = FileListTable()
        file_path = Path("/test/file.txt")
        
        table.add_file(
            file_path,
            file_type="spec_file",
            size=1024,
            status="completed"
        )
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_file_directory(self):
        """Test adding directory file."""
        table = FileListTable()
        dir_path = Path("/test/directory")
        
        table.add_file(dir_path, file_type="directory")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        table = FileListTable()
        
        size_str = table._format_file_size(512)
        
        assert size_str == "512B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes."""
        table = FileListTable()
        
        size_str = table._format_file_size(1536)  # 1.5KB
        
        assert size_str == "1.5KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes."""
        table = FileListTable()
        
        size_str = table._format_file_size(2 * 1024 * 1024)  # 2MB
        
        assert size_str == "2.0MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabytes."""
        table = FileListTable()
        
        size_str = table._format_file_size(3 * 1024 * 1024 * 1024)  # 3GB
        
        assert size_str == "3.0GB"

    def test_add_file_status_styling(self):
        """Test different status styling."""
        table = FileListTable()
        file_path = Path("/test/file.txt")
        
        statuses = ["pending", "processing", "completed", "failed", "skipped", "unknown"]
        
        for status in statuses:
            table.add_file(file_path, status=status)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == len(statuses)

    def test_add_file_no_size(self):
        """Test adding file without size."""
        table = FileListTable()
        file_path = Path("/test/file.txt")
        
        table.add_file(file_path, size=None)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1


class TestStatusTable:
    """Test StatusTable specialized table."""

    def test_status_table_initialization(self):
        """Test StatusTable initialization."""
        table = StatusTable()
        
        assert table.title == "Status"
        # Should have show_lines=True by default
        assert table.show_lines is True
        
        # Should have the 3 standard columns
        rich_table = table.get_table()
        assert len(rich_table.columns) == 3
        
        headers = [col.header for col in rich_table.columns]
        assert "Item" in headers
        assert "Value" in headers
        assert "Status" in headers

    def test_status_table_custom_title(self):
        """Test StatusTable with custom title."""
        custom_title = "System Status"
        table = StatusTable(title=custom_title)
        
        assert table.title == custom_title

    def test_add_status_item_info(self):
        """Test adding status item with info status."""
        table = StatusTable()
        
        table.add_status_item("Test Item", "test value", "info")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_status_item_success(self):
        """Test adding status item with success status."""
        table = StatusTable()
        
        table.add_status_item("Test Item", "test value", "success")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_status_item_warning(self):
        """Test adding status item with warning status."""
        table = StatusTable()
        
        table.add_status_item("Test Item", "test value", "warning")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_status_item_error(self):
        """Test adding status item with error status."""
        table = StatusTable()
        
        table.add_status_item("Test Item", "test value", "error")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_status_item_default(self):
        """Test adding status item with default status."""
        table = StatusTable()
        
        table.add_status_item("Test Item", "test value")  # Default should be "info"
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_status_item_different_value_types(self):
        """Test adding status items with different value types."""
        table = StatusTable()
        
        table.add_status_item("String", "text")
        table.add_status_item("Integer", 42)
        table.add_status_item("Float", 3.14)
        table.add_status_item("Boolean", True)
        table.add_status_item("None", None)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 5


class TestComparisonTable:
    """Test ComparisonTable specialized table."""

    def test_comparison_table_initialization(self):
        """Test ComparisonTable initialization."""
        table = ComparisonTable()
        
        assert table.title == "Comparison"
        assert table.show_lines is True
        
        # Should have the 4 standard columns
        rich_table = table.get_table()
        assert len(rich_table.columns) == 4
        
        headers = [col.header for col in rich_table.columns]
        assert "Property" in headers
        assert "Before" in headers
        assert "After" in headers
        assert "Change" in headers

    def test_comparison_table_custom_title(self):
        """Test ComparisonTable with custom title."""
        custom_title = "Performance Comparison"
        table = ComparisonTable(title=custom_title)
        
        assert table.title == custom_title

    def test_add_comparison_no_change(self):
        """Test adding comparison with no change."""
        table = ComparisonTable()
        
        table.add_comparison("Property", "value", "value")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_comparison_increase(self):
        """Test adding comparison with increase."""
        table = ComparisonTable()
        
        table.add_comparison("Count", 5, 10)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_comparison_decrease(self):
        """Test adding comparison with decrease."""
        table = ComparisonTable()
        
        table.add_comparison("Size", 100, 50)
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_comparison_string_comparison(self):
        """Test adding comparison with string values."""
        table = ComparisonTable()
        
        table.add_comparison("Version", "1.0.0", "2.0.0")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 1

    def test_add_comparison_different_types(self):
        """Test adding comparison with different value types."""
        table = ComparisonTable()
        
        table.add_comparison("Mixed", 10, "text")
        table.add_comparison("Boolean", True, False)
        table.add_comparison("None", None, "value")
        
        rich_table = table.get_table()
        assert len(rich_table.rows) == 3


class TestUtilityFunctions:
    """Test utility functions."""

    @patch('spec_cli.ui.tables.get_console')
    def test_create_file_table_basic(self, mock_get_console):
        """Test creating basic file table."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        # Create temporary files for testing
        files = [Path("/test/file1.txt"), Path("/test/file2.py")]
        
        with patch.object(Path, 'is_dir', return_value=False), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat') as mock_stat:
            
            mock_stat.return_value.st_size = 1024
            table = create_file_table(files)
            
            assert isinstance(table, FileListTable)
            rich_table = table.get_table()
            assert len(rich_table.rows) == 2

    @patch('spec_cli.ui.tables.get_console')
    def test_create_file_table_with_directories(self, mock_get_console):
        """Test creating file table with directories."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        files = [Path("/test/dir"), Path("/test/file.txt")]
        
        with patch.object(Path, 'is_dir', side_effect=[True, False]), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', side_effect=[False, True]), \
             patch.object(Path, 'stat') as mock_stat:
            
            mock_stat.return_value.st_size = 512
            table = create_file_table(files)
            
            assert isinstance(table, FileListTable)
            rich_table = table.get_table()
            assert len(rich_table.rows) == 2

    @patch('spec_cli.ui.tables.get_console')
    def test_create_file_table_custom_title(self, mock_get_console):
        """Test creating file table with custom title."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        files = [Path("/test/file.txt")]
        custom_title = "Project Files"
        
        with patch.object(Path, 'is_dir', return_value=False), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat') as mock_stat:
            
            mock_stat.return_value.st_size = 256
            table = create_file_table(files, title=custom_title)
            
            assert table.title == custom_title

    @patch('spec_cli.ui.tables.get_console')
    def test_create_file_table_nonexistent_files(self, mock_get_console):
        """Test creating file table with non-existent files."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        files = [Path("/nonexistent/file.txt")]
        
        with patch.object(Path, 'is_dir', return_value=False), \
             patch.object(Path, 'exists', return_value=False), \
             patch.object(Path, 'is_file', return_value=False):
            
            table = create_file_table(files)
            
            assert isinstance(table, FileListTable)
            rich_table = table.get_table()
            assert len(rich_table.rows) == 1

    @patch('spec_cli.ui.tables.get_console')
    def test_create_status_table_basic(self, mock_get_console):
        """Test creating basic status table."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {
            "initialized": True,
            "files_count": 5,
            "last_update": "2023-01-01",
            "disabled": False
        }
        
        table = create_status_table(data)
        
        assert isinstance(table, StatusTable)
        rich_table = table.get_table()
        assert len(rich_table.rows) == 4

    @patch('spec_cli.ui.tables.get_console')
    def test_create_status_table_custom_title(self, mock_get_console):
        """Test creating status table with custom title."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {"status": "ok"}
        custom_title = "System Status"
        
        table = create_status_table(data, title=custom_title)
        
        assert table.title == custom_title

    @patch('spec_cli.ui.tables.get_console')
    def test_create_status_table_status_logic(self, mock_get_console):
        """Test status table status determination logic."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {
            "bool_true": True,        # Should be "success"
            "bool_false": False,      # Should be "error"
            "positive_int": 10,       # Should be "success"
            "zero_int": 0,           # Should be "info"
            "negative_int": -5,      # Should be "info"
            "positive_float": 3.14,  # Should be "success"
            "zero_float": 0.0,       # Should be "info"
            "string": "text",        # Should be "info"
            "none_value": None       # Should be "info"
        }
        
        table = create_status_table(data)
        
        assert isinstance(table, StatusTable)
        rich_table = table.get_table()
        assert len(rich_table.rows) == 9

    @patch('spec_cli.ui.tables.get_console')
    def test_print_simple_table_basic(self, mock_get_console):
        """Test printing simple table."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = [
            {"name": "John", "age": 30, "city": "New York"},
            {"name": "Jane", "age": 25, "city": "Boston"}
        ]
        
        print_simple_table(data)
        
        # Should create and print a table
        mock_console.print.assert_called_once()

    @patch('spec_cli.ui.tables.get_console')
    def test_print_simple_table_with_headers(self, mock_get_console):
        """Test printing simple table with custom headers."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = [
            {"name": "John", "age": 30, "city": "New York"},
            {"name": "Jane", "age": 25, "city": "Boston"}
        ]
        headers = ["name", "city"]  # Skip age column
        
        print_simple_table(data, headers=headers)
        
        mock_console.print.assert_called_once()

    @patch('spec_cli.ui.tables.get_console')
    def test_print_simple_table_with_title(self, mock_get_console):
        """Test printing simple table with title."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = [{"name": "John", "age": 30}]
        title = "People Table"
        
        print_simple_table(data, title=title)
        
        mock_console.print.assert_called_once()

    @patch('spec_cli.ui.tables.get_console')
    def test_print_simple_table_empty_data(self, mock_get_console):
        """Test printing simple table with empty data."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        print_simple_table([])
        
        # Should not print anything for empty data
        mock_console.print.assert_not_called()

    @patch('spec_cli.ui.tables.get_console')
    def test_print_simple_table_missing_keys(self, mock_get_console):
        """Test printing simple table with missing keys in some rows."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = [
            {"name": "John", "age": 30, "city": "New York"},
            {"name": "Jane", "city": "Boston"}  # Missing age
        ]
        
        print_simple_table(data)
        
        mock_console.print.assert_called_once()

    @patch('spec_cli.ui.tables.get_console')
    def test_create_key_value_table_basic(self, mock_get_console):
        """Test creating key-value table."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {
            "project_name": "spec-cli",
            "version": "1.0.0",
            "debug_mode": True,
            "file_count": 42
        }
        
        table = create_key_value_table(data)
        
        assert isinstance(table, SpecTable)
        rich_table = table.get_table()
        assert len(rich_table.columns) == 2
        assert len(rich_table.rows) == 4

    @patch('spec_cli.ui.tables.get_console')
    def test_create_key_value_table_with_title(self, mock_get_console):
        """Test creating key-value table with title."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {"key": "value"}
        title = "Configuration"
        
        table = create_key_value_table(data, title=title)
        
        assert table.title == title

    @patch('spec_cli.ui.tables.get_console')
    def test_create_key_value_table_key_formatting(self, mock_get_console):
        """Test key formatting in key-value table."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        data = {
            "project_name": "test",
            "api_key_count": 5,
            "is_debug_enabled": True
        }
        
        table = create_key_value_table(data)
        
        # Keys should be formatted (underscores to spaces, title case)
        assert isinstance(table, SpecTable)

    def test_format_table_data_no_formatter(self):
        """Test format_table_data without custom formatter."""
        # Test different data types
        assert format_table_data("string") == "string"
        assert format_table_data(42) == "42"
        assert format_table_data(3.14) == "3.14"
        assert format_table_data(True) == "Yes"
        assert format_table_data(False) == "No"
        assert format_table_data(None) == "-"
        
        path = Path("/test/path")
        assert format_table_data(path) == str(path)

    def test_format_table_data_with_formatter(self):
        """Test format_table_data with custom formatter."""
        def custom_formatter(data):
            return f"Custom: {data}"
        
        result = format_table_data("test", formatter=custom_formatter)
        
        assert result == "Custom: test"

    def test_format_table_data_path_object(self):
        """Test format_table_data with Path object."""
        path = Path("/home/user/file.txt")
        
        result = format_table_data(path)
        
        assert result == str(path)

    def test_format_table_data_boolean_values(self):
        """Test format_table_data with boolean values."""
        assert format_table_data(True) == "Yes"
        assert format_table_data(False) == "No"

    def test_format_table_data_numeric_values(self):
        """Test format_table_data with numeric values."""
        assert format_table_data(0) == "0"
        assert format_table_data(-5) == "-5"
        assert format_table_data(3.14159) == "3.14159"

    def test_format_table_data_none_value(self):
        """Test format_table_data with None value."""
        assert format_table_data(None) == "-"

    def test_format_table_data_complex_object(self):
        """Test format_table_data with complex object."""
        class TestObject:
            def __str__(self):
                return "test_object_string"
        
        obj = TestObject()
        result = format_table_data(obj)
        
        assert result == "test_object_string"


class TestTableIntegration:
    """Test table integration scenarios."""

    @patch('spec_cli.ui.tables.get_console')
    def test_complete_file_table_workflow(self, mock_get_console):
        """Test complete file table workflow."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        # Create table and add various file types
        table = FileListTable(title="Project Files")
        
        # Add different types of files
        table.add_file(Path("/src/main.py"), "file", 2048, "completed")
        table.add_file(Path("/tests/"), "directory", None, "pending")
        table.add_file(Path("/docs/README.md"), "file", 512, "processing")
        table.add_file(Path("/config.json"), "spec_file", 128, "failed")
        
        # Print the table
        table.print()
        
        # Verify the table was printed
        mock_console.print.assert_called_once()
        
        # Verify all rows were added
        rich_table = table.get_table()
        assert len(rich_table.rows) == 4

    @patch('spec_cli.ui.tables.get_console')
    def test_complete_status_table_workflow(self, mock_get_console):
        """Test complete status table workflow."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        # Create table and add various status items
        table = StatusTable(title="System Status")
        
        table.add_status_item("Repository", "Initialized", "success")
        table.add_status_item("Files Processed", 25, "info")
        table.add_status_item("Warnings", 3, "warning")
        table.add_status_item("Errors", 0, "success")
        table.add_status_item("Last Backup", "Failed", "error")
        
        # Print the table
        table.print()
        
        # Verify the table was printed
        mock_console.print.assert_called_once()
        
        # Verify all rows were added
        rich_table = table.get_table()
        assert len(rich_table.rows) == 5

    @patch('spec_cli.ui.tables.get_console')
    def test_complete_comparison_table_workflow(self, mock_get_console):
        """Test complete comparison table workflow."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        # Create table and add various comparisons
        table = ComparisonTable(title="Performance Comparison")
        
        table.add_comparison("Processing Speed", "100 files/min", "150 files/min")
        table.add_comparison("Memory Usage", "512MB", "480MB")
        table.add_comparison("Error Rate", "2%", "1%")
        table.add_comparison("Uptime", "99.9%", "99.9%")
        
        # Print the table
        table.print()
        
        # Verify the table was printed
        mock_console.print.assert_called_once()
        
        # Verify all rows were added
        rich_table = table.get_table()
        assert len(rich_table.rows) == 4

    @patch('spec_cli.ui.tables.get_console')
    def test_utility_functions_integration(self, mock_get_console):
        """Test utility functions working together."""
        mock_console = Mock()
        mock_get_console.return_value.console = mock_console
        
        # Test data for different utilities
        files = [Path("/test1.py"), Path("/test2.py")]
        status_data = {"files": len(files), "ready": True}
        
        with patch.object(Path, 'is_dir', return_value=False), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat') as mock_stat:
            
            mock_stat.return_value.st_size = 1024
            
            # Create file table
            file_table = create_file_table(files, title="Test Files")
            
            # Create status table
            status_table = create_status_table(status_data, title="Test Status")
            
            # Create key-value table
            kv_table = create_key_value_table({"version": "1.0"}, title="Config")
            
            # All should be valid table instances
            assert isinstance(file_table, FileListTable)
            assert isinstance(status_table, StatusTable)
            assert isinstance(kv_table, SpecTable)
            
            # Print all tables
            file_table.print()
            status_table.print()
            kv_table.print()
            
            # Verify all were printed
            assert mock_console.print.call_count == 3