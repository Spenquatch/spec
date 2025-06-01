"""Spec init command implementation."""

from pathlib import Path

import click

from ...exceptions import SpecRepositoryError
from ...git.repository import SpecGitRepository
from ...logging.debug import debug_logger
from ..options import force_option, spec_command
from ..utils import echo_status


@spec_command()
@force_option
def init_command(debug: bool, verbose: bool, force: bool) -> None:
    """Initialize spec repository.

    Creates a new spec repository in the current directory with proper
    directory structure and Git configuration.
    """

    try:
        # Create repository instance
        repo = SpecGitRepository()
        current_dir = Path.cwd()

        # Check if already initialized
        if repo.is_initialized() and not force:
            echo_status(
                "Spec repository is already initialized. Use --force to reinitialize.",
                "warning",
            )
            return

        if force and repo.is_initialized():
            echo_status("Force reinitializing spec repository...", "info")
        else:
            echo_status("Initializing spec repository...", "info")

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

        echo_status(success_msg, "success")

        debug_logger.log(
            "INFO", "Repository initialized", directory=str(current_dir), force=force
        )

    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository initialization failed: {e}") from e
    except Exception as e:
        debug_logger.log("ERROR", "Initialization failed", error=str(e))
        raise click.ClickException(
            f"Unexpected error during initialization: {e}"
        ) from e
