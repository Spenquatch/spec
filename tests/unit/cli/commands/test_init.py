"""Tests for init command (commands/init.py)."""

from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.init import init_command
from spec_cli.exceptions import SpecRepositoryError


class TestInitCommand:
    """Test cases for init command functionality."""

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_success(self, mock_git_repo):
        """Test successful repository initialization."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = False
        mock_repo.initialize.return_value = None
        # After initialization, return True
        mock_repo.is_initialized.side_effect = [False, True]
        mock_git_repo.return_value = mock_repo
        
        runner = CliRunner()
        result = runner.invoke(init_command, [])
        
        assert result.exit_code == 0
        assert "Initializing spec repository" in result.output
        assert "initialized successfully" in result.output
        mock_repo.initialize.assert_called_once()

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_already_initialized(self, mock_git_repo):
        """Test init command when repository is already initialized."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = True
        mock_git_repo.return_value = mock_repo
        
        runner = CliRunner()
        result = runner.invoke(init_command, [])
        
        assert result.exit_code == 0
        assert "already initialized" in result.output
        mock_repo.initialize.assert_not_called()

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_force_reinitialize(self, mock_git_repo):
        """Test init command with force flag on already initialized repo."""
        mock_repo = MagicMock()
        # First call checks if initialized (True), second call after force flag (True), 
        # third call verifies initialization was successful (True)
        mock_repo.is_initialized.side_effect = [True, True, True]
        mock_repo.initialize.return_value = None
        mock_git_repo.return_value = mock_repo
        
        runner = CliRunner()
        result = runner.invoke(init_command, ["--force"])
        
        assert result.exit_code == 0
        assert "Force reinitializing" in result.output
        mock_repo.initialize.assert_called_once()

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_repository_error(self, mock_git_repo):
        """Test init command with repository error."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = False
        mock_repo.initialize.side_effect = SpecRepositoryError("Test error")
        mock_git_repo.return_value = mock_repo
        
        runner = CliRunner()
        result = runner.invoke(init_command, [])
        
        assert result.exit_code != 0
        assert "Repository initialization failed" in result.output

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_initialization_verification_fails(self, mock_git_repo):
        """Test init command when initialization verification fails."""
        mock_repo = MagicMock()
        mock_repo.is_initialized.side_effect = [False, False]  # Not initialized before or after
        mock_repo.initialize.return_value = None
        mock_git_repo.return_value = mock_repo
        
        runner = CliRunner()
        result = runner.invoke(init_command, [])
        
        assert result.exit_code != 0
        assert "Repository initialization failed" in result.output

    @patch('spec_cli.cli.commands.init.SpecGitRepository')
    def test_init_command_unexpected_error(self, mock_git_repo):
        """Test init command with unexpected error."""
        mock_git_repo.side_effect = Exception("Unexpected error")
        
        runner = CliRunner()
        result = runner.invoke(init_command, [])
        
        assert result.exit_code != 0
        assert "Unexpected error during initialization" in result.output

    def test_init_command_help(self):
        """Test init command help display."""
        runner = CliRunner()
        result = runner.invoke(init_command, ["--help"])
        
        assert result.exit_code == 0
        assert "Initialize spec repository" in result.output
        assert "--force" in result.output