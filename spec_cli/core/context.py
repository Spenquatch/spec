"""SpecContext core implementation for immutable dependency aggregation.

This module provides the SpecContext frozen dataclass that aggregates all critical
dependencies (settings, console, progress) for spec-cli operations with immutable
dependency injection support.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from ..logging.debug import debug_logger
from ..utils.context_utils import create_context_hash, validate_context_immutability
from ..utils.error_utils import create_error_context
from ..utils.factory_utils import validate_factory_inputs


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


class SpecFactoryError(SpecContextError):
    """Exception raised when SpecContext factory operations fail."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize SpecFactoryError with message and context.

        Args:
            message: Error message describing the factory operation failure
            context: Optional context dictionary with additional error details
        """
        super().__init__(message, context)
        debug_logger.log(
            "ERROR",
            "SpecContext factory error raised",
            error_message=message,
            factory_context=self.context,
        )


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

    def is_initialized(self) -> bool:
        """Check if the spec repository is initialized.

        Returns:
            True if repository is initialized, False otherwise
        """
        return (self.root_path / ".spec").exists()

    def __eq__(self, other: object) -> bool:
        """Check equality based on configuration values."""
        if not isinstance(other, SpecSettingsInterface):
            return False
        return (
            self.debug_enabled == other.debug_enabled
            and self.console_width == other.console_width
            and self.use_color == other.use_color
            and self.root_path == other.root_path
            and self.spec_dir == other.spec_dir
            and self.specs_dir == other.specs_dir
        )

    def __hash__(self) -> int:
        """Make settings hashable for use in dataclass."""
        return hash(
            (
                self.debug_enabled,
                self.console_width,
                self.use_color,
                str(self.root_path),
                str(self.spec_dir),
                str(self.specs_dir),
            )
        )


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

    def __eq__(self, other: object) -> bool:
        """Check equality for console interfaces."""
        return isinstance(other, SpecConsoleInterface)

    def __hash__(self) -> int:
        """Make console interface hashable."""
        return hash("SpecConsoleInterface")


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

    def __eq__(self, other: object) -> bool:
        """Check equality for progress interfaces."""
        return isinstance(other, SpecProgressInterface)

    def __hash__(self) -> int:
        """Make progress interface hashable."""
        return hash("SpecProgressInterface")


@dataclass(frozen=True)
class SpecContext:
    """Immutable dependency context for spec-cli operations.

    Aggregates critical dependencies identified in P1.1a analysis:
    - SpecSettings: 42 usage points (CRITICAL)
    - SpecConsole: 26 usage points (HIGH)
    - SpecProgress: 13 usage points (MEDIUM)

    Provides immutable dependency injection with thread-safe access.
    """

    settings: Any  # SpecSettingsInterface (temporarily Any for migration)
    console: Any  # SpecConsoleInterface (temporarily Any for migration)
    progress: Any  # SpecProgressInterface (temporarily Any for migration)

    def __post_init__(self) -> None:
        """Validate context after initialization.

        Raises:
            SpecContextError: If context validation fails
        """
        # Validate dependencies are not None
        if self.settings is None:
            raise SpecContextError("SpecContext requires settings dependency")
        if self.console is None:
            raise SpecContextError("SpecContext requires console dependency")
        if self.progress is None:
            raise SpecContextError("SpecContext requires progress dependency")

        # Validate immutability using helper
        if not validate_context_immutability(self):
            error_context = {"context_type": type(self).__name__}
            raise SpecContextError(
                "SpecContext must be immutable (frozen dataclass)", error_context
            )

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
        if console is None:
            raise SpecContextError("Console replacement cannot be None")

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
        if progress is None:
            raise SpecContextError("Progress replacement cannot be None")

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

    @classmethod
    def create_for_cli(
        cls, root_path: Path | None = None, **overrides: Any
    ) -> "SpecContext":
        """Create SpecContext for CLI environment with real dependencies.

        Factory method for creating production SpecContext instances in CLI
        environments with real dependency implementations.

        Args:
            root_path: Root path for spec operations (defaults to current directory)
            **overrides: Optional configuration overrides

        Returns:
            SpecContext instance configured for CLI environment

        Raises:
            SpecFactoryError: If CLI context creation fails

        Example:
            context = SpecContext.create_for_cli(Path("/project"))
            # Use context.settings, context.console, context.progress
        """
        try:
            debug_logger.log(
                "DEBUG",
                "Creating SpecContext for CLI environment",
                root_path=str(root_path) if root_path else None,
                overrides_count=len(overrides),
                override_keys=list(overrides.keys()),
            )

            # Validate inputs using factory utils
            validated_inputs = validate_factory_inputs(
                factory_type="cli_context",
                environment="cli",
                **overrides,
            )

            # Use current directory if no root path provided
            if root_path is None:
                root_path = Path.cwd()
                debug_logger.log(
                    "DEBUG", "Using current directory as root", root_path=str(root_path)
                )

            # Create CLI settings with real configuration using actual implementations
            from ..config.settings import get_settings
            from ..ui.console import get_console
            from ..ui.progress_manager import ProgressManager

            cli_settings = get_settings()
            cli_console = get_console()
            cli_progress = ProgressManager()

            debug_logger.log(
                "DEBUG",
                "Using concrete implementations",
                settings_type=type(cli_settings).__name__,
                console_type=type(cli_console).__name__,
                progress_type=type(cli_progress).__name__,
            )

            # Apply any setting overrides if provided
            for key, value in overrides.items():
                if hasattr(cli_settings, key):
                    setattr(cli_settings, key, value)
                    debug_logger.log(
                        "DEBUG", "Applied setting override", key=key, value=value
                    )

            # Create console adapter for interface compatibility
            class CLIConsoleAdapter:
                def __init__(self, console):
                    self._console = console
                    # Detect non-interactive mode to prevent hanging
                    import sys

                    self._is_interactive = sys.stdout.isatty() and sys.stderr.isatty()

                def print_message(self, text: str, style: str | None = None) -> None:
                    if not self._is_interactive:
                        # In non-interactive mode, use simple print to avoid Rich hanging
                        print(text)
                        return
                    if style:
                        self._console.print_status(text, style)
                    else:
                        self._console.print(text)

                def print_error(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Error: {text}")
                        return
                    self._console.print_status(text, "error")

                def print_success(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Success: {text}")
                        return
                    self._console.print_status(text, "success")

                def print_warning(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Warning: {text}")
                        return
                    self._console.print_status(text, "warning")

                def get_width(self) -> int:
                    return getattr(self._console, "width", 80)

                def supports_color(self) -> bool:
                    return self._is_interactive and not getattr(
                        self._console, "no_color", False
                    )

                def capture_output(self):
                    return getattr(self._console, "capture_output", lambda: None)()

            cli_console_adapter = CLIConsoleAdapter(cli_console)

            # Create and return context
            context = cls(
                settings=cli_settings,
                console=cli_console_adapter,
                progress=cli_progress,
            )

            debug_logger.log(
                "DEBUG",
                "CLI SpecContext created successfully",
                context_hash=context.get_context_hash()[:8],
                settings_type=type(cli_settings).__name__,
                console_type=type(cli_console).__name__,
                progress_type=type(cli_progress).__name__,
            )

            return context

        except Exception as e:
            error_context = create_error_context(root_path or Path.cwd())
            error_context.update(
                {
                    "factory_type": "cli",
                    "overrides": overrides,
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                }
            )
            raise SpecFactoryError(
                f"Failed to create CLI SpecContext: {e}", error_context
            ) from e

    @classmethod
    def create_for_testing(
        cls, testing_overrides: dict[str, Any] | None = None
    ) -> "SpecContext":
        """Create SpecContext for testing environment with mock dependencies.

        Factory method for creating test SpecContext instances with mock
        dependencies suitable for isolated unit testing.

        Args:
            testing_overrides: Optional configuration overrides for testing

        Returns:
            SpecContext instance configured for testing environment

        Raises:
            SpecFactoryError: If testing context creation fails

        Example:
            context = SpecContext.create_for_testing({"debug_enabled": True})
            # Use context with predictable mock behavior
        """
        try:
            overrides = testing_overrides or {}
            debug_logger.log(
                "DEBUG",
                "Creating SpecContext for testing environment",
                overrides_count=len(overrides),
                override_keys=list(overrides.keys()),
            )

            # Validate inputs using factory utils
            validated_inputs = validate_factory_inputs(
                factory_type="testing_context",
                environment="testing",
                **overrides,
            )

            # Create mock settings with deterministic behavior
            mock_settings = Mock(spec=SpecSettingsInterface)
            mock_settings.debug_enabled = validated_inputs.get("debug_mode", False)
            mock_settings.console_width = 80
            mock_settings.use_color = False  # Disable for testing consistency
            mock_settings.root_path = Path("/tmp/test")
            mock_settings.spec_dir = Path("/tmp/test/.spec")
            mock_settings.specs_dir = Path("/tmp/test/.specs")

            # Apply testing overrides to mock settings
            for key, value in overrides.items():
                if hasattr(SpecSettingsInterface(), key):
                    setattr(mock_settings, key, value)
                    debug_logger.log(
                        "DEBUG", "Applied testing override", key=key, value=value
                    )

            # Mock settings methods
            mock_settings.get_setting.return_value = None
            mock_settings.validate_configuration.return_value = {}

            # Create mock console with deterministic behavior
            mock_console = Mock(spec=SpecConsoleInterface)
            mock_console.get_width.return_value = 80
            mock_console.supports_color.return_value = False
            # Mock console methods don't need return values (print operations)
            mock_console.print_message.return_value = None
            mock_console.print_error.return_value = None
            mock_console.print_success.return_value = None
            mock_console.print_warning.return_value = None

            # Create mock progress with deterministic behavior
            mock_progress = Mock(spec=SpecProgressInterface)
            mock_progress.start_operation.return_value = "test_op_001"
            mock_progress.show_progress.return_value = None
            mock_progress.update_status.return_value = None
            mock_progress.finish_operation.return_value = None

            # Create and return context
            context = cls(
                settings=mock_settings, console=mock_console, progress=mock_progress
            )

            debug_logger.log(
                "DEBUG",
                "Testing SpecContext created successfully",
                context_hash=context.get_context_hash()[:8],
                settings_type=type(mock_settings).__name__,
                console_type=type(mock_console).__name__,
                progress_type=type(mock_progress).__name__,
            )

            return context

        except Exception as e:
            error_context = {
                "factory_type": "testing",
                "overrides": testing_overrides or {},
                "error_type": type(e).__name__,
                "error_details": str(e),
            }
            raise SpecFactoryError(
                f"Failed to create testing SpecContext: {e}", error_context
            ) from e
