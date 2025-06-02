import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.config import TemplateConfig
from spec_cli.templates.defaults import get_default_template_config
from spec_cli.templates.generator import SpecContentGenerator, generate_spec_content


class TestSpecContentGenerator:
    """Test SpecContentGenerator class."""

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
        settings.specs_dir = temp_dir / ".specs"
        settings.template_file = temp_dir / ".spectemplate"
        return settings

    @pytest.fixture
    def basic_template(self) -> TemplateConfig:
        """Create a basic template for testing."""
        return TemplateConfig(
            index="# {{filename}}\n\n**Location**: {{filepath}}\n\n## Purpose\n{{purpose}}",
            history="# History for {{filename}}\n\n**Location**: {{filepath}}\n\n## {{date}} - Initial Creation\n{{context}}",
        )

    @pytest.fixture
    def mock_dependencies(self) -> Generator[Dict[str, Mock], None, None]:
        """Mock all dependencies for isolated testing."""
        with patch(
            "spec_cli.templates.generator.DirectoryManager"
        ) as mock_dir_mgr_class, patch(
            "spec_cli.templates.generator.FileMetadataExtractor"
        ) as mock_meta_class, patch(
            "spec_cli.templates.generator.TemplateSubstitution"
        ) as mock_sub_class:
            # Setup directory manager mock
            mock_dir_mgr = Mock()
            mock_dir_mgr_class.return_value = mock_dir_mgr
            mock_dir_mgr.ensure_specs_directory.return_value = None
            mock_dir_mgr.create_spec_directory.return_value = Path(
                "/tmp/.specs/test.py"
            )
            mock_dir_mgr.check_existing_specs.return_value = {
                "index.md": False,
                "history.md": False,
            }
            mock_dir_mgr.backup_existing_files.return_value = []

            # Setup metadata extractor mock
            mock_meta = Mock()
            mock_meta_class.return_value = mock_meta
            mock_meta.get_file_metadata.return_value = {
                "type": "python",
                "category": "source",
                "size": 1024,
                "is_binary": False,
            }

            # Setup substitution mock
            mock_sub = Mock()
            mock_sub_class.return_value = mock_sub
            mock_sub.substitute.return_value = "Generated content"
            mock_sub.validate_template_syntax.return_value = []
            mock_sub.get_variables_in_template.return_value = {
                "filename",
                "filepath",
                "purpose",
            }
            mock_sub.preview_substitution.return_value = {
                "variables_found": ["filename", "filepath", "purpose"],
                "variables_resolved": ["filename", "filepath"],
                "variables_unresolved": ["purpose"],
                "syntax_issues": [],
            }
            mock_sub.get_substitution_stats.return_value = {
                "template_length": 100,
                "unique_variables": 3,
                "substitution_coverage": 66.7,
                "syntax_valid": True,
            }

            yield {
                "directory_manager": mock_dir_mgr,
                "metadata_extractor": mock_meta,
                "substitution": mock_sub,
            }

    def test_generator_creates_index_and_history_files(
        self,
        basic_template: TemplateConfig,
        mock_dependencies: Dict[str, Mock],
        temp_dir: Path,
    ) -> None:
        """Test that generator creates both index.md and history.md files."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        # Mock file writing
        created_files = {}

        def mock_write(file_path: Path, content: str) -> None:
            created_files[file_path.name] = file_path

        with patch.object(generator, "_write_content_file", side_effect=mock_write):
            result = generator.generate_spec_content(test_file, basic_template)

        assert "index" in result
        assert "history" in result
        assert "index.md" in created_files
        assert "history.md" in created_files

        # Verify substitution was called for both templates
        assert mock_dependencies["substitution"].substitute.call_count == 2

    def test_generator_uses_file_based_variables(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that generator extracts file-based variables."""
        generator = SpecContentGenerator()
        test_file = Path("src/models/user.py")

        variables = generator._get_file_based_variables(test_file)

        assert variables["filename"] == "user.py"
        assert variables["filepath"] == "src/models/user.py"
        assert variables["file_extension"] == "py"
        assert variables["file_stem"] == "user"
        assert variables["parent_directory"] == "models"
        assert variables["file_type"] == "python"  # From mock metadata

    def test_generator_applies_custom_variables_with_precedence(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that custom variables override file-based variables."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")
        custom_vars = {
            "filename": "CUSTOM_NAME.py",  # Override file-based
            "custom_field": "Custom Value",  # New variable
            "purpose": "Custom purpose",  # Override default
        }

        substitutions = generator._prepare_substitutions(
            test_file, custom_vars, basic_template
        )

        # Custom variables should take precedence
        assert substitutions["filename"] == "CUSTOM_NAME.py"
        assert substitutions["custom_field"] == "Custom Value"
        assert substitutions["purpose"] == "Custom purpose"

        # File-based variables should still be present for non-overridden values
        assert substitutions["file_extension"] == "py"

    def test_generator_handles_backup_existing_files(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that generator handles backing up existing files."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        # Mock existing files
        mock_dependencies["directory_manager"].check_existing_specs.return_value = {
            "index.md": True,
            "history.md": True,
        }
        mock_dependencies["directory_manager"].backup_existing_files.return_value = [
            Path("/backup/index.md.backup"),
            Path("/backup/history.md.backup"),
        ]

        with patch.object(generator, "_write_content_file"):
            generator.generate_spec_content(
                test_file, basic_template, backup_existing=True
            )

        # Verify backup was called
        mock_dependencies[
            "directory_manager"
        ].backup_existing_files.assert_called_once()

    def test_generator_handles_file_writing_errors(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that generator handles file writing errors gracefully."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        def mock_write_error(file_path: Path, content: str) -> None:
            raise OSError("Permission denied")

        with patch.object(
            generator, "_write_content_file", side_effect=mock_write_error
        ):
            with pytest.raises(SpecTemplateError) as exc_info:
                generator.generate_spec_content(test_file, basic_template)

        assert "Failed to generate spec content" in str(exc_info.value)

    def test_generator_integrates_with_substitution_engine(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test integration with the substitution engine."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        with patch.object(generator, "_write_content_file"):
            generator.generate_spec_content(test_file, basic_template)

        # Verify substitution engine was used
        mock_sub = mock_dependencies["substitution"]
        assert mock_sub.substitute.call_count == 2

        # Check that the template content was passed to substitution
        calls = mock_sub.substitute.call_args_list
        call_args = [call.args[0] for call in calls if call.args]
        assert basic_template.index in call_args
        assert basic_template.history in call_args

    def test_generator_integrates_with_directory_manager(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test integration with directory manager."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        with patch.object(generator, "_write_content_file"):
            generator.generate_spec_content(test_file, basic_template)

        # Verify directory manager methods were called
        dir_mgr = mock_dependencies["directory_manager"]
        dir_mgr.ensure_specs_directory.assert_called_once()
        dir_mgr.create_spec_directory.assert_called_once_with(test_file)
        dir_mgr.check_existing_specs.assert_called_once()

    def test_generator_integrates_with_metadata_extractor(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test integration with metadata extractor."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        variables = generator._get_file_based_variables(test_file)

        # Verify metadata extractor was used
        mock_dependencies[
            "metadata_extractor"
        ].get_file_metadata.assert_called_once_with(test_file)

        # Verify metadata was included in variables
        assert variables["file_type"] == "python"
        assert variables["file_category"] == "source"

    def test_generator_creates_spec_directories(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that generator creates spec directories correctly."""
        generator = SpecContentGenerator()
        test_file = Path("src/models/user.py")

        with patch.object(generator, "_write_content_file"):
            generator.generate_spec_content(test_file, basic_template)

        # Verify directory creation was called with correct path
        mock_dependencies[
            "directory_manager"
        ].create_spec_directory.assert_called_once_with(test_file)

    def test_generator_previews_generation_results(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test preview functionality."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")
        custom_vars = {"custom_field": "value"}

        preview = generator.preview_generation(test_file, basic_template, custom_vars)

        assert preview["file_path"] == str(test_file)
        assert (
            preview["template_name"] == "default"
        )  # Default since template has no name
        assert preview["custom_variables_provided"] == 1
        assert "template_variables" in preview
        assert "index" in preview["template_variables"]
        assert "history" in preview["template_variables"]
        assert "substitution_sample" in preview
        assert isinstance(preview["generation_ready"], bool)

    def test_generator_validates_generation_requirements(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test validation functionality."""
        generator = SpecContentGenerator()

        # Test with non-existent file
        non_existent_file = Path("nonexistent.py")
        issues = generator.validate_generation(non_existent_file, basic_template)
        assert any("does not exist" in issue for issue in issues)

        # Test with valid setup - use a simple template with only resolvable variables
        simple_template = TemplateConfig(
            index="# {{filename}}\n\n**Location**: {{filepath}}",
            history="# History for {{filename}}\n\n**Location**: {{filepath}}",
        )
        with patch.object(Path, "exists", return_value=True):
            # Mock the substitution's get_variables_in_template to return only variables we have
            with patch.object(
                generator.substitution, "get_variables_in_template"
            ) as mock_get_vars:
                mock_get_vars.return_value = {"filename", "filepath"}
                issues = generator.validate_generation(Path("test.py"), simple_template)
                # Should have no issues with mocked dependencies returning valid data
                assert len(issues) == 0

    def test_generator_provides_generation_statistics(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test statistics functionality."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        stats = generator.get_generation_stats(test_file, basic_template)

        assert stats["file_path"] == str(test_file)
        assert stats["template_name"] == "default"
        assert "total_variables_available" in stats
        assert "index_template" in stats
        assert "history_template" in stats
        assert "generation_ready" in stats

        # Verify substitution stats were called
        mock_sub = mock_dependencies["substitution"]
        assert mock_sub.get_substitution_stats.call_count == 2

    def test_generator_handles_missing_source_files(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test handling of missing source files."""
        generator = SpecContentGenerator()
        missing_file = Path("missing.py")

        # Test validation catches missing file
        issues = generator.validate_generation(missing_file, basic_template)
        assert any("does not exist" in issue for issue in issues)

        # Test preview handles missing file gracefully
        preview = generator.preview_generation(missing_file, basic_template)
        assert preview["file_path"] == str(missing_file)
        # Should still work since we're just analyzing templates, not reading the source file

    def test_generator_extracts_template_defaults(
        self, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test extraction of template defaults."""
        generator = SpecContentGenerator()

        # Test with basic template
        basic_template = TemplateConfig(
            index="# {{filename}}",
            history="# {{filename}}",
            description="Test template",
            version="2.0",
        )

        defaults = generator._get_template_defaults(basic_template)

        assert defaults["template_name"] == "default"  # No name attribute
        assert defaults["template_description"] == "Test template"
        assert defaults["template_version"] == "2.0"
        assert "creation_date" in defaults
        assert "creation_time" in defaults

    def test_backward_compatibility_function_works(
        self, basic_template: TemplateConfig, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that the backward compatibility function works."""
        test_file = Path("test.py")

        with patch.object(
            SpecContentGenerator, "generate_spec_content"
        ) as mock_generate:
            mock_generate.return_value = {
                "index": Path("index.md"),
                "history": Path("history.md"),
            }

            result = generate_spec_content(test_file, basic_template)

            assert "index" in result
            assert "history" in result
            mock_generate.assert_called_once_with(test_file, basic_template, None)


class TestGeneratorFileOperations:
    """Test file operation methods in isolation."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_write_content_file_creates_directories(self, temp_dir: Path) -> None:
        """Test that _write_content_file creates parent directories."""
        generator = SpecContentGenerator()
        test_file = temp_dir / "deep" / "nested" / "file.md"
        content = "Test content"

        generator._write_content_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_write_content_file_handles_encoding(self, temp_dir: Path) -> None:
        """Test that _write_content_file handles UTF-8 encoding correctly."""
        generator = SpecContentGenerator()
        test_file = temp_dir / "unicode.md"
        content = "Test with unicode: 中文 émojis 🎉"

        generator._write_content_file(test_file, content)

        assert test_file.exists()
        read_content = test_file.read_text(encoding="utf-8")
        assert read_content == content

    def test_write_content_file_handles_permission_errors(self, temp_dir: Path) -> None:
        """Test that _write_content_file handles permission errors."""
        import platform

        # Skip on Windows as directory permissions work differently
        if platform.system() == "Windows":
            pytest.skip("Directory permission tests not reliable on Windows")

        generator = SpecContentGenerator()

        # Create a read-only directory
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        test_file = readonly_dir / "file.md"

        try:
            with pytest.raises(SpecTemplateError) as exc_info:
                generator._write_content_file(test_file, "content")

            assert "Failed to write content" in str(exc_info.value)
        finally:
            # Cleanup: restore write permissions
            readonly_dir.chmod(0o755)


class TestGeneratorMetadataHandling:
    """Test metadata extraction and handling."""

    def test_get_file_based_variables_with_metadata(self) -> None:
        """Test variable extraction with successful metadata extraction."""
        generator = SpecContentGenerator()
        test_file = Path("src/models/user.py")

        # Mock successful metadata extraction
        with patch.object(
            generator.metadata_extractor, "get_file_metadata"
        ) as mock_extract:
            mock_extract.return_value = {
                "type": "python",
                "category": "source",
                "size": 2048,
                "is_binary": False,
            }

            variables = generator._get_file_based_variables(test_file)

            assert variables["filename"] == "user.py"
            assert variables["file_type"] == "python"
            assert variables["file_category"] == "source"
            assert variables["file_size"] == "2.0 KB"
            assert variables["is_binary"] is False

    def test_get_file_based_variables_without_metadata(self) -> None:
        """Test variable extraction when metadata extraction fails."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        # Mock failed metadata extraction
        with patch.object(
            generator.metadata_extractor, "get_file_metadata"
        ) as mock_extract:
            mock_extract.side_effect = Exception("Metadata extraction failed")

            variables = generator._get_file_based_variables(test_file)

            # Should return minimal variables
            assert variables["filename"] == "test.py"
            assert variables["file_type"] == "unknown"
            assert variables["file_category"] == "other"
            assert variables["is_binary"] is False
            assert variables["file_size"] == "unknown"

    def test_file_size_formatting(self) -> None:
        """Test that file sizes are formatted correctly."""
        generator = SpecContentGenerator()
        test_file = Path("test.py")

        # Test different file sizes
        test_cases = [
            (500, "500 bytes"),
            (1536, "1.5 KB"),
            (2097152, "2.00 MB"),
            (1024, "1.0 KB"),
        ]

        for size_bytes, expected in test_cases:
            with patch.object(
                generator.metadata_extractor, "get_file_metadata"
            ) as mock_extract:
                mock_extract.return_value = {"size": size_bytes, "type": "test"}

                variables = generator._get_file_based_variables(test_file)
                assert variables["file_size"] == expected


class TestGeneratorIntegration:
    """Integration tests that test multiple components working together."""

    def test_full_generation_workflow_with_real_template(self) -> None:
        """Test full generation workflow with real template configuration."""
        # Use real template from defaults
        template = get_default_template_config()
        generator = SpecContentGenerator()
        test_file = Path("example.py")

        # Mock only the file system dependencies
        with patch.object(
            generator.directory_manager, "ensure_specs_directory"
        ), patch.object(
            generator.directory_manager, "create_spec_directory"
        ) as mock_create, patch.object(
            generator.directory_manager, "check_existing_specs"
        ) as mock_check, patch.object(generator, "_write_content_file") as mock_write:
            mock_create.return_value = Path("/test/.specs/example.py")
            mock_check.return_value = {"index.md": False, "history.md": False}

            # Mock metadata extraction
            with patch.object(
                generator.metadata_extractor, "get_file_metadata"
            ) as mock_meta:
                mock_meta.return_value = {
                    "type": "python",
                    "category": "source",
                    "size": 1024,
                    "is_binary": False,
                }

                result = generator.generate_spec_content(test_file, template)

                # Verify both files were created
                assert "index" in result
                assert "history" in result
                assert mock_write.call_count == 2

                # Verify the generated content contains substituted variables
                write_calls = mock_write.call_args_list
                index_content = write_calls[0][0][
                    1
                ]  # First call, second argument (content)
                history_content = write_calls[1][0][
                    1
                ]  # Second call, second argument (content)

                assert "example.py" in index_content
                assert "example.py" in history_content
                assert "{{filename}}" not in index_content  # Should be substituted
                assert "{{filename}}" not in history_content  # Should be substituted
