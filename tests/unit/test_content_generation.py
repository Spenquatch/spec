"""Unit tests for content generation functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.__main__ import (
    TemplateConfig,
    _substitute_template,
    generate_spec_content,
)


class TestSubstituteTemplate:
    """Test the _substitute_template helper function."""

    def test_substitute_template_single_placeholder(self):
        """Test template substitution with single placeholder."""
        template = "Hello {{name}}!"
        substitutions = {"name": "World"}

        result = _substitute_template(template, substitutions)

        assert result == "Hello World!"

    def test_substitute_template_multiple_placeholders(self):
        """Test template substitution with multiple placeholders."""
        template = "File: {{filename}} at {{filepath}}"
        substitutions = {"filename": "test.py", "filepath": "src/test.py"}

        result = _substitute_template(template, substitutions)

        assert result == "File: test.py at src/test.py"

    def test_substitute_template_repeated_placeholder(self):
        """Test template substitution with repeated placeholders."""
        template = "{{name}} says hello to {{name}}"
        substitutions = {"name": "Alice"}

        result = _substitute_template(template, substitutions)

        assert result == "Alice says hello to Alice"

    def test_substitute_template_no_placeholders(self):
        """Test template substitution with no placeholders."""
        template = "This is a plain template"
        substitutions = {"unused": "value"}

        result = _substitute_template(template, substitutions)

        assert result == "This is a plain template"

    def test_substitute_template_unused_substitutions(self):
        """Test template substitution with unused substitutions."""
        template = "Hello {{name}}!"
        substitutions = {"name": "World", "unused": "value", "extra": "data"}

        result = _substitute_template(template, substitutions)

        assert result == "Hello World!"

    def test_substitute_template_missing_substitutions(self):
        """Test template substitution with missing substitutions leaves placeholders."""
        template = "Hello {{name}}! Welcome to {{place}}!"
        substitutions = {"name": "World"}

        result = _substitute_template(template, substitutions)

        assert result == "Hello World! Welcome to {{place}}!"

    def test_substitute_template_empty_template(self):
        """Test template substitution with empty template."""
        template = ""
        substitutions = {"name": "World"}

        result = _substitute_template(template, substitutions)

        assert result == ""

    def test_substitute_template_empty_substitutions(self):
        """Test template substitution with empty substitutions."""
        template = "Hello {{name}}!"
        substitutions = {}

        result = _substitute_template(template, substitutions)

        assert result == "Hello {{name}}!"

    def test_substitute_template_special_characters(self):
        """Test template substitution with special characters in values."""
        template = "File: {{filename}}"
        substitutions = {"filename": "test & file.py"}

        result = _substitute_template(template, substitutions)

        assert result == "File: test & file.py"

    def test_substitute_template_multiline(self):
        """Test template substitution with multiline template and values."""
        template = """# {{title}}

Content for {{title}} goes here.
Created on {{date}}.
        """
        substitutions = {"title": "My Document", "date": "2023-12-01"}

        result = _substitute_template(template, substitutions)

        expected = """# My Document

Content for My Document goes here.
Created on 2023-12-01.
        """
        assert result == expected


class TestGenerateSpecContent:
    """Test the generate_spec_content function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_path = Path("src/test.py")
        self.spec_dir = self.temp_dir / "specs" / "src" / "test"
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_generate_spec_content_creates_both_files(self):
        """Test that generate_spec_content creates both index.md and history.md."""
        template = TemplateConfig(
            index="# {{filename}}\nLocation: {{filepath}}",
            history="# History for {{filename}}\nDate: {{date}}",
        )

        generate_spec_content(self.file_path, self.spec_dir, template)

        # Check that both files exist
        assert (self.spec_dir / "index.md").exists()
        assert (self.spec_dir / "history.md").exists()

    def test_generate_spec_content_index_content(self):
        """Test that generate_spec_content creates correct index.md content."""
        template = TemplateConfig(
            index="# {{filename}}\nLocation: {{filepath}}\nExtension: {{file_extension}}"
        )

        generate_spec_content(self.file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")
        assert "# test.py" in index_content
        assert "Location: src/test.py" in index_content
        assert "Extension: py" in index_content

    def test_generate_spec_content_history_content(self):
        """Test that generate_spec_content creates correct history.md content."""
        template = TemplateConfig(
            history="# History for {{filename}}\nCreated: {{date}}"
        )

        with patch("spec_cli.__main__.datetime") as mock_datetime:
            mock_now = datetime(2023, 12, 1, 10, 30, 0)
            mock_datetime.now.return_value = mock_now

            generate_spec_content(self.file_path, self.spec_dir, template)

        history_content = (self.spec_dir / "history.md").read_text(encoding="utf-8")
        assert "# History for test.py" in history_content
        assert "Created: 2023-12-01" in history_content

    def test_generate_spec_content_all_substitutions(self):
        """Test that all expected substitutions are made."""
        template = TemplateConfig(
            index="""
{{filename}} - {{filepath}} - {{file_extension}} - {{date}}
{{purpose}} - {{responsibilities}} - {{requirements}}
{{example_usage}} - {{notes}}
            """.strip()
        )

        with patch("spec_cli.__main__.datetime") as mock_datetime:
            mock_now = datetime(2023, 12, 1, 10, 30, 0)
            mock_datetime.now.return_value = mock_now

            generate_spec_content(self.file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")

        # Check that all substitutions were made (no {{}} left)
        assert "{{" not in index_content
        assert "}}" not in index_content

        # Check specific values
        assert "test.py" in index_content
        assert "src/test.py" in index_content
        assert "py" in index_content
        assert "2023-12-01" in index_content
        assert "[Generated by spec-cli - to be filled]" in index_content

    def test_generate_spec_content_file_without_extension(self):
        """Test generate_spec_content with file that has no extension."""
        file_path = Path("README")
        template = TemplateConfig(index="Extension: {{file_extension}}")

        generate_spec_content(file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")
        assert "Extension: txt" in index_content

    def test_generate_spec_content_nested_file_path(self):
        """Test generate_spec_content with deeply nested file path."""
        file_path = Path("src/deeply/nested/path/file.js")
        template = TemplateConfig(
            index="File: {{filename}}\nPath: {{filepath}}\nExt: {{file_extension}}"
        )

        generate_spec_content(file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")
        assert "File: file.js" in index_content
        assert "Path: src/deeply/nested/path/file.js" in index_content
        assert "Ext: js" in index_content

    @patch("spec_cli.__main__.DEBUG", True)
    def test_generate_spec_content_debug_output(self, capsys):
        """Test that generate_spec_content produces debug output when DEBUG is True."""
        template = TemplateConfig(
            index="Short content", history="Another short content"
        )

        generate_spec_content(self.file_path, self.spec_dir, template)

        captured = capsys.readouterr()
        assert "🔍 Debug: Generated index.md" in captured.out
        assert "🔍 Debug: Generated history.md" in captured.out
        assert "chars)" in captured.out

    @patch("spec_cli.__main__.DEBUG", False)
    def test_generate_spec_content_no_debug_output(self, capsys):
        """Test that generate_spec_content produces no debug output when DEBUG is False."""
        template = TemplateConfig(index="Content", history="History")

        generate_spec_content(self.file_path, self.spec_dir, template)

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out

    def test_generate_spec_content_unicode_content(self):
        """Test generate_spec_content with Unicode content."""
        template = TemplateConfig(
            index="Unicode: 🚀 {{filename}} 📝", history="History: ⭐ {{filename}} 📚"
        )

        generate_spec_content(self.file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")
        history_content = (self.spec_dir / "history.md").read_text(encoding="utf-8")

        assert "🚀 test.py 📝" in index_content
        assert "⭐ test.py 📚" in history_content

    def test_generate_spec_content_permission_error(self):
        """Test generate_spec_content raises OSError when file writing fails."""
        # Create read-only directory
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        template = TemplateConfig()

        try:
            with pytest.raises(OSError, match="Failed to write spec files"):
                generate_spec_content(self.file_path, readonly_dir, template)
        finally:
            # Clean up - restore write permissions
            readonly_dir.chmod(0o755)

    def test_generate_spec_content_preserves_multiline_templates(self):
        """Test that multiline templates are preserved correctly."""
        multiline_template = """# {{filename}}

This is a multiline template
with proper formatting
and indentation.

**Location**: {{filepath}}
        """

        template = TemplateConfig(index=multiline_template)

        generate_spec_content(self.file_path, self.spec_dir, template)

        index_content = (self.spec_dir / "index.md").read_text(encoding="utf-8")

        # Check that multiline structure is preserved
        lines = index_content.split("\n")
        assert lines[0] == "# test.py"
        assert lines[1] == ""
        assert "This is a multiline template" in index_content
        assert "**Location**: src/test.py" in index_content
