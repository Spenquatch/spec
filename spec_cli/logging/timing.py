"""Performance timing utilities for measuring operation duration.

Provides context managers and data structures for collecting timing information
across multiple operations, with support for error tracking and summary statistics.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass
class TimingResult:
    """Results from a timing operation."""

    operation: str
    duration_ms: float
    start_time: float
    end_time: float
    success: bool = True
    error: str | None = None


class TimingContext:
    """Context manager for collecting timing information across operations."""

    def __init__(self) -> None:
        """Initialize timing context with empty results and operation tracking."""
        self.results: list[TimingResult] = []
        self._active_operations: dict[str, float] = {}

    def __enter__(self) -> "TimingContext":
        """Enter the timing context manager.

        Returns:
            Self for use in with statement
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the timing context manager.

        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception value if exception occurred
            exc_tb: Exception traceback if exception occurred
        """
        pass

    @contextmanager
    def time_operation(self, operation_name: str):  # type: ignore
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
                success=True,
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
                error=str(e),
            )
            self.results.append(result)
            raise
        finally:
            self._active_operations.pop(operation_name, None)

    def get_summary(self) -> dict[str, float]:
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

    def get_slowest_operations(self, limit: int = 5) -> list[TimingResult]:
        """Get the slowest operations."""
        return sorted(self.results, key=lambda r: r.duration_ms, reverse=True)[:limit]


# Convenience function for simple timing
@contextmanager
def timer(operation_name: str, logger=None):  # type: ignore
    """Time an operation with optional logging support."""
    start_time = time.perf_counter()

    if logger:
        logger.log("INFO", f"Starting: {operation_name}")

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        duration_ms = elapsed * 1000

        if logger:
            logger.log(
                "INFO",
                f"Completed: {operation_name}",
                duration_ms=f"{duration_ms:.2f}ms",
            )
