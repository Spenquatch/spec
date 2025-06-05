"""Integration test for Slice 1b: Secure Git Operations Integration.

This test validates that GitOperations.run_git_command() successfully blocks
injection attempts while allowing legitimate operations, as specified in
the slice requirements.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations


class TestSlice1bGitOperationsSecurityIntegration:
    """Integration test for secure git operations as required by Slice 1b."""

    @pytest.fixture
    def git_ops(self, tmp_path: Path) -> GitOperations:
        """Create GitOperations instance for integration testing."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        # Create directories for realistic testing
        specs_dir.mkdir(parents=True, exist_ok=True)

        return GitOperations(spec_dir, specs_dir, index_file)

    def test_git_operations_run_command_blocks_injection_attempts_while_allowing_legitimate_operations(
        self, git_ops: GitOperations
    ) -> None:
        """Integration test: GitOperations.run_git_command() blocks injection attempts while allowing legitimate operations.

        This is the core integration validation specified in Slice 1b requirements.
        """
        with patch("spec_cli.git.operations.subprocess.run") as mock_subprocess:
            # Setup mock for successful subprocess execution
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "success"
            mock_subprocess.return_value.stderr = ""

            # Create a test file in the specs directory for valid path testing
            test_file = git_ops.specs_dir / "valid_file.md"
            test_file.write_text("test content")

            # Test 1: Legitimate operations should succeed
            legitimate_commands = [
                ["status"],
                ["add", str(test_file)],  # Use absolute path to file in specs_dir
                [
                    "commit",
                    "--message=Add test file",
                ],  # Use flag format to avoid path detection
                ["log", "--oneline"],
                ["diff", "HEAD"],
                ["show", "HEAD"],
            ]

            for cmd in legitimate_commands:
                # This should not raise an exception
                result = git_ops.run_git_command(cmd)
                assert result.returncode == 0
                # Verify subprocess was actually called (command was not blocked)
                assert mock_subprocess.called
                mock_subprocess.reset_mock()

            # Test 2: Dangerous commands should be blocked before subprocess execution
            dangerous_commands = [
                ["rm", "-rf", "/"],
                ["exec", "malicious_script"],
                ["config", "--global", "core.editor", "evil"],
                ["submodule", "update", "--init", "--recursive"],
                ["clone", "malicious://repo", "/tmp/evil"],
            ]

            for cmd in dangerous_commands:
                with pytest.raises(SpecGitError) as exc_info:
                    git_ops.run_git_command(cmd)

                # Verify error indicates command validation failure
                assert "Command validation failed" in str(exc_info.value)
                # Verify subprocess was never called (command was blocked)
                assert not mock_subprocess.called

            # Test 3: Directory traversal attempts should be blocked
            traversal_commands = [
                ["add", "../../../etc/passwd"],
                ["add", "..\\..\\..\\windows\\system32\\cmd.exe"],
                ["diff", "/etc/shadow"],
                ["show", "HEAD:../../../../sensitive/file"],
            ]

            for cmd in traversal_commands:
                with pytest.raises(SpecGitError) as exc_info:
                    git_ops.run_git_command(cmd)

                # Verify error indicates validation failure
                assert "Command validation failed" in str(exc_info.value)
                # Verify subprocess was never called (command was blocked)
                assert not mock_subprocess.called

    def test_security_integration_maintains_existing_functionality(
        self, git_ops: GitOperations
    ) -> None:
        """Test that security integration doesn't break existing GitOperations functionality."""
        with patch("spec_cli.git.operations.subprocess.run") as mock_subprocess:
            # Setup mock
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "test output"
            mock_subprocess.return_value.stderr = ""

            # Create a test file for path validation
            test_file = git_ops.specs_dir / "test_file.md"
            test_file.write_text("test content")

            # Test all existing parameter patterns still work
            test_cases = [
                # Basic usage
                (["status"], {"capture_output": True}),
                # Without output capture
                (["status"], {"capture_output": False}),
                # With file arguments (use absolute path to valid file)
                (["add", str(test_file)], {"capture_output": True}),
            ]

            for args, kwargs in test_cases:
                result = git_ops.run_git_command(args, **kwargs)

                # Verify command executed successfully
                assert result.returncode == 0
                assert result.stdout == "test output"

                # Verify subprocess called with correct parameters
                call_args = mock_subprocess.call_args
                assert call_args[1]["capture_output"] == kwargs["capture_output"]

                # Reset for next test
                mock_subprocess.reset_mock()

    def test_error_handling_provides_secure_messages(
        self, git_ops: GitOperations
    ) -> None:
        """Test that error handling provides secure, non-leaky error messages."""
        # Test validation error message security
        with pytest.raises(SpecGitError) as exc_info:
            git_ops.run_git_command(["dangerous_command"])

        error_msg = str(exc_info.value)
        # Should contain validation failure indication
        assert "Command validation failed" in error_msg
        # Should contain specific security error
        assert "Git command 'dangerous_command' not allowed" in error_msg
        # Should not expose internal system details
        assert "subprocess" not in error_msg.lower()
        assert "python" not in error_msg.lower()

    def test_path_validation_integration_with_specs_directory(
        self, git_ops: GitOperations
    ) -> None:
        """Test that path validation correctly uses specs directory context."""
        with patch("spec_cli.git.operations.subprocess.run") as mock_subprocess:
            # Setup mock
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""
            mock_subprocess.return_value.stderr = ""

            # Create test file in specs directory
            test_file = git_ops.specs_dir / "test.md"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("test content")

            # Valid file within specs directory should work
            result = git_ops.run_git_command(["add", str(test_file)])
            assert result.returncode == 0
            assert mock_subprocess.called

            # Reset mock
            mock_subprocess.reset_mock()

            # Note: Relative paths are validated strictly and may fail
            # if they resolve outside the work tree. This is expected
            # security behavior. Commands without file arguments work fine.
            result = git_ops.run_git_command(["status"])
            assert result.returncode == 0
            assert mock_subprocess.called

    def test_security_validation_is_idempotent(self, git_ops: GitOperations) -> None:
        """Test that security validation behaves consistently across multiple calls."""
        # Test that the same command is consistently allowed
        with patch("spec_cli.git.operations.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""
            mock_subprocess.return_value.stderr = ""

            # Execute same valid command multiple times
            for _ in range(3):
                result = git_ops.run_git_command(["status"])
                assert result.returncode == 0

        # Test that the same dangerous command is consistently blocked
        for _ in range(3):
            with pytest.raises(SpecGitError) as exc_info:
                git_ops.run_git_command(["rm", "-rf", "/"])
            assert "Command validation failed" in str(exc_info.value)

    def test_integration_preserves_git_environment_configuration(
        self, git_ops: GitOperations
    ) -> None:
        """Test that security integration preserves Git environment configuration."""
        with patch("spec_cli.git.operations.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""
            mock_subprocess.return_value.stderr = ""

            # Execute command
            git_ops.run_git_command(["status"])

            # Verify subprocess was called with correct Git environment
            call_args = mock_subprocess.call_args
            env = call_args[1]["env"]

            # Verify spec-specific Git environment variables are set
            assert env["GIT_DIR"] == str(git_ops.spec_dir)
            assert env["GIT_WORK_TREE"] == str(git_ops.specs_dir)
            assert env["GIT_INDEX_FILE"] == str(git_ops.index_file)

            # Verify command includes proper Git configuration flags
            cmd = call_args[0][0]
            assert cmd[0] == "git"
            assert "-c" in cmd
            assert "core.excludesFile=" in cmd
            assert "core.ignoreCase=false" in cmd
            assert "status" in cmd
