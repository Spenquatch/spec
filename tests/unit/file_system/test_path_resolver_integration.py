"""Integration tests for PathResolver path utilities usage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecValidationError
from spec_cli.file_system.path_resolver import PathResolver


class TestPathResolverIntegration:
    """Test PathResolver integration with path utilities."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Create mock settings with temporary paths."""
        settings = Mock(spec=SpecSettings)
        settings.root_path = tmp_path / "project"
        settings.specs_dir = tmp_path / "project" / ".specs"
        settings.root_path.mkdir(parents=True, exist_ok=True)
        settings.specs_dir.mkdir(parents=True, exist_ok=True)
        return settings

    @pytest.fixture
    def path_resolver(self, mock_settings):
        """Create PathResolver with mock settings."""
        return PathResolver(settings=mock_settings)

    def test_path_resolution_when_using_safe_relative_to_then_consistent_errors(
        self, path_resolver, mock_settings, tmp_path
    ):
        """Test that path resolution uses safe_relative_to for consistent error handling."""
        # Create a path outside the project root
        outside_path = tmp_path / "outside" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()

        # Verify that _ensure_within_project raises SpecValidationError
        with pytest.raises(SpecValidationError, match="outside project root"):
            path_resolver._ensure_within_project(outside_path)

    def test_directory_validation_when_using_ensure_directory_then_consistent_behavior(
        self, path_resolver, mock_settings
    ):
        """Test that directory operations use path utilities for consistent behavior."""
        # Test convert_to_spec_directory_path with absolute path
        source_file = mock_settings.root_path / "src" / "main.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        spec_dir = path_resolver.convert_to_spec_directory_path(source_file)

        # Should return path under .specs
        assert spec_dir.parts[-3:] == (".specs", "src", "main")

    def test_path_normalization_when_using_normalize_path_then_consistent_format(
        self, path_resolver, mock_settings
    ):
        """Test that path operations use normalize_path for consistent formatting."""
        # Test with relative path inside project
        relative_path = Path("src") / "main.py"
        source_file = mock_settings.root_path / relative_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        # Test is_within_project with absolute path
        assert path_resolver.is_within_project(source_file) is True

        # Test with path outside project
        outside_path = mock_settings.root_path.parent / "outside.py"
        assert path_resolver.is_within_project(outside_path) is False

    def test_specs_path_conversion_when_using_safe_relative_to_then_proper_handling(
        self, path_resolver, mock_settings
    ):
        """Test that specs path conversion uses safe_relative_to properly."""
        # Test absolute path under .specs
        specs_file = mock_settings.specs_dir / "src" / "main.md"
        specs_file.parent.mkdir(parents=True, exist_ok=True)
        specs_file.touch()

        result = path_resolver.convert_from_specs_path(specs_file)

        # Should return relative path without .specs prefix
        assert result == Path("src") / "main.md"

    def test_source_file_conversion_when_using_safe_relative_to_then_secure_paths(
        self, path_resolver, mock_settings
    ):
        """Test that source file operations use path utilities for security."""
        # Test get_spec_files_for_source with absolute path
        source_file = mock_settings.root_path / "src" / "models.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        spec_files = path_resolver.get_spec_files_for_source(source_file)

        # Should return proper spec file paths
        assert "index" in spec_files
        assert "history" in spec_files
        assert spec_files["index"].name == "index.md"
        assert spec_files["history"].name == "history.md"

    @patch("spec_cli.file_system.path_resolver.debug_logger")
    def test_debug_logging_includes_operation_context(
        self, mock_logger, path_resolver, mock_settings
    ):
        """Test that path operations include proper debug context."""
        # Test path within project validation
        source_file = mock_settings.root_path / "test.py"
        source_file.touch()

        # This should trigger debug logging with operation context
        path_resolver._ensure_within_project(source_file)

        # Verify debug logging was called with operation context
        mock_logger.log.assert_called()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "INFO"
        assert "operation" in call_args[1]
        assert call_args[1]["operation"] == "path_validation"

    def test_error_handling_consistency_across_path_operations(
        self, path_resolver, mock_settings, tmp_path
    ):
        """Test that all path operations handle errors consistently."""
        # Test with path outside project root
        outside_path = tmp_path / "completely_outside" / "file.py"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()

        # All methods should handle outside paths consistently
        with pytest.raises(SpecValidationError):
            path_resolver._ensure_within_project(outside_path)

        assert path_resolver.is_within_project(outside_path) is False

        # convert_to_spec_directory_path should handle gracefully with non-strict mode
        spec_dir = path_resolver.convert_to_spec_directory_path(outside_path)
        assert (
            spec_dir.is_absolute()
        )  # Should return absolute path when outside project
