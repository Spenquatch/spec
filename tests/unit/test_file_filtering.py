"""Unit tests for file filtering and type detection functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from spec_cli.__main__ import (
    IGNORE_FILE,
    get_file_type,
    load_specignore_patterns,
    should_generate_spec,
)


class TestGetFileType:
    """Test the get_file_type function."""

    def test_get_file_type_python_files(self):
        """Test file type detection for Python files."""
        assert get_file_type(Path("script.py")) == "python"
        assert get_file_type(Path("module.pyx")) == "python"
        assert get_file_type(Path("types.pyi")) == "python"

    def test_get_file_type_javascript_files(self):
        """Test file type detection for JavaScript files."""
        assert get_file_type(Path("app.js")) == "javascript"
        assert get_file_type(Path("component.jsx")) == "javascript"
        assert get_file_type(Path("types.ts")) == "javascript"
        assert get_file_type(Path("component.tsx")) == "javascript"

    def test_get_file_type_web_files(self):
        """Test file type detection for web files."""
        assert get_file_type(Path("index.html")) == "html"
        assert get_file_type(Path("page.htm")) == "html"
        assert get_file_type(Path("styles.css")) == "css"
        assert get_file_type(Path("styles.scss")) == "css"
        assert get_file_type(Path("styles.sass")) == "css"
        assert get_file_type(Path("styles.less")) == "css"

    def test_get_file_type_data_formats(self):
        """Test file type detection for data format files."""
        assert get_file_type(Path("config.json")) == "json"
        assert get_file_type(Path("config.yaml")) == "yaml"
        assert get_file_type(Path("config.yml")) == "yaml"
        assert get_file_type(Path("config.toml")) == "toml"
        assert get_file_type(Path("data.csv")) == "csv"
        assert get_file_type(Path("query.sql")) == "sql"

    def test_get_file_type_documentation(self):
        """Test file type detection for documentation files."""
        assert get_file_type(Path("README.md")) == "markdown"
        assert get_file_type(Path("docs.markdown")) == "markdown"
        assert get_file_type(Path("index.rst")) == "restructuredtext"
        assert get_file_type(Path("notes.txt")) == "text"

    def test_get_file_type_config_files(self):
        """Test file type detection for configuration files."""
        assert get_file_type(Path("app.conf")) == "config"
        assert get_file_type(Path("settings.config")) == "config"
        assert get_file_type(Path("app.cfg")) == "config"
        assert get_file_type(Path("config.ini")) == "config"
        assert get_file_type(Path(".env")) == "environment"

    def test_get_file_type_build_files(self):
        """Test file type detection for build files."""
        assert get_file_type(Path("Makefile")) == "build"
        assert get_file_type(Path("makefile")) == "build"
        assert get_file_type(Path("Dockerfile")) == "build"
        assert get_file_type(Path("Vagrantfile")) == "build"
        assert get_file_type(Path("Rakefile")) == "build"
        assert get_file_type(Path("build.mk")) == "build"
        assert get_file_type(Path("rules.make")) == "build"

    def test_get_file_type_compiled_languages(self):
        """Test file type detection for compiled languages."""
        assert get_file_type(Path("main.c")) == "c"
        assert get_file_type(Path("header.h")) == "c"
        assert get_file_type(Path("main.cpp")) == "cpp"
        assert get_file_type(Path("main.cc")) == "cpp"
        assert get_file_type(Path("header.hpp")) == "cpp"
        assert get_file_type(Path("app.java")) == "java"
        assert get_file_type(Path("Main.class")) == "java"
        assert get_file_type(Path("main.rs")) == "rust"
        assert get_file_type(Path("main.go")) == "go"

    def test_get_file_type_other_languages(self):
        """Test file type detection for other programming languages."""
        assert get_file_type(Path("script.rb")) == "ruby"
        assert get_file_type(Path("app.php")) == "php"
        assert get_file_type(Path("App.swift")) == "swift"
        assert get_file_type(Path("Main.kt")) == "kotlin"
        assert get_file_type(Path("App.scala")) == "scala"
        assert get_file_type(Path("Program.cs")) == "csharp"
        assert get_file_type(Path("Module.vb")) == "visualbasic"

    def test_get_file_type_xml_files(self):
        """Test file type detection for XML files."""
        assert get_file_type(Path("config.xml")) == "xml"
        assert get_file_type(Path("transform.xsl")) == "xml"
        assert get_file_type(Path("schema.xsd")) == "xml"

    def test_get_file_type_case_insensitive(self):
        """Test that file type detection is case insensitive."""
        assert get_file_type(Path("Script.PY")) == "python"
        assert get_file_type(Path("App.JS")) == "javascript"
        assert get_file_type(Path("Index.HTML")) == "html"

    def test_get_file_type_no_extension(self):
        """Test file type detection for files without extension."""
        assert get_file_type(Path("README")) == "no_extension"
        assert get_file_type(Path("script")) == "no_extension"

    def test_get_file_type_unknown_extension(self):
        """Test file type detection for unknown extensions."""
        assert get_file_type(Path("file.xyz")) == "unknown"
        assert get_file_type(Path("data.custom")) == "unknown"


class TestLoadSpecignorePatterns:
    """Test the load_specignore_patterns function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Ensure clean state
        if IGNORE_FILE.exists():
            self.original_content = IGNORE_FILE.read_text()
        else:
            self.original_content = None

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.original_content is not None:
            IGNORE_FILE.write_text(self.original_content)
        elif IGNORE_FILE.exists():
            IGNORE_FILE.unlink()

    def test_load_specignore_patterns_no_file_returns_defaults(self):
        """Test that default patterns are returned when no .specignore file exists."""
        if IGNORE_FILE.exists():
            IGNORE_FILE.unlink()

        patterns = load_specignore_patterns()

        # Check that default patterns are included
        assert "*.pyc" in patterns
        assert "*.log" in patterns
        assert ".git/*" in patterns
        assert "node_modules/*" in patterns
        assert ".DS_Store" in patterns
        assert len(patterns) > 20  # Should have many default patterns

    def test_load_specignore_patterns_with_file_includes_custom_and_defaults(self):
        """Test that custom patterns are loaded along with defaults."""
        custom_patterns = "*.custom\n# This is a comment\ncustom_dir/*\n\n  \n"
        IGNORE_FILE.write_text(custom_patterns)

        patterns = load_specignore_patterns()

        # Check custom patterns
        assert "*.custom" in patterns
        assert "custom_dir/*" in patterns
        # Check defaults are still included
        assert "*.pyc" in patterns
        assert ".git/*" in patterns
        # Check comment and empty lines are ignored
        assert "# This is a comment" not in patterns
        assert "" not in patterns

    def test_load_specignore_patterns_handles_empty_file(self):
        """Test that empty .specignore file still returns defaults."""
        IGNORE_FILE.write_text("")

        patterns = load_specignore_patterns()

        # Should still have default patterns
        assert "*.pyc" in patterns
        assert ".git/*" in patterns
        assert len(patterns) > 20

    def test_load_specignore_patterns_handles_comments_and_whitespace(self):
        """Test that comments and whitespace are handled correctly."""
        content = """
        # Python cache files
        *.pyc
        __pycache__/*

        # Custom patterns
        *.temp

        # Another comment

        """
        IGNORE_FILE.write_text(content)

        patterns = load_specignore_patterns()

        assert "*.pyc" in patterns
        assert "__pycache__/*" in patterns
        assert "*.temp" in patterns
        # Comments should not be included
        assert "# Python cache files" not in patterns
        assert "# Custom patterns" not in patterns

    @patch("spec_cli.__main__.DEBUG", True)
    def test_load_specignore_patterns_debug_output(self, capsys):
        """Test that debug output is produced when DEBUG is True."""
        if IGNORE_FILE.exists():
            IGNORE_FILE.unlink()

        load_specignore_patterns()

        captured = capsys.readouterr()
        assert "🔍 Debug: Loaded" in captured.out
        assert "ignore patterns" in captured.out

    @patch("spec_cli.__main__.DEBUG", False)
    def test_load_specignore_patterns_no_debug_output(self, capsys):
        """Test that no debug output is produced when DEBUG is False."""
        load_specignore_patterns()

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out

    def test_load_specignore_patterns_handles_unicode(self):
        """Test that Unicode content in .specignore is handled correctly."""
        unicode_content = "*.pyc\n# Unicode: 🚀 test\n*.temp"
        IGNORE_FILE.write_text(unicode_content, encoding="utf-8")

        patterns = load_specignore_patterns()

        assert "*.pyc" in patterns
        assert "*.temp" in patterns
        # Comment with Unicode should not be included
        assert "# Unicode: 🚀 test" not in patterns


class TestShouldGenerateSpec:
    """Test the should_generate_spec function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_should_generate_spec_accepts_python_files(self):
        """Test that Python files are accepted for spec generation."""
        patterns = {"*.pyc", ".git/*"}

        assert should_generate_spec(Path("script.py"), patterns) is True
        assert should_generate_spec(Path("src/module.py"), patterns) is True

    def test_should_generate_spec_rejects_unknown_files(self):
        """Test that unknown file types are rejected."""
        patterns = set()

        assert should_generate_spec(Path("file.xyz"), patterns) is False
        assert should_generate_spec(Path("unknown.custom"), patterns) is False

    def test_should_generate_spec_rejects_binary_files(self):
        """Test that binary files are rejected."""
        patterns = set()

        assert should_generate_spec(Path("image.jpg"), patterns) is False
        assert should_generate_spec(Path("document.pdf"), patterns) is False
        assert should_generate_spec(Path("archive.zip"), patterns) is False
        assert should_generate_spec(Path("executable.exe"), patterns) is False

    def test_should_generate_spec_matches_glob_patterns(self):
        """Test that glob patterns are matched correctly."""
        patterns = {"*.pyc", "test_*.py", "temp/*"}

        # Should be rejected by patterns
        assert should_generate_spec(Path("cache.pyc"), patterns) is False
        assert should_generate_spec(Path("test_example.py"), patterns) is False
        assert should_generate_spec(Path("temp/file.py"), patterns) is False

        # Should be accepted (not matching patterns)
        assert should_generate_spec(Path("main.py"), patterns) is True
        assert should_generate_spec(Path("example_test.py"), patterns) is True

    def test_should_generate_spec_matches_directory_patterns(self):
        """Test that directory patterns (ending with /*) are matched."""
        patterns = {".git/*", "node_modules/*", "build/*"}

        # Files in ignored directories
        assert should_generate_spec(Path(".git/config"), patterns) is False
        assert (
            should_generate_spec(Path("node_modules/package/index.js"), patterns)
            is False
        )
        assert should_generate_spec(Path("build/output/main.py"), patterns) is False

        # Files not in ignored directories
        assert should_generate_spec(Path("src/main.py"), patterns) is True
        assert should_generate_spec(Path("docs/readme.md"), patterns) is True

    def test_should_generate_spec_matches_filename_only(self):
        """Test that patterns match against filename only."""
        patterns = {"*.log", ".DS_Store"}

        assert should_generate_spec(Path("logs/app.log"), patterns) is False
        assert should_generate_spec(Path("deep/path/.DS_Store"), patterns) is False
        assert should_generate_spec(Path("src/app.py"), patterns) is True

    @patch("spec_cli.__main__.ROOT")
    def test_should_generate_spec_rejects_large_files(self, mock_root):
        """Test that very large files are rejected."""
        patterns = set()

        # Create a temporary file that we can control the size of
        test_file = self.temp_dir / "large_file.py"
        test_file.write_text("content")

        # Mock ROOT to point to our temp directory
        mock_root.__truediv__.return_value = test_file

        # Mock file size to be > 1MB
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 2_000_000  # 2MB

            assert should_generate_spec(Path("large_file.py"), patterns) is False

    @patch("spec_cli.__main__.ROOT")
    def test_should_generate_spec_accepts_normal_size_files(self, mock_root):
        """Test that normal size files are accepted."""
        patterns = set()

        test_file = self.temp_dir / "normal_file.py"
        test_file.write_text("content")

        mock_root.__truediv__.return_value = test_file

        # Mock file size to be < 1MB
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 500_000  # 500KB

            assert should_generate_spec(Path("normal_file.py"), patterns) is True

    @patch("spec_cli.__main__.DEBUG", True)
    def test_should_generate_spec_debug_output_approved(self, capsys):
        """Test debug output for approved files."""
        patterns = set()

        should_generate_spec(Path("main.py"), patterns)

        captured = capsys.readouterr()
        assert "🔍 Debug: File main.py approved for spec generation" in captured.out

    @patch("spec_cli.__main__.DEBUG", True)
    def test_should_generate_spec_debug_output_rejected(self, capsys):
        """Test debug output for rejected files."""
        patterns = {"*.py"}

        should_generate_spec(Path("test.py"), patterns)

        captured = capsys.readouterr()
        assert "🔍 Debug: File test.py matches ignore pattern" in captured.out

    @patch("spec_cli.__main__.DEBUG", False)
    def test_should_generate_spec_no_debug_output(self, capsys):
        """Test that no debug output when DEBUG is False."""
        patterns = set()

        should_generate_spec(Path("main.py"), patterns)

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out

    def test_should_generate_spec_loads_patterns_when_none_provided(self):
        """Test that patterns are loaded automatically when not provided."""
        # This test verifies the function calls load_specignore_patterns()
        with patch("spec_cli.__main__.load_specignore_patterns") as mock_load:
            mock_load.return_value = {"*.test"}

            result = should_generate_spec(Path("file.py"))

            mock_load.assert_called_once()
            assert result is True  # file.py doesn't match *.test

    def test_should_generate_spec_case_sensitivity(self):
        """Test case sensitivity in pattern matching."""
        patterns = {"*.PY", "Test_*"}

        # fnmatch is case-sensitive by default
        assert (
            should_generate_spec(Path("script.py"), patterns) is True
        )  # *.PY doesn't match script.py
        assert (
            should_generate_spec(Path("Script.PY"), patterns) is False
        )  # *.PY matches Script.PY

        # Filename patterns should be case-sensitive for fnmatch
        assert should_generate_spec(Path("Test_file.py"), patterns) is False
        assert should_generate_spec(Path("test_file.py"), patterns) is True

    def test_should_generate_spec_complex_directory_structure(self):
        """Test pattern matching with complex directory structures."""
        patterns = {"src/test/*", "*/temp/*", "build/*"}

        # Complex path matching
        assert should_generate_spec(Path("src/test/unit.py"), patterns) is False
        assert should_generate_spec(Path("app/temp/cache.py"), patterns) is False
        assert should_generate_spec(Path("build/output.py"), patterns) is False

        # Should pass
        assert should_generate_spec(Path("src/main.py"), patterns) is True
        assert should_generate_spec(Path("tests/unit.py"), patterns) is True

    def test_should_generate_spec_edge_cases(self):
        """Test edge cases for file filtering."""
        patterns = {"*"}  # Match everything pattern

        # Even with match-all pattern, unknown files should be rejected
        assert should_generate_spec(Path("file.unknown"), patterns) is False

        # Empty patterns set
        empty_patterns = set()
        assert should_generate_spec(Path("main.py"), empty_patterns) is True
        assert should_generate_spec(Path("file.unknown"), empty_patterns) is False
