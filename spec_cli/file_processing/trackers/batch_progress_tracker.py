"""Progress tracking for batch file processing operations.

This module provides dedicated progress tracking functionality for batch processing,
extracting the tracking logic from BatchFileProcessor into a focused component
that manages progress state and emits appropriate events.
"""

import time
from pathlib import Path
from typing import Any

from ...logging.debug import debug_logger
from ..progress_events import ProgressReporter


class BatchProgressTracker:
    """Tracks progress for batch file processing operations.

    Manages tracking state, emits progress events, and provides summary statistics
    for batch processing operations. Integrates with the existing ProgressReporter
    infrastructure while providing a dedicated interface for batch progress.
    """

    def __init__(self, total_files: int, progress_reporter: ProgressReporter):
        """Initialize batch progress tracker.

        Args:
            total_files: Total number of files to process
            progress_reporter: Progress reporter instance for event emission

        Raises:
            ValueError: If total_files is negative
        """
        if total_files < 0:
            raise ValueError("total_files must be non-negative")

        self.total_files = total_files
        self.progress_reporter = progress_reporter

        # Tracking state
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        self.start_time: float | None = None
        self.end_time: float | None = None

        debug_logger.log(
            "INFO", "BatchProgressTracker initialized", total_files=total_files
        )

    def start_batch(self, message: str | None = None) -> None:
        """Start batch processing and emit batch started event.

        Args:
            message: Optional custom message for the batch start event
        """
        self.start_time = time.time()
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.skipped_files = 0

        self.progress_reporter.emit_batch_started(
            self.total_files, message or f"Processing {self.total_files} files"
        )

        debug_logger.log(
            "INFO", "Batch processing started", total_files=self.total_files
        )

    def track_file_started(self, file_path: Path) -> None:
        """Track when file processing starts.

        Args:
            file_path: Path of the file being processed
        """
        self.progress_reporter.emit_file_started(
            file_path, self.processed_files, self.total_files
        )

    def track_file_completed(self, file_path: Path, success: bool) -> None:
        """Track when file processing completes.

        Args:
            file_path: Path of the processed file
            success: Whether the file was processed successfully
        """
        self.processed_files += 1

        if success:
            self.successful_files += 1
        else:
            self.failed_files += 1

        self.progress_reporter.emit_file_completed(
            file_path, self.processed_files - 1, self.total_files, success
        )

    def track_file_skipped(self, file_path: Path) -> None:
        """Track when a file is skipped.

        Args:
            file_path: Path of the skipped file
        """
        self.skipped_files += 1

        debug_logger.log(
            "DEBUG",
            "File skipped",
            file_path=str(file_path),
            skipped_count=self.skipped_files,
        )

    def complete_batch(self, duration: float | None = None) -> None:
        """Complete batch processing and emit batch completed event.

        Args:
            duration: Optional duration override (uses calculated if None)
        """
        self.end_time = time.time()

        # Use provided duration or calculate from timing
        final_duration = duration
        if final_duration is None and self.start_time:
            final_duration = self.end_time - self.start_time

        self.progress_reporter.emit_batch_completed(
            self.total_files, self.successful_files, self.failed_files, final_duration
        )

        debug_logger.log(
            "INFO",
            "Batch processing completed",
            total_files=self.total_files,
            successful=self.successful_files,
            failed=self.failed_files,
            skipped=self.skipped_files,
            duration=final_duration,
        )

    def get_current_progress(self) -> float:
        """Get current progress as a percentage.

        Returns:
            Progress value between 0.0 and 1.0
        """
        if self.total_files == 0:
            return 1.0
        return self.processed_files / self.total_files

    def get_summary_statistics(self) -> dict[str, Any]:
        """Get summary statistics for the batch operation.

        Returns:
            Dictionary containing progress statistics
        """
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        elif self.start_time:
            duration = time.time() - self.start_time

        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "progress": self.get_current_progress(),
            "duration": duration,
            "success_rate": (self.successful_files / max(self.processed_files, 1)),
            "completion_rate": (
                self.processed_files / self.total_files if self.total_files > 0 else 1.0
            ),
        }

    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete.

        Returns:
            True if all files have been processed
        """
        return self.processed_files >= self.total_files

    @property
    def duration(self) -> float | None:
        """Get processing duration in seconds.

        Returns:
            Duration in seconds, or None if not started/completed
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None


def create_batch_progress_tracker(
    total_files: int, progress_reporter: ProgressReporter
) -> BatchProgressTracker:
    """Create a new batch progress tracker instance.

    Args:
        total_files: Total number of files to process
        progress_reporter: Progress reporter for event emission

    Returns:
        Configured BatchProgressTracker instance
    """
    return BatchProgressTracker(total_files, progress_reporter)
