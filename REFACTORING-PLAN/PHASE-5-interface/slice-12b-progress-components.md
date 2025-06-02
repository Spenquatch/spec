# Slice 12B: Progress Components

## Goal

Create spinner/progress-bar wrappers and a progress manager that emits events, providing Rich-based progress tracking with integration to batch processing events.

## Context

Building on the console and theme foundation from slice-12a, this slice implements progress tracking components that integrate with the progress event system from slice-11c-batch-processor. It provides both simple progress indicators and comprehensive progress management with event emission and tracking.

## Scope

**Included in this slice:**
- Progress bar wrappers with Rich integration
- Spinner components for indeterminate operations
- Progress manager that coordinates multiple progress displays
- Integration with progress events from batch processing
- Progress tracking utilities and helpers
- Mock-friendly progress components for testing

**NOT included in this slice:**
- Complex table/tree formatters (comes in slice-12c)
- Error display panels (comes in slice-12c)
- CLI command integration (comes in slice-13)
- Interactive progress dialogs

## Prerequisites

**Required modules that must exist:**
- `spec_cli.ui.console` (SpecConsole from slice-12a)
- `spec_cli.ui.theme` (SpecTheme from slice-12a)
- `spec_cli.file_processing.progress_events` (ProgressReporter from slice-11c)
- `spec_cli.logging.debug` (debug_logger for progress tracking)

**Required functions/classes:**
- `SpecConsole` and `get_console()` from slice-12a-console-theme
- `SpecTheme` and `get_current_theme()` from slice-12a-console-theme
- `ProgressReporter`, `ProgressEvent`, `ProgressEventType` from slice-11c-batch-processor
- All exception classes from slice-1-exceptions

## Files to Create

```
spec_cli/ui/
├── progress_bar.py      # Progress bar components
├── spinner.py          # Spinner components
├── progress_manager.py # Progress coordination and management
└── progress_utils.py   # Progress utilities and helpers
```

## Implementation Steps

### Step 1: Create spec_cli/ui/progress_bar.py

```python
import time
from typing import Optional, Any, Dict, Callable
from rich.progress import (
    Progress, ProgressColumn, BarColumn, TextColumn, 
    TimeElapsedColumn, TimeRemainingColumn, SpinnerColumn,
    TaskID
)
from rich.console import Console
from contextlib import contextmanager
from ..logging.debug import debug_logger
from .console import get_console

class SpecProgressBar:
    """Spec-specific progress bar wrapper with Rich integration."""
    
    def __init__(self, 
                 console: Optional[Console] = None,
                 show_percentage: bool = True,
                 show_time_elapsed: bool = True,
                 show_time_remaining: bool = True,
                 show_speed: bool = False,
                 auto_refresh: bool = True,
                 refresh_per_second: int = 10):
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
        
        self.tasks: Dict[str, TaskID] = {}
        self._is_started = False
        
        debug_logger.log("INFO", "SpecProgressBar initialized",
                        columns=len(columns),
                        auto_refresh=auto_refresh)
    
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
    
    def add_task(self, 
                description: str,
                total: Optional[int] = None,
                task_id: Optional[str] = None) -> str:
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
        
        debug_logger.log("DEBUG", "Progress task added",
                        task_id=task_id, description=description, total=total)
        
        return task_id
    
    def update_task(self, 
                   task_id: str,
                   advance: Optional[int] = None,
                   completed: Optional[int] = None,
                   total: Optional[int] = None,
                   description: Optional[str] = None,
                   **kwargs) -> None:
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
        
        update_kwargs = {}
        if advance is not None:
            update_kwargs["advance"] = advance
        if completed is not None:
            update_kwargs["completed"] = completed
        if total is not None:
            update_kwargs["total"] = total
        if description is not None:
            update_kwargs["description"] = description
        
        # Add custom data
        update_kwargs.update(kwargs)
        
        self.progress.update(rich_task_id, **update_kwargs)
        
        debug_logger.log("DEBUG", "Progress task updated",
                        task_id=task_id, **update_kwargs)
    
    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed.
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.tasks:
            debug_logger.log("WARNING", "Task not found for completion", task_id=task_id)
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
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
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
    def task_context(self, 
                    description: str,
                    total: Optional[int] = None,
                    task_id: Optional[str] = None):
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
    
    def __enter__(self):
        """Enter context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.stop()

class SimpleProgressBar:
    """Simplified progress bar for basic use cases."""
    
    def __init__(self, total: int, description: str = "Processing"):
        """Initialize simple progress bar.
        
        Args:
            total: Total number of items
            description: Progress description
        """
        self.total = total
        self.description = description
        self.completed = 0
        self.progress_bar = SpecProgressBar(
            show_time_remaining=True,
            show_percentage=True
        )
        self.task_id = None
    
    def start(self) -> None:
        """Start the progress bar."""
        self.progress_bar.start()
        self.task_id = self.progress_bar.add_task(
            self.description, 
            total=self.total
        )
    
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
    
    def __enter__(self):
        """Enter context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.finish()

# Convenience functions
def create_progress_bar(**kwargs) -> SpecProgressBar:
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
```

### Step 2: Create spec_cli/ui/spinner.py

```python
import time
import threading
from typing import Optional, Any
from rich.spinner import Spinner
from rich.console import Console
from rich.live import Live
from rich.text import Text
from contextlib import contextmanager
from ..logging.debug import debug_logger
from .console import get_console

class SpecSpinner:
    """Spec-specific spinner component with Rich integration."""
    
    def __init__(self,
                 text: str = "Loading...",
                 spinner_style: str = "dots",
                 console: Optional[Console] = None,
                 speed: float = 1.0):
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
        self.live: Optional[Live] = None
        self._is_running = False
        
        debug_logger.log("INFO", "SpecSpinner initialized",
                        text=text, style=spinner_style)
    
    def start(self) -> None:
        """Start the spinner animation."""
        if self._is_running:
            return
        
        spinner_text = Text.from_markup(f"{self.text}")
        display = Text.assemble(
            (self.spinner, "spinner"),
            " ",
            spinner_text
        )
        
        self.live = Live(
            display,
            console=self.console,
            refresh_per_second=10,
            transient=True
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
            display = Text.assemble(
                (self.spinner, "spinner"),
                " ",
                spinner_text
            )
            self.live.update(display)
        
        debug_logger.log("DEBUG", "Spinner text updated", text=text)
    
    def __enter__(self):
        """Enter context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.stop()

class TimedSpinner(SpecSpinner):
    """Spinner with automatic timeout."""
    
    def __init__(self, timeout: float = 30.0, **kwargs):
        """Initialize timed spinner.
        
        Args:
            timeout: Maximum time to run spinner (seconds)
            **kwargs: Arguments for SpecSpinner
        """
        super().__init__(**kwargs)
        self.timeout = timeout
        self._timer: Optional[threading.Timer] = None
    
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
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize spinner manager.
        
        Args:
            console: Console to use for all spinners
        """
        self.console = console or get_console().console
        self.spinners: dict[str, SpecSpinner] = {}
        self._active_spinner: Optional[str] = None
        
        debug_logger.log("INFO", "SpinnerManager initialized")
    
    def create_spinner(self,
                      spinner_id: str,
                      text: str = "Loading...",
                      **kwargs) -> SpecSpinner:
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
        
        spinner = SpecSpinner(
            text=text,
            console=self.console,
            **kwargs
        )
        
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
    def spinner_context(self, spinner_id: str, text: str, **kwargs):
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
def create_spinner(text: str = "Loading...", **kwargs) -> SpecSpinner:
    """Create a new spinner with default settings.
    
    Args:
        text: Text to display with spinner
        **kwargs: Configuration options for SpecSpinner
        
    Returns:
        Configured SpecSpinner instance
    """
    return SpecSpinner(text=text, **kwargs)

def timed_spinner(text: str = "Loading...", 
                 timeout: float = 30.0, 
                 **kwargs) -> TimedSpinner:
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
def spinner_context(text: str = "Loading...", **kwargs):
    """Context manager for simple spinner usage.
    
    Args:
        text: Text to display with spinner
        **kwargs: Configuration options for SpecSpinner
    """
    spinner = create_spinner(text, **kwargs)
    with spinner:
        yield spinner
```

### Step 3: Create spec_cli/ui/progress_manager.py

```python
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from ..file_processing.progress_events import (
    ProgressReporter, ProgressEvent, ProgressEventType, 
    ProcessingStage, progress_reporter
)
from ..logging.debug import debug_logger
from .progress_bar import SpecProgressBar
from .spinner import SpinnerManager
from .console import get_console

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
    
    def __init__(self, 
                 progress_reporter: Optional[ProgressReporter] = None,
                 auto_display: bool = True):
        """Initialize progress manager.
        
        Args:
            progress_reporter: Progress event reporter to use
            auto_display: Whether to automatically show/hide progress displays
        """
        self.progress_reporter = progress_reporter or progress_reporter
        self.auto_display = auto_display
        
        # Progress tracking
        self.progress_states: Dict[str, ProgressState] = {}
        self.active_operations: Dict[str, str] = {}  # operation_id -> display_type
        
        # Display components
        self.progress_bar = SpecProgressBar(
            show_percentage=True,
            show_time_remaining=True,
            auto_refresh=True
        )
        self.spinner_manager = SpinnerManager()
        
        # Event handling
        self._event_handlers: Dict[ProgressEventType, List[Callable]] = {}
        self._setup_event_handling()
        
        debug_logger.log("INFO", "ProgressManager initialized",
                        auto_display=auto_display)
    
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
                debug_logger.log("ERROR", "Progress event handler failed",
                               event_type=event.event_type.value,
                               error=str(e))
    
    def _handle_batch_started(self, event: ProgressEvent) -> None:
        """Handle batch started event."""
        operation_id = f"batch_{int(time.time())}"
        
        state = ProgressState(
            operation_id=operation_id,
            total_items=event.total_files or 0,
            completed_items=0,
            start_time=time.time()
        )
        
        self.progress_states[operation_id] = state
        
        if self.auto_display and event.total_files:
            # Use progress bar for determinate operations
            self.progress_bar.start()
            task_id = self.progress_bar.add_task(
                event.message or "Processing files",
                total=event.total_files
            )
            self.active_operations[operation_id] = f"progress_bar:{task_id}"
        
        debug_logger.log("INFO", "Batch operation started",
                        operation_id=operation_id,
                        total_files=event.total_files)
    
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
        console.print_status(
            event.message or "Batch operation completed",
            "success"
        )
        
        debug_logger.log("INFO", "Batch operation completed",
                        operation_id=operation_id)
    
    def _handle_batch_failed(self, event: ProgressEvent) -> None:
        """Handle batch failed event."""
        operation_id = self._find_active_operation()
        if operation_id:
            self._cleanup_operation(operation_id)
        
        # Show error message
        console = get_console()
        console.print_status(
            event.message or "Batch operation failed",
            "error"
        )
        
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
                task_id,
                completed=state.completed_items,
                description=description
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
    
    def start_indeterminate_operation(self, 
                                    operation_id: str,
                                    message: str = "Processing...") -> None:
        """Start an indeterminate progress operation (spinner).
        
        Args:
            operation_id: Unique operation identifier
            message: Message to display
        """
        spinner = self.spinner_manager.create_spinner(operation_id, message)
        self.spinner_manager.start_spinner(operation_id)
        
        self.active_operations[operation_id] = f"spinner:{operation_id}"
        
        state = ProgressState(
            operation_id=operation_id,
            total_items=0,
            completed_items=0,
            start_time=time.time()
        )
        self.progress_states[operation_id] = state
        
        debug_logger.log("INFO", "Indeterminate operation started",
                        operation_id=operation_id)
    
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
    
    def add_event_handler(self, 
                         event_type: ProgressEventType,
                         handler: Callable[[ProgressEvent], None]) -> None:
        """Add a custom event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        debug_logger.log("DEBUG", "Event handler added", event_type=event_type.value)
    
    def remove_event_handler(self,
                           event_type: ProgressEventType,
                           handler: Callable[[ProgressEvent], None]) -> bool:
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
            debug_logger.log("DEBUG", "Event handler removed", event_type=event_type.value)
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

# Global progress manager instance
_progress_manager: Optional[ProgressManager] = None

def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance.
    
    Returns:
        Global ProgressManager instance
    """
    global _progress_manager
    
    if _progress_manager is None:
        _progress_manager = ProgressManager()
        debug_logger.log("INFO", "Global progress manager initialized")
    
    return _progress_manager

def set_progress_manager(manager: ProgressManager) -> None:
    """Set the global progress manager.
    
    Args:
        manager: ProgressManager instance to set as global
    """
    global _progress_manager
    _progress_manager = manager
    debug_logger.log("INFO", "Global progress manager updated")

def reset_progress_manager() -> None:
    """Reset the global progress manager."""
    global _progress_manager
    if _progress_manager:
        _progress_manager.cleanup()
    _progress_manager = None
    debug_logger.log("INFO", "Global progress manager reset")
```

### Step 4: Create spec_cli/ui/progress_utils.py

```python
import time
from typing import Optional, Dict, Any, Callable, Union
from contextlib import contextmanager
from pathlib import Path
from ..logging.debug import debug_logger
from .progress_manager import get_progress_manager
from .spinner import spinner_context
from .progress_bar import simple_progress

def estimate_operation_time(item_count: int, 
                          base_time_per_item: float = 2.0,
                          overhead: float = 1.0) -> float:
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

def calculate_processing_speed(completed_items: int, 
                             elapsed_time: float) -> float:
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
def progress_context(total_items: Optional[int] = None,
                    description: str = "Processing",
                    show_spinner: bool = False):
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
            def update_progress(count: int = 1, message: Optional[str] = None):
                progress_bar.advance(count)
                if message:
                    # Update description if needed (limited support)
                    pass
            
            yield update_progress
    
    elif show_spinner:
        # Indeterminate progress with spinner
        with spinner_context(description) as spinner:
            def update_progress(count: int = 1, message: Optional[str] = None):
                if message:
                    spinner.update_text(message)
            
            yield update_progress
    
    else:
        # No visual progress
        def update_progress(count: int = 1, message: Optional[str] = None):
            pass
        
        yield update_progress

@contextmanager
def timed_operation(operation_name: str, 
                   log_result: bool = True):
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
            debug_logger.log("INFO", "Operation completed",
                           operation=operation_name,
                           duration=f"{elapsed:.2f}s")

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
        operation_id,
        f"Processing {total_files} files"
    )
    
    def track_file_completion(file_path: Path) -> None:
        nonlocal completed_files
        completed_files += 1
        
        # Update progress text
        progress_manager._update_operation_text(
            operation_id,
            f"Processing {file_path.name} ({completed_files}/{total_files})"
        )
        
        # Finish operation when all files are done
        if completed_files >= total_files:
            progress_manager.finish_operation(operation_id)
    
    return track_file_completion

class ProgressTracker:
    """Utility class for tracking progress of complex operations."""
    
    def __init__(self, 
                 operation_name: str,
                 total_items: Optional[int] = None,
                 auto_finish: bool = True):
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
        self.start_time: Optional[float] = None
        self.progress_manager = get_progress_manager()
        self.operation_id = f"{operation_name}_{int(time.time())}"
        
        debug_logger.log("INFO", "ProgressTracker initialized",
                        operation=operation_name,
                        total_items=total_items)
    
    def start(self) -> None:
        """Start progress tracking."""
        self.start_time = time.time()
        
        if self.total_items is not None:
            # Will be handled by progress manager events
            pass
        else:
            self.progress_manager.start_indeterminate_operation(
                self.operation_id,
                self.operation_name
            )
        
        debug_logger.log("DEBUG", "Progress tracking started",
                        operation_id=self.operation_id)
    
    def update(self, count: int = 1, message: Optional[str] = None) -> None:
        """Update progress.
        
        Args:
            count: Number of items completed
            message: Optional status message
        """
        self.completed_items += count
        
        if message:
            self.progress_manager._update_operation_text(
                self.operation_id,
                f"{self.operation_name}: {message}"
            )
        
        # Auto-finish if we've completed all items
        if (self.auto_finish and 
            self.total_items is not None and 
            self.completed_items >= self.total_items):
            self.finish()
    
    def finish(self) -> None:
        """Finish progress tracking."""
        self.progress_manager.finish_operation(self.operation_id)
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            debug_logger.log("INFO", "Progress tracking completed",
                           operation=self.operation_name,
                           completed_items=self.completed_items,
                           duration=f"{elapsed:.2f}s")
    
    def get_statistics(self) -> Dict[str, Any]:
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
    
    def __enter__(self):
        """Enter context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.finish()

# Convenience functions
def track_progress(operation_name: str, 
                  total_items: Optional[int] = None) -> ProgressTracker:
    """Create a progress tracker for an operation.
    
    Args:
        operation_name: Name of the operation
        total_items: Total number of items
        
    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(operation_name, total_items)

def show_progress_for_files(files: list[Path], 
                          operation_name: str = "Processing files") -> Callable[[Path], None]:
    """Show progress for file operations.
    
    Args:
        files: List of files to process
        operation_name: Name of the operation
        
    Returns:
        Function to call when each file is completed
    """
    return create_file_progress_tracker(files)
```

### Step 5: Update spec_cli/ui/__init__.py

```python
"""Rich-based terminal UI system for spec CLI.

This package provides console theming, progress tracking, and the foundation
for error display and formatting components.
"""

from .console import get_console, spec_console, SpecConsole, set_console, reset_console
from .theme import SpecTheme, ColorScheme, get_current_theme, set_current_theme, reset_theme
from .styles import SpecStyles, style_text, format_path, format_status, create_rich_text
from .progress_bar import SpecProgressBar, SimpleProgressBar, create_progress_bar, simple_progress
from .spinner import SpecSpinner, TimedSpinner, SpinnerManager, create_spinner, timed_spinner, spinner_context
from .progress_manager import ProgressManager, ProgressState, get_progress_manager, set_progress_manager, reset_progress_manager
from .progress_utils import (
    progress_context, timed_operation, ProgressTracker,
    track_progress, show_progress_for_files,
    estimate_operation_time, format_time_duration, calculate_processing_speed
)

__all__ = [
    # Console and theming
    "get_console",
    "spec_console", 
    "SpecConsole",
    "set_console",
    "reset_console",
    "SpecTheme",
    "ColorScheme",
    "get_current_theme",
    "set_current_theme",
    "reset_theme",
    "SpecStyles",
    "style_text",
    "format_path",
    "format_status",
    "create_rich_text",
    
    # Progress components
    "SpecProgressBar",
    "SimpleProgressBar", 
    "create_progress_bar",
    "simple_progress",
    "SpecSpinner",
    "TimedSpinner",
    "SpinnerManager",
    "create_spinner",
    "timed_spinner",
    "spinner_context",
    
    # Progress management
    "ProgressManager",
    "ProgressState",
    "get_progress_manager",
    "set_progress_manager",
    "reset_progress_manager",
    
    # Progress utilities
    "progress_context",
    "timed_operation",
    "ProgressTracker",
    "track_progress",
    "show_progress_for_files",
    "estimate_operation_time",
    "format_time_duration",
    "calculate_processing_speed",
]
```

## Test Requirements

Create comprehensive tests for progress components:

### Test Cases (16 tests total)

**Progress Bar Tests:**
1. **test_spec_progress_bar_creation_and_configuration**
2. **test_progress_bar_task_management**
3. **test_progress_bar_context_manager**
4. **test_simple_progress_bar_workflow**

**Spinner Tests:**
5. **test_spec_spinner_basic_functionality**
6. **test_timed_spinner_timeout_behavior**
7. **test_spinner_manager_coordination**
8. **test_spinner_context_manager**

**Progress Manager Tests:**
9. **test_progress_manager_event_integration**
10. **test_progress_manager_batch_operation_tracking**
11. **test_progress_manager_display_coordination**
12. **test_progress_manager_custom_event_handlers**

**Progress Utils Tests:**
13. **test_progress_context_wrapper**
14. **test_progress_tracker_functionality**
15. **test_timing_and_estimation_utilities**
16. **test_file_progress_tracking**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/ui/test_progress_bar.py tests/unit/ui/test_spinner.py tests/unit/ui/test_progress_manager.py tests/unit/ui/test_progress_utils.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/ui/ --cov=spec_cli.ui --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/ui/

# Check code formatting
poetry run ruff check spec_cli/ui/
poetry run ruff format spec_cli/ui/

# Verify imports work correctly
python -c "from spec_cli.ui import SpecProgressBar, SpecSpinner, ProgressManager; print('Import successful')"

# Test progress bar functionality
python -c "
from spec_cli.ui.progress_bar import SimpleProgressBar
import time

with SimpleProgressBar(10, 'Test operation') as progress:
    for i in range(10):
        time.sleep(0.1)
        progress.advance()
        
print('Progress bar test completed')
"

# Test spinner functionality (mock-friendly)
python -c "
from spec_cli.ui.spinner import create_spinner

spinner = create_spinner('Loading test data')
print(f'Spinner created with text: {spinner.text}')
print(f'Spinner style: {spinner.spinner_style}')
"

# Test progress manager integration
python -c "
from spec_cli.ui.progress_manager import get_progress_manager
from spec_cli.file_processing.progress_events import ProgressEventType

manager = get_progress_manager()
print(f'Progress manager initialized')
print(f'Event handlers: {list(manager._event_handlers.keys())}')

# Test operation tracking
manager.start_indeterminate_operation('test_op', 'Testing')
state = manager.get_operation_state('test_op')
if state:
    print(f'Operation state: {state.operation_id}')
manager.finish_operation('test_op')
"

# Test progress utilities
python -c "
from spec_cli.ui.progress_utils import estimate_operation_time, format_time_duration

# Test time estimation
estimated = estimate_operation_time(100, 1.5, 5.0)
print(f'Estimated time for 100 items: {format_time_duration(estimated)}')

# Test time formatting
for seconds in [30, 90, 3600, 7200]:
    formatted = format_time_duration(seconds)
    print(f'{seconds}s = {formatted}')
"
```

## Definition of Done

- [ ] SpecProgressBar with Rich integration and task management
- [ ] SpecSpinner components with timeout support
- [ ] SpinnerManager for coordinating multiple spinners
- [ ] ProgressManager integrating with batch processing events
- [ ] Progress utilities for common patterns and helpers
- [ ] Mock-friendly components for reliable testing
- [ ] Event-driven progress coordination
- [ ] All 16 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration ready for formatter views (slice-12c)

## Next Slice Preparation

This slice enables **slice-12c-formatter-error-views.md** by providing:
- Progress display foundation for complex operations
- Event-driven UI coordination patterns
- Rich component integration examples
- Console management for display components