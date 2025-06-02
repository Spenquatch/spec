"""Logging infrastructure for spec CLI.

This package provides debug logging, performance timing, and structured
logging capabilities for development and troubleshooting.
"""

from .debug import DebugLogger, debug_logger
from .timing import TimingContext, timer

__all__ = [
    "DebugLogger",
    "debug_logger",
    "timer",
    "TimingContext",
]
