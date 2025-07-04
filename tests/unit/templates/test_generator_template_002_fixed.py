"""Comprehensive unit tests for template generator core generation.

Tests target: SpecContentGenerator.generate_spec_content, load_template (convenience function),
and apply_variables (_prepare_substitutions and variable processing functions).
Coverage target: 80%+ for template generation core logic.
"""

# Mock the problematic AI imports before importing the main module
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

with patch.dict(
    "sys.modules",
    {
        "torch": Mock(),
        "spec_cli.ai.providers.generation": Mock(),
        "spec_cli.ai.providers.local": Mock(),
        "spec_cli.ai.providers.manager": Mock(),
        "spec_cli.templates.ai_integration": Mock(),
    },
):
    from spec_cli.config.settings import SpecSettings
    from spec_cli.exceptions import SpecTemplateError
    from spec_cli.templates.config import TemplateConfig
    from spec_cli.templates.generator import SpecContentGenerator, generate_spec_content


class TestSpecContentGeneratorBasic:
    """Basic unit tests for SpecContentGenerator functionality."""

    def test_init_with_settings(self):
        """Test generator initialization with explicit settings."""
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.ignore_file = Path(".specignore")
        mock_settings.specs_dir = Path(".specs")
        mock_settings.project_root = Path(".")
        mock_settings.ignore_patterns = []

        generator = SpecContentGenerator(mock_settings)
        assert generator.settings == mock_settings

    @patch("spec_cli.templates.generator.get_settings")
    def test_init_with_default_settings(self, mock_get_settings):
        """Test generator initialization with default settings."""
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.ignore_file = Path(".specignore")
        mock_settings.specs_dir = Path(".specs")
        mock_settings.project_root = Path(".")
        mock_settings.ignore_patterns = []
        mock_get_settings.return_value = mock_settings

        generator = SpecContentGenerator()
        assert generator.settings == mock_settings


class TestPrepareSubstitutionsUnit:
    """Unit tests for variable preparation methods."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.ignore_file = Path(".specignore")
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.project_root = Path(".")
        self.mock_settings.ignore_patterns = []

        self.generator = SpecContentGenerator(self.mock_settings)

        # Create valid template (minimum 10 chars each)
        self.template = TemplateConfig(
            index="# {{filename}} test template content",
            history="# {{filename}} history content template",
            description="Test template",
            version="1.0",
        )

    def test_get_file_based_variables_basic(self):
        """Test basic file variable extraction."""
        file_path = Path("src/test_file.py")

        with patch.object(
            self.generator.metadata_extractor, "get_file_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = None

            result = self.generator._get_file_based_variables(file_path)

            # Verify basic file information
            assert result["filename"] == "test_file.py"
            assert result["file_extension"] == "py"
            assert result["file_stem"] == "test_file"
            assert result["parent_directory"] == "src"
            assert "filepath" in result

    def test_get_file_based_variables_with_metadata(self):
        """Test file variable extraction with metadata."""
        file_path = Path("src/test_file.py")

        with patch.object(
            self.generator.metadata_extractor, "get_file_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = {
                "type": "python",
                "category": "source",
                "size": 1024,
                "is_binary": False,
            }

            result = self.generator._get_file_based_variables(file_path)

            # Verify metadata was included
            assert result["file_type"] == "python"
            assert result["file_category"] == "source"
            assert not result["is_binary"]
            assert "file_size" in result

    def test_get_file_based_variables_metadata_error(self):
        """Test file variable extraction when metadata fails."""
        file_path = Path("src/test_file.py")

        with patch.object(
            self.generator.metadata_extractor, "get_file_metadata"
        ) as mock_metadata:
            mock_metadata.side_effect = Exception("Metadata failed")

            result = self.generator._get_file_based_variables(file_path)

            # Should still have basic file info
            assert result["filename"] == "test_file.py"
            assert result["file_type"] == "unknown"
            assert result["file_category"] == "other"

    def test_get_template_defaults(self):
        """Test template default variable extraction."""
        result = self.generator._get_template_defaults(self.template)

        # Verify standard defaults
        assert result["template_description"] == "Test template"
        assert result["template_version"] == "1.0"
        assert "creation_date" in result
        assert "creation_time" in result

        # Verify date format
        assert len(result["creation_date"]) == 10  # YYYY-MM-DD format
        assert len(result["creation_time"]) == 8  # HH:MM:SS format

    def test_prepare_substitutions_integration(self):
        """Test complete substitution preparation."""
        file_path = Path("src/test_file.py")
        custom_vars = {"purpose": "testing", "author": "test user"}

        with patch.object(
            self.generator.metadata_extractor, "get_file_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = {"type": "python"}

            result = self.generator._prepare_substitutions(
                file_path, custom_vars, self.template
            )

            # Verify all variable types are included
            assert result["filename"] == "test_file.py"  # file-based
            assert result["purpose"] == "testing"  # custom
            assert result["author"] == "test user"  # custom
            assert "creation_date" in result  # template defaults

    def test_custom_variables_override(self):
        """Test that custom variables override other variables."""
        file_path = Path("src/test_file.py")
        custom_vars = {"filename": "custom_name.py"}  # Override file-based variable

        with patch.object(
            self.generator.metadata_extractor, "get_file_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = {}

            result = self.generator._prepare_substitutions(
                file_path, custom_vars, self.template
            )

            # Custom variable should override file-based
            assert result["filename"] == "custom_name.py"


class TestWriteContentFileUnit:
    """Unit tests for content file writing."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.ignore_file = Path(".specignore")
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.project_root = Path(".")
        self.mock_settings.ignore_patterns = []

        self.generator = SpecContentGenerator(self.mock_settings)

    def test_write_content_file_success(self):
        """Test successful content file writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_content.md"
            content = "# Test Content\n\nThis is test content."

            self.generator._write_content_file(file_path, content)

            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content

    def test_write_content_file_with_subdirectories(self):
        """Test writing content file with nested directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "dirs" / "test.md"
            content = "# Nested Content"

            self.generator._write_content_file(file_path, content)

            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content

    @patch("spec_cli.templates.generator.normalize_path")
    def test_write_content_file_error_handling(self, mock_normalize):
        """Test content file writing error handling."""
        # Setup mock to cause OSError
        mock_path = Mock()
        mock_path.parent = Path("/nonexistent")
        mock_path.open.side_effect = OSError("Permission denied")
        mock_normalize.return_value = mock_path

        with pytest.raises(SpecTemplateError, match="Failed to write content"):
            self.generator._write_content_file(Path("test.md"), "content")


class TestConvenienceFunctionUnit:
    """Unit tests for the convenience function."""

    @patch("spec_cli.templates.generator.SpecContentGenerator")
    def test_generate_spec_content_function(self, mock_generator_class):
        """Test the convenience function creates and uses generator."""
        # Setup mock
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        expected_result = {"index": Path("index.md"), "history": Path("history.md")}
        mock_generator.generate_spec_content.return_value = expected_result

        # Create valid template
        template = TemplateConfig(
            index="# {{filename}} template content here",
            history="# {{filename}} history template content here",
            description="Test template",
            version="1.0",
        )

        file_path = Path("test_file.py")
        custom_vars = {"purpose": "testing"}

        result = generate_spec_content(file_path, template, custom_vars)

        # Verify generator was created and called correctly
        mock_generator_class.assert_called_once()
        mock_generator.generate_spec_content.assert_called_once_with(
            file_path, template, custom_vars
        )
        assert result == expected_result


class TestGenerateSpecContentIntegration:
    """Integration tests for the main generation method."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.ignore_file = Path(".specignore")
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.project_root = Path(".")
        self.mock_settings.ignore_patterns = []

        self.generator = SpecContentGenerator(self.mock_settings)

        self.template = TemplateConfig(
            index="# {{filename}}\n\nPurpose: {{purpose}}\nType: {{file_type}}",
            history="# {{filename}} History\n\nCreated: {{creation_date}}",
            description="Test template",
            version="1.0",
        )

    def test_generate_spec_content_basic_flow(self):
        """Test basic generation flow with mocked dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spec_dir = Path(temp_dir) / "spec"
            spec_dir.mkdir()

            # Mock the directory manager methods that are called
            with (
                patch.object(
                    self.generator.directory_manager,
                    "ensure_specs_directory",
                    return_value=None,
                ),
                patch.object(
                    self.generator.directory_manager,
                    "create_spec_directory",
                    return_value=spec_dir,
                ),
                patch.object(
                    self.generator.directory_manager,
                    "check_existing_specs",
                    return_value={"index.md": False, "history.md": False},
                ),
                patch.object(
                    self.generator, "_write_content_file", return_value=None
                ) as mock_write,
            ):
                # Test generation
                file_path = Path("src/test_file.py")
                custom_vars = {"purpose": "testing"}

                result = self.generator.generate_spec_content(
                    file_path, self.template, custom_vars, backup_existing=False
                )

                # Verify structure
                assert "index" in result
                assert "history" in result
                assert result["index"].name == "index.md"
                assert result["history"].name == "history.md"

                # Verify content was written twice (index and history)
                assert mock_write.call_count == 2

    @patch("spec_cli.templates.generator.DirectoryManager")
    def test_generate_spec_content_with_substitution_error(
        self, mock_dir_manager_class
    ):
        """Test generation with substitution error."""
        mock_dir_manager = Mock()
        mock_dir_manager_class.return_value = mock_dir_manager

        with tempfile.TemporaryDirectory() as temp_dir:
            spec_dir = Path(temp_dir) / "spec"
            spec_dir.mkdir()

            mock_dir_manager.create_spec_directory.return_value = spec_dir
            mock_dir_manager.check_existing_specs.return_value = {
                "index.md": False,
                "history.md": False,
            }

            # Mock substitution to fail
            with patch.object(
                self.generator.substitution, "substitute"
            ) as mock_substitute:
                mock_substitute.side_effect = Exception("Substitution failed")

                file_path = Path("src/test_file.py")

                with pytest.raises(
                    SpecTemplateError, match="Failed to generate spec content"
                ):
                    self.generator.generate_spec_content(
                        file_path, self.template, backup_existing=False
                    )


class TestValidationMethods:
    """Unit tests for validation and preview methods."""

    def setup_method(self):
        """Setup test environment."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.ignore_file = Path(".specignore")
        self.mock_settings.specs_dir = Path(".specs")
        self.mock_settings.project_root = Path(".")
        self.mock_settings.ignore_patterns = []

        self.generator = SpecContentGenerator(self.mock_settings)

        self.template = TemplateConfig(
            index="# {{filename}} test content here",
            history="# {{filename}} history here",
            description="Test template",
            version="1.0",
        )

    def test_validate_generation_empty_templates(self):
        """Test validation with minimal template content."""
        # Create template with content that meets minimum length requirements and includes required placeholders
        minimal_template = TemplateConfig(
            index="# {{filename}} - Minimal Index Template Content Here",
            history="# {{filename}} - Minimal History Template Content Here",
            description="Minimal template for testing",
            version="1.0",
        )

        file_path = Path("src/test_file.py")

        with (
            patch.object(
                self.generator.substitution, "validate_template_syntax", return_value=[]
            ),
            patch.object(
                self.generator.substitution,
                "get_variables_in_template",
                return_value=set(),
            ),
            patch("spec_cli.templates.generator.normalize_path") as mock_normalize,
        ):
            # Mock file existence check
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_normalize.return_value = mock_path

            # Mock directory manager
            with patch.object(
                self.generator.directory_manager, "create_spec_directory"
            ) as mock_create:
                mock_create.return_value = Path("/tmp/spec")

                issues = self.generator.validate_generation(file_path, minimal_template)

                # Should have minimal issues for valid minimal template
                assert len(issues) <= 3

    @patch.object(SpecContentGenerator, "_prepare_substitutions")
    def test_preview_generation_basic(self, mock_prepare_subs):
        """Test basic preview generation."""
        mock_prepare_subs.return_value = {
            "filename": "test_file.py",
            "purpose": "testing",
        }

        with patch.object(
            self.generator.substitution, "preview_substitution"
        ) as mock_preview:
            mock_preview.return_value = {
                "variables_found": ["filename"],
                "variables_resolved": ["filename"],
                "variables_unresolved": [],
                "syntax_issues": [],
            }

            file_path = Path("src/test_file.py")
            result = self.generator.preview_generation(file_path, self.template)

            assert result["file_path"] == str(file_path)
            assert "template_variables" in result
            assert "substitution_sample" in result

    def test_get_generation_stats_basic(self):
        """Test basic generation statistics."""
        with patch.object(
            self.generator.substitution, "get_substitution_stats"
        ) as mock_stats:
            mock_stats.return_value = {
                "template_length": 100,
                "unique_variables": 3,
                "substitution_coverage": 80,
                "syntax_valid": True,
            }

            file_path = Path("src/test_file.py")
            result = self.generator.get_generation_stats(file_path, self.template)

            assert result["file_path"] == str(file_path)
            assert "index_template" in result
            assert "history_template" in result
            assert "generation_ready" in result
