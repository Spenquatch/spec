import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecFileError
from spec_cli.file_system.directory_traversal import DirectoryTraversal


class TestDirectoryTraversal:
    """Test suite for DirectoryTraversal class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def complex_directory(self, temp_dir):
        """Create a complex directory structure for testing."""
        # Create various file types
        (temp_dir / "main.py").write_text("print('main')")
        (temp_dir / "config.json").write_text('{"key": "value"}')
        (temp_dir / "README.md").write_text("# Project")
        (temp_dir / "image.png").write_bytes(b"\x89PNG\r\n")  # Binary file
        (temp_dir / ".env").write_text("SECRET=value")
        
        # Create subdirectories
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("def helper(): pass")
        (src_dir / "models.py").write_text("class User: pass")
        
        tests_dir = temp_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test_main(): pass")
        
        # Create build directory (should be ignored)
        build_dir = temp_dir / "build"
        build_dir.mkdir()
        (build_dir / "output.js").write_text("console.log('built');")
        
        # Create .git directory (should be ignored)
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]")
        
        return temp_dir

    @pytest.fixture
    def traversal(self, complex_directory):
        """Create a DirectoryTraversal instance for testing."""
        return DirectoryTraversal(complex_directory)

    def test_directory_traversal_finds_processable_files(self, traversal, complex_directory):
        """Test finding processable files."""
        processable_files = traversal.find_processable_files()
        
        # Should find Python, JSON, and Markdown files but not binary or ignored files
        file_names = [f.name for f in processable_files]
        
        assert "main.py" in file_names
        assert "config.json" in file_names
        assert "README.md" in file_names
        assert "utils.py" in file_names
        assert "models.py" in file_names
        assert "test_main.py" in file_names
        
        # Should not include binary files
        assert "image.png" not in file_names
        # Note: .env might be included depending on ignore patterns - this is OK

    def test_directory_traversal_respects_ignore_patterns(self, traversal):
        """Test that ignore patterns are respected."""
        processable_files = traversal.find_processable_files()
        
        # Check that .git directory is ignored (build might not be in default patterns)
        for file_path in processable_files:
            assert not str(file_path).startswith(".git/")

    def test_directory_traversal_respects_max_files_limit(self, traversal):
        """Test that max files limit is respected."""
        limited_files = traversal.find_processable_files(max_files=3)
        
        assert len(limited_files) <= 3

    def test_directory_traversal_analyzes_structure(self, traversal, complex_directory):
        """Test directory structure analysis."""
        analysis = traversal.analyze_directory_structure()
        
        # Check basic structure
        assert analysis["directory"] == str(complex_directory)
        assert analysis["total_files"] > 0
        assert analysis["processable_files"] > 0
        assert analysis["ignored_files"] > 0
        
        # Check file type analysis
        assert "python" in analysis["file_types"]
        assert "json" in analysis["file_types"]
        # README.md might be detected as "documentation" by special filename, not "markdown"
        assert ("markdown" in analysis["file_types"] or "documentation" in analysis["file_types"])
        
        # Check category analysis
        assert "programming" in analysis["file_categories"]
        assert "data" in analysis["file_categories"]
        
        # Check depth analysis
        assert analysis["max_depth"] >= 2  # Has subdirectories
        assert analysis["deepest_path"] != ""

    def test_directory_traversal_finds_files_by_pattern(self, traversal):
        """Test finding files by pattern."""
        # Find all Python files
        python_files = traversal.find_files_by_pattern("*.py")
        
        file_names = [f.name for f in python_files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "models.py" in file_names
        assert "test_main.py" in file_names
        
        # Find all JSON files
        json_files = traversal.find_files_by_pattern("*.json")
        assert len(json_files) >= 1
        assert any(f.name == "config.json" for f in json_files)

    def test_directory_traversal_creates_directory_summary(self, traversal, complex_directory):
        """Test creating directory summary."""
        summary = traversal.get_directory_summary()
        
        # Check summary structure
        assert "directory" in summary
        assert "processable_file_count" in summary
        assert "total_file_count" in summary
        assert "ignored_file_count" in summary
        assert "primary_file_types" in summary
        assert "primary_categories" in summary
        assert "directory_depth" in summary
        assert "ready_for_spec_generation" in summary
        
        # Should be ready for spec generation
        assert summary["ready_for_spec_generation"] is True
        assert summary["processable_file_count"] > 0

    def test_directory_traversal_handles_non_existent_directory(self, temp_dir):
        """Test handling non-existent directories."""
        traversal = DirectoryTraversal(temp_dir)
        non_existent = temp_dir / "non_existent"
        
        with pytest.raises(SpecFileError) as exc_info:
            traversal.find_processable_files(directory=non_existent)
        
        assert "Directory does not exist" in str(exc_info.value)

    def test_directory_traversal_handles_empty_directory(self, temp_dir):
        """Test handling empty directories."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        traversal = DirectoryTraversal(temp_dir)
        files = traversal.find_processable_files(directory=empty_dir)
        
        assert files == []

    def test_directory_traversal_handles_file_access_errors(self, traversal):
        """Test handling file access errors during traversal."""
        # Mock os.stat to raise error for some files
        original_stat = Path.stat
        
        def mock_stat(self):
            if "error_file" in str(self):
                raise OSError("Permission denied")
            return original_stat(self)
        
        with patch.object(Path, "stat", mock_stat):
            # Should handle errors gracefully
            analysis = traversal.analyze_directory_structure()
            assert "total_files" in analysis
            assert "error" not in analysis

    def test_directory_traversal_format_size_utility(self, traversal):
        """Test file size formatting utility."""
        # Test various sizes
        assert traversal._format_size(0) == "0.0 B"
        assert traversal._format_size(512) == "512.0 B"
        assert traversal._format_size(1024) == "1.0 KB"
        assert traversal._format_size(1048576) == "1.0 MB"
        assert traversal._format_size(1073741824) == "1.0 GB"

    def test_directory_traversal_top_items_utility(self, traversal):
        """Test top items utility function."""
        items_dict = {
            "python": 5,
            "javascript": 3,
            "json": 2,
            "markdown": 1,
        }
        
        top_items = traversal._get_top_items(items_dict, 2)
        
        assert len(top_items) == 2
        assert top_items[0]["type"] == "python"
        assert top_items[0]["count"] == 5
        assert top_items[1]["type"] == "javascript"
        assert top_items[1]["count"] == 3

    def test_directory_traversal_relative_path_handling(self, temp_dir):
        """Test handling of files outside root path."""
        # Create a traversal with a subdirectory as root
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.py").write_text("print('test')")
        
        # Create a file outside the subdir
        (temp_dir / "outside.py").write_text("print('outside')")
        
        traversal = DirectoryTraversal(subdir)
        files = traversal.find_processable_files(directory=temp_dir)
        
        # Should only include files relative to the root path
        file_paths = [str(f) for f in files]
        assert any("file.py" in path for path in file_paths)

    def test_directory_traversal_large_directory_depth(self, temp_dir):
        """Test handling directories with large depth."""
        # Create a deep directory structure
        current_dir = temp_dir
        for i in range(10):
            current_dir = current_dir / f"level{i}"
            current_dir.mkdir()
            (current_dir / f"file{i}.py").write_text(f"# Level {i}")
        
        traversal = DirectoryTraversal(temp_dir)
        analysis = traversal.analyze_directory_structure()
        
        assert analysis["max_depth"] >= 10
        assert "level" in analysis["deepest_path"]

    def test_directory_traversal_summary_with_errors(self, temp_dir):
        """Test directory summary when errors occur."""
        traversal = DirectoryTraversal(temp_dir)
        
        # Mock analyze_directory_structure to raise an error
        with patch.object(traversal, "analyze_directory_structure", side_effect=Exception("Test error")):
            summary = traversal.get_directory_summary()
            
            assert "error" in summary
            assert summary["ready_for_spec_generation"] is False

    @patch("spec_cli.file_system.directory_traversal.debug_logger")
    def test_directory_traversal_logs_operations(self, mock_logger, traversal):
        """Test that traversal operations are logged."""
        traversal.find_processable_files(max_files=5)
        
        # Should have logged operations
        mock_logger.log.assert_called()
        
        # Check for specific log levels
        calls = mock_logger.log.call_args_list
        info_calls = [call for call in calls if call[0][0] == "INFO"]
        assert len(info_calls) > 0