import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from ..logging.debug import debug_logger
from .console import get_console


class SpecSpinner:
    """Spec-specific spinner component with Rich integration."""

    def __init__(
        self,
        text: str = "Loading...",
        spinner_style: str = "dots",
        console: Console | None = None,
        speed: float = 1.0,
    ) -> None:
        """Initialize the spinner.

        Args:
            text: Text to display with spinner
            spinner_style: Spinner animation style
            console: Console to use (uses global if None)
            speed: Animation speed multiplier
        """
        self.text = text
        self.spinner_style = spinner_style
        self.console = console or get_console().console
        self.speed = speed

        self.spinner = Spinner(spinner_style, speed=speed)
        self.live: Live | None = None
        self._is_running = False

        debug_logger.log(
            "INFO", "SpecSpinner initialized", text=text, style=spinner_style
        )

    def start(self) -> None:
        """Start the spinner animation."""
        if self._is_running:
            return

        spinner_text = Text.from_markup(f"{self.text}")
        display = Text.assemble(str(self.spinner), " ", spinner_text)

        self.live = Live(
            display, console=self.console, refresh_per_second=10, transient=True
        )

        self.live.start()
        self._is_running = True

        debug_logger.log("DEBUG", "Spinner started")

    def stop(self) -> None:
        """Stop the spinner animation."""
        if not self._is_running or not self.live:
            return

        self.live.stop()
        self.live = None
        self._is_running = False

        debug_logger.log("DEBUG", "Spinner stopped")

    def update_text(self, text: str) -> None:
        """Update the spinner text.

        Args:
            text: New text to display
        """
        self.text = text

        if self._is_running and self.live:
            spinner_text = Text.from_markup(text)
            display = Text.assemble(str(self.spinner), " ", spinner_text)
            self.live.update(display)

        debug_logger.log("DEBUG", "Spinner text updated", text=text)

    def __enter__(self) -> "SpecSpinner":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.stop()


class TimedSpinner(SpecSpinner):
    """Spinner with automatic timeout."""

    def __init__(self, timeout: float = 30.0, **kwargs: Any) -> None:
        """Initialize timed spinner.

        Args:
            timeout: Maximum time to run spinner (seconds)
            **kwargs: Arguments for SpecSpinner
        """
        super().__init__(**kwargs)
        self.timeout = timeout
        self._timer: threading.Timer | None = None

    def start(self) -> None:
        """Start the spinner with timeout."""
        super().start()

        # Start timeout timer
        self._timer = threading.Timer(self.timeout, self._timeout_callback)
        self._timer.start()

        debug_logger.log("DEBUG", "Timed spinner started", timeout=self.timeout)

    def stop(self) -> None:
        """Stop the spinner and cancel timeout."""
        if self._timer:
            self._timer.cancel()
            self._timer = None

        super().stop()
        debug_logger.log("DEBUG", "Timed spinner stopped")

    def _timeout_callback(self) -> None:
        """Handle spinner timeout."""
        debug_logger.log("WARNING", "Spinner timed out", timeout=self.timeout)
        self.stop()


class SpinnerManager:
    """Manages multiple spinners and provides coordination."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize spinner manager.

        Args:
            console: Console to use for all spinners
        """
        self.console = console or get_console().console
        self.spinners: dict[str, SpecSpinner] = {}
        self._active_spinner: str | None = None

        debug_logger.log("INFO", "SpinnerManager initialized")

    def create_spinner(
        self, spinner_id: str, text: str = "Loading...", **kwargs: Any
    ) -> SpecSpinner:
        """Create a new spinner.

        Args:
            spinner_id: Unique identifier for the spinner
            text: Text to display with spinner
            **kwargs: Additional arguments for SpecSpinner

        Returns:
            Created SpecSpinner instance
        """
        if spinner_id in self.spinners:
            debug_logger.log("WARNING", "Spinner already exists", spinner_id=spinner_id)
            return self.spinners[spinner_id]

        spinner = SpecSpinner(text=text, console=self.console, **kwargs)

        self.spinners[spinner_id] = spinner

        debug_logger.log("DEBUG", "Spinner created", spinner_id=spinner_id)
        return spinner

    def start_spinner(self, spinner_id: str) -> bool:
        """Start a specific spinner.

        Args:
            spinner_id: Spinner identifier

        Returns:
            True if started successfully
        """
        if spinner_id not in self.spinners:
            debug_logger.log("WARNING", "Spinner not found", spinner_id=spinner_id)
            return False

        # Stop any currently active spinner
        if self._active_spinner and self._active_spinner != spinner_id:
            self.stop_spinner(self._active_spinner)

        self.spinners[spinner_id].start()
        self._active_spinner = spinner_id

        debug_logger.log("DEBUG", "Spinner started", spinner_id=spinner_id)
        return True

    def stop_spinner(self, spinner_id: str) -> bool:
        """Stop a specific spinner.

        Args:
            spinner_id: Spinner identifier

        Returns:
            True if stopped successfully
        """
        if spinner_id not in self.spinners:
            debug_logger.log("WARNING", "Spinner not found", spinner_id=spinner_id)
            return False

        self.spinners[spinner_id].stop()

        if self._active_spinner == spinner_id:
            self._active_spinner = None

        debug_logger.log("DEBUG", "Spinner stopped", spinner_id=spinner_id)
        return True

    def update_spinner_text(self, spinner_id: str, text: str) -> bool:
        """Update spinner text.

        Args:
            spinner_id: Spinner identifier
            text: New text to display

        Returns:
            True if updated successfully
        """
        if spinner_id not in self.spinners:
            debug_logger.log("WARNING", "Spinner not found", spinner_id=spinner_id)
            return False

        self.spinners[spinner_id].update_text(text)
        return True

    def remove_spinner(self, spinner_id: str) -> bool:
        """Remove a spinner.

        Args:
            spinner_id: Spinner identifier

        Returns:
            True if removed successfully
        """
        if spinner_id not in self.spinners:
            return False

        # Stop spinner if it's running
        self.stop_spinner(spinner_id)
        del self.spinners[spinner_id]

        debug_logger.log("DEBUG", "Spinner removed", spinner_id=spinner_id)
        return True

    def stop_all(self) -> None:
        """Stop all active spinners."""
        for spinner_id in list(self.spinners.keys()):
            self.stop_spinner(spinner_id)

        debug_logger.log("DEBUG", "All spinners stopped")

    @contextmanager
    def spinner_context(
        self, spinner_id: str, text: str, **kwargs: Any
    ) -> Generator[SpecSpinner, None, None]:
        """Context manager for temporary spinners.

        Args:
            spinner_id: Spinner identifier
            text: Spinner text
            **kwargs: Additional spinner arguments
        """
        spinner = self.create_spinner(spinner_id, text, **kwargs)
        self.start_spinner(spinner_id)
        try:
            yield spinner
        finally:
            self.remove_spinner(spinner_id)


# Convenience functions
def create_spinner(text: str = "Loading...", **kwargs: Any) -> SpecSpinner:
    """Create a new spinner with default settings.

    Args:
        text: Text to display with spinner
        **kwargs: Configuration options for SpecSpinner

    Returns:
        Configured SpecSpinner instance
    """
    return SpecSpinner(text=text, **kwargs)


def timed_spinner(
    text: str = "Loading...", timeout: float = 30.0, **kwargs: Any
) -> TimedSpinner:
    """Create a timed spinner.

    Args:
        text: Text to display with spinner
        timeout: Maximum time to run (seconds)
        **kwargs: Additional configuration options

    Returns:
        TimedSpinner instance
    """
    return TimedSpinner(text=text, timeout=timeout, **kwargs)


@contextmanager
def spinner_context(
    text: str = "Loading...", **kwargs: Any
) -> Generator[SpecSpinner, None, None]:
    """Context manager for simple spinner usage.

    Args:
        text: Text to display with spinner
        **kwargs: Configuration options for SpecSpinner
    """
    spinner = create_spinner(text, **kwargs)
    with spinner:
        yield spinner
