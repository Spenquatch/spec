"""File system utilities for operations, statistics, and metadata.

This module provides essential file system utilities including readability
checks, size formatting, timestamp handling, file discovery operations,
and safe file operation validation. These utilities are used throughout
the spec system for consistent file handling.
"""

import os
from datetime import datetime
from pathlib import Path

from ..exceptions import SpecFileError
from ..logging.debug import debug_logger


def ensure_file_readable(file_path: Path) -> bool:
    """Ensure a file is readable, with helpful error reporting.

    Args:
        file_path: Path to check

    Returns:
        True if readable, False otherwise

    """
    if not file_path.exists():
        debug_logger.log("WARNING", "File does not exist", file_path=str(file_path))
        return False

    if not file_path.is_file():
        debug_logger.log(
            "WARNING", "Path is not a regular file", file_path=str(file_path)
        )
        return False

    if not os.access(file_path, os.R_OK):
        debug_logger.log("WARNING", "File is not readable", file_path=str(file_path))
        return False

    return True


def get_file_extension_stats(files: list[Path]) -> dict[str, int]:
    """Get statistics about file extensions in a list of files.

    Args:
        files: List of file paths to analyze

    Returns:
        Dictionary with extension statistics

    """
    extension_stats: dict[str, int] = {}

    for file_path in files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if not ext:
                ext = "no_extension"
            extension_stats[ext] = extension_stats.get(ext, 0) + 1

    debug_logger.log(
        "DEBUG",
        "File extension statistics",
        unique_extensions=len(extension_stats),
        total_files=len(files),
    )

    return extension_stats


def find_largest_files(directory: Path, limit: int = 10) -> list[dict[str, object]]:
    """Find the largest files in a directory.

    Args:
        directory: Directory to search
        limit: Maximum number of files to return

    Returns:
        List of dictionaries with file info, sorted by size (largest first)

    """
    if not directory.is_dir():
        raise SpecFileError(f"Path is not a directory: {directory}")

    files_with_size = []

    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    files_with_size.append(
                        {
                            "path": file_path,
                            "size": size,
                            "size_formatted": format_file_size(size),
                        }
                    )
                except OSError:
                    continue

        # Sort by size (largest first) and return top N
        files_with_size.sort(
            key=lambda x: x["size"] if isinstance(x["size"], int) else 0, reverse=True
        )
        return files_with_size[:limit]

    except OSError as e:
        raise SpecFileError(f"Cannot search directory {directory}: {e}") from e


def find_recently_modified_files(
    directory: Path, limit: int = 10
) -> list[dict[str, object]]:
    """Find the most recently modified files in a directory.

    Args:
        directory: Directory to search
        limit: Maximum number of files to return

    Returns:
        List of dictionaries with file info, sorted by modification time (newest first)

    """
    if not directory.is_dir():
        raise SpecFileError(f"Path is not a directory: {directory}")

    files_with_time = []

    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    mtime = file_path.stat().st_mtime
                    files_with_time.append(
                        {
                            "path": file_path,
                            "modified_time": mtime,
                            "modified_formatted": format_timestamp(mtime),
                        }
                    )
                except OSError:
                    continue

        # Sort by modification time (newest first) and return top N
        files_with_time.sort(
            key=lambda x: x["modified_time"]
            if isinstance(x["modified_time"], int | float)
            else 0,
            reverse=True,
        )
        return files_with_time[:limit]

    except OSError as e:
        raise SpecFileError(f"Cannot search directory {directory}: {e}") from e


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string

    """
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} PB"


def format_timestamp(timestamp: float) -> str:
    """Format Unix timestamp in human-readable format.

    Args:
        timestamp: Unix timestamp

    Returns:
        Formatted timestamp string

    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_file_operation(file_path: Path, operation: str) -> bool:
    """Safely perform file operations with error handling.

    Args:
        file_path: Path to file
        operation: Operation to check ('read', 'write', 'execute')

    Returns:
        True if operation is safe, False otherwise

    """
    if not file_path.exists():
        return False

    operation_map = {"read": os.R_OK, "write": os.W_OK, "execute": os.X_OK}

    if operation not in operation_map:
        debug_logger.log("ERROR", "Unknown file operation", operation=operation)
        return False

    try:
        return os.access(file_path, operation_map[operation])
    except OSError as e:
        debug_logger.log(
            "ERROR",
            "File operation check failed",
            file_path=str(file_path),
            operation=operation,
            error=str(e),
        )
        return False


def get_unique_extensions(files: list[Path]) -> set[str]:
    """Get set of unique file extensions from a list of files.

    Args:
        files: List of file paths

    Returns:
        Set of unique extensions (lowercase)

    """
    extensions = set()

    for file_path in files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext:
                extensions.add(ext)

    return extensions


def filter_files_by_size(
    files: list[Path], min_size: int = 0, max_size: int | None = None
) -> list[Path]:
    """Filter files by size range.

    Args:
        files: List of file paths to filter
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes (None for no limit)

    Returns:
        Filtered list of file paths

    """
    filtered = []

    for file_path in files:
        if file_path.is_file():
            try:
                size = file_path.stat().st_size
                if size >= min_size and (max_size is None or size <= max_size):
                    filtered.append(file_path)
            except OSError:
                continue

    debug_logger.log(
        "DEBUG",
        "Filtered files by size",
        original_count=len(files),
        filtered_count=len(filtered),
        min_size=min_size,
        max_size=max_size,
    )

    return filtered
