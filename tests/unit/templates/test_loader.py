import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.config import TemplateConfig
from spec_cli.templates.loader import TemplateLoader, load_template


class TestTemplateLoader:
    """Test TemplateLoader class."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir: Path) -> Mock:
        """Create mock settings with temporary directory."""
        settings = Mock(spec=SpecSettings)
        settings.template_file = temp_dir / ".spectemplate"
        return settings

    def test_template_loader_loads_from_yaml_file(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test loading template from YAML file."""
        template_file = mock_settings.template_file

        # Create valid template file
        template_data = {
            "version": "2.0",
            "description": "Test template",
            "index": "# {{filename}}\n\n**Location**: {{filepath}}\n\nTest index template with enough content for validation\n\n## Purpose\n{{purpose}}\n\n## Overview\n{{overview}}\n\n## Usage\n{{example_usage}}",
            "history": "# History for {{filename}}\n\n**Location**: {{filepath}}\n\nTest history template with enough content\n\n## {{date}} - Initial Creation\n{{context}}",
        }

        with template_file.open("w") as f:
            yaml.dump(template_data, f)

        loader = TemplateLoader(mock_settings)
        config = loader.load_template()

        assert isinstance(config, TemplateConfig)
        assert config.version == "2.0"
        assert config.description == "Test template"
        assert "Test index template" in config.index
        assert "Test history template" in config.history

    def test_template_loader_uses_defaults_when_file_missing(
        self, mock_settings: Mock
    ) -> None:
        """Test fallback to defaults when template file is missing."""
        # Ensure template file doesn't exist
        assert not mock_settings.template_file.exists()

        loader = TemplateLoader(mock_settings)
        config = loader.load_template()

        assert isinstance(config, TemplateConfig)
        assert config.version == "1.0"  # Default version
        assert "{{filename}}" in config.index
        assert "{{filename}}" in config.history

    def test_template_loader_handles_empty_yaml_file(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test handling of empty YAML file."""
        template_file = mock_settings.template_file

        # Create empty file
        template_file.touch()

        loader = TemplateLoader(mock_settings)
        config = loader.load_template()

        # Should fall back to defaults
        assert isinstance(config, TemplateConfig)
        assert config.version == "1.0"

    def test_template_loader_validates_loaded_templates(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test that loaded templates are validated."""
        template_file = mock_settings.template_file

        # Create invalid template (missing required placeholder)
        template_data = {
            "index": "# Missing filename placeholder",
            "history": "# {{filename}}",
        }

        with template_file.open("w") as f:
            yaml.dump(template_data, f)

        loader = TemplateLoader(mock_settings)

        with pytest.raises(SpecTemplateError) as exc_info:
            loader.load_template()

        error_msg = str(exc_info.value).lower()
        assert (
            "validation failed" in error_msg
            or "error reading template file" in error_msg
        )

    def test_template_loader_handles_invalid_yaml(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test handling of invalid YAML syntax."""
        template_file = mock_settings.template_file

        # Create file with invalid YAML
        with template_file.open("w") as f:
            f.write("invalid: yaml: content: [\n")

        loader = TemplateLoader(mock_settings)

        with pytest.raises(SpecTemplateError) as exc_info:
            loader.load_template()

        assert "Invalid YAML" in str(exc_info.value)

    def test_template_loader_saves_template_configuration(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test saving template configuration to file."""
        config = TemplateConfig(
            index="# {{filename}}\n\n**Location**: {{filepath}}\n\nSaved template with enough content\n\n## Purpose\n{{purpose}}\n\n## Overview\n{{overview}}\n\n## Usage\n{{example_usage}}",
            history="# {{filename}}\n\n**Location**: {{filepath}}\n\nSaved history template\n\n## {{date}} - Initial Creation\n{{context}}",
            version="3.0",
            description="Saved config",
        )

        loader = TemplateLoader(mock_settings)
        loader.save_template(config, backup_existing=False)

        # Verify file was created and content is correct
        assert mock_settings.template_file.exists()

        with mock_settings.template_file.open() as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["version"] == "3.0"
        assert saved_data["description"] == "Saved config"
        assert "Saved template" in saved_data["index"]

    def test_template_loader_backs_up_existing_files(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test backing up existing template files."""
        template_file = mock_settings.template_file

        # Create existing file
        with template_file.open("w") as f:
            f.write("existing content")

        config = TemplateConfig(
            index="# {{filename}}\n\n**Location**: {{filepath}}\n\nTemplate with proper content length\n\n## Purpose\n{{purpose}}\n\n## Overview\n{{overview}}\n\n## Usage\n{{example_usage}}",
            history="# {{filename}}\n\n**Location**: {{filepath}}\n\nHistory template\n\n## {{date}} - Initial Creation\n{{context}}",
        )

        loader = TemplateLoader(mock_settings)
        loader.save_template(config, backup_existing=True)

        # Check that backup was created
        backup_files = list(temp_dir.glob("*.backup_*"))
        assert len(backup_files) >= 1

        # Verify backup contains original content
        with backup_files[0].open() as f:
            backup_content = f.read()
        assert "existing content" in backup_content

    def test_template_loader_gets_template_info(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test getting template information."""
        loader = TemplateLoader(mock_settings)

        # Test with missing file
        info = loader.get_template_info()
        assert info["file_exists"] is False
        assert info["using_defaults"] is True

        # Create template file
        template_data = {
            "version": "1.5",
            "description": "Info test",
            "index": "# {{filename}}\n\n**Location**: {{filepath}}\n\nTemplate for info testing with enough content\n\n## Purpose\n{{purpose}}\n\n## Overview\n{{overview}}\n\n## Usage\n{{example_usage}}",
            "history": "# {{filename}}\n\n**Location**: {{filepath}}\n\nHistory template for info testing\n\n## {{date}} - Initial Creation\n{{context}}",
        }

        with mock_settings.template_file.open("w") as f:
            yaml.dump(template_data, f)

        # Test with existing file
        info = loader.get_template_info()
        assert info["file_exists"] is True
        assert info["using_defaults"] is False
        assert info["version"] == "1.5"
        assert info["has_description"] is True
        assert info["placeholder_count"] >= 2


class TestLoadTemplateFunction:
    """Test the convenience load_template function."""

    def test_load_template_convenience_function(self) -> None:
        """Test that the convenience function works."""
        with patch("spec_cli.templates.loader.TemplateLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_config = Mock(spec=TemplateConfig)
            mock_loader.load_template.return_value = mock_config
            mock_loader_class.return_value = mock_loader

            result = load_template()

            assert result == mock_config
            mock_loader_class.assert_called_once_with(None)
            mock_loader.load_template.assert_called_once()

    def test_load_template_with_custom_settings(self) -> None:
        """Test load_template with custom settings."""
        mock_settings = Mock()

        with patch("spec_cli.templates.loader.TemplateLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_config = Mock(spec=TemplateConfig)
            mock_loader.load_template.return_value = mock_config
            mock_loader_class.return_value = mock_loader

            result = load_template(mock_settings)

            assert result == mock_config
            mock_loader_class.assert_called_once_with(mock_settings)


class TestTemplateLoaderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir: Path) -> Mock:
        """Create mock settings with temporary directory."""
        settings = Mock(spec=SpecSettings)
        settings.template_file = temp_dir / ".spectemplate"
        return settings

    def test_template_loader_handles_non_dict_yaml(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test handling of YAML that doesn't contain a dictionary."""
        template_file = mock_settings.template_file

        # Create YAML file with list instead of dict
        with template_file.open("w") as f:
            yaml.dump(["not", "a", "dict"], f)

        loader = TemplateLoader(mock_settings)

        with pytest.raises(SpecTemplateError) as exc_info:
            loader.load_template()

        assert "must contain a YAML dictionary" in str(exc_info.value)

    def test_template_loader_handles_file_permission_errors(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test handling of file permission errors."""
        # Create the template file first so it exists
        template_file = mock_settings.template_file
        template_file.touch()

        loader = TemplateLoader(mock_settings)

        # Mock the _load_from_file method to raise permission error
        with patch.object(
            loader, "_load_from_file", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(SpecTemplateError) as exc_info:
                loader.load_template()

            assert "Failed to load template configuration" in str(exc_info.value)

    def test_template_loader_save_validates_before_saving(
        self, mock_settings: Mock
    ) -> None:
        """Test that save validates configuration before writing."""
        # Create invalid config (this should pass Pydantic but fail our validator)
        config = TemplateConfig(
            index="# {{filename}}\n{{invalid_placeholder}}", history="# {{filename}}"
        )

        loader = TemplateLoader(mock_settings)

        with pytest.raises(SpecTemplateError):
            loader.save_template(config)

    def test_template_loader_backup_handles_errors_gracefully(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test that backup errors don't prevent saving."""
        template_file = mock_settings.template_file

        # Create existing file
        with template_file.open("w") as f:
            f.write("existing")

        config = TemplateConfig(
            index="# {{filename}}\n\n**Location**: {{filepath}}\n\nTemplate with proper content length\n\n## Purpose\n{{purpose}}\n\n## Overview\n{{overview}}\n\n## Usage\n{{example_usage}}",
            history="# {{filename}}\n\n**Location**: {{filepath}}\n\nHistory template\n\n## {{date}} - Initial Creation\n{{context}}",
        )

        loader = TemplateLoader(mock_settings)

        # Mock shutil.copy2 to raise an error
        with patch("shutil.copy2", side_effect=OSError("Backup failed")):
            # Should still save successfully despite backup failure
            loader.save_template(config, backup_existing=True)
            assert template_file.exists()

    def test_template_loader_get_info_handles_corrupt_file(
        self, temp_dir: Path, mock_settings: Mock
    ) -> None:
        """Test template info with corrupt template file."""
        template_file = mock_settings.template_file

        # Create corrupt file
        with template_file.open("w") as f:
            f.write("corrupted: yaml: [")

        loader = TemplateLoader(mock_settings)
        info = loader.get_template_info()

        assert info["file_exists"] is True
        assert "error" in info
        assert "Invalid YAML" in info["error"]
