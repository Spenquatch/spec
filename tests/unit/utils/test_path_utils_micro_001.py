"""Unit tests for path_utils module - Micro-Agent filesystem_001 Implementation"""

import os
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
    """Test safe_relative_to function"""

    def test_safe_relative_to_valid_subpath(self):
        """Test safe_relative_to with valid subpath"""

        def mock_resolve_func(self):
            if "main.py" in str(self):
                return Path("/project/src/main.py")
            else:
                return Path("/project")

        with patch.object(Path, "resolve", mock_resolve_func):
            result = safe_relative_to("/project/src/main.py", "/project")
            assert result == Path("src/main.py")

    def test_safe_relative_to_outside_root_strict(self):
        """Test safe_relative_to with path outside root in strict mode"""

        def mock_resolve_func(self):
            if "file.py" in str(self):
                return Path("/other/file.py")
            else:
                return Path("/project")

        with patch.object(Path, "resolve", mock_resolve_func):
            with patch.object(
                Path, "relative_to", side_effect=ValueError("not relative")
            ):
                with pytest.raises(
                    SpecValidationError, match="Path .* is outside root"
                ):
                    safe_relative_to("/other/file.py", "/project", strict=True)

    def test_safe_relative_to_outside_root_non_strict(self):
        """Test safe_relative_to with path outside root in non-strict mode"""
        outside_path = Path("/other/file.py")

        def mock_resolve_func(self):
            if "file.py" in str(self):
                return outside_path
            else:
                return Path("/project")

        with patch.object(Path, "resolve", mock_resolve_func):
            with patch.object(
                Path, "relative_to", side_effect=ValueError("not relative")
            ):
                result = safe_relative_to("/other/file.py", "/project", strict=False)
                assert result == outside_path

    def test_safe_relative_to_type_error_path(self):
        """Test safe_relative_to with invalid path type"""
        with pytest.raises(TypeError, match="path must be str or Path"):
            safe_relative_to(123, "/project")

    def test_safe_relative_to_type_error_root(self):
        """Test safe_relative_to with invalid root type"""
        with pytest.raises(TypeError, match="root must be str or Path"):
            safe_relative_to("/path", 123)

    def test_safe_relative_to_string_inputs(self):
        """Test safe_relative_to with string inputs"""

        def mock_resolve_func(self):
            if "main.py" in str(self):
                return Path("/project/src/main.py")
            else:
                return Path("/project")

        with patch.object(Path, "resolve", mock_resolve_func):
            result = safe_relative_to("/project/src/main.py", "/project")
            assert result == Path("src/main.py")


class TestEnsureDirectory:
    """Test ensure_directory function"""

    def test_ensure_directory_creates_new_directory(self):
        """Test ensure_directory creates new directory"""
        test_path = Path("/test/new/dir")

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "mkdir") as mock_mkdir:
                result = ensure_directory(test_path)

                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                assert result == test_path

    def test_ensure_directory_existing_directory(self):
        """Test ensure_directory with existing directory"""
        test_path = Path("/test/existing/dir")

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "is_dir", return_value=True):
                result = ensure_directory(test_path)

                assert result == test_path

    def test_ensure_directory_existing_file(self):
        """Test ensure_directory with existing file (not directory)"""
        test_path = Path("/test/existing/file.txt")

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "is_dir", return_value=False):
                with pytest.raises(
                    SpecValidationError, match="exists but is not a directory"
                ):
                    ensure_directory(test_path)

    def test_ensure_directory_type_error(self):
        """Test ensure_directory with invalid type"""
        with pytest.raises(TypeError, match="path must be str or Path"):
            ensure_directory(123)

    def test_ensure_directory_no_parents(self):
        """Test ensure_directory without creating parents"""
        test_path = Path("/test/dir")

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "mkdir") as mock_mkdir:
                ensure_directory(test_path, parents=False)

                mock_mkdir.assert_called_once_with(parents=False, exist_ok=True)

    def test_ensure_directory_string_input(self):
        """Test ensure_directory with string input"""
        test_path = "/test/string/dir"

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "mkdir"):
                result = ensure_directory(test_path)

                assert result == Path(test_path)


class TestNormalizePath:
    """Test normalize_path function"""

    def test_normalize_path_with_symlinks(self):
        """Test normalize_path with symlink resolution"""
        test_path = Path("/test/path")
        resolved_path = Path("/resolved/test/path")

        with patch.object(Path, "resolve", return_value=resolved_path):
            result = normalize_path(test_path)

            assert result == resolved_path

    def test_normalize_path_without_symlinks(self):
        """Test normalize_path without symlink resolution"""
        test_path = Path("./relative/path")

        with patch.object(Path, "cwd", return_value=Path("/current")):
            with patch.object(Path, "is_absolute", return_value=False):
                result = normalize_path(test_path, resolve_symlinks=False)

                assert result == Path("/current") / test_path

    def test_normalize_path_absolute_no_symlinks(self):
        """Test normalize_path with absolute path and no symlink resolution"""
        test_path = Path("/absolute/path")

        with patch.object(Path, "is_absolute", return_value=True):
            result = normalize_path(test_path, resolve_symlinks=False)

            assert result == test_path

    def test_normalize_path_type_error(self):
        """Test normalize_path with invalid type"""
        with pytest.raises(TypeError, match="path must be str or Path"):
            normalize_path(123)

    def test_normalize_path_string_input(self):
        """Test normalize_path with string input"""
        test_path = "/test/string/path"
        resolved_path = Path("/resolved/test/string/path")

        with patch.object(Path, "resolve", return_value=resolved_path):
            result = normalize_path(test_path)

            assert result == resolved_path


class TestResolveProjectRoot:
    """Test resolve_project_root function"""

    def test_resolve_project_root_finds_git(self):
        """Test resolve_project_root finds .git directory"""
        start_path = Path("/project/src")
        root_path = Path("/project")

        with patch("spec_cli.utils.path_utils.normalize_path", return_value=start_path):

            def mock_exists_func(self):
                return str(self) == "/project/.git"

            with patch.object(Path, "exists", mock_exists_func):
                result = resolve_project_root(start_path)
                assert result == root_path

    def test_resolve_project_root_finds_spec(self):
        """Test resolve_project_root finds .spec directory"""
        start_path = Path("/project/src")
        root_path = Path("/project")

        with patch("spec_cli.utils.path_utils.normalize_path", return_value=start_path):

            def mock_exists_func(self):
                return str(self) == "/project/.spec"

            with patch.object(Path, "exists", mock_exists_func):
                result = resolve_project_root(start_path)
                assert result == root_path

    def test_resolve_project_root_finds_pyproject_toml(self):
        """Test resolve_project_root finds pyproject.toml"""
        start_path = Path("/project/src")
        root_path = Path("/project")

        with patch("spec_cli.utils.path_utils.normalize_path", return_value=start_path):

            def mock_exists_func(self):
                return str(self) == "/project/pyproject.toml"

            with patch.object(Path, "exists", mock_exists_func):
                result = resolve_project_root(start_path)
                assert result == root_path

    def test_resolve_project_root_no_markers(self):
        """Test resolve_project_root when no markers found"""
        start_path = Path("/some/path")

        with patch("spec_cli.utils.path_utils.normalize_path", return_value=start_path):
            with patch.object(Path, "exists", return_value=False):
                result = resolve_project_root(start_path)

                assert result == start_path

    def test_resolve_project_root_default_start_path(self):
        """Test resolve_project_root with default start path"""
        with patch.object(Path, "cwd", return_value=Path("/current")):
            with patch(
                "spec_cli.utils.path_utils.normalize_path",
                return_value=Path("/current"),
            ):
                with patch.object(Path, "exists", return_value=False):
                    result = resolve_project_root()

                    assert result == Path("/current")

    def test_resolve_project_root_type_error(self):
        """Test resolve_project_root with invalid type"""
        with pytest.raises(TypeError, match="start_path must be str, Path, or None"):
            resolve_project_root(123)


class TestIsSubpath:
    """Test is_subpath function"""

    def test_is_subpath_true(self):
        """Test is_subpath returns True for valid subpath"""
        with patch("spec_cli.utils.path_utils.normalize_path") as mock_normalize:
            mock_normalize.side_effect = lambda x: Path(x).resolve()
            with patch.object(Path, "relative_to") as mock_relative_to:
                mock_relative_to.return_value = Path("src/main.py")

                result = is_subpath("/project/src/main.py", "/project")

                assert result is True

    def test_is_subpath_false(self):
        """Test is_subpath returns False for non-subpath"""
        with patch("spec_cli.utils.path_utils.normalize_path") as mock_normalize:
            mock_normalize.side_effect = lambda x: Path(x).resolve()
            with patch.object(
                Path, "relative_to", side_effect=ValueError("not relative")
            ):
                result = is_subpath("/other/file.py", "/project")

                assert result is False

    def test_is_subpath_type_error_child(self):
        """Test is_subpath with invalid child type"""
        with pytest.raises(TypeError, match="child must be str or Path"):
            is_subpath(123, "/project")

    def test_is_subpath_type_error_parent(self):
        """Test is_subpath with invalid parent type"""
        with pytest.raises(TypeError, match="parent must be str or Path"):
            is_subpath("/path", 123)


class TestGetRelativePathOrAbsolute:
    """Test get_relative_path_or_absolute function"""

    def test_get_relative_path_or_absolute_relative_success(self):
        """Test get_relative_path_or_absolute returns relative path"""
        with patch("spec_cli.utils.path_utils.safe_relative_to") as mock_safe_relative:
            mock_safe_relative.return_value = Path("src/main.py")

            result = get_relative_path_or_absolute("/project/src/main.py", "/project")

            assert result == Path("src/main.py")

    def test_get_relative_path_or_absolute_absolute_fallback(self):
        """Test get_relative_path_or_absolute returns absolute path on failure"""
        absolute_path = Path("/other/file.py")

        with patch("spec_cli.utils.path_utils.safe_relative_to") as mock_safe_relative:
            mock_safe_relative.side_effect = SpecValidationError("Path outside root")
            with patch(
                "spec_cli.utils.path_utils.normalize_path", return_value=absolute_path
            ):
                result = get_relative_path_or_absolute("/other/file.py", "/project")

                assert result == absolute_path

    def test_get_relative_path_or_absolute_type_error_path(self):
        """Test get_relative_path_or_absolute with invalid path type"""
        with pytest.raises(TypeError, match="path must be str or Path"):
            get_relative_path_or_absolute(123, "/project")

    def test_get_relative_path_or_absolute_type_error_base(self):
        """Test get_relative_path_or_absolute with invalid base type"""
        with pytest.raises(TypeError, match="base must be str or Path"):
            get_relative_path_or_absolute("/path", 123)


class TestEnsurePathPermissions:
    """Test ensure_path_permissions function"""

    def test_ensure_path_permissions_read_only(self):
        """Test ensure_path_permissions with read-only requirement"""
        test_path = Path("/test/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                mock_access.side_effect = lambda path, mode: mode == os.R_OK

                # Should not raise exception
                ensure_path_permissions(test_path, require_write=False)

    def test_ensure_path_permissions_read_write(self):
        """Test ensure_path_permissions with read-write requirement"""
        test_path = Path("/test/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                mock_access.side_effect = (
                    lambda path, mode: True
                )  # All permissions granted

                # Should not raise exception
                ensure_path_permissions(test_path, require_write=True)

    def test_ensure_path_permissions_not_exists(self):
        """Test ensure_path_permissions with non-existent path"""
        test_path = Path("/nonexistent/path")

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SpecValidationError, match="Path does not exist"):
                ensure_path_permissions(test_path)

    def test_ensure_path_permissions_no_read(self):
        """Test ensure_path_permissions with no read permission"""
        test_path = Path("/test/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(SpecValidationError, match="No read permission"):
                    ensure_path_permissions(test_path)

    def test_ensure_path_permissions_no_write(self):
        """Test ensure_path_permissions with no write permission when required"""
        test_path = Path("/test/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                mock_access.side_effect = (
                    lambda path, mode: mode == os.R_OK
                )  # Only read permission

                with pytest.raises(SpecValidationError, match="No write permission"):
                    ensure_path_permissions(test_path, require_write=True)

    def test_ensure_path_permissions_type_error(self):
        """Test ensure_path_permissions with invalid type"""
        with pytest.raises(TypeError, match="path must be str or Path"):
            ensure_path_permissions(123)


class TestCrossPlatformUtilities:
    """Test cross-platform path utilities"""

    def test_normalize_path_separators_windows_style(self):
        """Test normalize_path_separators with Windows-style separators"""
        result = normalize_path_separators("src\\models\\user.py")
        assert result == "src/models/user.py"

    def test_normalize_path_separators_unix_style(self):
        """Test normalize_path_separators with Unix-style separators"""
        result = normalize_path_separators("src/models/user.py")
        assert result == "src/models/user.py"

    def test_normalize_path_separators_mixed_style(self):
        """Test normalize_path_separators with mixed separators"""
        result = normalize_path_separators("src\\models/user.py")
        assert result == "src/models/user.py"

    def test_normalize_path_separators_path_object(self):
        """Test normalize_path_separators with Path object"""
        result = normalize_path_separators(Path("src/models/user.py"))
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_unix_style(self):
        """Test remove_specs_prefix with Unix-style prefix"""
        result = remove_specs_prefix(".specs/src/models/user.py")
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_windows_style(self):
        """Test remove_specs_prefix with Windows-style prefix"""
        result = remove_specs_prefix(".specs\\src\\models\\user.py")
        assert result == "src/models/user.py"

    def test_remove_specs_prefix_no_prefix(self):
        """Test remove_specs_prefix with no prefix"""
        result = remove_specs_prefix("src/models/user.py")
        assert result == "src/models/user.py"

    def test_ensure_specs_prefix_no_existing_prefix(self):
        """Test ensure_specs_prefix with no existing prefix"""
        result = ensure_specs_prefix("src/models/user.py")
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_existing_unix_prefix(self):
        """Test ensure_specs_prefix with existing Unix prefix"""
        result = ensure_specs_prefix(".specs/src/models/user.py")
        assert result == ".specs/src/models/user.py"

    def test_ensure_specs_prefix_existing_windows_prefix(self):
        """Test ensure_specs_prefix with existing Windows prefix"""
        result = ensure_specs_prefix(".specs\\src\\models\\user.py")
        assert result == ".specs/src/models/user.py"

    def test_is_specs_path_unix_style(self):
        """Test is_specs_path with Unix-style path"""
        result = is_specs_path(".specs/src/models/user.py")
        assert result is True

    def test_is_specs_path_windows_style(self):
        """Test is_specs_path with Windows-style path"""
        result = is_specs_path(".specs\\src\\models\\user.py")
        assert result is True

    def test_is_specs_path_no_prefix(self):
        """Test is_specs_path with no prefix"""
        result = is_specs_path("src/models/user.py")
        assert result is False

    def test_convert_to_posix_style(self):
        """Test convert_to_posix_style function"""
        result = convert_to_posix_style("src\\models\\user.py")
        assert result == "src/models/user.py"

    def test_edge_case_empty_string(self):
        """Test cross-platform utilities with empty string"""
        assert normalize_path_separators("") == ""
        assert remove_specs_prefix("") == ""
        assert ensure_specs_prefix("") == ".specs/"
        assert is_specs_path("") is False

    def test_edge_case_root_specs_path(self):
        """Test cross-platform utilities with root .specs path"""
        assert remove_specs_prefix(".specs/") == ""
        assert ensure_specs_prefix(".specs/") == ".specs/"
        assert is_specs_path(".specs/") is True
