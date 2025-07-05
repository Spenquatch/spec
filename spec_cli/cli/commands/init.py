"""Spec init command implementation."""

from pathlib import Path

import click

from ...core.context import SpecContext
from ...exceptions import SpecRepositoryError
from ...git.repository import SpecGitRepository
from ..decorators import context_injection
from ..options import force_option, spec_command


@spec_command()
@force_option
@context_injection
def init_command(context: SpecContext, debug: bool, verbose: bool, force: bool) -> None:
    """Initialize spec repository.

    Creates a new spec repository in the current directory with proper
    directory structure and Git configuration.

    Args:
        context: SpecContext with settings, console, and progress dependencies
        debug: Debug mode flag
        verbose: Verbose mode flag
        force: Force reinitialize flag
    """
    try:
        # Create repository instance
        repo = SpecGitRepository()
        current_dir = Path.cwd()

        # Check if already initialized
        if repo.is_initialized() and not force:
            context.console.print_warning(
                "Spec repository is already initialized. Use --force to reinitialize."
            )
            return

        if force and repo.is_initialized():
            context.console.print_message(
                "Force reinitializing spec repository...", "info"
            )
        else:
            context.console.print_message("Initializing spec repository...", "info")

        # Initialize repository
        repo.initialize()

        # Verify initialization
        if not repo.is_initialized():
            raise SpecRepositoryError("Repository initialization failed")

        # Display success message
        success_msg = (
            "Spec repository initialized successfully!\n\n"
            "Created directories:\n"
            "  • .spec/     - Git repository for spec tracking\n"
            "  • .specs/    - Documentation directory\n\n"
            "Next steps:\n"
            "  • Run 'spec status' to check repository status\n"
            "  • Run 'spec gen <files>' to generate documentation"
        )

        context.console.print_success(success_msg)

        # Log through context if debug mode enabled
        if context.settings.debug_enabled:
            from ...logging.debug import debug_logger

            debug_logger.log(
                "INFO",
                "Repository initialized",
                directory=str(current_dir),
                force=force,
            )

    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository initialization failed: {e}") from e
    except Exception as e:
        if context.settings.debug_enabled:
            from ...logging.debug import debug_logger

            debug_logger.log("ERROR", "Initialization failed", error=str(e))
        raise click.ClickException(
            f"Unexpected error during initialization: {e}"
        ) from e
