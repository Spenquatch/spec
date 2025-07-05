"""Unit tests for command analysis utilities."""

import pytest

from spec_cli.utils.command_analysis import (
    CommandAnalysisError,
    CommandStructureReport,
    SingletonUsage,
    analyze_command_structure,
    identify_singleton_usage,
)

# Test constants
DEFAULT_FILE_COUNT = 2
DEFAULT_COMMAND_NAME = "test_command"
DEFAULT_SINGLETON_CLASS = "TestRepository"
SAMPLE_CLICK_COMMAND = """
import click

@click.command()
def test_command():
    pass
"""
SAMPLE_SINGLETON_USAGE = """
from spec_cli.git.repository import SpecGitRepository

def test_function():
    repo = SpecGitRepository()
    return repo
"""
SAMPLE_FACTORY_USAGE = """
from spec_cli.ui.console import get_console

def test_function():
    console = get_console()
    return console
"""


class TestCommandAnalysis:
    """Test command structure analysis functionality."""

    def test_analyze_command_structure_when_valid_cli_dir_then_returns_structure_report(
        self, tmp_path
    ):
        """Test analyzing valid CLI directory returns complete structure report."""
        # Setup: Create CLI directory with commands
        cli_dir = tmp_path / "cli"
        cli_dir.mkdir()
        commands_dir = cli_dir / "commands"
        commands_dir.mkdir()

        # Create sample command file
        cmd_file = commands_dir / "test_cmd.py"
        cmd_file.write_text(SAMPLE_CLICK_COMMAND)

        # Create file with singleton usage
        singleton_file = commands_dir / "singleton_cmd.py"
        singleton_file.write_text(SAMPLE_SINGLETON_USAGE)

        # Action: Analyze command structure
        result = analyze_command_structure(cli_dir)

        # Assert: Report contains expected structure
        assert isinstance(result, CommandStructureReport)
        assert result.file_count == DEFAULT_FILE_COUNT
        assert len(result.commands) >= 1
        assert len(result.click_patterns) >= 1
        assert len(result.singleton_usage) >= 1
        assert result.analysis_errors == []

        # Verify command detection
        command_names = [cmd["name"] for cmd in result.commands]
        assert DEFAULT_COMMAND_NAME in command_names

        # Verify Click pattern detection
        click_decorators = [pattern.decorator_name for pattern in result.click_patterns]
        assert "command" in click_decorators

        # Verify singleton detection
        singleton_classes = [usage.singleton_class for usage in result.singleton_usage]
        assert "SpecGitRepository" in singleton_classes

    def test_analyze_command_structure_when_empty_dir_then_returns_empty_report(
        self, tmp_path
    ):
        """Test analyzing empty directory returns empty report."""
        # Setup: Create empty CLI directory
        cli_dir = tmp_path / "empty_cli"
        cli_dir.mkdir()

        # Action: Analyze empty directory
        result = analyze_command_structure(cli_dir)

        # Assert: Report is empty but valid
        assert isinstance(result, CommandStructureReport)
        assert result.file_count == 0
        assert result.commands == []
        assert result.click_patterns == []
        assert result.singleton_usage == []
        assert result.analysis_errors == []

    def test_analyze_command_structure_when_invalid_dir_then_raises_analysis_error(
        self, tmp_path
    ):
        """Test analyzing non-existent directory raises CommandAnalysisError."""
        # Setup: Non-existent directory path
        invalid_dir = tmp_path / "nonexistent"

        # Action & Assert: Should raise CommandAnalysisError
        with pytest.raises(CommandAnalysisError) as exc_info:
            analyze_command_structure(invalid_dir)

        assert "does not exist" in str(exc_info.value)

    def test_identify_singleton_usage_when_command_has_singletons_then_returns_usage_list(
        self, tmp_path
    ):
        """Test identifying singleton usage returns complete usage list."""
        # Setup: Create file with singleton patterns
        cmd_file = tmp_path / "singleton_test.py"
        cmd_file.write_text(SAMPLE_SINGLETON_USAGE)

        # Action: Identify singleton usage
        result = identify_singleton_usage(cmd_file)

        # Assert: Singleton usage detected
        assert isinstance(result, list)
        assert len(result) >= 1

        usage = result[0]
        assert isinstance(usage, SingletonUsage)
        assert usage.singleton_class == "SpecGitRepository"
        assert usage.usage_pattern == "direct_instantiation"
        assert usage.file_path == str(cmd_file)
        assert usage.line_number > 0
        assert "SpecGitRepository()" in usage.context

    def test_identify_singleton_usage_when_no_singletons_then_returns_empty_list(
        self, tmp_path
    ):
        """Test file with no singleton usage returns empty list."""
        # Setup: Create file without singleton usage
        cmd_file = tmp_path / "no_singleton.py"
        cmd_file.write_text("""
def simple_function():
    return "no singletons here"
""")

        # Action: Identify singleton usage
        result = identify_singleton_usage(cmd_file)

        # Assert: No singleton usage found
        assert isinstance(result, list)
        assert len(result) == 0

    def test_identify_singleton_usage_when_invalid_file_then_raises_file_error(
        self, tmp_path
    ):
        """Test analyzing non-existent file raises CommandAnalysisError."""
        # Setup: Non-existent file path
        invalid_file = tmp_path / "nonexistent.py"

        # Action & Assert: Should raise CommandAnalysisError
        with pytest.raises(CommandAnalysisError) as exc_info:
            identify_singleton_usage(invalid_file)

        assert "does not exist" in str(exc_info.value)

    def test_analyze_click_patterns_when_valid_commands_then_identifies_decorator_usage(
        self, tmp_path
    ):
        """Test Click pattern analysis identifies decorator usage correctly."""
        # Setup: Create file with various Click decorators
        cmd_file = tmp_path / "click_patterns.py"
        cmd_file.write_text("""
import click

@click.command()
def regular_command():
    pass

@click.group()
def command_group():
    pass

@spec_command()
def custom_command():
    pass
""")

        # Action: Analyze command structure
        cli_dir = tmp_path
        result = analyze_command_structure(cli_dir)

        # Assert: All Click patterns identified
        assert len(result.click_patterns) >= 3

        pattern_types = {pattern.decorator_name for pattern in result.click_patterns}
        assert "command" in pattern_types
        assert "group" in pattern_types
        assert "spec_command" in pattern_types

        # Verify command vs group classification
        command_patterns = [p for p in result.click_patterns if p.is_command]
        group_patterns = [p for p in result.click_patterns if p.is_group]

        assert len(command_patterns) >= 2  # command and spec_command
        assert len(group_patterns) >= 1  # group


class TestCommandAnalysisHelpers:
    """Test helper functions for command analysis."""

    def test_extract_decorator_patterns_when_click_decorators_then_returns_patterns(
        self, tmp_path
    ):
        """Test decorator pattern extraction identifies Click decorators."""
        # Setup: Create file with decorator patterns
        cmd_file = tmp_path / "decorator_test.py"
        cmd_file.write_text("""
import click

@click.command()
@click.option('--verbose', is_flag=True)
def decorated_command(verbose):
    pass
""")

        # Action: Analyze command structure to get patterns
        cli_dir = tmp_path
        result = analyze_command_structure(cli_dir)

        # Assert: Click decorator patterns identified
        click_patterns = [
            p for p in result.click_patterns if p.decorator_name == "command"
        ]
        assert len(click_patterns) >= 1

        pattern = click_patterns[0]
        assert pattern.function_name == "decorated_command"
        assert pattern.is_command is True
        assert pattern.is_group is False

    def test_extract_singleton_imports_when_singleton_usage_then_returns_import_list(
        self, tmp_path
    ):
        """Test singleton import detection in files."""
        # Setup: Create file with singleton imports and usage
        cmd_file = tmp_path / "import_test.py"
        cmd_file.write_text("""
from spec_cli.git.repository import SpecGitRepository
from spec_cli.ui.console import get_console

def test_function():
    repo = SpecGitRepository()
    console = get_console()
    return repo, console
""")

        # Action: Identify singleton usage
        result = identify_singleton_usage(cmd_file)

        # Assert: Both singleton patterns identified
        assert len(result) >= 2

        singleton_classes = [usage.singleton_class for usage in result]
        usage_patterns = [usage.usage_pattern for usage in result]

        assert "SpecGitRepository" in singleton_classes
        assert "Console" in singleton_classes
        assert "direct_instantiation" in usage_patterns
        assert "factory_function" in usage_patterns

    def test_parse_command_signature_when_valid_function_then_returns_signature_info(
        self, tmp_path
    ):
        """Test command signature parsing for dependency injection requirements."""
        # Setup: Create file with command function
        cmd_file = tmp_path / "signature_test.py"
        cmd_file.write_text("""
import click

@click.command()
def complex_command(debug: bool, verbose: bool, force: bool = False):
    pass
""")

        # Action: Analyze command structure
        cli_dir = tmp_path
        result = analyze_command_structure(cli_dir)

        # Assert: Command structure detected
        commands = [cmd for cmd in result.commands if cmd["name"] == "complex_command"]
        assert len(commands) == 1

        command = commands[0]
        assert command["type"] == "command"
        assert int(command["line"]) > 0


class TestCommandAnalysisErrorHandling:
    """Test error handling in command analysis."""

    def test_command_analysis_error_when_invalid_file_encoding_then_raises_analysis_error(
        self, tmp_path
    ):
        """Test handling files with invalid encoding."""
        # Setup: Create file with invalid encoding
        bad_file = tmp_path / "bad_encoding.py"
        bad_file.write_bytes(b"\xff\xfe# Invalid UTF-8")

        # Action & Assert: Should handle encoding error gracefully
        with pytest.raises(CommandAnalysisError) as exc_info:
            identify_singleton_usage(bad_file)

        assert "Cannot decode file" in str(exc_info.value)

    def test_analyze_singleton_usage_when_permission_error_then_provides_context(
        self, tmp_path
    ):
        """Test handling permission errors during file analysis."""
        # Setup: Create file then make it unreadable
        protected_file = tmp_path / "protected.py"
        protected_file.write_text("# test file")
        protected_file.chmod(0o000)

        try:
            # Action & Assert: Should handle permission error
            with pytest.raises(CommandAnalysisError) as exc_info:
                identify_singleton_usage(protected_file)

            assert "Failed to analyze file" in str(exc_info.value)

        finally:
            # Cleanup: Restore permissions for cleanup
            protected_file.chmod(0o644)


class TestCrossPlatformSupport:
    """Test cross-platform compatibility for command analysis."""

    def test_pattern_analysis_cross_platform_path_handling(self, tmp_path):
        """Test path handling works across different platforms."""
        # Setup: Create nested directory structure
        cli_dir = tmp_path / "cli"
        nested_dir = cli_dir / "commands" / "nested"
        nested_dir.mkdir(parents=True)

        # Create file in nested directory
        cmd_file = nested_dir / "cross_platform.py"
        cmd_file.write_text(SAMPLE_CLICK_COMMAND)

        # Action: Analyze command structure
        result = analyze_command_structure(cli_dir)

        # Assert: File found and analyzed regardless of platform
        assert result.file_count >= 1
        assert len(result.commands) >= 1

        # Verify path normalization
        command_files = [cmd["file"] for cmd in result.commands]
        assert any("cross_platform.py" in file_path for file_path in command_files)


class TestIntegrationWithExistingCode:
    """Test integration with existing codebase patterns."""

    def test_pattern_analysis_performance_with_large_file(self, tmp_path):
        """Test performance analysis with larger files."""
        # Setup: Create file with many functions
        large_file = tmp_path / "large_module.py"
        large_content = """
import click
from spec_cli.git.repository import SpecGitRepository

""" + "\n".join(
            [
                f"""
@click.command()
def command_{i}():
    repo = SpecGitRepository()
    return repo
"""
                for i in range(50)
            ]
        )

        large_file.write_text(large_content)

        # Action: Analyze large file
        result = analyze_command_structure(tmp_path)

        # Assert: All patterns detected efficiently
        assert len(result.commands) >= 50
        assert len(result.singleton_usage) >= 50
        assert result.analysis_errors == []

        # Verify all singleton usage is SpecGitRepository
        singleton_classes = [usage.singleton_class for usage in result.singleton_usage]
        assert all(cls == "SpecGitRepository" for cls in singleton_classes)


# Fixtures for test data
@pytest.fixture
def mock_cli_directory(tmp_path):
    """Create mock CLI directory structure for testing."""
    cli_dir = tmp_path / "cli"
    cli_dir.mkdir()
    commands_dir = cli_dir / "commands"
    commands_dir.mkdir()

    # Create sample command file
    init_file = commands_dir / "init.py"
    init_file.write_text("""
import click
from spec_cli.git.repository import SpecGitRepository

@click.command()
def init_command():
    repo = SpecGitRepository()
    return repo.initialize()
""")

    return cli_dir


@pytest.fixture
def mock_command_file(tmp_path):
    """Create mock command file for testing."""
    cmd_file = tmp_path / "test_command.py"
    cmd_file.write_text("""
from spec_cli.config import Settings
from spec_cli.ui.console import get_console

def test_command():
    settings = Settings()
    console = get_console()
    return settings.get_value()
""")
    return cmd_file


@pytest.fixture
def sample_singleton_patterns():
    """Provide sample singleton patterns for testing."""
    return [
        SingletonUsage(
            singleton_class="SpecGitRepository",
            usage_pattern="direct_instantiation",
            file_path="/test/file.py",
            line_number=10,
            context="repo = SpecGitRepository()",
        ),
        SingletonUsage(
            singleton_class="Console",
            usage_pattern="factory_function",
            file_path="/test/file.py",
            line_number=15,
            context="console = get_console()",
        ),
    ]
