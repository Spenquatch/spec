# Slice 11C: Batch Processing and Progress Events

## Goal

Iterate over changed files, call conflict resolution from slice-11b, and emit progress events for comprehensive batch processing workflows.

## Context

Building on change detection from slice-11a and conflict resolution from slice-11b, this slice creates the batch processing engine. It orchestrates the complete file processing workflow, handles progress tracking, and provides integration points for Rich UI components that will be added in PHASE-5.

## Scope

**Included in this slice:**
- BatchFileProcessor class for coordinating batch operations
- Progress event system for tracking operation status
- File processing pipeline with change detection and conflict resolution
- Error recovery and rollback capabilities for batch operations
- Integration with workflow orchestration from slice-10c

**NOT included in this slice:**
- Rich UI progress bars (comes in PHASE-5)
- Interactive conflict resolution prompts (comes in PHASE-5)
- CLI command integration (comes in slice-13)
- Template generation logic (already in slice-8b)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for batch processing errors)
- `spec_cli.logging.debug` (debug_logger for batch operation tracking)
- `spec_cli.config.settings` (SpecSettings for batch configuration)
- `spec_cli.file_processing.change_detector` (FileChangeDetector from slice-11a)
- `spec_cli.file_processing.conflict_resolver` (ConflictResolver from slice-11b)
- `spec_cli.templates.generator` (SpecContentGenerator from slice-8b)
- `spec_cli.core.workflow_orchestrator` (SpecWorkflowOrchestrator from slice-10c)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `FileChangeDetector` from slice-11a-change-detection
- `ConflictResolver`, `ConflictResolutionStrategy` from slice-11b-conflict-resolver
- `SpecContentGenerator` from slice-8b-spec-generator
- `SpecWorkflowOrchestrator` from slice-10c-spec-workflow

## Files to Create

```
spec_cli/file_processing/
├── batch_processor.py      # BatchFileProcessor class
├── progress_events.py      # Progress event system
└── processing_pipeline.py  # File processing pipeline utilities
```

## Implementation Steps

### Step 1: Create spec_cli/file_processing/progress_events.py

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from ..logging.debug import debug_logger

class ProgressEventType(Enum):
    """Types of progress events."""
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"
    FILE_STARTED = "file_started"
    FILE_COMPLETED = "file_completed"
    FILE_FAILED = "file_failed"
    FILE_SKIPPED = "file_skipped"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    PROGRESS_UPDATE = "progress_update"
    WARNING = "warning"
    ERROR = "error"

class ProcessingStage(Enum):
    """Stages of file processing."""
    INITIALIZATION = "initialization"
    CHANGE_DETECTION = "change_detection"
    CONTENT_GENERATION = "content_generation"
    CONFLICT_DETECTION = "conflict_detection"
    CONFLICT_RESOLUTION = "conflict_resolution"
    FILE_WRITING = "file_writing"
    CACHE_UPDATE = "cache_update"
    CLEANUP = "cleanup"

@dataclass
class ProgressEvent:
    """Represents a progress event during batch processing."""
    event_type: ProgressEventType
    timestamp: datetime = field(default_factory=datetime.now)
    file_path: Optional[Path] = None
    stage: Optional[ProcessingStage] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "file_path": str(self.file_path) if self.file_path else None,
            "stage": self.stage.value if self.stage else None,
            "progress": self.progress,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "message": self.message,
            "metadata": self.metadata,
        }

class ProgressReporter:
    """Reports progress events to registered listeners."""
    
    def __init__(self):
        self.listeners: List[Callable[[ProgressEvent], None]] = []
        self.events: List[ProgressEvent] = []
        self.max_events = 1000  # Limit stored events to prevent memory issues
        
        debug_logger.log("INFO", "ProgressReporter initialized")
    
    def add_listener(self, listener: Callable[[ProgressEvent], None]) -> None:
        """Add a progress event listener.
        
        Args:
            listener: Function that accepts ProgressEvent
        """
        self.listeners.append(listener)
        debug_logger.log("DEBUG", "Progress listener added",
                        total_listeners=len(self.listeners))
    
    def remove_listener(self, listener: Callable[[ProgressEvent], None]) -> bool:
        """Remove a progress event listener.
        
        Args:
            listener: Listener function to remove
            
        Returns:
            True if listener was removed
        """
        try:
            self.listeners.remove(listener)
            debug_logger.log("DEBUG", "Progress listener removed")
            return True
        except ValueError:
            return False
    
    def emit_event(self, event: ProgressEvent) -> None:
        """Emit a progress event to all listeners.
        
        Args:
            event: Progress event to emit
        """
        # Store event (with size limit)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events // 2:]  # Keep most recent half
        
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                debug_logger.log("WARNING", "Progress listener failed",
                               error=str(e))
        
        # Log important events
        if event.event_type in [
            ProgressEventType.BATCH_STARTED,
            ProgressEventType.BATCH_COMPLETED,
            ProgressEventType.BATCH_FAILED,
            ProgressEventType.ERROR
        ]:
            debug_logger.log("INFO", "Progress event",
                           event_type=event.event_type.value,
                           message=event.message)
    
    def emit_batch_started(self, total_files: int, message: Optional[str] = None) -> None:
        """Emit batch started event."""
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            total_files=total_files,
            processed_files=0,
            progress=0.0,
            message=message or f"Starting batch processing of {total_files} files"
        )
        self.emit_event(event)
    
    def emit_batch_completed(self, 
                           total_files: int,
                           successful_files: int,
                           failed_files: int,
                           duration: Optional[float] = None) -> None:
        """Emit batch completed event."""
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_COMPLETED,
            total_files=total_files,
            processed_files=total_files,
            progress=1.0,
            message=f"Batch completed: {successful_files} successful, {failed_files} failed",
            metadata={
                "successful_files": successful_files,
                "failed_files": failed_files,
                "duration": duration,
            }
        )
        self.emit_event(event)
    
    def emit_file_started(self, file_path: Path, file_index: int, total_files: int) -> None:
        """Emit file processing started event."""
        progress = file_index / total_files if total_files > 0 else 0.0
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED,
            file_path=file_path,
            total_files=total_files,
            processed_files=file_index,
            progress=progress,
            message=f"Processing {file_path.name}"
        )
        self.emit_event(event)
    
    def emit_file_completed(self, 
                          file_path: Path,
                          file_index: int,
                          total_files: int,
                          success: bool = True) -> None:
        """Emit file processing completed event."""
        progress = (file_index + 1) / total_files if total_files > 0 else 1.0
        event_type = ProgressEventType.FILE_COMPLETED if success else ProgressEventType.FILE_FAILED
        
        event = ProgressEvent(
            event_type=event_type,
            file_path=file_path,
            total_files=total_files,
            processed_files=file_index + 1,
            progress=progress,
            message=f"{'Completed' if success else 'Failed'} {file_path.name}"
        )
        self.emit_event(event)
    
    def emit_stage_update(self,
                         file_path: Path,
                         stage: ProcessingStage,
                         message: Optional[str] = None) -> None:
        """Emit processing stage update."""
        event = ProgressEvent(
            event_type=ProgressEventType.STAGE_STARTED,
            file_path=file_path,
            stage=stage,
            message=message or f"Stage: {stage.value}"
        )
        self.emit_event(event)
    
    def emit_conflict_detected(self,
                             file_path: Path,
                             conflict_type: str,
                             strategy: Optional[str] = None) -> None:
        """Emit conflict detected event."""
        event = ProgressEvent(
            event_type=ProgressEventType.CONFLICT_DETECTED,
            file_path=file_path,
            message=f"Conflict detected: {conflict_type}",
            metadata={
                "conflict_type": conflict_type,
                "strategy": strategy,
            }
        )
        self.emit_event(event)
    
    def emit_warning(self, message: str, file_path: Optional[Path] = None) -> None:
        """Emit warning event."""
        event = ProgressEvent(
            event_type=ProgressEventType.WARNING,
            file_path=file_path,
            message=message
        )
        self.emit_event(event)
    
    def emit_error(self, message: str, file_path: Optional[Path] = None, error: Optional[Exception] = None) -> None:
        """Emit error event."""
        metadata = {}
        if error:
            metadata["error_type"] = type(error).__name__
            metadata["error_details"] = str(error)
        
        event = ProgressEvent(
            event_type=ProgressEventType.ERROR,
            file_path=file_path,
            message=message,
            metadata=metadata
        )
        self.emit_event(event)
    
    def get_recent_events(self, count: int = 10) -> List[ProgressEvent]:
        """Get recent progress events.
        
        Args:
            count: Number of recent events to return
            
        Returns:
            List of recent events
        """
        return self.events[-count:] if self.events else []
    
    def get_events_by_type(self, event_type: ProgressEventType) -> List[ProgressEvent]:
        """Get all events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            
        Returns:
            List of matching events
        """
        return [event for event in self.events if event.event_type == event_type]
    
    def clear_events(self) -> None:
        """Clear all stored events."""
        self.events.clear()
        debug_logger.log("DEBUG", "Progress events cleared")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of progress events.
        
        Returns:
            Summary dictionary
        """
        if not self.events:
            return {"total_events": 0}
        
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        latest_event = self.events[-1] if self.events else None
        
        return {
            "total_events": len(self.events),
            "event_counts": event_counts,
            "latest_event": latest_event.to_dict() if latest_event else None,
            "timespan": {
                "start": self.events[0].timestamp.isoformat(),
                "end": self.events[-1].timestamp.isoformat(),
            } if self.events else None,
        }

# Global progress reporter instance
progress_reporter = ProgressReporter()
```

### Step 2: Create spec_cli/file_processing/processing_pipeline.py

```python
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from ..exceptions import SpecProcessingError
from ..templates.generator import SpecContentGenerator
from ..templates.loader import load_template
from ..logging.debug import debug_logger
from .change_detector import FileChangeDetector
from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy, ConflictInfo
from .progress_events import ProgressReporter, ProcessingStage

class FileProcessingResult:
    """Result of processing a single file."""
    
    def __init__(self,
                 file_path: Path,
                 success: bool,
                 generated_files: Optional[Dict[str, Path]] = None,
                 conflict_info: Optional[ConflictInfo] = None,
                 resolution_strategy: Optional[ConflictResolutionStrategy] = None,
                 errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.success = success
        self.generated_files = generated_files or {}
        self.conflict_info = conflict_info
        self.resolution_strategy = resolution_strategy
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": str(self.file_path),
            "success": self.success,
            "generated_files": {k: str(v) for k, v in self.generated_files.items()},
            "has_conflict": self.conflict_info is not None,
            "conflict_type": self.conflict_info.conflict_type.value if self.conflict_info else None,
            "resolution_strategy": self.resolution_strategy.value if self.resolution_strategy else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

class FileProcessingPipeline:
    """Pipeline for processing individual files through all stages."""
    
    def __init__(self,
                 content_generator: SpecContentGenerator,
                 change_detector: FileChangeDetector,
                 conflict_resolver: ConflictResolver,
                 progress_reporter: ProgressReporter):
        self.content_generator = content_generator
        self.change_detector = change_detector
        self.conflict_resolver = conflict_resolver
        self.progress_reporter = progress_reporter
        
        debug_logger.log("INFO", "FileProcessingPipeline initialized")
    
    def process_file(self,
                    file_path: Path,
                    custom_variables: Optional[Dict[str, Any]] = None,
                    conflict_strategy: Optional[ConflictResolutionStrategy] = None,
                    force_regenerate: bool = False) -> FileProcessingResult:
        """Process a single file through the complete pipeline.
        
        Args:
            file_path: Path to the file to process
            custom_variables: Optional custom template variables
            conflict_strategy: Strategy for conflict resolution
            force_regenerate: Whether to force regeneration even if unchanged
            
        Returns:
            FileProcessingResult with processing outcome
        """
        debug_logger.log("INFO", "Processing file through pipeline",
                        file_path=str(file_path))
        
        result = FileProcessingResult(file_path, success=False)
        
        try:
            with debug_logger.timer("file_processing_pipeline"):
                # Stage 1: Change Detection
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CHANGE_DETECTION
                )
                
                if not force_regenerate and not self.change_detector.has_file_changed(file_path):
                    result.success = True
                    result.warnings.append("File unchanged, skipping")
                    debug_logger.log("INFO", "File unchanged, skipping", file_path=str(file_path))
                    return result
                
                # Stage 2: Content Generation
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CONTENT_GENERATION
                )
                
                template = load_template()
                generation_result = self._generate_content(
                    file_path, template, custom_variables
                )
                
                if not generation_result["success"]:
                    result.errors.extend(generation_result["errors"])
                    return result
                
                generated_files = generation_result["generated_files"]
                
                # Stage 3: Conflict Detection and Resolution
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CONFLICT_DETECTION
                )
                
                conflicts_resolved = self._handle_conflicts(
                    generated_files, conflict_strategy
                )
                
                if conflicts_resolved["conflicts"]:
                    result.conflict_info = conflicts_resolved["conflicts"][0]  # First conflict for reference
                    result.resolution_strategy = conflicts_resolved["strategy_used"]
                
                if not conflicts_resolved["success"]:
                    result.errors.extend(conflicts_resolved["errors"])
                    return result
                
                # Stage 4: Cache Update
                self.progress_reporter.emit_stage_update(
                    file_path, ProcessingStage.CACHE_UPDATE
                )
                
                self.change_detector.update_file_cache(file_path)
                
                # Success
                result.success = True
                result.generated_files = generated_files
                result.warnings.extend(conflicts_resolved["warnings"])
            
            debug_logger.log("INFO", "File processing completed successfully",
                           file_path=str(file_path))
            
            return result
            
        except Exception as e:
            error_msg = f"File processing failed: {e}"
            debug_logger.log("ERROR", error_msg, file_path=str(file_path))
            result.errors.append(error_msg)
            return result
    
    def _generate_content(self,
                         file_path: Path,
                         template: Any,
                         custom_variables: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate content for the file."""
        try:
            generated_files = self.content_generator.generate_spec_content(
                file_path=file_path,
                template=template,
                custom_variables=custom_variables,
                backup_existing=False  # Conflict resolution handles backups
            )
            
            return {
                "success": True,
                "generated_files": generated_files,
                "errors": [],
            }
            
        except Exception as e:
            return {
                "success": False,
                "generated_files": {},
                "errors": [f"Content generation failed: {e}"],
            }
    
    def _handle_conflicts(self,
                         generated_files: Dict[str, Path],
                         strategy: Optional[ConflictResolutionStrategy]) -> Dict[str, Any]:
        """Handle conflicts for generated files."""
        conflicts = []
        resolved_conflicts = []
        errors = []
        warnings = []
        strategy_used = None
        
        try:
            # Check each generated file for conflicts
            for file_type, file_path in generated_files.items():
                if not file_path.exists():
                    continue  # No conflict for new files
                
                # Read the content that would be written
                try:
                    new_content = file_path.read_text(encoding='utf-8')
                except OSError as e:
                    errors.append(f"Could not read generated content for {file_path}: {e}")
                    continue
                
                # Detect conflict
                conflict = self.conflict_resolver.detect_conflict(file_path, new_content)
                if conflict:
                    conflicts.append(conflict)
                    
                    # Emit conflict detected event
                    self.progress_reporter.emit_conflict_detected(
                        file_path,
                        conflict.conflict_type.value,
                        strategy.value if strategy else None
                    )
                    
                    # Resolve conflict
                    resolution_result = self.conflict_resolver.resolve_conflict(
                        conflict, strategy, create_backup=True
                    )
                    
                    if resolution_result.success:
                        resolved_conflicts.append(resolution_result)
                        strategy_used = resolution_result.strategy_used
                        warnings.extend(resolution_result.warnings)
                    else:
                        errors.extend(resolution_result.errors)
            
            return {
                "success": len(errors) == 0,
                "conflicts": conflicts,
                "resolved_conflicts": resolved_conflicts,
                "strategy_used": strategy_used,
                "errors": errors,
                "warnings": warnings,
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflicts": conflicts,
                "resolved_conflicts": [],
                "strategy_used": None,
                "errors": [f"Conflict handling failed: {e}"],
                "warnings": warnings,
            }
    
    def validate_file_for_processing(self, file_path: Path) -> List[str]:
        """Validate that a file can be processed.
        
        Args:
            file_path: Path to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check file exists
        if not file_path.exists():
            issues.append(f"File does not exist: {file_path}")
            return issues
        
        # Check file is readable
        try:
            file_path.read_text(encoding='utf-8')
        except OSError as e:
            issues.append(f"Cannot read file {file_path}: {e}")
        
        # Check file size
        try:
            size = file_path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB limit
            if size > max_size:
                issues.append(f"File too large: {size} bytes (max {max_size})")
        except OSError as e:
            issues.append(f"Cannot get file stats for {file_path}: {e}")
        
        return issues
    
    def get_processing_estimate(self, files: List[Path]) -> Dict[str, Any]:
        """Estimate processing requirements for a list of files.
        
        Args:
            files: List of files to estimate
            
        Returns:
            Dictionary with processing estimates
        """
        estimate = {
            "total_files": len(files),
            "processable_files": 0,
            "files_needing_processing": 0,
            "estimated_duration_seconds": 0,
            "validation_issues": [],
        }
        
        for file_path in files:
            issues = self.validate_file_for_processing(file_path)
            if issues:
                estimate["validation_issues"].extend(issues)
                continue
            
            estimate["processable_files"] += 1
            
            # Check if file needs processing
            if self.change_detector.has_file_changed(file_path):
                estimate["files_needing_processing"] += 1
                
                # Rough time estimate (2 seconds per file)
                estimate["estimated_duration_seconds"] += 2
        
        return estimate
```

### Step 3: Create spec_cli/file_processing/batch_processor.py

```python
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from ..exceptions import SpecBatchProcessingError
from ..config.settings import get_settings, SpecSettings
from ..core.workflow_orchestrator import SpecWorkflowOrchestrator
from ..logging.debug import debug_logger
from .change_detector import FileChangeDetector
from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy
from .processing_pipeline import FileProcessingPipeline, FileProcessingResult
from .progress_events import ProgressReporter, ProgressEventType, progress_reporter

class BatchProcessingOptions:
    """Configuration options for batch processing."""
    
    def __init__(self,
                 max_files: Optional[int] = None,
                 max_parallel: int = 1,
                 force_regenerate: bool = False,
                 skip_unchanged: bool = True,
                 conflict_strategy: Optional[ConflictResolutionStrategy] = None,
                 create_backups: bool = True,
                 auto_commit: bool = False,
                 custom_variables: Optional[Dict[str, Any]] = None):
        self.max_files = max_files
        self.max_parallel = max_parallel
        self.force_regenerate = force_regenerate
        self.skip_unchanged = skip_unchanged
        self.conflict_strategy = conflict_strategy or ConflictResolutionStrategy.MERGE_INTELLIGENT
        self.create_backups = create_backups
        self.auto_commit = auto_commit
        self.custom_variables = custom_variables or {}

class BatchProcessingResult:
    """Result of batch processing operation."""
    
    def __init__(self):
        self.success = False
        self.total_files = 0
        self.successful_files: List[Path] = []
        self.failed_files: List[Path] = []
        self.skipped_files: List[Path] = []
        self.file_results: Dict[str, FileProcessingResult] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.workflow_id: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.change_detector = FileChangeDetector(self.settings)
        self.conflict_resolver = ConflictResolver(self.settings)
        self.workflow_orchestrator = SpecWorkflowOrchestrator(self.settings)
        self.progress_reporter = progress_reporter
        
        # Create processing pipeline
        from ..templates.generator import SpecContentGenerator
        content_generator = SpecContentGenerator(self.settings)
        
        self.pipeline = FileProcessingPipeline(
            content_generator=content_generator,
            change_detector=self.change_detector,
            conflict_resolver=self.conflict_resolver,
            progress_reporter=self.progress_reporter
        )
        
        debug_logger.log("INFO", "BatchFileProcessor initialized")
    
    def process_files(self,
                     file_paths: List[Path],
                     options: Optional[BatchProcessingOptions] = None,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None) -> BatchProcessingResult:
        """Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            options: Batch processing options
            progress_callback: Optional progress callback function
            
        Returns:
            BatchProcessingResult with processing outcomes
        """
        options = options or BatchProcessingOptions()
        
        debug_logger.log("INFO", "Starting batch file processing",
                        total_files=len(file_paths),
                        max_files=options.max_files,
                        force_regenerate=options.force_regenerate)
        
        result = BatchProcessingResult()
        result.start_time = time.time()
        
        try:
            with debug_logger.timer("batch_file_processing"):
                # Limit files if specified
                files_to_process = file_paths
                if options.max_files and len(file_paths) > options.max_files:
                    files_to_process = file_paths[:options.max_files]
                    result.warnings.append(f"Limited to {options.max_files} files")
                
                result.total_files = len(files_to_process)
                
                # Filter files that need processing (unless force regenerate)
                if not options.force_regenerate and options.skip_unchanged:
                    files_needing_processing = self.change_detector.get_files_needing_processing(
                        files_to_process, force_all=False
                    )
                    
                    # Track skipped files
                    skipped = set(files_to_process) - set(files_needing_processing)
                    result.skipped_files.extend(skipped)
                    
                    files_to_process = files_needing_processing
                    
                    debug_logger.log("INFO", "Filtered files needing processing",
                                   original_count=result.total_files,
                                   processing_count=len(files_to_process),
                                   skipped_count=len(skipped))
                
                # Emit batch started event
                self.progress_reporter.emit_batch_started(
                    len(files_to_process),
                    f"Processing {len(files_to_process)} files"
                )
                
                # Process files
                self._process_files_sequentially(
                    files_to_process, options, result, progress_callback
                )
                
                # Handle post-processing
                if options.auto_commit and result.successful_files:
                    self._handle_auto_commit(result, options)
                
                # Finalize result
                result.success = len(result.errors) == 0
                result.end_time = time.time()
                
                # Emit batch completed event
                self.progress_reporter.emit_batch_completed(
                    result.total_files,
                    len(result.successful_files),
                    len(result.failed_files),
                    result.duration
                )
            
            debug_logger.log("INFO", "Batch file processing completed",
                           total_files=result.total_files,
                           successful=len(result.successful_files),
                           failed=len(result.failed_files),
                           duration=result.duration)
            
            return result
            
        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            debug_logger.log("ERROR", error_msg)
            
            result.errors.append(error_msg)
            result.success = False
            result.end_time = time.time()
            
            # Emit batch failed event
            self.progress_reporter.emit_event(
                ProgressEventType.BATCH_FAILED,
                message=error_msg
            )
            
            return result
    
    def _process_files_sequentially(self,
                                   files: List[Path],
                                   options: BatchProcessingOptions,
                                   result: BatchProcessingResult,
                                   progress_callback: Optional[Callable[[int, int, str], None]]) -> None:
        """Process files sequentially."""
        for i, file_path in enumerate(files):
            try:
                # Emit file started event
                self.progress_reporter.emit_file_started(file_path, i, len(files))
                
                # Progress callback
                if progress_callback:
                    progress_callback(i, len(files), f"Processing {file_path.name}")
                
                # Process single file
                file_result = self.pipeline.process_file(
                    file_path=file_path,
                    custom_variables=options.custom_variables,
                    conflict_strategy=options.conflict_strategy,
                    force_regenerate=options.force_regenerate
                )
                
                # Store result
                result.file_results[str(file_path)] = file_result
                
                # Categorize result
                if file_result.success:
                    result.successful_files.append(file_path)
                    
                    # Emit file completed event
                    self.progress_reporter.emit_file_completed(file_path, i, len(files), True)
                else:
                    result.failed_files.append(file_path)
                    result.errors.extend(file_result.errors)
                    
                    # Emit file failed event
                    self.progress_reporter.emit_file_completed(file_path, i, len(files), False)
                    
                    # Emit error event
                    error_msg = f"Processing failed for {file_path}: {'; '.join(file_result.errors)}"
                    self.progress_reporter.emit_error(error_msg, file_path)
                
                # Add warnings
                result.warnings.extend(file_result.warnings)
                
            except Exception as e:
                error_msg = f"Unexpected error processing {file_path}: {e}"
                debug_logger.log("ERROR", error_msg)
                
                result.failed_files.append(file_path)
                result.errors.append(error_msg)
                
                # Emit error event
                self.progress_reporter.emit_error(error_msg, file_path, e)
        
        # Final progress callback
        if progress_callback:
            progress_callback(len(files), len(files), "Completed")
    
    def _handle_auto_commit(self, result: BatchProcessingResult, options: BatchProcessingOptions) -> None:
        """Handle automatic commit of successful files."""
        try:
            debug_logger.log("INFO", "Handling auto-commit",
                           successful_files=len(result.successful_files))
            
            # Use workflow orchestrator for commit
            workflow_result = self.workflow_orchestrator.generate_specs_for_files(
                result.successful_files,
                custom_variables=options.custom_variables,
                auto_commit=True,
                create_backup=options.create_backups
            )
            
            result.workflow_id = workflow_result.get("workflow_id")
            
            if not workflow_result.get("success"):
                result.warnings.append("Auto-commit failed")
                
        except Exception as e:
            result.warnings.append(f"Auto-commit failed: {e}")
            debug_logger.log("WARNING", "Auto-commit failed", error=str(e))
    
    def estimate_batch_processing(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Estimate batch processing requirements.
        
        Args:
            file_paths: List of files to estimate
            
        Returns:
            Dictionary with processing estimates
        """
        return self.pipeline.get_processing_estimate(file_paths)
    
    def validate_batch_processing(self,
                                file_paths: List[Path],
                                options: Optional[BatchProcessingOptions] = None) -> List[str]:
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
    
    def get_processing_summary(self, result: BatchProcessingResult) -> Dict[str, Any]:
        """Get a summary of batch processing results.
        
        Args:
            result: Batch processing result
            
        Returns:
            Summary dictionary
        """
        summary = {
            "overview": {
                "total_files": result.total_files,
                "successful": len(result.successful_files),
                "failed": len(result.failed_files),
                "skipped": len(result.skipped_files),
                "success_rate": (
                    len(result.successful_files) / result.total_files * 100
                    if result.total_files > 0 else 0
                ),
                "duration": result.duration,
            },
            "conflicts": {
                "files_with_conflicts": 0,
                "conflict_types": {},
                "resolution_strategies": {},
            },
            "errors": {
                "total_errors": len(result.errors),
                "error_types": {},
            },
            "warnings": {
                "total_warnings": len(result.warnings),
            },
        }
        
        # Analyze file results for conflicts and errors
        for file_result in result.file_results.values():
            if file_result.conflict_info:
                summary["conflicts"]["files_with_conflicts"] += 1
                
                conflict_type = file_result.conflict_info.conflict_type.value
                summary["conflicts"]["conflict_types"][conflict_type] = \
                    summary["conflicts"]["conflict_types"].get(conflict_type, 0) + 1
                
                if file_result.resolution_strategy:
                    strategy = file_result.resolution_strategy.value
                    summary["conflicts"]["resolution_strategies"][strategy] = \
                        summary["conflicts"]["resolution_strategies"].get(strategy, 0) + 1
            
            # Analyze errors (simplified)
            for error in file_result.errors:
                if "permission" in error.lower():
                    error_type = "permission"
                elif "conflict" in error.lower():
                    error_type = "conflict"
                elif "generation" in error.lower():
                    error_type = "generation"
                else:
                    error_type = "other"
                
                summary["errors"]["error_types"][error_type] = \
                    summary["errors"]["error_types"].get(error_type, 0) + 1
        
        return summary

# Convenience functions
def process_files_batch(file_paths: List[Path],
                       **kwargs) -> BatchProcessingResult:
    """Convenience function for batch processing."""
    processor = BatchFileProcessor()
    options = BatchProcessingOptions(**kwargs)
    return processor.process_files(file_paths, options)

def estimate_processing_time(file_paths: List[Path]) -> Dict[str, Any]:
    """Convenience function for processing estimation."""
    processor = BatchFileProcessor()
    return processor.estimate_batch_processing(file_paths)
```

### Step 4: Update spec_cli/file_processing/__init__.py

```python
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
```

## Test Requirements

Create comprehensive tests for batch processing:

### Test Cases (18 tests total)

**Progress Events Tests:**
1. **test_progress_event_creation_and_serialization**
2. **test_progress_reporter_listener_management**
3. **test_progress_reporter_event_emission**
4. **test_progress_reporter_event_storage_and_retrieval**

**Processing Pipeline Tests:**
5. **test_file_processing_pipeline_complete_flow**
6. **test_pipeline_change_detection_integration**
7. **test_pipeline_conflict_resolution_integration**
8. **test_pipeline_content_generation_integration**
9. **test_pipeline_validation_and_estimation**

**Batch Processor Tests:**
10. **test_batch_processor_sequential_processing**
11. **test_batch_processor_progress_tracking**
12. **test_batch_processor_conflict_handling**
13. **test_batch_processor_error_recovery**
14. **test_batch_processor_auto_commit_integration**
15. **test_batch_processing_options_configuration**
16. **test_batch_processing_validation**
17. **test_batch_processing_estimation**
18. **test_batch_processing_summary_generation**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_processing/test_batch_processor.py tests/unit/file_processing/test_progress_events.py tests/unit/file_processing/test_processing_pipeline.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_processing/ --cov=spec_cli.file_processing --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_processing/

# Check code formatting
poetry run ruff check spec_cli/file_processing/
poetry run ruff format spec_cli/file_processing/

# Verify imports work correctly
python -c "from spec_cli.file_processing import BatchFileProcessor, BatchProcessingOptions, progress_reporter; print('Import successful')"

# Test progress events
python -c "
from spec_cli.file_processing.progress_events import ProgressReporter, ProgressEventType, ProcessingStage
from pathlib import Path

reporter = ProgressReporter()

# Add listener
def print_event(event):
    print(f'Event: {event.event_type.value} - {event.message}')

reporter.add_listener(print_event)

# Emit some events
reporter.emit_batch_started(5, 'Test batch')
reporter.emit_file_started(Path('test.py'), 0, 5)
reporter.emit_stage_update(Path('test.py'), ProcessingStage.CONTENT_GENERATION, 'Generating content')
reporter.emit_file_completed(Path('test.py'), 0, 5, True)
reporter.emit_batch_completed(5, 4, 1, 10.5)

# Get summary
summary = reporter.get_summary()
print(f'\nEvent summary: {summary["total_events"]} events')
"

# Test batch processing options
python -c "
from spec_cli.file_processing.batch_processor import BatchProcessingOptions
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy

# Create options
options = BatchProcessingOptions(
    max_files=100,
    force_regenerate=True,
    conflict_strategy=ConflictResolutionStrategy.MERGE_INTELLIGENT,
    auto_commit=True
)

print(f'Batch options:')
print(f'  Max files: {options.max_files}')
print(f'  Force regenerate: {options.force_regenerate}')
print(f'  Conflict strategy: {options.conflict_strategy.value}')
print(f'  Auto commit: {options.auto_commit}')
"

# Test processing pipeline validation
python -c "
from spec_cli.file_processing.processing_pipeline import FileProcessingPipeline
from spec_cli.file_processing.change_detector import FileChangeDetector
from spec_cli.file_processing.conflict_resolver import ConflictResolver
from spec_cli.file_processing.progress_events import ProgressReporter
from spec_cli.templates.generator import SpecContentGenerator
from pathlib import Path
import tempfile

# Create pipeline components
content_generator = SpecContentGenerator()
change_detector = FileChangeDetector()
conflict_resolver = ConflictResolver()
progress_reporter = ProgressReporter()

pipeline = FileProcessingPipeline(
    content_generator, change_detector, conflict_resolver, progress_reporter
)

# Test validation
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
    f.write('print(\"Hello, World!\")')
    test_file = Path(f.name)

try:
    # Validate file
    issues = pipeline.validate_file_for_processing(test_file)
    print(f'Validation issues: {len(issues)}')
    
    # Get estimate
    estimate = pipeline.get_processing_estimate([test_file])
    print(f'Processing estimate:')
    for key, value in estimate.items():
        if key != 'validation_issues':
            print(f'  {key}: {value}')
            
finally:
    test_file.unlink()
"

# Test batch processor estimation
python -c "
from spec_cli.file_processing.batch_processor import BatchFileProcessor
from pathlib import Path

processor = BatchFileProcessor()

# Test with current Python files (limited)
current_dir = Path.cwd()
python_files = list(current_dir.glob('**/*.py'))[:5]  # Limit to 5 files

if python_files:
    estimate = processor.estimate_batch_processing(python_files)
    print(f'Batch processing estimate for {len(python_files)} files:')
    for key, value in estimate.items():
        if key != 'validation_issues':
            print(f'  {key}: {value}')
    
    if estimate['validation_issues']:
        print(f'  Validation issues: {len(estimate["validation_issues"])}')
else:
    print('No Python files found for estimation')
"
```

## Definition of Done

- [ ] BatchFileProcessor class for coordinating batch operations
- [ ] Progress event system with comprehensive event types
- [ ] FileProcessingPipeline for individual file processing workflows
- [ ] Integration with change detection from slice-11a
- [ ] Integration with conflict resolution from slice-11b
- [ ] Progress tracking and event emission throughout processing
- [ ] Error recovery and batch operation rollback capabilities
- [ ] Processing estimation and validation utilities
- [ ] Integration with workflow orchestration from slice-10c
- [ ] All 18 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Comprehensive batch processing with progress events
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice completes **PHASE-4** (Git and Core Logic) by providing:
- Complete file processing infrastructure that PHASE-5 can build upon
- Progress event system that Rich UI components can consume
- Batch processing capabilities that CLI commands can leverage
- Integration foundation for comprehensive spec generation workflows