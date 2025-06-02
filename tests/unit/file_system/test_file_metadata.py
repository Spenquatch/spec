import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecFileError
from spec_cli.file_system.file_metadata import FileMetadataExtractor


class TestFileMetadataExtractor:
    """Test suite for FileMetadataExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a FileMetadataExtractor instance for testing."""
        return FileMetadataExtractor()

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('Hello, World!')\n")
            f.write("# This is a test file\n")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_binary_file(self):
        """Create a temporary binary file for testing."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".jpg") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # PNG header-like data
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "test.py").write_text("print('python')")
            (temp_path / "test.js").write_text("console.log('javascript');")
            (temp_path / "README.md").write_text("# Test Project")
            (temp_path / ".hidden").write_text("hidden file")
            (temp_path / "empty.txt").touch()
            
            # Create a binary file
            (temp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            
            yield temp_path

    def test_file_metadata_extracts_basic_information(self, extractor, temp_file):
        """Test extraction of basic file information."""
        metadata = extractor.get_file_metadata(temp_file)
        
        # Check basic properties
        assert metadata["name"] == temp_file.name
        assert metadata["stem"] == temp_file.stem
        assert metadata["suffix"] == temp_file.suffix
        assert metadata["path"] == str(temp_file)
        assert metadata["parent"] == str(temp_file.parent)
        
        # Check size information
        assert metadata["size_bytes"] > 0
        assert "B" in metadata["size_formatted"]
        
        # Check timing information
        assert "modified_time" in metadata
        assert "created_time" in metadata
        assert "accessed_time" in metadata
        assert metadata["modified_datetime"] is not None
        
        # Check permissions
        assert "permissions" in metadata
        assert isinstance(metadata["is_readable"], bool)
        assert isinstance(metadata["is_writable"], bool)
        assert isinstance(metadata["is_executable"], bool)
        
        # Check file type analysis
        assert metadata["file_type"] == "python"
        assert metadata["file_category"] == "programming"
        assert metadata["is_binary"] is False
        assert metadata["is_processable"] is True

    def test_file_metadata_handles_binary_files(self, extractor, temp_binary_file):
        """Test handling of binary files."""
        metadata = extractor.get_file_metadata(temp_binary_file)
        
        assert metadata["is_binary"] is True
        assert metadata["file_type"] == "unknown"  # .jpg should be binary
        assert metadata["line_count"] is None  # No line counting for binary files

    def test_file_metadata_counts_lines_for_text_files(self, extractor, temp_file):
        """Test line counting for text files."""
        metadata = extractor.get_file_metadata(temp_file)
        
        # Our temp file has 2 lines
        assert metadata["line_count"] == 2
        assert metadata["is_binary"] is False

    def test_file_metadata_handles_permission_errors(self, extractor):
        """Test handling of files that don't exist."""
        non_existent_file = Path("/non/existent/file.py")
        
        with pytest.raises(SpecFileError) as exc_info:
            extractor.get_file_metadata(non_existent_file)
        
        assert "does not exist" in str(exc_info.value)

    def test_file_metadata_formats_sizes_correctly(self, extractor):
        """Test file size formatting."""
        # Test various sizes
        assert extractor._format_file_size(0) == "0.0 B"
        assert extractor._format_file_size(512) == "512.0 B"
        assert extractor._format_file_size(1024) == "1.0 KB"
        assert extractor._format_file_size(1536) == "1.5 KB"
        assert extractor._format_file_size(1048576) == "1.0 MB"
        assert extractor._format_file_size(1073741824) == "1.0 GB"

    def test_directory_composition_analyzes_mixed_files(self, extractor, temp_dir):
        """Test directory composition analysis with mixed file types."""
        composition = extractor.get_directory_composition(temp_dir)
        
        # Check basic stats
        assert composition["total_files"] == 6  # py, js, md, hidden, empty, png
        assert composition["total_size"] > 0
        assert "total_size_formatted" in composition
        
        # Check file type breakdown
        assert "python" in composition["file_types"]
        assert "javascript" in composition["file_types"]
        # README.md is detected as "documentation" by special filename, not "markdown" by extension
        assert "documentation" in composition["file_types"]
        
        # Check category breakdown
        assert "programming" in composition["file_categories"]
        assert "documentation" in composition["file_categories"]
        
        # Check characteristic counts
        assert composition["processable_files"] >= 3  # py, js, md
        assert composition["binary_files"] >= 1  # png
        assert composition["hidden_files"] >= 1  # .hidden
        assert composition["empty_files"] >= 1  # empty.txt
        
        # Check largest and newest file tracking
        assert composition["largest_file"] is not None
        assert composition["newest_file"] is not None

    def test_directory_composition_handles_empty_directory(self, extractor):
        """Test directory composition analysis with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            composition = extractor.get_directory_composition(temp_path)
            
            assert composition["total_files"] == 0
            assert composition["total_size"] == 0
            assert composition["processable_files"] == 0
            assert composition["binary_files"] == 0
            assert composition["hidden_files"] == 0
            assert composition["empty_files"] == 0
            assert composition["largest_file"] is None
            assert composition["newest_file"] is None

    def test_file_comparison_identifies_differences(self, extractor, temp_dir):
        """Test file comparison functionality."""
        file1 = temp_dir / "test.py"
        file2 = temp_dir / "test.js"
        
        comparison = extractor.compare_files(file1, file2)
        
        assert "same_type" in comparison
        assert "same_size" in comparison
        assert "size_difference" in comparison
        assert "newer_file" in comparison
        assert "larger_file" in comparison
        assert "both_processable" in comparison
        
        # These should be different types
        assert comparison["same_type"] is False
        # Both should be processable
        assert comparison["both_processable"] is True

    def test_metadata_handles_relative_paths(self, extractor):
        """Test that metadata extractor handles relative paths correctly."""
        # Use pyproject.toml which we know exists in the current directory
        relative_path = Path("pyproject.toml")
        
        metadata = extractor.get_file_metadata(relative_path)
        
        # Should still extract metadata correctly
        assert metadata["name"] == "pyproject.toml"
        assert metadata["file_type"] == "toml"

    @patch("spec_cli.file_system.file_metadata.debug_logger")
    def test_metadata_logs_operations(self, mock_logger, extractor, temp_file):
        """Test that metadata operations are logged."""
        extractor.get_file_metadata(temp_file)
        
        # Should have logged the metadata extraction
        mock_logger.log.assert_called()
        
        # Check that DEBUG level was used
        calls = mock_logger.log.call_args_list
        debug_calls = [call for call in calls if call[0][0] == "DEBUG"]
        assert len(debug_calls) > 0

    def test_line_counting_handles_encoding_issues(self, extractor):
        """Test line counting with different encodings."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            # Write some Latin-1 encoded text
            f.write("Hello\nWörld\n".encode("latin-1"))
            temp_path = Path(f.name)
        
        try:
            count = extractor._count_lines(temp_path)
            assert count == 2  # Should count lines despite encoding issues
        finally:
            temp_path.unlink()

    @patch("pathlib.Path.stat")
    def test_metadata_handles_stat_errors(self, mock_stat, extractor, temp_file):
        """Test handling of OS errors during stat operations."""
        mock_stat.side_effect = OSError("Permission denied")
        
        with pytest.raises(SpecFileError) as exc_info:
            extractor.get_file_metadata(temp_file)
        
        assert "Cannot access file metadata" in str(exc_info.value)

    def test_directory_composition_handles_non_directory(self, extractor, temp_file):
        """Test directory composition with non-directory path."""
        with pytest.raises(SpecFileError) as exc_info:
            extractor.get_directory_composition(temp_file)
        
        assert "not a directory" in str(exc_info.value)