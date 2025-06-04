import re
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.file_system.ignore_patterns import IgnorePatternMatcher


class TestIgnorePatternMatcher:
    """Test suite for IgnorePatternMatcher class."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.ignore_file = temp_dir / ".specignore"
        return settings

    def test_ignore_patterns_loads_default_patterns(self, mock_settings: Mock) -> None:
        """Test that default ignore patterns are loaded."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Should have default patterns
        assert len(matcher.default_ignore_patterns) > 0
        assert ".git" in matcher.default_ignore_patterns
        assert "__pycache__" in matcher.default_ignore_patterns
        assert "*.tmp" in matcher.default_ignore_patterns

        # Should have compiled patterns
        assert len(matcher.patterns) > 0
        assert len(matcher.raw_patterns) > 0

    def test_ignore_patterns_loads_from_specignore_file(
        self, mock_settings: Mock
    ) -> None:
        """Test loading patterns from .specignore file."""
        # Create a .specignore file
        specignore_content = """
# This is a comment
*.pyc
build/
!important.pyc
.env
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)

        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Should include both default and file patterns
        assert "*.pyc" in matcher.raw_patterns  # From file
        assert ".git" in matcher.raw_patterns  # From defaults
        assert "!important.pyc" in matcher.raw_patterns  # Negation pattern

        # Should have loaded from file
        assert matcher.loaded_from == mock_settings.ignore_file

    def test_ignore_patterns_handles_missing_specignore_file(
        self, mock_settings: Mock
    ) -> None:
        """Test handling when .specignore file doesn't exist."""
        # Ensure file doesn't exist
        if mock_settings.ignore_file.exists():
            mock_settings.ignore_file.unlink()

        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Should still work with default patterns
        assert len(matcher.patterns) > 0
        assert matcher.loaded_from is None

        # Should only have default patterns
        assert set(matcher.raw_patterns) == set(matcher.default_ignore_patterns)

    def test_ignore_patterns_handles_malformed_specignore_file(
        self, mock_settings: Mock
    ) -> None:
        """Test handling of malformed .specignore file."""
        # Create a file that can't be read properly
        mock_settings.ignore_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8

        with patch("spec_cli.file_system.ignore_patterns.debug_logger") as mock_logger:
            matcher = IgnorePatternMatcher(settings=mock_settings)

            # Should log warning but continue with defaults
            mock_logger.log.assert_called()
            warning_calls = [
                call
                for call in mock_logger.log.call_args_list
                if call[0][0] == "WARNING"
            ]
            assert len(warning_calls) > 0

        # Should still have default patterns
        assert len(matcher.patterns) > 0

    def test_gitignore_to_regex_handles_wildcards(self, mock_settings: Mock) -> None:
        """Test gitignore to regex conversion with wildcards."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test wildcard patterns
        test_cases = [
            ("*.py", True, "test.py"),
            ("*.py", False, "test.js"),
            ("test*", True, "test.py"),
            ("test*", True, "testing.py"),
            ("test?", True, "test1"),
            ("test?", False, "test12"),
        ]

        for pattern, should_match, test_path in test_cases:
            result = matcher.test_pattern(pattern, test_path)
            assert result == should_match, f"Pattern '{pattern}' vs '{test_path}'"

    def test_gitignore_to_regex_handles_directory_patterns(
        self, mock_settings: Mock
    ) -> None:
        """Test gitignore to regex conversion with directory patterns."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test directory patterns
        test_cases = [
            ("build/", True, "build/"),
            ("build/", True, "build/file.txt"),
            ("build/", False, "build.txt"),
            ("node_modules", True, "node_modules"),
            ("node_modules", True, "node_modules/package"),
            ("src/test", True, "src/test"),
            ("src/test", True, "src/test/file.py"),
        ]

        for pattern, should_match, test_path in test_cases:
            result = matcher.test_pattern(pattern, test_path)
            assert result == should_match, f"Pattern '{pattern}' vs '{test_path}'"

    def test_gitignore_to_regex_handles_negation_patterns(
        self, mock_settings: Mock
    ) -> None:
        """Test gitignore to regex conversion with negation patterns."""
        # Create patterns with negation
        specignore_content = """
*.pyc
!important.pyc
build/
!build/keep.txt
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test negation logic
        assert matcher.should_ignore(Path("test.pyc")) is True
        assert matcher.should_ignore(Path("important.pyc")) is False  # Negated
        assert matcher.should_ignore(Path("build/temp.txt")) is True
        assert matcher.should_ignore(Path("build/keep.txt")) is False  # Negated

    def test_should_ignore_matches_file_patterns(self, mock_settings: Mock) -> None:
        """Test file pattern matching."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test default patterns
        test_cases = [
            (Path(".git/config"), True),
            (Path("__pycache__/test.pyc"), True),
            (Path(".DS_Store"), True),
            (Path("test.py"), False),
            (Path("README.md"), False),
        ]

        for file_path, should_ignore in test_cases:
            result = matcher.should_ignore(file_path)
            assert (
                result == should_ignore
            ), f"Path '{file_path}' should_ignore={should_ignore}"

    def test_should_ignore_matches_directory_patterns(
        self, mock_settings: Mock
    ) -> None:
        """Test directory pattern matching."""
        specignore_content = """
build/
*.tmp
node_modules
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test directory patterns
        test_cases = [
            (Path("build"), True),
            (Path("build/file.txt"), True),
            (Path("src/build/file.txt"), True),  # Matches at any level
            (Path("node_modules"), True),
            (Path("node_modules/package/index.js"), True),
            (Path("file.tmp"), True),
            (Path("src/file.tmp"), True),
            (Path("src/code.py"), False),
        ]

        for file_path, should_ignore in test_cases:
            result = matcher.should_ignore(file_path)
            assert (
                result == should_ignore
            ), f"Path '{file_path}' should_ignore={should_ignore}"

    def test_should_ignore_respects_negation_patterns(
        self, mock_settings: Mock
    ) -> None:
        """Test that negation patterns override ignore patterns."""
        specignore_content = """
*.log
!important.log
temp/
!temp/keep/
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test negation behavior
        assert matcher.should_ignore(Path("debug.log")) is True
        assert matcher.should_ignore(Path("important.log")) is False
        assert matcher.should_ignore(Path("temp/file.txt")) is True
        assert matcher.should_ignore(Path("temp/keep/file.txt")) is False

    def test_filter_paths_removes_ignored_files(self, mock_settings: Mock) -> None:
        """Test filtering a list of paths."""
        specignore_content = """
*.pyc
build/
.env
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test path filtering
        paths = [
            Path("src/main.py"),
            Path("src/test.pyc"),
            Path("build/output.txt"),
            Path(".env"),
            Path("README.md"),
            Path("requirements.txt"),
        ]

        filtered = matcher.filter_paths(paths)

        # Should keep non-ignored files
        expected_kept = {
            Path("src/main.py"),
            Path("README.md"),
            Path("requirements.txt"),
        }

        assert set(filtered) == expected_kept

    def test_runtime_pattern_addition_works(self, mock_settings: Mock) -> None:
        """Test adding patterns at runtime."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Initially should not ignore .env files
        assert matcher.should_ignore(Path(".env")) is False

        # Add runtime pattern
        success = matcher.add_runtime_pattern("*.env")
        assert success is True

        # Now should ignore .env files
        assert matcher.should_ignore(Path(".env")) is True
        assert matcher.should_ignore(Path("production.env")) is True

        # Test invalid regex pattern by mocking re.compile to raise error
        with patch("re.compile", side_effect=re.error("Invalid pattern")):
            success = matcher.add_runtime_pattern("invalid")
            assert success is False

    def test_pattern_summary_provides_debug_info(self, mock_settings: Mock) -> None:
        """Test getting pattern summary for debugging."""
        specignore_content = """
*.pyc
!important.pyc
build/
""".strip()

        mock_settings.ignore_file.write_text(specignore_content)
        matcher = IgnorePatternMatcher(settings=mock_settings)

        summary = matcher.get_pattern_summary()

        assert "total_patterns" in summary
        assert "negation_patterns" in summary
        assert "raw_patterns" in summary
        assert "loaded_from" in summary
        assert "default_pattern_count" in summary

        # Should have at least one negation pattern
        assert summary["negation_patterns"] >= 1
        assert summary["total_patterns"] > 0
        assert len(summary["raw_patterns"]) > 0

    def test_path_normalization_handles_different_separators(
        self, mock_settings: Mock
    ) -> None:
        """Test that path separators are normalized correctly."""
        matcher = IgnorePatternMatcher(settings=mock_settings)

        # Test with different path separators
        test_cases = [
            Path("src/test.py"),
            Path("src\\test.py"),  # Windows-style
            Path("./src/test.py"),  # Relative with ./
        ]

        # All should be handled consistently
        for path in test_cases:
            result = matcher.should_ignore(path)
            assert isinstance(result, bool)

    def test_reload_patterns_updates_matcher(self, mock_settings: Mock) -> None:
        """Test reloading patterns from file."""
        # Initial patterns
        mock_settings.ignore_file.write_text("*.old")
        matcher = IgnorePatternMatcher(settings=mock_settings)

        assert matcher.should_ignore(Path("test.old")) is True
        assert matcher.should_ignore(Path("test.new")) is False

        # Update file
        mock_settings.ignore_file.write_text("*.new")
        matcher.reload_patterns()

        # Should now use new patterns (plus defaults)
        assert matcher.should_ignore(Path("test.new")) is True
        # Note: test.old might still be ignored by default patterns

    @patch("spec_cli.file_system.ignore_patterns.debug_logger")
    def test_debug_logging_tracks_operations(
        self, mock_logger: Mock, mock_settings: Mock
    ) -> None:
        """Test that operations are properly logged."""
        matcher = IgnorePatternMatcher(settings=mock_settings)
        matcher.should_ignore(Path("test.py"))

        # Should have logged operations
        mock_logger.log.assert_called()

        # Check for specific log levels
        calls = mock_logger.log.call_args_list
        debug_calls = [call for call in calls if call[0][0] == "DEBUG"]
        info_calls = [call for call in calls if call[0][0] == "INFO"]

        assert len(debug_calls) > 0
        assert len(info_calls) > 0
