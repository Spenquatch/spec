"""Migration facade bridge for singleton to dependency injection transition.

Provides backward compatibility during gradual migration.

This bridge allows legacy singleton code and new context-based code to coexist
during the migration period. It will be removed after migration completion.
"""

import threading
from typing import Any, Protocol

# Import original singletons (these imports may fail if singletons don't exist yet)
try:
    from ..logging.debug import debug_logger as _original_debug_logger
except ImportError:
    _original_debug_logger = None  # type: ignore[assignment]

try:
    from ..ui.console import get_console as _original_get_console
except ImportError:
    _original_get_console = None  # type: ignore[assignment]

try:
    from ..config.settings import get_settings as _original_get_settings
except ImportError:
    _original_get_settings = None  # type: ignore[assignment]

try:
    from ..ui.theme import get_current_theme as _original_get_current_theme
except ImportError:
    _original_get_current_theme = None  # type: ignore[assignment]

# Thread-safe context management
_context_lock = threading.Lock()
_migration_context: Any | None = None


def set_migration_context(context: Any) -> None:
    """Set the migration context for facade access."""
    global _migration_context
    with _context_lock:
        _migration_context = context


def get_migration_context() -> Any:
    """Get current migration context or None."""
    with _context_lock:
        return _migration_context


# Logger Protocol for type safety
class LoggerProtocol(Protocol):
    """Protocol for logger interface during migration."""

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log a message with specified level."""

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""


class DebugLoggerFacade:
    """
    Facade for debug_logger that can use context or fall back to singleton.

    During migration, this allows both old singleton-based code and new
    context-based code to work simultaneously.
    """

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message using context logger if available, otherwise singleton."""
        context = get_migration_context()
        if context and hasattr(context, "logger"):
            context.logger.log(level, message, **kwargs)
        elif _original_debug_logger:
            _original_debug_logger.log(level, message, **kwargs)
        else:
            # Fallback to print if no logger available
            print(f"[{level}] {message}")

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self.log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self.log("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self.log("DEBUG", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self.log("WARNING", message, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to context logger or original logger."""
        context = get_migration_context()
        if context and hasattr(context, "logger"):
            return getattr(context.logger, name)
        elif _original_debug_logger:
            return getattr(_original_debug_logger, name)
        else:
            raise AttributeError(f"No logger available for attribute: {name}")


def get_console() -> Any:
    """Facade for console access during migration."""
    context = get_migration_context()
    if context and hasattr(context, "console"):
        return context.console
    elif _original_get_console is not None:
        return _original_get_console()

    # Return a mock console for testing
    class MockConsole:  # type: ignore[unreachable]
        def print(self, *args, **kwargs: Any) -> None:
            print(*args)

        def print_status(
            self, message: str, status: str = "info", **kwargs: Any
        ) -> None:
            print(f"[{status.upper()}] {message}")

        def get_time(self) -> float:
            """Mock get_time method for Rich compatibility."""
            import time

            return time.time()

        def log(self, *args, **kwargs: Any) -> None:
            """Mock log method for Rich compatibility."""
            # Rich uses this for internal logging, just ignore
            pass

        @property
        def console(self) -> Any:
            """Mock console property to match SpecConsole interface."""
            return self

    return MockConsole()


def get_settings() -> Any:
    """Facade for settings access during migration."""
    context = get_migration_context()
    if context and hasattr(context, "settings"):
        return context.settings
    elif _original_get_settings is not None:
        return _original_get_settings()

    # Return empty settings for testing
    class MockSettings:  # type: ignore[unreachable]
        pass

    return MockSettings()


def get_current_theme() -> Any:
    """Facade for theme access during migration."""
    context = get_migration_context()
    if context and hasattr(context, "theme"):
        return context.theme
    elif _original_get_current_theme is not None:
        return _original_get_current_theme()

    # Return mock theme for testing
    class MockTheme:  # type: ignore[unreachable]
        def get_style(self, style_name: str) -> str:
            return ""

        def get_emoji_replacements(self) -> dict[str, str]:
            return {}

        @property
        def theme(self) -> Any:
            return self

    return MockTheme()


# Export facade instances
debug_logger = DebugLoggerFacade()


# Validation functions for testing
def validate_facade_bridge() -> bool:
    """Validate that facade bridge is working correctly."""
    try:
        # Test debug logger facade
        debug_logger.log("INFO", "Facade bridge test")

        # Test console facade
        console = get_console()
        console.print("Facade bridge console test")

        # Test settings facade
        get_settings()

        # Test theme facade
        theme = get_current_theme()
        theme.get_style("test")

        return True
    except Exception as e:
        print(f"Facade bridge validation failed: {e}")
        return False


def get_facade_status() -> dict[str, Any]:
    """Get current facade bridge status for diagnostics."""
    return {
        "context_set": get_migration_context() is not None,
        "original_debug_logger": _original_debug_logger is not None,
        "original_get_console": _original_get_console is not None,
        "original_get_settings": _original_get_settings is not None,
        "original_get_current_theme": _original_get_current_theme is not None,
        "facade_operational": validate_facade_bridge(),
    }
