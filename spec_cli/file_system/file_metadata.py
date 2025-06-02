import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ..exceptions import SpecFileError
from ..logging.debug import debug_logger
from .file_type_detector import FileTypeDetector


class FileMetadataExtractor:
    """Extracts comprehensive metadata from files for analysis and reporting."""

    def __init__(self) -> None:
        self.type_detector = FileTypeDetector()

    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive metadata about a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing file metadata

        Raises:
            SpecFileError: If file cannot be accessed or analyzed
        """
        try:
            # Ensure path is absolute for consistent results
            if not file_path.is_absolute():
                file_path = file_path.resolve()

            if not file_path.exists():
                raise SpecFileError(f"File does not exist: {file_path}")

            stat_info = file_path.stat()

            # Basic file information
            metadata = {
                "path": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "parent": str(file_path.parent),
                # Size information
                "size_bytes": stat_info.st_size,
                "size_formatted": self._format_file_size(stat_info.st_size),
                # Timing information
                "modified_time": stat_info.st_mtime,
                "modified_datetime": datetime.fromtimestamp(stat_info.st_mtime),
                "created_time": stat_info.st_ctime,
                "created_datetime": datetime.fromtimestamp(stat_info.st_ctime),
                "accessed_time": stat_info.st_atime,
                "accessed_datetime": datetime.fromtimestamp(stat_info.st_atime),
                # Permission information
                "permissions": stat.filemode(stat_info.st_mode),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "is_executable": os.access(file_path, os.X_OK),
                # File type analysis
                "file_type": self.type_detector.get_file_type(file_path),
                "file_category": self.type_detector.get_file_category(file_path),
                "is_binary": self.type_detector.is_binary_file(file_path),
                "is_processable": self.type_detector.is_processable_file(file_path),
                # File characteristics
                "is_hidden": file_path.name.startswith("."),
                "is_empty": stat_info.st_size == 0,
                "line_count": None,  # Will be populated if text file
            }

            # Add line count for text files (if reasonable size)
            if (
                not metadata["is_binary"]
                and metadata["is_processable"]
                and stat_info.st_size < 1_048_576
            ):  # 1MB limit
                try:
                    metadata["line_count"] = self._count_lines(file_path)
                except Exception as e:
                    debug_logger.log(
                        "WARNING",
                        "Could not count lines",
                        file_path=str(file_path),
                        error=str(e),
                    )

            debug_logger.log(
                "DEBUG",
                "Extracted file metadata",
                file_path=str(file_path),
                file_type=metadata["file_type"],
                size_bytes=metadata["size_bytes"],
            )

            return metadata

        except OSError as e:
            raise SpecFileError(
                f"Cannot access file metadata for {file_path}: {e}",
                {"file_path": str(file_path), "os_error": str(e)},
            ) from e

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        size_float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} TB"

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a text file."""
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with file_path.open("r", encoding="latin-1") as f:
                    return sum(1 for _ in f)
            except Exception:
                return 0

    def get_directory_composition(self, directory_path: Path) -> Dict[str, Any]:
        """Analyze the composition of files in a directory.

        Args:
            directory_path: Path to directory to analyze

        Returns:
            Dictionary with directory composition statistics
        """
        if not directory_path.is_dir():
            raise SpecFileError(f"Path is not a directory: {directory_path}")

        composition: Dict[str, Any] = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "file_categories": {},
            "processable_files": 0,
            "binary_files": 0,
            "hidden_files": 0,
            "empty_files": 0,
            "largest_file": None,
            "newest_file": None,
        }

        newest_time = 0
        largest_size = 0

        try:
            for item in directory_path.iterdir():
                if item.is_file():
                    try:
                        metadata = self.get_file_metadata(item)
                        composition["total_files"] += 1
                        composition["total_size"] += metadata["size_bytes"]

                        # Track file types
                        file_type = metadata["file_type"]
                        composition["file_types"][file_type] = (
                            composition["file_types"].get(file_type, 0) + 1
                        )

                        # Track file categories
                        category = metadata["file_category"]
                        if category:
                            composition["file_categories"][category] = (
                                composition["file_categories"].get(category, 0) + 1
                            )

                        # Track characteristics
                        if metadata["is_processable"]:
                            composition["processable_files"] += 1
                        if metadata["is_binary"]:
                            composition["binary_files"] += 1
                        if metadata["is_hidden"]:
                            composition["hidden_files"] += 1
                        if metadata["is_empty"]:
                            composition["empty_files"] += 1

                        # Track largest file
                        if metadata["size_bytes"] > largest_size:
                            largest_size = metadata["size_bytes"]
                            composition["largest_file"] = {
                                "path": metadata["path"],
                                "size": metadata["size_formatted"],
                            }

                        # Track newest file
                        if metadata["modified_time"] > newest_time:
                            newest_time = metadata["modified_time"]
                            composition["newest_file"] = {
                                "path": metadata["path"],
                                "modified": metadata["modified_datetime"].isoformat(),
                            }

                    except SpecFileError as e:
                        debug_logger.log(
                            "WARNING",
                            "Could not analyze file in directory",
                            file_path=str(item),
                            error=str(e),
                        )
                        continue

            # Add formatted total size
            composition["total_size_formatted"] = self._format_file_size(
                composition["total_size"]
            )

            debug_logger.log(
                "INFO",
                "Directory composition analyzed",
                directory=str(directory_path),
                total_files=composition["total_files"],
                processable_files=composition["processable_files"],
            )

            return composition

        except OSError as e:
            raise SpecFileError(
                f"Cannot analyze directory composition for {directory_path}: {e}",
                {"directory_path": str(directory_path), "os_error": str(e)},
            ) from e

    def compare_files(self, file1: Path, file2: Path) -> Dict[str, Any]:
        """Compare two files and return comparison results."""
        try:
            meta1 = self.get_file_metadata(file1)
            meta2 = self.get_file_metadata(file2)

            comparison = {
                "same_type": meta1["file_type"] == meta2["file_type"],
                "same_size": meta1["size_bytes"] == meta2["size_bytes"],
                "size_difference": abs(meta1["size_bytes"] - meta2["size_bytes"]),
                "newer_file": (
                    file1 if meta1["modified_time"] > meta2["modified_time"] else file2
                ),
                "larger_file": (
                    file1 if meta1["size_bytes"] > meta2["size_bytes"] else file2
                ),
                "both_processable": meta1["is_processable"] and meta2["is_processable"],
            }

            return comparison

        except Exception as e:
            raise SpecFileError(f"Cannot compare files: {e}") from e
