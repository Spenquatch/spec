from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

    def __init__(self) -> None:
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
        debug_logger.log(
            "DEBUG", "Progress listener added", total_listeners=len(self.listeners)
        )

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
            self.events = self.events[-self.max_events // 2 :]  # Keep most recent half

        # Notify listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                debug_logger.log("WARNING", "Progress listener failed", error=str(e))

        # Log important events
        if event.event_type in [
            ProgressEventType.BATCH_STARTED,
            ProgressEventType.BATCH_COMPLETED,
            ProgressEventType.BATCH_FAILED,
            ProgressEventType.ERROR,
        ]:
            debug_logger.log(
                "INFO",
                f"Progress event: {event.event_type.value}",
                event_type=event.event_type.value,
            )

    def emit_batch_started(
        self, total_files: int, message: Optional[str] = None
    ) -> None:
        """Emit batch started event."""
        event = ProgressEvent(
            event_type=ProgressEventType.BATCH_STARTED,
            total_files=total_files,
            processed_files=0,
            progress=0.0,
            message=message or f"Starting batch processing of {total_files} files",
        )
        self.emit_event(event)

    def emit_batch_completed(
        self,
        total_files: int,
        successful_files: int,
        failed_files: int,
        duration: Optional[float] = None,
    ) -> None:
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
            },
        )
        self.emit_event(event)

    def emit_file_started(
        self, file_path: Path, file_index: int, total_files: int
    ) -> None:
        """Emit file processing started event."""
        progress = file_index / total_files if total_files > 0 else 0.0
        event = ProgressEvent(
            event_type=ProgressEventType.FILE_STARTED,
            file_path=file_path,
            total_files=total_files,
            processed_files=file_index,
            progress=progress,
            message=f"Processing {file_path.name}",
        )
        self.emit_event(event)

    def emit_file_completed(
        self, file_path: Path, file_index: int, total_files: int, success: bool = True
    ) -> None:
        """Emit file processing completed event."""
        progress = (file_index + 1) / total_files if total_files > 0 else 1.0
        event_type = (
            ProgressEventType.FILE_COMPLETED
            if success
            else ProgressEventType.FILE_FAILED
        )

        event = ProgressEvent(
            event_type=event_type,
            file_path=file_path,
            total_files=total_files,
            processed_files=file_index + 1,
            progress=progress,
            message=f"{'Completed' if success else 'Failed'} {file_path.name}",
        )
        self.emit_event(event)

    def emit_stage_update(
        self, file_path: Path, stage: ProcessingStage, message: Optional[str] = None
    ) -> None:
        """Emit processing stage update."""
        event = ProgressEvent(
            event_type=ProgressEventType.STAGE_STARTED,
            file_path=file_path,
            stage=stage,
            message=message or f"Stage: {stage.value}",
        )
        self.emit_event(event)

    def emit_conflict_detected(
        self, file_path: Path, conflict_type: str, strategy: Optional[str] = None
    ) -> None:
        """Emit conflict detected event."""
        event = ProgressEvent(
            event_type=ProgressEventType.CONFLICT_DETECTED,
            file_path=file_path,
            message=f"Conflict detected: {conflict_type}",
            metadata={
                "conflict_type": conflict_type,
                "strategy": strategy,
            },
        )
        self.emit_event(event)

    def emit_warning(self, message: str, file_path: Optional[Path] = None) -> None:
        """Emit warning event."""
        event = ProgressEvent(
            event_type=ProgressEventType.WARNING, file_path=file_path, message=message
        )
        self.emit_event(event)

    def emit_error(
        self,
        message: str,
        file_path: Optional[Path] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Emit error event."""
        metadata = {}
        if error:
            metadata["error_type"] = type(error).__name__
            metadata["error_details"] = str(error)

        event = ProgressEvent(
            event_type=ProgressEventType.ERROR,
            file_path=file_path,
            message=message,
            metadata=metadata,
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

        event_counts: Dict[str, int] = {}
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
            }
            if self.events
            else None,
        }


# Global progress reporter instance
progress_reporter = ProgressReporter()
