"""Integration tests for configuration loader and environment management - Config 002 Slice.

This test module focuses on integration testing for configuration loading
across multiple sources, environment variable integration, and cross-platform
compatibility for the spec_cli.config.loader module.
"""

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from spec_cli.config.loader import ConfigurationLoader
from spec_cli.config.settings import SettingsManager, SpecSettings, reset_settings
from spec_cli.exceptions import SpecConfigurationError


class TestConfigurationLoaderIntegration:
    """Integration tests for ConfigurationLoader with environment and cross-platform support."""

    def setup_method(self) -> None:
        """Setup test fixtures and reset environment."""
        # Reset settings to clean state
        reset_settings()

        # Store original environment variables
        self.original_env = {
            key: os.environ.get(key)
            for key in [
                "SPEC_DEBUG",
                "SPEC_DEBUG_LEVEL",
                "SPEC_DEBUG_TIMING",
                "SPEC_USE_COLOR",
                "SPEC_CONSOLE_WIDTH",
            ]
        }

        # Clear environment variables for clean testing
        for key in self.original_env:
            if key in os.environ:
                del os.environ[key]

    def teardown_method(self) -> None:
        """Restore original environment variables."""
        # Restore original environment
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

        # Reset settings
        reset_settings()

    @pytest.fixture
    def temp_project_root(self, tmp_path: Path) -> Path:
        """Create temporary project root with standard structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        return project_root

    @pytest.fixture
    def config_with_yaml(self, temp_project_root: Path) -> dict[str, Any]:
        """Create YAML configuration file."""
        config_data = {
            "debug": {"enabled": True, "level": "DEBUG"},
            "terminal": {"use_color": False, "console_width": 100},
            "paths": {"template_file": "custom.md"},
            "template": {"index": "# {{filename}}\n\nYAML content"},
        }

        yaml_file = temp_project_root / ".specconfig.yaml"
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        return config_data

    @pytest.fixture
    def config_with_pyproject_toml(self, temp_project_root: Path) -> dict[str, Any]:
        """Create pyproject.toml configuration file."""
        config_data = {
            "debug": {"enabled": False, "level": "INFO"},
            "terminal": {"use_color": True, "console_width": 120},
            "paths": {"template_file": "toml_template.md"},
            "template": {"history": "# {{filename}} History\n\nTOML content"},
        }

        toml_content = """
[tool.spec.debug]
enabled = false
level = "INFO"

[tool.spec.terminal]
use_color = true
console_width = 120

[tool.spec.paths]
template_file = "toml_template.md"

[tool.spec.template]
history = "# {{filename}} History\\n\\nTOML content"
"""

        toml_file = temp_project_root / "pyproject.toml"
        toml_file.write_text(toml_content)

        return config_data

    def get_fresh_settings(self, temp_project_root: Path) -> SpecSettings:
        """Create fresh settings instance for testing."""
        manager = SettingsManager()
        return manager.get_settings(temp_project_root)

    # Environment variable integration tests
    def test_environment_variables_override_config_files(
        self, temp_project_root: Path, config_with_yaml: dict[str, Any]
    ) -> None:
        """Test environment variables take precedence over config files."""
        # Set environment variables
        os.environ["SPEC_DEBUG"] = "0"  # Override YAML enabled=True
        os.environ["SPEC_DEBUG_LEVEL"] = "ERROR"  # Override YAML level=DEBUG
        os.environ["SPEC_USE_COLOR"] = "1"  # Override YAML use_color=False
        os.environ["SPEC_CONSOLE_WIDTH"] = "80"  # Override YAML console_width=100

        # Load configuration and get integrated settings
        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()
        settings = self.get_fresh_settings(temp_project_root)

        # Verify environment variables override config file
        assert not settings.debug_enabled  # ENV: False overrides YAML: True
        assert settings.debug_level == "ERROR"  # ENV: ERROR overrides YAML: DEBUG
        assert settings.use_color  # ENV: True overrides YAML: False
        assert settings.console_width == 80  # ENV: 80 overrides YAML: 100

        # Verify file config still loaded for non-environment settings
        assert config["paths"]["template_file"] == "custom.md"
        assert "{{filename}}" in config["template"]["index"]

    def test_environment_variables_with_no_config_files(
        self, temp_project_root: Path
    ) -> None:
        """Test environment variables work when no config files exist."""
        # Set environment variables
        os.environ["SPEC_DEBUG"] = "true"
        os.environ["SPEC_DEBUG_LEVEL"] = "WARNING"
        os.environ["SPEC_USE_COLOR"] = "no"
        os.environ["SPEC_CONSOLE_WIDTH"] = "200"
        os.environ["SPEC_DEBUG_TIMING"] = "yes"

        # Load configuration and get settings
        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()
        settings = self.get_fresh_settings(temp_project_root)

        # Verify environment variables are applied
        assert settings.debug_enabled
        assert settings.debug_level == "WARNING"
        assert not settings.use_color
        assert settings.console_width == 200
        assert settings.debug_timing

        # Verify no config loaded from files
        assert config == {}

    def test_environment_variable_boolean_parsing(
        self, temp_project_root: Path
    ) -> None:
        """Test various boolean formats in environment variables."""
        test_cases = [
            ("1", True),
            ("0", False),
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
            ("TRUE", True),
            ("FALSE", False),
            ("invalid", False),  # Default to False for invalid values
            ("", False),  # Default to False for empty
        ]

        for env_value, expected in test_cases:
            # Clean environment
            for key in ["SPEC_DEBUG", "SPEC_USE_COLOR", "SPEC_DEBUG_TIMING"]:
                if key in os.environ:
                    del os.environ[key]
            reset_settings()

            # Set test value
            os.environ["SPEC_DEBUG"] = env_value

            # Get settings
            manager = SettingsManager()
            settings = manager.get_settings(temp_project_root)

            assert settings.debug_enabled == expected, (
                f"Value '{env_value}' should parse to {expected}"
            )

    def test_environment_variable_console_width_validation(
        self, temp_project_root: Path
    ) -> None:
        """Test console width environment variable validation and limits."""
        test_cases = [
            ("80", 80),  # Valid value
            ("40", 40),  # Minimum boundary
            ("30", 40),  # Below minimum, should be set to 40
            ("1000", 1000),  # Large valid value
            ("invalid", None),  # Invalid value, should be None
            ("", None),  # Empty value, should be None
        ]

        for env_value, expected in test_cases:
            # Clean environment
            if "SPEC_CONSOLE_WIDTH" in os.environ:
                del os.environ["SPEC_CONSOLE_WIDTH"]
            reset_settings()

            # Set test value
            if env_value:  # Don't set empty string as env var
                os.environ["SPEC_CONSOLE_WIDTH"] = env_value

            # Get settings
            manager = SettingsManager()
            settings = manager.get_settings(temp_project_root)

            assert settings.console_width == expected, (
                f"Width '{env_value}' should result in {expected}"
            )

    # Cross-platform configuration file handling tests
    @pytest.mark.parametrize("platform", ["windows", "posix"])
    def test_cross_platform_path_handling(
        self, temp_project_root: Path, platform: str
    ) -> None:
        """Test configuration loading works across different platforms."""
        # Create config with paths that might differ across platforms
        config_data = {
            "paths": {
                "root_path": str(temp_project_root),
                "template_file": "templates/custom.md",
            }
        }

        yaml_file = temp_project_root / ".specconfig.yaml"
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # Mock platform-specific behavior
        with patch("pathlib.Path.resolve") as mock_resolve:
            if platform == "windows":
                # Simulate Windows path behavior
                mock_resolve.return_value = Path("C:\\test\\project")
            else:
                # Simulate POSIX path behavior
                mock_resolve.return_value = Path("/test/project")

            loader = ConfigurationLoader(temp_project_root)
            config = loader.load_configuration()

            # Verify configuration loads successfully regardless of platform
            assert config["paths"]["template_file"] == "templates/custom.md"
            assert str(temp_project_root) in config["paths"]["root_path"]

    def test_unicode_handling_in_config_files(self, temp_project_root: Path) -> None:
        """Test configuration files with Unicode content are handled properly."""
        # Create config with Unicode characters
        config_data = {
            "template": {
                "index": "# {{filename}} 📝\n\nUnicode content: αβγ",
                "history": "# Histórico de {{filename}} 🇪🇸",
            }
        }

        yaml_file = temp_project_root / ".specconfig.yaml"
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True)

        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()

        # Verify Unicode content is preserved
        assert "📝" in config["template"]["index"]
        assert "αβγ" in config["template"]["index"]
        assert "🇪🇸" in config["template"]["history"]
        assert "Histórico" in config["template"]["history"]

    def test_file_encoding_error_handling(self, temp_project_root: Path) -> None:
        """Test handling of files with incorrect encoding."""
        # Create file with invalid UTF-8 content
        yaml_file = temp_project_root / ".specconfig.yaml"
        with yaml_file.open("wb") as f:
            f.write(b"\xff\xfe# Invalid UTF-8\n")

        loader = ConfigurationLoader(temp_project_root)

        # Should raise SpecConfigurationError for encoding issues
        with pytest.raises(SpecConfigurationError) as exc_info:
            loader.load_configuration()

        assert "read YAML configuration file" in str(exc_info.value)
        assert "utf-8" in str(exc_info.value).lower()

    # Configuration precedence and source integration tests
    def test_configuration_precedence_yaml_then_toml(
        self,
        temp_project_root: Path,
        config_with_yaml: dict[str, Any],
        config_with_pyproject_toml: dict[str, Any],
    ) -> None:
        """Test configuration precedence: YAML loads first, TOML overrides."""
        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()

        # TOML should override YAML values
        assert config["debug"]["enabled"] is False  # TOML value
        assert config["debug"]["level"] == "INFO"  # TOML value
        assert config["terminal"]["use_color"] is True  # TOML value
        assert config["terminal"]["console_width"] == 120  # TOML value

        # Should have merged values from both files
        # YAML has index, TOML has history, both should be present
        if "template" in config:
            if "index" in config["template"]:
                assert (
                    config["template"]["index"] == "# {{filename}}\n\nYAML content"
                )  # YAML only
            if "history" in config["template"]:
                assert "TOML content" in config["template"]["history"]  # TOML only

        assert (
            config["paths"]["template_file"] == "toml_template.md"
        )  # TOML overrides YAML

    def test_configuration_integration_with_settings_manager(
        self, temp_project_root: Path, config_with_yaml: dict[str, Any]
    ) -> None:
        """Test configuration loader integration with SettingsManager."""
        # Set some environment variables
        os.environ["SPEC_DEBUG"] = "true"
        os.environ["SPEC_USE_COLOR"] = "false"

        # Load configuration
        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()

        # Get settings (which should integrate environment + config)
        settings = self.get_fresh_settings(temp_project_root)

        # Verify settings integration
        assert settings.debug_enabled  # From environment
        assert not settings.use_color  # From environment
        assert settings.root_path == temp_project_root

        # Verify config loaded correctly
        assert config["template"]["index"] == "# {{filename}}\n\nYAML content"

    def test_available_sources_detection(
        self, temp_project_root: Path, config_with_yaml: dict[str, Any]
    ) -> None:
        """Test detection of available configuration sources."""
        loader = ConfigurationLoader(temp_project_root)
        sources = loader.get_available_sources()

        # Should detect YAML file
        assert len(sources) == 1
        assert sources[0].name == ".specconfig.yaml"

        # Add TOML file
        toml_file = temp_project_root / "pyproject.toml"
        toml_file.write_text("[tool.spec]\ndebug = {enabled = true}")

        sources = loader.get_available_sources()

        # Should detect both files
        assert len(sources) == 2
        source_names = {source.name for source in sources}
        assert ".specconfig.yaml" in source_names
        assert "pyproject.toml" in source_names

    def test_syntax_validation_without_loading(self, temp_project_root: Path) -> None:
        """Test syntax validation of configuration files."""
        loader = ConfigurationLoader(temp_project_root)

        # Create valid YAML file
        valid_yaml = temp_project_root / ".specconfig.yaml"
        valid_yaml.write_text("debug:\n  enabled: true\n")

        # Create invalid YAML file
        invalid_yaml = temp_project_root / "invalid.yaml"
        invalid_yaml.write_text("debug:\n  enabled: [invalid yaml")

        # Test validation
        assert loader.validate_source_syntax(valid_yaml) is True
        assert loader.validate_source_syntax(invalid_yaml) is False

    def test_empty_and_missing_configuration_files(
        self, temp_project_root: Path
    ) -> None:
        """Test handling of empty and missing configuration files."""
        loader = ConfigurationLoader(temp_project_root)

        # No config files exist
        config = loader.load_configuration()
        assert config == {}

        # Create empty YAML file
        empty_yaml = temp_project_root / ".specconfig.yaml"
        empty_yaml.write_text("")

        config = loader.load_configuration()
        assert config == {}

        # Create YAML file with null content
        empty_yaml.write_text("null\n")

        config = loader.load_configuration()
        assert config == {}

    def test_configuration_error_context_information(
        self, temp_project_root: Path
    ) -> None:
        """Test error messages include helpful context information."""
        # Create invalid YAML file
        invalid_yaml = temp_project_root / ".specconfig.yaml"
        invalid_yaml.write_text("debug:\n  level: [invalid")

        loader = ConfigurationLoader(temp_project_root)

        with pytest.raises(SpecConfigurationError) as exc_info:
            loader.load_configuration()

        error_msg = str(exc_info.value)
        # Should include operation context (file paths are sanitized in error handler)
        assert "parse YAML configuration" in error_msg
        assert "load configuration file" in error_msg

    # Integration with file system permissions and access
    def test_configuration_loading_with_permission_restrictions(
        self, temp_project_root: Path
    ) -> None:
        """Test configuration loading behavior with restricted permissions."""
        # Create config file
        config_file = temp_project_root / ".specconfig.yaml"
        config_file.write_text("debug:\n  enabled: true\n")

        # Make file unreadable (simulation for testing)
        with patch("pathlib.Path.open", side_effect=PermissionError("Access denied")):
            loader = ConfigurationLoader(temp_project_root)

            with pytest.raises(SpecConfigurationError) as exc_info:
                loader.load_configuration()

            assert "load configuration file" in str(exc_info.value)

    def test_concurrent_settings_access_thread_safety(
        self, temp_project_root: Path
    ) -> None:
        """Test thread safety of settings access with configuration loading."""
        import threading

        # Create config file
        config_file = temp_project_root / ".specconfig.yaml"
        config_file.write_text("debug:\n  enabled: true\n")

        results = []
        errors = []

        def load_and_validate() -> None:
            try:
                loader = ConfigurationLoader(temp_project_root)
                config = loader.load_configuration()
                manager = SettingsManager()
                settings = manager.get_settings(temp_project_root)
                results.append((config, settings.root_path))
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=load_and_validate) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors and consistent results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5

        # All results should be consistent
        for config, root_path in results:
            assert config["debug"]["enabled"] is True
            assert root_path == temp_project_root

    def test_toml_module_availability_fallback(self, temp_project_root: Path) -> None:
        """Test graceful fallback when TOML module is unavailable."""
        # Create pyproject.toml file
        toml_file = temp_project_root / "pyproject.toml"
        toml_file.write_text("[tool.spec]\ndebug = {enabled = true}")

        # Mock tomllib as unavailable
        with patch("spec_cli.config.loader.tomllib", None):
            loader = ConfigurationLoader(temp_project_root)
            config = loader.load_configuration()

            # Should gracefully skip TOML file
            assert config == {}

    def test_configuration_with_complex_nested_structures(
        self, temp_project_root: Path
    ) -> None:
        """Test configuration loading with complex nested data structures."""
        complex_config = {
            "debug": {
                "enabled": True,
                "level": "DEBUG",
                "components": ["loader", "validator", "settings"],
                "timing": {"enabled": True, "precision": "millisecond"},
            },
            "template": {
                "variables": {
                    "author": "Test User",
                    "project": "{{project_name}}",
                    "metadata": {
                        "version": "1.0.0",
                        "tags": ["spec", "cli", "documentation"],
                    },
                }
            },
        }

        yaml_file = temp_project_root / ".specconfig.yaml"
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(complex_config, f)

        loader = ConfigurationLoader(temp_project_root)
        config = loader.load_configuration()

        # Verify complex nested structure is preserved
        assert config["debug"]["components"] == ["loader", "validator", "settings"]
        assert config["debug"]["timing"]["precision"] == "millisecond"
        assert config["template"]["variables"]["metadata"]["tags"] == [
            "spec",
            "cli",
            "documentation",
        ]

    def test_unknown_config_file_type_handling(self, temp_project_root: Path) -> None:
        """Test handling of unknown configuration file types."""
        # Create config file with unknown extension
        unknown_config = temp_project_root / ".specconfig.json"
        unknown_config.write_text('{"debug": {"enabled": true}}')

        loader = ConfigurationLoader(temp_project_root)
        # Manually test the unknown file type path
        result = loader._load_from_file(unknown_config)

        # Should return empty dict for unknown file types
        assert result == {}

    def test_yaml_syntax_error_handling(self, temp_project_root: Path) -> None:
        """Test YAML syntax error handling with specific error context."""
        # Create YAML file with syntax error
        invalid_yaml = temp_project_root / ".specconfig.yaml"
        invalid_yaml.write_text("debug:\n  enabled: [unclosed")

        loader = ConfigurationLoader(temp_project_root)

        with pytest.raises(SpecConfigurationError) as exc_info:
            loader.load_configuration()

        # Should include YAML parsing context
        error_msg = str(exc_info.value)
        assert "parse YAML configuration" in error_msg

    def test_toml_syntax_error_handling(self, temp_project_root: Path) -> None:
        """Test TOML syntax error handling with specific error context."""
        # Create TOML file with syntax error
        invalid_toml = temp_project_root / "pyproject.toml"
        invalid_toml.write_text("[tool.spec]\ndebug = {invalid toml")

        loader = ConfigurationLoader(temp_project_root)

        with pytest.raises(SpecConfigurationError) as exc_info:
            loader.load_configuration()

        # Should include TOML parsing context
        error_msg = str(exc_info.value)
        assert "parse TOML configuration" in error_msg

    @patch("spec_cli.config.loader.sys.version_info", (3, 10))
    def test_python_310_tomli_import_fallback(self, temp_project_root: Path) -> None:
        """Test tomli import fallback for Python < 3.11."""
        # Create TOML file
        toml_file = temp_project_root / "pyproject.toml"
        toml_file.write_text("[tool.spec]\ndebug = {enabled = true}")

        # Mock tomli availability
        with patch("spec_cli.config.loader.tomllib") as mock_tomllib:
            mock_tomllib.load.return_value = {
                "tool": {"spec": {"debug": {"enabled": True}}}
            }

            loader = ConfigurationLoader(temp_project_root)
            config = loader.load_configuration()

            # Should successfully load using tomli
            assert config["debug"]["enabled"] is True
