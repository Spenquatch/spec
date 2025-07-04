"""Unit tests for Git test helpers infrastructure.

This module tests the Git test helper infrastructure itself to ensure
reliable mocking and simulation capabilities for other test suites.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.utils.path_utils import normalize_path_separators
from spec_cli.utils.test_helpers.git_test_helpers import (
    GitCommandSimulator,
    GitEnvironmentIsolator,
    GitRepositoryMocker,
    create_git_command_simulator,
    create_git_environment_isolator,
    create_git_repository_mocker,
)


class TestGitRepositoryMocker:
    """Test GitRepositoryMocker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repo_path = Path("/tmp/test_repo")
        self.mocker = GitRepositoryMocker(self.repo_path)

    def test_initialization_with_defaults(self):
        """Test GitRepositoryMocker initialization with default state."""
        assert self.mocker.repo_path == self.repo_path.resolve()
        assert self.mocker.state["current_branch"] == "main"
        assert self.mocker.state["branches"] == ["main"]
        assert self.mocker.state["initialized"] is False
        assert len(self.mocker.command_history) == 0

    def test_initialization_with_custom_state(self):
        """Test GitRepositoryMocker initialization with custom state."""
        initial_state = {
            "current_branch": "develop",
            "branches": ["main", "develop"],
            "files": {"test.txt": "content"},
        }
        mocker = GitRepositoryMocker(self.repo_path, initial_state)

        assert mocker.state["current_branch"] == "develop"
        assert mocker.state["branches"] == ["main", "develop"]
        assert mocker.state["files"] == {"test.txt": "content"}

    def test_mock_git_init_command(self):
        """Test mocking of git init command."""
        command = ["git", "init"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Initialized empty Git repository" in result.stdout
        assert self.mocker.state["initialized"] is True
        assert command in self.mocker.command_history

    def test_mock_git_init_bare_command(self):
        """Test mocking of git init --bare command."""
        command = ["git", "init", "--bare", "/path/to/repo"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Initialized empty Git repository" in result.stdout
        assert not result.stdout.endswith("/.git/")  # Bare repo doesn't have .git
        assert self.mocker.state["initialized"] is True

    def test_mock_git_add_command(self):
        """Test mocking of git add command."""
        # Add a file to the repository first
        self.mocker.add_file("test.txt", "content")

        command = ["git", "add", "test.txt"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "test.txt" in self.mocker.state["staged_files"]
        assert "test.txt" not in self.mocker.state["untracked_files"]

    def test_mock_git_add_multiple_files(self):
        """Test mocking of git add with multiple files."""
        # Add files to the repository
        self.mocker.add_file("file1.txt", "content1")
        self.mocker.add_file("file2.txt", "content2")

        command = ["git", "add", "file1.txt", "file2.txt"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "file1.txt" in self.mocker.state["staged_files"]
        assert "file2.txt" in self.mocker.state["staged_files"]

    def test_mock_git_add_with_force_flag(self):
        """Test mocking of git add with -f flag."""
        self.mocker.add_file("test.txt", "content")

        command = ["git", "add", "-f", "test.txt"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "test.txt" in self.mocker.state["staged_files"]

    def test_mock_git_commit_command(self):
        """Test mocking of git commit command."""
        # Stage a file first
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        command = ["git", "commit", "-m", "Test commit"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Test commit" in result.stdout
        assert len(self.mocker.state["commits"]) == 1
        assert self.mocker.state["commits"][0]["message"] == "Test commit"
        assert (
            len(self.mocker.state["staged_files"]) == 0
        )  # Should be cleared after commit

    def test_mock_git_commit_creates_commit_hash(self):
        """Test that git commit creates a proper commit hash."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        command = ["git", "commit", "-m", "Test commit"]
        result = self.mocker.mock_git_command(command)

        commit = self.mocker.state["commits"][0]
        assert len(commit["hash"]) > 7  # Should be a reasonable hash length
        assert commit["hash"] == self.mocker.state["head_commit"]
        assert commit["hash"][:7] in result.stdout  # Short hash in output

    def test_mock_git_status_clean(self):
        """Test mocking of git status with clean repository."""
        command = ["git", "status"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "On branch main" in result.stdout
        assert "nothing to commit, working tree clean" in result.stdout

    def test_mock_git_status_with_staged_files(self):
        """Test mocking of git status with staged files."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        command = ["git", "status"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Changes to be committed:" in result.stdout
        assert "new file:   test.txt" in result.stdout

    def test_mock_git_status_with_modified_files(self):
        """Test mocking of git status with modified files."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.modify_file("test.txt", "new content")

        command = ["git", "status"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Changes not staged for commit:" in result.stdout
        assert "modified:   test.txt" in result.stdout

    def test_mock_git_status_with_untracked_files(self):
        """Test mocking of git status with untracked files."""
        self.mocker.add_file("untracked.txt", "content")

        command = ["git", "status"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "Untracked files:" in result.stdout
        assert "untracked.txt" in result.stdout

    def test_mock_git_log_empty_repository(self):
        """Test mocking of git log with no commits."""
        command = ["git", "log"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert result.stdout == ""

    def test_mock_git_log_with_commits(self):
        """Test mocking of git log with commits."""
        # Create a commit
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")
        self.mocker.mock_git_command(["git", "commit", "-m", "First commit"])

        command = ["git", "log"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "First commit" in result.stdout
        assert "commit abc0000123" in result.stdout

    def test_mock_git_log_oneline_format(self):
        """Test mocking of git log --oneline."""
        # Create a commit
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")
        self.mocker.mock_git_command(["git", "commit", "-m", "First commit"])

        command = ["git", "log", "--oneline"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "abc0000 First commit" in result.stdout

    def test_mock_git_log_custom_format(self):
        """Test mocking of git log with custom format."""
        # Create a commit
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")
        self.mocker.mock_git_command(["git", "commit", "-m", "First commit"])

        command = ["git", "log", "--pretty=format:%H|%s|%an|%ad"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        lines = result.stdout.split("\n")
        assert len(lines) == 1
        parts = lines[0].split("|")
        assert len(parts) == 4
        assert parts[1] == "First commit"

    def test_mock_git_diff_no_changes(self):
        """Test mocking of git diff with no changes."""
        command = ["git", "diff"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert result.stdout == ""

    def test_mock_git_diff_with_changes(self):
        """Test mocking of git diff with changes."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.modify_file("test.txt", "new content")

        command = ["git", "diff"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "diff --git" in result.stdout

    def test_mock_git_diff_cached(self):
        """Test mocking of git diff --cached."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        command = ["git", "diff", "--cached"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "diff --git" in result.stdout

    def test_mock_git_diff_name_only(self):
        """Test mocking of git diff --name-only."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.modify_file("test.txt", "new content")

        command = ["git", "diff", "--name-only"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "test.txt" in result.stdout

    def test_mock_git_rev_parse_head(self):
        """Test mocking of git rev-parse HEAD."""
        # Create a commit first
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")
        self.mocker.mock_git_command(["git", "commit", "-m", "Test commit"])

        command = ["git", "rev-parse", "HEAD"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert result.stdout == self.mocker.state["head_commit"]

    def test_mock_git_rev_parse_head_no_commits(self):
        """Test mocking of git rev-parse HEAD with no commits."""
        command = ["git", "rev-parse", "HEAD"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 128
        assert "fatal: ambiguous argument" in result.stderr

    def test_mock_git_symbolic_ref(self):
        """Test mocking of git symbolic-ref."""
        command = ["git", "symbolic-ref", "HEAD"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "refs/heads/main" in result.stdout

    def test_mock_git_symbolic_ref_short(self):
        """Test mocking of git symbolic-ref --short HEAD."""
        command = ["git", "symbolic-ref", "--short", "HEAD"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert result.stdout == "main"

    def test_mock_git_diff_index_quiet_no_changes(self):
        """Test mocking of git diff-index --quiet with no changes."""
        command = ["git", "diff-index", "--quiet", "HEAD", "--"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0

    def test_mock_git_diff_index_quiet_with_changes(self):
        """Test mocking of git diff-index --quiet with changes."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.modify_file("test.txt", "new content")

        command = ["git", "diff-index", "--quiet", "HEAD", "--"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 1

    def test_mock_git_diff_index_cached_with_staged(self):
        """Test mocking of git diff-index --cached with staged files."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        command = ["git", "diff-index", "--quiet", "--cached", "HEAD", "--"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 1

    def test_mock_git_ls_files_others(self):
        """Test mocking of git ls-files --others."""
        self.mocker.add_file("untracked.txt", "content")

        command = ["git", "ls-files", "--others", "--exclude-standard"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "untracked.txt" in result.stdout

    def test_mock_git_ls_files_tracked(self):
        """Test mocking of git ls-files for tracked files."""
        # Create and commit a file
        self.mocker.add_file("tracked.txt", "content")
        self.mocker.stage_file("tracked.txt")
        self.mocker.mock_git_command(["git", "commit", "-m", "Add tracked file"])

        command = ["git", "ls-files"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "tracked.txt" in result.stdout

    def test_mock_git_version(self):
        """Test mocking of git --version."""
        command = ["git", "--version"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 0
        assert "git version" in result.stdout

    def test_mock_unknown_git_command(self):
        """Test mocking of unknown git command."""
        command = ["git", "unknown-command"]
        result = self.mocker.mock_git_command(command)

        assert result.returncode == 1
        assert "is not a git command" in result.stderr

    def test_invalid_command_raises_error(self):
        """Test that invalid commands raise ValueError."""
        with pytest.raises(ValueError, match="Expected git command"):
            self.mocker.mock_git_command(["not-git", "status"])

    def test_empty_command_raises_error(self):
        """Test that empty commands raise ValueError."""
        with pytest.raises(ValueError, match="Expected git command"):
            self.mocker.mock_git_command([])

    def test_add_file_method(self):
        """Test add_file method."""
        self.mocker.add_file("test.txt", "content")

        assert "test.txt" in self.mocker.state["files"]
        assert self.mocker.state["files"]["test.txt"] == "content"
        assert "test.txt" in self.mocker.state["untracked_files"]

    def test_stage_file_method(self):
        """Test stage_file method."""
        self.mocker.add_file("test.txt", "content")
        self.mocker.stage_file("test.txt")

        assert "test.txt" in self.mocker.state["staged_files"]
        assert "test.txt" not in self.mocker.state["untracked_files"]

    def test_modify_file_method(self):
        """Test modify_file method."""
        self.mocker.add_file("test.txt", "original")
        self.mocker.modify_file("test.txt", "modified")

        assert self.mocker.state["files"]["test.txt"] == "modified"
        assert "test.txt" in self.mocker.state["modified_files"]

    def test_get_state_method(self):
        """Test get_state method returns copy of state."""
        state = self.mocker.get_state()

        assert isinstance(state, dict)
        assert state is not self.mocker.state  # Should be a copy
        assert state["current_branch"] == "main"

    def test_get_command_history_method(self):
        """Test get_command_history method."""
        self.mocker.mock_git_command(["git", "status"])
        self.mocker.mock_git_command(["git", "init"])

        history = self.mocker.get_command_history()

        assert len(history) == 2
        assert history[0] == ["git", "status"]
        assert history[1] == ["git", "init"]
        assert history is not self.mocker.command_history  # Should be a copy

    def test_path_normalization(self):
        """Test that file paths are normalized consistently."""
        self.mocker.add_file("path\\with\\backslashes.txt", "content")

        # Path should be normalized to forward slashes
        assert "path/with/backslashes.txt" in self.mocker.state["files"]
        assert "path/with/backslashes.txt" in self.mocker.state["untracked_files"]


class TestGitCommandSimulator:
    """Test GitCommandSimulator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = GitCommandSimulator()

    def test_initialization(self):
        """Test GitCommandSimulator initialization."""
        assert len(self.simulator.mock_responses) == 0
        assert len(self.simulator.command_history) == 0
        assert self.simulator.default_repository is None

    def test_register_command_response(self):
        """Test registering command responses."""
        response = {"returncode": 0, "stdout": "test output", "stderr": ""}
        self.simulator.register_command_response("git status", response)

        assert "git status" in self.simulator.mock_responses
        assert self.simulator.mock_responses["git status"] == response

    def test_set_default_repository(self):
        """Test setting default repository."""
        repo = GitRepositoryMocker(Path("/tmp/test"))
        self.simulator.set_default_repository(repo)

        assert self.simulator.default_repository is repo

    def test_mock_git_commands_context(self):
        """Test mock_git_commands context manager."""
        response = {"returncode": 0, "stdout": "mocked output", "stderr": ""}
        self.simulator.register_command_response("git status", response)

        with self.simulator.mock_git_commands() as mock_run:
            result = subprocess.run(["git", "status"], capture_output=True, text=True)

            assert result.returncode == 0
            assert result.stdout == "mocked output"
            assert mock_run.called

    def test_command_simulation_with_registered_response(self):
        """Test command simulation with registered responses."""
        response = {"returncode": 1, "stdout": "", "stderr": "error message"}
        self.simulator.register_command_response("git failed-command", response)

        result = self.simulator._simulate_command(["git", "failed-command"])

        assert result.returncode == 1
        assert result.stderr == "error message"
        assert "git failed-command" in self.simulator.command_history

    def test_command_simulation_with_default_repository(self):
        """Test command simulation with default repository."""
        repo = GitRepositoryMocker(Path("/tmp/test"))
        self.simulator.set_default_repository(repo)

        result = self.simulator._simulate_command(["git", "status"])

        assert result.returncode == 0
        assert "On branch main" in result.stdout

    def test_command_simulation_with_default_response(self):
        """Test command simulation with default response."""
        result = self.simulator._simulate_command(["unknown", "command"])

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_command_matches_pattern_exact(self):
        """Test exact command pattern matching."""
        assert self.simulator._command_matches_pattern("git status", "git status")
        assert not self.simulator._command_matches_pattern("git log", "git status")

    def test_command_matches_pattern_prefix(self):
        """Test prefix command pattern matching."""
        assert self.simulator._command_matches_pattern(
            "git status --short", "git status"
        )
        assert not self.simulator._command_matches_pattern("git log", "git status")

    def test_command_matches_pattern_wildcard(self):
        """Test wildcard command pattern matching."""
        assert self.simulator._command_matches_pattern("git add file.txt", "git add *")
        assert self.simulator._command_matches_pattern(
            "git add multiple files", "git add *"
        )
        assert not self.simulator._command_matches_pattern("git status", "git add *")

    def test_get_command_history(self):
        """Test getting command history."""
        self.simulator._simulate_command(["git", "status"])
        self.simulator._simulate_command(["git", "add", "file.txt"])

        history = self.simulator.get_command_history()

        assert len(history) == 2
        assert history[0] == "git status"
        assert history[1] == "git add file.txt"

    def test_clear_history(self):
        """Test clearing command history."""
        self.simulator._simulate_command(["git", "status"])
        assert len(self.simulator.command_history) == 1

        self.simulator.clear_history()
        assert len(self.simulator.command_history) == 0

    def test_default_repository_command_failure(self):
        """Test handling of default repository command failures."""
        # Create a mock repository that raises an exception
        mock_repo = Mock()
        mock_repo.mock_git_command.side_effect = Exception("Mock error")
        self.simulator.set_default_repository(mock_repo)

        # Should fall back to default response
        result = self.simulator._simulate_command(["git", "status"])

        assert result.returncode == 0
        assert result.stdout == ""


class TestGitEnvironmentIsolator:
    """Test GitEnvironmentIsolator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.spec_dir = Path("/tmp/test/.spec")
        self.specs_dir = Path("/tmp/test/.specs")
        self.isolator = GitEnvironmentIsolator(self.spec_dir, self.specs_dir)

    def test_initialization(self):
        """Test GitEnvironmentIsolator initialization."""
        assert self.isolator.spec_dir == self.spec_dir.resolve()
        assert self.isolator.specs_dir == self.specs_dir.resolve()
        assert len(self.isolator.original_env) == 0
        assert len(self.isolator.isolated_env) == 0

    def test_isolated_git_environment_context(self):
        """Test isolated_git_environment context manager."""
        # Store original environment values
        original_git_dir = os.environ.get("GIT_DIR")
        original_git_work_tree = os.environ.get("GIT_WORK_TREE")

        try:
            with self.isolator.isolated_git_environment() as env_vars:
                # Check that isolation variables are set (resolve paths for comparison)
                assert (
                    Path(os.environ.get("GIT_DIR")).resolve() == self.spec_dir.resolve()
                )
                assert (
                    Path(os.environ.get("GIT_WORK_TREE")).resolve()
                    == self.specs_dir.resolve()
                )
                assert os.environ.get("GIT_CONFIG_NOSYSTEM") == "1"
                assert os.environ.get("GIT_CONFIG_GLOBAL") == "/dev/null"

                # Check returned environment variables (resolve paths for comparison)
                assert Path(env_vars["GIT_DIR"]).resolve() == self.spec_dir.resolve()
                assert (
                    Path(env_vars["GIT_WORK_TREE"]).resolve()
                    == self.specs_dir.resolve()
                )

            # Check that environment is restored
            assert os.environ.get("GIT_DIR") == original_git_dir
            assert os.environ.get("GIT_WORK_TREE") == original_git_work_tree

        finally:
            # Ensure cleanup
            if original_git_dir is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = original_git_dir

            if original_git_work_tree is None:
                os.environ.pop("GIT_WORK_TREE", None)
            else:
                os.environ["GIT_WORK_TREE"] = original_git_work_tree

    def test_isolated_git_environment_preserves_existing_values(self):
        """Test that isolation preserves existing environment values."""
        # Set some existing values
        os.environ["GIT_DIR"] = "/original/git/dir"
        os.environ["GIT_WORK_TREE"] = "/original/work/tree"

        try:
            with self.isolator.isolated_git_environment():
                # Values should be overridden during isolation (resolve paths for comparison)
                assert Path(os.environ["GIT_DIR"]).resolve() == self.spec_dir.resolve()
                assert (
                    Path(os.environ["GIT_WORK_TREE"]).resolve()
                    == self.specs_dir.resolve()
                )

            # Original values should be restored
            assert os.environ["GIT_DIR"] == "/original/git/dir"
            assert os.environ["GIT_WORK_TREE"] == "/original/work/tree"

        finally:
            # Clean up test environment
            os.environ.pop("GIT_DIR", None)
            os.environ.pop("GIT_WORK_TREE", None)

    def test_isolated_git_environment_handles_missing_values(self):
        """Test that isolation handles missing environment values correctly."""
        # Ensure variables are not set
        os.environ.pop("GIT_DIR", None)
        os.environ.pop("GIT_WORK_TREE", None)

        with self.isolator.isolated_git_environment():
            # Values should be set during isolation (resolve paths for comparison)
            assert Path(os.environ["GIT_DIR"]).resolve() == self.spec_dir.resolve()
            assert (
                Path(os.environ["GIT_WORK_TREE"]).resolve() == self.specs_dir.resolve()
            )

        # Values should be removed after isolation
        assert "GIT_DIR" not in os.environ
        assert "GIT_WORK_TREE" not in os.environ

    def test_setup_git_isolation(self):
        """Test _setup_git_isolation method."""
        original_git_dir = os.environ.get("GIT_DIR")

        try:
            self.isolator._setup_git_isolation()

            # Resolve paths for comparison
            assert Path(os.environ["GIT_DIR"]).resolve() == self.spec_dir.resolve()
            assert (
                Path(os.environ["GIT_WORK_TREE"]).resolve() == self.specs_dir.resolve()
            )
            assert "GIT_DIR" in self.isolator.original_env
            assert len(self.isolator.isolated_env) > 0

        finally:
            # Clean up
            self.isolator._restore_git_environment()
            if original_git_dir is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = original_git_dir

    def test_restore_git_environment(self):
        """Test _restore_git_environment method."""
        # Set up isolation first
        original_value = os.environ.get("GIT_DIR")
        self.isolator._setup_git_isolation()

        # Restore environment
        self.isolator._restore_git_environment()

        assert os.environ.get("GIT_DIR") == original_value
        assert len(self.isolator.original_env) == 0
        assert len(self.isolator.isolated_env) == 0


class TestFactoryFunctions:
    """Test factory functions for creating test helpers."""

    def test_create_git_repository_mocker(self):
        """Test create_git_repository_mocker factory function."""
        repo_path = Path("/tmp/test_repo")
        mocker = create_git_repository_mocker(repo_path)

        assert isinstance(mocker, GitRepositoryMocker)
        assert mocker.repo_path == repo_path.resolve()

    def test_create_git_repository_mocker_with_initial_state(self):
        """Test create_git_repository_mocker with initial state."""
        repo_path = Path("/tmp/test_repo")
        initial_state = {"current_branch": "develop"}
        mocker = create_git_repository_mocker(repo_path, initial_state)

        assert isinstance(mocker, GitRepositoryMocker)
        assert mocker.state["current_branch"] == "develop"

    def test_create_git_command_simulator(self):
        """Test create_git_command_simulator factory function."""
        simulator = create_git_command_simulator()

        assert isinstance(simulator, GitCommandSimulator)
        assert len(simulator.mock_responses) == 0

    def test_create_git_environment_isolator(self):
        """Test create_git_environment_isolator factory function."""
        spec_dir = Path("/tmp/.spec")
        specs_dir = Path("/tmp/.specs")
        isolator = create_git_environment_isolator(spec_dir, specs_dir)

        assert isinstance(isolator, GitEnvironmentIsolator)
        assert isolator.spec_dir == spec_dir.resolve()
        assert isolator.specs_dir == specs_dir.resolve()


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple helpers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repo_path = Path("/tmp/integration_test")
        self.mocker = GitRepositoryMocker(self.repo_path)
        self.simulator = GitCommandSimulator()
        self.isolator = GitEnvironmentIsolator(
            self.repo_path / ".spec", self.repo_path / ".specs"
        )

    def test_full_git_workflow_simulation(self):
        """Test complete Git workflow with all helpers."""
        # Set up simulator with repository
        self.simulator.set_default_repository(self.mocker)

        with self.simulator.mock_git_commands():
            with self.isolator.isolated_git_environment():
                # Simulate a complete Git workflow
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "add", "test.txt"], check=True)
                subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

                # Verify state
                assert self.mocker.state["initialized"] is True
                assert len(self.mocker.state["commits"]) == 1
                assert self.mocker.state["commits"][0]["message"] == "Initial commit"

    def test_repository_mocker_with_environment_isolation(self):
        """Test repository mocker works with environment isolation."""
        with self.isolator.isolated_git_environment() as env_vars:
            # Add and stage a file
            self.mocker.add_file("isolated_test.txt", "content")
            result = self.mocker.mock_git_command(["git", "add", "isolated_test.txt"])

            assert result.returncode == 0
            assert "isolated_test.txt" in self.mocker.state["staged_files"]

            # Environment should be isolated (resolve paths for comparison)
            assert (
                Path(env_vars["GIT_DIR"]).resolve()
                == (self.repo_path / ".spec").resolve()
            )

    def test_command_simulator_with_custom_responses(self):
        """Test command simulator with custom responses and default repository."""
        # Register custom response for specific command
        custom_response = {
            "returncode": 0,
            "stdout": "custom branch info",
            "stderr": "",
        }
        self.simulator.register_command_response("git branch", custom_response)
        self.simulator.set_default_repository(self.mocker)

        with self.simulator.mock_git_commands():
            # Custom response should be used
            result = subprocess.run(["git", "branch"], capture_output=True, text=True)
            assert result.stdout == "custom branch info"

            # Default repository should be used for other commands
            result = subprocess.run(["git", "status"], capture_output=True, text=True)
            assert "On branch main" in result.stdout

    def test_error_handling_in_integration(self):
        """Test error handling across integrated helpers."""
        # Test invalid command in repository mocker
        with pytest.raises(ValueError):
            self.mocker.mock_git_command(["not-git"])

        # Test command simulation error handling
        result = self.simulator._simulate_command(["git", "invalid-command"])
        assert result.returncode == 0  # Default response

        # Test environment isolation cleanup on exception
        try:
            with self.isolator.isolated_git_environment():
                raise Exception("Test exception")
        except Exception:
            pass

        # Environment should be restored even after exception
        assert len(self.isolator.original_env) == 0


class TestCoverageEdgeCases:
    """Additional tests to achieve 100% coverage for missing lines."""

    def test_git_add_with_skip_flag_edge_cases(self):
        """Test git add command with flags that cause argument skipping."""
        repo_path = Path("/tmp/test_repo")
        mocker = GitRepositoryMocker(repo_path)

        # Add a file first to make it trackable
        mocker.add_file("test.txt", "content")

        # Test add command with -f flag that should skip next argument
        result = mocker.mock_git_command(
            ["git", "add", "-f", "ignored_arg", "test.txt"]
        )

        assert result.returncode == 0
        assert "test.txt" in mocker.state["staged_files"]

    def test_git_log_with_custom_format_empty_repository(self):
        """Test git log with custom format when no commits exist."""
        repo_path = Path("/tmp/test_repo")
        mocker = GitRepositoryMocker(repo_path)

        # Test with custom format and no commits - should hit the empty stdout line
        result = mocker.mock_git_command(["git", "log", "--pretty=format:%H %s"])

        assert result.returncode == 0
        assert result.stdout == ""

    def test_git_command_empty_and_edge_cases(self):
        """Test edge cases in git command processing."""
        repo_path = Path("/tmp/test_repo")
        mocker = GitRepositoryMocker(repo_path)

        # Test command with just 'git' - should raise ValueError on line 132-133
        with pytest.raises(ValueError, match="Expected git command"):
            mocker.mock_git_command(["not-git"])

        # Test empty command list - should raise ValueError
        with pytest.raises((ValueError, IndexError)):
            mocker.mock_git_command([])

    def test_environment_isolation_setup_and_restore_edge_cases(self):
        """Test environment isolation edge cases."""
        spec_dir = Path("/tmp/.spec")
        specs_dir = Path("/tmp/.specs")
        isolator = GitEnvironmentIsolator(spec_dir, specs_dir)

        # Test direct setup and restore methods to hit lines 281, 284
        original_git_dir = os.environ.get("GIT_DIR")

        try:
            # Call setup directly
            isolator._setup_git_isolation()
            assert os.environ.get("GIT_DIR") == str(spec_dir.resolve())

            # Call restore directly
            isolator._restore_git_environment()

            # Should restore to original state
            if original_git_dir is None:
                assert "GIT_DIR" not in os.environ or os.environ.get("GIT_DIR") == ""
            else:
                assert os.environ.get("GIT_DIR") == original_git_dir

        finally:
            # Ensure cleanup
            if original_git_dir is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = original_git_dir

    def test_factory_functions_edge_cases(self):
        """Test factory functions to hit missing lines 741-743, 752, 764-766."""
        import tempfile

        # Test create_git_repository_mocker with initial state
        initial_state = {"current_branch": "develop", "files": {"test.txt": "content"}}
        repo_path = Path("/tmp/factory_test")
        mocker = create_git_repository_mocker(repo_path, initial_state)

        assert mocker.state["current_branch"] == "develop"
        assert "test.txt" in mocker.state["files"]

        # Test create_git_environment_isolator with tmp_path simulation
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            spec_dir = tmp_path / ".spec"
            specs_dir = tmp_path / ".specs"
            isolator = create_git_environment_isolator(spec_dir, specs_dir)

            assert isolator.spec_dir == spec_dir.resolve()
            assert isolator.specs_dir == specs_dir.resolve()

    def test_command_simulator_default_repository_exception_handling(self):
        """Test command simulator handling of default repository exceptions."""
        simulator = GitCommandSimulator()

        # Create a mock repository that raises an exception
        mock_repo = Mock()
        mock_repo.mock_git_command.side_effect = Exception("Mock repository error")
        simulator.set_default_repository(mock_repo)

        # Should fall back to default response when repository raises exception
        result = simulator._simulate_command(["git", "status"])

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_path_normalization_in_repository_mocker(self):
        """Test path normalization coverage in various methods."""
        repo_path = Path("/tmp/test_repo")
        mocker = GitRepositoryMocker(repo_path)

        # Test path normalization in add_file method
        test_path = "path\\with\\backslashes.txt"
        mocker.add_file(test_path, "content")
        normalized_path = normalize_path_separators(test_path)

        assert normalized_path in mocker.state["files"]
        assert normalized_path in mocker.state["untracked_files"]

        # Test stage_file with normalized paths - need to use the same path that was added
        mocker.stage_file(test_path)
        assert normalized_path in mocker.state["staged_files"]

        # Now test modify_file which should add to modified_files
        mocker.modify_file(test_path, "new content")
        assert normalized_path in mocker.state["modified_files"]
