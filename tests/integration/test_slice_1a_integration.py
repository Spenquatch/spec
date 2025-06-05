"""Integration tests for Slice 1a - Git Command Whitelist Validator with GitOperations."""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.git.operations import GitOperations
from spec_cli.utils.security_validators import (
    ALLOWED_GIT_COMMANDS,
    validate_git_command,
)


class TestGitOperationsSecurityIntegration:
    """Integration tests validating security validator against actual GitOperations usage."""

    @pytest.fixture
    def mock_git_operations(self, tmp_path):
        """Create a mock GitOperations instance for testing."""
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        index_file = tmp_path / ".spec-index"

        # Create directories for realistic setup
        spec_dir.mkdir()
        specs_dir.mkdir()

        return GitOperations(spec_dir, specs_dir, index_file)

    def test_validate_git_operations_common_commands_are_allowed(
        self, mock_git_operations
    ):
        """Test that common GitOperations commands pass security validation."""
        # Common commands used by GitOperations based on the codebase
        common_commands = [
            ["init", "--bare"],
            ["add", "-f", "file.md"],
            ["commit", "-m", "Initial spec commit"],
            ["status", "--porcelain"],
            ["log", "--oneline", "-n", "10"],
            ["diff", "--cached"],
            ["show", "HEAD:file.md"],
        ]

        work_tree = mock_git_operations.specs_dir

        for cmd in common_commands:
            with patch(
                "spec_cli.utils.security_validators.safe_relative_to"
            ) as mock_safe_relative_to:
                mock_safe_relative_to.return_value = Path("safe/path.txt")
                is_valid, error = validate_git_command(cmd, work_tree)
                assert is_valid is True, (
                    f"Command {cmd} should be valid but got error: {error}"
                )
                assert error is None

    def test_validate_dangerous_commands_are_blocked(self, mock_git_operations):
        """Test that dangerous commands that should never be used are blocked."""
        dangerous_commands = [
            ["reset", "--hard", "HEAD~1"],
            ["push", "origin", "main"],
            ["pull", "origin", "main"],
            ["rm", "-rf", "."],
            ["checkout", "-b", "new-branch"],
            ["rebase", "-i", "HEAD~3"],
            ["merge", "feature-branch"],
        ]

        work_tree = mock_git_operations.specs_dir

        for cmd in dangerous_commands:
            is_valid, error = validate_git_command(cmd, work_tree)
            assert is_valid is False, f"Dangerous command {cmd} should be blocked"
            assert f"Git command '{cmd[0]}' not allowed" in error

    @patch("spec_cli.utils.security_validators.safe_relative_to")
    def test_validate_file_path_security_with_specs_directory(
        self, mock_safe_relative_to, mock_git_operations
    ):
        """Test that file path validation works correctly with .specs directory structure."""
        mock_safe_relative_to.return_value = Path("docs/file.md")

        # Valid file paths within .specs directory
        valid_file_commands = [
            ["add", "docs/index.md"],
            ["add", "src/models/user.md", "src/models/history.md"],
            ["diff", "api/endpoints.md"],
            ["show", "HEAD:readme.md"],
        ]

        work_tree = mock_git_operations.specs_dir

        for cmd in valid_file_commands:
            is_valid, error = validate_git_command(cmd, work_tree)
            assert is_valid is True, f"Valid file command {cmd} should pass"
            assert error is None

    def test_validate_directory_traversal_prevention_with_specs_context(
        self, mock_git_operations
    ):
        """Test that directory traversal attacks are prevented in .specs context."""
        # Simulate directory traversal attempts that would escape .specs directory
        traversal_attacks = [
            ["add", "../../../etc/passwd"],
            ["add", "..\\..\\..\\windows\\system32\\config"],
            ["diff", "../.git/config"],
            ["show", "../../../../sensitive/file"],
        ]

        work_tree = mock_git_operations.specs_dir

        for cmd in traversal_attacks:
            is_valid, error = validate_git_command(cmd, work_tree)
            assert is_valid is False, f"Directory traversal {cmd} should be blocked"
            assert "outside work tree" in error

    def test_validate_git_operations_environment_setup_commands(
        self, mock_git_operations
    ):
        """Test validation of commands used during GitOperations initialization."""
        # Commands typically used during spec repository setup
        setup_commands = [
            ["init", "--bare"],  # Initialize bare repository
            ["status"],  # Check repository state
            ["log", "--oneline"],  # Check commit history
        ]

        for cmd in setup_commands:
            is_valid, error = validate_git_command(cmd)
            assert is_valid is True, f"Setup command {cmd} should be valid"
            assert error is None

    def test_validate_spec_file_operations_commands(self, mock_git_operations):
        """Test validation of commands used for spec file management."""
        # Commands used for managing .md files in .specs directory
        spec_file_commands = [
            ["add", "-f", "component.md"],  # Force add (bypasses .gitignore)
            ["commit", "-m", "Update component documentation"],
            ["diff", "component.md"],
            ["show", "HEAD:component.md"],
            ["log", "--oneline", "component.md"],
        ]

        work_tree = mock_git_operations.specs_dir

        with patch(
            "spec_cli.utils.security_validators.safe_relative_to"
        ) as mock_safe_relative_to:
            mock_safe_relative_to.return_value = Path("component.md")

            for cmd in spec_file_commands:
                is_valid, error = validate_git_command(cmd, work_tree)
                assert is_valid is True, f"Spec file command {cmd} should be valid"
                assert error is None

    def test_validate_command_completeness_against_allowed_list(self):
        """Test that all allowed commands are actually used by the spec system."""
        # Verify that our allowed commands list matches actual usage patterns
        # This test ensures we're not allowing unnecessary commands

        # Commands that should definitely be in the allowed list based on spec functionality
        required_commands = {
            "init",  # Repository initialization
            "add",  # Adding spec files
            "commit",  # Committing documentation changes
            "status",  # Checking repository state
            "log",  # Viewing documentation history
            "diff",  # Comparing documentation versions
            "show",  # Displaying specific documentation versions
        }

        assert required_commands.issubset(ALLOWED_GIT_COMMANDS), (
            f"Missing required commands: {required_commands - ALLOWED_GIT_COMMANDS}"
        )

        # Ensure we're not allowing too many commands (security principle of least privilege)
        assert len(ALLOWED_GIT_COMMANDS) <= 10, (
            f"Too many allowed commands ({len(ALLOWED_GIT_COMMANDS)}), consider reducing for security"
        )

    def test_validate_integration_with_real_file_structure(self, tmp_path):
        """Test validation against a realistic .specs directory structure."""
        # Create a realistic .specs directory structure
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        # Create nested directory structure like real spec usage
        (specs_dir / "src" / "models").mkdir(parents=True)
        (specs_dir / "docs" / "api").mkdir(parents=True)
        (specs_dir / "tests").mkdir()

        # Create some spec files
        (specs_dir / "src" / "models" / "index.md").write_text("# Models")
        (specs_dir / "docs" / "api" / "endpoints.md").write_text("# API")
        (specs_dir / "README.md").write_text("# Project Specs")

        # Test commands against this realistic structure
        realistic_commands = [
            ["add", "src/models/index.md"],
            ["add", "docs/api/endpoints.md", "README.md"],
            ["commit", "-m", "Add initial documentation"],
            ["diff", "src/models/index.md"],
            ["log", "--oneline", "docs/api/endpoints.md"],
        ]

        with patch(
            "spec_cli.utils.security_validators.safe_relative_to"
        ) as mock_safe_relative_to:
            mock_safe_relative_to.return_value = Path("valid/path.md")

            for cmd in realistic_commands:
                is_valid, error = validate_git_command(cmd, specs_dir)
                assert is_valid is True, f"Realistic command {cmd} should be valid"
                assert error is None

    def test_validate_error_handling_integration(self, mock_git_operations):
        """Test that validation errors integrate properly with GitOperations error handling."""
        # Test commands that should fail validation
        invalid_commands = [
            ([], "Empty git command"),
            (["push"], "Git command 'push' not allowed"),
            (["add", "../../../etc/passwd"], "outside work tree"),
        ]

        work_tree = mock_git_operations.specs_dir

        for cmd, expected_error_fragment in invalid_commands:
            is_valid, error = validate_git_command(cmd, work_tree if cmd else None)
            assert is_valid is False, f"Invalid command {cmd} should fail validation"
            assert expected_error_fragment in error, (
                f"Error message '{error}' should contain '{expected_error_fragment}'"
            )
