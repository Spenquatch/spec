"""Batch file processing module.

Provides functionality for processing multiple files in batches with progress tracking,
error recovery, and conflict resolution. Includes options for parallel processing,
automatic commit, and comprehensive result reporting.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ..config.settings import SpecSettings, get_settings
from ..logging.debug import debug_logger
from ..utils.error_utils import create_error_context, handle_os_error
from .aggregators.result_aggregator import BatchResultAggregator
from .change_detector import FileChangeDetector
from .conflict_resolver import ConflictResolutionStrategy, ConflictResolver
from .processing_pipeline import FileProcessingPipeline, FileProcessingResult
from .progress_events import ProgressEventType, progress_reporter
from .trackers.batch_progress_tracker import BatchProgressTracker


class BatchProcessingOptions:
    """Configuration options for batch processing."""

    def __init__(
        self,
        max_files: int | None = None,
        max_parallel: int = 1,
        force_regenerate: bool = False,
        skip_unchanged: bool = True,
        conflict_strategy: ConflictResolutionStrategy | None = None,
        create_backups: bool = True,
        auto_commit: bool = False,
        custom_variables: dict[str, Any] | None = None,
    ):
        """Initialize batch processing options.

        Args:
            max_files: Maximum number of files to process (None for unlimited)
            max_parallel: Maximum number of parallel processing threads
            force_regenerate: Whether to force regeneration of all files
            skip_unchanged: Whether to skip files that haven't changed
            conflict_strategy: Strategy for resolving conflicts (defaults to MERGE_INTELLIGENT)
            create_backups: Whether to create backups before processing
            auto_commit: Whether to automatically commit successful changes
            custom_variables: Custom variables for template processing
        """
        self.max_files = max_files
        self.max_parallel = max_parallel
        self.force_regenerate = force_regenerate
        self.skip_unchanged = skip_unchanged
        self.conflict_strategy = (
            conflict_strategy or ConflictResolutionStrategy.MERGE_INTELLIGENT
        )
        self.create_backups = create_backups
        self.auto_commit = auto_commit
        self.custom_variables = custom_variables or {}


class BatchProcessingResult:
    """Result of batch processing operation."""

    def __init__(self) -> None:
        """Initialize empty batch processing result.

        Creates a new result object with default values for tracking
        batch processing outcomes, timing, and file categorization.
        """
        self.success = False
        self.total_files = 0
        self.successful_files: list[Path] = []
        self.failed_files: list[Path] = []
        self.skipped_files: list[Path] = []
        self.file_results: dict[str, FileProcessingResult] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.workflow_id: str | None = None

    @property
    def duration(self) -> float | None:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "total_files": self.total_files,
            "successful_count": len(self.successful_files),
            "failed_count": len(self.failed_files),
            "skipped_count": len(self.skipped_files),
            "successful_files": [str(f) for f in self.successful_files],
            "failed_files": [str(f) for f in self.failed_files],
            "skipped_files": [str(f) for f in self.skipped_files],
            "errors": self.errors,
            "warnings": self.warnings,
            "duration": self.duration,
            "workflow_id": self.workflow_id,
        }


class BatchFileProcessor:
    """Processes multiple files in batch with progress tracking and error recovery."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize batch file processor.

        Args:
            settings: Optional spec settings to use, defaults to global settings
        """
        self.settings = settings or get_settings()
        self.change_detector = FileChangeDetector(self.settings)
        self.conflict_resolver = ConflictResolver(self.settings)
        self.progress_reporter = progress_reporter
        self.result_aggregator = BatchResultAggregator()

        # Create processing pipeline
        from ..templates.generator import SpecContentGenerator

        content_generator = SpecContentGenerator(self.settings)

        self.pipeline = FileProcessingPipeline(
            content_generator=content_generator,
            change_detector=self.change_detector,
            conflict_resolver=self.conflict_resolver,
            progress_reporter=self.progress_reporter,
        )

        debug_logger.log("INFO", "BatchFileProcessor initialized")

    def process_files(
        self,
        file_paths: list[Path],
        options: BatchProcessingOptions | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> BatchProcessingResult:
        """Process multiple files in batch.

        Args:
            file_paths: List of file paths to process
            options: Batch processing options
            progress_callback: Optional progress callback function

        Returns:
            BatchProcessingResult with processing outcomes
        """
        options = options or BatchProcessingOptions()

        debug_logger.log(
            "INFO",
            "Starting batch file processing",
            total_files=len(file_paths),
            max_files=options.max_files,
            force_regenerate=options.force_regenerate,
        )

        result = BatchProcessingResult()
        result.start_time = time.time()

        try:
            with debug_logger.timer("batch_file_processing"):
                # Limit files if specified
                files_to_process = file_paths
                if options.max_files and len(file_paths) > options.max_files:
                    files_to_process = file_paths[: options.max_files]
                    result.warnings.append(f"Limited to {options.max_files} files")

                result.total_files = len(files_to_process)

                # Filter files that need processing (unless force regenerate)
                if not options.force_regenerate and options.skip_unchanged:
                    files_needing_processing = (
                        self.change_detector.get_files_needing_processing(
                            files_to_process, force_all=False
                        )
                    )

                    # Track skipped files
                    skipped = set(files_to_process) - set(files_needing_processing)
                    result.skipped_files.extend(skipped)

                    files_to_process = files_needing_processing

                    debug_logger.log(
                        "INFO",
                        "Filtered files needing processing",
                        original_count=result.total_files,
                        processing_count=len(files_to_process),
                        skipped_count=len(skipped),
                    )

                # Create progress tracker for this batch
                progress_tracker = BatchProgressTracker(
                    len(files_to_process), self.progress_reporter
                )
                progress_tracker.start_batch(
                    f"Processing {len(files_to_process)} files"
                )

                # Track skipped files with progress tracker
                for skipped_file in result.skipped_files:
                    progress_tracker.track_file_skipped(skipped_file)

                # Process files
                self._process_files_sequentially(
                    files_to_process,
                    options,
                    result,
                    progress_callback,
                    progress_tracker,
                )

                # Handle post-processing
                if options.auto_commit and result.successful_files:
                    self._handle_auto_commit(result, options)

                # Finalize result
                result.success = len(result.errors) == 0
                result.end_time = time.time()

                # Complete batch tracking
                progress_tracker.complete_batch(result.duration)

            debug_logger.log(
                "INFO",
                "Batch file processing completed",
                total_files=result.total_files,
                successful=len(result.successful_files),
                failed=len(result.failed_files),
                duration=result.duration,
            )

            return result

        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            debug_logger.log("ERROR", error_msg)

            result.errors.append(error_msg)
            result.success = False
            result.end_time = time.time()

            # Emit batch failed event
            from .progress_events import ProgressEvent

            self.progress_reporter.emit_event(
                ProgressEvent(
                    event_type=ProgressEventType.BATCH_FAILED, message=error_msg
                )
            )

            return result

    def _process_files_sequentially(
        self,
        files: list[Path],
        options: BatchProcessingOptions,
        result: BatchProcessingResult,
        progress_callback: Callable[[int, int, str], None] | None,
        progress_tracker: BatchProgressTracker,
    ) -> None:
        """Process files sequentially."""
        for i, file_path in enumerate(files):
            try:
                # Track file started with progress tracker
                progress_tracker.track_file_started(file_path)

                # Progress callback
                if progress_callback:
                    progress_callback(i, len(files), f"Processing {file_path.name}")

                # Process single file
                file_result = self.pipeline.process_file(
                    file_path=file_path,
                    custom_variables=options.custom_variables,
                    conflict_strategy=options.conflict_strategy,
                    force_regenerate=options.force_regenerate,
                )

                # Store result
                result.file_results[str(file_path)] = file_result

                # Categorize result
                if file_result.success:
                    result.successful_files.append(file_path)
                    # Track file completion with progress tracker
                    progress_tracker.track_file_completed(file_path, True)
                else:
                    result.failed_files.append(file_path)
                    result.errors.extend(file_result.errors)
                    # Track file completion with progress tracker
                    progress_tracker.track_file_completed(file_path, False)

                    # Emit error event for additional context
                    error_msg = f"Processing failed for {file_path}: {'; '.join(file_result.errors)}"
                    self.progress_reporter.emit_error(error_msg, file_path)

                # Add warnings
                result.warnings.extend(file_result.warnings)

            except Exception as e:
                if isinstance(e, OSError):
                    formatted_error = handle_os_error(e)
                    context = create_error_context(file_path)
                    context.update(
                        {
                            "operation": "batch_file_processing",
                            "batch_size": len(files),
                            "current_index": i,
                        }
                    )
                    debug_logger.log(
                        "ERROR",
                        f"Batch processing failed: {formatted_error}",
                        **context,
                    )
                    error_msg = f"File processing failed: {formatted_error}"
                else:
                    error_msg = f"Unexpected error processing {file_path}: {e}"
                    debug_logger.log("ERROR", error_msg)

                result.failed_files.append(file_path)
                result.errors.append(error_msg)

                # Track file completion as failed with progress tracker
                progress_tracker.track_file_completed(file_path, False)

                # Emit error event
                self.progress_reporter.emit_error(error_msg, file_path, e)

        # Final progress callback
        if progress_callback:
            progress_callback(len(files), len(files), "Completed")

    def _handle_auto_commit(
        self, result: BatchProcessingResult, options: BatchProcessingOptions
    ) -> None:
        """Handle automatic commit of successful files."""
        try:
            debug_logger.log(
                "INFO",
                "Handling auto-commit",
                successful_files=len(result.successful_files),
            )

            # Use direct git operations instead of workflow orchestrator
            from ..git.repository import SpecGitRepository

            repo = SpecGitRepository(self.settings)

            try:
                # Add processed files to git
                repo.add_files([str(f) for f in result.successful_files])

                # Create commit
                commit_msg = f"Process {len(result.successful_files)} spec files"
                repo.commit(commit_msg)

                # Create workflow result using aggregator
                workflow_id = f"batch-{int(time.time())}"
                workflow_result = self.result_aggregator.create_workflow_summary(
                    result.successful_files, workflow_id
                )
                result.workflow_id = workflow_result["workflow_id"]

            except Exception as git_error:
                result.warnings.append(f"Auto-commit failed: {git_error}")

        except Exception as e:
            if isinstance(e, OSError):
                formatted_error = handle_os_error(e)
                context = create_error_context(Path.cwd())
                context.update(
                    {
                        "operation": "auto_commit",
                        "successful_files_count": len(result.successful_files),
                    }
                )
                debug_logger.log(
                    "WARNING", f"Auto-commit failed: {formatted_error}", **context
                )
                result.warnings.append(f"Auto-commit failed: {formatted_error}")
            else:
                result.warnings.append(f"Auto-commit failed: {e}")
                debug_logger.log("WARNING", "Auto-commit failed", error=str(e))

    def estimate_batch_processing(self, file_paths: list[Path]) -> dict[str, Any]:
        """Estimate batch processing requirements.

        Args:
            file_paths: List of files to estimate

        Returns:
            Dictionary with processing estimates
        """
        return self.pipeline.get_processing_estimate(file_paths)

    def validate_batch_processing(
        self, file_paths: list[Path], options: BatchProcessingOptions | None = None
    ) -> list[str]:
        """Validate batch processing requirements.

        Args:
            file_paths: List of files to validate
            options: Processing options

        Returns:
            List of validation issues
        """
        issues = []
        options = options or BatchProcessingOptions()

        # Validate file count
        if not file_paths:
            issues.append("No files provided for processing")
            return issues

        # Validate individual files
        for file_path in file_paths:
            file_issues = self.pipeline.validate_file_for_processing(file_path)
            issues.extend(file_issues)

        # Validate conflict strategy
        if options.conflict_strategy:
            try:
                # Test if strategy is valid
                ConflictResolutionStrategy(options.conflict_strategy.value)
            except ValueError:
                issues.append(f"Invalid conflict strategy: {options.conflict_strategy}")

        return issues

    def get_processing_summary(self, result: BatchProcessingResult) -> dict[str, Any]:
        """Get a summary of batch processing results.

        Args:
            result: Batch processing result

        Returns:
            Summary dictionary with additional batch-specific information
        """
        # Use the aggregator to process file results
        aggregated_summary = self.result_aggregator.aggregate_results(
            result.file_results
        )

        # Enhance the aggregated summary with batch-specific information
        enhanced_summary = aggregated_summary["summary"].copy()

        # Override overview with actual batch result totals for backward compatibility
        enhanced_summary["overview"] = {
            "total_files": result.total_files,
            "successful": len(result.successful_files),
            "failed": len(result.failed_files),
            "skipped": len(result.skipped_files),
            "success_rate": (
                len(result.successful_files) / result.total_files * 100
                if result.total_files > 0
                else 0
            ),
            "duration": result.duration,
        }

        # Use batch-level errors for total_errors to maintain backward compatibility
        enhanced_summary["errors"]["total_errors"] = len(result.errors)

        enhanced_summary["warnings"] = {
            "total_warnings": len(result.warnings),
        }

        return cast(dict[str, Any], enhanced_summary)


# Convenience functions
def process_files_batch(file_paths: list[Path], **kwargs: Any) -> BatchProcessingResult:
    """Process files in batch using default processor."""
    processor = BatchFileProcessor()
    options = BatchProcessingOptions(**kwargs)
    return processor.process_files(file_paths, options)


def estimate_processing_time(file_paths: list[Path]) -> dict[str, Any]:
    """Estimate processing time for given file paths."""
    processor = BatchFileProcessor()
    return processor.estimate_batch_processing(file_paths)
