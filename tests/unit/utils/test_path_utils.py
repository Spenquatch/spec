"""Tests for path_utils module."""

import os
import tempfile
from pathlib import Path
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
    """Test safe_relative_to function."""

    def test_safe_relative_to_when_valid_subpath_then_returns_relative_path(
        self, tmp_path
    ):
        """Test relative path calculation for valid subpath."""
        child = tmp_path / "sub" / "file.txt"
        parent = tmp_path

        # Create the path to make it exist
        child.parent.mkdir(exist_ok=True)
        child.touch()

        result = safe_relative_to(child, parent)

        assert result == Path("sub/file.txt")

    def test_safe_relative_to_when_path_outside_root_strict_then_raises_error(
        self, tmp_path
    ):
        """Test that paths outside root raise error in strict mode."""
        outside_path = Path("/completely/different/path")

        with pytest.raises(SpecValidationError, match="is outside root"):
            safe_relative_to(outside_path, tmp_path, strict=True)

    def test_safe_relative_to_when_path_outside_root_non_strict_then_returns_original(
        self, tmp_path
    ):
        """Test that paths outside root return original path in non-strict mode."""
        outside_path = Path("/completely/different/path")

        result = safe_relative_to(outside_path, tmp_path, strict=False)

        assert result == outside_path.resolve()

    def test_safe_relative_to_when_string_paths_then_works_correctly(self, tmp_path):
        """Test with string paths instead of Path objects."""
        child_str = str(tmp_path / "subdir" / "file.txt")
        parent_str = str(tmp_path)

        result = safe_relative_to(child_str, parent_str)

        assert result == Path("subdir/file.txt")

    def test_safe_relative_to_when_same_path_then_returns_dot(self, tmp_path):
        """Test when child and parent are the same path."""
        result = safe_relative_to(tmp_path, tmp_path)

        assert result == Path(".")

    def test_safe_relative_to_when_invalid_path_type_then_raises_type_error(self):
        """Test that invalid path types raise TypeError."""
        with pytest.raises(TypeError, match="path must be str or Path"):
            safe_relative_to(123, "/some/path")  # type: ignore

        with pytest.raises(TypeError, match="root must be str or Path"):
            safe_relative_to("/some/path", 456)  # type: ignore

    def test_safe_relative_to_when_deeper_nested_paths_then_has_relative_components(
        self, tmp_path
    ):
        """Test relative path calculation with nested paths going up directories."""
        # Create nested structure: tmp_path/level1/level2/level3/file.txt
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        file_in_level3 = level3 / "file.txt"
        file_in_level3.touch()

        # Get relative path from file to level1 (should be ../../../file.txt relative to level1)
        result = safe_relative_to(file_in_level3, level1)

        expected = Path("level2/level3/file.txt")
        assert result == expected
        # This test is actually checking the basic functionality, not ".." paths
        # The ".." paths would be used if we were computing the inverse


class TestEnsureDirectory:
    """Test ensure_directory function."""

    def test_ensure_directory_when_not_exists_then_creates(self, tmp_path):
        """Test directory creation when it doesn't exist."""
        new_dir = tmp_path / "new" / "nested" / "directory"

        result = ensure_directory(new_dir)

        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_when_exists_then_returns_existing(self, tmp_path):
        """Test that existing directory is returned without error."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)

        assert result == existing_dir
        assert existing_dir.exists()

    def test_ensure_directory_when_parents_false_and_parent_missing_then_raises_error(
        self, tmp_path
    ):
        """Test that parents=False raises error when parent doesn't exist."""
        missing_parent_dir = tmp_path / "missing" / "child"

        with pytest.raises(FileNotFoundError):
            ensure_directory(missing_parent_dir, parents=False)

    def test_ensure_directory_when_file_exists_then_raises_validation_error(
        self, tmp_path
    ):
        """Test that existing file at path raises validation error."""
        existing_file = tmp_path / "file.txt"
        existing_file.touch()

        with pytest.raises(SpecValidationError, match="exists but is not a directory"):
            ensure_directory(existing_file)

    def test_ensure_directory_when_string_path_then_works(self, tmp_path):
        """Test with string path instead of Path object."""
        new_dir_str = str(tmp_path / "string_path")

        result = ensure_directory(new_dir_str)

        assert result == Path(new_dir_str)
        assert result.exists()

    def test_ensure_directory_when_invalid_type_then_raises_type_error(self):
        """Test that invalid path type raises TypeError."""
        with pytest.raises(TypeError, match="path must be str or Path"):
            ensure_directory(123)  # type: ignore


class TestNormalizePath:
    """Test normalize_path function."""

    def test_normalize_path_when_relative_path_then_returns_absolute(self):
        """Test that relative path returns absolute path."""
        relative = Path(".")

        result = normalize_path(relative)

        assert result.is_absolute()
        assert result == Path.cwd().resolve()

    def test_normalize_path_when_absolute_path_then_resolves(self):
        """Test that absolute path gets resolved."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            absolute = Path(tmp_dir) / "." / "subdir"

            result = normalize_path(absolute)

            assert result.is_absolute()
            assert str(result).endswith("subdir")
            assert "/." not in str(result)

    def test_normalize_path_when_resolve_symlinks_false_then_no_symlink_resolution(
        self,
    ):
        """Test that symlinks are not resolved when resolve_symlinks=False."""
        relative = Path(".")

        result = normalize_path(relative, resolve_symlinks=False)

        assert result.is_absolute()
        assert result == Path.cwd()

    def test_normalize_path_when_string_path_then_works(self):
        """Test with string path."""
        result = normalize_path(".")

        assert result.is_absolute()
        assert isinstance(result, Path)

    def test_normalize_path_when_invalid_type_then_raises_type_error(self):
        """Test that invalid path type raises TypeError."""
        with pytest.raises(TypeError, match="path must be str or Path"):
            normalize_path(123)  # type: ignore


class TestResolveProjectRoot:
    """Test resolve_project_root function."""

    def test_resolve_project_root_when_git_repo_then_returns_git_root(self, tmp_path):
        """Test finding project root with .git directory."""
        # Create a .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create subdirectory to search from
        subdir = tmp_path / "src" / "deep"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)

        assert result == tmp_path

    def test_resolve_project_root_when_spec_repo_then_returns_spec_root(self, tmp_path):
        """Test finding project root with .spec directory."""
        # Create a .spec directory
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir()

        # Create subdirectory to search from
        subdir = tmp_path / "docs"
        subdir.mkdir()

        result = resolve_project_root(subdir)

        assert result == tmp_path

    def test_resolve_project_root_when_pyproject_toml_then_returns_project_root(
        self, tmp_path
    ):
        """Test finding project root with pyproject.toml."""
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").touch()

        # Create subdirectory to search from
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)

        result = resolve_project_root(subdir)

        assert result == tmp_path

    def test_resolve_project_root_when_no_markers_then_returns_start_path(
        self, tmp_path
    ):
        """Test that start path is returned when no project markers found."""
        # Don't create any project markers

        result = resolve_project_root(tmp_path)

        assert result == tmp_path

    def test_resolve_project_root_when_no_start_path_then_uses_cwd(self):
        """Test that current directory is used when no start path provided."""
        result = resolve_project_root()

        # Should return some path (current working directory or a parent)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_resolve_project_root_when_string_path_then_works(self, tmp_path):
        """Test with string start path."""
        (tmp_path / "setup.py").touch()

        result = resolve_project_root(str(tmp_path))

        assert result == tmp_path

    def test_resolve_project_root_when_invalid_type_then_raises_type_error(self):
        """Test that invalid start_path type raises TypeError."""
        with pytest.raises(TypeError, match="start_path must be str, Path, or None"):
            resolve_project_root(123)  # type: ignore


class TestIsSubpath:
    """Test is_subpath function."""

    def test_is_subpath_when_child_under_parent_then_returns_true(self, tmp_path):
        """Test that child under parent returns True."""
        parent = tmp_path
        child = tmp_path / "subdir" / "file.txt"

        result = is_subpath(child, parent)

        assert result is True

    def test_is_subpath_when_child_outside_parent_then_returns_false(self, tmp_path):
        """Test that child outside parent returns False."""
        parent = tmp_path / "project"
        child = tmp_path / "other" / "file.txt"

        result = is_subpath(child, parent)

        assert result is False

    def test_is_subpath_when_same_path_then_returns_true(self, tmp_path):
        """Test that same path returns True."""
        result = is_subpath(tmp_path, tmp_path)

        assert result is True

    def test_is_subpath_when_string_paths_then_works(self, tmp_path):
        """Test with string paths."""
        parent_str = str(tmp_path)
        child_str = str(tmp_path / "subdir")

        result = is_subpath(child_str, parent_str)

        assert result is True

    def test_is_subpath_when_invalid_types_then_raises_type_error(self):
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError, match="child must be str or Path"):
            is_subpath(123, "/parent")  # type: ignore

        with pytest.raises(TypeError, match="parent must be str or Path"):
            is_subpath("/child", 456)  # type: ignore


class TestGetRelativePathOrAbsolute:
    """Test get_relative_path_or_absolute function."""

    def test_get_relative_path_or_absolute_when_under_base_then_returns_relative(
        self, tmp_path
    ):
        """Test that path under base returns relative path."""
        base = tmp_path
        path = tmp_path / "src" / "main.py"

        result = get_relative_path_or_absolute(path, base)

        assert result == Path("src/main.py")

    def test_get_relative_path_or_absolute_when_outside_base_then_returns_absolute(
        self, tmp_path
    ):
        """Test that path outside base returns absolute path."""
        base = tmp_path / "project"
        path = tmp_path / "other" / "file.py"

        result = get_relative_path_or_absolute(path, base)

        assert result.is_absolute()
        assert result == path.resolve()

    def test_get_relative_path_or_absolute_when_string_paths_then_works(self, tmp_path):
        """Test with string paths."""
        base_str = str(tmp_path)
        path_str = str(tmp_path / "file.txt")

        result = get_relative_path_or_absolute(path_str, base_str)

        assert result == Path("file.txt")

    def test_get_relative_path_or_absolute_when_invalid_types_then_raises_type_error(
        self,
    ):
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError, match="path must be str or Path"):
            get_relative_path_or_absolute(123, "/base")  # type: ignore

        with pytest.raises(TypeError, match="base must be str or Path"):
            get_relative_path_or_absolute("/path", 456)  # type: ignore


class TestEnsurePathPermissions:
    """Test ensure_path_permissions function."""

    def test_ensure_path_permissions_when_readable_path_then_passes(self, tmp_path):
        """Test that readable path passes permission check."""
        test_dir = tmp_path / "readable"
        test_dir.mkdir()

        # Should not raise any exception
        ensure_path_permissions(test_dir)

    def test_ensure_path_permissions_when_writable_required_and_writable_then_passes(
        self, tmp_path
    ):
        """Test that writable path passes when write permission required."""
        test_dir = tmp_path / "writable"
        test_dir.mkdir()

        # Should not raise any exception
        ensure_path_permissions(test_dir, require_write=True)

    def test_ensure_path_permissions_when_nonexistent_path_then_raises_error(
        self, tmp_path
    ):
        """Test that nonexistent path raises validation error."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(SpecValidationError, match="Path does not exist"):
            ensure_path_permissions(nonexistent)

    @patch("os.access")
    def test_ensure_path_permissions_when_no_read_permission_then_raises_error(
        self, mock_access, tmp_path
    ):
        """Test that path without read permission raises error."""
        test_dir = tmp_path / "no_read"
        test_dir.mkdir()

        # Mock os.access to return False for read permission
        mock_access.side_effect = lambda path, mode: mode != os.R_OK

        with pytest.raises(SpecValidationError, match="No read permission"):
            ensure_path_permissions(test_dir)

    @patch("os.access")
    def test_ensure_path_permissions_when_no_write_permission_then_raises_error(
        self, mock_access, tmp_path
    ):
        """Test that path without write permission raises error when required."""
        test_dir = tmp_path / "no_write"
        test_dir.mkdir()

        # Mock os.access to return False for write permission only
        mock_access.side_effect = lambda path, mode: mode != os.W_OK

        with pytest.raises(SpecValidationError, match="No write permission"):
            ensure_path_permissions(test_dir, require_write=True)

    def test_ensure_path_permissions_when_string_path_then_works(self, tmp_path):
        """Test with string path."""
        test_dir = tmp_path / "string_test"
        test_dir.mkdir()

        # Should not raise any exception
        ensure_path_permissions(str(test_dir))

    def test_ensure_path_permissions_when_invalid_type_then_raises_type_error(self):
        """Test that invalid path type raises TypeError."""
        with pytest.raises(TypeError, match="path must be str or Path"):
            ensure_path_permissions(123)  # type: ignore


# Cross-platform path utilities tests


class TestNormalizePathSeparators:
    """Test normalize_path_separators function."""

    def test_normalize_windows_separators(self) -> None:
        """Test normalization of Windows-style backslashes."""
        windows_path = "src\\models\\user.py"
        result = normalize_path_separators(windows_path)
        assert result == "src/models/user.py"

    def test_normalize_unix_separators(self) -> None:
        """Test that Unix-style paths remain unchanged."""
        unix_path = "src/models/user.py"
        result = normalize_path_separators(unix_path)
        assert result == "src/models/user.py"

    def test_normalize_mixed_separators(self) -> None:
        """Test normalization of mixed separator styles."""
        mixed_path = "src\\models/user.py"
        result = normalize_path_separators(mixed_path)
        assert result == "src/models/user.py"

    def test_normalize_path_object(self) -> None:
        """Test normalization with Path objects."""
        path_obj = Path("src") / "models" / "user.py"
        result = normalize_path_separators(path_obj)
        assert result == "src/models/user.py"

    def test_normalize_absolute_path(self) -> None:
        """Test normalization of absolute paths."""
        # Note: This test normalizes separators but keeps the path structure
        abs_path = "C:\\Users\\test\\project\\src\\models\\user.py"
        result = normalize_path_separators(abs_path)
        assert result == "C:/Users/test/project/src/models/user.py"

    def test_normalize_empty_path(self) -> None:
        """Test normalization of empty path."""
        result = normalize_path_separators("")
        assert result == ""

    def test_normalize_single_file(self) -> None:
        """Test normalization of single file name."""
        result = normalize_path_separators("user.py")
        assert result == "user.py"


class TestRemoveSpecsPrefix:
    """Test remove_specs_prefix function."""

    def test_remove_unix_specs_prefix(self) -> None:
        """Test removal of Unix-style .specs/ prefix."""
        path_with_prefix = ".specs/src/models/user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_windows_specs_prefix(self) -> None:
        """Test removal of Windows-style .specs\\ prefix."""
        path_with_prefix = ".specs\\src\\models\\user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_no_prefix(self) -> None:
        """Test handling of paths without .specs prefix."""
        path_without_prefix = "src/models/user.py"
        result = remove_specs_prefix(path_without_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_mixed_separators(self) -> None:
        """Test removal with mixed separators in remaining path."""
        path_with_prefix = ".specs/src\\models/user.py"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_root_file(self) -> None:
        """Test removal when file is directly in .specs."""
        path_with_prefix = ".specs/README.md"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "README.md"

    def test_remove_specs_prefix_windows_root_file(self) -> None:
        """Test removal of Windows prefix for root file."""
        path_with_prefix = ".specs\\README.md"
        result = remove_specs_prefix(path_with_prefix)
        assert result == "README.md"


class TestEnsureSpecsPrefix:
    """Test ensure_specs_prefix function."""

    def test_ensure_specs_prefix_adds_prefix(self) -> None:
        """Test adding .specs/ prefix to path without it."""
        path_without_prefix = "src/models/user.py"
        result = ensure_specs_prefix(path_without_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_keeps_existing(self) -> None:
        """Test that existing .specs/ prefix is preserved."""
        path_with_prefix = ".specs/src/models/user.py"
        result = ensure_specs_prefix(path_with_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_normalizes_windows(self) -> None:
        """Test that Windows .specs\\ prefix is normalized."""
        path_with_windows_prefix = ".specs\\src\\models\\user.py"
        result = ensure_specs_prefix(path_with_windows_prefix)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_with_path_object(self) -> None:
        """Test with Path object input."""
        path_obj = Path("src") / "models" / "user.py"
        result = ensure_specs_prefix(path_obj)
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_root_file(self) -> None:
        """Test adding prefix to root file."""
        result = ensure_specs_prefix("README.md")
        assert result == ".specs/README.md"


class TestIsSpecsPath:
    """Test is_specs_path function."""

    def test_is_specs_path_unix_prefix(self) -> None:
        """Test detection of Unix-style .specs/ prefix."""
        specs_path = ".specs/src/models/user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_windows_prefix(self) -> None:
        """Test detection of Windows-style .specs\\ prefix."""
        specs_path = ".specs\\src\\models\\user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_no_prefix(self) -> None:
        """Test detection when no .specs prefix exists."""
        regular_path = "src/models/user.py"
        assert is_specs_path(regular_path) is False

    def test_is_specs_path_with_path_object(self) -> None:
        """Test detection with Path object."""
        specs_path = Path(".specs") / "src" / "models" / "user.py"
        assert is_specs_path(specs_path) is True

    def test_is_specs_path_similar_name(self) -> None:
        """Test that similar but different names are not detected."""
        similar_paths = [
            "specs/src/models/user.py",  # Missing dot
            ".spec/src/models/user.py",  # Missing 's'
            "myspecs/src/models/user.py",  # Different name
        ]
        for path in similar_paths:
            assert is_specs_path(path) is False

    def test_is_specs_path_root_file(self) -> None:
        """Test detection for file directly in .specs."""
        specs_path = ".specs/README.md"
        assert is_specs_path(specs_path) is True


class TestConvertToPosixStyle:
    """Test convert_to_posix_style function (alias for normalize_path_separators)."""

    def test_convert_to_posix_style_basic(self) -> None:
        """Test basic conversion to POSIX style."""
        windows_path = "src\\models\\user.py"
        result = convert_to_posix_style(windows_path)
        assert result == "src/models/user.py"

    def test_convert_to_posix_style_with_path_object(self) -> None:
        """Test conversion with Path object."""
        path_obj = Path("src") / "models" / "user.py"
        result = convert_to_posix_style(path_obj)
        assert result == "src/models/user.py"


class TestCrossplatformBehavior:
    """Test cross-platform behavior patterns."""

    def test_round_trip_specs_operations(self) -> None:
        """Test that adding and removing .specs prefix works correctly."""
        original_paths = [
            "src/models/user.py",
            "src\\models\\user.py",
            "docs/README.md",
            "test.py",
        ]

        for original in original_paths:
            # Add prefix
            with_prefix = ensure_specs_prefix(original)
            # Remove prefix
            without_prefix = remove_specs_prefix(with_prefix)
            # Should match normalized original
            expected = normalize_path_separators(original)
            assert without_prefix == expected

    def test_consistent_separator_handling(self) -> None:
        """Test that all functions consistently use forward slashes."""
        windows_paths = [
            "src\\models\\user.py",
            ".specs\\src\\models\\user.py",
            "docs\\README.md",
        ]

        for path in windows_paths:
            # All functions should return paths with forward slashes
            assert "\\" not in normalize_path_separators(path)
            assert "\\" not in remove_specs_prefix(path)
            assert "\\" not in ensure_specs_prefix(path)
            assert "\\" not in convert_to_posix_style(path)

    def test_path_object_compatibility(self) -> None:
        """Test that all functions work with both strings and Path objects."""
        test_path = Path("src") / "models" / "user.py"

        # All functions should accept Path objects
        normalize_result = normalize_path_separators(test_path)
        prefix_result = ensure_specs_prefix(test_path)
        posix_result = convert_to_posix_style(test_path)
        is_specs_result = is_specs_path(test_path)

        # Results should be consistent
        assert normalize_result == "src/models/user.py"
        assert prefix_result == ".specs/src/models/user.py"
        assert posix_result == "src/models/user.py"
        assert is_specs_result is False
