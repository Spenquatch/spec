"""File processing utilities for spec CLI.

This package provides change detection, conflict resolution, and batch processing
capabilities for efficient spec generation workflows.
"""

from .change_detector import FileChangeDetector
from .file_cache import FileCacheManager
from .conflict_resolver import (
    ConflictResolver,
    ConflictResolutionStrategy,
    ConflictType,
    ConflictInfo,
    ConflictResolutionResult,
)
from .merge_helpers import ContentMerger
from .batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
    BatchProcessingResult,
    process_files_batch,
    estimate_processing_time,
)
from .processing_pipeline import FileProcessingPipeline, FileProcessingResult
from .progress_events import (
    ProgressReporter,
    ProgressEvent,
    ProgressEventType,
    ProcessingStage,
    progress_reporter,
)

__all__ = [
    "FileChangeDetector",
    "FileCacheManager",
    "ConflictResolver",
    "ConflictResolutionStrategy",
    "ConflictType",
    "ConflictInfo",
    "ConflictResolutionResult",
    "ContentMerger",
    "BatchFileProcessor",
    "BatchProcessingOptions",
    "BatchProcessingResult",
    "process_files_batch",
    "estimate_processing_time",
    "FileProcessingPipeline",
    "FileProcessingResult",
    "ProgressReporter",
    "ProgressEvent",
    "ProgressEventType",
    "ProcessingStage",
    "progress_reporter",
]