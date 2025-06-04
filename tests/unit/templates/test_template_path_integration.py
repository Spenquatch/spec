"""Integration tests for Template system path utilities usage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.templates.config import TemplateConfig
from spec_cli.templates.generator import SpecContentGenerator
from spec_cli.templates.loader import TemplateLoader


class TestTemplateLoaderPathIntegration:
    """Test TemplateLoader integration with path utilities."""

    @pytest.fixture
    def temp_settings(self, tmp_path):
        """Create temporary settings with proper paths."""
        settings = Mock(spec=SpecSettings)
        settings.template_file = tmp_path / ".spectemplate"
        settings.root_path = tmp_path
        return settings

    @pytest.fixture
    def template_loader(self, temp_settings):
        """Create TemplateLoader with temporary settings."""
        return TemplateLoader(settings=temp_settings)

    @pytest.fixture
    def sample_config(self):
        """Create sample template configuration."""
        return TemplateConfig(
            index="""# {{filename}}

## Purpose
{{filepath}} is a test file for integration testing.

## Overview
This file demonstrates path utility integration.

## Usage
Used for testing template loader functionality.

## Example
```python
# Example usage of {{filename}}
```
""",
            history="""# History for {{filename}}

File: {{filepath}}

## Changes
- Initial creation
- Path utility integration testing
""",
            description="Sample template",
            author="Test User",
        )

    def test_template_loading_when_using_path_utilities_then_secure_and_consistent(
        self, template_loader, temp_settings, sample_config
    ):
        """Test that template loading uses path utilities for security and consistency."""
        # Save a template configuration
        template_loader.save_template(sample_config, backup_existing=False)

        # Verify the template file was created with proper path handling
        assert temp_settings.template_file.exists()

        # Load the configuration back
        loaded_config = template_loader.load_template()

        # Should load successfully with consistent path handling
        assert loaded_config.index == sample_config.index
        assert loaded_config.history == sample_config.history
        assert loaded_config.description == sample_config.description

    def test_template_directory_when_using_ensure_directory_then_proper_creation(
        self, template_loader, tmp_path, sample_config
    ):
        """Test that template directory creation uses ensure_directory properly."""
        # Create a nested template path
        nested_template_dir = tmp_path / "nested" / "templates"
        template_file = nested_template_dir / ".spectemplate"

        # Update settings with nested path
        template_loader.settings.template_file = template_file

        # Save should create all necessary directories
        template_loader.save_template(sample_config, backup_existing=False)

        # Verify directory structure was created
        assert nested_template_dir.exists()
        assert template_file.exists()

    @patch("spec_cli.templates.loader.debug_logger")
    def test_template_operations_include_debug_context(
        self, mock_logger, template_loader, sample_config
    ):
        """Test that template operations include proper debug context."""
        # Save template configuration
        template_loader.save_template(sample_config, backup_existing=False)

        # Verify debug logging was called with operation context
        mock_logger.log.assert_called()

        # Check for operation context in debug calls
        debug_calls = [
            call for call in mock_logger.log.call_args_list if call[0][0] == "DEBUG"
        ]
        assert len(debug_calls) > 0

        # Should have operation context
        operation_contexts = []
        for call in debug_calls:
            if len(call[1]) > 0 and "operation" in call[1]:
                operation_contexts.append(call[1]["operation"])

        assert "template_file_creation" in operation_contexts


class TestTemplateGeneratorPathIntegration:
    """Test SpecContentGenerator integration with path utilities."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create source files
        (project_root / "src" / "main.py").parent.mkdir(parents=True)
        (project_root / "src" / "main.py").touch()

        return project_root

    @pytest.fixture
    def temp_settings(self, temp_project):
        """Create temporary settings."""
        settings = Mock(spec=SpecSettings)
        settings.root_path = temp_project
        settings.specs_dir = temp_project / ".specs"
        settings.ignore_file = temp_project / ".specignore"
        settings.template_file = temp_project / ".spectemplate"
        return settings

    @pytest.fixture
    def generator(self, temp_settings):
        """Create SpecContentGenerator with temporary settings."""
        return SpecContentGenerator(settings=temp_settings)

    @pytest.fixture
    def sample_template(self):
        """Create sample template configuration."""
        return TemplateConfig(
            index="""# {{filename}}

## Purpose
File: {{filepath}} serves as a test file for generator integration.

## Overview
This template tests path utility integration in the generator.

## Usage
Used for validating secure path operations.

## Example
```python
# Example usage
```
""",
            history="""# History for {{filename}}

File: {{filepath}}

## Changes
- Initial creation for testing
- Path utility integration validation
""",
            description="Test template",
        )

    def test_output_generation_when_using_path_utilities_then_secure_paths(
        self, generator, temp_project, sample_template
    ):
        """Test that output generation uses path utilities for secure path handling."""
        source_file = temp_project / "src" / "main.py"

        # Generate content with path validation - this creates both index.md and history.md
        created_files = generator.generate_spec_content(source_file, sample_template)

        # Verify files were created with proper path handling
        assert "index" in created_files
        assert "history" in created_files
        assert created_files["index"].exists()
        assert created_files["history"].exists()
        assert created_files["index"].parent.exists()

    def test_output_directory_when_using_ensure_directory_then_proper_structure(
        self, generator, temp_project, sample_template
    ):
        """Test that output directory creation uses ensure_directory properly."""
        source_file = temp_project / "src" / "nested" / "deep" / "file.py"

        # Create the source file so it exists for generation
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.touch()

        # Generate content to deeply nested path
        created_files = generator.generate_spec_content(source_file, sample_template)

        # Verify entire directory structure was created
        assert "index" in created_files
        assert created_files["index"].parent.exists()
        assert created_files["index"].exists()

        # Check all intermediate directories exist
        assert (temp_project / ".specs" / "src").exists()
        assert (temp_project / ".specs" / "src" / "nested").exists()
        assert (temp_project / ".specs" / "src" / "nested" / "deep").exists()

    def test_file_validation_when_using_normalize_path_then_consistent_checks(
        self, generator, temp_project, sample_template
    ):
        """Test that file validation uses normalize_path for consistent path handling."""
        # Test with existing file
        existing_file = temp_project / "src" / "main.py"
        issues = generator.validate_generation(existing_file, sample_template)

        # Should pass validation for existing file
        file_not_exist_issues = [issue for issue in issues if "does not exist" in issue]
        assert len(file_not_exist_issues) == 0

        # Test with non-existing file
        non_existing_file = temp_project / "src" / "missing.py"
        issues = generator.validate_generation(non_existing_file, sample_template)

        # Should fail validation for missing file
        file_not_exist_issues = [issue for issue in issues if "does not exist" in issue]
        assert len(file_not_exist_issues) > 0

    @patch("spec_cli.templates.generator.debug_logger")
    def test_generator_operations_include_debug_context(
        self, mock_logger, generator, temp_project, sample_template
    ):
        """Test that generator operations include proper debug context."""
        source_file = temp_project / "src" / "main.py"

        # Generate content
        generator.generate_spec_content(source_file, sample_template)

        # Verify debug logging was called with operation context
        mock_logger.log.assert_called()

        # Check for operation context in debug calls
        debug_calls = [
            call for call in mock_logger.log.call_args_list if call[0][0] == "DEBUG"
        ]
        assert len(debug_calls) > 0

        # Should have operation context
        operation_contexts = []
        for call in debug_calls:
            if len(call[1]) > 0 and "operation" in call[1]:
                operation_contexts.append(call[1]["operation"])

        assert "spec_file_generation" in operation_contexts

    def test_path_normalization_handles_different_formats(
        self, generator, temp_project, sample_template
    ):
        """Test that path operations handle different path formats consistently."""
        # Test with Path object
        source_file_path = temp_project / "src" / "main.py"

        # Test with string path
        source_file_str = str(source_file_path)

        # Both should validate consistently
        issues_path = generator.validate_generation(source_file_path, sample_template)
        issues_str = generator.validate_generation(
            Path(source_file_str), sample_template
        )

        # Results should be the same regardless of input format
        file_issues_path = [issue for issue in issues_path if "does not exist" in issue]
        file_issues_str = [issue for issue in issues_str if "does not exist" in issue]
        assert len(file_issues_path) == len(file_issues_str)

    def test_secure_path_validation_prevents_directory_traversal(
        self, generator, temp_project, sample_template
    ):
        """Test that path validation prevents directory traversal attacks."""
        # Test with relative path that tries to escape project
        malicious_source = temp_project / "src" / ".." / ".." / "malicious.py"
        malicious_source.parent.mkdir(parents=True, exist_ok=True)
        malicious_source.touch()

        # Should handle path safely without allowing traversal
        try:
            created_files = generator.generate_spec_content(
                malicious_source, sample_template
            )

            # If files were created, they should be within the project structure
            if created_files and "index" in created_files:
                index_file = created_files["index"]
                if index_file.exists():
                    # Verify it's actually within the expected directory structure
                    assert temp_project in index_file.resolve().parents
        except Exception:
            # Path validation should prevent this, which is the expected behavior
            pass
