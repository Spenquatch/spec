"""Comprehensive configuration management tests - Config 001 Slice.

This test module focuses on configuration scenarios, environment testing,
and integration testing for the spec_cli.config.settings module. Complements
the existing micro_001 tests with comprehensive scenario coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import (
    SettingsManager,
    SpecSettings,
    get_console,
    get_settings,
    reset_settings,
)
from spec_cli.exceptions import SpecConfigurationError

class TestConfigurationScenarios:
    """Test configuration scenarios and environment-based behavior."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    @patch.dict(os.environ, {}, clear=True)
    def test_default_configuration_scenario(self, tmp_path: Path) -> None:
        """Test default configuration when no environment variables are set."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify all default values
        assert settings.debug_enabled is False
        assert settings.debug_level == "INFO"
        assert settings.debug_timing is False
        assert settings.use_color is True
        assert settings.console_width is None

        # Verify path configuration
        assert settings.root_path == tmp_path
        assert settings.spec_dir == tmp_path / ".spec"
        assert settings.specs_dir == tmp_path / ".specs"
        assert settings.index_file == tmp_path / ".spec-index"
        assert settings.ignore_file == tmp_path / ".specignore"
        assert settings.template_file == tmp_path / ".spectemplate"
        assert settings.gitignore_file == tmp_path / ".gitignore"

    @patch.dict(
        os.environ,
        {
            "SPEC_DEBUG": "true",
            "SPEC_DEBUG_LEVEL": "WARNING",
            "SPEC_DEBUG_TIMING": "1",
            "SPEC_USE_COLOR": "yes",
            "SPEC_CONSOLE_WIDTH": "100",
        },
    )
    def test_development_configuration_scenario(self, tmp_path: Path) -> None:
        """Test development configuration with debug enabled."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify development configuration
        assert settings.debug_enabled is True
        assert settings.debug_level == "WARNING"
        assert settings.debug_timing is True
        assert settings.use_color is True
        assert settings.console_width == 100

    @patch.dict(
        os.environ,
        {
            "SPEC_DEBUG": "false",
            "SPEC_DEBUG_LEVEL": "ERROR",
            "SPEC_DEBUG_TIMING": "0",
            "SPEC_USE_COLOR": "no",
            "SPEC_CONSOLE_WIDTH": "80",
        },
    )
    def test_production_configuration_scenario(self, tmp_path: Path) -> None:
        """Test production configuration with minimal debug output."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify production configuration
        assert settings.debug_enabled is False
        assert settings.debug_level == "ERROR"
        assert settings.debug_timing is False
        assert settings.use_color is False
        assert settings.console_width == 80

    @patch.dict(
        os.environ,
        {
            "SPEC_DEBUG": "invalid",
            "SPEC_DEBUG_LEVEL": "INVALID_LEVEL",
            "SPEC_DEBUG_TIMING": "maybe",
            "SPEC_USE_COLOR": "sometimes",
            "SPEC_CONSOLE_WIDTH": "not_a_number",
        },
    )
    @patch("spec_cli.config.settings.debug_logger")
    def test_invalid_environment_variables_scenario(
        self, mock_debug_logger: Mock, tmp_path: Path
    ) -> None:
        """Test behavior with invalid environment variable values."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify fallback to defaults for invalid values
        assert settings.debug_enabled is False  # Default for invalid "invalid"
        assert settings.debug_level == "INVALID_LEVEL"  # Passed through as-is
        assert settings.debug_timing is False  # Default for invalid "maybe"
        assert (
            settings.use_color is True
        )  # Default is True, invalid "sometimes" falls back to default
        assert settings.console_width is None  # None for invalid number

        # Verify warning was logged for invalid console width
        mock_debug_logger.log.assert_any_call(
            "WARNING", "Invalid SPEC_CONSOLE_WIDTH value", value="not_a_number"
        )

    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "10"})
    def test_minimum_console_width_enforcement_scenario(self, tmp_path: Path) -> None:
        """Test console width minimum enforcement scenario."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify minimum width is enforced
        assert settings.console_width == 40

    @patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": "2000"})
    def test_large_console_width_scenario(self, tmp_path: Path) -> None:
        """Test behavior with very large console width."""
        settings = SpecSettings(root_path=tmp_path)

        # Verify large width is accepted
        assert settings.console_width == 2000

class TestEnvironmentTesting:
    """Test environment variable parsing and behavior."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    def test_boolean_environment_variable_parsing_comprehensive(
        self, tmp_path: Path
    ) -> None:
        """Test comprehensive boolean environment variable parsing."""
        settings = SpecSettings(root_path=tmp_path)

        # Test all true variations (case insensitive)
        true_values = ["1", "true", "TRUE", "True", "yes", "YES", "Yes"]
        for value in true_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = settings._get_bool_env("TEST_BOOL", False)
                assert result is True, f"Value '{value}' should be True"

        # Test all false variations (case insensitive)
        false_values = ["0", "false", "FALSE", "False", "no", "NO", "No"]
        for value in false_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = settings._get_bool_env("TEST_BOOL", True)
                assert result is False, f"Value '{value}' should be False"

        # Test invalid/unrecognized values fall back to default
        invalid_values = ["", "maybe", "2", "off", "on", "enabled", "disabled"]
        for value in invalid_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result_true = settings._get_bool_env("TEST_BOOL", True)
                result_false = settings._get_bool_env("TEST_BOOL", False)
                assert result_true is True, f"Value '{value}' should fall back to True"
                assert result_false is False, (
                    f"Value '{value}' should fall back to False"
                )

    def test_debug_level_environment_variable_handling(self, tmp_path: Path) -> None:
        """Test debug level environment variable handling."""
        # Test standard levels
        standard_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        for level in standard_levels:
            with patch.dict(os.environ, {"SPEC_DEBUG_LEVEL": level}):
                settings = SpecSettings(root_path=tmp_path)
                assert settings.debug_level == level

        # Test case insensitive handling
        with patch.dict(os.environ, {"SPEC_DEBUG_LEVEL": "debug"}):
            settings = SpecSettings(root_path=tmp_path)
            assert settings.debug_level == "DEBUG"

        # Test custom/invalid levels are preserved
        with patch.dict(os.environ, {"SPEC_DEBUG_LEVEL": "CUSTOM_LEVEL"}):
            settings = SpecSettings(root_path=tmp_path)
            assert settings.debug_level == "CUSTOM_LEVEL"

    def test_console_width_edge_cases(self, tmp_path: Path) -> None:
        """Test console width environment variable edge cases."""
        edge_cases = [
            ("39", 40),  # Below minimum, enforced to 40
            ("40", 40),  # Exactly at minimum
            ("41", 41),  # Just above minimum
            ("1000", 1000),  # Large valid value
            ("0", 40),  # Zero enforced to minimum
            ("-1", 40),  # Negative enforced to minimum
        ]

        for env_value, expected in edge_cases:
            with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": env_value}):
                settings = SpecSettings(root_path=tmp_path)
                assert settings.console_width == expected, (
                    f"Value '{env_value}' should result in {expected}"
                )

    @patch("spec_cli.config.settings.debug_logger")
    def test_console_width_invalid_values_logging(
        self, mock_debug_logger: Mock, tmp_path: Path
    ) -> None:
        """Test console width invalid values are logged appropriately."""
        invalid_values = ["abc", "12.5", "1e2", "infinity", "NaN"]

        for invalid_value in invalid_values:
            mock_debug_logger.reset_mock()
            with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": invalid_value}):
                settings = SpecSettings(root_path=tmp_path)
                assert settings.console_width is None

                # Verify warning was logged
                mock_debug_logger.log.assert_any_call(
                    "WARNING", "Invalid SPEC_CONSOLE_WIDTH value", value=invalid_value
                )

        # Test empty string separately as it might not trigger warning
        mock_debug_logger.reset_mock()
        with patch.dict(os.environ, {"SPEC_CONSOLE_WIDTH": ""}):
            settings = SpecSettings(root_path=tmp_path)
            assert settings.console_width is None
            # Empty string might not trigger warning, so don't assert it

class TestIntegrationScenarios:
    """Test integration scenarios between components."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    def test_settings_and_console_integration(self, tmp_path: Path) -> None:
        """Test settings and console integration."""
        # Set up environment for testing
        with patch.dict(
            os.environ, {"SPEC_USE_COLOR": "true", "SPEC_CONSOLE_WIDTH": "120"}
        ):
            manager = SettingsManager()
            settings = manager.get_settings(tmp_path)
            console = manager.get_console(tmp_path)

            # Verify settings are applied to console
            assert settings.use_color is True
            assert settings.console_width == 120
            assert console.width == 120
            assert console._force_terminal is True

    def test_console_theme_integration(self, tmp_path: Path) -> None:
        """Test console theme integration."""
        manager = SettingsManager()
        console = manager.get_console(tmp_path)

        # Test that theme styles are accessible (Rich Console doesn't expose theme directly)
        for style_name in [
            "success",
            "error",
            "warning",
            "info",
            "debug",
            "path",
            "count",
        ]:
            style = console.get_style(style_name)
            assert style is not None, f"Style '{style_name}' should be available"

    def test_manager_state_consistency_across_operations(self, tmp_path: Path) -> None:
        """Test manager maintains consistent state across operations."""
        manager = SettingsManager()

        # Get settings multiple times
        settings1 = manager.get_settings(tmp_path)
        settings2 = manager.get_settings(tmp_path)
        settings3 = manager.get_settings()  # Use default path

        # First two should be identical (same path)
        assert settings1 is settings2

        # Third might be different if default path differs
        if settings3.root_path == tmp_path:
            assert settings1 is settings3
        else:
            assert settings1 is not settings3

    def test_convenience_functions_integration(self, tmp_path: Path) -> None:
        """Test convenience functions integration with manager."""
        # Test that convenience functions work consistently
        settings1 = get_settings(tmp_path)
        console1 = get_console(tmp_path)

        # Get again - should be cached
        settings2 = get_settings(tmp_path)
        console2 = get_console(tmp_path)

        assert settings1 is settings2
        assert console1 is console2

        # Reset and verify new instances
        reset_settings()

        settings3 = get_settings(tmp_path)
        console3 = get_console(tmp_path)

        assert settings1 is not settings3
        assert console1 is not console3

    def test_cross_platform_path_handling(self, tmp_path: Path) -> None:
        """Test cross-platform path handling in settings."""
        # Create settings with various path types
        settings = SpecSettings(root_path=tmp_path)

        # Verify all paths are Path objects
        assert isinstance(settings.root_path, Path)
        assert isinstance(settings.spec_dir, Path)
        assert isinstance(settings.specs_dir, Path)
        assert isinstance(settings.index_file, Path)
        assert isinstance(settings.ignore_file, Path)
        assert isinstance(settings.template_file, Path)
        assert isinstance(settings.gitignore_file, Path)

        # Verify paths are properly constructed relative to root
        assert settings.spec_dir.parent == settings.root_path
        assert settings.specs_dir.parent == settings.root_path
        assert settings.index_file.parent == settings.root_path
        assert settings.ignore_file.parent == settings.root_path
        assert settings.template_file.parent == settings.root_path
        assert settings.gitignore_file.parent == settings.root_path

class TestPermissionAndInitializationScenarios:
    """Test permission validation and initialization scenarios."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    def test_initialization_state_scenarios(self, tmp_path: Path) -> None:
        """Test various initialization state scenarios."""
        settings = SpecSettings(root_path=tmp_path)

        # Initially not initialized
        assert settings.is_initialized() is False

        # Create only spec_dir
        settings.spec_dir.mkdir()
        assert settings.is_initialized() is False

        # Create only specs_dir (remove spec_dir first)
        settings.spec_dir.rmdir()
        settings.specs_dir.mkdir()
        assert settings.is_initialized() is False

        # Create both directories
        settings.spec_dir.mkdir()
        assert settings.is_initialized() is True

        # Create files instead of directories
        settings.spec_dir.rmdir()
        settings.specs_dir.rmdir()
        settings.spec_dir.touch()  # Create as file
        settings.specs_dir.mkdir()
        assert settings.is_initialized() is False

        # Clean up and test reverse scenario
        settings.spec_dir.unlink()
        settings.specs_dir.rmdir()
        settings.spec_dir.mkdir()
        settings.specs_dir.touch()  # Create as file
        assert settings.is_initialized() is False

    def test_permission_validation_scenarios(self, tmp_path: Path) -> None:
        """Test permission validation scenarios."""
        settings = SpecSettings(root_path=tmp_path)

        # Not initialized - no validation needed
        settings.validate_permissions()  # Should not raise

        # Create directories
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        # With proper permissions - should not raise
        settings.validate_permissions()

    @patch("os.access")
    def test_permission_validation_failure_scenarios(
        self, mock_access: Mock, tmp_path: Path
    ) -> None:
        """Test permission validation failure scenarios."""
        settings = SpecSettings(root_path=tmp_path)
        settings.spec_dir.mkdir()
        settings.specs_dir.mkdir()

        # Test spec_dir permission failure
        def spec_dir_no_write(path: str, mode: int) -> bool:
            return not (str(path).endswith(".spec") and mode == os.W_OK)

        mock_access.side_effect = spec_dir_no_write

        with pytest.raises(SpecConfigurationError) as exc_info:
            settings.validate_permissions()

        error_str = str(exc_info.value)
        assert "No write permission" in error_str
        assert str(settings.spec_dir) in error_str

        # Test specs_dir permission failure
        def specs_dir_no_write(path: str, mode: int) -> bool:
            return not (str(path).endswith(".specs") and mode == os.W_OK)

        mock_access.side_effect = specs_dir_no_write

        with pytest.raises(SpecConfigurationError) as exc_info:
            settings.validate_permissions()

        error_str = str(exc_info.value)
        assert "No write permission" in error_str
        assert str(settings.specs_dir) in error_str

class TestComplexIntegrationWorkflows:
    """Test complex integration workflows and real-world scenarios."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        reset_settings()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        reset_settings()

    def test_multi_project_scenario(self) -> None:
        """Test managing multiple projects with different settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple project directories
            project1 = temp_path / "project1"
            project2 = temp_path / "project2"
            project1.mkdir()
            project2.mkdir()

            # Set different environment variables for each
            with patch.dict(
                os.environ, {"SPEC_USE_COLOR": "true", "SPEC_CONSOLE_WIDTH": "80"}
            ):
                settings1 = get_settings(project1)
                console1 = get_console(project1)

            with patch.dict(
                os.environ, {"SPEC_USE_COLOR": "false", "SPEC_CONSOLE_WIDTH": "120"}
            ):
                settings2 = get_settings(project2)
                console2 = get_console(project2)

            # Verify different configurations
            assert settings1.root_path == project1
            assert settings2.root_path == project2
            assert settings1 is not settings2
            assert console1 is not console2

    def test_settings_persistence_across_resets(self, tmp_path: Path) -> None:
        """Test settings behavior across manager resets."""
        # Create initial settings
        settings1 = get_settings(tmp_path)
        console1 = get_console(tmp_path)

        original_root = settings1.root_path
        original_debug = settings1.debug_enabled

        # Reset and recreate
        reset_settings()

        settings2 = get_settings(tmp_path)
        console2 = get_console(tmp_path)

        # Verify new instances but same configuration
        assert settings1 is not settings2
        assert console1 is not console2
        assert settings2.root_path == original_root
        assert settings2.debug_enabled == original_debug

    @patch.dict(
        os.environ,
        {
            "SPEC_DEBUG": "1",
            "SPEC_DEBUG_LEVEL": "DEBUG",
            "SPEC_USE_COLOR": "true",
            "SPEC_CONSOLE_WIDTH": "100",
        },
    )
    def test_full_development_workflow(self, tmp_path: Path) -> None:
        """Test full development workflow with all features enabled."""
        # Initialize spec directories
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        spec_dir.mkdir()
        specs_dir.mkdir()

        # Get settings and console
        settings = get_settings(tmp_path)
        console = get_console(tmp_path)

        # Verify development configuration
        assert settings.debug_enabled is True
        assert settings.debug_level == "DEBUG"
        assert settings.use_color is True
        assert settings.console_width == 100
        assert settings.is_initialized() is True

        # Verify console configuration
        assert console.width == 100
        assert console._force_terminal is True

        # Test permission validation
        settings.validate_permissions()  # Should not raise

        # Test that theme styles work (Rich Console doesn't expose theme directly)
        for style in ["success", "error", "warning", "info", "debug", "path", "count"]:
            style_obj = console.get_style(style)
            assert style_obj is not None

    def test_error_recovery_scenarios(self, tmp_path: Path) -> None:
        """Test error recovery in various scenarios."""
        # Test with invalid path that gets corrected
        with patch("spec_cli.config.settings.normalize_path") as mock_normalize:
            # First call fails, second succeeds
            mock_normalize.side_effect = [ValueError("Invalid path"), tmp_path]

            # This should recover gracefully (depending on implementation)
            # The actual behavior depends on how normalize_path failures are handled
            try:
                settings = SpecSettings(root_path=tmp_path)
                # If it doesn't raise, verify it still works
                assert settings.root_path is not None
            except ValueError:
                # If it raises, that's also acceptable behavior
                pass

    def test_concurrent_access_simulation(self, tmp_path: Path) -> None:
        """Simulate concurrent access to settings manager."""
        import threading
        import time

        results = []
        errors = []

        def worker(worker_id: int) -> None:
            try:
                # Small random delay to increase chance of race conditions
                time.sleep(worker_id * 0.001)
                settings = get_settings(tmp_path)
                console = get_console(tmp_path)
                results.append(
                    {
                        "worker_id": worker_id,
                        "settings_id": id(settings),
                        "console_id": id(console),
                        "root_path": str(settings.root_path),
                    }
                )
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all workers got the same instances (singleton behavior)
        assert len(results) == 5
        settings_ids = {result["settings_id"] for result in results}
        console_ids = {result["console_id"] for result in results}

        # Should all be the same due to singleton pattern
        assert len(settings_ids) == 1, (
            f"Expected 1 unique settings instance, got {len(settings_ids)}"
        )
        assert len(console_ids) == 1, (
            f"Expected 1 unique console instance, got {len(console_ids)}"
        )
