# Slice 2: Debug Logging and Timing Infrastructure

## Goal

Create a comprehensive debug logging system with structured output, timing capabilities, and environment-based configuration for all spec operations.

## Context

The current monolithic code has basic debug logging scattered throughout with inconsistent formatting. This slice creates a centralized logging system that provides structured debugging information, performance timing, and configurable output levels. It builds on the exception hierarchy from slice-1 to provide proper error logging.

## Scope

**Included in this slice:**
- DebugLogger class with structured logging capabilities
- Performance timing context manager for operations
- Environment variable configuration for debug levels
- Integration with exception hierarchy for error logging

**NOT included in this slice:**
- File-based logging (console output only for now)
- Log rotation or persistence
- User-facing progress indicators (comes in PHASE-5)
- Message formatters (moved to slice-12-rich-ui for presentation logic)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for error logging)

**Required functions/classes:**
- All exception classes from slice-1-exceptions

## Files to Create

```
spec_cli/logging/
├── __init__.py             # Module exports
├── debug.py                # DebugLogger class and global instance
└── timing.py               # Performance timing utilities
```

## Implementation Steps

### Step 1: Create spec_cli/logging/__init__.py

```python
"""Logging infrastructure for spec CLI.

This package provides debug logging, performance timing, and structured
logging capabilities for development and troubleshooting.
"""

from .debug import DebugLogger, debug_logger
from .timing import timer, TimingContext

__all__ = [
    "DebugLogger",
    "debug_logger",
    "timer", 
    "TimingContext",
]
```

### Step 2: Create spec_cli/logging/debug.py

```python
import logging
import os
import time
from typing import Any, Dict, Optional
from contextlib import contextmanager
from ..exceptions import SpecError

class DebugLogger:
    """Enhanced debug logging with structured output and timing capabilities."""
    
    def __init__(self):
        self.enabled = self._is_debug_enabled()
        self.level = self._get_debug_level()
        self.timing_enabled = self._is_timing_enabled()
        self.logger = self._setup_logger()
        
    def _is_debug_enabled(self) -> bool:
        """Check if debug logging is enabled via environment."""
        debug_value = os.environ.get("SPEC_DEBUG", "").lower()
        return debug_value in ["1", "true", "yes"]
    
    def _get_debug_level(self) -> str:
        """Get debug level from environment."""
        return os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
    
    def _is_timing_enabled(self) -> bool:
        """Check if performance timing is enabled."""
        timing_value = os.environ.get("SPEC_DEBUG_TIMING", "").lower()
        return timing_value in ["1", "true", "yes"]
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the internal logger with appropriate configuration."""
        logger = logging.getLogger("spec_cli.debug")
        
        if not self.enabled:
            logger.setLevel(logging.CRITICAL + 1)  # Disable all logging
            return logger
            
        # Set level based on environment
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        logger.setLevel(level_map.get(self.level, logging.INFO))
        
        # Create console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[SPEC DEBUG] %(asctime)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False
        
        return logger
    
    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message with structured data.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Primary log message
            **kwargs: Additional contextual data to include
        """
        if not self.enabled:
            return
        
        # Format structured data
        extra_data = ""
        if kwargs:
            extra_parts = [f"{key}={value}" for key, value in kwargs.items()]
            extra_data = f" ({', '.join(extra_parts)})"
        
        full_message = f"{message}{extra_data}"
        level_method = getattr(self.logger, level.lower(), self.logger.info)
        level_method(full_message)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with full context information.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        if not self.enabled:
            return
            
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        # Add SpecError context if available
        if isinstance(error, SpecError):
            error_info.update(error.get_context())
        
        # Add additional context
        if context:
            error_info.update(context)
        
        self.log("ERROR", f"Exception occurred: {error}", **error_info)
    
    @contextmanager
    def timer(self, operation_name: str):
        """Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation being timed
        """
        if not self.timing_enabled:
            yield
            return
        
        start_time = time.perf_counter()
        self.log("INFO", f"Starting operation: {operation_name}")
        
        try:
            yield
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self.log("ERROR", f"Operation failed: {operation_name}", 
                    duration_ms=f"{elapsed * 1000:.2f}ms",
                    error=str(e))
            raise
        finally:
            elapsed = time.perf_counter() - start_time
            self.log("INFO", f"Completed operation: {operation_name}", 
                    duration_ms=f"{elapsed * 1000:.2f}ms")
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: Dict[str, Any] = None) -> None:
        """Log function call with arguments.
        
        Args:
            func_name: Name of the function being called
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if not self.enabled:
            return
            
        call_info = {"function": func_name}
        
        if args:
            call_info["args_count"] = len(args)
            # Only log first few args to avoid too much output
            if len(args) <= 3:
                call_info["args"] = str(args)
        
        if kwargs:
            call_info["kwargs_keys"] = list(kwargs.keys())
        
        self.log("DEBUG", f"Function call: {func_name}", **call_info)

# Global debug logger instance
debug_logger = DebugLogger()
```

### Step 3: Create spec_cli/logging/timing.py

```python
import time
from typing import Dict, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field

@dataclass
class TimingResult:
    """Results from a timing operation."""
    operation: str
    duration_ms: float
    start_time: float
    end_time: float
    success: bool = True
    error: Optional[str] = None

class TimingContext:
    """Context manager for collecting timing information across operations."""
    
    def __init__(self):
        self.results: List[TimingResult] = []
        self._active_operations: Dict[str, float] = {}
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Time a specific operation and collect results."""
        start_time = time.perf_counter()
        self._active_operations[operation_name] = start_time
        
        try:
            yield
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            result = TimingResult(
                operation=operation_name,
                duration_ms=duration_ms,
                start_time=start_time,
                end_time=end_time,
                success=True
            )
            self.results.append(result)
            
        except Exception as e:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            result = TimingResult(
                operation=operation_name,
                duration_ms=duration_ms,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error=str(e)
            )
            self.results.append(result)
            raise
        finally:
            self._active_operations.pop(operation_name, None)
    
    def get_summary(self) -> Dict[str, float]:
        """Get timing summary statistics."""
        if not self.results:
            return {}
        
        total_time = sum(r.duration_ms for r in self.results)
        successful_operations = [r for r in self.results if r.success]
        
        return {
            "total_operations": len(self.results),
            "successful_operations": len(successful_operations),
            "failed_operations": len(self.results) - len(successful_operations),
            "total_time_ms": total_time,
            "average_time_ms": total_time / len(self.results) if self.results else 0,
            "fastest_operation_ms": min(r.duration_ms for r in self.results),
            "slowest_operation_ms": max(r.duration_ms for r in self.results),
        }
    
    def get_slowest_operations(self, limit: int = 5) -> List[TimingResult]:
        """Get the slowest operations."""
        return sorted(self.results, key=lambda r: r.duration_ms, reverse=True)[:limit]

# Convenience function for simple timing
@contextmanager
def timer(operation_name: str, logger=None):
    """Simple timing context manager with optional logging."""
    start_time = time.perf_counter()
    
    if logger:
        logger.log("INFO", f"Starting: {operation_name}")
    
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        duration_ms = elapsed * 1000
        
        if logger:
            logger.log("INFO", f"Completed: {operation_name}", duration_ms=f"{duration_ms:.2f}ms")
```


## Test Requirements

Create `tests/unit/logging/test_debug.py` and `test_timing.py` with these specific test cases:

### Test Cases (14 tests total)

**Debug Logger Tests:**
1. **test_debug_logger_respects_environment_variables**
2. **test_debug_logger_disabled_when_spec_debug_false**
3. **test_debug_logger_formats_structured_data**
4. **test_debug_logger_handles_different_log_levels**
5. **test_debug_logger_timer_measures_duration**
6. **test_debug_logger_timer_handles_exceptions**
7. **test_debug_logger_logs_spec_error_context**
8. **test_debug_logger_logs_function_calls_with_args**

**Timing Tests:**
9. **test_timing_context_collects_operation_results**
10. **test_timing_context_handles_failed_operations**
11. **test_timing_context_calculates_summary_statistics**
12. **test_timing_context_identifies_slowest_operations**
13. **test_timer_function_works_with_logger**
14. **test_timer_function_works_without_logger**


## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/logging/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/logging/ --cov=spec_cli.logging --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/logging/

# Check code formatting
poetry run ruff check spec_cli/logging/
poetry run ruff format spec_cli/logging/

# Verify imports work correctly
python -c "from spec_cli.logging import debug_logger; print('Import successful')"

# Test debug logging functionality
SPEC_DEBUG=1 python -c "
from spec_cli.logging import debug_logger
debug_logger.log('INFO', 'Test message', file_path='test.py', operation='test')
with debug_logger.timer('test_operation'):
    import time
    time.sleep(0.01)
print('Debug logging test complete')
"

# Test timing functionality
python -c "
from spec_cli.logging import TimingContext
with TimingContext() as ctx:
    with ctx.time_operation('test_op'):
        pass
print(f'Timing test: {ctx.get_summary()}')
"
```

## Definition of Done

- [ ] `spec_cli/logging/` package created with all required modules
- [ ] DebugLogger class with environment-based configuration
- [ ] Performance timing system with context managers
- [ ] Structured logging with contextual information
- [ ] Integration with exception hierarchy for error logging
- [ ] Global debug_logger instance available for import
- [ ] All 20 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Code formatted and linted successfully
- [ ] Debug functionality verified with environment variables

## Next Slice Preparation

This slice enables **slice-3-configuration.md** by providing:
- `debug_logger` for logging configuration operations
- `timer` context manager for timing configuration loading
- Error logging capabilities for configuration validation

The configuration slice will use the logging system to provide debugging information during settings loading and validation.