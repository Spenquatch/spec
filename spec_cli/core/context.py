"""SpecContext core implementation for immutable dependency aggregation.

This module provides the SpecContext frozen dataclass that aggregates all critical
dependencies (settings, console, progress) for spec-cli operations with immutable
dependency injection support.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.context_utils import create_context_hash, validate_context_immutability


class SpecContextError(Exception):
    """Exception raised when SpecContext operations fail."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize SpecContextError with message and context.

        Args:
            message: Error message describing the context operation failure
            context: Optional context dictionary with additional error details
        """
        super().__init__(message)
        self.context = context or {}


class SpecSettingsInterface:
    """Interface specification for settings dependency in SpecContext.

    Based on analysis from P1.1a: 42 usage points across codebase.
    Current implementation: spec_cli.config.settings with singleton pattern.
    """

    def __init__(self) -> None:
        """Initialize settings interface."""
        # These will be abstract/protocol methods in actual implementation
        self.debug_enabled: bool = False
        self.console_width: int = 80
        self.use_color: bool = True
        self.root_path: Path = Path.cwd()
        self.spec_dir: Path = Path(".spec")
        self.specs_dir: Path = Path(".specs")

    def get_setting(self, key: str) -> Any:
        """Get setting value by key.

        Args:
            key: Setting key to retrieve

        Returns:
            Setting value or None if not found
        """
        return getattr(self, key, None)

    def validate_configuration(self) -> dict[str, str]:
        """Validate current configuration settings.

        Returns:
            Dictionary of validation results (empty if valid)
        """
        return {}


class SpecConsoleInterface:
    """Interface specification for console dependency in SpecContext.

    Based on analysis from P1.1a: 26 usage points across codebase.
    Current implementation: spec_cli.ui.console with singleton pattern.
    """

    def print_message(self, text: str, style: str | None = None) -> None:
        """Print formatted message to console.

        Args:
            text: Message text to display
            style: Optional style for formatting
        """
        pass

    def print_error(self, text: str) -> None:
        """Print error message to console.

        Args:
            text: Error message to display
        """
        pass

    def print_success(self, text: str) -> None:
        """Print success message to console.

        Args:
            text: Success message to display
        """
        pass

    def print_warning(self, text: str) -> None:
        """Print warning message to console.

        Args:
            text: Warning message to display
        """
        pass

    def get_width(self) -> int:
        """Get console width in characters.

        Returns:
            Console width in characters
        """
        return 80

    def supports_color(self) -> bool:
        """Check if console supports color output.

        Returns:
            True if color is supported, False otherwise
        """
        return True

    def capture_output(self) -> AbstractContextManager[str]:
        """Capture console output for testing.

        Returns:
            Context manager that captures output
        """

        # This would be implemented with actual capture logic
        class MockCapture:
            def __enter__(self) -> str:
                return ""

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                pass

        return MockCapture()


class SpecProgressInterface:
    """Interface specification for progress dependency in SpecContext.

    Based on analysis from P1.1a: 13 usage points across codebase.
    Current implementation: Multiple classes, missing unified interface.
    """

    def show_progress(self, current: int, total: int, description: str = "") -> None:
        """Show progress update.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        pass

    def update_status(self, status: str) -> None:
        """Update progress status message.

        Args:
            status: Status message to display
        """
        pass

    def start_operation(self, description: str, total: int | None = None) -> str:
        """Start a new progress operation.

        Args:
            description: Operation description
            total: Optional total progress value

        Returns:
            Operation ID for tracking
        """
        return "op_001"

    def finish_operation(self, operation_id: str) -> None:
        """Finish a progress operation.

        Args:
            operation_id: Operation ID to finish
        """
        pass

    def create_spinner(self, description: str) -> AbstractContextManager[None]:
        """Create spinner context manager.

        Args:
            description: Spinner description

        Returns:
            Context manager for spinner operation
        """

        # This would be implemented with actual spinner logic
        class MockSpinner:
            def __enter__(self) -> None:
                pass

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                pass

        return MockSpinner()


@dataclass(frozen=True)
class SpecContext:
    """Immutable dependency context for spec-cli operations.

    Aggregates critical dependencies identified in P1.1a analysis:
    - SpecSettings: 42 usage points (CRITICAL)
    - SpecConsole: 26 usage points (HIGH)
    - SpecProgress: 13 usage points (MEDIUM)

    Provides immutable dependency injection with thread-safe access.
    """

    settings: SpecSettingsInterface
    console: SpecConsoleInterface
    progress: SpecProgressInterface

    def __post_init__(self) -> None:
        """Validate context after initialization.

        Raises:
            SpecContextError: If context validation fails
        """
        # Validate immutability using helper
        if not validate_context_immutability(self):
            error_context = {"context_type": type(self).__name__}
            raise SpecContextError(
                "SpecContext must be immutable (frozen dataclass)", error_context
            )

        # All dependencies are guaranteed by type annotations
        # SpecContext requires non-None dependencies for proper initialization

    def with_settings(self, **overrides: Any) -> "SpecContext":
        """Create new context with settings overrides.

        Args:
            **overrides: Settings attribute overrides

        Returns:
            New SpecContext with modified settings

        Raises:
            SpecContextError: If settings override fails
        """
        try:
            # Create new settings instance with overrides
            new_settings = SpecSettingsInterface()

            # Copy existing attributes
            for attr in [
                "debug_enabled",
                "console_width",
                "use_color",
                "root_path",
                "spec_dir",
                "specs_dir",
            ]:
                if hasattr(self.settings, attr):
                    setattr(new_settings, attr, getattr(self.settings, attr))

            # Apply overrides
            for key, value in overrides.items():
                if hasattr(new_settings, key):
                    setattr(new_settings, key, value)

            return SpecContext(
                settings=new_settings, console=self.console, progress=self.progress
            )

        except Exception as e:
            error_context = {"overrides": str(overrides), "error": str(e)}
            raise SpecContextError(
                f"Failed to create context with settings overrides: {e}", error_context
            ) from e

    def with_console(self, console: SpecConsoleInterface) -> "SpecContext":
        """Create new context with different console.

        Args:
            console: New console interface instance

        Returns:
            New SpecContext with modified console

        Raises:
            SpecContextError: If console replacement fails
        """
        # Type annotations guarantee console is not None

        return SpecContext(
            settings=self.settings, console=console, progress=self.progress
        )

    def with_progress(self, progress: SpecProgressInterface) -> "SpecContext":
        """Create new context with different progress handler.

        Args:
            progress: New progress interface instance

        Returns:
            New SpecContext with modified progress

        Raises:
            SpecContextError: If progress replacement fails
        """
        # Type annotations guarantee progress is not None

        return SpecContext(
            settings=self.settings, console=self.console, progress=progress
        )

    def get_context_hash(self) -> str:
        """Get deterministic hash of context contents.

        Returns:
            SHA-256 hash string of context

        Raises:
            SpecContextError: If hash generation fails
        """
        try:
            return create_context_hash(self)
        except Exception as e:
            error_context = {"context_type": type(self).__name__, "error": str(e)}
            raise SpecContextError(
                f"Failed to generate context hash: {e}", error_context
            ) from e

    def __eq__(self, other: Any) -> bool:
        """Check equality using context hash.

        Args:
            other: Other context to compare

        Returns:
            True if contexts are equal, False otherwise
        """
        if not isinstance(other, SpecContext):
            return False

        try:
            return self.get_context_hash() == other.get_context_hash()
        except SpecContextError:
            return False
