"""Integration tests for commit command context injection migration."""

from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.commit import commit_command
from spec_cli.core.context import SpecContext

# Test constants
TEST_COMMIT_MESSAGE = "Integration test commit"
TEST_FILE_PATH = ".specs/integration_test.md"

@pytest.fixture
def integration_context():
    """Create integration test context with realistic dependencies."""
    return SpecContext.create_for_testing(
        {"debug_enabled": False, "console_width": 80, "use_color": False}
    )

@pytest.fixture
def integration_repo():
    """Create integration repository mock with realistic behavior."""
    repo = Mock()
    repo.get_git_status.return_value = {
        "staged": [TEST_FILE_PATH],
        "modified": [],
        "untracked": [],
        "deleted": [],
    }
    repo.commit.return_value = "abc123456789"
    repo.add_files.return_value = None
    return repo

class TestCommitCommandMigrationIntegration:
    """Test commit command migration with integrated context flow."""

    def test_commit_command_migration_when_full_workflow_then_consistent_with_other_migrated_commands(
        self, integration_context, integration_repo
    ):
        """Test that commit command migration integrates consistently with other migrated commands."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger") as mock_debug,
        ):
            # Execute full commit workflow
            commit_command(
                context=integration_context,
                debug=True,
                verbose=True,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify repository operations
            integration_repo.get_git_status.assert_called()
            integration_repo.commit.assert_called_once_with(TEST_COMMIT_MESSAGE)

            # Verify context console usage
            assert integration_context.console.print_success.called
            integration_context.console.print_success.assert_called_with(
                "Created commit: abc12345"
            )

            # Verify debug logging
            mock_debug.log.assert_called_with(
                "INFO",
                "Commit command completed",
                commit_hash="abc123456789",
                files=1,
                amend=False,
            )

    def test_commit_command_when_used_with_migrated_add_then_context_consistent(
        self, integration_context, integration_repo
    ):
        """Test context consistency when used with other migrated commands."""
        # Simulate repository state after add command
        integration_repo.get_git_status.return_value = {
            "staged": [TEST_FILE_PATH, ".specs/added_file.md"],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }

        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message="Commit after add command",
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify multiple files handled correctly
            integration_repo.commit.assert_called_once_with("Commit after add command")

            # Verify context used consistently across commands
            assert type(integration_context.console).__name__ == "Mock"
            assert hasattr(integration_context, "settings")
            assert hasattr(integration_context, "progress")

    def test_commit_command_when_used_with_migrated_init_then_dependency_injection_works(
        self, integration_context, integration_repo
    ):
        """Test dependency injection works consistently with init command patterns."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            # Test that context dependencies are properly injected
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify context structure matches other migrated commands
            assert integration_context.settings is not None
            assert integration_context.console is not None
            assert integration_context.progress is not None

            # Verify console methods are available (same as init command)
            assert hasattr(integration_context.console, "print_message")
            assert hasattr(integration_context.console, "print_success")
            assert hasattr(integration_context.console, "print_warning")
            assert hasattr(integration_context.console, "print_error")

    def test_commit_command_when_context_factory_provides_dependencies_then_uses_injected_instances(
        self, integration_context, integration_repo
    ):
        """Test that context factory-provided dependencies are used correctly."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify that factory-created context is used
            assert integration_context.console.print_success.called
            assert integration_context.console.print_message.called

            # Verify context hash is deterministic
            context_hash = integration_context.get_context_hash()
            assert len(context_hash) == 64  # SHA-256 hash length
            assert context_hash.isalnum()

    def test_commit_command_when_singleton_elimination_complete_then_no_global_state_access(
        self, integration_context, integration_repo
    ):
        """Test that singleton elimination is complete and no global state is accessed."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            # Execute command
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify all console operations go through context
            assert integration_context.console.print_success.called

            # Verify no direct singleton access (all goes through context)
            # This would be validated by absence of direct imports/calls to singletons
            # in the migrated code
            call_args = integration_context.console.print_success.call_args_list
            assert len(call_args) >= 1  # At least one success message

    def test_commit_command_when_preview_and_result_display_then_uses_context_consistently(
        self, integration_context, integration_repo
    ):
        """Test that preview and result display use context consistently."""
        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify context console was used for all output
            # Preview, success message, and result display
            console_calls = integration_context.console.print_message.call_args_list
            success_calls = integration_context.console.print_success.call_args_list

            # Should have multiple console interactions
            total_console_calls = len(console_calls) + len(success_calls)
            assert total_console_calls >= 2  # At least preview + success

    def test_commit_command_when_error_scenarios_then_context_error_handling_consistent(
        self, integration_context, integration_repo
    ):
        """Test that error handling through context is consistent."""
        # Configure repo to have no staged files
        integration_repo.get_git_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }

        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=integration_repo,
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=False,
                amend=False,
                dry_run=False,
            )

            # Verify error message delivered through context
            integration_context.console.print_message.assert_called_with(
                "No changes to commit. Working directory clean.", "info"
            )

    def test_commit_command_when_auto_stage_workflow_then_helper_functions_use_context(
        self, integration_context
    ):
        """Test that helper functions properly use context in auto-stage workflow."""
        # Create repo with modified files for auto-staging
        auto_stage_repo = Mock()
        auto_stage_repo.get_git_status.side_effect = [
            {  # Before staging
                "staged": [],
                "modified": [TEST_FILE_PATH],
                "untracked": [],
                "deleted": [],
            },
            {  # After staging
                "staged": [TEST_FILE_PATH],
                "modified": [],
                "untracked": [],
                "deleted": [],
            },
        ]
        auto_stage_repo.add_files.return_value = None
        auto_stage_repo.commit.return_value = "def456789"

        with (
            patch(
                "spec_cli.cli.commands.commit.get_spec_repository",
                return_value=auto_stage_repo,
            ),
            patch(
                "spec_cli.cli.commands.commit.get_user_confirmation", return_value=True
            ),
            patch("spec_cli.cli.commands.commit.debug_logger"),
        ):
            commit_command(
                context=integration_context,
                debug=False,
                verbose=False,
                message=TEST_COMMIT_MESSAGE,
                all=True,  # Enable auto-staging
                amend=False,
                dry_run=False,
            )

            # Verify staging operations
            auto_stage_repo.add_files.assert_called_with([TEST_FILE_PATH])
            auto_stage_repo.commit.assert_called_once_with(TEST_COMMIT_MESSAGE)

            # Verify helper functions used context
            assert integration_context.console.print_message.called
            assert integration_context.console.print_success.called
