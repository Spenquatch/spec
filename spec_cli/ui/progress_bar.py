"""
Rich progress bar components for determinate progress tracking.

Provides configurable progress bars with time estimates and task management.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from ..logging.debug import debug_logger
from .console import get_console


class SpecProgressBar:
    """Spec-specific progress bar wrapper with Rich integration."""

    def __init__(
        self,
        console: Console | None = None,
        show_percentage: bool = True,
        show_time_elapsed: bool = True,
        show_time_remaining: bool = True,
        show_speed: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: int = 10,
    ) -> None:
        """Initialize the progress bar.

        Args:
            console: Console to use (uses global if None)
            show_percentage: Whether to show percentage
            show_time_elapsed: Whether to show elapsed time
            show_time_remaining: Whether to show remaining time
            show_speed: Whether to show processing speed
            auto_refresh: Whether to auto-refresh display
            refresh_per_second: Refresh rate
        """
        self.console = console or get_console().console
        self.show_percentage = show_percentage
        self.show_time_elapsed = show_time_elapsed
        self.show_time_remaining = show_time_remaining
        self.show_speed = show_speed

        # Build progress columns
        columns = self._build_columns()

        self.progress = Progress(
            *columns,
            console=self.console,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
        )

        self.tasks: dict[str, TaskID] = {}
        self._is_started = False

        debug_logger.log(
            "INFO",
            "SpecProgressBar initialized",
            columns=len(columns),
            auto_refresh=auto_refresh,
        )

    def _build_columns(self) -> list[ProgressColumn]:
        """Build progress bar columns based on configuration."""
        columns = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
        ]

        if self.show_percentage:
            columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))

        columns.append(TextColumn("({task.completed}/{task.total})"))

        if self.show_time_elapsed:
            columns.append(TimeElapsedColumn())

        if self.show_time_remaining:
            columns.append(TimeRemainingColumn())

        if self.show_speed:
            columns.append(TextColumn("[progress.data.speed]{task.speed} files/s"))

        return columns

    def start(self) -> None:
        """Start the progress display."""
        if not self._is_started:
            self.progress.start()
            self._is_started = True
            debug_logger.log("DEBUG", "Progress bar started")

    def stop(self) -> None:
        """Stop the progress display."""
        if self._is_started:
            self.progress.stop()
            self._is_started = False
            debug_logger.log("DEBUG", "Progress bar stopped")

    def add_task(
        self,
        description: str,
        total: int | None = None,
        task_id: str | None = None,
    ) -> str:
        """Add a new progress task.

        Args:
            description: Task description
            total: Total number of items (None for indeterminate)
            task_id: Optional task identifier

        Returns:
            Task identifier string
        """
        if not self._is_started:
            self.start()

        rich_task_id = self.progress.add_task(description, total=total)

        # Generate task ID if not provided
        if task_id is None:
            task_id = f"task_{len(self.tasks)}"

        self.tasks[task_id] = rich_task_id

        debug_logger.log(
            "DEBUG",
            "Progress task added",
            task_id=task_id,
            description=description,
            total=total,
        )

        return task_id

    def update_task(
        self,
        task_id: str,
        advance: int | None = None,
        completed: int | None = None,
        total: int | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Update a progress task.

        Args:
            task_id: Task identifier
            advance: Number of items to advance
            completed: Total completed items
            total: New total (if changed)
            description: New description
            **kwargs: Additional task data
        """
        if task_id not in self.tasks:
            debug_logger.log("WARNING", "Task not found for update", task_id=task_id)
            return

        rich_task_id = self.tasks[task_id]

        # Use proper Progress.update API
        if advance is not None:
            self.progress.advance(rich_task_id, advance)
        if completed is not None:
            self.progress.update(rich_task_id, completed=completed)
        if total is not None:
            self.progress.update(rich_task_id, total=total)
        if description is not None:
            self.progress.update(rich_task_id, description=description)

        # Add any other custom data
        if kwargs:
            self.progress.update(rich_task_id, **kwargs)

        debug_logger.log("DEBUG", "Progress task updated", task_id=task_id)

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed.

        Args:
            task_id: Task identifier
        """
        if task_id not in self.tasks:
            debug_logger.log(
                "WARNING", "Task not found for completion", task_id=task_id
            )
            return

        rich_task_id = self.tasks[task_id]
        task = self.progress.tasks[rich_task_id]

        if task.total is not None:
            self.progress.update(rich_task_id, completed=task.total)

        debug_logger.log("DEBUG", "Progress task completed", task_id=task_id)

    def remove_task(self, task_id: str) -> None:
        """Remove a progress task.

        Args:
            task_id: Task identifier
        """
        if task_id not in self.tasks:
            debug_logger.log("WARNING", "Task not found for removal", task_id=task_id)
            return

        rich_task_id = self.tasks[task_id]
        self.progress.remove_task(rich_task_id)
        del self.tasks[task_id]

        debug_logger.log("DEBUG", "Progress task removed", task_id=task_id)

    def get_task_info(self, task_id: str) -> dict[str, Any] | None:
        """Get information about a task.

        Args:
            task_id: Task identifier

        Returns:
            Task information dictionary or None if not found
        """
        if task_id not in self.tasks:
            return None

        rich_task_id = self.tasks[task_id]
        task = self.progress.tasks[rich_task_id]

        return {
            "description": task.description,
            "total": task.total,
            "completed": task.completed,
            "percentage": task.percentage,
            "remaining": task.remaining,
            "elapsed": task.elapsed,
            "speed": task.speed,
            "finished": task.finished,
        }

    @contextmanager
    def task_context(
        self,
        description: str,
        total: int | None = None,
        task_id: str | None = None,
    ) -> Generator[str, None, None]:
        """Context manager for progress tasks.

        Args:
            description: Task description
            total: Total number of items
            task_id: Optional task identifier

        Yields:
            Task identifier for updates
        """
        task_id = self.add_task(description, total, task_id)
        try:
            yield task_id
        finally:
            self.remove_task(task_id)

    def __enter__(self) -> "SpecProgressBar":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.stop()


class SimpleProgressBar:
    """Simplified progress bar for basic use cases."""

    def __init__(self, total: int, description: str = "Processing") -> None:
        """Initialize simple progress bar.

        Args:
            total: Total number of items
            description: Progress description
        """
        self.total = total
        self.description = description
        self.completed = 0
        self.progress_bar = SpecProgressBar(
            show_time_remaining=True, show_percentage=True
        )
        self.task_id: str | None = None

    def start(self) -> None:
        """Start the progress bar."""
        self.progress_bar.start()
        self.task_id = self.progress_bar.add_task(self.description, total=self.total)

    def advance(self, count: int = 1) -> None:
        """Advance the progress bar.

        Args:
            count: Number of items to advance
        """
        if self.task_id:
            self.completed += count
            self.progress_bar.update_task(self.task_id, advance=count)

    def finish(self) -> None:
        """Finish the progress bar."""
        if self.task_id:
            self.progress_bar.complete_task(self.task_id)
            self.progress_bar.stop()

    def __enter__(self) -> "SimpleProgressBar":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.finish()


# Convenience functions
def create_progress_bar(**kwargs: Any) -> SpecProgressBar:
    """Create a new progress bar with default settings.

    Args:
        **kwargs: Configuration options for SpecProgressBar

    Returns:
        Configured SpecProgressBar instance
    """
    return SpecProgressBar(**kwargs)


def simple_progress(total: int, description: str = "Processing") -> SimpleProgressBar:
    """Create a simple progress bar for basic use cases.

    Args:
        total: Total number of items
        description: Progress description

    Returns:
        SimpleProgressBar instance
    """
    return SimpleProgressBar(total, description)
