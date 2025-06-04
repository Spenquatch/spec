import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

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
    """Test the SpecSettings dataclass functionality."""

    def test_spec_settings_initializes_with_correct_paths(self) -> None:
        """Test that SpecSettings creates correct computed paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)

            assert settings.root_path == root_path
            assert settings.spec_dir == root_path / ".spec"
            assert settings.specs_dir == root_path / ".specs"
            assert settings.index_file == root_path / ".spec-index"
            assert settings.ignore_file == root_path / ".specignore"
            assert settings.template_file == root_path / ".spectemplate"
            assert settings.gitignore_file == root_path / ".gitignore"

    def test_spec_settings_detects_debug_environment_variables(self) -> None:
        """Test that SpecSettings reads debug environment variables correctly."""
        with patch.dict(
            os.environ,
            {
                "SPEC_DEBUG": "1",
                "SPEC_DEBUG_LEVEL": "WARNING",
                "SPEC_DEBUG_TIMING": "yes",
            },
            clear=True,
        ):
            settings = SpecSettings()

            assert settings.debug_enabled is True
            assert settings.debug_level == "WARNING"
            assert settings.debug_timing is True

    def test_spec_settings_detects_terminal_environment_variables(self) -> None:
        """Test that SpecSettings reads terminal environment variables correctly."""
        with patch.dict(
            os.environ,
            {"SPEC_USE_COLOR": "false", "SPEC_CONSOLE_WIDTH": "120"},
            clear=True,
        ):
            settings = SpecSettings()

            assert settings.use_color is False
            assert settings.console_width == 120

    def test_spec_settings_validates_initialization_state(self) -> None:
        """Test that SpecSettings correctly detects initialization state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)

            # Not initialized initially
            assert settings.is_initialized() is False

            # Create directories
            settings.spec_dir.mkdir()
            settings.specs_dir.mkdir()

            # Should be initialized now
            assert settings.is_initialized() is True

    def test_spec_settings_validates_permissions(self) -> None:
        """Test that SpecSettings validates directory permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            settings = SpecSettings(root_path=root_path)

            # Should not raise when not initialized
            settings.validate_permissions()

            # Create directories
            settings.spec_dir.mkdir()
            settings.specs_dir.mkdir()

            # Should not raise when permissions are OK
            settings.validate_permissions()

            # Test with non-writable directory (mock)
            with patch("os.access", return_value=False):
                with pytest.raises(SpecConfigurationError) as exc_info:
                    settings.validate_permissions()

                assert "No write permission" in str(exc_info.value)

    def test_spec_settings_handles_invalid_console_width(self) -> None:
        """Test that SpecSettings handles invalid console width gracefully."""
        with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "invalid"}, clear=True):
            # Should not raise, just use default
            settings = SpecSettings()
            assert settings.console_width is None

        with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "20"}, clear=True):
            # Should enforce minimum width
            settings = SpecSettings()
            assert settings.console_width == 40

    def test_spec_settings_bool_env_parsing(self) -> None:
        """Test _get_bool_env method with various inputs."""
        settings = SpecSettings()

        # Test true values
        with patch.dict(os.environ, {"TEST_VAR": "1"}, clear=True):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "true"}, clear=True):
            assert settings._get_bool_env("TEST_VAR", False) is True

        with patch.dict(os.environ, {"TEST_VAR": "YES"}, clear=True):
            assert settings._get_bool_env("TEST_VAR", False) is True

        # Test false values
        with patch.dict(os.environ, {"TEST_VAR": "0"}, clear=True):
            assert settings._get_bool_env("TEST_VAR", True) is False

        with patch.dict(os.environ, {"TEST_VAR": "false"}, clear=True):
            assert settings._get_bool_env("TEST_VAR", True) is False

        # Test default value
        with patch.dict(os.environ, {}, clear=True):
            assert settings._get_bool_env("NONEXISTENT", True) is True
            assert settings._get_bool_env("NONEXISTENT", False) is False


class TestSettingsManager:
    """Test the SettingsManager class functionality."""

    def teardown_method(self) -> None:
        """Reset settings manager after each test."""
        reset_settings()

    def test_settings_manager_provides_singleton_behavior(self) -> None:
        """Test that SettingsManager returns the same instance."""
        manager = SettingsManager()
        settings1 = manager.get_settings()
        settings2 = manager.get_settings()

        assert settings1 is settings2

    def test_settings_manager_handles_root_path_changes(self) -> None:
        """Test that SettingsManager creates new instance for different root paths."""
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                path1 = Path(temp_dir1)
                path2 = Path(temp_dir2)

                manager = SettingsManager()
                settings1 = manager.get_settings(path1)
                settings2 = manager.get_settings(path2)

                assert settings1 is not settings2
                assert settings1.root_path == path1
                assert settings2.root_path == path2

    def test_settings_manager_resets_console_when_settings_change(self) -> None:
        """Test that console is reset when settings change."""
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                path1 = Path(temp_dir1)
                path2 = Path(temp_dir2)

                manager = SettingsManager()
                # Get console for first path
                console1 = manager.get_console(path1)

                # Get console for second path (should reset)
                console2 = manager.get_console(path2)

                # Should be different console instances
                assert console1 is not console2

    def test_settings_manager_reset_functionality(self) -> None:
        """Test that reset_settings() clears instances."""
        manager1 = SettingsManager()
        settings1 = manager1.get_settings()
        console1 = manager1.get_console()

        reset_settings()

        manager2 = SettingsManager()
        settings2 = manager2.get_settings()
        console2 = manager2.get_console()

        assert manager1 is not manager2
        assert settings1 is not settings2
        assert console1 is not console2


class TestConsoleIntegration:
    """Test Rich console integration."""

    def teardown_method(self) -> None:
        """Reset settings manager after each test."""
        reset_settings()

    def test_console_uses_spec_theme_consistently(self) -> None:
        """Test that console uses the correct SPEC_THEME."""
        manager = SettingsManager()
        console = manager.get_console()

        # Test that SPEC_THEME contains expected styles
        assert "success" in SPEC_THEME.styles
        assert "error" in SPEC_THEME.styles
        assert "warning" in SPEC_THEME.styles
        assert "info" in SPEC_THEME.styles

        # Test that console can use the styles
        from rich.text import Text

        text = Text("test", style="success")
        # Should not raise any errors when rendering styled text
        console.render(text)

    def test_console_respects_color_settings(self) -> None:
        """Test that console respects color environment variables."""
        with patch.dict(os.environ, {"SPEC_USE_COLOR": "true"}, clear=True):
            reset_settings()
            manager = SettingsManager()
            console = manager.get_console()

            # When color is enabled, force_terminal should be True
            assert console._force_terminal is True

        with patch.dict(os.environ, {"SPEC_USE_COLOR": "false"}, clear=True):
            reset_settings()
            manager = SettingsManager()
            console = manager.get_console()

            # When color is disabled, force_terminal should be False
            assert console._force_terminal is False

    def test_console_handles_width_configuration(self) -> None:
        """Test that console respects width configuration."""
        with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "100"}, clear=True):
            reset_settings()
            manager = SettingsManager()
            console = manager.get_console()

            # Check width configuration
            assert console._width == 100


class TestConvenienceFunctions:
    """Test convenience functions."""

    def teardown_method(self) -> None:
        """Reset settings manager after each test."""
        reset_settings()

    def test_get_settings_convenience_function(self) -> None:
        """Test that get_settings() works correctly."""
        settings = get_settings()
        manager = SettingsManager()
        manager_settings = manager.get_settings()

        assert settings is manager_settings

    def test_get_console_convenience_function(self) -> None:
        """Test that get_console() works correctly."""
        console = get_console()
        manager = SettingsManager()
        manager_console = manager.get_console()

        assert console is manager_console

    def test_settings_manager_singleton_decorator_integration(self) -> None:
        """Test that SettingsManager uses singleton decorator correctly."""
        manager1 = SettingsManager()
        manager2 = SettingsManager()

        # Should be the same instance due to singleton decorator
        assert manager1 is manager2

        # Should have singleton attributes
        assert hasattr(SettingsManager, "_is_singleton")
        assert hasattr(SettingsManager, "_original_class")
        assert SettingsManager._is_singleton is True
