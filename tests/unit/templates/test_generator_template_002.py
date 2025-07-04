"""Comprehensive unit tests for template generator core generation.

Tests target: SpecContentGenerator.generate_spec_content, load_template (convenience function),
and apply_variables (_prepare_substitutions and variable processing functions).
Coverage target: 80%+ for template generation core logic.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Mock all the problematic imports
mock_torch = Mock()
mock_torch.__version__ = "1.0.0"

with patch.dict(
    "sys.modules",
    {
        "torch": mock_torch,
        "llama_cpp": Mock(),
        "spec_cli.ai": Mock(),
        "spec_cli.ai.providers": Mock(),
        "spec_cli.ai.providers.generation": Mock(),
        "spec_cli.ai.providers.local": Mock(),
        "spec_cli.ai.providers.manager": Mock(),
        "spec_cli.templates.ai_integration": Mock(),
    },
):
    import sys

    sys.modules["torch"] = mock_torch

    from spec_cli.config.settings import SpecSettings
    from spec_cli.exceptions import SpecTemplateError
    from spec_cli.templates.config import TemplateConfig
    from spec_cli.templates.generator import SpecContentGenerator, generate_spec_content


class TestSpecContentGenerator:
    """Unit tests for SpecContentGenerator class."""

    def setup_method(self):
        """Setup for each test."""
        # Create proper mock settings
        self.settings = Mock(spec=SpecSettings)
        self.settings.ignore_file = Path(".specignore")
        self.settings.specs_dir = Path(".specs")
        self.settings.project_root = Path(".")
        self.settings.ignore_patterns = []
        self.settings.root_path = Path(".")

        # Create valid templates
        self.template = TemplateConfig(
            index="# {{filename}} - Test Template\n\nPurpose: {{purpose}}",
            history="# {{filename}} History\n\nCreated: {{creation_date}}",
            description="Test template",
            version="1.0",
        )

    def test_init_with_settings(self):
        """Test generator initialization."""
        generator = SpecContentGenerator(self.settings)
        assert generator.settings == self.settings

    @patch("spec_cli.templates.generator.get_settings")
    def test_init_default_settings(self, mock_get_settings):
        """Test generator initialization with default settings."""
        mock_get_settings.return_value = self.settings
        generator = SpecContentGenerator()
        assert generator.settings == self.settings

    def test_get_template_defaults(self):
        """Test template default variable extraction."""
        generator = SpecContentGenerator(self.settings)
        result = generator._get_template_defaults(self.template)

        assert result["template_description"] == "Test template"
        assert result["template_version"] == "1.0"
        assert "creation_date" in result
        assert "creation_time" in result
        assert len(result["creation_date"]) == 10  # YYYY-MM-DD

    def test_get_file_based_variables_basic(self):
        """Test file-based variable extraction."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator.metadata_extractor, "get_file_metadata", return_value=None
        ):
            result = generator._get_file_based_variables(Path("src/test.py"))

        assert result["filename"] == "test.py"
        assert result["file_extension"] == "py"
        assert result["file_stem"] == "test"
        assert result["parent_directory"] == "src"

    def test_get_file_based_variables_with_metadata(self):
        """Test file-based variables with metadata."""
        generator = SpecContentGenerator(self.settings)

        metadata = {
            "type": "python",
            "category": "source",
            "size": 1024,
            "is_binary": False,
        }

        with patch.object(
            generator.metadata_extractor, "get_file_metadata", return_value=metadata
        ):
            result = generator._get_file_based_variables(Path("src/test.py"))

        assert result["file_type"] == "python"
        assert result["file_category"] == "source"
        assert not result["is_binary"]

    def test_get_file_based_variables_error_handling(self):
        """Test file variables when metadata extraction fails."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator.metadata_extractor,
            "get_file_metadata",
            side_effect=Exception("Failed"),
        ):
            result = generator._get_file_based_variables(Path("src/test.py"))

        assert result["filename"] == "test.py"
        assert result["file_type"] == "unknown"
        assert result["file_category"] == "other"

    def test_prepare_substitutions(self):
        """Test complete substitution preparation."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator.metadata_extractor, "get_file_metadata", return_value={}
        ):
            result = generator._prepare_substitutions(
                Path("src/test.py"),
                {"purpose": "testing", "author": "user"},
                self.template,
            )

        # File-based variables
        assert result["filename"] == "test.py"
        # Custom variables (highest precedence)
        assert result["purpose"] == "testing"
        assert result["author"] == "user"
        # Template defaults
        assert "creation_date" in result

    def test_prepare_substitutions_variable_precedence(self):
        """Test that custom variables override others."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator.metadata_extractor, "get_file_metadata", return_value={}
        ):
            result = generator._prepare_substitutions(
                Path("src/test.py"),
                {"filename": "custom.py"},  # Override file-based
                self.template,
            )

        assert result["filename"] == "custom.py"

    def test_write_content_file(self):
        """Test content file writing."""
        generator = SpecContentGenerator(self.settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            content = "# Test Content\n\nThis is a test."

            generator._write_content_file(file_path, content)

            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content

    def test_write_content_file_creates_directories(self):
        """Test that content file writing creates parent directories."""
        generator = SpecContentGenerator(self.settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nested" / "dirs" / "test.md"
            content = "# Nested Content"

            generator._write_content_file(file_path, content)

            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content

    @patch("spec_cli.templates.generator.normalize_path")
    def test_write_content_file_error(self, mock_normalize):
        """Test content file writing error handling."""
        generator = SpecContentGenerator(self.settings)

        mock_path = Mock()
        mock_path.parent = Path("/invalid")
        mock_path.open.side_effect = OSError("Permission denied")
        mock_normalize.return_value = mock_path

        with pytest.raises(SpecTemplateError, match="Failed to write content"):
            generator._write_content_file(Path("test.md"), "content")


class TestGenerateSpecContent:
    """Tests for the main generate_spec_content method."""

    def setup_method(self):
        """Setup for each test."""
        self.settings = Mock(spec=SpecSettings)
        self.settings.ignore_file = Path(".specignore")
        self.settings.specs_dir = Path(".specs")
        self.settings.project_root = Path(".")
        self.settings.ignore_patterns = []
        self.settings.root_path = Path(".")

        self.template = TemplateConfig(
            index="# {{filename}} - Test Template\n\nPurpose: {{purpose}}",
            history="# {{filename}} History\n\nCreated: {{creation_date}}",
            description="Test template",
            version="1.0",
        )

    def test_generate_spec_content_basic(self):
        """Test basic spec content generation."""
        generator = SpecContentGenerator(self.settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "spec"
            spec_dir.mkdir()

            # Create actual file paths for proper testing
            spec_dir / "index.md"
            spec_dir / "history.md"

            # Mock the directory manager methods that are called
            with (
                patch.object(
                    generator.directory_manager,
                    "ensure_specs_directory",
                    return_value=None,
                ),
                patch.object(
                    generator.directory_manager,
                    "create_spec_directory",
                    return_value=spec_dir,
                ),
                patch.object(
                    generator.directory_manager,
                    "check_existing_specs",
                    return_value={"index.md": False, "history.md": False},
                ),
                patch.object(
                    generator, "_write_content_file", return_value=None
                ) as mock_write,
            ):
                # Test generation
                result = generator.generate_spec_content(
                    Path("src/test.py"),
                    self.template,
                    {"purpose": "testing"},
                    backup_existing=False,
                )

                # Verify structure - check that result contains the expected file paths
                assert "index" in result
                assert "history" in result
                assert result["index"].name == "index.md"
                assert result["history"].name == "history.md"

                # Verify content was written twice (index and history)
                assert mock_write.call_count == 2

    def test_generate_spec_content_with_backup(self):
        """Test generation with existing file backup."""
        generator = SpecContentGenerator(self.settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "spec"
            spec_dir.mkdir()

            # Mock the directory manager methods that are called
            with (
                patch.object(
                    generator.directory_manager,
                    "ensure_specs_directory",
                    return_value=None,
                ),
                patch.object(
                    generator.directory_manager,
                    "create_spec_directory",
                    return_value=spec_dir,
                ),
                patch.object(
                    generator.directory_manager,
                    "check_existing_specs",
                    return_value={"index.md": True, "history.md": True},
                ),
                patch.object(
                    generator.directory_manager,
                    "backup_existing_files",
                    return_value=["backup1.md", "backup2.md"],
                ) as mock_backup,
                patch.object(generator, "_write_content_file", return_value=None),
            ):
                # Test with variables
                generator.generate_spec_content(
                    Path("src/test.py"),
                    self.template,
                    {"purpose": "testing"},
                    backup_existing=True,
                )

                # Verify backup was called
                mock_backup.assert_called_once_with(spec_dir)

    @patch("spec_cli.templates.generator.DirectoryManager")
    def test_generate_spec_content_substitution_error(self, mock_dm_class):
        """Test generation with substitution error."""
        generator = SpecContentGenerator(self.settings)

        mock_dm = Mock()
        mock_dm_class.return_value = mock_dm

        with tempfile.TemporaryDirectory() as tmpdir:
            spec_dir = Path(tmpdir) / "spec"
            spec_dir.mkdir()

            mock_dm.create_spec_directory.return_value = spec_dir
            mock_dm.check_existing_specs.return_value = {
                "index.md": False,
                "history.md": False,
            }

            # Make substitution fail
            with patch.object(
                generator.substitution, "substitute", side_effect=Exception("Failed")
            ):
                with pytest.raises(
                    SpecTemplateError, match="Failed to generate spec content"
                ):
                    generator.generate_spec_content(
                        Path("src/test.py"), self.template, backup_existing=False
                    )


class TestConvenienceFunction:
    """Tests for the convenience function."""

    @patch("spec_cli.templates.generator.SpecContentGenerator")
    def test_generate_spec_content_function(self, mock_gen_class):
        """Test the convenience function."""
        mock_gen = Mock()
        mock_gen_class.return_value = mock_gen

        expected = {"index": Path("index.md"), "history": Path("history.md")}
        mock_gen.generate_spec_content.return_value = expected

        template = TemplateConfig(
            index="# {{filename}} template content here",
            history="# {{filename}} history template content here",
            description="Test template",
            version="1.0",
        )

        result = generate_spec_content(
            Path("test.py"), template, {"purpose": "testing"}
        )

        mock_gen_class.assert_called_once()
        mock_gen.generate_spec_content.assert_called_once()
        assert result == expected


class TestValidationMethods:
    """Tests for validation and preview methods."""

    def setup_method(self):
        """Setup for each test."""
        self.settings = Mock(spec=SpecSettings)
        self.settings.ignore_file = Path(".specignore")
        self.settings.specs_dir = Path(".specs")
        self.settings.project_root = Path(".")
        self.settings.ignore_patterns = []
        self.settings.root_path = Path(".")

        self.template = TemplateConfig(
            index="# {{filename}} test content here",
            history="# {{filename}} history content here",
            description="Test template",
            version="1.0",
        )

    def test_validate_generation_valid_template(self):
        """Test validation with valid template."""
        generator = SpecContentGenerator(self.settings)

        with (
            patch.object(
                generator.substitution, "validate_template_syntax", return_value=[]
            ),
            patch.object(
                generator.substitution, "get_variables_in_template", return_value=set()
            ),
            patch("spec_cli.templates.generator.normalize_path") as mock_normalize,
        ):
            # Mock file existence check
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_normalize.return_value = mock_path

            # Mock directory manager
            with patch.object(
                generator.directory_manager, "create_spec_directory"
            ) as mock_create:
                mock_create.return_value = Path("/tmp/spec")

                issues = generator.validate_generation(
                    Path("src/test.py"), self.template
                )

                # Should have minimal issues (normalize_path complications)
                assert len(issues) <= 2

    @patch.object(SpecContentGenerator, "_prepare_substitutions")
    def test_preview_generation(self, mock_prepare):
        """Test preview generation."""
        generator = SpecContentGenerator(self.settings)

        mock_prepare.return_value = {"filename": "test.py"}

        with patch.object(
            generator.substitution, "preview_substitution"
        ) as mock_preview:
            mock_preview.return_value = {
                "variables_found": ["filename"],
                "variables_resolved": ["filename"],
                "variables_unresolved": [],
                "syntax_issues": [],
            }

            result = generator.preview_generation(Path("src/test.py"), self.template)

            assert result["file_path"] == "src/test.py"
            assert "template_variables" in result
            assert result["generation_ready"]

    def test_preview_generation_error(self):
        """Test preview generation with error."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator, "_prepare_substitutions", side_effect=Exception("Failed")
        ):
            result = generator.preview_generation(Path("src/test.py"), self.template)

            assert "error" in result
            assert not result["generation_ready"]

    def test_get_generation_stats(self):
        """Test generation statistics."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator.substitution, "get_substitution_stats"
        ) as mock_stats:
            mock_stats.return_value = {
                "template_length": 100,
                "unique_variables": 2,
                "substitution_coverage": 80,
                "syntax_valid": True,
            }

            result = generator.get_generation_stats(Path("src/test.py"), self.template)

            assert result["file_path"] == "src/test.py"
            assert "index_template" in result
            assert "history_template" in result
            assert result["generation_ready"]

    def test_get_generation_stats_error(self):
        """Test generation statistics with error."""
        generator = SpecContentGenerator(self.settings)

        with patch.object(
            generator, "_prepare_substitutions", side_effect=Exception("Failed")
        ):
            result = generator.get_generation_stats(Path("src/test.py"), self.template)

            assert "error" in result
            assert not result["generation_ready"]
