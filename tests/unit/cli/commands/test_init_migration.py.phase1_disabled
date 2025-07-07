"""Tests for init command migration to context injection."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.init import init_command
from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)
from spec_cli.exceptions import SpecRepositoryError

# Test constants
DEFAULT_CURRENT_DIR = Path("/test/project")
DEFAULT_SUCCESS_MESSAGE = (
    "Spec repository initialized successfully!\n\n"
    "Created directories:\n"
    "  • .spec/     - Git repository for spec tracking\n"
    "  • .specs/    - Documentation directory\n\n"
    "Next steps:\n"
    "  • Run 'spec status' to check repository status\n"
    "  • Run 'spec gen <files>' to generate documentation"
)
DEFAULT_WARNING_MESSAGE = (
    "Spec repository is already initialized. Use --force to reinitialize."
)
FORCE_REINIT_MESSAGE = "Force reinitializing spec repository..."
NORMAL_INIT_MESSAGE = "Initializing spec repository..."


class TestInitCommandMigration:
    """Test init command migration with context injection."""

    @pytest.fixture
    def mock_spec_context(self):
        """Create mock SpecContext for testing."""
        mock_settings = Mock(spec=SpecSettingsInterface)
        mock_settings.debug_enabled = False

        mock_console = Mock(spec=SpecConsoleInterface)
        mock_progress = Mock(spec=SpecProgressInterface)

        return SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )

    @pytest.fixture
    def mock_console(self):
        """Create mock console for testing."""
        return Mock(spec=SpecConsoleInterface)

    @pytest.fixture
    def original_init_behavior(self):
        """Capture original init command behavior for comparison."""
        return Mock()

    def test_migrated_init_when_valid_context_then_executes_successfully(
        self, mock_spec_context
    ):
        """Test migrated init command executes successfully with valid context."""
        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_context,
        ):
            # Setup mocks
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo.initialize.return_value = None
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Mock context retrieval to return our test context
            mock_get_context.return_value = mock_spec_context

            # Execute command callback directly (bypass Click parameters)
            init_command.callback(False, False, False)

            # Verify repository operations
            mock_repo.is_initialized.assert_called()
            mock_repo.initialize.assert_called_once()

            # Verify console interactions
            mock_spec_context.console.print_message.assert_called_once_with(
                NORMAL_INIT_MESSAGE, "info"
            )
            mock_spec_context.console.print_success.assert_called_once_with(
                DEFAULT_SUCCESS_MESSAGE
            )

    def test_migrated_init_when_missing_context_then_raises_context_error(self):
        """Test migrated init command raises error when context is missing."""
        with pytest.raises(TypeError):
            # This should fail because context parameter is required
            init_command.callback(debug=False, verbose=False, force=False)  # type: ignore[call-arg]

    def test_migrated_init_when_invalid_context_then_raises_validation_error(self):
        """Test migrated init command raises error when context is invalid."""
        with pytest.raises((TypeError, AttributeError)):
            # This should fail because invalid context doesn't have required attributes
            init_command.callback(
                "invalid_context",  # type: ignore[arg-type]
                False,
                False,
                False,
            )

    def test_migrated_init_preserves_original_behavior_with_context_injection(
        self, mock_spec_context
    ):
        """Test migrated init preserves original behavior through context injection."""
        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
        ):
            # Setup repository already initialized scenario
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = True
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command without force
            init_command(
                context=mock_spec_context, debug=False, verbose=False, force=False
            )

            # Verify warning message displayed (preserves original behavior)
            mock_spec_context.console.print_warning.assert_called_once_with(
                DEFAULT_WARNING_MESSAGE
            )

            # Verify repository initialization not called
            mock_repo.initialize.assert_not_called()

    def test_migrated_init_maintains_click_command_attributes(self):
        """Test migrated init maintains Click command attributes."""
        # The init_command is now a Click Command object
        assert hasattr(init_command, "callback")
        assert hasattr(init_command, "params")
        assert hasattr(init_command, "name")

        # Verify the callback function has the right signature
        callback = init_command.callback
        assert hasattr(callback, "__name__")
        assert callback.__name__ == "init_command"

        # Verify docstring preserved in callback
        assert callback.__doc__ is not None
        assert "Initialize spec repository" in callback.__doc__

    def test_migrated_init_handles_initialization_errors_appropriately(
        self, mock_spec_context
    ):
        """Test migrated init handles repository initialization errors."""
        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            pytest.raises(Exception) as exc_info,
        ):
            # Setup repository to raise error
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo.initialize.side_effect = SpecRepositoryError("Init failed")
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command callback directly (bypass Click)
            init_command.callback(mock_spec_context, False, False, False)

        # Verify error handling
        assert "Repository initialization failed" in str(exc_info.value)

    def test_migrated_init_supports_existing_command_line_options(
        self, mock_spec_context
    ):
        """Test migrated init supports existing command line options."""
        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
        ):
            # Setup repository already initialized
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = True
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command callback with force flag directly (bypass Click)
            init_command.callback(mock_spec_context, False, False, True)

            # Verify force reinitialize message
            mock_spec_context.console.print_message.assert_called_once_with(
                FORCE_REINIT_MESSAGE, "info"
            )

            # Verify repository initialization called with force
            mock_repo.initialize.assert_called_once()

    def test_migrated_init_debug_logging_when_debug_enabled(self, mock_spec_context):
        """Test migrated init uses debug logging when debug mode enabled."""
        # Enable debug mode in context
        mock_spec_context.settings.debug_enabled = True

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.logging.debug.debug_logger") as mock_debug_logger,
        ):
            # Setup successful initialization
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command callback directly (bypass Click)
            init_command.callback(mock_spec_context, True, False, False)

            # Verify debug logging called
            mock_debug_logger.log.assert_called_with(
                "INFO",
                "Repository initialized",
                directory=str(DEFAULT_CURRENT_DIR),
                force=False,
            )

    def test_migrated_init_debug_logging_when_debug_disabled(self, mock_spec_context):
        """Test migrated init skips debug logging when debug mode disabled."""
        # Ensure debug mode disabled
        mock_spec_context.settings.debug_enabled = False

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.logging.debug.debug_logger") as mock_debug_logger,
        ):
            # Setup successful initialization
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command callback directly (bypass Click)
            init_command.callback(mock_spec_context, False, False, False)

            # Verify debug logging not called
            mock_debug_logger.log.assert_not_called()

    def test_migrated_init_error_logging_when_debug_enabled(self, mock_spec_context):
        """Test migrated init logs errors when debug mode enabled."""
        # Enable debug mode
        mock_spec_context.settings.debug_enabled = True

        with (
            patch("spec_cli.cli.commands.init.SpecGitRepository") as mock_repo_class,
            patch("spec_cli.cli.commands.init.Path.cwd") as mock_cwd,
            patch("spec_cli.cli.commands.init.debug_logger") as mock_debug_logger,
            pytest.raises(Exception),
        ):
            # Setup repository to raise generic error
            mock_repo = Mock()
            mock_repo.is_initialized.return_value = False
            mock_repo.initialize.side_effect = RuntimeError("Unexpected error")
            mock_repo_class.return_value = mock_repo
            mock_cwd.return_value = DEFAULT_CURRENT_DIR

            # Execute command callback directly (bypass Click)
            init_command.callback(mock_spec_context, True, False, False)

        # Verify error logging called
        mock_debug_logger.log.assert_called_with(
            "ERROR", "Initialization failed", error="Unexpected error"
        )
