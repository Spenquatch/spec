"""Unit tests for path_utils module - Cross-Platform Path Handling.

Test suite for path_001 slice: comprehensive cross-platform path utilities
testing for consistent path handling across Windows, macOS, and Linux.
"""

import os
import platform
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecValidationError
from spec_cli.utils.path_utils import (
    convert_to_posix_style,
    ensure_directory,
    ensure_path_permissions,
    ensure_specs_prefix,
    get_relative_path_or_absolute,
    is_specs_path,
    is_subpath,
    normalize_path,
    normalize_path_separators,
    remove_specs_prefix,
    resolve_project_root,
    safe_relative_to,
)


class TestSafeRelativeTo:
    """Test safe_relative_to function for cross-platform relative path computation."""

    def test_valid_relative_path_computation(self, tmp_path: Any) -> None:
        """Test successful relative path computation with valid paths."""
        root = tmp_path
        child_dir = tmp_path / "src" / "models"
        child_dir.mkdir(parents=True)
        child_file = child_dir / "user.py"
        child_file.write_text("# User model")

        result = safe_relative_to(child_file, root)
        expected = Path("src/models/user.py")
        assert result == expected

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        root = tmp_path
        child_dir = tmp_path / "src"
        child_dir.mkdir()
        child_file = child_dir / "main.py"
        child_file.write_text("# Main module")

        # Test string inputs
        result_str = safe_relative_to(str(child_file), str(root))
        expected = Path("src/main.py")
        assert result_str == expected

        # Test Path object inputs
        result_path = safe_relative_to(child_file, root)
        assert result_path == expected

        # Test mixed inputs
        result_mixed = safe_relative_to(str(child_file), root)
        assert result_mixed == expected

    def test_outside_root_strict_mode(self, tmp_path: Any) -> None:
        """Test error handling when path is outside root with strict=True."""
        root = tmp_path / "project"
        root.mkdir()
        outside_file = tmp_path / "outside" / "file.py"
        outside_file.parent.mkdir()
        outside_file.write_text("# Outside file")

        with pytest.raises(SpecValidationError) as exc_info:
            safe_relative_to(outside_file, root, strict=True)

        assert "is outside root" in str(exc_info.value)
        assert str(outside_file.resolve()) in str(exc_info.value)
        assert str(root.resolve()) in str(exc_info.value)

    def test_outside_root_non_strict_mode(self, tmp_path: Any) -> None:
        """Test behavior when path is outside root with strict=False."""
        root = tmp_path / "project"
        root.mkdir()
        outside_file = tmp_path / "outside" / "file.py"
        outside_file.parent.mkdir()
        outside_file.write_text("# Outside file")

        result = safe_relative_to(outside_file, root, strict=False)
        assert result == outside_file.resolve()

    def test_type_validation_path_parameter(self) -> None:
        """Test TypeError for invalid path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            safe_relative_to(123, "/root")  # type: ignore
        assert "path must be str or Path" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_type_validation_root_parameter(self) -> None:
        """Test TypeError for invalid root parameter types."""
        with pytest.raises(TypeError) as exc_info:
            safe_relative_to("/path", 123)  # type: ignore
        assert "root must be str or Path" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_cross_platform_path_separators(self, tmp_path: Any) -> None:
        """Test handling of different path separators across platforms."""
        root = tmp_path
        child_dir = tmp_path / "src" / "models"
        child_dir.mkdir(parents=True)
        child_file = child_dir / "user.py"
        child_file.write_text("# User model")

        # Test with different separator styles
        if platform.system() == "Windows":
            # On Windows, test both separator styles
            result = safe_relative_to(child_file, root)
            expected = Path("src/models/user.py")
            assert result == expected
        else:
            # On Unix-like systems, standard forward slashes
            result = safe_relative_to(child_file, root)
            expected = Path("src/models/user.py")
            assert result == expected


class TestEnsureDirectory:
    """Test ensure_directory function for cross-platform directory creation."""

    def test_create_new_directory(self, tmp_path: Any) -> None:
        """Test creating a new directory when it doesn't exist."""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_directory(new_dir)

        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directories_with_parents(self, tmp_path: Any) -> None:
        """Test creating nested directories with parents=True."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        result = ensure_directory(nested_dir, parents=True)

        assert result == nested_dir
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert nested_dir.parent.exists()

    def test_create_nested_directories_without_parents(self, tmp_path: Any) -> None:
        """Test creating nested directories with parents=False raises error."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        with pytest.raises(OSError):
            ensure_directory(nested_dir, parents=False)

    def test_existing_directory_unchanged(self, tmp_path: Any) -> None:
        """Test that existing directory is returned unchanged."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)

        assert result == existing_dir
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_existing_file_raises_error(self, tmp_path: Any) -> None:
        """Test that existing file (not directory) raises SpecValidationError."""
        existing_file = tmp_path / "existing_file.txt"
        existing_file.write_text("content")

        with pytest.raises(SpecValidationError) as exc_info:
            ensure_directory(existing_file)

        assert "exists but is not a directory" in str(exc_info.value)
        assert str(existing_file) in str(exc_info.value)

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        new_dir_str = tmp_path / "new_dir_str"
        new_dir_path = tmp_path / "new_dir_path"

        # Test string input
        result_str = ensure_directory(str(new_dir_str))
        assert result_str == new_dir_str
        assert new_dir_str.exists()

        # Test Path object input
        result_path = ensure_directory(new_dir_path)
        assert result_path == new_dir_path
        assert new_dir_path.exists()

    def test_type_validation(self) -> None:
        """Test TypeError for invalid path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            ensure_directory(123)  # type: ignore
        assert "path must be str or Path" in str(exc_info.value)
        assert "int" in str(exc_info.value)


class TestNormalizePath:
    """Test normalize_path function for cross-platform path normalization."""

    def test_normalize_relative_path(self, tmp_path: Any, monkeypatch: Any) -> None:
        """Test normalizing relative paths to absolute paths."""
        monkeypatch.chdir(tmp_path)
        relative_path = "src/main.py"

        result = normalize_path(relative_path)
        expected = tmp_path / "src" / "main.py"
        assert result == expected
        assert result.is_absolute()

    def test_normalize_dot_paths(self, tmp_path: Any, monkeypatch: Any) -> None:
        """Test normalizing paths with dots (. and ..)."""
        monkeypatch.chdir(tmp_path)
        dot_path = "./src/../main.py"

        result = normalize_path(dot_path)
        expected = tmp_path / "main.py"
        assert result == expected

    def test_absolute_path_unchanged(self, tmp_path: Any) -> None:
        """Test that absolute paths are resolved but structure maintained."""
        abs_path = tmp_path / "src" / "main.py"

        result = normalize_path(abs_path)
        assert result == abs_path.resolve()
        assert result.is_absolute()

    def test_resolve_symlinks_enabled(self, tmp_path: Any) -> None:
        """Test symlink resolution when resolve_symlinks=True."""
        # Create target file and symlink
        target_file = tmp_path / "target.py"
        target_file.write_text("# Target file")
        symlink_file = tmp_path / "symlink.py"

        # Only test on platforms that support symlinks
        try:
            symlink_file.symlink_to(target_file)

            result = normalize_path(symlink_file, resolve_symlinks=True)
            assert result == target_file.resolve()
        except OSError:
            # Skip test if symlinks are not supported
            pytest.skip("Symlinks not supported on this platform")

    def test_resolve_symlinks_disabled(self, tmp_path: Any, monkeypatch: Any) -> None:
        """Test symlink handling when resolve_symlinks=False."""
        monkeypatch.chdir(tmp_path)
        relative_path = "src/main.py"

        result = normalize_path(relative_path, resolve_symlinks=False)
        expected = tmp_path / "src" / "main.py"
        assert result == expected
        assert result.is_absolute()

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        test_path = tmp_path / "test.py"

        # Test string input
        result_str = normalize_path(str(test_path))
        assert result_str == test_path.resolve()

        # Test Path object input
        result_path = normalize_path(test_path)
        assert result_path == test_path.resolve()

    def test_type_validation(self) -> None:
        """Test TypeError for invalid path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            normalize_path(123)  # type: ignore
        assert "path must be str or Path" in str(exc_info.value)


class TestResolveProjectRoot:
    """Test resolve_project_root function for finding project root directories."""

    def test_find_git_repository_root(self, tmp_path: Any) -> None:
        """Test finding project root by .git directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "src" / "models"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)
        assert result == tmp_path

    def test_find_spec_repository_root(self, tmp_path: Any) -> None:
        """Test finding project root by .spec directory."""
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir()
        subdir = tmp_path / "src" / "models"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)
        assert result == tmp_path

    def test_find_pyproject_toml_root(self, tmp_path: Any) -> None:
        """Test finding project root by pyproject.toml file."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("[tool.poetry]")
        subdir = tmp_path / "src" / "models"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)
        assert result == tmp_path

    def test_find_package_json_root(self, tmp_path: Any) -> None:
        """Test finding project root by package.json file."""
        package_file = tmp_path / "package.json"
        package_file.write_text('{"name": "test"}')
        subdir = tmp_path / "src" / "models"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)
        assert result == tmp_path

    def test_no_project_root_found(self, tmp_path: Any) -> None:
        """Test behavior when no project root markers are found."""
        subdir = tmp_path / "isolated" / "directory"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)
        assert result == subdir.resolve()

    def test_default_start_path_current_directory(
        self, tmp_path: Any, monkeypatch: Any
    ) -> None:
        """Test using current directory as default start path."""
        monkeypatch.chdir(tmp_path)
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = resolve_project_root()
        assert result == tmp_path

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "src"
        subdir.mkdir()

        # Test string input
        result_str = resolve_project_root(str(subdir))
        assert result_str == tmp_path

        # Test Path object input
        result_path = resolve_project_root(subdir)
        assert result_path == tmp_path

    def test_type_validation(self) -> None:
        """Test TypeError for invalid start_path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            resolve_project_root(123)  # type: ignore
        assert "start_path must be str, Path, or None" in str(exc_info.value)


class TestIsSubpath:
    """Test is_subpath function for cross-platform subpath checking."""

    def test_valid_subpath_relationship(self, tmp_path: Any) -> None:
        """Test detecting valid subpath relationships."""
        parent = tmp_path
        child = tmp_path / "src" / "models" / "user.py"
        child.parent.mkdir(parents=True)
        child.write_text("# User model")

        result = is_subpath(child, parent)
        assert result is True

    def test_invalid_subpath_relationship(self, tmp_path: Any) -> None:
        """Test detecting invalid subpath relationships."""
        parent = tmp_path / "project"
        parent.mkdir()
        outside = tmp_path / "outside" / "file.py"
        outside.parent.mkdir()
        outside.write_text("# Outside file")

        result = is_subpath(outside, parent)
        assert result is False

    def test_same_path_is_subpath(self, tmp_path: Any) -> None:
        """Test that identical paths return True."""
        path = tmp_path / "test_dir"
        path.mkdir()

        result = is_subpath(path, path)
        assert result is True

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        parent = tmp_path
        child = tmp_path / "src" / "main.py"
        child.parent.mkdir()
        child.write_text("# Main module")

        # Test string inputs
        result_str = is_subpath(str(child), str(parent))
        assert result_str is True

        # Test Path object inputs
        result_path = is_subpath(child, parent)
        assert result_path is True

        # Test mixed inputs
        result_mixed = is_subpath(str(child), parent)
        assert result_mixed is True

    def test_type_validation_child_parameter(self) -> None:
        """Test TypeError for invalid child parameter types."""
        with pytest.raises(TypeError) as exc_info:
            is_subpath(123, "/parent")  # type: ignore
        assert "child must be str or Path" in str(exc_info.value)

    def test_type_validation_parent_parameter(self) -> None:
        """Test TypeError for invalid parent parameter types."""
        with pytest.raises(TypeError) as exc_info:
            is_subpath("/child", 123)  # type: ignore
        assert "parent must be str or Path" in str(exc_info.value)


class TestGetRelativePathOrAbsolute:
    """Test get_relative_path_or_absolute function for flexible path resolution."""

    def test_relative_path_under_base(self, tmp_path: Any) -> None:
        """Test returning relative path when path is under base."""
        base = tmp_path
        child = tmp_path / "src" / "models" / "user.py"
        child.parent.mkdir(parents=True)
        child.write_text("# User model")

        result = get_relative_path_or_absolute(child, base)
        expected = Path("src/models/user.py")
        assert result == expected

    def test_absolute_path_outside_base(self, tmp_path: Any) -> None:
        """Test returning absolute path when path is outside base."""
        base = tmp_path / "project"
        base.mkdir()
        outside = tmp_path / "outside" / "file.py"
        outside.parent.mkdir()
        outside.write_text("# Outside file")

        result = get_relative_path_or_absolute(outside, base)
        assert result == outside.resolve()
        assert result.is_absolute()

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        base = tmp_path
        child = tmp_path / "src" / "main.py"
        child.parent.mkdir()
        child.write_text("# Main module")

        # Test string inputs
        result_str = get_relative_path_or_absolute(str(child), str(base))
        expected = Path("src/main.py")
        assert result_str == expected

        # Test Path object inputs
        result_path = get_relative_path_or_absolute(child, base)
        assert result_path == expected

    def test_type_validation_path_parameter(self) -> None:
        """Test TypeError for invalid path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            get_relative_path_or_absolute(123, "/base")  # type: ignore
        assert "path must be str or Path" in str(exc_info.value)

    def test_type_validation_base_parameter(self) -> None:
        """Test TypeError for invalid base parameter types."""
        with pytest.raises(TypeError) as exc_info:
            get_relative_path_or_absolute("/path", 123)  # type: ignore
        assert "base must be str or Path" in str(exc_info.value)


class TestEnsurePathPermissions:
    """Test ensure_path_permissions function for permission validation."""

    def test_existing_readable_path(self, tmp_path: Any) -> None:
        """Test validation passes for existing readable path."""
        test_file = tmp_path / "readable.txt"
        test_file.write_text("content")

        # Should not raise exception
        ensure_path_permissions(test_file, require_write=False)

    def test_existing_writable_path(self, tmp_path: Any) -> None:
        """Test validation passes for existing writable path."""
        test_file = tmp_path / "writable.txt"
        test_file.write_text("content")

        # Should not raise exception
        ensure_path_permissions(test_file, require_write=True)

    def test_nonexistent_path_raises_error(self, tmp_path: Any) -> None:
        """Test SpecValidationError for non-existent path."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(SpecValidationError) as exc_info:
            ensure_path_permissions(nonexistent)

        assert "Path does not exist" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    @patch("os.access")
    def test_no_read_permission_raises_error(
        self, mock_access: Any, tmp_path: Any
    ) -> None:
        """Test SpecValidationError when path lacks read permission."""
        test_file = tmp_path / "no_read.txt"
        test_file.write_text("content")

        # Mock os.access to return False for read permission
        mock_access.side_effect = lambda path, mode: mode != os.R_OK

        with pytest.raises(SpecValidationError) as exc_info:
            ensure_path_permissions(test_file)

        assert "No read permission" in str(exc_info.value)

    @patch("os.access")
    def test_no_write_permission_raises_error(
        self, mock_access: Any, tmp_path: Any
    ) -> None:
        """Test SpecValidationError when path lacks write permission."""
        test_file = tmp_path / "no_write.txt"
        test_file.write_text("content")

        # Mock os.access to allow read but deny write
        def mock_access_func(path: Any, mode: Any) -> bool:
            if mode == os.R_OK:
                return True
            elif mode == os.W_OK:
                return False
            return True

        mock_access.side_effect = mock_access_func

        with pytest.raises(SpecValidationError) as exc_info:
            ensure_path_permissions(test_file, require_write=True)

        assert "No write permission" in str(exc_info.value)

    def test_string_and_path_object_inputs(self, tmp_path: Any) -> None:
        """Test function accepts both string and Path object inputs."""
        test_file = tmp_path / "permissions_test.txt"
        test_file.write_text("content")

        # Test string input
        ensure_path_permissions(str(test_file))

        # Test Path object input
        ensure_path_permissions(test_file)

    def test_type_validation(self) -> None:
        """Test TypeError for invalid path parameter types."""
        with pytest.raises(TypeError) as exc_info:
            ensure_path_permissions(123)  # type: ignore
        assert "path must be str or Path" in str(exc_info.value)


class TestNormalizePathSeparators:
    """Test normalize_path_separators function for cross-platform separator handling."""

    def test_windows_backslashes_to_forward_slashes(self) -> None:
        """Test converting Windows backslashes to forward slashes."""
        windows_path = r"src\models\user.py"
        result = normalize_path_separators(windows_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_mixed_separators_normalized(self) -> None:
        """Test normalizing paths with mixed separators."""
        mixed_path = r"src\models/user.py"
        result = normalize_path_separators(mixed_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_unix_forward_slashes_unchanged(self) -> None:
        """Test that Unix forward slashes remain unchanged."""
        unix_path = "src/models/user.py"
        result = normalize_path_separators(unix_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_path_object_input(self) -> None:
        """Test function accepts Path object input."""
        path_obj = Path("src") / "models" / "user.py"
        result = normalize_path_separators(path_obj)
        expected = "src/models/user.py"
        assert result == expected

    def test_empty_and_edge_cases(self) -> None:
        """Test edge cases like empty strings and single separators."""
        assert normalize_path_separators("") == ""
        assert normalize_path_separators("\\") == "/"
        assert normalize_path_separators("/") == "/"
        assert normalize_path_separators(".") == "."
        assert normalize_path_separators("..") == ".."

    def test_complex_windows_paths(self) -> None:
        """Test complex Windows paths with drive letters and UNC paths."""
        # Drive letter paths
        drive_path = r"C:\Users\user\Documents\project\src\main.py"
        result = normalize_path_separators(drive_path)
        expected = "C:/Users/user/Documents/project/src/main.py"
        assert result == expected

        # UNC paths
        unc_path = r"\\server\share\project\src\main.py"
        result = normalize_path_separators(unc_path)
        expected = "//server/share/project/src/main.py"
        assert result == expected


class TestRemoveSpecsPrefix:
    """Test remove_specs_prefix function for cross-platform .specs/ prefix removal."""

    def test_remove_unix_specs_prefix(self) -> None:
        """Test removing Unix-style .specs/ prefix."""
        specs_path = ".specs/src/models/user.py"
        result = remove_specs_prefix(specs_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_remove_windows_specs_prefix(self) -> None:
        """Test removing Windows-style .specs\\ prefix."""
        specs_path = r".specs\src\models\user.py"
        result = remove_specs_prefix(specs_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_remove_mixed_separators_specs_prefix(self) -> None:
        """Test removing .specs prefix with mixed separators."""
        specs_path = r".specs\src/models\user.py"
        result = remove_specs_prefix(specs_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_no_specs_prefix_normalizes_separators(self) -> None:
        """Test that paths without .specs prefix get separator normalization."""
        normal_path = r"src\models\user.py"
        result = remove_specs_prefix(normal_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_empty_path_after_prefix_removal(self) -> None:
        """Test handling of paths that become empty after prefix removal."""
        specs_only = ".specs/"
        result = remove_specs_prefix(specs_only)
        expected = ""
        assert result == expected

        specs_only_windows = ".specs\\"
        result = remove_specs_prefix(specs_only_windows)
        expected = ""
        assert result == expected

    def test_specs_prefix_case_sensitivity(self) -> None:
        """Test that prefix removal is case-sensitive."""
        uppercase_path = ".SPECS/src/models/user.py"
        result = remove_specs_prefix(uppercase_path)
        # Should not remove uppercase prefix, just normalize
        expected = ".SPECS/src/models/user.py"
        assert result == expected


class TestEnsureSpecsPrefix:
    """Test ensure_specs_prefix function for cross-platform .specs/ prefix handling."""

    def test_add_specs_prefix_to_normal_path(self) -> None:
        """Test adding .specs/ prefix to normal path."""
        normal_path = "src/models/user.py"
        result = ensure_specs_prefix(normal_path)
        expected = ".specs/src/models/user.py"
        assert result == expected

    def test_normalize_existing_unix_specs_prefix(self) -> None:
        """Test normalizing existing Unix-style .specs/ prefix."""
        specs_path = ".specs/src/models/user.py"
        result = ensure_specs_prefix(specs_path)
        expected = ".specs/src/models/user.py"
        assert result == expected

    def test_normalize_existing_windows_specs_prefix(self) -> None:
        """Test normalizing existing Windows-style .specs\\ prefix."""
        specs_path = r".specs\src\models\user.py"
        result = ensure_specs_prefix(specs_path)
        expected = ".specs/src/models/user.py"
        assert result == expected

    def test_normalize_mixed_separators_with_specs_prefix(self) -> None:
        """Test normalizing .specs prefix with mixed separators."""
        specs_path = r".specs\src/models\user.py"
        result = ensure_specs_prefix(specs_path)
        expected = ".specs/src/models/user.py"
        assert result == expected

    def test_path_object_input(self) -> None:
        """Test function accepts Path object input."""
        path_obj = Path("src") / "models" / "user.py"
        result = ensure_specs_prefix(path_obj)
        expected = ".specs/src/models/user.py"
        assert result == expected

    def test_empty_path_gets_specs_prefix(self) -> None:
        """Test that empty path gets .specs/ prefix."""
        empty_path = ""
        result = ensure_specs_prefix(empty_path)
        expected = ".specs/"
        assert result == expected


class TestIsSpecsPath:
    """Test is_specs_path function for cross-platform .specs/ detection."""

    def test_detect_unix_specs_path(self) -> None:
        """Test detecting Unix-style .specs/ paths."""
        specs_path = ".specs/src/models/user.py"
        result = is_specs_path(specs_path)
        assert result is True

    def test_detect_windows_specs_path(self) -> None:
        """Test detecting Windows-style .specs\\ paths."""
        specs_path = r".specs\src\models\user.py"
        result = is_specs_path(specs_path)
        assert result is True

    def test_detect_mixed_separators_specs_path(self) -> None:
        """Test detecting .specs paths with mixed separators."""
        specs_path = r".specs\src/models\user.py"
        result = is_specs_path(specs_path)
        assert result is True

    def test_reject_normal_path(self) -> None:
        """Test rejecting paths without .specs prefix."""
        normal_path = "src/models/user.py"
        result = is_specs_path(normal_path)
        assert result is False

    def test_reject_similar_but_different_prefix(self) -> None:
        """Test rejecting paths with similar but different prefixes."""
        similar_paths = [
            "specs/src/models/user.py",  # Missing dot
            ".spec/src/models/user.py",  # Singular
            ".SPECS/src/models/user.py",  # Uppercase
            "project/.specs/src/models/user.py",  # Not at start
        ]

        for path in similar_paths:
            result = is_specs_path(path)
            assert result is False, (
                f"Path '{path}' should not be detected as specs path"
            )

    def test_path_object_input(self) -> None:
        """Test function accepts Path object input."""
        specs_path_obj = Path(".specs") / "src" / "models" / "user.py"
        result = is_specs_path(specs_path_obj)
        assert result is True

        normal_path_obj = Path("src") / "models" / "user.py"
        result = is_specs_path(normal_path_obj)
        assert result is False

    def test_edge_cases(self) -> None:
        """Test edge cases like empty paths and just .specs."""
        assert is_specs_path("") is False
        assert is_specs_path(".specs") is False
        assert is_specs_path(".specs/") is True
        assert is_specs_path(".specs\\") is True


class TestConvertToPosixStyle:
    """Test convert_to_posix_style function (alias for normalize_path_separators)."""

    def test_windows_to_posix_conversion(self) -> None:
        """Test converting Windows paths to POSIX style."""
        windows_path = r"src\models\user.py"
        result = convert_to_posix_style(windows_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_posix_path_unchanged(self) -> None:
        """Test that POSIX paths remain unchanged."""
        posix_path = "src/models/user.py"
        result = convert_to_posix_style(posix_path)
        expected = "src/models/user.py"
        assert result == expected

    def test_path_object_input(self) -> None:
        """Test function accepts Path object input."""
        path_obj = Path("src") / "models" / "user.py"
        result = convert_to_posix_style(path_obj)
        expected = "src/models/user.py"
        assert result == expected

    def test_semantic_equivalence_with_normalize_path_separators(self) -> None:
        """Test that convert_to_posix_style produces same results as normalize_path_separators."""
        test_paths = [
            r"src\models\user.py",
            "src/models/user.py",
            r"src\models/user\file.py",
            "path/with/forward/slashes",
            r"path\with\back\slashes",
        ]

        for path in test_paths:
            posix_result = convert_to_posix_style(path)
            normalize_result = normalize_path_separators(path)
            assert posix_result == normalize_result, f"Results differ for path: {path}"


class TestCrossPlatformIntegration:
    """Integration tests for cross-platform path handling scenarios."""

    def test_full_specs_workflow_unix_style(self, tmp_path: Any) -> None:
        """Test complete .specs workflow with Unix-style paths."""
        # Simulate complete workflow
        original_path = "src/models/user.py"

        # Add specs prefix
        specs_path = ensure_specs_prefix(original_path)
        assert specs_path == ".specs/src/models/user.py"
        assert is_specs_path(specs_path) is True

        # Remove specs prefix
        clean_path = remove_specs_prefix(specs_path)
        assert clean_path == original_path

        # Normalize separators
        normalized = normalize_path_separators(clean_path)
        assert normalized == original_path

    def test_full_specs_workflow_windows_style(self, tmp_path: Any) -> None:
        """Test complete .specs workflow with Windows-style paths."""
        # Simulate complete workflow with Windows paths
        original_path = r"src\models\user.py"

        # Add specs prefix (should normalize)
        specs_path = ensure_specs_prefix(original_path)
        assert specs_path == ".specs/src/models/user.py"
        assert is_specs_path(specs_path) is True

        # Remove specs prefix
        clean_path = remove_specs_prefix(specs_path)
        assert clean_path == "src/models/user.py"

        # Convert to POSIX style
        posix_path = convert_to_posix_style(clean_path)
        assert posix_path == "src/models/user.py"

    def test_mixed_separator_handling(self, tmp_path: Any) -> None:
        """Test handling of paths with mixed separators."""
        mixed_path = r".specs\src/models\user.py"

        # Should detect as specs path
        assert is_specs_path(mixed_path) is True

        # Should normalize when ensuring prefix
        normalized_specs = ensure_specs_prefix(mixed_path)
        assert normalized_specs == ".specs/src/models/user.py"

        # Should clean and normalize when removing prefix
        clean_path = remove_specs_prefix(mixed_path)
        assert clean_path == "src/models/user.py"

    def test_path_resolution_with_relative_operations(self, tmp_path: Any) -> None:
        """Test path resolution combined with relative operations."""
        # Create directory structure
        project_root = tmp_path
        git_dir = project_root / ".git"
        git_dir.mkdir()

        src_dir = project_root / "src" / "models"
        src_dir.mkdir(parents=True)
        user_file = src_dir / "user.py"
        user_file.write_text("# User model")

        # Test project root resolution
        found_root = resolve_project_root(src_dir)
        assert found_root == project_root

        # Test relative path computation
        relative_path = safe_relative_to(user_file, project_root)
        expected = Path("src/models/user.py")
        assert relative_path == expected

        # Test subpath checking
        assert is_subpath(user_file, project_root) is True
        assert is_subpath(user_file, src_dir) is True

    def test_directory_operations_with_permissions(self, tmp_path: Any) -> None:
        """Test directory operations combined with permission checking."""
        # Create nested directory structure
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        # Ensure directory creation
        created_dir = ensure_directory(nested_dir, parents=True)
        assert created_dir == nested_dir
        assert nested_dir.exists()

        # Check permissions
        ensure_path_permissions(nested_dir, require_write=True)

        # Create test file and check permissions
        test_file = nested_dir / "test.txt"
        test_file.write_text("test content")
        ensure_path_permissions(test_file, require_write=True)
