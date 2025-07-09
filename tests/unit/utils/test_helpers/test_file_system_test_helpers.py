"""Unit tests for file system test infrastructure helpers.

This module provides comprehensive test coverage for the file system test
infrastructure, validating all helper classes and their functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.utils.test_helpers.file_system_test_helpers import (
    CrossPlatformPathValidator,
    FilePermissionMocker,
    TempFileStructureBuilder,
    create_cross_platform_path_validator,
    create_file_permission_mocker,
    create_temp_file_structure,
)


class TestTempFileStructureBuilder:
    """Unit tests for TempFileStructureBuilder."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.builder = TempFileStructureBuilder(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, "builder"):
            self.builder.cleanup()

    def test_init_creates_builder_with_base_path(self):
        """Test builder initialization with base path."""
        assert self.builder.base_path == self.temp_dir.resolve()
        assert self.builder.structure == {}
        assert self.builder.permissions == {}
        assert self.builder.created_paths == set()

    def test_add_file_stores_file_configuration(self):
        """Test adding file to structure stores configuration."""
        result = self.builder.add_file("test.txt", "content", 0o644)

        assert result is self.builder  # Method chaining
        assert "test.txt" in self.builder.structure
        assert self.builder.structure["test.txt"]["type"] == "file"
        assert self.builder.structure["test.txt"]["content"] == "content"
        assert self.builder.permissions["test.txt"] == 0o644

    def test_add_file_normalizes_path_separators(self):
        """Test file paths are normalized across platforms."""
        self.builder.add_file("dir\\subdir\\test.txt", "content")

        assert "dir/subdir/test.txt" in self.builder.structure
        assert "dir\\subdir\\test.txt" not in self.builder.structure

    def test_add_file_without_permissions_omits_permission_config(self):
        """Test adding file without permissions doesn't set permissions."""
        self.builder.add_file("test.txt", "content")

        assert "test.txt" not in self.builder.permissions

    def test_add_directory_stores_directory_configuration(self):
        """Test adding directory to structure stores configuration."""
        result = self.builder.add_directory("testdir", 0o755)

        assert result is self.builder  # Method chaining
        assert "testdir" in self.builder.structure
        assert self.builder.structure["testdir"]["type"] == "directory"
        assert self.builder.permissions["testdir"] == 0o755

    def test_add_directory_normalizes_path_separators(self):
        """Test directory paths are normalized across platforms."""
        self.builder.add_directory("dir\\subdir")

        assert "dir/subdir" in self.builder.structure
        assert "dir\\subdir" not in self.builder.structure

    def test_add_symlink_stores_symlink_configuration(self):
        """Test adding symlink to structure stores configuration."""
        result = self.builder.add_symlink("link.txt", "target.txt")

        assert result is self.builder  # Method chaining
        assert "link.txt" in self.builder.structure
        assert self.builder.structure["link.txt"]["type"] == "symlink"
        assert self.builder.structure["link.txt"]["target"] == "target.txt"

    def test_add_symlink_normalizes_both_paths(self):
        """Test symlink paths are normalized across platforms."""
        self.builder.add_symlink("dir\\link.txt", "target\\file.txt")

        assert "dir/link.txt" in self.builder.structure
        assert self.builder.structure["dir/link.txt"]["target"] == "target/file.txt"

    def test_build_creates_files_on_disk(self):
        """Test build creates actual files on disk."""
        self.builder.add_file("test.txt", "test content")
        self.builder.add_directory("testdir")

        result_path = self.builder.build()

        # Compare resolved paths since macOS may have symlink differences
        assert result_path.resolve() == self.temp_dir.resolve()
        assert (self.temp_dir / "test.txt").exists()
        assert (self.temp_dir / "test.txt").read_text() == "test content"
        assert (self.temp_dir / "testdir").is_dir()

    def test_build_creates_nested_structure(self):
        """Test build creates nested directory structures."""
        self.builder.add_directory("parent/child")
        self.builder.add_file("parent/child/file.txt", "nested content")

        self.builder.build()

        assert (self.temp_dir / "parent").is_dir()
        assert (self.temp_dir / "parent" / "child").is_dir()
        assert (self.temp_dir / "parent" / "child" / "file.txt").exists()
        assert (
            self.temp_dir / "parent" / "child" / "file.txt"
        ).read_text() == "nested content"

    def test_build_sets_permissions_when_specified(self):
        """Test build sets file permissions when specified."""
        self.builder.add_file("test.txt", "content", 0o600)

        self.builder.build()

        file_path = self.temp_dir / "test.txt"
        file_mode = file_path.stat().st_mode & 0o777
        assert file_mode == 0o600

    def test_build_creates_symlinks(self):
        """Test build creates symbolic links."""
        self.builder.add_file("target.txt", "target content")
        self.builder.add_symlink("link.txt", "target.txt")

        self.builder.build()

        link_path = self.temp_dir / "link.txt"
        target_path = self.temp_dir / "target.txt"

        assert link_path.is_symlink()
        assert link_path.resolve() == target_path.resolve()

    def test_build_handles_creation_errors(self):
        """Test build handles file creation errors gracefully."""
        # Create a file that will conflict with directory creation
        conflicting_file = self.temp_dir / "conflict"
        conflicting_file.write_text("blocking content")

        self.builder.add_directory("conflict/subdir")

        with pytest.raises(OSError, match="Failed to create file structure"):
            self.builder.build()

    def test_cleanup_removes_created_structure(self):
        """Test cleanup removes all created files and directories."""
        self.builder.add_file("test.txt", "content")
        self.builder.add_directory("testdir")
        self.builder.build()

        # Verify files exist
        assert (self.temp_dir / "test.txt").exists()
        assert (self.temp_dir / "testdir").exists()

        self.builder.cleanup()

        # Verify files are removed
        assert not self.temp_dir.exists()

    def test_cleanup_handles_missing_directory(self):
        """Test cleanup handles case where directory doesn't exist."""
        # Don't build anything, just try to cleanup
        self.builder.cleanup()  # Should not raise exception

    @patch("shutil.rmtree")
    def test_cleanup_handles_removal_errors(self, mock_rmtree):
        """Test cleanup handles removal errors gracefully."""
        mock_rmtree.side_effect = OSError("Permission denied")

        self.builder.build()
        self.builder.cleanup()  # Should not raise exception


class TestFilePermissionMocker:
    """Unit tests for FilePermissionMocker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mocker = FilePermissionMocker()

    def test_init_creates_empty_mocker(self):
        """Test mocker initialization."""
        assert self.mocker.mocked_permissions == {}
        assert self.mocker.active_patches == []

    def test_set_file_permissions_stores_permissions(self):
        """Test setting file permissions stores configuration."""
        self.mocker.set_file_permissions("/test/path", 0o755)

        assert "/test/path" in self.mocker.mocked_permissions
        assert self.mocker.mocked_permissions["/test/path"] == 0o755

    def test_set_file_permissions_normalizes_path(self):
        """Test permission setting normalizes path separators."""
        self.mocker.set_file_permissions("test\\path\\file.txt", 0o644)

        assert "test/path/file.txt" in self.mocker.mocked_permissions
        assert "test\\path\\file.txt" not in self.mocker.mocked_permissions

    def test_make_readonly_sets_readonly_permissions(self):
        """Test make_readonly sets read-only permissions."""
        self.mocker.make_readonly("/test/file.txt")

        assert self.mocker.mocked_permissions["/test/file.txt"] == 0o444

    def test_make_writable_sets_writable_permissions(self):
        """Test make_writable sets writable permissions."""
        self.mocker.make_writable("/test/file.txt")

        assert self.mocker.mocked_permissions["/test/file.txt"] == 0o644

    def test_make_executable_sets_executable_permissions(self):
        """Test make_executable sets executable permissions."""
        self.mocker.make_executable("/test/file.txt")

        assert self.mocker.mocked_permissions["/test/file.txt"] == 0o755

    def test_remove_all_permissions_sets_no_permissions(self):
        """Test remove_all_permissions sets no permissions."""
        self.mocker.remove_all_permissions("/test/file.txt")

        assert self.mocker.mocked_permissions["/test/file.txt"] == 0o000

    def test_mock_permissions_context_manager_applies_patches(self):
        """Test permission mocking context manager applies patches."""
        self.mocker.set_file_permissions("/test/file.txt", 0o644)

        with self.mocker.mock_permissions():
            assert len(self.mocker.active_patches) == 3

        # Patches should be cleaned up
        assert len(self.mocker.active_patches) == 0

    def test_mock_stat_returns_configured_permissions(self):
        """Test mocked stat returns configured permissions."""
        test_path = "/test/file.txt"
        self.mocker.set_file_permissions(test_path, 0o755)

        with self.mocker.mock_permissions():
            stat_result = os.stat(test_path)
            assert stat_result.st_mode == 0o755

    def test_mock_access_respects_configured_permissions(self):
        """Test mocked access respects configured permissions."""
        test_path = "/test/file.txt"
        self.mocker.set_file_permissions(test_path, 0o400)  # Read-only

        with self.mocker.mock_permissions():
            assert os.access(test_path, os.R_OK)  # Should have read access
            assert not os.access(test_path, os.W_OK)  # Should not have write access
            assert not os.access(test_path, os.X_OK)  # Should not have execute access

    def test_mock_access_allows_multiple_permission_checks(self):
        """Test mocked access handles combined permission checks."""
        test_path = "/test/file.txt"
        self.mocker.set_file_permissions(test_path, 0o755)  # Read, write, execute

        with self.mocker.mock_permissions():
            assert os.access(test_path, os.R_OK | os.W_OK)  # Combined check
            assert os.access(test_path, os.R_OK | os.X_OK)  # Combined check

    def test_mock_permissions_falls_back_for_unmocked_paths(self):
        """Test permission mocking falls back to real OS for unmocked paths."""
        # Don't mock any paths

        with patch("os.stat") as mock_real_stat, patch("os.access") as mock_real_access:
            mock_real_stat.return_value = Mock(spec=[])
            mock_real_access.return_value = True

            with self.mocker.mock_permissions():
                os.stat("/unmocked/path")
                os.access("/unmocked/path", os.R_OK)

            # Real functions should have been called
            mock_real_stat.assert_called_once_with("/unmocked/path")
            mock_real_access.assert_called_once_with("/unmocked/path", os.R_OK)


class TestCrossPlatformPathValidator:
    """Unit tests for CrossPlatformPathValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = CrossPlatformPathValidator()

    def test_init_creates_empty_validator(self):
        """Test validator initialization."""
        assert self.validator.validation_results == []

    def test_validate_path_normalization_with_correct_normalization(self):
        """Test path normalization validation with correct input."""
        result = self.validator.validate_path_normalization(
            "path\\to\\file.txt", "path/to/file.txt"
        )

        assert result is True
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is True

    def test_validate_path_normalization_with_incorrect_normalization(self):
        """Test path normalization validation with incorrect expected result."""
        result = self.validator.validate_path_normalization(
            "path\\to\\file.txt",
            "path\\to\\file.txt",  # Not normalized
        )

        assert result is False
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is False

    def test_validate_relative_path_handling_with_safe_path(self):
        """Test relative path validation with safe relative path."""
        base_path = Path("/base")
        result = self.validator.validate_relative_path_handling(
            base_path, "subdir/file.txt"
        )

        assert result is True
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is True

    def test_validate_relative_path_handling_with_path_traversal(self):
        """Test relative path validation with path traversal attempt."""
        base_path = Path("/base")
        result = self.validator.validate_relative_path_handling(base_path, "../outside")

        assert result is False
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is False

    def test_validate_relative_path_handling_with_invalid_path(self):
        """Test relative path validation with invalid path characters."""
        base_path = Path("/base")

        # Use a path that would cause resolution to fail
        with patch("pathlib.Path.resolve", side_effect=OSError("Invalid path")):
            result = self.validator.validate_relative_path_handling(
                base_path, "invalid\x00path"
            )

        assert result is False
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is False
        assert "error" in self.validator.validation_results[0]

    def test_validate_absolute_path_detection_with_absolute_path(self):
        """Test absolute path detection with actual absolute path."""
        result = self.validator.validate_absolute_path_detection("/absolute/path", True)

        assert result is True
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is True

    def test_validate_absolute_path_detection_with_relative_path(self):
        """Test absolute path detection with relative path."""
        result = self.validator.validate_absolute_path_detection("relative/path", False)

        assert result is True
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is True

    def test_validate_absolute_path_detection_with_incorrect_expectation(self):
        """Test absolute path detection with incorrect expectation."""
        result = self.validator.validate_absolute_path_detection(
            "/absolute/path", False
        )

        assert result is False
        assert len(self.validator.validation_results) == 1
        assert self.validator.validation_results[0]["valid"] is False

    def test_get_validation_summary_with_mixed_results(self):
        """Test validation summary with mixed pass/fail results."""
        # Add some passing and failing validations
        self.validator.validate_path_normalization(
            "path\\file.txt", "path/file.txt"
        )  # Pass
        self.validator.validate_absolute_path_detection("/abs", False)  # Fail
        self.validator.validate_relative_path_handling(Path("/base"), "subdir")  # Pass

        summary = self.validator.get_validation_summary()

        assert summary["total_tests"] == 3
        assert summary["passed_tests"] == 2
        assert summary["failed_tests"] == 1
        assert summary["success_rate"] == 2 / 3
        assert len(summary["results"]) == 3

    def test_get_validation_summary_with_no_results(self):
        """Test validation summary with no validation results."""
        summary = self.validator.get_validation_summary()

        assert summary["total_tests"] == 0
        assert summary["passed_tests"] == 0
        assert summary["failed_tests"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["results"] == []


class TestFactoryFunctions:
    """Unit tests for factory functions."""

    def test_create_temp_file_structure_returns_builder(self):
        """Test factory function returns TempFileStructureBuilder."""
        base_path = Path("/test")
        builder = create_temp_file_structure(base_path)

        assert isinstance(builder, TempFileStructureBuilder)
        assert builder.base_path == base_path

    def test_create_file_permission_mocker_returns_mocker(self):
        """Test factory function returns FilePermissionMocker."""
        mocker = create_file_permission_mocker()

        assert isinstance(mocker, FilePermissionMocker)
        assert mocker.mocked_permissions == {}

    def test_create_cross_platform_path_validator_returns_validator(self):
        """Test factory function returns CrossPlatformPathValidator."""
        validator = create_cross_platform_path_validator()

        assert isinstance(validator, CrossPlatformPathValidator)
        assert validator.validation_results == []


class TestIntegrationScenarios:
    """Integration tests combining multiple helpers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.builder = TempFileStructureBuilder(self.temp_dir)
        self.mocker = FilePermissionMocker()
        self.validator = CrossPlatformPathValidator()

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, "builder"):
            self.builder.cleanup()

    def test_complete_file_system_test_workflow(self):
        """Test complete workflow using all helpers together."""
        # Build file structure
        self.builder.add_file("config.txt", "key=value", 0o600)
        self.builder.add_directory("data", 0o755)
        self.builder.add_file("data/important.txt", "sensitive data")
        structure_path = self.builder.build()

        # Validate cross-platform behavior
        assert self.validator.validate_path_normalization(
            "data\\important.txt", "data/important.txt"
        )
        assert self.validator.validate_relative_path_handling(
            structure_path, "data/important.txt"
        )

        # Test with permission mocking - set up path correctly
        config_path_str = str(structure_path / "config.txt")
        self.mocker.set_file_permissions(config_path_str, 0o444)  # Make it read-only

        # Test with permission mocking
        with self.mocker.mock_permissions():
            # File should have mocked permissions
            assert not os.access(config_path_str, os.W_OK)  # Should be read-only
            assert os.access(config_path_str, os.R_OK)  # Should be readable

        # Validate results
        summary = self.validator.get_validation_summary()
        assert summary["total_tests"] == 2
        assert summary["passed_tests"] == 2

    def test_error_handling_across_helpers(self):
        """Test error handling works consistently across helpers."""
        # Test builder error handling with a more reliable conflict scenario
        self.builder.add_directory("existing_dir")
        structure_path = self.builder.build()

        # Create a real file to conflict with
        conflict_file = structure_path / "existing_dir"
        conflict_file.rmdir()  # Remove the directory
        conflict_file.write_text("blocking content")  # Create file with same name

        # Now try to create directory with same name - should fail
        new_builder = TempFileStructureBuilder(structure_path)
        new_builder.add_directory("existing_dir/subdir")  # This should conflict

        with pytest.raises(OSError, match="Failed to create file structure"):
            new_builder.build()

        # Test validator error handling with invalid paths
        result = self.validator.validate_relative_path_handling(
            Path("/nonexistent"), "../../../etc/passwd"
        )
        assert result is False

        # Test mocker cleanup after exceptions
        self.mocker.set_file_permissions("/test", 0o755)
        try:
            with self.mocker.mock_permissions():
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Patches should still be cleaned up
        assert len(self.mocker.active_patches) == 0
