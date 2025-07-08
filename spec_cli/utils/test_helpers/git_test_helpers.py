"""Git test infrastructure for comprehensive Git operation mocking.

This module provides comprehensive Git test infrastructure to enable testing
of Git operations without actual Git commands, including repository state
mocking, command simulation, and environment isolation.
"""

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from ...core.context_bridge import debug_logger
from ...utils.path_utils import normalize_path_separators


class GitRepositoryMocker:
    """Mock Git repository for testing Git operations without real Git commands.

    This class provides comprehensive Git repository state simulation, allowing
    tests to verify Git operations without requiring actual Git commands or
    affecting the host system.
    """

    def __init__(self, repo_path: Path, initial_state: dict[str, Any] | None = None):
        """Initialize mock Git repository.

        Args:
            repo_path: Path where mock repository should appear to exist
            initial_state: Initial repository state (files, commits, branches)
        """
        self.repo_path = Path(repo_path).resolve()
        self.state = initial_state or {
            "files": {},
            "commits": [],
            "current_branch": "main",
            "branches": ["main"],
            "staged_files": set(),
            "modified_files": set(),
            "untracked_files": set(),
            "initialized": False,
            "head_commit": None,
        }
        self.command_history: list[list[str]] = []

        debug_logger.log(
            "DEBUG",
            "GitRepositoryMocker initialized",
            repo_path=str(self.repo_path),
            initial_state_keys=list(self.state.keys()),
        )

    def mock_git_command(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock Git command execution with realistic responses.

        Args:
            command: Git command as list of strings

        Returns:
            CompletedProcess with appropriate stdout/stderr/returncode

        Raises:
            ValueError: If command is not a valid Git command
        """
        self.command_history.append(command.copy())

        if not command or command[0] != "git":
            raise ValueError(
                f"Expected git command, got: {command[0] if command else 'empty'}"
            )

        git_command = command[1] if len(command) > 1 else ""

        debug_logger.log(
            "DEBUG",
            "Mocking Git command",
            command=git_command,
            full_command=command,
        )

        # Handle different Git commands
        if git_command == "init":
            return self._mock_git_init(command)
        elif git_command == "add":
            return self._mock_git_add(command)
        elif git_command == "commit":
            return self._mock_git_commit(command)
        elif git_command == "status":
            return self._mock_git_status(command)
        elif git_command == "log":
            return self._mock_git_log(command)
        elif git_command == "diff":
            return self._mock_git_diff(command)
        elif git_command == "rev-parse":
            return self._mock_git_rev_parse(command)
        elif git_command == "symbolic-ref":
            return self._mock_git_symbolic_ref(command)
        elif git_command == "diff-index":
            return self._mock_git_diff_index(command)
        elif git_command == "ls-files":
            return self._mock_git_ls_files(command)
        elif git_command == "--version":
            return self._mock_git_version(command)
        else:
            return self._mock_unknown_command(command)

    def _mock_git_init(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git init command."""
        is_bare = "--bare" in command
        self.state["initialized"] = True

        if is_bare:
            stdout = f"Initialized empty Git repository in {self.repo_path}/"
        else:
            stdout = f"Initialized empty Git repository in {self.repo_path}/.git/"

        debug_logger.log("DEBUG", "Mock git init", is_bare=is_bare, stdout=stdout)

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_add(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git add command."""
        # Extract files to add (skip 'git', 'add', and flags)
        files_to_add = []
        skip_next = False

        for _i, arg in enumerate(command[2:], 2):  # Start after 'git add'
            if skip_next:
                skip_next = False
                continue
            if arg.startswith("-"):
                continue
            files_to_add.append(arg)

        # Stage the files
        for file_path in files_to_add:
            normalized_path = normalize_path_separators(file_path)
            self.state["staged_files"].add(normalized_path)
            # Remove from untracked if it was there
            self.state["untracked_files"].discard(normalized_path)

        debug_logger.log(
            "DEBUG",
            "Mock git add",
            files_added=files_to_add,
            staged_count=len(self.state["staged_files"]),
        )

        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def _mock_git_commit(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git commit command."""
        # Extract commit message
        message = "test commit"
        if "-m" in command:
            msg_index = command.index("-m")
            if msg_index + 1 < len(command):
                message = command[msg_index + 1]

        # Create commit object
        commit_hash = f"abc{len(self.state['commits']):04d}123"
        commit = {
            "hash": commit_hash,
            "message": message,
            "files": list(self.state["staged_files"]),
            "author": "Test User <test@example.com>",
            "timestamp": "2025-01-01T00:00:00Z",
        }

        self.state["commits"].append(commit)
        self.state["head_commit"] = commit_hash

        # Clear staged files after commit
        self.state["staged_files"].clear()

        stdout = f"[{self.state['current_branch']} {commit_hash[:7]}] {message}"

        debug_logger.log(
            "DEBUG",
            "Mock git commit",
            commit_hash=commit_hash,
            commit_message=message,
            files_committed=commit["files"],
        )

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_status(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git status command."""
        lines = [f"On branch {self.state['current_branch']}"]

        if self.state["staged_files"]:
            lines.append("Changes to be committed:")
            for file_path in sorted(self.state["staged_files"]):
                lines.append(f"  new file:   {file_path}")

        if self.state["modified_files"]:
            lines.append("Changes not staged for commit:")
            for file_path in sorted(self.state["modified_files"]):
                lines.append(f"  modified:   {file_path}")

        if self.state["untracked_files"]:
            lines.append("Untracked files:")
            for file_path in sorted(self.state["untracked_files"]):
                lines.append(f"  {file_path}")

        if not (
            self.state["staged_files"]
            or self.state["modified_files"]
            or self.state["untracked_files"]
        ):
            lines.append("nothing to commit, working tree clean")

        stdout = "\n".join(lines)

        debug_logger.log("DEBUG", "Mock git status", line_count=len(lines))

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_log(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git log command."""
        if not self.state["commits"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        # Handle different log formats
        if "--pretty=format:" in " ".join(command):
            # Custom format
            format_str = None
            for _i, arg in enumerate(command):
                if arg.startswith("--pretty=format:"):
                    format_str = arg.split(":", 1)[1]
                    break

            if format_str:
                lines = []
                for commit in reversed(self.state["commits"]):
                    line = format_str.replace("%H", commit["hash"])
                    line = line.replace("%s", commit["message"])
                    line = line.replace("%an", commit["author"].split("<")[0].strip())
                    line = line.replace("%ad", commit["timestamp"])
                    lines.append(line)
                stdout = "\n".join(lines)
            else:
                stdout = ""
        else:
            # Default format
            lines = []
            for commit in reversed(self.state["commits"]):
                if "--oneline" in command:
                    lines.append(f"{commit['hash'][:7]} {commit['message']}")
                else:
                    lines.extend(
                        [
                            f"commit {commit['hash']}",
                            f"Author: {commit['author']}",
                            f"Date:   {commit['timestamp']}",
                            "",
                            f"    {commit['message']}",
                            "",
                        ]
                    )
            stdout = "\n".join(lines)

        debug_logger.log(
            "DEBUG", "Mock git log", commit_count=len(self.state["commits"])
        )

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_diff(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git diff command."""
        # Simple diff mock - could be enhanced for specific needs
        if "--cached" in command:
            # Staged changes
            if self.state["staged_files"]:
                stdout = "diff --git a/file.txt b/file.txt\n+new content"
            else:
                stdout = ""
        elif "--name-only" in command:
            if "--cached" in command:
                stdout = "\n".join(sorted(self.state["staged_files"]))
            else:
                stdout = "\n".join(sorted(self.state["modified_files"]))
        else:
            # Working directory changes
            if self.state["modified_files"]:
                stdout = "diff --git a/file.txt b/file.txt\n+modified content"
            else:
                stdout = ""

        debug_logger.log("DEBUG", "Mock git diff", has_output=bool(stdout))

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_rev_parse(
        self, command: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Mock git rev-parse command."""
        if "HEAD" in command:
            if self.state["head_commit"]:
                stdout = self.state["head_commit"]
            else:
                return subprocess.CompletedProcess(
                    command, 128, stdout="", stderr="fatal: ambiguous argument 'HEAD'"
                )
        else:
            stdout = "abc1234567890"  # Default hash

        debug_logger.log("DEBUG", "Mock git rev-parse", stdout=stdout)

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_symbolic_ref(
        self, command: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Mock git symbolic-ref command."""
        if "--short" in command and "HEAD" in command:
            stdout = self.state["current_branch"]
        else:
            stdout = f"refs/heads/{self.state['current_branch']}"

        debug_logger.log("DEBUG", "Mock git symbolic-ref", branch=stdout)

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_diff_index(
        self, command: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Mock git diff-index command."""
        # Return code 1 if there are changes, 0 if clean
        if "--quiet" in command:
            if "--cached" in command:
                # Check staged changes
                returncode = 1 if self.state["staged_files"] else 0
            else:
                # Check working directory changes
                returncode = 1 if self.state["modified_files"] else 0
        else:
            returncode = 0  # Non-quiet mode always succeeds

        debug_logger.log("DEBUG", "Mock git diff-index", returncode=returncode)

        return subprocess.CompletedProcess(command, returncode, stdout="", stderr="")

    def _mock_git_ls_files(
        self, command: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Mock git ls-files command."""
        if "--others" in command:
            # Untracked files
            stdout = "\n".join(sorted(self.state["untracked_files"]))
        else:
            # Tracked files
            tracked_files = set()
            for commit in self.state["commits"]:
                tracked_files.update(commit["files"])
            tracked_files.update(self.state["staged_files"])
            stdout = "\n".join(sorted(tracked_files))

        debug_logger.log(
            "DEBUG",
            "Mock git ls-files",
            file_count=len(stdout.split("\n")) if stdout else 0,
        )

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_git_version(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Mock git --version command."""
        stdout = "git version 2.34.1"

        debug_logger.log("DEBUG", "Mock git version")

        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def _mock_unknown_command(
        self, command: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Mock unknown Git command with error."""
        git_cmd = command[1] if len(command) > 1 else "unknown"
        stderr = f"git: '{git_cmd}' is not a git command. See 'git --help'."

        debug_logger.log("DEBUG", "Mock unknown git command", command=git_cmd)

        return subprocess.CompletedProcess(command, 1, stdout="", stderr=stderr)

    def add_file(self, file_path: str, content: str = "test content") -> None:
        """Add file to mock repository state.

        Args:
            file_path: Path of file to add
            content: Content of the file
        """
        normalized_path = normalize_path_separators(file_path)
        self.state["files"][normalized_path] = content
        self.state["untracked_files"].add(normalized_path)

        debug_logger.log("DEBUG", "File added to mock repo", file_path=normalized_path)

    def stage_file(self, file_path: str) -> None:
        """Stage file in mock repository.

        Args:
            file_path: Path of file to stage
        """
        normalized_path = normalize_path_separators(file_path)
        if (
            normalized_path in self.state["files"]
            or normalized_path in self.state["untracked_files"]
        ):
            self.state["staged_files"].add(normalized_path)
            self.state["untracked_files"].discard(normalized_path)

        debug_logger.log("DEBUG", "File staged in mock repo", file_path=normalized_path)

    def modify_file(self, file_path: str, content: str = "modified content") -> None:
        """Modify existing file in mock repository.

        Args:
            file_path: Path of file to modify
            content: New content of the file
        """
        normalized_path = normalize_path_separators(file_path)
        if normalized_path in self.state["files"]:
            self.state["files"][normalized_path] = content
            self.state["modified_files"].add(normalized_path)

        debug_logger.log(
            "DEBUG", "File modified in mock repo", file_path=normalized_path
        )

    def get_state(self) -> dict[str, Any]:
        """Get current repository state.

        Returns:
            Dictionary containing current repository state
        """
        return self.state.copy()

    def get_command_history(self) -> list[list[str]]:
        """Get history of Git commands executed.

        Returns:
            List of command lists that were executed
        """
        return self.command_history.copy()


class GitCommandSimulator:
    """Simulate Git command execution for testing.

    This class provides a flexible system for registering custom responses
    to Git commands, allowing fine-grained control over subprocess mocking
    in tests.
    """

    def __init__(self) -> None:
        """Initialize Git command simulator."""
        self.mock_responses: dict[str, dict[str, Any]] = {}
        self.command_history: list[str] = []
        self.default_repository: GitRepositoryMocker | None = None

        debug_logger.log("DEBUG", "GitCommandSimulator initialized")

    def register_command_response(
        self, command_pattern: str, response: dict[str, Any]
    ) -> None:
        """Register a response for a Git command pattern.

        Args:
            command_pattern: Pattern to match (e.g., "git status", "git add *")
            response: Response dict with returncode, stdout, stderr
        """
        self.mock_responses[command_pattern] = response

        debug_logger.log(
            "DEBUG",
            "Git command response registered",
            pattern=command_pattern,
            returncode=response.get("returncode", 0),
        )

    def set_default_repository(self, repository: GitRepositoryMocker) -> None:
        """Set default repository for command simulation.

        Args:
            repository: GitRepositoryMocker to use as default
        """
        self.default_repository = repository

        debug_logger.log("DEBUG", "Default repository set for command simulator")

    @contextmanager
    def mock_git_commands(self) -> Iterator[Mock]:
        """Context manager to mock all Git subprocess calls.

        Yields:
            Mock object that can be used to inspect calls
        """
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = self._simulate_command

            debug_logger.log("DEBUG", "Git command mocking context entered")

            try:
                yield mock_run
            finally:
                debug_logger.log(
                    "DEBUG",
                    "Git command mocking context exited",
                    total_commands_executed=len(self.command_history),
                )

    def _simulate_command(
        self, command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        """Simulate command execution based on registered responses.

        Args:
            command: Command to simulate
            **kwargs: Additional subprocess.run arguments

        Returns:
            CompletedProcess with simulated results
        """
        command_str = " ".join(command)
        self.command_history.append(command_str)

        debug_logger.log("DEBUG", "Simulating command", command=command_str)

        # Check for registered responses first
        for pattern, response in self.mock_responses.items():
            if self._command_matches_pattern(command_str, pattern):
                debug_logger.log("DEBUG", "Using registered response", pattern=pattern)
                return subprocess.CompletedProcess(
                    command,
                    response.get("returncode", 0),
                    stdout=response.get("stdout", ""),
                    stderr=response.get("stderr", ""),
                )

        # Use default repository if available and command is git
        if self.default_repository and command and command[0] == "git":
            try:
                return self.default_repository.mock_git_command(command)
            except Exception as e:
                debug_logger.log(
                    "WARNING", "Default repository command failed", error=str(e)
                )

        # Default response for unregistered commands
        debug_logger.log("DEBUG", "Using default response for unknown command")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def _command_matches_pattern(self, command_str: str, pattern: str) -> bool:
        """Check if command matches a pattern.

        Args:
            command_str: Command string to check
            pattern: Pattern to match against

        Returns:
            True if command matches pattern
        """
        # Simple pattern matching - could be enhanced with regex
        if "*" in pattern:
            # Handle wildcard patterns
            pattern_parts = pattern.split("*")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                return command_str.startswith(prefix) and command_str.endswith(suffix)

        return command_str == pattern or command_str.startswith(pattern + " ")

    def get_command_history(self) -> list[str]:
        """Get history of commands that were simulated.

        Returns:
            List of command strings that were executed
        """
        return self.command_history.copy()

    def clear_history(self) -> None:
        """Clear command history."""
        self.command_history.clear()
        debug_logger.log("DEBUG", "Command history cleared")


class GitEnvironmentIsolator:
    """Isolate Git environment for testing.

    This class provides environment variable isolation specifically for Git
    operations, ensuring tests don't interfere with the host system's Git
    configuration or repositories.
    """

    def __init__(self, spec_dir: Path, specs_dir: Path):
        """Initialize Git environment isolator.

        Args:
            spec_dir: Path to .spec directory
            specs_dir: Path to .specs directory
        """
        self.spec_dir = Path(spec_dir).resolve()
        self.specs_dir = Path(specs_dir).resolve()
        self.original_env: dict[str, str | None] = {}
        self.isolated_env: dict[str, str] = {}

        debug_logger.log(
            "DEBUG",
            "GitEnvironmentIsolator initialized",
            spec_dir=str(self.spec_dir),
            specs_dir=str(self.specs_dir),
        )

    @contextmanager
    def isolated_git_environment(self) -> Iterator[dict[str, str]]:
        """Context manager for isolated Git environment.

        Yields:
            Dictionary of Git environment variables that were set
        """
        try:
            debug_logger.log("DEBUG", "Setting up Git environment isolation")
            self._setup_git_isolation()
            yield self.isolated_env
        finally:
            debug_logger.log("DEBUG", "Restoring original Git environment")
            self._restore_git_environment()

    def _setup_git_isolation(self) -> None:
        """Set up Git environment variable isolation."""
        git_env_vars = {
            "GIT_DIR": str(self.spec_dir),
            "GIT_WORK_TREE": str(self.specs_dir),
            "GIT_INDEX_FILE": str(self.spec_dir / "index"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",  # Disable global config
        }

        # Store original environment
        for key in git_env_vars:
            self.original_env[key] = os.environ.get(key)

        # Apply isolation
        os.environ.update(git_env_vars)
        self.isolated_env = git_env_vars.copy()

        debug_logger.log(
            "DEBUG",
            "Git environment isolation applied",
            vars_set=list(git_env_vars.keys()),
        )

    def _restore_git_environment(self) -> None:
        """Restore original Git environment."""
        restored_count = 0

        for key, original_value in self.original_env.items():
            if original_value is None:
                # Variable wasn't set originally, remove it
                os.environ.pop(key, None)
            else:
                # Restore original value
                os.environ[key] = original_value
            restored_count += 1

        self.original_env.clear()
        self.isolated_env.clear()

        debug_logger.log(
            "DEBUG", "Git environment restored", vars_restored=restored_count
        )


# Factory functions for easy helper creation


def create_git_repository_mocker(
    repo_path: Path, initial_state: dict[str, Any] | None = None
) -> GitRepositoryMocker:
    """Create GitRepositoryMocker instance.

    Args:
        repo_path: Path where mock repository should appear to exist
        initial_state: Optional initial repository state

    Returns:
        Configured GitRepositoryMocker instance
    """
    debug_logger.log("DEBUG", "Creating GitRepositoryMocker", repo_path=str(repo_path))
    return GitRepositoryMocker(repo_path, initial_state)


def create_git_command_simulator() -> GitCommandSimulator:
    """Create GitCommandSimulator instance.

    Returns:
        Configured GitCommandSimulator instance
    """
    debug_logger.log("DEBUG", "Creating GitCommandSimulator")
    return GitCommandSimulator()


def create_git_environment_isolator(
    spec_dir: Path, specs_dir: Path
) -> GitEnvironmentIsolator:
    """Create GitEnvironmentIsolator instance.

    Args:
        spec_dir: Path to .spec directory
        specs_dir: Path to .specs directory

    Returns:
        Configured GitEnvironmentIsolator instance
    """
    debug_logger.log(
        "DEBUG",
        "Creating GitEnvironmentIsolator",
        spec_dir=str(spec_dir),
        specs_dir=str(specs_dir),
    )
    return GitEnvironmentIsolator(spec_dir, specs_dir)


# Pytest fixtures for integration


def git_test_repository(tmp_path: Path) -> GitRepositoryMocker:
    """Pytest fixture for temporary Git repository.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        GitRepositoryMocker instance for testing
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    return create_git_repository_mocker(repo_path)


def git_command_simulator() -> GitCommandSimulator:
    """Pytest fixture for Git command simulation.

    Returns:
        GitCommandSimulator instance for testing
    """
    return create_git_command_simulator()


def git_environment_isolator(tmp_path: Path) -> GitEnvironmentIsolator:
    """Pytest fixture for Git environment isolation.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        GitEnvironmentIsolator instance for testing
    """
    spec_dir = tmp_path / ".spec"
    specs_dir = tmp_path / ".specs"
    return create_git_environment_isolator(spec_dir, specs_dir)
