"""File processing utilities for spec CLI.

This package provides change detection, conflict resolution, and batch processing
capabilities for efficient spec generation workflows.
"""

from .batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
    BatchProcessingResult,
    estimate_processing_time,
    process_files_batch,
)
from .change_detector import FileChangeDetector
from .conflict_resolver import (
    ConflictInfo,
    ConflictResolutionResult,
    ConflictResolutionStrategy,
    ConflictResolver,
    ConflictType,
)
from .file_cache import FileCacheManager
from .merge_helpers import ContentMerger
from .processing_pipeline import FileProcessingPipeline, FileProcessingResult
from .progress_events import (
    ProcessingStage,
    ProgressEvent,
    ProgressEventType,
    ProgressReporter,
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
