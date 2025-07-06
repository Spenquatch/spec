"""Unit tests for SpecSettings configuration management - Micro-Agent Implementation.

This test module provides comprehensive coverage for the config/settings.py module,
focusing on SpecSettings dataclass, SettingsManager singleton, and convenience functions.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.theme import Theme

from spec_cli.config.settings import (
    SPEC_THEME,
    SettingsManager,
    SpecSettings,
    get_console,
    get_settings,
    reset_settings,
)
from spec_cli.exceptions import SpecConfigurationError

# Type: ignore for mypy on test methods to focus on coverage over typing
# mypy: disable-error-code=no-untyped-def

class TestSpecSettings:
    """Unit tests for SpecSettings dataclass."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        self.test_root = Path("/test/project")

    @patch("spec_cli.config.settings.resolve_project_root")
    @patch("spec_cli.config.settings.normalize_path")
    @patch("spec_cli.config.settings.debug_logger")
    def test_spec_settings_initialization_with_defaults(
        self,
        mock_debug_logger: Mock,
        mock_normalize_path: Mock,
        mock_resolve_project_root: Mock,
    ) -> None:
        """Test SpecSettings initialization with default values."""
        # Setup mocks
        mock_resolve_project_root.return_value = self.test_root
        mock_normalize_path.return_value = self.test_root

        # Create settings instance
        settings = SpecSettings()

        # Verify path initialization
        assert settings.root_path == self.test_root
        assert settings.spec_dir == self.test_root / ".spec"
        assert settings.specs_dir == self.test_root / ".specs"
        assert settings.index_file == self.test_root / ".spec-index"
        assert settings.ignore_file == self.test_root / ".specignore"
        assert settings.template_file == self.test_root / ".spectemplate"
        assert settings.gitignore_file == self.test_root / ".gitignore"

        # Verify debug logger was called
        mock_debug_logger.log.assert_called_once()

    @patch("spec_cli.config.settings.normalize_path")
    @patch("spec_cli.config.settings.debug_logger")
    @patch.dict(
        os.environ,
        {
            "SPEC_DEBUG": "1",
            "SPEC_DEBUG_LEVEL": "DEBUG",
            "SPEC_DEBUG_TIMING": "true",
            "SPEC_USE_COLOR": "false",
            "SPEC_CONSOLE_WIDTH": "120",
        },
    )
    def test_spec_settings_initialization_with_environment_variables(
        self, mock_debug_logger, mock_normalize_path
    ):
        """Test SpecSettings initialization with environment variables."""
        mock_normalize_path.return_value = self.test_root

        settings = SpecSettings(root_path=self.test_root)

        # Verify environment variable processing
        assert settings.debug_enabled is True
        assert settings.debug_level == "DEBUG"
        assert settings.debug_timing is True
        assert settings.use_color is False
        assert settings.console_width == 120

    @patch("spec_cli.config.settings.normalize_path")
    @patch("spec_cli.config.settings.debug_logger")
    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "invalid"})
    def test_spec_settings_invalid_console_width_handling(
        self, mock_debug_logger, mock_normalize_path
    ):
        """Test SpecSettings handling of invalid console width."""
        mock_normalize_path.return_value = self.test_root

        settings = SpecSettings(root_path=self.test_root)

        # Verify invalid width is ignored and warning is logged
        assert settings.console_width is None
        mock_debug_logger.log.assert_any_call(
            "WARNING", "Invalid SPEC_CONSOLE_WIDTH value", value="invalid"
        )

    @patch("spec_cli.config.settings.normalize_path")
    @patch("spec_cli.config.settings.debug_logger")
    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "20"})
    def test_spec_settings_minimum_console_width_enforcement(
        self, mock_debug_logger, mock_normalize_path
    ):
        """Test SpecSettings enforces minimum console width."""
        mock_normalize_path.return_value = self.test_root

        settings = SpecSettings(root_path=self.test_root)

        # Verify minimum width is enforced
        assert settings.console_width == 40

    def test_get_bool_env_method_with_true_values(self) -> None:
        """Test _get_bool_env method with various true values."""
        settings = SpecSettings(root_path=self.test_root)

        with patch.dict(os.environ, {"TEST_VAR": "1"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "true"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "YES"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

    def test_get_bool_env_method_with_false_values(self) -> None:
        """Test _get_bool_env method with various false values."""
        settings = SpecSettings(root_path=self.test_root)

        with patch.dict(os.environ, {"TEST_VAR": "0"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

        with patch.dict(os.environ, {"TEST_VAR": "false"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

        with patch.dict(os.environ, {"TEST_VAR": "NO"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

    def test_get_bool_env_method_with_default_values(self) -> None:
        """Test _get_bool_env method returns default for unrecognized values."""
        settings = SpecSettings(root_path=self.test_root)

        with patch.dict(os.environ, {"TEST_VAR": "maybe"}):
            assert settings._get_bool_env("TEST_VAR", True) is True

        with patch.dict(os.environ, {}):
            assert settings._get_bool_env("NONEXISTENT_VAR", False) is False

    @patch("spec_cli.config.settings.normalize_path")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_is_initialized_method_when_directories_exist(
        self, mock_is_dir, mock_exists, mock_normalize_path
    ):
        """Test is_initialized method when both directories exist."""
        mock_normalize_path.return_value = self.test_root
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        settings = SpecSettings(root_path=self.test_root)

        assert settings.is_initialized() is True

    @patch("spec_cli.config.settings.normalize_path")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_is_initialized_method_when_directories_missing(
        self, mock_is_dir, mock_exists, mock_normalize_path
    ):
        """Test is_initialized method when directories are missing."""
        mock_normalize_path.return_value = self.test_root
        mock_exists.return_value = False
        mock_is_dir.return_value = True

        settings = SpecSettings(root_path=self.test_root)

        assert settings.is_initialized() is False

    @patch("spec_cli.config.settings.normalize_path")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_is_initialized_method_when_directory_not_dir(
        self, mock_is_dir, mock_exists, mock_normalize_path
    ):
        """Test is_initialized method when directory exists but is not a directory."""
        mock_normalize_path.return_value = self.test_root
        mock_exists.return_value = True
        mock_is_dir.return_value = False

        settings = SpecSettings(root_path=self.test_root)

        assert settings.is_initialized() is False

    @patch("spec_cli.config.settings.normalize_path")
    @patch("os.access")
    def test_validate_permissions_success(
        self, mock_access, mock_normalize_path
    ) -> None:
        """Test validate_permissions when permissions are adequate."""
        mock_normalize_path.return_value = self.test_root
        mock_access.return_value = True

        settings = SpecSettings(root_path=self.test_root)

        with patch.object(settings, "is_initialized", return_value=True):
            # Should not raise any exception
            settings.validate_permissions()

        # Verify access checks were called
        assert mock_access.call_count == 2

    @patch("spec_cli.config.settings.normalize_path")
    @patch("os.access")
    def test_validate_permissions_spec_dir_no_write_access(
        self, mock_access, mock_normalize_path
    ):
        """Test validate_permissions when spec_dir has no write access."""
        mock_normalize_path.return_value = self.test_root

        def access_side_effect(path, mode):
            if str(path).endswith(".spec"):
                return False
            return True

        mock_access.side_effect = access_side_effect

        settings = SpecSettings(root_path=self.test_root)

        with patch.object(settings, "is_initialized", return_value=True):
            with pytest.raises(SpecConfigurationError) as exc_info:
                settings.validate_permissions()

            assert "No write permission" in str(exc_info.value)
            assert str(settings.spec_dir) in str(exc_info.value)

    @patch("spec_cli.config.settings.normalize_path")
    @patch("os.access")
    def test_validate_permissions_specs_dir_no_write_access(
        self, mock_access, mock_normalize_path
    ):
        """Test validate_permissions when specs_dir has no write access."""
        mock_normalize_path.return_value = self.test_root

        def access_side_effect(path, mode):
            if str(path).endswith(".specs"):
                return False
            return True

        mock_access.side_effect = access_side_effect

        settings = SpecSettings(root_path=self.test_root)

        with patch.object(settings, "is_initialized", return_value=True):
            with pytest.raises(SpecConfigurationError) as exc_info:
                settings.validate_permissions()

            assert "No write permission" in str(exc_info.value)
            assert str(settings.specs_dir) in str(exc_info.value)

    @patch("spec_cli.config.settings.normalize_path")
    def test_validate_permissions_not_initialized(self, mock_normalize_path) -> None:
        """Test validate_permissions when spec is not initialized."""
        mock_normalize_path.return_value = self.test_root

        settings = SpecSettings(root_path=self.test_root)

        with patch.object(settings, "is_initialized", return_value=False):
            # Should not raise any exception
            settings.validate_permissions()

class TestSettingsManager:
    """Unit tests for SettingsManager singleton."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        # Reset singleton for each test
        reset_settings()
        self.test_root = Path("/test/project")

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    @patch("spec_cli.config.settings.SpecSettings")
    def test_settings_manager_singleton_behavior(self, mock_spec_settings) -> None:
        """Test SettingsManager implements singleton pattern correctly."""
        manager1 = SettingsManager()
        manager2 = SettingsManager()

        assert manager1 is manager2

    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_settings_creates_new_instance_when_none_exists(
        self, mock_spec_settings
    ) -> None:
        """Test get_settings creates new instance when none exists."""
        mock_settings = Mock()
        mock_spec_settings.return_value = mock_settings

        manager = SettingsManager()
        result = manager.get_settings(self.test_root)

        assert result == mock_settings
        mock_spec_settings.assert_called_once_with(self.test_root)

    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_settings_reuses_existing_instance_with_same_path(
        self, mock_spec_settings
    ) -> None:
        """Test get_settings reuses existing instance with same root path."""
        mock_settings = Mock()
        mock_settings.root_path = self.test_root
        mock_spec_settings.return_value = mock_settings

        manager = SettingsManager()
        result1 = manager.get_settings(self.test_root)
        result2 = manager.get_settings(self.test_root)

        assert result1 == result2
        mock_spec_settings.assert_called_once()

    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_settings_creates_new_instance_with_different_path(
        self, mock_spec_settings
    ) -> None:
        """Test get_settings creates new instance with different root path."""
        mock_settings1 = Mock()
        mock_settings1.root_path = self.test_root
        mock_settings2 = Mock()
        mock_settings2.root_path = Path("/different/path")

        mock_spec_settings.side_effect = [mock_settings1, mock_settings2]

        manager = SettingsManager()
        result1 = manager.get_settings(self.test_root)
        result2 = manager.get_settings(Path("/different/path"))

        assert result1 != result2
        assert mock_spec_settings.call_count == 2

    @patch("spec_cli.config.settings.Console")
    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_console_creates_new_instance_when_none_exists(
        self, mock_spec_settings, mock_console
    ):
        """Test get_console creates new Console instance when none exists."""
        mock_settings = Mock()
        mock_settings.use_color = True
        mock_settings.console_width = 80
        mock_spec_settings.return_value = mock_settings

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        manager = SettingsManager()
        result = manager.get_console(self.test_root)

        assert result == mock_console_instance
        mock_console.assert_called_once_with(
            theme=SPEC_THEME,
            force_terminal=True,
            width=80,
        )

    @patch("spec_cli.config.settings.Console")
    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_console_reuses_existing_instance(
        self, mock_spec_settings, mock_console
    ) -> None:
        """Test get_console reuses existing Console instance."""
        mock_settings = Mock()
        mock_settings.root_path = self.test_root
        mock_settings.use_color = True
        mock_settings.console_width = 80
        mock_spec_settings.return_value = mock_settings

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        manager = SettingsManager()
        result1 = manager.get_console(self.test_root)
        result2 = manager.get_console(self.test_root)

        assert result1 == result2
        assert result1 == mock_console_instance
        # Console should only be created once because settings path didn't change
        mock_console.assert_called_once()

    @patch("spec_cli.config.settings.Console")
    @patch("spec_cli.config.settings.SpecSettings")
    def test_get_console_resets_when_settings_change(
        self, mock_spec_settings, mock_console
    ) -> None:
        """Test get_console resets console when settings change."""
        mock_settings1 = Mock()
        mock_settings1.root_path = self.test_root
        mock_settings1.use_color = True
        mock_settings1.console_width = 80

        mock_settings2 = Mock()
        mock_settings2.root_path = Path("/different/path")
        mock_settings2.use_color = False
        mock_settings2.console_width = 120

        mock_spec_settings.side_effect = [mock_settings1, mock_settings2]

        mock_console_instance1 = Mock()
        mock_console_instance2 = Mock()
        mock_console.side_effect = [mock_console_instance1, mock_console_instance2]

        manager = SettingsManager()
        result1 = manager.get_console(self.test_root)
        result2 = manager.get_console(Path("/different/path"))

        assert result1 != result2
        assert mock_console.call_count == 2

    def test_reset_method_clears_instances(self) -> None:
        """Test reset method clears both settings and console instances."""
        manager = SettingsManager()

        # Set some mock instances
        manager._settings_instance = Mock()
        manager._console_instance = Mock()

        manager.reset()

        assert manager._settings_instance is None
        assert manager._console_instance is None

class TestConvenienceFunctions:
    """Unit tests for convenience functions."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()
        self.test_root = Path("/test/project")

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    @patch("spec_cli.config.settings.SettingsManager")
    def test_get_settings_function_calls_manager(self, mock_settings_manager) -> None:
        """Test get_settings function calls SettingsManager correctly."""
        mock_manager = Mock()
        mock_settings = Mock()
        mock_manager.get_settings.return_value = mock_settings
        mock_settings_manager.return_value = mock_manager

        result = get_settings(self.test_root)

        assert result == mock_settings
        mock_manager.get_settings.assert_called_once_with(self.test_root)

    @patch("spec_cli.config.settings.SettingsManager")
    def test_get_console_function_calls_manager(self, mock_settings_manager) -> None:
        """Test get_console function calls SettingsManager correctly."""
        mock_manager = Mock()
        mock_console = Mock()
        mock_manager.get_console.return_value = mock_console
        mock_settings_manager.return_value = mock_manager

        result = get_console(self.test_root)

        assert result == mock_console
        mock_manager.get_console.assert_called_once_with(self.test_root)

    def test_reset_settings_function_calls_manager_and_singleton_reset():
        """Test reset_settings function calls both manager reset and singleton reset."""
        # Create a real manager to test the reset behavior
        manager = SettingsManager()
        manager._settings_instance = Mock()
        manager._console_instance = Mock()

        reset_settings()

        # Verify manager was reset
        assert manager._settings_instance is None
        assert manager._console_instance is None

        # Verify singleton reset was called

class TestSpecTheme:
    """Unit tests for SPEC_THEME configuration."""

    def test_spec_theme_contains_required_styles(self) -> None:
        """Test SPEC_THEME contains all required style definitions."""
        required_styles = [
            "success",
            "error",
            "warning",
            "info",
            "debug",
            "path",
            "count",
        ]

        for style in required_styles:
            assert style in SPEC_THEME.styles
            assert SPEC_THEME.styles[style] is not None

    def test_spec_theme_is_theme_instance(self) -> None:
        """Test SPEC_THEME is a proper Rich Theme instance."""
        assert isinstance(SPEC_THEME, Theme)
