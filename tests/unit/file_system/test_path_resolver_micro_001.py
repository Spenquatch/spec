"""Unit tests for PathResolver class - Micro-Agent filesystem_001 Implementation"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecFileError, SpecValidationError
from spec_cli.file_system.path_resolver import PathResolver


class TestPathResolverMicro001:
    """Unit tests for PathResolver - Micro-Agent Implementation"""

    def setup_method(self):
        """Setup using discovered helpers"""
        # Mock settings for controlled testing
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test/project")
        self.mock_settings.specs_dir = Path("/test/project/.specs")

        self.path_resolver = PathResolver(self.mock_settings)

    def test_init_with_default_settings(self):
        """Test PathResolver initialization requires settings"""
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            PathResolver()

    def test_init_with_custom_settings(self):
        """Test PathResolver initialization with custom settings"""
        custom_settings = Mock(spec=SpecSettings)
        resolver = PathResolver(custom_settings)
        assert resolver.settings == custom_settings

    def test_resolve_input_path_current_directory(self):
        """Test resolving current directory shorthand"""
        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project/src")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path("src")

                result = self.path_resolver.resolve_input_path(".")

                mock_ensure.assert_called_once_with(Path("/test/project/src"))
                assert result == Path("src")

    def test_resolve_input_path_absolute_path(self):
        """Test resolving absolute paths"""
        absolute_path = Path("/test/project/src/main.py")
        with patch.object(self.path_resolver, "_ensure_within_project") as mock_ensure:
            mock_ensure.return_value = Path("src/main.py")

            result = self.path_resolver.resolve_input_path("/test/project/src/main.py")

            mock_ensure.assert_called_once_with(absolute_path)
            assert result == Path("src/main.py")

    def test_resolve_input_path_relative_path(self):
        """Test resolving relative paths"""
        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path("src/main.py")

                result = self.path_resolver.resolve_input_path("src/main.py")

                # Should resolve relative to current working directory
                expected_absolute = Path("/test/project/src/main.py").resolve()
                mock_ensure.assert_called_once_with(expected_absolute)
                assert result == Path("src/main.py")

    def test_resolve_input_path_os_error(self):
        """Test resolve_input_path handling OSError"""
        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.side_effect = OSError("Permission denied")

            with pytest.raises(SpecFileError, match="Failed to resolve path"):
                self.path_resolver.resolve_input_path(".")

    def test_ensure_within_project_valid_path(self):
        """Test _ensure_within_project with valid path"""
        absolute_path = Path("/test/project/src/main.py")

        with patch(
            "spec_cli.file_system.path_resolver.normalize_path"
        ) as mock_normalize:
            mock_normalize.side_effect = lambda x: x  # Return input unchanged
            with patch(
                "spec_cli.file_system.path_resolver.safe_relative_to"
            ) as mock_safe_relative:
                mock_safe_relative.return_value = Path("src/main.py")

                result = self.path_resolver._ensure_within_project(absolute_path)

                assert result == Path("src/main.py")
                mock_safe_relative.assert_called_once_with(
                    absolute_path, self.mock_settings.root_path, strict=True
                )

    def test_ensure_within_project_outside_boundaries(self):
        """Test _ensure_within_project with path outside project"""
        absolute_path = Path("/other/project/file.py")

        with patch(
            "spec_cli.file_system.path_resolver.normalize_path"
        ) as mock_normalize:
            mock_normalize.side_effect = lambda x: x
            with patch(
                "spec_cli.file_system.path_resolver.safe_relative_to"
            ) as mock_safe_relative:
                mock_safe_relative.side_effect = SpecValidationError(
                    "Path outside root"
                )

                with pytest.raises(
                    SpecValidationError, match="Path .* is outside project root"
                ):
                    self.path_resolver._ensure_within_project(absolute_path)

    def test_convert_to_spec_directory_path_relative_file(self):
        """Test converting relative file path to spec directory path"""
        file_path = Path("src/models/user.py")

        result = self.path_resolver.convert_to_spec_directory_path(file_path)

        expected = self.mock_settings.specs_dir / "src/models/user"
        assert result == expected

    def test_convert_to_spec_directory_path_absolute_file(self):
        """Test converting absolute file path to spec directory path"""
        file_path = Path("/test/project/src/models/user.py")

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.return_value = Path("src/models/user.py")

            result = self.path_resolver.convert_to_spec_directory_path(file_path)

            expected = self.mock_settings.specs_dir / "src/models/user"
            assert result == expected

    def test_convert_to_spec_directory_path_outside_project(self):
        """Test converting file path outside project boundaries"""
        file_path = Path("/other/project/file.py")

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.side_effect = SpecValidationError("Path outside root")

            # Should handle gracefully and use path as-is
            result = self.path_resolver.convert_to_spec_directory_path(file_path)

            # Should create spec dir with the original absolute path structure
            expected = self.mock_settings.specs_dir / file_path.parent / file_path.stem
            assert result == expected

    def test_get_spec_files_for_source_relative_path(self):
        """Test getting spec files for relative source path"""
        source_file = Path("src/models/user.py")

        result = self.path_resolver.get_spec_files_for_source(source_file)

        expected_dir = self.mock_settings.specs_dir / "src/models/user"
        expected = {
            "index": expected_dir / "index.md",
            "history": expected_dir / "history.md",
        }
        assert result == expected

    def test_get_spec_files_for_source_absolute_path(self):
        """Test getting spec files for absolute source path"""
        source_file = Path("/test/project/src/models/user.py")

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.return_value = Path("src/models/user.py")

            result = self.path_resolver.get_spec_files_for_source(source_file)

            expected_dir = self.mock_settings.specs_dir / "src/models/user"
            expected = {
                "index": expected_dir / "index.md",
                "history": expected_dir / "history.md",
            }
            assert result == expected

    def test_convert_from_specs_path_absolute_under_specs(self):
        """Test converting absolute path under .specs/ directory"""
        specs_path = Path("/test/project/.specs/src/models/user.py")

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.return_value = Path("src/models/user.py")

            result = self.path_resolver.convert_from_specs_path(specs_path)

            assert result == Path("src/models/user.py")

    def test_convert_from_specs_path_absolute_not_under_specs(self):
        """Test converting absolute path not under .specs/ directory"""
        specs_path = Path("/other/path/file.py")

        with patch(
            "spec_cli.file_system.path_resolver.safe_relative_to"
        ) as mock_safe_relative:
            mock_safe_relative.side_effect = SpecValidationError(
                "Path not under .specs"
            )

            result = self.path_resolver.convert_from_specs_path(specs_path)

            assert result == specs_path

    def test_convert_from_specs_path_with_specs_prefix_unix(self):
        """Test converting path with .specs/ prefix (Unix style)"""
        specs_path = ".specs/src/models/user.py"

        with patch(
            "spec_cli.file_system.path_resolver.remove_specs_prefix"
        ) as mock_remove:
            mock_remove.return_value = "src/models/user.py"

            result = self.path_resolver.convert_from_specs_path(specs_path)

            assert result == Path("src/models/user.py")

    def test_convert_from_specs_path_with_specs_prefix_windows(self):
        r"""Test converting path with .specs\ prefix (Windows style)"""
        specs_path = ".specs\\src\\models\\user.py"

        with patch(
            "spec_cli.file_system.path_resolver.remove_specs_prefix"
        ) as mock_remove:
            mock_remove.return_value = "src/models/user.py"

            result = self.path_resolver.convert_from_specs_path(specs_path)

            assert result == Path("src/models/user.py")

    def test_convert_from_specs_path_no_prefix(self):
        """Test converting path without .specs prefix"""
        specs_path = "src/models/user.py"

        result = self.path_resolver.convert_from_specs_path(specs_path)

        assert result == Path("src/models/user.py")

    def test_is_within_project_absolute_path_inside(self):
        """Test is_within_project with absolute path inside project"""
        path = Path("/test/project/src/main.py")

        with patch(
            "spec_cli.file_system.path_resolver.normalize_path"
        ) as mock_normalize:
            mock_normalize.side_effect = lambda x: x
            with patch(
                "spec_cli.file_system.path_resolver.safe_relative_to"
            ) as mock_safe_relative:
                mock_safe_relative.return_value = Path("src/main.py")

                result = self.path_resolver.is_within_project(path)

                assert result is True

    def test_is_within_project_absolute_path_outside(self):
        """Test is_within_project with absolute path outside project"""
        path = Path("/other/project/file.py")

        with patch(
            "spec_cli.file_system.path_resolver.normalize_path"
        ) as mock_normalize:
            mock_normalize.side_effect = lambda x: x
            with patch(
                "spec_cli.file_system.path_resolver.safe_relative_to"
            ) as mock_safe_relative:
                mock_safe_relative.side_effect = SpecValidationError(
                    "Path outside root"
                )

                result = self.path_resolver.is_within_project(path)

                assert result is False

    def test_is_within_project_relative_path(self):
        """Test is_within_project with relative path"""
        path = Path("src/main.py")

        result = self.path_resolver.is_within_project(path)

        assert result is True

    def test_is_within_project_value_error(self):
        """Test is_within_project handles ValueError"""
        path = Path("/test/project/src/main.py")

        with patch(
            "spec_cli.file_system.path_resolver.normalize_path"
        ) as mock_normalize:
            mock_normalize.side_effect = lambda x: x
            with patch(
                "spec_cli.file_system.path_resolver.safe_relative_to"
            ) as mock_safe_relative:
                mock_safe_relative.side_effect = ValueError("Invalid path")

                result = self.path_resolver.is_within_project(path)

                assert result is False

    def test_get_absolute_path(self):
        """Test converting relative path to absolute path"""
        relative_path = Path("src/main.py")

        result = self.path_resolver.get_absolute_path(relative_path)

        expected = self.mock_settings.root_path / relative_path
        assert result == expected

    def test_validate_path_exists_relative_path(self):
        """Test validate_path_exists with relative path that exists"""
        path = Path("src/main.py")
        # absolute_path = self.mock_settings.root_path / path

        with patch.object(Path, "exists", return_value=True):
            # Should not raise exception
            self.path_resolver.validate_path_exists(path)

    def test_validate_path_exists_absolute_path(self):
        """Test validate_path_exists with absolute path that exists"""
        path = Path("/test/project/src/main.py")

        with patch.object(Path, "exists", return_value=True):
            # Should not raise exception
            self.path_resolver.validate_path_exists(path)

    def test_validate_path_exists_not_found(self):
        """Test validate_path_exists with non-existent path"""
        path = Path("src/nonexistent.py")

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SpecFileError, match="Path does not exist"):
                self.path_resolver.validate_path_exists(path)

    def test_edge_case_empty_path_string(self):
        """Test handling of empty path string"""
        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path("")

                result = self.path_resolver.resolve_input_path("")
                assert result == Path("")

    def test_edge_case_very_long_path(self):
        """Test handling of very long path strings"""
        long_path = "a/" * 100 + "file.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(long_path)

                result = self.path_resolver.resolve_input_path(long_path)
                assert result == Path(long_path)

    def test_path_with_special_characters(self):
        """Test handling paths with special characters"""
        special_path = "src/file with spaces & symbols!.py"

        with patch("spec_cli.file_system.path_resolver.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/project")
            with patch.object(
                self.path_resolver, "_ensure_within_project"
            ) as mock_ensure:
                mock_ensure.return_value = Path(special_path)

                result = self.path_resolver.resolve_input_path(special_path)
                assert result == Path(special_path)
