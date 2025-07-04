"""Unit tests for CLI init command - Micro-Agent Implementation.

This module provides comprehensive testing of the init command functionality
including success scenarios, error handling, force reinitialization, and
edge cases.

Tests validate:
- Repository initialization workflow
- Force reinitialization behavior
- Error handling and exception scenarios
- CLI output and status messages
- Integration with Git repository operations
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.init import init_command
from spec_cli.exceptions import SpecRepositoryError
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    isolated_cli_environment,
)


class TestInitCommandMicro002:
    """Unit tests for init command - Micro-Agent Implementation."""

    def setup_method(self) -> None:
        """Setup test environment with CLI helpers."""
        self.cli_runner = create_cli_command_runner()

    @pytest.fixture
    def mock_git_repo(self) -> Mock:
        """Mock SpecGitRepository for testing."""
        with patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            yield mock_repo

    @pytest.fixture
    def mock_echo_status(self) -> Mock:
        """Mock echo_status function for testing."""
        with patch("spec_cli.cli.commands.init.echo_status") as mock_echo:
            yield mock_echo

    @pytest.fixture
    def mock_debug_logger(self) -> Mock:
        """Mock debug logger for testing."""
        with patch("spec_cli.cli.commands.init.debug_logger") as mock_logger:
            yield mock_logger

    def test_init_command_successful_initialization(
        self, mock_git_repo: Mock, mock_echo_status: Mock, mock_debug_logger: Mock
    ) -> None:
        """Test successful repository initialization."""
        # Setup mocks - first call returns False (not initialized), second returns True (initialized)
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        # Run init command
        result = self.cli_runner.run_command(init_command)

        # Verify success
        result.assert_success()

        # Verify Git repository operations - called twice (check, then verify)
        assert mock_git_repo.is_initialized.call_count == 2
        mock_git_repo.initialize.assert_called_once()

        # Verify status messages
        mock_echo_status.assert_any_call("Initializing spec repository...", "info")
        mock_echo_status.assert_any_call(
            "Spec repository initialized successfully!\n\n"
            "Created directories:\n"
            "  • .spec/     - Git repository for spec tracking\n"
            "  • .specs/    - Documentation directory\n\n"
            "Next steps:\n"
            "  • Run 'spec status' to check repository status\n"
            "  • Run 'spec gen <files>' to generate documentation",
            "success",
        )

        # Verify debug logging
        mock_debug_logger.log.assert_called()
        call_args = mock_debug_logger.log.call_args
        assert call_args[0] == ("INFO", "Repository initialized")
        assert call_args[1]["force"] is False
        assert "directory" in call_args[1]

    def test_init_command_already_initialized_no_force(
        self, mock_git_repo: Mock, mock_echo_status: Mock
    ) -> None:
        """Test init command when repository already exists without force flag."""
        # Setup mocks - repository already initialized
        mock_git_repo.is_initialized.return_value = True

        # Run init command without force
        result = self.cli_runner.run_command(init_command)

        # Verify success (no error, just warning)
        result.assert_success()

        # Verify repository not reinitialized
        mock_git_repo.initialize.assert_not_called()

        # Verify warning message
        mock_echo_status.assert_called_once_with(
            "Spec repository is already initialized. Use --force to reinitialize.",
            "warning",
        )

    def test_init_command_force_reinitialize(
        self, mock_git_repo: Mock, mock_echo_status: Mock, mock_debug_logger: Mock
    ) -> None:
        """Test force reinitialization of existing repository."""
        # Setup mocks - repository already initialized (3 calls: check, check for force message, verify after init)
        mock_git_repo.is_initialized.side_effect = [True, True, True]

        # Run init command with force flag
        result = self.cli_runner.run_command(init_command, args=["--force"])

        # Verify success
        result.assert_success()

        # Verify repository reinitialized
        mock_git_repo.initialize.assert_called_once()

        # Verify force reinitialize message
        mock_echo_status.assert_any_call(
            "Force reinitializing spec repository...", "info"
        )

        # Verify debug logging with force=True (in isolated environment)
        mock_debug_logger.log.assert_called()
        call_args = mock_debug_logger.log.call_args
        assert call_args[0] == ("INFO", "Repository initialized")
        assert call_args[1]["force"] is True
        assert "directory" in call_args[1]

    def test_init_command_initialization_fails(
        self, mock_git_repo: Mock, mock_debug_logger: Mock
    ) -> None:
        """Test init command when Git repository initialization fails."""
        # Setup mocks - initialization fails
        mock_git_repo.is_initialized.side_effect = [
            False,
            False,
        ]  # Not initialized, then still not initialized
        mock_git_repo.initialize.return_value = None

        # Run init command expecting failure
        result = self.cli_runner.run_command(init_command)

        # Verify command fails
        result.assert_failure()

        # Verify error message contains repository initialization failure
        assert "Repository initialization failed" in result.output

    def test_init_command_git_repository_error(
        self, mock_git_repo: Mock, mock_echo_status: Mock, mock_debug_logger: Mock
    ) -> None:
        """Test init command when SpecGitRepository raises an error."""
        # Setup mocks - Git repository raises error
        mock_git_repo.is_initialized.return_value = False
        mock_git_repo.initialize.side_effect = SpecRepositoryError(
            "Git initialization failed"
        )

        # Run init command expecting failure
        result = self.cli_runner.run_command(init_command)

        # Verify command fails
        result.assert_failure()

        # Verify error message contains the exception details
        assert (
            "Repository initialization failed: Git initialization failed"
            in result.output
        )

    def test_init_command_unexpected_exception(
        self, mock_git_repo, mock_debug_logger: Mock
    ) -> None:
        """Test init command with unexpected exception."""
        # Setup mocks - unexpected exception
        mock_git_repo.is_initialized.side_effect = ValueError("Unexpected error")

        # Run init command expecting failure
        result = self.cli_runner.run_command(init_command)

        # Verify command fails
        result.assert_failure()

        # Verify error logging
        mock_debug_logger.log.assert_called_with(
            "ERROR", "Initialization failed", error="Unexpected error"
        )

        # Verify error message
        assert (
            "Unexpected error during initialization: Unexpected error" in result.output
        )

    def test_init_command_with_debug_flag(
        self, mock_git_repo, mock_echo_status, mock_debug_logger: Mock
    ) -> None:
        """Test init command with debug flag enabled."""
        # Setup mocks - not initialized, then successfully initialized
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        # Run init command with debug flag
        result = self.cli_runner.run_command(init_command, args=["--debug"])

        # Verify success
        result.assert_success()

        # Verify Git repository operations
        mock_git_repo.initialize.assert_called_once()

    def test_init_command_with_verbose_flag(
        self, mock_git_repo, mock_echo_status, mock_debug_logger: Mock
    ) -> None:
        """Test init command with verbose flag enabled."""
        # Setup mocks - not initialized, then successfully initialized
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        # Run init command with verbose flag
        result = self.cli_runner.run_command(init_command, args=["--verbose"])

        # Verify success
        result.assert_success()

        # Verify Git repository operations
        mock_git_repo.initialize.assert_called_once()

    def test_init_command_combined_flags(
        self, mock_git_repo, mock_echo_status, mock_debug_logger: Mock
    ) -> None:
        """Test init command with combined debug, verbose, and force flags."""
        # Setup mocks - repository already initialized (3 calls: check, check for force message, verify after init)
        mock_git_repo.is_initialized.side_effect = [True, True, True]

        # Run init command with all flags
        result = self.cli_runner.run_command(
            init_command, args=["--debug", "--verbose", "--force"]
        )

        # Verify success
        result.assert_success()

        # Verify repository reinitialized
        mock_git_repo.initialize.assert_called_once()

        # Verify force message
        mock_echo_status.assert_any_call(
            "Force reinitializing spec repository...", "info"
        )

    def test_init_command_current_directory_tracking(
        self, mock_git_repo, mock_debug_logger: Mock
    ) -> None:
        """Test that init command tracks current directory correctly."""
        # Setup mocks - not initialized, then successfully initialized
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        # Run init command
        result = self.cli_runner.run_command(init_command)

        # Verify success
        result.assert_success()

        # Verify debug logging includes current directory (in isolated environment)
        mock_debug_logger.log.assert_called()
        call_args = mock_debug_logger.log.call_args
        assert call_args[0] == ("INFO", "Repository initialized")
        assert call_args[1]["force"] is False
        assert "directory" in call_args[1]

    def test_init_command_output_format_validation(
        self, mock_git_repo, mock_echo_status: Mock
    ) -> None:
        """Test that init command produces correctly formatted output."""
        # Setup mocks - not initialized, then successfully initialized
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        # Run init command
        result = self.cli_runner.run_command(init_command)

        # Verify success
        result.assert_success()

        # Verify success message format and content
        expected_success_message = (
            "Spec repository initialized successfully!\n\n"
            "Created directories:\n"
            "  • .spec/     - Git repository for spec tracking\n"
            "  • .specs/    - Documentation directory\n\n"
            "Next steps:\n"
            "  • Run 'spec status' to check repository status\n"
            "  • Run 'spec gen <files>' to generate documentation"
        )
        mock_echo_status.assert_any_call(expected_success_message, "success")

    def test_init_command_git_repository_instance_creation(self: Mock) -> None:
        """Test that init command creates SpecGitRepository instance correctly."""
        with patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.is_initialized.side_effect = [False, True]
            mock_repo.initialize.return_value = None
            mock_repo_class.return_value = mock_repo

            # Run init command
            result = self.cli_runner.run_command(init_command)

            # Verify success
            result.assert_success()

            # Verify SpecGitRepository was instantiated without arguments
            mock_repo_class.assert_called_once_with()

    def test_init_command_path_handling(
        self, mock_git_repo, mock_debug_logger: Mock
    ) -> None:
        """Test init command handles path operations correctly."""
        # Setup mocks - not initialized, then successfully initialized
        mock_git_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.initialize.return_value = None

        with patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/directory")

            # Run init command
            result = self.cli_runner.run_command(init_command)

            # Verify success
            result.assert_success()

            # Verify current directory was accessed
            mock_cwd.assert_called_once()

            # Verify debug logging includes correct directory
            mock_debug_logger.log.assert_called_with(
                "INFO",
                "Repository initialized",
                directory="/test/directory",
                force=False,
            )

    def test_init_command_integration_with_isolated_environment(self: Mock) -> None:
        """Test init command in isolated CLI environment."""
        with isolated_cli_environment() as env:
            runner = env["runner"]

            with patch(
                "spec_cli.cli.commands.init.SpecGitRepository"
            ) as mock_repo_class:
                mock_repo = Mock()
                mock_repo.is_initialized.side_effect = [False, True]
                mock_repo.initialize.return_value = None
                mock_repo_class.return_value = mock_repo

                # Run init command in isolated environment
                result = runner.run_command(init_command)

                # Verify success
                result.assert_success()

                # Verify repository operations - called twice (check, then verify)
                assert mock_repo.is_initialized.call_count == 2
                mock_repo.initialize.assert_called_once()

    def test_init_command_click_exception_handling(self, mock_git_repo: Mock) -> None:
        """Test that ClickException is raised for repository errors."""
        # Setup mocks - repository error
        mock_git_repo.is_initialized.return_value = False
        mock_git_repo.initialize.side_effect = SpecRepositoryError(
            "Test repository error"
        )

        # Run init command expecting ClickException
        result = self.cli_runner.run_command(init_command)

        # Verify command fails with expected exit code
        result.assert_failure()

        # Verify error message format
        assert (
            "Repository initialization failed: Test repository error" in result.output
        )

    def test_init_command_error_message_formatting(
        self, mock_git_repo, mock_debug_logger: Mock
    ) -> None:
        """Test error message formatting for different exception types."""
        test_cases = [
            (
                SpecRepositoryError("Repo error"),
                "Repository initialization failed: Repo error",
            ),
            (
                ValueError("Value error"),
                "Unexpected error during initialization: Value error",
            ),
            (
                RuntimeError("Runtime error"),
                "Unexpected error during initialization: Runtime error",
            ),
        ]

        for exception, expected_message in test_cases:
            # Reset mocks
            mock_git_repo.reset_mock()
            mock_debug_logger.reset_mock()

            # Setup mock to raise specific exception
            mock_git_repo.is_initialized.side_effect = exception

            # Run init command
            result = self.cli_runner.run_command(init_command)

            # Verify failure
            result.assert_failure()

            # Verify error message contains expected text
            assert expected_message in result.output
