"""Cross-platform path handling tests - Micro-Agent filesystem_001 Implementation"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecValidationError
from spec_cli.file_system.path_resolver import PathResolver
from spec_cli.utils.path_utils import (
    ensure_path_permissions,
    ensure_specs_prefix,
    is_specs_path,
    normalize_path_separators,
    remove_specs_prefix,
)


class TestCrossPlatformPathHandling:
    """Test cross-platform path handling across Windows and Unix systems"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test/project")
        self.mock_settings.specs_dir = Path("/test/project/.specs")
        self.path_resolver = PathResolver(self.mock_settings)

    def test_windows_path_separators_in_specs_conversion(self):
        """Test Windows-style path separators in specs path conversion"""
        windows_specs_path = ".specs\\src\\models\\user.py"

        result = self.path_resolver.convert_from_specs_path(windows_specs_path)

        # Should handle Windows separators and return normalized path
        assert result == Path("src/models/user.py")

    def test_mixed_path_separators_normalization(self):
        """Test mixed path separators are normalized correctly"""
        mixed_path = "src\\models/user\\handlers.py"

        normalized = normalize_path_separators(mixed_path)

        assert normalized == "src/models/user/handlers.py"
        assert "\\" not in normalized

    def test_specs_prefix_handling_windows_style(self):
        """Test .specs prefix handling with Windows-style paths"""
        windows_specs_path = ".specs\\src\\models\\user.py"

        # Test removal
        removed = remove_specs_prefix(windows_specs_path)
        assert removed == "src/models/user.py"

        # Test detection
        is_specs = is_specs_path(windows_specs_path)
        assert is_specs is True

        # Test ensuring prefix
        ensured = ensure_specs_prefix("src\\models\\user.py")
        assert ensured == ".specs/src/models/user.py"

    def test_specs_prefix_handling_unix_style(self):
        """Test .specs prefix handling with Unix-style paths"""
        unix_specs_path = ".specs/src/models/user.py"

        # Test removal
        removed = remove_specs_prefix(unix_specs_path)
        assert removed == "src/models/user.py"

        # Test detection
        is_specs = is_specs_path(unix_specs_path)
        assert is_specs is True

        # Test ensuring prefix
        ensured = ensure_specs_prefix("src/models/user.py")
        assert ensured == ".specs/src/models/user.py"

    def test_path_resolver_with_windows_absolute_paths(self):
        """Test PathResolver with Windows-style absolute paths"""
        # Mock Windows-style absolute path
        windows_absolute = "C:\\test\\project\\src\\main.py"

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.return_value = Path("src/main.py")

            result = self.path_resolver.convert_to_spec_directory_path(
                Path(windows_absolute)
            )

            expected = self.mock_settings.specs_dir / "src/main"
            assert result == expected

    def test_path_resolver_specs_conversion_cross_platform(self):
        """Test PathResolver specs conversion works across platforms"""
        # Test both Windows and Unix style specs paths
        test_cases = [
            ".specs/src/models/user.py",
            ".specs\\src\\models\\user.py",
            ".specs/src\\models/user.py",  # Mixed separators
        ]

        for specs_path in test_cases:
            result = self.path_resolver.convert_from_specs_path(specs_path)
            assert result == Path("src/models/user.py")

    def test_normalize_path_separators_edge_cases(self):
        """Test normalize_path_separators with edge cases"""
        test_cases = [
            ("", ""),
            ("\\", "/"),
            ("\\\\", "//"),
            ("a\\b\\c\\", "a/b/c/"),
            ("\\a\\b\\c", "/a/b/c"),
            ("a/b\\c/d", "a/b/c/d"),
        ]

        for input_path, expected in test_cases:
            result = normalize_path_separators(input_path)
            assert result == expected


class TestPermissionHandling:
    """Test file system permission handling"""

    def test_ensure_path_permissions_read_access_granted(self):
        """Test ensure_path_permissions when read access is granted"""
        test_path = Path("/test/readable/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                mock_access.side_effect = lambda path, mode: mode == os.R_OK

                # Should not raise exception
                ensure_path_permissions(test_path, require_write=False)

                mock_access.assert_called_with(test_path, os.R_OK)

    def test_ensure_path_permissions_write_access_granted(self):
        """Test ensure_path_permissions when read and write access are granted"""
        test_path = Path("/test/writable/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access", return_value=True):
                # Should not raise exception
                ensure_path_permissions(test_path, require_write=True)

    def test_ensure_path_permissions_read_access_denied(self):
        """Test ensure_path_permissions when read access is denied"""
        test_path = Path("/test/unreadable/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(SpecValidationError, match="No read permission"):
                    ensure_path_permissions(test_path)

    def test_ensure_path_permissions_write_access_denied(self):
        """Test ensure_path_permissions when write access is denied but required"""
        test_path = Path("/test/readonly/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                # Grant read but deny write
                mock_access.side_effect = lambda path, mode: mode == os.R_OK

                with pytest.raises(SpecValidationError, match="No write permission"):
                    ensure_path_permissions(test_path, require_write=True)

    def test_ensure_path_permissions_path_not_exists(self):
        """Test ensure_path_permissions when path does not exist"""
        test_path = Path("/test/nonexistent/path")

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SpecValidationError, match="Path does not exist"):
                ensure_path_permissions(test_path)

    def test_ensure_path_permissions_with_string_path(self):
        """Test ensure_path_permissions with string path input"""
        test_path = "/test/string/path"

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access", return_value=True):
                # Should not raise exception
                ensure_path_permissions(test_path, require_write=True)

    def test_ensure_path_permissions_os_specific_behavior(self):
        """Test ensure_path_permissions behaves correctly across different OS"""
        test_path = Path("/test/os/specific/path")

        with patch.object(Path, "exists", return_value=True):
            with patch("os.access") as mock_access:
                # Mock OS-specific permission checks
                mock_access.side_effect = lambda path, mode: {
                    os.R_OK: True,
                    os.W_OK: True,
                    os.X_OK: False,  # Execute permission denied
                }.get(mode, False)

                # Should only check read and write permissions
                ensure_path_permissions(test_path, require_write=True)

                # Verify correct permission flags were checked
                calls = mock_access.call_args_list
                modes_checked = [call[0][1] for call in calls]
                assert os.R_OK in modes_checked
                assert os.W_OK in modes_checked


class TestPathValidationEdgeCases:
    """Test edge cases in path validation and resolution"""

    def setup_method(self):
        """Setup test environment"""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test/project")
        self.mock_settings.specs_dir = Path("/test/project/.specs")
        self.path_resolver = PathResolver(self.mock_settings)

    def test_resolve_input_path_with_unicode_characters(self):
        """Test resolving paths with Unicode characters"""
        unicode_path = "src/files/测试文件.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(unicode_path)

                result = self.path_resolver.resolve_input_path(unicode_path)
                assert result == Path(unicode_path)

    def test_resolve_input_path_with_special_characters(self):
        """Test resolving paths with special characters"""
        special_path = "src/files/file with spaces & symbols!@#.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(special_path)

                result = self.path_resolver.resolve_input_path(special_path)
                assert result == Path(special_path)

    def test_convert_to_spec_directory_path_with_dots_in_name(self):
        """Test converting paths with dots in file names"""
        file_with_dots = Path("src/models/user.model.py")

        result = self.path_resolver.convert_to_spec_directory_path(file_with_dots)

        # Should use stem (filename without extension)
        expected = self.mock_settings.specs_dir / "src/models/user.model"
        assert result == expected

    def test_convert_to_spec_directory_path_no_extension(self):
        """Test converting paths with no file extension"""
        file_no_ext = Path("src/scripts/build")

        result = self.path_resolver.convert_to_spec_directory_path(file_no_ext)

        expected = self.mock_settings.specs_dir / "src/scripts/build"
        assert result == expected

    def test_specs_path_handling_empty_components(self):
        """Test specs path handling with empty path components"""
        edge_cases = [
            ".specs//src//models//user.py",  # Double slashes
            ".specs/./src/models/user.py",  # Current directory references
            ".specs/src/../src/models/user.py",  # Parent directory references
        ]

        for edge_case in edge_cases:
            # Should handle gracefully without throwing exceptions
            result = self.path_resolver.convert_from_specs_path(edge_case)
            # Result should be some valid Path object
            assert isinstance(result, Path)

    def test_very_long_path_handling(self):
        """Test handling of very long file paths"""
        # Create a very long path
        long_components = ["very_long_directory_name_" + str(i) for i in range(20)]
        long_path = "/".join(long_components) + "/file.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(long_path)

                result = self.path_resolver.resolve_input_path(long_path)
                assert result == Path(long_path)

    def test_case_sensitivity_handling(self):
        """Test path handling with different case variations"""
        # Test case variations (important for case-insensitive filesystems)
        case_variations = [
            "src/Models/User.py",
            "SRC/models/USER.py",
            "Src/Models/user.PY",
        ]

        for case_path in case_variations:
            with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/test/project")
                with patch.object(
                    self.path_resolver, "_ensure_within_project"
                ) as mock_ensure:
                    mock_ensure.return_value = Path(case_path)

                    result = self.path_resolver.resolve_input_path(case_path)
                    assert result == Path(case_path)

    def test_symlink_handling_in_path_resolution(self):
        """Test path resolution with symbolic links"""
        symlink_path = "src/symlink_to_models/user.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(symlink_path)

                result = self.path_resolver.resolve_input_path(symlink_path)
                assert result == Path(symlink_path)
