import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecFileError, SpecValidationError
from spec_cli.file_system.path_resolver import PathResolver


# Helper function for cross-platform path comparison in tests
def normalize_path_for_comparison(path: Path) -> str:
    """Normalize path for cross-platform comparison."""
    return str(path).replace("\\", "/")


class TestPathResolver:
    """Test the PathResolver class functionality."""

    def test_path_resolver_initializes_with_default_settings(self) -> None:
        """Test that PathResolver initializes with default settings."""
        with patch(
            "spec_cli.file_system.path_resolver.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            resolver = PathResolver()

            assert resolver.settings is mock_settings
            mock_get_settings.assert_called_once()

    def test_path_resolver_initializes_with_custom_settings(self) -> None:
        """Test that PathResolver can use custom settings."""
        custom_settings = MagicMock()
        resolver = PathResolver(settings=custom_settings)

        assert resolver.settings is custom_settings

    def test_resolve_input_path_handles_current_directory(self) -> None:
        """Test resolving current directory '.' input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            with patch("pathlib.Path.cwd", return_value=root_path):
                result = resolver.resolve_input_path(".")

                # Should return empty path for current directory
                assert result == Path(".")

    def test_resolve_input_path_handles_relative_paths(self) -> None:
        """Test resolving relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Create subdirectory
            subdir = root_path / "subdir"
            subdir.mkdir()

            with patch("pathlib.Path.cwd", return_value=root_path):
                result = resolver.resolve_input_path("subdir")

                assert result == Path("subdir")

    def test_resolve_input_path_handles_absolute_paths_within_project(self) -> None:
        """Test resolving absolute paths within project boundaries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Create file within project
            test_file = root_path / "test.py"
            test_file.touch()

            result = resolver.resolve_input_path(str(test_file))

            assert result == Path("test.py")

    def test_resolve_input_path_rejects_paths_outside_project(self) -> None:
        """Test that paths outside project boundaries are rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "project"
            root_path.mkdir()
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Path outside project
            outside_path = Path(temp_dir) / "outside.py"
            outside_path.touch()

            with pytest.raises(SpecValidationError) as exc_info:
                resolver.resolve_input_path(str(outside_path))

            assert "outside project root" in str(exc_info.value)

    def test_resolve_input_path_handles_os_errors(self) -> None:
        """Test error handling for OS errors during path resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Mock Path.cwd() to raise OSError
            with patch("pathlib.Path.cwd", side_effect=OSError("Mocked OS error")):
                with pytest.raises(SpecFileError) as exc_info:
                    resolver.resolve_input_path(".")

                assert "Failed to resolve path" in str(exc_info.value)

    def test_convert_to_spec_directory_path_creates_correct_structure(self) -> None:
        """Test conversion of file paths to spec directory paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            file_path = Path("src/models.py")
            result = resolver.convert_to_spec_directory_path(file_path)

            expected = settings.specs_dir / "src" / "models"
            assert result == expected

    def test_convert_to_spec_directory_path_handles_nested_files(self) -> None:
        """Test conversion for nested file structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            file_path = Path("src/components/auth/login.tsx")
            result = resolver.convert_to_spec_directory_path(file_path)

            expected = settings.specs_dir / "src" / "components" / "auth" / "login"
            assert result == expected

    def test_convert_to_spec_directory_path_removes_file_extension(self) -> None:
        """Test that file extensions are properly removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            file_path = Path("test.js")
            result = resolver.convert_to_spec_directory_path(file_path)

            expected = settings.specs_dir / "test"
            assert result == expected

    def test_convert_from_specs_path_handles_absolute_specs_paths(self) -> None:
        """Test conversion from absolute .specs/ paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            specs_path = settings.specs_dir / "src" / "models" / "index.md"
            result = resolver.convert_from_specs_path(specs_path)

            expected = Path("src") / "models" / "index.md"
            assert result == expected

    def test_convert_from_specs_path_handles_relative_specs_paths(self) -> None:
        """Test conversion from relative .specs/ paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            specs_path = ".specs/src/models/index.md"
            result = resolver.convert_from_specs_path(specs_path)

            expected = Path("src") / "models" / "index.md"
            assert normalize_path_for_comparison(
                result
            ) == normalize_path_for_comparison(expected)

    def test_convert_from_specs_path_removes_specs_prefix(self) -> None:
        """Test that .specs/ prefix is properly removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            specs_path = ".specs/file.md"
            result = resolver.convert_from_specs_path(specs_path)

            assert normalize_path_for_comparison(result) == "file.md"

    def test_convert_from_specs_path_handles_non_specs_paths(self) -> None:
        """Test handling of paths not in .specs/ context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            regular_path = "src/models.py"
            result = resolver.convert_from_specs_path(regular_path)

            assert result == Path("src/models.py")

    def test_is_within_project_accepts_valid_paths(self) -> None:
        """Test that valid paths within project are accepted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Test relative path
            relative_path = Path("src/models.py")
            assert resolver.is_within_project(relative_path) is True

            # Test absolute path within project
            absolute_path = root_path / "src" / "models.py"
            assert resolver.is_within_project(absolute_path) is True

    def test_is_within_project_rejects_external_paths(self) -> None:
        """Test that paths outside project are rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "project"
            root_path.mkdir()
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Path outside project
            external_path = Path(temp_dir) / "external.py"
            assert resolver.is_within_project(external_path) is False

    def test_get_absolute_path_converts_correctly(self) -> None:
        """Test conversion from relative to absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            relative_path = Path("src/models.py")
            result = resolver.get_absolute_path(relative_path)

            expected = root_path / "src" / "models.py"
            assert result == expected

    def test_validate_path_exists_passes_for_existing_paths(self) -> None:
        """Test that validation passes for existing paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # Create test file
            test_file = root_path / "test.py"
            test_file.touch()

            # Should not raise any exception
            resolver.validate_path_exists(Path("test.py"))

    def test_validate_path_exists_raises_for_missing_paths(self) -> None:
        """Test that validation raises for missing paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            with pytest.raises(SpecFileError) as exc_info:
                resolver.validate_path_exists(Path("nonexistent.py"))

            assert "Path does not exist" in str(exc_info.value)

    def test_ensure_within_project_with_valid_path(self) -> None:
        """Test _ensure_within_project with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            absolute_path = root_path / "src" / "models.py"
            result = resolver._ensure_within_project(absolute_path)

            expected = Path("src") / "models.py"
            assert result == expected

    def test_ensure_within_project_with_invalid_path(self) -> None:
        """Test _ensure_within_project with path outside project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "project"
            root_path.mkdir()
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            external_path = Path(temp_dir) / "external.py"

            with pytest.raises(SpecValidationError) as exc_info:
                resolver._ensure_within_project(external_path)

            assert "outside project root" in str(exc_info.value)

    def test_get_spec_files_for_source_with_relative_path(self) -> None:
        """Test getting spec files for a relative source file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            source_file = Path("src/models.py")
            result = resolver.get_spec_files_for_source(source_file)

            expected_spec_dir = settings.specs_dir / "src" / "models"
            expected = {
                "index": expected_spec_dir / "index.md",
                "history": expected_spec_dir / "history.md",
            }

            assert result == expected

    def test_get_spec_files_for_source_with_absolute_path(self) -> None:
        """Test getting spec files for an absolute source file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            source_file = root_path / "src" / "models.py"
            result = resolver.get_spec_files_for_source(source_file)

            expected_spec_dir = settings.specs_dir / "src" / "models"
            expected = {
                "index": expected_spec_dir / "index.md",
                "history": expected_spec_dir / "history.md",
            }

            assert result == expected

    def test_get_spec_files_for_source_with_nested_structure(self) -> None:
        """Test getting spec files for nested directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            source_file = Path("src/components/auth/login.tsx")
            result = resolver.get_spec_files_for_source(source_file)

            expected_spec_dir = (
                settings.specs_dir / "src" / "components" / "auth" / "login"
            )
            expected = {
                "index": expected_spec_dir / "index.md",
                "history": expected_spec_dir / "history.md",
            }

            assert result == expected

    def test_get_spec_files_for_source_with_file_outside_project(self) -> None:
        """Test getting spec files for a file outside project boundaries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "project"
            root_path.mkdir()
            settings = SpecSettings(root_path=root_path)
            resolver = PathResolver(settings=settings)

            # File outside project
            external_file = Path(temp_dir) / "external.py"
            result = resolver.get_spec_files_for_source(external_file)

            # Should still work but use the file as-is for spec directory creation
            expected_spec_dir = settings.specs_dir / temp_dir / "external"
            expected = {
                "index": expected_spec_dir / "index.md",
                "history": expected_spec_dir / "history.md",
            }

            assert result == expected
