import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations


class TestGitOperations:
    """Tests for GitOperations class."""

    @pytest.fixture
    def git_ops(self, tmp_path: Path) -> GitOperations:
        """Create GitOperations instance for testing."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        return GitOperations(spec_dir, specs_dir, index_file)

    def test_git_operations_initialization(
        self, git_ops: GitOperations, tmp_path: Path
    ) -> None:
        """Test GitOperations initializes with correct paths."""
        assert git_ops.spec_dir == tmp_path / ".spec"
        assert git_ops.specs_dir == tmp_path / ".specs"
        assert git_ops.index_file == tmp_path / ".spec-index"

    def test_git_operations_prepares_environment_correctly(
        self, git_ops: GitOperations
    ) -> None:
        """Test that Git environment variables are prepared correctly."""
        env = git_ops._prepare_git_environment()

        # Check that all required Git environment variables are set
        assert "GIT_DIR" in env
        assert "GIT_WORK_TREE" in env
        assert "GIT_INDEX_FILE" in env

        # Check values
        assert env["GIT_DIR"] == str(git_ops.spec_dir)
        assert env["GIT_WORK_TREE"] == str(git_ops.specs_dir)
        assert env["GIT_INDEX_FILE"] == str(git_ops.index_file)

        # Check that original environment is preserved
        assert env["PATH"] == os.environ["PATH"]

    def test_git_operations_prepares_command_correctly(
        self, git_ops: GitOperations
    ) -> None:
        """Test that Git commands are prepared with correct flags."""
        args = ["status"]
        cmd = git_ops._prepare_git_command(args)

        expected = [
            "git",
            "-c",
            "core.excludesFile=",
            "-c",
            "core.ignoreCase=false",
            "status",
        ]

        assert cmd == expected

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_executes_commands_successfully(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test successful Git command execution."""
        # Setup mock
        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Execute command
        result = git_ops.run_git_command(["status"])

        # Verify subprocess.run was called correctly
        assert mock_run.called
        call_args = mock_run.call_args

        # Check command structure
        cmd = call_args[0][0]
        assert cmd[0] == "git"
        assert "status" in cmd

        # Check environment
        env = call_args[1]["env"]
        assert env["GIT_DIR"] == str(git_ops.spec_dir)
        assert env["GIT_WORK_TREE"] == str(git_ops.specs_dir)

        # Check other parameters
        assert call_args[1]["check"] is True
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True

        assert result == mock_process

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_handles_command_failures(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test handling of Git command failures."""
        # Setup mock to raise CalledProcessError
        error = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "status"], stderr="fatal: not a git repository"
        )
        mock_run.side_effect = error

        # Verify exception is raised
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["status"])

        assert "Git command failed" in str(exc_info.value)
        assert "fatal: not a git repository" in str(exc_info.value)

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_handles_missing_git_binary(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test handling when Git binary is not found."""
        # Setup mock to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("Git not found")

        # Verify exception is raised
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["status"])

        assert "Git command not found" in str(exc_info.value)
        assert "Please ensure Git is installed and in PATH" in str(exc_info.value)

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_initializes_repository(
        self, mock_run: Mock, git_ops: GitOperations, tmp_path: Path
    ) -> None:
        """Test repository initialization."""
        # Setup mock
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Initialized empty Git repository"
        mock_run.return_value = mock_process

        # Initialize repository
        git_ops.initialize_repository()

        # Verify subprocess.run was called
        assert mock_run.called
        call_args = mock_run.call_args

        # Check command
        cmd = call_args[0][0]
        assert cmd[0] == "git"
        assert cmd[1] == "init"
        assert cmd[2] == "--bare"
        assert cmd[3] == str(git_ops.spec_dir)

        # Check that spec directory was created
        assert git_ops.spec_dir.exists()

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_handles_initialization_failure(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test handling of repository initialization failure."""
        # Setup mock to raise CalledProcessError
        error = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "init", "--bare"], stderr="Permission denied"
        )
        mock_run.side_effect = error

        # Verify exception is raised
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.initialize_repository()

        assert "Failed to initialize Git repository" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_checks_git_availability(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test Git availability check."""
        # Test when Git is available
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "git version 2.34.1"
        mock_run.return_value = mock_process

        assert git_ops.check_git_available() is True

        # Verify correct command was called
        call_args = mock_run.call_args
        assert call_args[0][0] == ["git", "--version"]

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_handles_git_unavailable(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test Git availability check when Git is not available."""
        # Test when Git is not available
        mock_run.side_effect = FileNotFoundError("Git not found")

        assert git_ops.check_git_available() is False

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_gets_git_version(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test getting Git version."""
        # Test successful version retrieval
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "git version 2.34.1\n"
        mock_run.return_value = mock_process

        version = git_ops.get_git_version()
        assert version == "git version 2.34.1"

        # Verify correct command was called
        call_args = mock_run.call_args
        assert call_args[0][0] == ["git", "--version"]

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_handles_version_failure(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test handling when Git version cannot be obtained."""
        mock_run.side_effect = FileNotFoundError("Git not found")

        version = git_ops.get_git_version()
        assert version is None

    @patch("spec_cli.git.operations.debug_logger")
    def test_git_operations_logs_command_execution(
        self, mock_logger: Mock, git_ops: GitOperations
    ) -> None:
        """Test that Git command execution is properly logged."""
        with patch("spec_cli.git.operations.subprocess.run") as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            git_ops.run_git_command(["status"])

            # Verify logging calls
            assert mock_logger.log.called

            # Check that INFO level logging occurred
            log_calls = mock_logger.log.call_args_list
            info_calls = [call for call in log_calls if call[0][0] == "INFO"]
            assert len(info_calls) >= 2  # At least execution start and completion

    @patch("spec_cli.git.operations.subprocess.run")
    def test_git_operations_working_directory_setting(
        self, mock_run: Mock, git_ops: GitOperations
    ) -> None:
        """Test that Git commands run from correct working directory."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        git_ops.run_git_command(["status"])

        # Verify working directory is set to parent of specs directory
        call_args = mock_run.call_args
        expected_cwd = str(git_ops.specs_dir.parent)
        assert call_args[1]["cwd"] == expected_cwd
