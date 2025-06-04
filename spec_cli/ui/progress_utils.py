import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..logging.debug import debug_logger
from .progress_bar import simple_progress
from .progress_manager import get_progress_manager
from .spinner import spinner_context


def estimate_operation_time(
    item_count: int, base_time_per_item: float = 2.0, overhead: float = 1.0
) -> float:
    """Estimate operation completion time.

    Args:
        item_count: Number of items to process
        base_time_per_item: Base processing time per item (seconds)
        overhead: Additional overhead time (seconds)

    Returns:
        Estimated total time in seconds
    """
    return (item_count * base_time_per_item) + overhead


def format_time_duration(seconds: float) -> str:
    """Format time duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_processing_speed(completed_items: int, elapsed_time: float) -> float:
    """Calculate processing speed.

    Args:
        completed_items: Number of completed items
        elapsed_time: Time elapsed in seconds

    Returns:
        Items per second
    """
    if elapsed_time <= 0:
        return 0.0
    return completed_items / elapsed_time


@contextmanager
def progress_context(
    total_items: int | None = None,
    description: str = "Processing",
    show_spinner: bool = False,
) -> Iterator[Any]:
    """Context manager for simple progress tracking.

    Args:
        total_items: Total number of items (None for indeterminate)
        description: Progress description
        show_spinner: Whether to show spinner for indeterminate progress

    Yields:
        Progress update function
    """
    if total_items is not None:
        # Determinate progress with progress bar
        with simple_progress(total_items, description) as progress_bar:

            def update_progress(count: int = 1, message: str | None = None) -> None:
                progress_bar.advance(count)
                if message:
                    # Update description if needed (limited support)
                    pass

            yield update_progress

    elif show_spinner:
        # Indeterminate progress with spinner
        with spinner_context(description) as spinner:

            def update_progress(count: int = 1, message: str | None = None) -> None:
                if message:
                    spinner.update_text(message)

            yield update_progress

    else:
        # No visual progress
        def update_progress(count: int = 1, message: str | None = None) -> None:
            pass

        yield update_progress


@contextmanager
def timed_operation(
    operation_name: str, log_result: bool = True
) -> Iterator[Callable[[], float]]:
    """Context manager for timing operations.

    Args:
        operation_name: Name of the operation
        log_result: Whether to log the timing result

    Yields:
        Function to get elapsed time
    """
    start_time = time.time()

    def get_elapsed() -> float:
        return time.time() - start_time

    try:
        yield get_elapsed
    finally:
        elapsed = get_elapsed()
        if log_result:
            debug_logger.log(
                "INFO",
                "Operation completed",
                operation=operation_name,
                duration=f"{elapsed:.2f}s",
            )


def create_file_progress_tracker(files: list[Path]) -> Callable[[Path], None]:
    """Create a progress tracker for file operations.

    Args:
        files: List of files to track

    Returns:
        Function to call when a file is processed
    """
    total_files = len(files)
    completed_files = 0
    progress_manager = get_progress_manager()

    operation_id = f"file_operation_{int(time.time())}"
    progress_manager.start_indeterminate_operation(
        operation_id, f"Processing {total_files} files"
    )

    def track_file_completion(file_path: Path) -> None:
        nonlocal completed_files
        completed_files += 1

        # Update progress text
        progress_manager._update_operation_text(
            operation_id,
            f"Processing {file_path.name} ({completed_files}/{total_files})",
        )

        # Finish operation when all files are done
        if completed_files >= total_files:
            progress_manager.finish_operation(operation_id)

    return track_file_completion


class ProgressTracker:
    """Utility class for tracking progress of complex operations."""

    def __init__(
        self,
        operation_name: str,
        total_items: int | None = None,
        auto_finish: bool = True,
    ) -> None:
        """Initialize progress tracker.

        Args:
            operation_name: Name of the operation
            total_items: Total number of items (None for indeterminate)
            auto_finish: Whether to auto-finish when total is reached
        """
        self.operation_name = operation_name
        self.total_items = total_items
        self.auto_finish = auto_finish

        self.completed_items = 0
        self.start_time: float | None = None
        self.progress_manager = get_progress_manager()
        self.operation_id = f"{operation_name}_{int(time.time())}"

        debug_logger.log(
            "INFO",
            "ProgressTracker initialized",
            operation=operation_name,
            total_items=total_items,
        )

    def start(self) -> None:
        """Start progress tracking."""
        self.start_time = time.time()

        if self.total_items is not None:
            # Will be handled by progress manager events
            pass
        else:
            self.progress_manager.start_indeterminate_operation(
                self.operation_id, self.operation_name
            )

        debug_logger.log(
            "DEBUG", "Progress tracking started", operation_id=self.operation_id
        )

    def update(self, count: int = 1, message: str | None = None) -> None:
        """Update progress.

        Args:
            count: Number of items completed
            message: Optional status message
        """
        self.completed_items += count

        if message:
            self.progress_manager._update_operation_text(
                self.operation_id, f"{self.operation_name}: {message}"
            )

        # Auto-finish if we've completed all items
        if (
            self.auto_finish
            and self.total_items is not None
            and self.completed_items >= self.total_items
        ):
            self.finish()

    def finish(self) -> None:
        """Finish progress tracking."""
        self.progress_manager.finish_operation(self.operation_id)

        if self.start_time:
            elapsed = time.time() - self.start_time
            debug_logger.log(
                "INFO",
                "Progress tracking completed",
                operation=self.operation_name,
                completed_items=self.completed_items,
                duration=f"{elapsed:.2f}s",
            )

    def get_statistics(self) -> dict[str, Any]:
        """Get progress statistics.

        Returns:
            Dictionary with progress statistics
        """
        stats = {
            "operation_name": self.operation_name,
            "completed_items": self.completed_items,
            "total_items": self.total_items,
        }

        if self.start_time:
            elapsed = time.time() - self.start_time
            stats["elapsed_time"] = elapsed
            stats["items_per_second"] = calculate_processing_speed(
                self.completed_items, elapsed
            )

            if self.total_items:
                progress_ratio = self.completed_items / self.total_items
                stats["progress_percentage"] = progress_ratio * 100

                if progress_ratio > 0:
                    estimated_total = elapsed / progress_ratio
                    stats["estimated_completion"] = estimated_total - elapsed

        return stats

    def __enter__(self) -> "ProgressTracker":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.finish()


# Convenience functions
def track_progress(
    operation_name: str, total_items: int | None = None
) -> ProgressTracker:
    """Create a progress tracker for an operation.

    Args:
        operation_name: Name of the operation
        total_items: Total number of items

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(operation_name, total_items)


def show_progress_for_files(
    files: list[Path], operation_name: str = "Processing files"
) -> Callable[[Path], None]:
    """Show progress for file operations.

    Args:
        files: List of files to process
        operation_name: Name of the operation

    Returns:
        Function to call when each file is completed
    """
    return create_file_progress_tracker(files)
