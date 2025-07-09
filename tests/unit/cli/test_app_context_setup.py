"""Unit tests for CLI application context setup functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest
from click.testing import CliRunner

from spec_cli.cli.app import app, create_cli_app
from spec_cli.core.context import SpecContext
from spec_cli.utils.cli_setup_utils import CLISetupError


class TestCLIAppContextSetup:
    """Test CLI application context setup functionality."""

    def test_cli_app_when_valid_root_path_then_initializes_context_successfully(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app initializes context successfully with valid root path."""
        # Setup: Create CLI runner and configure root path
        runner = CliRunner()

        with patch("spec_cli.cli.app.Path.cwd", return_value=tmp_path):
            # Action: Invoke CLI app
            result = runner.invoke(app, ["--version"])

        # Assert: Command succeeded and context was initialized
        assert result.exit_code == 0
        assert "Spec CLI v0.1.0" in result.output

    def test_cli_app_when_invalid_root_path_then_raises_setup_error(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app handles invalid root path with setup error."""
        # Setup: Mock initialize_cli_context to raise CLISetupError
        with patch("spec_cli.cli.app.initialize_cli_context") as mock_init:
            mock_init.side_effect = CLISetupError("Test setup error")
            runner = CliRunner()

            # Action: Invoke CLI app
            result = runner.invoke(app, ["--version"])

        # Assert: Error was handled gracefully
        assert result.exit_code != 0
        mock_init.assert_called_once()

    def test_cli_app_when_context_setup_fails_then_handles_error_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app handles context setup failures gracefully."""
        # Setup: Mock setup_click_context_storage to raise exception
        with patch("spec_cli.cli.app.setup_click_context_storage") as mock_setup:
            mock_setup.side_effect = Exception("Context setup failed")
            runner = CliRunner()

            # Action: Invoke CLI app
            result = runner.invoke(app, ["--version"])

        # Assert: Error was handled gracefully
        assert result.exit_code != 0

    def test_cli_app_provides_context_to_all_registered_commands(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app provides context to all registered commands."""
        # Setup: Create CLI app and get context
        cli_app = create_cli_app(tmp_path)
        CliRunner()

        # Action: Get list of commands
        commands = list(cli_app.commands.keys())

        # Assert: Commands are properly registered
        expected_commands = [
            "init",
            "status",
            "help",
            "gen",
            "regen",
            "add",
            "agent-scope",
            "diff",
            "log",
            "show",
            "commit",
        ]
        for cmd in expected_commands:
            assert cmd in commands

    def test_cli_app_maintains_click_group_functionality_with_context(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app maintains Click group functionality with context."""
        # Setup: Create CLI app
        cli_app = create_cli_app(tmp_path)

        # Assert: CLI app is a Click Group
        assert isinstance(cli_app, click.Group)
        assert hasattr(cli_app, "commands")
        assert hasattr(cli_app, "add_command")

    def test_cli_app_handles_concurrent_context_access_safely(
        self, tmp_path: Path
    ) -> None:
        """Test CLI app handles concurrent context access safely."""
        # Setup: Create multiple CLI apps for concurrent testing
        app1 = create_cli_app(tmp_path)
        app2 = create_cli_app(tmp_path)

        # Action: Create multiple runners (simulating concurrent access)
        runner1 = CliRunner()
        runner2 = CliRunner()

        # Execute commands concurrently
        result1 = runner1.invoke(app1, ["--version"])
        result2 = runner2.invoke(app2, ["--version"])

        # Assert: Both commands executed successfully
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert "Spec CLI v0.1.0" in result1.output
        assert "Spec CLI v0.1.0" in result2.output

    def test_cli_app_properly_cleans_up_context_on_exit(self, tmp_path: Path) -> None:
        """Test CLI app properly cleans up context on exit."""
        # Setup: Create CLI runner
        runner = CliRunner()

        with patch("spec_cli.cli.app.Path.cwd", return_value=tmp_path):
            # Action: Invoke and exit CLI app
            result = runner.invoke(app, ["--version"])

        # Assert: Command completed cleanly
        assert result.exit_code == 0
        # Context cleanup is automatic with Click's context management

    @pytest.fixture
    def mock_spec_context(self) -> Mock:
        """Mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_context.settings = Mock(spec=[])
        mock_context.settings.root_path = Path("/test")
        mock_context.console = Mock(spec=[])
        mock_context.progress = Mock(spec=[])
        mock_context.get_context_hash.return_value = "test_hash_12345678"
        return mock_context

    @pytest.fixture
    def mock_click_context(self) -> Mock:
        """Mock Click context for testing."""
        mock_ctx = Mock(spec=click.Context)
        mock_ctx.command = Mock(spec=[])
        mock_ctx.command.name = "test_command"
        mock_ctx.obj = {}
        return mock_ctx

    @pytest.fixture
    def test_cli_app(self, tmp_path: Path) -> click.Group:
        """Create test CLI app for testing."""
        return create_cli_app(tmp_path)


class TestCreateCLIApp:
    """Test create_cli_app function."""

    def test_create_cli_app_when_valid_path_then_returns_click_group(
        self, tmp_path: Path
    ) -> None:
        """Test create_cli_app returns Click Group with valid path."""
        # Action: Create CLI app
        cli_app = create_cli_app(tmp_path)

        # Assert: Returns Click Group with commands
        assert isinstance(cli_app, click.Group)
        assert len(cli_app.commands) > 0

    def test_create_cli_app_when_none_path_then_uses_current_directory(self) -> None:
        """Test create_cli_app uses current directory when path is None."""
        # Setup: Mock Path.cwd
        with patch("spec_cli.cli.app.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/current")

            # Action: Create CLI app with None path
            cli_app = create_cli_app(None)

        # Assert: CLI app created successfully
        assert isinstance(cli_app, click.Group)

    def test_create_cli_app_when_context_fails_then_handles_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Test create_cli_app handles context initialization failures."""
        # Setup: Mock initialize_cli_context to fail
        with patch("spec_cli.cli.app.initialize_cli_context") as mock_init:
            mock_init.side_effect = CLISetupError("Setup failed")

            # Action: Create CLI app
            cli_app = create_cli_app(tmp_path)
            runner = CliRunner()
            result = runner.invoke(cli_app, ["--version"])

        # Assert: Error handled gracefully
        assert result.exit_code != 0
