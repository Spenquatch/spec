import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from ..core.error_handler import ErrorHandler
from ..file_processing.progress_events import (
    ProcessingStage,
    ProgressEvent,
    ProgressEventType,
    ProgressReporter,
    progress_reporter,
)
from ..logging.debug import debug_logger
from ..utils.singleton import reset_singleton, singleton_decorator
from .console import get_console
from .progress_bar import SpecProgressBar
from .spinner import SpinnerManager


@dataclass
class ProgressState:
    """Represents the current state of a progress operation."""

    operation_id: str
    total_items: int
    completed_items: int
    current_item: Optional[str] = None
    stage: Optional[ProcessingStage] = None
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage (0.0 to 1.0)."""
        if self.total_items == 0:
            return 0.0
        return self.completed_items / self.total_items

    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return None
        return time.time() - self.start_time


class ProgressManager:
    """Coordinates progress display and integrates with progress events."""

    def __init__(
        self,
        progress_reporter_instance: Optional[ProgressReporter] = None,
        auto_display: bool = True,
    ) -> None:
        """Initialize progress manager.

        Args:
            progress_reporter_instance: Progress event reporter to use
            auto_display: Whether to automatically show/hide progress displays
        """
        self.progress_reporter = progress_reporter_instance or progress_reporter
        self.auto_display = auto_display
        self.error_handler = ErrorHandler({"component": "progress_manager"})

        # Progress tracking
        self.progress_states: Dict[str, ProgressState] = {}
        self.active_operations: Dict[str, str] = {}  # operation_id -> display_type

        # Display components
        self.progress_bar = SpecProgressBar(
            show_percentage=True, show_time_remaining=True, auto_refresh=True
        )
        self.spinner_manager = SpinnerManager()

        # Event handling
        self._event_handlers: Dict[ProgressEventType, List[Callable]] = {}
        self._setup_event_handling()

        debug_logger.log(
            "INFO", "ProgressManager initialized", auto_display=auto_display
        )

    def _setup_event_handling(self) -> None:
        """Set up progress event handling."""
        # Register as listener for progress events
        self.progress_reporter.add_listener(self._handle_progress_event)

        # Set up default event handlers
        self._event_handlers = {
            ProgressEventType.BATCH_STARTED: [self._handle_batch_started],
            ProgressEventType.BATCH_COMPLETED: [self._handle_batch_completed],
            ProgressEventType.BATCH_FAILED: [self._handle_batch_failed],
            ProgressEventType.FILE_STARTED: [self._handle_file_started],
            ProgressEventType.FILE_COMPLETED: [self._handle_file_completed],
            ProgressEventType.FILE_FAILED: [self._handle_file_failed],
            ProgressEventType.STAGE_STARTED: [self._handle_stage_started],
            ProgressEventType.PROGRESS_UPDATE: [self._handle_progress_update],
        }

    def _handle_progress_event(self, event: ProgressEvent) -> None:
        """Handle incoming progress events.

        Args:
            event: Progress event to handle
        """
        handlers = self._event_handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log the error but don't stop processing other handlers
                self.error_handler.report(
                    e,
                    "handle progress event",
                    event_type=event.event_type.value,
                    handler_name=handler.__name__
                    if hasattr(handler, "__name__")
                    else str(handler),
                    progress_operation="progress_event_handling",
                )
                # Continue processing other handlers

    def _handle_batch_started(self, event: ProgressEvent) -> None:
        """Handle batch started event."""
        operation_id = f"batch_{int(time.time())}"

        state = ProgressState(
            operation_id=operation_id,
            total_items=event.total_files or 0,
            completed_items=0,
            start_time=time.time(),
        )

        self.progress_states[operation_id] = state

        if self.auto_display and event.total_files:
            # Use progress bar for determinate operations
            self.progress_bar.start()
            task_id = self.progress_bar.add_task(
                event.message or "Processing files", total=event.total_files
            )
            self.active_operations[operation_id] = f"progress_bar:{task_id}"

        debug_logger.log(
            "INFO",
            "Batch operation started",
            operation_id=operation_id,
            total_files=event.total_files,
        )

    def _handle_batch_completed(self, event: ProgressEvent) -> None:
        """Handle batch completed event."""
        # Find the matching operation
        operation_id = self._find_active_operation()
        if not operation_id:
            return

        state = self.progress_states.get(operation_id)
        if state:
            state.completed_items = state.total_items

        self._cleanup_operation(operation_id)

        # Show completion message
        console = get_console()
        console.print_status(event.message or "Batch operation completed", "success")

        debug_logger.log("INFO", "Batch operation completed", operation_id=operation_id)

    def _handle_batch_failed(self, event: ProgressEvent) -> None:
        """Handle batch failed event."""
        operation_id = self._find_active_operation()
        if operation_id:
            self._cleanup_operation(operation_id)

        # Show error message
        console = get_console()
        console.print_status(event.message or "Batch operation failed", "error")

        debug_logger.log("ERROR", "Batch operation failed")

    def _handle_file_started(self, event: ProgressEvent) -> None:
        """Handle file processing started event."""
        operation_id = self._find_active_operation()
        if not operation_id:
            return

        state = self.progress_states.get(operation_id)
        if state:
            state.current_item = str(event.file_path) if event.file_path else None

        # Update progress display
        self._update_progress_display(operation_id, event)

    def _handle_file_completed(self, event: ProgressEvent) -> None:
        """Handle file processing completed event."""
        operation_id = self._find_active_operation()
        if not operation_id:
            return

        state = self.progress_states.get(operation_id)
        if state:
            state.completed_items = event.processed_files or state.completed_items + 1

        # Update progress display
        self._update_progress_display(operation_id, event)

    def _handle_file_failed(self, event: ProgressEvent) -> None:
        """Handle file processing failed event."""
        # Same as completed for progress tracking
        self._handle_file_completed(event)

    def _handle_stage_started(self, event: ProgressEvent) -> None:
        """Handle processing stage started event."""
        operation_id = self._find_active_operation()
        if not operation_id:
            return

        state = self.progress_states.get(operation_id)
        if state:
            state.stage = event.stage

        # Update display with stage information
        if event.stage:
            stage_text = f"Stage: {event.stage.value}"
            self._update_operation_text(operation_id, stage_text)

    def _handle_progress_update(self, event: ProgressEvent) -> None:
        """Handle general progress update event."""
        operation_id = self._find_active_operation()
        if not operation_id:
            return

        self._update_progress_display(operation_id, event)

    def _update_progress_display(self, operation_id: str, event: ProgressEvent) -> None:
        """Update the progress display for an operation."""
        display_info = self.active_operations.get(operation_id)
        if not display_info:
            return

        state = self.progress_states.get(operation_id)
        if not state:
            return

        if display_info.startswith("progress_bar:"):
            # Update progress bar
            task_id = display_info.split(":", 1)[1]

            description = event.message or "Processing"
            if state.current_item:
                description = f"{description}: {state.current_item}"

            self.progress_bar.update_task(
                task_id, completed=state.completed_items, description=description
            )

        elif display_info.startswith("spinner:"):
            # Update spinner
            spinner_id = display_info.split(":", 1)[1]

            text = event.message or "Processing"
            if state.current_item:
                text = f"{text}: {state.current_item}"

            self.spinner_manager.update_spinner_text(spinner_id, text)

    def _update_operation_text(self, operation_id: str, text: str) -> None:
        """Update the text for an operation display."""
        display_info = self.active_operations.get(operation_id)
        if not display_info:
            return

        if display_info.startswith("spinner:"):
            spinner_id = display_info.split(":", 1)[1]
            self.spinner_manager.update_spinner_text(spinner_id, text)

    def _find_active_operation(self) -> Optional[str]:
        """Find the currently active operation."""
        # For now, just return the first active operation
        # In the future, this could be more sophisticated
        return next(iter(self.active_operations.keys()), None)

    def _cleanup_operation(self, operation_id: str) -> None:
        """Clean up resources for a completed operation."""
        display_info = self.active_operations.get(operation_id)
        if display_info:
            if display_info.startswith("progress_bar:"):
                task_id = display_info.split(":", 1)[1]
                self.progress_bar.remove_task(task_id)
                if not self.progress_bar.tasks:
                    self.progress_bar.stop()

            elif display_info.startswith("spinner:"):
                spinner_id = display_info.split(":", 1)[1]
                self.spinner_manager.remove_spinner(spinner_id)

        # Clean up tracking
        self.active_operations.pop(operation_id, None)
        self.progress_states.pop(operation_id, None)

        debug_logger.log("DEBUG", "Operation cleaned up", operation_id=operation_id)

    def start_indeterminate_operation(
        self, operation_id: str, message: str = "Processing..."
    ) -> None:
        """Start an indeterminate progress operation (spinner).

        Args:
            operation_id: Unique operation identifier
            message: Message to display
        """
        self.spinner_manager.create_spinner(operation_id, message)
        self.spinner_manager.start_spinner(operation_id)

        self.active_operations[operation_id] = f"spinner:{operation_id}"

        state = ProgressState(
            operation_id=operation_id,
            total_items=0,
            completed_items=0,
            start_time=time.time(),
        )
        self.progress_states[operation_id] = state

        debug_logger.log(
            "INFO", "Indeterminate operation started", operation_id=operation_id
        )

    def finish_operation(self, operation_id: str) -> None:
        """Finish a progress operation.

        Args:
            operation_id: Operation identifier
        """
        self._cleanup_operation(operation_id)
        debug_logger.log("INFO", "Operation finished", operation_id=operation_id)

    def get_operation_state(self, operation_id: str) -> Optional[ProgressState]:
        """Get the state of a progress operation.

        Args:
            operation_id: Operation identifier

        Returns:
            ProgressState or None if not found
        """
        return self.progress_states.get(operation_id)

    def add_event_handler(
        self,
        event_type: ProgressEventType,
        handler: Callable[[ProgressEvent], None],
    ) -> None:
        """Add a custom event handler.

        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

        self._event_handlers[event_type].append(handler)
        debug_logger.log("DEBUG", "Event handler added", event_type=event_type.value)

    def remove_event_handler(
        self,
        event_type: ProgressEventType,
        handler: Callable[[ProgressEvent], None],
    ) -> bool:
        """Remove a custom event handler.

        Args:
            event_type: Type of event
            handler: Handler function to remove

        Returns:
            True if handler was removed
        """
        if event_type not in self._event_handlers:
            return False

        try:
            self._event_handlers[event_type].remove(handler)
            debug_logger.log(
                "DEBUG", "Event handler removed", event_type=event_type.value
            )
            return True
        except ValueError:
            return False

    def cleanup(self) -> None:
        """Clean up all progress operations and displays."""
        # Stop all progress displays
        self.spinner_manager.stop_all()
        self.progress_bar.stop()

        # Clear tracking
        self.active_operations.clear()
        self.progress_states.clear()

        debug_logger.log("INFO", "ProgressManager cleaned up")


@singleton_decorator
class ProgressManagerSingleton:
    """Manages global progress manager instances."""

    def __init__(self) -> None:
        """Initialize progress manager singleton."""
        self._progress_manager: Optional[ProgressManager] = None
        self._lock = threading.Lock()

    def get_progress_manager(self) -> ProgressManager:
        """Get the global progress manager instance.

        Returns:
            Global ProgressManager instance
        """
        if self._progress_manager is None:
            with self._lock:
                if self._progress_manager is None:
                    self._progress_manager = ProgressManager()
                    debug_logger.log("INFO", "Global progress manager initialized")

        return self._progress_manager

    def set_progress_manager(self, manager: ProgressManager) -> None:
        """Set the global progress manager.

        Args:
            manager: ProgressManager instance to set as global
        """
        with self._lock:
            self._progress_manager = manager
            debug_logger.log("INFO", "Global progress manager updated")

    def reset(self) -> None:
        """Reset the global progress manager."""
        with self._lock:
            if self._progress_manager:
                self._progress_manager.cleanup()
            self._progress_manager = None
            debug_logger.log("INFO", "Global progress manager reset")


# Convenience functions for getting progress manager
def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance."""
    return ProgressManagerSingleton().get_progress_manager()


def set_progress_manager(manager: ProgressManager) -> None:
    """Set the global progress manager."""
    ProgressManagerSingleton().set_progress_manager(manager)


def reset_progress_manager() -> None:
    """Reset the global progress manager."""
    manager = ProgressManagerSingleton()
    manager.reset()
    reset_singleton(ProgressManagerSingleton)
