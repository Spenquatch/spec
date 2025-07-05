"""Unit tests for CLI setup utilities functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.core.context import SpecContext, SpecFactoryError
from spec_cli.utils.cli_setup_utils import (
    CLISetupError,
    create_cli_app_with_context,
    initialize_cli_context,
    setup_click_context_storage,
    validate_cli_context_setup,
)


class TestInitializeCLIContext:
    """Test initialize_cli_context function."""

    def test_initialize_cli_context_when_valid_path_then_returns_context(
        self, tmp_path: Path
    ) -> None:
        """Test initialize_cli_context returns SpecContext with valid path."""
        # Setup: Mock SpecContext.create_for_cli
        with patch(
            "spec_cli.utils.cli_setup_utils.SpecContext.create_for_cli"
        ) as mock_create:
            mock_context = Mock(spec=SpecContext)
            mock_context.get_context_hash.return_value = "test_hash_12345678"
            mock_context.settings = Mock()
            mock_context.settings.root_path = tmp_path
            mock_create.return_value = mock_context

            # Action: Initialize CLI context
            result = initialize_cli_context(tmp_path)

        # Assert: Context created and returned
        assert result == mock_context
        mock_create.assert_called_once_with(root_path=tmp_path)

    def test_initialize_cli_context_when_none_path_then_uses_current_directory(
        self,
    ) -> None:
        """Test initialize_cli_context uses current directory when path is None."""
        # Setup: Mock SpecContext.create_for_cli and Path.cwd
        with patch(
            "spec_cli.utils.cli_setup_utils.SpecContext.create_for_cli"
        ) as mock_create:
            mock_context = Mock(spec=SpecContext)
            mock_context.get_context_hash.return_value = "test_hash_12345678"
            mock_context.settings = Mock()
            mock_context.settings.root_path = Path("/test/current")
            mock_create.return_value = mock_context

            with patch("spec_cli.utils.cli_setup_utils.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/test/current")

                # Action: Initialize CLI context with None
                result = initialize_cli_context(None)

        # Assert: Used current directory
        assert result == mock_context
        mock_create.assert_called_once_with(root_path=Path("/test/current"))

    def test_initialize_cli_context_when_invalid_path_then_raises_initialization_error(
        self,
    ) -> None:
        """Test initialize_cli_context raises error with invalid path type."""
        # Action & Assert: Invalid path type raises TypeError
        with pytest.raises(TypeError, match="Expected Path or None"):
            initialize_cli_context("invalid_path")  # type: ignore[arg-type]

    def test_initialize_cli_context_when_factory_fails_then_raises_setup_error(
        self, tmp_path: Path
    ) -> None:
        """Test initialize_cli_context raises CLISetupError when factory fails."""
        # Setup: Mock SpecContext.create_for_cli to raise exception
        with patch(
            "spec_cli.utils.cli_setup_utils.SpecContext.create_for_cli"
        ) as mock_create:
            mock_create.side_effect = SpecFactoryError("Factory failed")

            # Action & Assert: Raises CLISetupError
            with pytest.raises(CLISetupError, match="Failed to initialize CLI context"):
                initialize_cli_context(tmp_path)


class TestSetupClickContextStorage:
    """Test setup_click_context_storage function."""

    def test_setup_click_context_storage_when_valid_contexts_then_stores_successfully(
        self,
    ) -> None:
        """Test setup_click_context_storage stores SpecContext successfully."""
        # Setup: Create mock contexts
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = "test"

        spec_ctx = Mock(spec=SpecContext)
        spec_ctx.get_context_hash.return_value = "test_hash_12345678"

        # Mock the integration function
        with patch(
            "spec_cli.cli.context_integration.integrate_spec_context"
        ) as mock_integrate:
            # Action: Setup Click context storage
            setup_click_context_storage(click_ctx, spec_ctx)

        # Assert: Integration was called
        mock_integrate.assert_called_once_with(click_ctx, spec_ctx)

    def test_setup_click_context_storage_when_invalid_click_context_then_raises_type_error(
        self,
    ) -> None:
        """Test setup_click_context_storage raises TypeError with invalid Click context."""
        # Setup: Create valid SpecContext and invalid Click context
        spec_ctx = Mock(spec=SpecContext)

        # Action & Assert: Invalid Click context raises TypeError
        with pytest.raises(TypeError, match="Expected click.Context"):
            setup_click_context_storage("invalid", spec_ctx)  # type: ignore[arg-type]

    def test_setup_click_context_storage_when_invalid_spec_context_then_raises_type_error(
        self,
    ) -> None:
        """Test setup_click_context_storage raises TypeError with invalid SpecContext."""
        # Setup: Create valid Click context and invalid SpecContext
        click_ctx = Mock(spec=click.Context)

        # Action & Assert: Invalid SpecContext raises TypeError
        with pytest.raises(TypeError, match="Expected SpecContext"):
            setup_click_context_storage(click_ctx, "invalid")  # type: ignore[arg-type]

    def test_setup_click_context_storage_when_integration_fails_then_raises_setup_error(
        self,
    ) -> None:
        """Test setup_click_context_storage raises CLISetupError when integration fails."""
        # Setup: Create mock contexts
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = "test"

        spec_ctx = Mock(spec=SpecContext)
        spec_ctx.get_context_hash.return_value = "test_hash_12345678"

        # Mock integration to fail
        with patch(
            "spec_cli.cli.context_integration.integrate_spec_context"
        ) as mock_integrate:
            mock_integrate.side_effect = Exception("Integration failed")

            # Action & Assert: Raises CLISetupError
            with pytest.raises(
                CLISetupError, match="Failed to setup Click context storage"
            ):
                setup_click_context_storage(click_ctx, spec_ctx)


class TestCreateCLIAppWithContext:
    """Test create_cli_app_with_context function."""

    def test_create_cli_app_with_context_when_valid_path_then_returns_click_group(
        self, tmp_path: Path
    ) -> None:
        """Test create_cli_app_with_context returns Click Group with valid path."""
        # Setup: Mock context initialization
        with patch(
            "spec_cli.utils.cli_setup_utils.initialize_cli_context"
        ) as mock_init:
            mock_context = Mock(spec=SpecContext)
            mock_context.get_context_hash.return_value = "test_hash_12345678"
            mock_init.return_value = mock_context

            # Action: Create CLI app with context
            result = create_cli_app_with_context(tmp_path)

        # Assert: Returns Click Group
        assert isinstance(result, click.Group)
        mock_init.assert_called_once_with(tmp_path)

    def test_create_cli_app_with_context_when_none_path_then_uses_current_directory(
        self,
    ) -> None:
        """Test create_cli_app_with_context uses current directory when path is None."""
        # Setup: Mock context initialization and Path.cwd
        with patch(
            "spec_cli.utils.cli_setup_utils.initialize_cli_context"
        ) as mock_init:
            mock_context = Mock(spec=SpecContext)
            mock_context.get_context_hash.return_value = "test_hash_12345678"
            mock_init.return_value = mock_context

            with patch("spec_cli.utils.cli_setup_utils.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/test/current")

                # Action: Create CLI app with None path
                result = create_cli_app_with_context(None)

        # Assert: Returns Click Group and initialize was called
        assert isinstance(result, click.Group)
        mock_init.assert_called_once_with(None)

    def test_create_cli_app_with_context_when_invalid_path_then_raises_type_error(
        self,
    ) -> None:
        """Test create_cli_app_with_context raises TypeError with invalid path."""
        # Action & Assert: Invalid path type raises TypeError
        with pytest.raises(TypeError, match="Expected Path or None"):
            create_cli_app_with_context("invalid")  # type: ignore[arg-type]

    def test_create_cli_app_with_context_when_initialization_fails_then_raises_setup_error(
        self, tmp_path: Path
    ) -> None:
        """Test create_cli_app_with_context raises CLISetupError when initialization fails."""
        # Setup: Mock initialization to fail
        with patch(
            "spec_cli.utils.cli_setup_utils.initialize_cli_context"
        ) as mock_init:
            mock_init.side_effect = CLISetupError("Initialization failed")

            # Action & Assert: Raises CLISetupError
            with pytest.raises(
                CLISetupError, match="Failed to create CLI app with context"
            ):
                create_cli_app_with_context(tmp_path)


class TestValidateCLIContextSetup:
    """Test validate_cli_context_setup function."""

    def test_validate_cli_context_setup_when_context_available_then_returns_valid_result(
        self,
    ) -> None:
        """Test validate_cli_context_setup returns valid result when context is available."""
        # Setup: Create mock Click context with SpecContext
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = "test"

        mock_spec_context = Mock(spec=SpecContext)
        mock_spec_context.settings = Mock()
        mock_spec_context.console = Mock()
        mock_spec_context.progress = Mock()
        mock_spec_context.get_context_hash.return_value = "test_hash_12345678"

        # Mock retrieve_spec_context
        with patch(
            "spec_cli.cli.context_integration.retrieve_spec_context"
        ) as mock_retrieve:
            mock_retrieve.return_value = mock_spec_context

            # Action: Validate CLI context setup
            result = validate_cli_context_setup(click_ctx)

        # Assert: Returns valid setup result
        assert result["spec_context_available"] is True
        assert result["dependencies_valid"] is True
        assert result["setup_complete"] is True
        assert result["context_hash"] == "test_has"

    def test_validate_cli_context_setup_when_context_missing_then_returns_invalid_result(
        self,
    ) -> None:
        """Test validate_cli_context_setup returns invalid result when context is missing."""
        # Setup: Create mock Click context without SpecContext
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = "test"

        # Mock retrieve_spec_context to return None
        with patch(
            "spec_cli.cli.context_integration.retrieve_spec_context"
        ) as mock_retrieve:
            mock_retrieve.return_value = None

            # Action: Validate CLI context setup
            result = validate_cli_context_setup(click_ctx)

        # Assert: Returns invalid setup result
        assert result["spec_context_available"] is False
        assert result["dependencies_valid"] is False
        assert result["setup_complete"] is False
        assert result["context_hash"] is None

    def test_validate_cli_context_setup_when_invalid_click_context_then_raises_type_error(
        self,
    ) -> None:
        """Test validate_cli_context_setup raises TypeError with invalid Click context."""
        # Action & Assert: Invalid Click context raises TypeError
        with pytest.raises(TypeError, match="Expected click.Context"):
            validate_cli_context_setup("invalid")  # type: ignore[arg-type]

    def test_validate_cli_context_setup_when_validation_fails_then_raises_setup_error(
        self,
    ) -> None:
        """Test validate_cli_context_setup raises CLISetupError when validation fails."""
        # Setup: Create mock Click context
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = "test"

        # Mock retrieve_spec_context to fail
        with patch(
            "spec_cli.cli.context_integration.retrieve_spec_context"
        ) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Validation failed")

            # Action & Assert: Raises CLISetupError
            with pytest.raises(
                CLISetupError, match="Failed to validate CLI context setup"
            ):
                validate_cli_context_setup(click_ctx)
