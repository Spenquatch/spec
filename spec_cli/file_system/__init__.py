"""File system operations for spec CLI.

This package provides abstractions for file system operations including
path resolution, file analysis, and directory management.
"""

from .path_resolver import PathResolver

__all__ = [
    "PathResolver",
]