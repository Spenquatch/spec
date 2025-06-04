import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecFileError
from spec_cli.file_system import file_utils


class TestFileUtils:
    """Test suite for file utility functions."""

    @pytest.fixture
    def temp_file(self) -> Generator[Path, None, None]:
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('Hello, World!')")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_dir_with_files(self) -> Generator[Path, None, None]:
        """Create a temporary directory with various files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files of different sizes and types
            (temp_path / "small.py").write_text("print('small')")
            (temp_path / "medium.js").write_text("console.log('medium file');\n" * 10)
            (temp_path / "large.txt").write_text("Large content\n" * 100)
            (temp_path / "config.json").write_text('{"key": "value"}')
            (temp_path / "README.md").write_text("# Test")

            # Create a subdirectory with files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("print('nested')")

            yield temp_path

    def test_ensure_file_readable_validates_accessibility(
        self, temp_file: Path
    ) -> None:
        """Test file readability validation."""
        # Should be readable
        assert file_utils.ensure_file_readable(temp_file) is True

        # Test non-existent file
        non_existent = Path("/non/existent/file.txt")
        assert file_utils.ensure_file_readable(non_existent) is False

        # Test directory (not a regular file)
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            assert file_utils.ensure_file_readable(dir_path) is False

    def test_file_extension_stats_counts_correctly(
        self, temp_dir_with_files: Path
    ) -> None:
        """Test file extension statistics counting."""
        files = list(temp_dir_with_files.rglob("*"))
        files = [f for f in files if f.is_file()]

        stats = file_utils.get_file_extension_stats(files)

        # Check expected extensions
        assert ".py" in stats
        assert ".js" in stats
        assert ".txt" in stats
        assert ".json" in stats
        assert ".md" in stats

        # Check counts
        assert stats[".py"] == 2  # small.py and nested.py
        assert stats[".js"] == 1
        assert stats[".txt"] == 1
        assert stats[".json"] == 1
        assert stats[".md"] == 1

    def test_largest_files_finder_sorts_by_size(
        self, temp_dir_with_files: Path
    ) -> None:
        """Test finding largest files and sorting by size."""
        largest_files = file_utils.find_largest_files(temp_dir_with_files, limit=3)

        # Should return list of dictionaries
        assert isinstance(largest_files, list)
        assert len(largest_files) <= 3

        # Each item should have required keys
        for file_info in largest_files:
            assert "path" in file_info
            assert "size" in file_info
            assert "size_formatted" in file_info

        # Should be sorted by size (largest first) - just check they have size keys
        if len(largest_files) > 1:
            for i in range(len(largest_files) - 1):
                size_current = largest_files[i]["size"]
                size_next = largest_files[i + 1]["size"]
                assert isinstance(size_current, int | float)
                assert isinstance(size_next, int | float)
                assert size_current >= size_next

    def test_recently_modified_finder_sorts_by_time(
        self, temp_dir_with_files: Path
    ) -> None:
        """Test finding recently modified files and sorting by time."""
        # Modify one file to ensure different timestamps
        time.sleep(0.1)  # Small delay to ensure different timestamps
        (temp_dir_with_files / "small.py").write_text("print('modified')")

        recent_files = file_utils.find_recently_modified_files(
            temp_dir_with_files, limit=3
        )

        # Should return list of dictionaries
        assert isinstance(recent_files, list)
        assert len(recent_files) <= 3

        # Each item should have required keys
        for file_info in recent_files:
            assert "path" in file_info
            assert "modified_time" in file_info
            assert "modified_formatted" in file_info

        # Should be sorted by modification time (newest first) - just check they have time keys
        if len(recent_files) > 1:
            for i in range(len(recent_files) - 1):
                time_current = recent_files[i]["modified_time"]
                time_next = recent_files[i + 1]["modified_time"]
                assert isinstance(time_current, int | float)
                assert isinstance(time_next, int | float)
                assert time_current >= time_next

    def test_safe_file_operation_checks_permissions(self, temp_file: Path) -> None:
        """Test safe file operation permission checking."""
        # Test read operation
        assert file_utils.safe_file_operation(temp_file, "read") is True

        # Test write operation (should be true for temp file)
        assert file_utils.safe_file_operation(temp_file, "write") is True

        # Test invalid operation
        assert file_utils.safe_file_operation(temp_file, "invalid") is False

        # Test non-existent file
        non_existent = Path("/non/existent/file.txt")
        assert file_utils.safe_file_operation(non_existent, "read") is False

    def test_file_filtering_by_size_works_correctly(
        self, temp_dir_with_files: Path
    ) -> None:
        """Test filtering files by size range."""
        files = list(temp_dir_with_files.rglob("*"))
        files = [f for f in files if f.is_file()]

        # Filter for small files (< 100 bytes)
        small_files = file_utils.filter_files_by_size(files, min_size=0, max_size=100)

        # Should return a list
        assert isinstance(small_files, list)

        # All returned files should be within size range
        for file_path in small_files:
            size = file_path.stat().st_size
            assert 0 <= size <= 100

        # Filter for larger files (> 100 bytes)
        large_files = file_utils.filter_files_by_size(files, min_size=100)

        for file_path in large_files:
            size = file_path.stat().st_size
            assert size >= 100

    def test_utility_functions_handle_edge_cases(self) -> None:
        """Test utility functions with edge cases."""
        # Test format_file_size with various sizes
        assert file_utils.format_file_size(0) == "0.0 B"
        assert file_utils.format_file_size(1023) == "1023.0 B"
        assert file_utils.format_file_size(1024) == "1.0 KB"
        assert file_utils.format_file_size(1048576) == "1.0 MB"
        assert file_utils.format_file_size(1073741824) == "1.0 GB"
        assert file_utils.format_file_size(1099511627776) == "1.0 TB"

        # Test format_timestamp
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC (but local time may differ)
        formatted = file_utils.format_timestamp(timestamp)
        assert isinstance(formatted, str)
        assert len(formatted) > 10  # Should be a reasonable date string

        # Test get_unique_extensions with empty list
        assert file_utils.get_unique_extensions([]) == set()

        # Test get_file_extension_stats with empty list
        assert file_utils.get_file_extension_stats([]) == {}

    def test_unique_extensions_extraction(self, temp_dir_with_files: Path) -> None:
        """Test extraction of unique file extensions."""
        files = list(temp_dir_with_files.rglob("*"))
        files = [f for f in files if f.is_file()]

        extensions = file_utils.get_unique_extensions(files)

        # Should return a set
        assert isinstance(extensions, set)

        # Should contain expected extensions
        expected_extensions = {".py", ".js", ".txt", ".json", ".md"}
        assert extensions == expected_extensions

    def test_find_functions_handle_invalid_directory(self) -> None:
        """Test that find functions handle invalid directories."""
        invalid_dir = Path("/non/existent/directory")

        with pytest.raises(SpecFileError):
            file_utils.find_largest_files(invalid_dir)

        with pytest.raises(SpecFileError):
            file_utils.find_recently_modified_files(invalid_dir)

    def test_find_functions_with_file_as_directory(self, temp_file: Path) -> None:
        """Test find functions when given a file instead of directory."""
        with pytest.raises(SpecFileError) as exc_info:
            file_utils.find_largest_files(temp_file)

        assert "not a directory" in str(exc_info.value)

    @patch("spec_cli.file_system.file_utils.debug_logger")
    def test_functions_log_operations(
        self, mock_logger: Mock, temp_dir_with_files: Path
    ) -> None:
        """Test that utility functions log their operations."""
        files = list(temp_dir_with_files.rglob("*"))
        files = [f for f in files if f.is_file()]

        # Call functions that should log
        file_utils.get_file_extension_stats(files)
        file_utils.filter_files_by_size(files, min_size=0, max_size=100)

        # Should have logged operations
        mock_logger.log.assert_called()

    def test_permission_checking_with_access_error(self, temp_file: Path) -> None:
        """Test permission checking when os.access raises an error."""
        with patch("os.access", side_effect=OSError("Permission denied")):
            result = file_utils.safe_file_operation(temp_file, "read")
            assert result is False

    def test_file_stats_excludes_directories(self, temp_dir_with_files: Path) -> None:
        """Test that file statistics functions exclude directories."""
        # Include both files and directories in the list
        all_paths = list(temp_dir_with_files.rglob("*"))

        stats = file_utils.get_file_extension_stats(all_paths)
        extensions = file_utils.get_unique_extensions(all_paths)

        # Should only count actual files, not directories
        # We know there are 6 files total
        total_counted = sum(stats.values())
        assert total_counted == 6

        # Extensions should not be empty (directories don't have extensions)
        assert len(extensions) > 0

    def test_size_filtering_handles_stat_errors(
        self, temp_dir_with_files: Path
    ) -> None:
        """Test size filtering when stat() calls fail."""
        files = list(temp_dir_with_files.rglob("*"))
        files = [f for f in files if f.is_file()]

        # Test with files that exist and work normally first
        filtered = file_utils.filter_files_by_size(files, min_size=0)
        assert len(filtered) >= 0  # Should not crash

        # Test with non-existent files (which will cause OSError in stat)
        non_existent_files = [
            Path("/non/existent/file1.txt"),
            Path("/non/existent/file2.txt"),
        ]
        filtered_non_existent = file_utils.filter_files_by_size(
            non_existent_files, min_size=0
        )
        assert filtered_non_existent == []  # Should handle gracefully
