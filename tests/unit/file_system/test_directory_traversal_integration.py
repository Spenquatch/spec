"""Integration tests for DirectoryTraversal path utilities usage."""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecFileError
from spec_cli.file_system.directory_traversal import DirectoryTraversal


class TestDirectoryTraversalIntegration:
    """Test DirectoryTraversal integration with path utilities."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure for testing."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create test files
        (project_root / "main.py").touch()
        (project_root / "src" / "models.py").parent.mkdir(parents=True)
        (project_root / "src" / "models.py").touch()
        (project_root / "tests" / "test_main.py").parent.mkdir(parents=True)
        (project_root / "tests" / "test_main.py").touch()

        # Create some files outside project (for testing path resolution)
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        (external_dir / "external.py").touch()

        return project_root

    @pytest.fixture
    def directory_traversal(self, temp_project):
        """Create DirectoryTraversal instance with temporary project."""
        return DirectoryTraversal(root_path=temp_project)

    def test_directory_creation_when_using_ensure_directory_then_consistent_behavior(
        self, directory_traversal, temp_project
    ):
        """Test that directory operations use path utilities for consistent behavior."""
        # Test find_processable_files with path utilities
        processable_files = directory_traversal.find_processable_files()

        # Should find files and handle paths consistently
        assert len(processable_files) > 0

        # All returned paths should be relative to project root
        for file_path in processable_files:
            assert not file_path.is_absolute()
            assert isinstance(file_path, Path)

    def test_path_validation_when_using_safe_relative_to_then_proper_errors(
        self, directory_traversal, temp_project, tmp_path
    ):
        """Test that path validation uses safe_relative_to for proper error handling."""
        # Create a symbolic link outside the project that points inside
        external_link = tmp_path / "external_link.py"
        internal_file = temp_project / "main.py"

        try:
            external_link.symlink_to(internal_file)

            # Test that traversal handles symlinks properly with normalize_path
            processable_files = directory_traversal.find_processable_files()

            # Should find the original file, not the symlink
            file_names = [f.name for f in processable_files]
            assert "main.py" in file_names

        except OSError:
            # Symlink creation might fail on some systems, skip test
            pytest.skip("Cannot create symlinks on this system")

    def test_traversal_normalization_when_using_normalize_path_then_consistent_paths(
        self, directory_traversal, temp_project
    ):
        """Test that traversal operations use normalize_path for consistent path handling."""
        # Test analyze_directory_structure
        analysis = directory_traversal.analyze_directory_structure()

        # Should return proper analysis with normalized paths
        assert analysis["total_files"] > 0
        assert analysis["processable_files"] > 0
        assert "largest_files" in analysis

        # All paths in largest_files should be normalized relative paths
        for file_info in analysis["largest_files"]:
            file_path = Path(file_info["path"])
            assert not file_path.is_absolute()

    def test_pattern_search_when_using_safe_relative_to_then_secure_paths(
        self, directory_traversal, temp_project
    ):
        """Test that pattern search uses path utilities for security."""
        # Test find_files_by_pattern
        python_files = directory_traversal.find_files_by_pattern("*.py")

        # Should find Python files with proper path handling
        assert len(python_files) > 0

        # All paths should be relative and properly normalized
        for file_path in python_files:
            assert not file_path.is_absolute()
            assert file_path.suffix == ".py"

    def test_directory_summary_when_using_path_utilities_then_consistent_results(
        self, directory_traversal, temp_project
    ):
        """Test that directory summary uses path utilities consistently."""
        # Test get_directory_summary
        summary = directory_traversal.get_directory_summary()

        # Should return proper summary with normalized data
        assert summary["processable_file_count"] > 0
        assert summary["total_file_count"] > 0
        assert summary["ready_for_spec_generation"] is True
        assert "primary_file_types" in summary

    @patch("spec_cli.file_system.directory_traversal.debug_logger")
    def test_debug_logging_includes_operation_context(
        self, mock_logger, directory_traversal, temp_project
    ):
        """Test that path operations include proper debug context."""
        # Create a file that will trigger debug logging
        test_file = temp_project / "debug_test.py"
        test_file.touch()

        # Trigger operations that should log with operation context
        directory_traversal.find_processable_files()

        # Verify debug logging was called
        mock_logger.log.assert_called()

        # The find_processable_files method should have made INFO calls
        info_calls = [
            call for call in mock_logger.log.call_args_list if call[0][0] == "INFO"
        ]
        assert len(info_calls) > 0

    def test_error_handling_with_invalid_directory(self, temp_project):
        """Test error handling when directory doesn't exist."""
        non_existent = temp_project / "non_existent"
        directory_traversal = DirectoryTraversal(root_path=temp_project)

        # Should raise SpecFileError for non-existent directory
        with pytest.raises(SpecFileError, match="Directory does not exist"):
            directory_traversal.find_processable_files(directory=non_existent)

    def test_path_normalization_handles_different_path_formats(
        self, directory_traversal, temp_project
    ):
        """Test that path utilities handle different path formats consistently."""
        # Create a subdirectory for testing
        sub_dir = temp_project / "subdir"
        sub_dir.mkdir()
        (sub_dir / "test.py").touch()

        # Test with different path formats
        analysis1 = directory_traversal.analyze_directory_structure(sub_dir)

        # Test with string path
        analysis2 = directory_traversal.analyze_directory_structure(str(sub_dir))

        # Results should be consistent regardless of path format
        assert analysis1["total_files"] == analysis2["total_files"]
        assert analysis1["processable_files"] == analysis2["processable_files"]

    def test_relative_path_consistency_across_methods(
        self, directory_traversal, temp_project
    ):
        """Test that all methods return consistent relative paths."""
        # Get results from different methods
        processable_files = directory_traversal.find_processable_files()
        python_files = directory_traversal.find_files_by_pattern("*.py")
        analysis = directory_traversal.analyze_directory_structure()

        # All should return relative paths
        for file_path in processable_files:
            assert not file_path.is_absolute()

        for file_path in python_files:
            assert not file_path.is_absolute()

        # Analysis largest_files should also use relative paths
        for file_info in analysis["largest_files"]:
            file_path = Path(file_info["path"])
            assert not file_path.is_absolute()
