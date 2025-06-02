"""Git operations for spec CLI.

This package provides Git repository abstractions, command execution,
and path conversion utilities for the isolated .spec repository system.
"""

from .operations import GitOperations
from .path_converter import GitPathConverter
from .repository import GitRepository, SpecGitRepository

__all__ = [
    "GitRepository",
    "SpecGitRepository",
    "GitOperations",
    "GitPathConverter",
]
