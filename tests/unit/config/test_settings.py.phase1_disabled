"""Unit tests for config.settings module.

Tests for SpecSettings dataclass and SettingsManager singleton functionality,
covering configuration management, environment variable handling, and Rich
console integration.
"""

import os
from unittest.mock import patch

import pytest
from rich.console import Console
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

class TestSpecSettings:
    """Unit tests for SpecSettings dataclass."""

    def test_init_with_default_path(self):
        """Test SpecSettings initialization with default project root."""
        settings = SpecSettings()

        assert settings.root_path is not None
        assert settings.spec_dir == settings.root_path / ".spec"
        assert settings.specs_dir == settings.root_path / ".specs"
        assert settings.index_file == settings.root_path / ".spec-index"
        assert settings.ignore_file == settings.root_path / ".specignore"
        assert settings.template_file == settings.root_path / ".spectemplate"
        assert settings.gitignore_file == settings.root_path / ".gitignore"

    def test_init_with_custom_path(self, tmp_path):
        """Test SpecSettings initialization with custom root path."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.root_path == tmp_path
        assert settings.spec_dir == tmp_path / ".spec"
        assert settings.specs_dir == tmp_path / ".specs"
        assert settings.index_file == tmp_path / ".spec-index"
        assert settings.ignore_file == tmp_path / ".specignore"
        assert settings.template_file == tmp_path / ".spectemplate"
        assert settings.gitignore_file == tmp_path / ".gitignore"

    @patch.dict(os.environ, {}, clear=True)
    def test_environment_defaults(self, tmp_path):
        """Test environment variable defaults when not set."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.debug_enabled is False
        assert settings.debug_level == "INFO"
        assert settings.debug_timing is False
        assert settings.use_color is True
        assert settings.console_width is None

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
    def test_environment_variables_enabled(self, tmp_path):
        """Test environment variable parsing when enabled."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.debug_enabled is True
        assert settings.debug_level == "DEBUG"
        assert settings.debug_timing is True
        assert settings.use_color is False
        assert settings.console_width == 120

    @patch.dict(
        os.environ,
        {"SPEC_DEBUG": "0", "SPEC_DEBUG_TIMING": "no", "SPEC_USE_COLOR": "false"},
    )
    def test_environment_variables_disabled(self, tmp_path):
        """Test environment variable parsing when disabled."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.debug_enabled is False
        assert settings.debug_timing is False
        assert settings.use_color is False

    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "30"})
    def test_console_width_minimum_enforced(self, tmp_path):
        """Test console width minimum value enforcement."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.console_width == 40  # Minimum enforced

    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "invalid"})
    @patch("spec_cli.config.settings.debug_logger")
    def test_invalid_console_width_logged(self, mock_logger, tmp_path):
        """Test invalid console width value logging."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.console_width is None
        # Check that warning was logged (could be any of the log calls)
        warning_calls = [
            call for call in mock_logger.log.call_args_list if call[0][0] == "WARNING"
        ]
        assert len(warning_calls) > 0
        warning_call = warning_calls[0]
        assert "Invalid SPEC_CONSOLE_WIDTH value" in warning_call[0][1]

    def test_get_bool_env_true_values(self, tmp_path):
        """Test _get_bool_env with true values."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings._get_bool_env("TEST_TRUE_1", False) is False  # Not set

        with patch.dict(os.environ, {"TEST_VAR": "1"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "true"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "yes"}):
            assert settings._get_bool_env("TEST_VAR", False) is True

    def test_get_bool_env_false_values(self, tmp_path):
        """Test _get_bool_env with false values."""
        settings = SpecSettings(root_path=tmp_path)

        with patch.dict(os.environ, {"TEST_VAR": "0"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

        with patch.dict(os.environ, {"TEST_VAR": "false"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

        with patch.dict(os.environ, {"TEST_VAR": "no"}):
            assert settings._get_bool_env("TEST_VAR", True) is False

    def test_get_bool_env_default_fallback(self, tmp_path):
        """Test _get_bool_env fallback to default value."""
        settings = SpecSettings(root_path=tmp_path)

        with patch.dict(os.environ, {"TEST_VAR": "invalid"}):
            assert settings._get_bool_env("TEST_VAR", True) is True
            assert settings._get_bool_env("TEST_VAR", False) is False

    def test_is_initialized_false_when_not_setup(self, tmp_path):
        """Test is_initialized returns False when directories don't exist."""
        settings = SpecSettings(root_path=tmp_path)

        assert settings.is_initialized() is False

    def test_is_initialized_false_when_partial_setup(self, tmp_path):
        """Test is_initialized returns False when only spec_dir exists."""
        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()

        assert settings.is_initialized() is False

    def test_is_initialized_true_when_complete_setup(self, tmp_path):
        """Test is_initialized returns True when both directories exist."""
        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        assert settings.is_initialized() is True

    def test_validate_permissions_not_initialized(self, tmp_path):
        """Test validate_permissions does nothing when not initialized."""
        settings = SpecSettings(root_path=tmp_path)

        # Should not raise exception
        settings.validate_permissions()

    def test_validate_permissions_success(self, tmp_path):
        """Test validate_permissions succeeds with proper permissions."""
        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        # Should not raise exception
        settings.validate_permissions()

    @patch("os.access")
    def test_validate_permissions_spec_dir_no_write(self, mock_access, tmp_path):
        """Test validate_permissions raises error for spec_dir without write access."""
        mock_access.side_effect = lambda path, mode: mode != os.W_OK or str(
            path
        ).endswith(".spec")

        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        with pytest.raises(SpecConfigurationError) as exc_info:
            settings.validate_permissions()

        assert "No write permission" in str(exc_info.value)
        assert str(settings.spec_dir) in str(exc_info.value)

    @patch("os.access")
    def test_validate_permissions_specs_dir_no_write(self, mock_access, tmp_path):
        """Test validate_permissions raises error for specs_dir without write access."""

        def mock_access_fn(path, mode):
            if mode == os.W_OK and str(path).endswith(".specs"):
                return False
            return True

        mock_access.side_effect = mock_access_fn

        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        with pytest.raises(SpecConfigurationError) as exc_info:
            settings.validate_permissions()

        assert "No write permission" in str(exc_info.value)
        assert str(settings.specs_dir) in str(exc_info.value)

class TestSettingsManager:
    """Unit tests for SettingsManager singleton."""

    def setup_method(self):
        """Reset singleton state before each test."""
        reset_settings()

    def teardown_method(self):
        """Clean up singleton state after each test."""
        reset_settings()

    def test_singleton_behavior(self):
        """Test SettingsManager is a singleton."""
        manager1 = SettingsManager()
        manager2 = SettingsManager()

        assert manager1 is manager2

    def test_get_settings_creates_instance(self, tmp_path):
        """Test get_settings creates SpecSettings instance."""
        manager = SettingsManager()
        settings = manager.get_settings(tmp_path)

        assert isinstance(settings, SpecSettings)
        assert settings.root_path == tmp_path

    def test_get_settings_caches_instance(self, tmp_path):
        """Test get_settings caches the SpecSettings instance."""
        manager = SettingsManager()
        settings1 = manager.get_settings(tmp_path)
        settings2 = manager.get_settings(tmp_path)

        assert settings1 is settings2

    def test_get_settings_new_path_creates_new_instance(self, tmp_path):
        """Test get_settings creates new instance for different path."""
        manager = SettingsManager()
        settings1 = manager.get_settings(tmp_path)

        new_path = tmp_path / "different"
        new_path.mkdir()
        settings2 = manager.get_settings(new_path)

        assert settings1 is not settings2
        assert settings1.root_path != settings2.root_path

    def test_get_console_creates_instance(self, tmp_path):
        """Test get_console creates Rich Console instance."""
        manager = SettingsManager()
        console = manager.get_console(tmp_path)

        assert isinstance(console, Console)
        # Verify theme is applied by checking if we can get a themed style
        success_style = console.get_style("success")
        assert success_style is not None

    def test_get_console_caches_instance(self, tmp_path):
        """Test get_console caches the Console instance."""
        manager = SettingsManager()
        console1 = manager.get_console(tmp_path)
        console2 = manager.get_console(tmp_path)

        assert console1 is console2

    def test_get_console_reset_on_settings_change(self, tmp_path):
        """Test get_console resets when settings change."""
        manager = SettingsManager()
        console1 = manager.get_console(tmp_path)

        new_path = tmp_path / "different"
        new_path.mkdir()
        console2 = manager.get_console(new_path)

        # Should be different console instances
        assert console1 is not console2

    @patch.dict(os.environ, {"SPEC_USE_COLOR": "false", "SPEC_CONSOLE_WIDTH": "100"})
    def test_get_console_respects_settings(self, tmp_path):
        """Test get_console respects settings configuration."""
        manager = SettingsManager()
        console = manager.get_console(tmp_path)

        assert console.width == 100
        # Check force_terminal via private attribute
        assert hasattr(console, "_force_terminal")
        assert console._force_terminal is False

    def test_reset_clears_instances(self, tmp_path):
        """Test reset clears cached instances."""
        manager = SettingsManager()
        settings1 = manager.get_settings(tmp_path)
        console1 = manager.get_console(tmp_path)

        manager.reset()

        settings2 = manager.get_settings(tmp_path)
        console2 = manager.get_console(tmp_path)

        assert settings1 is not settings2
        assert console1 is not console2

class TestConvenienceFunctions:
    """Unit tests for convenience functions."""

    def setup_method(self):
        """Reset singleton state before each test."""
        reset_settings()

    def teardown_method(self):
        """Clean up singleton state after each test."""
        reset_settings()

    def test_get_settings_function(self, tmp_path):
        """Test get_settings convenience function."""
        settings = get_settings(tmp_path)

        assert isinstance(settings, SpecSettings)
        assert settings.root_path == tmp_path

    def test_get_console_function(self, tmp_path):
        """Test get_console convenience function."""
        console = get_console(tmp_path)

        assert isinstance(console, Console)
        # Verify theme is applied by checking if we can get a themed style
        success_style = console.get_style("success")
        assert success_style is not None

    def test_reset_settings_function(self, tmp_path):
        """Test reset_settings convenience function."""
        settings1 = get_settings(tmp_path)
        console1 = get_console(tmp_path)

        reset_settings()

        settings2 = get_settings(tmp_path)
        console2 = get_console(tmp_path)

        assert settings1 is not settings2
        assert console1 is not console2

    def test_convenience_functions_use_same_manager(self, tmp_path):
        """Test convenience functions use the same manager instance."""
        settings = get_settings(tmp_path)
        console = get_console(tmp_path)

        # Call again to get cached instances
        settings2 = get_settings(tmp_path)
        console2 = get_console(tmp_path)

        assert settings is settings2
        assert console is console2

class TestSpecTheme:
    """Unit tests for SPEC_THEME constant."""

    def test_spec_theme_is_theme_instance(self):
        """Test SPEC_THEME is a Rich Theme instance."""
        assert isinstance(SPEC_THEME, Theme)

    def test_spec_theme_has_required_styles(self):
        """Test SPEC_THEME contains required style definitions."""
        expected_styles = [
            "success",
            "error",
            "warning",
            "info",
            "debug",
            "path",
            "count",
        ]

        theme_styles = SPEC_THEME.styles
        for style in expected_styles:
            assert style in theme_styles

    def test_spec_theme_style_values(self):
        """Test SPEC_THEME style values are correct."""
        styles = SPEC_THEME.styles

        assert "green" in str(styles["success"])
        assert "red" in str(styles["error"])
        assert "yellow" in str(styles["warning"])
        assert "blue" in str(styles["info"])
        assert "dim" in str(styles["debug"])
        assert "cyan" in str(styles["path"])
        assert "white" in str(styles["count"])

class TestIntegration:
    """Integration tests for settings components."""

    def setup_method(self):
        """Reset singleton state before each test."""
        reset_settings()

    def teardown_method(self):
        """Clean up singleton state after each test."""
        reset_settings()

    @patch.dict(
        os.environ,
        {"SPEC_DEBUG": "1", "SPEC_USE_COLOR": "true", "SPEC_CONSOLE_WIDTH": "80"},
    )
    def test_full_workflow_integration(self, tmp_path):
        """Test complete settings workflow integration."""
        # Create spec directories
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        spec_dir.mkdir()
        specs_dir.mkdir()

        # Get settings and console
        settings = get_settings(tmp_path)
        console = get_console(tmp_path)

        # Verify settings
        assert settings.debug_enabled is True
        assert settings.use_color is True
        assert settings.console_width == 80
        assert settings.is_initialized() is True

        # Verify console configuration
        assert console.width == 80
        assert hasattr(console, "_force_terminal")
        assert console._force_terminal is True
        # Verify theme is applied by checking if we can get a themed style
        success_style = console.get_style("success")
        assert success_style is not None

        # Verify permissions validation
        settings.validate_permissions()  # Should not raise

    def test_settings_path_normalization(self, tmp_path):
        """Test settings properly normalizes and resolves paths."""
        # Create nested path with symbolic components
        nested_path = tmp_path / "project" / "subdir"
        nested_path.mkdir(parents=True)

        settings = SpecSettings(root_path=nested_path)

        # Verify paths are properly resolved
        assert settings.root_path == nested_path
        assert settings.spec_dir == nested_path / ".spec"
        assert settings.specs_dir == nested_path / ".specs"

        # Verify all paths are absolute
        assert settings.root_path.is_absolute()
        assert settings.spec_dir.is_absolute()
        assert settings.specs_dir.is_absolute()
