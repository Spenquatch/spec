"""Unit tests for Git operations core functionality.

Tests the low-level Git command execution with spec environment configuration,
including command validation, environment isolation, and error handling.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations
from spec_cli.utils.test_helpers.git_test_helpers import (
    create_git_command_simulator,
    create_git_environment_isolator,
)


class TestGitOperationsInitialization:
    """Test GitOperations initialization and configuration."""

    def test_initialization_with_valid_paths(self, tmp_path: Path) -> None:
        """Test GitOperations initialization with valid paths."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        assert git_ops.spec_dir == spec_dir
        assert git_ops.specs_dir == specs_dir
        assert git_ops.index_file == index_file
        assert git_ops.git_error_handler is not None

    def test_initialization_preserves_path_types(self, tmp_path: Path) -> None:
        """Test that initialization preserves the provided path types."""
        spec_dir = Path("relative/.spec")
        specs_dir = Path("relative/.specs")
        index_file = Path("relative/.spec-index")

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        # Paths should be preserved as provided (relative in this case)
        assert git_ops.spec_dir == spec_dir
        assert git_ops.specs_dir == specs_dir
        assert git_ops.index_file == index_file

    def test_initialization_with_path_objects(self, tmp_path: Path) -> None:
        """Test initialization with Path objects."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        assert isinstance(git_ops.spec_dir, Path)
        assert isinstance(git_ops.specs_dir, Path)
        assert isinstance(git_ops.index_file, Path)


class TestGitCommandExecution:
    """Test Git command execution functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.tmp_path = Path("/tmp/test")
        self.spec_dir = self.tmp_path / ".spec"
        self.specs_dir = self.tmp_path / ".specs"
        self.index_file = self.tmp_path / ".spec-index"
        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_run_git_command_success(self, mock_run: Mock, mock_validate: Mock) -> None:
        """Test successful Git command execution."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        args = ["status", "--porcelain"]
        result = self.git_ops.run_git_command(args)

        # Verify validation was called
        mock_validate.assert_called_once_with(args, self.specs_dir)

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # Check command structure
        cmd = call_args[0][0]
        assert cmd[0] == "git"
        assert "-c" in cmd
        assert "core.excludesFile=" in cmd
        assert "status" in cmd
        assert "--porcelain" in cmd

        # Check environment variables
        env = call_args[1]["env"]
        assert "GIT_DIR" in env
        assert "GIT_WORK_TREE" in env
        assert "GIT_INDEX_FILE" in env
        assert env["GIT_DIR"] == str(self.spec_dir)
        assert env["GIT_WORK_TREE"] == str(self.specs_dir)
        assert env["GIT_INDEX_FILE"] == str(self.index_file)

        # Check other parameters
        assert call_args[1]["check"] is True
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["cwd"] == str(self.specs_dir.parent)

        assert result == mock_result

    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_validation_failure(self, mock_validate: Mock) -> None:
        """Test Git command execution with validation failure."""
        mock_validate.return_value = (False, "Unsafe command detected")

        args = ["rm", "-rf", "/"]

        with pytest.raises(
            SpecGitError, match="Command validation failed: Unsafe command detected"
        ):
            self.git_ops.run_git_command(args)

    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_run_git_command_subprocess_error(
        self, mock_run: Mock, mock_validate: Mock
    ) -> None:
        """Test Git command execution with subprocess error."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "status"], "Command failed", "Error details"
        )

        args = ["status"]

        with pytest.raises(SpecGitError, match="Git command failed"):
            self.git_ops.run_git_command(args)

    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_run_git_command_file_not_found(
        self, mock_run: Mock, mock_validate: Mock
    ) -> None:
        """Test Git command execution when Git is not found."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = FileNotFoundError("git command not found")

        args = ["status"]

        with pytest.raises(SpecGitError, match="Git command not found"):
            self.git_ops.run_git_command(args)

    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_run_git_command_unexpected_error(
        self, mock_run: Mock, mock_validate: Mock
    ) -> None:
        """Test Git command execution with unexpected error."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = RuntimeError("Unexpected error")

        args = ["status"]

        with pytest.raises(
            SpecGitError, match="Unexpected error during git command execution"
        ):
            self.git_ops.run_git_command(args)

    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_run_git_command_no_capture(
        self, mock_run: Mock, mock_validate: Mock
    ) -> None:
        """Test Git command execution without output capture."""
        mock_validate.return_value = (True, None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        args = ["add", "file.txt"]
        result = self.git_ops.run_git_command(args, capture_output=False)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is False
        assert result == mock_result


class TestGitEnvironmentConfiguration:
    """Test Git environment configuration functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.tmp_path = Path("/tmp/test")
        self.spec_dir = self.tmp_path / ".spec"
        self.specs_dir = self.tmp_path / ".specs"
        self.index_file = self.tmp_path / ".spec-index"
        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    @patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/home/user"})
    def test_prepare_git_environment(self) -> None:
        """Test Git environment preparation."""
        env = self.git_ops._prepare_git_environment()

        # Check that original environment is preserved
        assert env["PATH"] == "/usr/bin"
        assert env["HOME"] == "/home/user"

        # Check that Git-specific variables are set
        assert env["GIT_DIR"] == str(self.spec_dir)
        assert env["GIT_WORK_TREE"] == str(self.specs_dir)
        assert env["GIT_INDEX_FILE"] == str(self.index_file)

    @patch.dict("os.environ", {"GIT_DIR": "/old/git/dir"})
    def test_prepare_git_environment_overrides_existing(self) -> None:
        """Test that Git environment preparation overrides existing Git variables."""
        env = self.git_ops._prepare_git_environment()

        # Check that old value is overridden
        assert env["GIT_DIR"] == str(self.spec_dir)
        assert env["GIT_DIR"] != "/old/git/dir"

    def test_prepare_git_command_basic(self) -> None:
        """Test basic Git command preparation."""
        args = ["status", "--porcelain"]
        cmd = self.git_ops._prepare_git_command(args)

        assert cmd[0] == "git"
        assert "-c" in cmd
        assert "core.excludesFile=" in cmd
        assert "-c" in cmd
        assert "core.ignoreCase=false" in cmd
        assert "status" in cmd
        assert "--porcelain" in cmd

    def test_prepare_git_command_empty_args(self) -> None:
        """Test Git command preparation with empty arguments."""
        args: list[str] = []
        cmd = self.git_ops._prepare_git_command(args)

        assert cmd[0] == "git"
        assert "-c" in cmd
        assert "core.excludesFile=" in cmd
        assert "core.ignoreCase=false" in cmd
        assert len(cmd) == 5  # git + 4 config options

    def test_prepare_git_command_complex_args(self) -> None:
        """Test Git command preparation with complex arguments."""
        args = ["add", "-f", "file with spaces.txt", "--verbose"]
        cmd = self.git_ops._prepare_git_command(args)

        assert "add" in cmd
        assert "-f" in cmd
        assert "file with spaces.txt" in cmd
        assert "--verbose" in cmd


class TestGitRepositoryInitialization:
    """Test Git repository initialization functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.tmp_path = Path("/tmp/test")
        self.spec_dir = self.tmp_path / ".spec"
        self.specs_dir = self.tmp_path / ".specs"
        self.index_file = self.tmp_path / ".spec-index"
        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    @patch("spec_cli.git.operations.subprocess.run")
    def test_initialize_repository_success(self, mock_run: Mock) -> None:
        """Test successful repository initialization."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Initialized empty Git repository"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        self.git_ops.initialize_repository()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "git"
        assert "init" in cmd
        assert "--bare" in cmd
        assert str(self.spec_dir) in cmd

    @patch("spec_cli.git.operations.subprocess.run")
    def test_initialize_repository_subprocess_error(self, mock_run: Mock) -> None:
        """Test repository initialization with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "init"], "Initialization failed", "Error details"
        )

        with pytest.raises(SpecGitError, match="Git command failed"):
            self.git_ops.initialize_repository()

    @patch("spec_cli.git.operations.subprocess.run")
    def test_initialize_repository_unexpected_error(self, mock_run: Mock) -> None:
        """Test repository initialization with unexpected error."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(
            SpecGitError, match="Unexpected error during git command execution"
        ):
            self.git_ops.initialize_repository()

    @patch("pathlib.Path.mkdir")
    @patch("spec_cli.git.operations.subprocess.run")
    def test_initialize_repository_creates_directory(
        self, mock_run: Mock, mock_mkdir: Mock
    ) -> None:
        """Test that repository initialization creates spec directory."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        self.git_ops.initialize_repository()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGitAvailabilityChecks:
    """Test Git availability checking functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.tmp_path = Path("/tmp/test")
        self.spec_dir = self.tmp_path / ".spec"
        self.specs_dir = self.tmp_path / ".specs"
        self.index_file = self.tmp_path / ".spec-index"
        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    @patch("spec_cli.git.operations.subprocess.run")
    def test_check_git_available_success(self, mock_run: Mock) -> None:
        """Test successful Git availability check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_run.return_value = mock_result

        result = self.git_ops.check_git_available()

        assert result is True
        mock_run.assert_called_once_with(
            [
                "git",
                "-c",
                "core.excludesFile=",
                "-c",
                "core.ignoreCase=false",
                "--version",
            ],
            env=mock_run.call_args[1]["env"],
            check=True,
            capture_output=True,
            text=True,
            cwd=mock_run.call_args[1]["cwd"],
        )

    @patch("spec_cli.git.operations.subprocess.run")
    def test_check_git_available_subprocess_error(self, mock_run: Mock) -> None:
        """Test Git availability check with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "--version"])

        result = self.git_ops.check_git_available()

        assert result is False

    @patch("spec_cli.git.operations.subprocess.run")
    def test_check_git_available_file_not_found(self, mock_run: Mock) -> None:
        """Test Git availability check when Git is not found."""
        mock_run.side_effect = FileNotFoundError("git command not found")

        result = self.git_ops.check_git_available()

        assert result is False

    @patch("spec_cli.git.operations.subprocess.run")
    def test_get_git_version_success(self, mock_run: Mock) -> None:
        """Test successful Git version retrieval."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1\n"
        mock_run.return_value = mock_result

        version = self.git_ops.get_git_version()

        assert version == "git version 2.34.1"
        mock_run.assert_called_once_with(
            [
                "git",
                "-c",
                "core.excludesFile=",
                "-c",
                "core.ignoreCase=false",
                "--version",
            ],
            env=mock_run.call_args[1]["env"],
            check=True,
            capture_output=True,
            text=True,
            cwd=mock_run.call_args[1]["cwd"],
        )

    @patch("spec_cli.git.operations.subprocess.run")
    def test_get_git_version_subprocess_error(self, mock_run: Mock) -> None:
        """Test Git version retrieval with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "--version"])

        version = self.git_ops.get_git_version()

        assert version is None

    @patch("spec_cli.git.operations.subprocess.run")
    def test_get_git_version_file_not_found(self, mock_run: Mock) -> None:
        """Test Git version retrieval when Git is not found."""
        mock_run.side_effect = FileNotFoundError("git command not found")

        version = self.git_ops.get_git_version()

        assert version is None


class TestGitOperationsIntegration:
    """Test Git operations integration scenarios."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.command_simulator = create_git_command_simulator()

    @patch("spec_cli.git.operations.validate_git_command")
    def test_full_workflow_simulation(
        self, mock_validate: Mock, tmp_path: Path
    ) -> None:
        """Test complete Git workflow simulation."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        # Always allow commands for this test
        mock_validate.return_value = (True, None)

        with self.command_simulator.mock_git_commands():
            # Test basic commands
            result1 = git_ops.run_git_command(["status", "--porcelain"])
            result2 = git_ops.run_git_command(["add", "test.txt"])
            result3 = git_ops.run_git_command(["commit", "-m", "Test commit"])

            # All commands should succeed
            assert result1.returncode == 0
            assert result2.returncode == 0
            assert result3.returncode == 0

        # Verify command history
        history = self.command_simulator.get_command_history()
        assert len(history) >= 3
        # Check if commands were recorded (history is list of command strings)
        history_str = str(history)
        assert "status" in history_str
        assert "add" in history_str
        assert "commit" in history_str

    @patch("spec_cli.git.operations.validate_git_command")
    def test_error_recovery_simulation(
        self, mock_validate: Mock, tmp_path: Path
    ) -> None:
        """Test error recovery scenarios."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        # Always allow commands for this test
        mock_validate.return_value = (True, None)

        with self.command_simulator.mock_git_commands():
            # Test successful command execution
            result = git_ops.run_git_command(["status", "--porcelain"])
            assert result.returncode == 0

            # Test another successful command to show recovery pattern
            result = git_ops.run_git_command(["log", "--oneline"])
            assert result.returncode == 0

        # Verify command history shows execution
        history = self.command_simulator.get_command_history()
        assert len(history) >= 2

    def test_environment_isolation(self, tmp_path: Path) -> None:
        """Test environment variable isolation."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        env_isolator = create_git_environment_isolator(spec_dir, specs_dir)

        with env_isolator.isolated_git_environment():
            # Set conflicting environment variables
            os.environ["GIT_DIR"] = "/conflicting/path"
            os.environ["GIT_WORK_TREE"] = "/conflicting/worktree"

            env = git_ops._prepare_git_environment()

            # Verify spec-specific values override conflicting ones
            assert env["GIT_DIR"] == str(spec_dir)
            assert env["GIT_WORK_TREE"] == str(specs_dir)
            assert env["GIT_INDEX_FILE"] == str(index_file)


class TestGitOperationsEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.tmp_path = Path("/tmp/test")
        self.spec_dir = self.tmp_path / ".spec"
        self.specs_dir = self.tmp_path / ".specs"
        self.index_file = self.tmp_path / ".spec-index"
        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    def test_empty_command_arguments(self) -> None:
        """Test handling of empty command arguments."""
        cmd = self.git_ops._prepare_git_command([])

        assert cmd[0] == "git"
        assert len(cmd) == 5  # git + 4 config options

    def test_command_with_special_characters(self) -> None:
        """Test command preparation with special characters."""
        args = [
            "add",
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
        ]
        cmd = self.git_ops._prepare_git_command(args)

        assert "file with spaces.txt" in cmd
        assert "file-with-dashes.txt" in cmd
        assert "file_with_underscores.txt" in cmd

    def test_very_long_command_arguments(self) -> None:
        """Test handling of very long command arguments."""
        long_filename = "a" * 255 + ".txt"
        args = ["add", long_filename]
        cmd = self.git_ops._prepare_git_command(args)

        assert long_filename in cmd

    @patch("spec_cli.git.operations.validate_git_command")
    def test_command_validation_error_details(self, mock_validate: Mock) -> None:
        """Test detailed error handling for command validation."""
        mock_validate.return_value = (False, "Dangerous operation: rm -rf detected")

        with pytest.raises(SpecGitError) as exc_info:
            self.git_ops.run_git_command(["rm", "-rf", "/"])

        assert "Command validation failed" in str(exc_info.value)
        assert "Dangerous operation: rm -rf detected" in str(exc_info.value)
