import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from spec_cli.config.loader import ConfigurationLoader
from spec_cli.exceptions import SpecConfigurationError


class TestConfigurationLoader:
    """Test the ConfigurationLoader class functionality."""

    def test_configuration_loader_loads_from_yaml(self) -> None:
        """Test loading configuration from YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / ".specconfig.yaml"

            # Create test YAML config
            config_data = {
                "debug": {"enabled": True, "level": "DEBUG"},
                "terminal": {"use_color": False},
            }
            with config_file.open("w") as f:
                yaml.dump(config_data, f)

            loader = ConfigurationLoader(root_path)
            result = loader.load_configuration()

            assert result == config_data

    def test_configuration_loader_loads_from_pyproject_toml(self) -> None:
        """Test loading configuration from pyproject.toml [tool.spec] section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            toml_file = root_path / "pyproject.toml"

            # Create test TOML config
            toml_content = """
[tool.spec]
debug = {enabled = true, level = "INFO"}
terminal = {console_width = 120}
"""
            with toml_file.open("w") as f:
                f.write(toml_content)

            loader = ConfigurationLoader(root_path)
            result = loader.load_configuration()

            expected = {
                "debug": {"enabled": True, "level": "INFO"},
                "terminal": {"console_width": 120},
            }
            assert result == expected

    def test_configuration_loader_handles_missing_files(self) -> None:
        """Test that loader handles missing configuration files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            loader = ConfigurationLoader(root_path)

            result = loader.load_configuration()

            # Should return empty dict when no config files exist
            assert result == {}

    def test_configuration_loader_respects_precedence_order(self) -> None:
        """Test that TOML config overrides YAML config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"
            toml_file = root_path / "pyproject.toml"

            # Create YAML config
            yaml_config = {
                "debug": {"enabled": False, "level": "ERROR"},
                "terminal": {"use_color": True},
                "only_in_yaml": "value",
            }
            with yaml_file.open("w") as f:
                yaml.dump(yaml_config, f)

            # Create TOML config that overrides some values
            toml_content = """
[tool.spec]
debug = {enabled = true, level = "DEBUG"}
only_in_toml = "value"
"""
            with toml_file.open("w") as f:
                f.write(toml_content)

            loader = ConfigurationLoader(root_path)
            result = loader.load_configuration()

            # TOML should override YAML for debug section
            expected = {
                "debug": {"enabled": True, "level": "DEBUG"},  # From TOML
                "terminal": {"use_color": True},  # From YAML
                "only_in_yaml": "value",  # From YAML
                "only_in_toml": "value",  # From TOML
            }
            assert result == expected

    def test_configuration_loader_handles_malformed_yaml(self) -> None:
        """Test error handling for malformed YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"

            # Create invalid YAML
            with yaml_file.open("w") as f:
                f.write("invalid: yaml: content: [")

            loader = ConfigurationLoader(root_path)

            with pytest.raises(SpecConfigurationError) as exc_info:
                loader.load_configuration()

            assert "Invalid YAML syntax" in str(exc_info.value)
            assert str(yaml_file) in str(exc_info.value)

    def test_configuration_loader_handles_malformed_toml(self) -> None:
        """Test error handling for malformed TOML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            toml_file = root_path / "pyproject.toml"

            # Create invalid TOML
            with toml_file.open("w") as f:
                f.write("[invalid toml content")

            loader = ConfigurationLoader(root_path)

            with pytest.raises(SpecConfigurationError) as exc_info:
                loader.load_configuration()

            assert "Invalid TOML syntax" in str(exc_info.value)
            assert str(toml_file) in str(exc_info.value)

    def test_configuration_loader_handles_encoding_errors(self) -> None:
        """Test error handling for files with encoding issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"

            # Create file with invalid UTF-8
            with yaml_file.open("wb") as f:
                f.write(b"debug: \xff\xfe invalid utf-8")

            loader = ConfigurationLoader(root_path)

            with pytest.raises(SpecConfigurationError) as exc_info:
                loader.load_configuration()

            assert "file encoding issue" in str(exc_info.value)

    def test_configuration_loader_get_available_sources(self) -> None:
        """Test getting list of available configuration sources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"

            loader = ConfigurationLoader(root_path)

            # No sources initially
            assert loader.get_available_sources() == []

            # Create YAML file
            yaml_file.touch()
            available = loader.get_available_sources()
            assert len(available) == 1
            assert yaml_file in available

    def test_configuration_loader_validate_source_syntax(self) -> None:
        """Test syntax validation without loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"

            loader = ConfigurationLoader(root_path)

            # Valid YAML
            with yaml_file.open("w") as f:
                yaml.dump({"debug": {"enabled": True}}, f)

            assert loader.validate_source_syntax(yaml_file) is True

            # Invalid YAML
            with yaml_file.open("w") as f:
                f.write("invalid: yaml: [")

            assert loader.validate_source_syntax(yaml_file) is False

    def test_configuration_loader_handles_empty_yaml(self) -> None:
        """Test handling of empty YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            yaml_file = root_path / ".specconfig.yaml"

            # Create empty YAML file
            yaml_file.touch()

            loader = ConfigurationLoader(root_path)
            result = loader.load_configuration()

            # Should return empty dict for empty file
            assert result == {}

    def test_configuration_loader_handles_toml_import_error(self) -> None:
        """Test graceful handling when TOML library is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            toml_file = root_path / "pyproject.toml"

            # Create TOML file
            with toml_file.open("w") as f:
                f.write("[tool.spec]\ndebug = {enabled = true}")

            loader = ConfigurationLoader(root_path)

            # Mock import error for both tomllib and tomli
            with patch("builtins.__import__", side_effect=ImportError):
                result = loader.load_configuration()

                # Should skip TOML file and return empty dict
                assert result == {}
