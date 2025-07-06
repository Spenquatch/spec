"""Unit tests for commit command context injection migration."""

from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.cli.commands.commit import commit_command
from spec_cli.core.context import SpecContext
from spec_cli.exceptions import SpecRepositoryError

# Test constants
TEST_COMMIT_MESSAGE = "Test commit message"
TEST_COMMIT_HASH = "abc12345"
TEST_FILE_PATH = ".specs/test.md"
EXPECTED_CONTEXT_TYPES = ["SpecContext", "Mock"]


# Fixtures
@pytest.fixture
def mock_context():
    """Create mock SpecContext for testing."""
    context = Mock(spec=SpecContext)
    context.console = Mock()
    context.settings = Mock()
    context.progress = Mock()

    # Configure console methods
    context.console.print_message = Mock()
    context.console.print_error = Mock()
    context.console.print_success = Mock()
    context.console.print_warning = Mock()

    return context


@pytest.fixture
def mock_repo():
    """Create mock repository for testing."""
    repo = Mock()
    repo.get_git_status.return_value = {
        "staged": [TEST_FILE_PATH],
        "modified": [],
        "untracked": [],
        "deleted": [],
    }
    repo.commit.return_value = TEST_COMMIT_HASH
    repo.amend_commit.return_value = TEST_COMMIT_HASH
    return repo


@pytest.fixture
def mock_repo_empty():
    """Create mock repository with no staged changes."""
    repo = Mock()
    repo.get_git_status.return_value = {
        "staged": [],
        "modified": [],
        "untracked": [],
        "deleted": [],
    }
    return repo


@pytest.fixture
def mock_repo_modified():
    """Create mock repository with modified files."""
    repo = Mock()
    repo.get_git_status.return_value = {
        "staged": [],
        "modified": [TEST_FILE_PATH],
        "untracked": [],
        "deleted": [],
    }
    return repo


class TestCommitCommandContextInjection:
    """Test context injection decorator application."""

    def test_commit_command_when_context_decorator_applied_then_receives_context_parameter(
        self, mock_context, mock_repo
    ):
        """Test that commit command receives context parameter through decorator."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            # Execute command callback directly (bypass Click parameters)
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify context was used (console methods called)
            assert mock_context.console.print_success.called
            mock_context.console.print_success.assert_called_with(
                f"Created commit: {TEST_COMMIT_HASH[:8]}"
            )

    def test_commit_command_when_using_context_console_then_accesses_console_from_context(
        self, mock_context, mock_repo
    ):
        """Test that commit command accesses console from context."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify console methods called from context
            mock_context.console.print_success.assert_called_once_with(
                f"Created commit: {TEST_COMMIT_HASH[:8]}"
            )

    def test_commit_command_when_singleton_replaced_then_no_singleton_references_remain(
        self, mock_context, mock_repo
    ):
        """Test that singleton references are replaced with context attribute access."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify context console was used instead of singleton
            assert mock_context.console.print_success.called
            assert mock_context.console.print_message.called

    def test_commit_command_when_migrated_signature_then_maintains_click_compatibility(
        self, mock_context, mock_repo
    ):
        """Test that migrated command signature maintains Click compatibility."""
        import inspect

        # Get function signature of the actual callback
        sig = inspect.signature(commit_command.callback)
        params = list(sig.parameters.keys())

        # Verify context is first parameter
        assert params[0] == "context"

        # Verify all original Click parameters preserved
        expected_params = [
            "context",
            "debug",
            "verbose",
            "message",
            "all",
            "amend",
            "dry_run",
        ]
        assert params == expected_params

        # Verify parameter types
        assert sig.parameters["context"].annotation == SpecContext

    def test_commit_command_when_behavior_validation_then_identical_to_original_behavior(
        self, mock_context, mock_repo
    ):
        """Test that migrated command maintains identical behavior."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            # Test successful commit
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify repository methods called
            mock_repo.get_git_status.assert_called()
            mock_repo.commit.assert_called_once_with(TEST_COMMIT_MESSAGE)

            # Verify success message displayed
            mock_context.console.print_success.assert_called_with(
                f"Created commit: {TEST_COMMIT_HASH[:8]}"
            )

    def test_commit_command_when_context_injection_error_then_raises_migration_error(
        self, mock_repo
    ):
        """Test that context injection errors are handled properly."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            # Test with invalid context type
            with pytest.raises(TypeError):
                commit_command.callback(
                    False, False, TEST_COMMIT_MESSAGE, False, False, False
                )


class TestCommitCommandContextBehavior:
    """Test commit command behavior with context injection."""

    def test_commit_command_when_no_staged_files_then_uses_context_console_warning(
        self, mock_context, mock_repo_empty
    ):
        """Test warning message uses context console."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo_empty,
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify context console used for warning
            mock_context.console.print_message.assert_called_with(
                "No changes to commit. Working directory clean.", "info"
            )

    def test_commit_command_when_modified_files_available_then_uses_context_console_warning(
        self, mock_context, mock_repo_modified
    ):
        """Test warning about unstaged files uses context console."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo_modified,
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify context console used for warning
            mock_context.console.print_warning.assert_called_with(
                "No changes staged for commit. Use 'spec add' to stage changes "
                "or use --all to stage all modified files."
            )

    def test_commit_command_when_dry_run_then_uses_context_console_info(
        self, mock_context, mock_repo
    ):
        """Test dry run message uses context console."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, True
            )  # dry_run=True

            # Verify context console used for dry run message
            mock_context.console.print_message.assert_called_with(
                "This is a dry run. No commit would be created.", "info"
            )

    def test_commit_command_when_amend_commit_then_uses_context_console_success(
        self, mock_context, mock_repo
    ):
        """Test amend commit success message uses context console."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, True, False
            )  # amend=True

            # Verify amend commit method called
            mock_repo.amend_commit.assert_called_once_with(TEST_COMMIT_MESSAGE)

            # Verify context console used for success message
            mock_context.console.print_success.assert_called_with(
                f"Amended commit: {TEST_COMMIT_HASH[:8]}"
            )

    def test_commit_command_when_user_cancels_then_uses_context_console_info(
        self, mock_context, mock_repo
    ):
        """Test commit cancellation message uses context console."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=False
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, False, False, False
            )

            # Verify context console used for cancellation message
            mock_context.console.print_message.assert_called_with(
                "Commit cancelled", "info"
            )

    def test_commit_command_when_auto_stage_all_then_uses_context_console_info(
        self, mock_context, mock_repo_modified
    ):
        """Test auto-stage message uses context console."""
        # Configure repo to return staged files after staging
        mock_repo_modified.get_git_status.side_effect = [
            {  # First call - before staging
                "staged": [],
                "modified": [TEST_FILE_PATH],
                "untracked": [],
                "deleted": [],
            },
            {  # Second call - after staging
                "staged": [TEST_FILE_PATH],
                "modified": [],
                "untracked": [],
                "deleted": [],
            },
        ]

        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo_modified,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            commit_command.callback(
                False, False, TEST_COMMIT_MESSAGE, True, False, False
            )  # all=True

            # Verify staging attempted
            mock_repo_modified.add_files.assert_called_with([TEST_FILE_PATH])

            # Verify context console used for auto-stage message
            # Note: The message is called within _auto_stage_changes helper
            assert mock_context.console.print_message.called

    def test_commit_command_when_error_occurs_then_maintains_error_handling(
        self, mock_context, mock_repo
    ):
        """Test that error handling is maintained with context injection."""
        # Configure repo to raise an error
        mock_repo.commit.side_effect = SpecRepositoryError("Test error")

        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=mock_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger") as mock_debug,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click",
                return_value=mock_context,
            ),
        ):
            # Verify error is properly raised
            with pytest.raises(click.ClickException) as exc_info:
                commit_command.callback(
                    False, False, TEST_COMMIT_MESSAGE, False, False, False
                )

            # Verify error message format
            assert "Commit failed:" in str(exc_info.value)

            # Verify debug logging occurred
            mock_debug.log.assert_called_with(
                "ERROR", "Commit command failed", error="Test error"
            )
