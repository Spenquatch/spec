"""Unit tests for GitOperations - Repository Management (git_001).

Comprehensive unit tests for GitOperations class covering repository
initialization, command execution, environment configuration, and error handling.
"""

import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations


class TestGitOperationsInit:
    """Test GitOperations initialization and configuration."""

    def test_init_when_valid_paths_then_initializes_correctly(
        self, tmp_path: Path
    ) -> None:
        """Test GitOperations initialization with valid paths."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        assert git_ops.spec_dir == spec_dir
        assert git_ops.specs_dir == specs_dir
        assert git_ops.index_file == index_file
        assert git_ops.git_error_handler is not None

    def test_init_when_paths_are_strings_then_stores_as_provided(
        self, tmp_path: Path
    ) -> None:
        """Test GitOperations initialization with string paths."""
        spec_dir = str(tmp_path / ".spec")
        specs_dir = str(tmp_path / ".specs")
        index_file = str(tmp_path / ".spec-index")

        git_ops = GitOperations(Path(spec_dir), Path(specs_dir), Path(index_file))

        assert isinstance(git_ops.spec_dir, Path)
        assert isinstance(git_ops.specs_dir, Path)
        assert isinstance(git_ops.index_file, Path)

    @patch("spec_cli.git.operations.debug_logger")
    def test_init_when_created_then_logs_initialization(
        self, mock_logger: Any, tmp_path: Path
    ) -> None:
        """Test that initialization is logged properly."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        GitOperations(spec_dir, specs_dir, index_file)

        mock_logger.log.assert_called_with(
            "INFO",
            "GitOperations initialized",
            spec_dir=str(spec_dir),
            specs_dir=str(specs_dir),
            index_file=str(index_file),
        )


class TestGitOperationsEnvironment:
    """Test Git environment preparation."""

    def test_prepare_git_environment_when_called_then_sets_git_variables(
        self, tmp_path: Path
    ) -> None:
        """Test Git environment variable preparation."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        env = git_ops._prepare_git_environment()

        assert env["GIT_DIR"] == str(spec_dir)
        assert env["GIT_WORK_TREE"] == str(specs_dir)
        assert env["GIT_INDEX_FILE"] == str(index_file)

    def test_prepare_git_environment_when_called_then_preserves_existing_env(
        self, tmp_path: Path
    ) -> None:
        """Test that existing environment variables are preserved."""
        original_path = os.environ.get("PATH", "")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        env = git_ops._prepare_git_environment()

        assert env["PATH"] == original_path

    @patch("spec_cli.git.operations.debug_logger")
    def test_prepare_git_environment_when_called_then_logs_debug_info(
        self, mock_logger: Any, tmp_path: Path
    ) -> None:
        """Test that environment preparation is logged."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        git_ops._prepare_git_environment()

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Git environment prepared",
            GIT_DIR=str(spec_dir),
            GIT_WORK_TREE=str(specs_dir),
            GIT_INDEX_FILE=str(index_file),
        )


class TestGitOperationsCommandPreparation:
    """Test Git command preparation."""

    def test_prepare_git_command_when_simple_args_then_adds_config_flags(
        self, tmp_path: Path
    ) -> None:
        """Test that git command is prepared with configuration flags."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        cmd = git_ops._prepare_git_command(["status"])

        expected = [
            "git",
            "-c",
            "core.excludesFile=",
            "-c",
            "core.ignoreCase=false",
            "status",
        ]
        assert cmd == expected

    def test_prepare_git_command_when_multiple_args_then_preserves_order(
        self, tmp_path: Path
    ) -> None:
        """Test that multiple command arguments are preserved in order."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        cmd = git_ops._prepare_git_command(["add", "-f", "file.txt"])

        assert cmd[-3:] == ["add", "-f", "file.txt"]

    @patch("spec_cli.git.operations.debug_logger")
    def test_prepare_git_command_when_called_then_logs_debug_info(
        self, mock_logger: Any, tmp_path: Path
    ) -> None:
        """Test that command preparation is logged."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        git_ops._prepare_git_command(["status"])

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Git command prepared",
            original_args=["status"],
            full_command=[
                "git",
                "-c",
                "core.excludesFile=",
                "-c",
                "core.ignoreCase=false",
                "status",
            ],
        )


class TestGitOperationsCommandExecution:
    """Test Git command execution."""

    @patch("subprocess.run")
    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_when_valid_command_then_executes_successfully(
        self, mock_validate: Any, mock_run: Any, tmp_path: Path
    ) -> None:
        """Test successful Git command execution."""
        mock_validate.return_value = (True, None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        result = git_ops.run_git_command(["status"])

        assert result == mock_result
        mock_validate.assert_called_once_with(["status"], specs_dir)
        mock_run.assert_called_once()

    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_when_validation_fails_then_raises_spec_git_error(
        self, mock_validate: Any, tmp_path: Path
    ) -> None:
        """Test that command validation failure raises SpecGitError."""
        mock_validate.return_value = (
            False,
            "Git command 'dangerous-command' not allowed",
        )

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(SpecGitError, match="Command validation failed"):
            git_ops.run_git_command(["dangerous-command"])

    @patch("subprocess.run")
    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_when_subprocess_error_then_raises_spec_git_error(
        self, mock_validate: Any, mock_run: Any, tmp_path
    ) -> None:
        """Test that subprocess.CalledProcessError is converted to SpecGitError."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "status"], "error"
        )

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(SpecGitError, match="Git command failed"):
            git_ops.run_git_command(["status"])

    @patch("subprocess.run")
    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_when_git_not_found_then_raises_spec_git_error(
        self, mock_validate: Any, mock_run: Any, tmp_path
    ) -> None:
        """Test that FileNotFoundError is converted to SpecGitError."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = FileNotFoundError("git not found")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(SpecGitError, match="Git command not found"):
            git_ops.run_git_command(["status"])

    @patch("subprocess.run")
    @patch("spec_cli.git.operations.validate_git_command")
    def test_run_git_command_when_unexpected_error_then_raises_spec_git_error(
        self, mock_validate: Any, mock_run: Any, tmp_path
    ) -> None:
        """Test that unexpected errors are converted to SpecGitError."""
        mock_validate.return_value = (True, None)
        mock_run.side_effect = RuntimeError("Unexpected error")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(
            SpecGitError, match="Unexpected error during git command execution"
        ):
            git_ops.run_git_command(["status"])

    @patch("subprocess.run")
    @patch("spec_cli.git.operations.validate_git_command")
    @patch("spec_cli.git.operations.debug_logger")
    def test_run_git_command_when_successful_then_logs_execution_info(
        self, mock_logger: Any, mock_validate: Any, mock_run: Any, tmp_path
    ) -> None:
        """Test that successful command execution is logged."""
        mock_validate.return_value = (True, None)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        git_ops.run_git_command(["status"])

        # Verify execution logging
        mock_logger.log.assert_any_call(
            "INFO",
            "Executing Git command",
            command="git -c core.excludesFile= -c core.ignoreCase=false status",
            git_dir=str(spec_dir),
            work_tree=str(specs_dir),
        )

        # Verify completion logging
        mock_logger.log.assert_any_call(
            "INFO",
            "Git command completed successfully",
            command="status",
            return_code=0,
        )


class TestGitOperationsRepositoryInit:
    """Test repository initialization functionality."""

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_initialize_repository_when_called_then_creates_bare_repo(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test repository initialization creates bare repository."""
        mock_result = Mock()
        mock_result.stdout = "Initialized empty Git repository"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        git_ops.initialize_repository()

        # Verify directory was created
        assert spec_dir.exists()

        # Verify correct git command was called
        mock_run_git.assert_called_once_with(["init", "--bare", str(spec_dir)])

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_initialize_repository_when_git_error_then_reraises_spec_git_error(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test that SpecGitError from run_git_command is re-raised."""
        mock_run_git.side_effect = SpecGitError("Git init failed")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(SpecGitError, match="Git init failed"):
            git_ops.initialize_repository()

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_initialize_repository_when_unexpected_error_then_raises_spec_git_error(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test that unexpected errors are converted to SpecGitError."""
        mock_run_git.side_effect = RuntimeError("Unexpected error")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        with pytest.raises(
            SpecGitError, match="Unexpected error initializing repository"
        ):
            git_ops.initialize_repository()

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    @patch("spec_cli.git.operations.debug_logger")
    def test_initialize_repository_when_successful_then_logs_info(
        self, mock_logger: Any, mock_run_git: Any, tmp_path
    ) -> None:
        """Test that successful repository initialization is logged."""
        mock_result = Mock()
        mock_result.stdout = "Initialized empty Git repository"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        git_ops.initialize_repository()

        mock_logger.log.assert_any_call("INFO", "Initializing bare Git repository")
        mock_logger.log.assert_any_call(
            "INFO",
            "Bare Git repository initialized",
            spec_dir=str(spec_dir),
            stdout="Initialized empty Git repository",
        )


class TestGitOperationsUtilityMethods:
    """Test utility methods for Git operations."""

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_check_git_available_when_git_works_then_returns_true(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test check_git_available returns True when Git is available."""
        mock_result = Mock()
        mock_result.stdout = "git version 2.34.1"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        result = git_ops.check_git_available()

        assert result is True
        mock_run_git.assert_called_once_with(["--version"])

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_check_git_available_when_git_fails_then_returns_false(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test check_git_available returns False when Git is not available."""
        mock_run_git.side_effect = SpecGitError("Git not found")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        result = git_ops.check_git_available()

        assert result is False

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_get_git_version_when_git_works_then_returns_version(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test get_git_version returns version string when Git is available."""
        mock_result = Mock()
        mock_result.stdout = "git version 2.34.1\n"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        version = git_ops.get_git_version()

        assert version == "git version 2.34.1"
        mock_run_git.assert_called_once_with(["--version"])

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_get_git_version_when_git_fails_then_returns_none(
        self, mock_run_git: Any, tmp_path
    ) -> None:
        """Test get_git_version returns None when Git is not available."""
        mock_run_git.side_effect = SpecGitError("Git not found")

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        version = git_ops.get_git_version()

        assert version is None

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    @patch("spec_cli.git.operations.debug_logger")
    def test_utility_methods_when_called_then_log_appropriately(
        self, mock_logger: Any, mock_run_git: Any, tmp_path
    ) -> None:
        """Test that utility methods log debug information appropriately."""
        mock_result = Mock()
        mock_result.stdout = "git version 2.34.1"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)

        # Test check_git_available logging
        git_ops.check_git_available()
        mock_logger.log.assert_any_call(
            "DEBUG", "Git availability check passed", version="git version 2.34.1"
        )

        # Test get_git_version logging
        git_ops.get_git_version()
        mock_logger.log.assert_any_call(
            "DEBUG", "Git version obtained", version="git version 2.34.1"
        )


class TestGitOperationsEdgeCases:
    """Additional edge case tests for GitOperations."""

    @patch("spec_cli.git.operations.GitOperations.run_git_command")
    def test_version_with_newline_stripping(
        self, mock_run_git: Any, tmp_path: Path
    ) -> None:
        """Test that version string properly strips newlines."""
        mock_result = Mock()
        mock_result.stdout = "git version 2.34.1\n\n"
        mock_run_git.return_value = mock_result

        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        version = git_ops.get_git_version()

        assert version == "git version 2.34.1"

    def test_command_preparation_with_empty_args(self, tmp_path: Path) -> None:
        """Test command preparation with empty arguments."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        git_ops = GitOperations(spec_dir, specs_dir, index_file)
        cmd = git_ops._prepare_git_command([])

        expected = [
            "git",
            "-c",
            "core.excludesFile=",
            "-c",
            "core.ignoreCase=false",
        ]
        assert cmd == expected
