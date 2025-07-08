"""CLI context initialization utilities for dependency injection support."""

from pathlib import Path
from typing import Any

import click

from ..core.context import SpecContext
from ..core.context_bridge import debug_logger
from .error_utils import create_error_context


class CLISetupError(Exception):
    """Exception raised when CLI setup operations fail."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize CLISetupError with message and context.

        Args:
            message: Error message describing the CLI setup failure
            context: Optional context dictionary with additional error details
        """
        super().__init__(message)
        self.context = context or {}


def initialize_cli_context(root_path: Path | None = None) -> SpecContext:
    """Initialize SpecContext for CLI environment.

    Creates a properly configured SpecContext using the factory method
    from P1.2b implementation, suitable for CLI operations.

    Args:
        root_path: Root path for CLI operations (uses current directory if None)

    Returns:
        SpecContext instance configured for CLI environment

    Raises:
        CLISetupError: If context initialization fails
        TypeError: If root_path is not a Path or None

    Example:
        >>> from pathlib import Path
        >>> context = initialize_cli_context(Path("/project"))
        >>> assert context.settings.root_path == Path("/project")
    """
    if root_path is not None and not isinstance(root_path, Path):
        raise TypeError(f"Expected Path or None, got {type(root_path)}")

    try:
        # Use current directory if no root path provided
        if root_path is None:
            root_path = Path.cwd()

        debug_logger.log(
            "DEBUG",
            "Initializing CLI context",
            root_path=str(root_path),
            root_exists=root_path.exists(),
        )

        # Create CLI context using P1.2b factory method
        context = SpecContext.create_for_cli(root_path=root_path)

        debug_logger.log(
            "DEBUG",
            "CLI context initialized successfully",
            context_hash=context.get_context_hash()[:8],
            settings_root=str(context.settings.root_path),
        )

        return context

    except Exception as e:
        error_context = create_error_context(root_path or Path.cwd())
        error_context.update(
            {
                "operation": "cli_context_initialization",
                "root_path": str(root_path) if root_path else None,
                "error_type": type(e).__name__,
            }
        )
        raise CLISetupError(
            f"Failed to initialize CLI context: {e}", error_context
        ) from e


def setup_click_context_storage(
    click_ctx: click.Context, spec_ctx: SpecContext
) -> None:
    """Setup Click context storage for SpecContext.

    Integrates SpecContext with Click context using utilities from P2.1b
    Click integration implementation.

    Args:
        click_ctx: Click context object to store SpecContext in
        spec_ctx: SpecContext instance to integrate

    Raises:
        CLISetupError: If Click context setup fails
        TypeError: If arguments are not correct types

    Example:
        >>> import click
        >>> from spec_cli.core.context import SpecContext
        >>> ctx = click.Context(click.Command("test"))
        >>> spec_ctx = SpecContext.create_for_testing()
        >>> setup_click_context_storage(ctx, spec_ctx)
        >>> # SpecContext now accessible via Click context
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(spec_ctx, SpecContext):
        raise TypeError(f"Expected SpecContext, got {type(spec_ctx)}")

    try:
        # Import here to avoid circular imports
        from ..cli.context_integration import integrate_spec_context

        debug_logger.log(
            "DEBUG",
            "Setting up Click context storage",
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
            context_hash=spec_ctx.get_context_hash()[:8],
        )

        # Use P2.1b integration utilities
        integrate_spec_context(click_ctx, spec_ctx)

        debug_logger.log(
            "DEBUG",
            "Click context storage setup successfully",
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

    except Exception as e:
        error_context = {
            "operation": "click_context_storage_setup",
            "click_command": getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
            "context_hash": spec_ctx.get_context_hash()[:8],
            "error_type": type(e).__name__,
        }
        raise CLISetupError(
            f"Failed to setup Click context storage: {e}", error_context
        ) from e


def create_cli_app_with_context(root_path: Path | None = None) -> click.Group:
    """Create CLI application with integrated SpecContext setup.

    Creates a Click Group with proper SpecContext initialization and
    integration for all commands.

    Args:
        root_path: Root path for CLI operations (uses current directory if None)

    Returns:
        Click Group with integrated SpecContext support

    Raises:
        CLISetupError: If CLI app creation with context fails
        TypeError: If root_path is not a Path or None

    Example:
        >>> from pathlib import Path
        >>> app = create_cli_app_with_context(Path("/project"))
        >>> # App ready with SpecContext integration
    """
    if root_path is not None and not isinstance(root_path, Path):
        raise TypeError(f"Expected Path or None, got {type(root_path)}")

    try:
        # Initialize CLI context
        spec_context = initialize_cli_context(root_path)

        # Create Click group with context callback
        @click.group(
            invoke_without_command=True,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        @click.pass_context
        def cli_app(ctx: click.Context) -> None:
            """CLI application with integrated SpecContext."""
            # Setup context storage for all commands
            setup_click_context_storage(ctx, spec_context)

        debug_logger.log(
            "DEBUG",
            "CLI app with context created successfully",
            root_path=str(root_path) if root_path else "current_directory",
            context_hash=spec_context.get_context_hash()[:8],
        )

        return cli_app

    except Exception as e:
        error_context = create_error_context(root_path or Path.cwd())
        error_context.update(
            {
                "operation": "cli_app_creation_with_context",
                "root_path": str(root_path) if root_path else None,
                "error_type": type(e).__name__,
            }
        )
        raise CLISetupError(
            f"Failed to create CLI app with context: {e}", error_context
        ) from e


def validate_cli_context_setup(click_ctx: click.Context) -> dict[str, Any]:
    """Validate that CLI context is properly setup.

    Verifies that SpecContext is properly integrated and accessible
    through Click context.

    Args:
        click_ctx: Click context object to validate

    Returns:
        Validation results dictionary with setup status

    Raises:
        CLISetupError: If validation fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> result = validate_cli_context_setup(ctx)
        >>> print(result["spec_context_available"])  # True/False
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        # Import here to avoid circular imports
        from ..cli.context_integration import retrieve_spec_context

        debug_logger.log(
            "DEBUG",
            "Validating CLI context setup",
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

        # Check if SpecContext is available
        spec_context = retrieve_spec_context(click_ctx)
        context_available = spec_context is not None

        # Check if context has required dependencies
        dependencies_valid = False
        if spec_context:
            dependencies_valid = all(
                [
                    hasattr(spec_context, "settings") and spec_context.settings,
                    hasattr(spec_context, "console") and spec_context.console,
                    hasattr(spec_context, "progress") and spec_context.progress,
                ]
            )

        validation_result = {
            "spec_context_available": context_available,
            "dependencies_valid": dependencies_valid,
            "setup_complete": context_available and dependencies_valid,
            "context_hash": (
                spec_context.get_context_hash()[:8] if spec_context else None
            ),
        }

        debug_logger.log(
            "DEBUG",
            "CLI context validation completed",
            validation_result=validation_result,
        )

        return validation_result

    except Exception as e:
        error_context = {
            "operation": "cli_context_validation",
            "click_command": getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
            "error_type": type(e).__name__,
        }
        raise CLISetupError(
            f"Failed to validate CLI context setup: {e}", error_context
        ) from e
