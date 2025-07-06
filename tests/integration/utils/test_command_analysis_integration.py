"""Integration tests for command analysis functionality."""

from pathlib import Path

import pytest

from spec_cli.utils.command_analysis import (
    CommandStructureReport,
    analyze_command_structure,
)

# Test constants
EXPECTED_MIN_COMMANDS = 5
EXPECTED_MIN_SINGLETON_USAGE = 10
REAL_CLI_COMMANDS = [
    "init_command",
    "status_command",
    "add_command",
    "gen_command",
    "show_command",
]

class TestCommandAnalysisIntegration:
    """Integration tests for command analysis with real CLI structure."""

    def test_full_cli_analysis_with_real_command_structure(self, tmp_path):
        """Test complete CLI analysis flow with realistic command structure."""
        # Setup: Create realistic CLI structure with multiple commands
        cli_dir = tmp_path / "cli"
        cli_dir.mkdir()
        commands_dir = cli_dir / "commands"
        commands_dir.mkdir()

        # Create realistic init command
        init_file = commands_dir / "init.py"
        init_file.write_text("""
from pathlib import Path
import click
from ...exceptions import SpecRepositoryError
from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ..options import force_option, spec_command
from ..utils import echo_status

@spec_command()
@force_option
def init_command(debug: bool, verbose: bool, force: bool) -> None:
    try:
        repo = SpecGitRepository()
        current_dir = Path.cwd()

        if repo.is_initialized() and not force:
            echo_status("Already initialized", "warning")
            return

        repo.initialize()
        echo_status("Initialized successfully", "success")

    except SpecRepositoryError as e:
        raise click.ClickException(f"Initialization failed: {e}") from e
""")

        # Create realistic status command
        status_file = commands_dir / "status.py"
        status_file.write_text("""
import click
from ...ui.console import get_console
from ...git.repository import SpecGitRepository
from ..options import spec_command
from ..utils import echo_status, get_spec_repository

@spec_command()
@click.option("--health", is_flag=True, help="Health check")
def status_command(debug: bool, verbose: bool, health: bool) -> None:
    console = get_console()

    try:
        repo = get_spec_repository()

        if health:
            echo_status("Running health check...", "info")
            health_info = _get_repository_health(repo)
        else:
            echo_status("Checking status...", "info")
            status_info = _get_repository_status(repo)

    except Exception as e:
        raise click.ClickException(f"Status check failed: {e}") from e

def _get_repository_health(repo):
    return {"status": "healthy"}

def _get_repository_status(repo):
    return {"files": 0}
""")

        # Create add command with different patterns
        add_file = commands_dir / "add.py"
        add_file.write_text("""
import click
from ...git.repository import SpecGitRepository
from ...ui.progress_manager import get_progress_manager
from ..options import spec_command

@spec_command()
def add_command(debug: bool, verbose: bool, files: list) -> None:
    repo = SpecGitRepository()
    progress = get_progress_manager()

    for file in files:
        repo.add(file)
        progress.update(f"Added {file}")
""")

        # Create utility file with helper functions
        utils_file = cli_dir / "utils.py"
        utils_file.write_text("""
from ..git.repository import SpecGitRepository
from ..ui.console import get_console

def get_spec_repository():
    repo = SpecGitRepository()
    if not repo.is_initialized():
        raise Exception("Not initialized")
    return repo

def echo_status(message, status_type="info"):
    console = get_console()
    console.print(f"[{status_type}]{message}[/{status_type}]")
""")

        # Action: Run full command analysis on CLI directory
        result = analyze_command_structure(cli_dir)

        # Assert: Analysis correctly identifies all commands, patterns, and singleton usage
        assert isinstance(result, CommandStructureReport)

        # Verify comprehensive command detection
        assert result.file_count >= 4  # init, status, add, utils
        assert len(result.commands) >= 3  # init_command, status_command, add_command
        assert len(result.click_patterns) >= 3  # Click decorators found
        assert len(result.singleton_usage) >= 6  # Multiple singleton patterns
        assert result.analysis_errors == []  # No analysis errors

        # Verify specific command detection
        command_names = [cmd["name"] for cmd in result.commands]
        for expected_cmd in ["init_command", "status_command", "add_command"]:
            assert expected_cmd in command_names

        # Verify Click pattern detection
        click_decorators = [pattern.decorator_name for pattern in result.click_patterns]
        assert "spec_command" in click_decorators

        # Verify comprehensive singleton usage detection
        singleton_classes = [usage.singleton_class for usage in result.singleton_usage]
        usage_patterns = [usage.usage_pattern for usage in result.singleton_usage]

        # Check for expected singleton classes
        assert "SpecGitRepository" in singleton_classes
        assert "Console" in singleton_classes
        assert "ProgressManager" in singleton_classes

        # Check for expected usage patterns
        assert "direct_instantiation" in usage_patterns
        assert "factory_function" in usage_patterns

        # Verify file-specific analysis
        init_patterns = [u for u in result.singleton_usage if "init.py" in u.file_path]
        status_patterns = [
            u for u in result.singleton_usage if "status.py" in u.file_path
        ]

        assert len(init_patterns) >= 1  # SpecGitRepository() in init
        assert len(status_patterns) >= 2  # get_console(), get_spec_repository()

    def test_real_project_cli_analysis_performance(self):
        """Test analysis performance on actual project CLI directory."""
        # Setup: Use actual project CLI directory
        project_root = Path(__file__).parent.parent.parent.parent
        actual_cli_dir = project_root / "spec_cli" / "cli"

        # Skip if CLI directory doesn't exist (test isolation)
        if not actual_cli_dir.exists():
            pytest.skip("Actual CLI directory not available")

        # Action: Analyze real CLI structure
        result = analyze_command_structure(actual_cli_dir)

        # Assert: Real analysis produces comprehensive results
        assert isinstance(result, CommandStructureReport)
        assert result.file_count >= 20  # Real project has many files
        assert len(result.commands) >= EXPECTED_MIN_COMMANDS
        assert len(result.singleton_usage) >= EXPECTED_MIN_SINGLETON_USAGE

        # Verify real commands are found
        command_names = [cmd["name"] for cmd in result.commands]
        real_commands_found = [cmd for cmd in REAL_CLI_COMMANDS if cmd in command_names]
        assert len(real_commands_found) >= 3  # At least 3 real commands found

        # Verify real singleton patterns
        singleton_classes = {usage.singleton_class for usage in result.singleton_usage}
        expected_singletons = {"SpecGitRepository", "Console", "ProgressManager"}
        found_singletons = singleton_classes.intersection(expected_singletons)
        assert len(found_singletons) >= 2  # At least 2 expected singletons found

    def test_cross_slice_integration_analysis_provides_migration_data(self, tmp_path):
        """Test analysis provides data needed for cross-slice migration planning."""
        # Setup: Create CLI structure representing migration targets
        cli_dir = tmp_path / "cli"
        cli_dir.mkdir()
        commands_dir = cli_dir / "commands"
        commands_dir.mkdir()

        # Create init command (P2.3b target)
        init_file = commands_dir / "init.py"
        init_file.write_text("""
@spec_command()
def init_command(debug: bool, verbose: bool, force: bool) -> None:
    repo = SpecGitRepository()  # Target for P2.3b migration
    repo.initialize()
""")

        # Create status command (P2.3c target)
        status_file = commands_dir / "status.py"
        status_file.write_text("""
@spec_command()
def status_command(debug: bool, verbose: bool, health: bool) -> None:
    console = get_console()  # Target for P2.3c migration
    repo = get_spec_repository()  # Target for P2.3c migration
    console.print("Status check")
""")

        # Action: Analyze for migration planning
        result = analyze_command_structure(cli_dir)

        # Assert: Analysis provides migration requirements for P2.3b and P2.3c
        # P2.3b (init) requirements
        init_singletons = [
            u
            for u in result.singleton_usage
            if "init.py" in u.file_path and u.singleton_class == "SpecGitRepository"
        ]
        assert len(init_singletons) >= 1
        assert init_singletons[0].usage_pattern == "direct_instantiation"

        # P2.3c (status) requirements
        status_singletons = [
            u for u in result.singleton_usage if "status.py" in u.file_path
        ]
        status_classes = {u.singleton_class for u in status_singletons}
        assert "Console" in status_classes
        assert "SpecGitRepository" in status_classes

        # Verify migration guidance data
        factory_patterns = [
            u for u in result.singleton_usage if u.usage_pattern == "factory_function"
        ]
        direct_patterns = [
            u
            for u in result.singleton_usage
            if u.usage_pattern == "direct_instantiation"
        ]

        assert len(factory_patterns) >= 1  # get_console(), get_spec_repository()
        assert len(direct_patterns) >= 1  # SpecGitRepository()

    def test_migration_requirements_completeness_validation(self, tmp_path):
        """Test analysis provides complete requirements for dependency injection migration."""
        # Setup: Create comprehensive CLI structure
        cli_dir = tmp_path / "cli"
        cli_dir.mkdir()
        commands_dir = cli_dir / "commands"
        commands_dir.mkdir()

        # Create command with multiple dependency types
        complex_file = commands_dir / "complex_command.py"
        complex_file.write_text("""
import click
from ...git.repository import SpecGitRepository
from ...ui.console import get_console
from ...ui.progress_manager import get_progress_manager
from ...logging.debug import debug_logger

@spec_command()
@click.option("--verbose", is_flag=True)
def complex_command(debug: bool, verbose: bool) -> None:
    # Direct instantiation pattern
    repo = SpecGitRepository()

    # Factory function patterns
    console = get_console()
    progress = get_progress_manager()

    # Mixed usage
    if repo.is_initialized():
        console.print("Repository ready")
        progress.start("Processing")
""")

        # Action: Analyze comprehensive structure
        result = analyze_command_structure(cli_dir)

        # Assert: Complete migration requirements identified
        assert len(result.singleton_usage) >= 3  # repo, console, progress

        # Verify dependency injection requirements
        singleton_classes = {usage.singleton_class for usage in result.singleton_usage}
        usage_patterns = {usage.usage_pattern for usage in result.singleton_usage}

        # All dependency types identified
        expected_classes = {"SpecGitRepository", "Console", "ProgressManager"}
        assert singleton_classes.issuperset(expected_classes)

        # Both instantiation patterns identified
        expected_patterns = {"direct_instantiation", "factory_function"}
        assert usage_patterns.issuperset(expected_patterns)

        # Context provides migration guidance
        contexts = [usage.context for usage in result.singleton_usage]
        assert any("SpecGitRepository()" in ctx for ctx in contexts)
        assert any("get_console()" in ctx for ctx in contexts)
        assert any("get_progress_manager()" in ctx for ctx in contexts)

        # Line numbers for precise targeting
        line_numbers = [usage.line_number for usage in result.singleton_usage]
        assert all(line_num > 0 for line_num in line_numbers)
        assert len(set(line_numbers)) >= 3  # Different lines for different patterns
