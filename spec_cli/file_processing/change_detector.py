import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecFileError
from ..file_system.file_metadata import FileMetadataExtractor
from ..file_system.ignore_patterns import IgnorePatternMatcher
from ..logging.debug import debug_logger
from .file_cache import FileCacheEntry, FileCacheManager


class FileChangeDetector:
    """Detects file changes using hash comparison and caching."""

    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.cache_manager = FileCacheManager(self.settings)
        self.metadata_extractor = FileMetadataExtractor()
        self.ignore_matcher = IgnorePatternMatcher(self.settings)

        debug_logger.log("INFO", "FileChangeDetector initialized")

    def calculate_file_hashes(self, file_path: Path) -> Tuple[str, str]:
        """Calculate MD5 and SHA256 hashes for a file.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (md5_hash, sha256_hash)

        Raises:
            SpecFileError: If file cannot be read
        """
        debug_logger.log("DEBUG", "Calculating file hashes", file_path=str(file_path))

        try:
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()

            with file_path.open("rb") as f:
                # Read in chunks to handle large files efficiently
                chunk_size = 8192
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)

            md5_result = md5_hash.hexdigest()
            sha256_result = sha256_hash.hexdigest()

            debug_logger.log(
                "DEBUG",
                "File hashes calculated",
                file_path=str(file_path),
                md5=md5_result[:8],
                sha256=sha256_result[:8],
            )

            return md5_result, sha256_result

        except OSError as e:
            error_msg = f"Failed to calculate hashes for {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecFileError(error_msg) from e

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive file information including hashes.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        try:
            # Get basic file stats
            stat = file_path.stat()

            # Calculate hashes
            md5_hash, sha256_hash = self.calculate_file_hashes(file_path)

            # Get metadata
            metadata = self.metadata_extractor.get_file_metadata(file_path)

            file_info = {
                "file_path": str(file_path),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "hash_md5": md5_hash,
                "hash_sha256": sha256_hash,
                "metadata": metadata or {},
                "last_checked": time.time(),
            }

            return file_info

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to get file info",
                file_path=str(file_path),
                error=str(e),
            )
            raise SpecFileError(f"Failed to get file info for {file_path}: {e}") from e

    def has_file_changed(self, file_path: Path) -> bool:
        """Check if a file has changed since last processing.

        Args:
            file_path: Path to check (relative to project root)

        Returns:
            True if file has changed or is not in cache
        """
        debug_logger.log(
            "DEBUG", "Checking if file has changed", file_path=str(file_path)
        )

        file_path_str = str(file_path)

        # Check if file exists
        if not file_path.exists():
            # File doesn't exist, check if it was deleted
            cached_entry = self.cache_manager.get_entry(file_path_str)
            if cached_entry:
                debug_logger.log("INFO", "File was deleted", file_path=file_path_str)
                self.cache_manager.remove_entry(file_path_str)
                return True
            return False

        # Get cached entry
        cached_entry = self.cache_manager.get_entry(file_path_str)
        if not cached_entry:
            debug_logger.log(
                "DEBUG",
                "File not in cache, treating as changed",
                file_path=file_path_str,
            )
            return True

        # Quick check using file stats
        try:
            stat = file_path.stat()
            if cached_entry.is_stale(stat.st_mtime, stat.st_size):
                debug_logger.log(
                    "DEBUG",
                    "File stats changed",
                    file_path=file_path_str,
                    cached_mtime=cached_entry.mtime,
                    current_mtime=stat.st_mtime,
                )
                return True
        except OSError as e:
            debug_logger.log(
                "WARNING",
                "Could not get file stats",
                file_path=file_path_str,
                error=str(e),
            )
            return True

        # File hasn't changed based on quick check
        debug_logger.log(
            "DEBUG", "File unchanged based on stats", file_path=file_path_str
        )
        return False

    def has_file_changed_deep(self, file_path: Path) -> bool:
        """Perform deep hash-based change detection.

        Args:
            file_path: Path to check

        Returns:
            True if file content has changed
        """
        debug_logger.log(
            "DEBUG", "Performing deep change detection", file_path=str(file_path)
        )

        file_path_str = str(file_path)

        # Get current file hashes
        try:
            current_md5, current_sha256 = self.calculate_file_hashes(file_path)
        except SpecFileError:
            return True  # Treat hash calculation failure as changed

        # Get cached entry
        cached_entry = self.cache_manager.get_entry(file_path_str)
        if not cached_entry:
            return True

        # Compare hashes
        hash_changed = (
            cached_entry.hash_md5 != current_md5
            or cached_entry.hash_sha256 != current_sha256
        )

        if hash_changed:
            debug_logger.log(
                "DEBUG", "File content changed (hash mismatch)", file_path=file_path_str
            )
        else:
            debug_logger.log(
                "DEBUG", "File content unchanged (hash match)", file_path=file_path_str
            )

        return hash_changed

    def update_file_cache(self, file_path: Path) -> FileCacheEntry:
        """Update cache entry for a file.

        Args:
            file_path: Path to update cache for

        Returns:
            Updated cache entry
        """
        debug_logger.log("DEBUG", "Updating file cache", file_path=str(file_path))

        file_info = self.get_file_info(file_path)

        cache_entry = FileCacheEntry(
            file_path=str(file_path),
            hash_md5=file_info["hash_md5"],
            hash_sha256=file_info["hash_sha256"],
            size=file_info["size"],
            mtime=file_info["mtime"],
            last_processed=time.time(),
            metadata=file_info["metadata"],
        )

        self.cache_manager.set_entry(cache_entry)

        debug_logger.log("DEBUG", "File cache updated", file_path=str(file_path))

        return cache_entry

    def detect_changes_in_directory(
        self, directory: Path, deep_scan: bool = False, max_files: Optional[int] = None
    ) -> Dict[str, List[Path]]:
        """Detect changes in all files within a directory.

        Args:
            directory: Directory to scan
            deep_scan: Whether to perform hash-based detection
            max_files: Maximum number of files to check

        Returns:
            Dictionary with 'changed', 'unchanged', 'new', 'deleted' file lists
        """
        debug_logger.log(
            "INFO",
            "Detecting changes in directory",
            directory=str(directory),
            deep_scan=deep_scan,
            max_files=max_files,
        )

        changes: Dict[str, List[Path]] = {
            "changed": [],
            "unchanged": [],
            "new": [],
            "deleted": [],
        }

        try:
            with debug_logger.timer("directory_change_detection"):
                # Get all current files
                current_files = set()
                files_checked = 0

                for file_path in directory.rglob("*"):
                    if not file_path.is_file():
                        continue

                    # Check ignore patterns
                    try:
                        # Try to get relative path to current working directory
                        try:
                            relative_path = file_path.relative_to(Path.cwd())
                        except ValueError:
                            # If not relative to cwd, use relative to the directory being scanned
                            relative_path = file_path.relative_to(directory)

                        if self.ignore_matcher.should_ignore(relative_path):
                            continue
                    except ValueError:
                        continue

                    current_files.add(relative_path)

                    # Check for changes
                    if deep_scan:
                        has_changed = self.has_file_changed_deep(relative_path)
                    else:
                        has_changed = self.has_file_changed(relative_path)

                    # Categorize file
                    cached_entry = self.cache_manager.get_entry(str(relative_path))
                    if not cached_entry:
                        changes["new"].append(relative_path)
                    elif has_changed:
                        changes["changed"].append(relative_path)
                    else:
                        changes["unchanged"].append(relative_path)

                    files_checked += 1
                    if max_files and files_checked >= max_files:
                        debug_logger.log(
                            "INFO", "Reached max files limit", max_files=max_files
                        )
                        break

                # Check for deleted files
                all_cached_files = set(self.cache_manager.get_all_entries().keys())
                current_files_str = {str(fp) for fp in current_files}
                deleted_files = all_cached_files - current_files_str

                for deleted_file_str in deleted_files:
                    deleted_path = Path(deleted_file_str)
                    changes["deleted"].append(deleted_path)
                    self.cache_manager.remove_entry(deleted_file_str)

            debug_logger.log(
                "INFO",
                "Directory change detection complete",
                directory=str(directory),
                changed=len(changes["changed"]),
                new=len(changes["new"]),
                unchanged=len(changes["unchanged"]),
                deleted=len(changes["deleted"]),
            )

            return changes

        except Exception as e:
            error_msg = f"Failed to detect changes in {directory}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecFileError(error_msg) from e

    def get_files_needing_processing(
        self, file_paths: List[Path], force_all: bool = False
    ) -> List[Path]:
        """Get list of files that need processing based on change detection.

        Args:
            file_paths: List of file paths to check
            force_all: Whether to force processing of all files

        Returns:
            List of files that need processing
        """
        debug_logger.log(
            "INFO",
            "Determining files needing processing",
            total_files=len(file_paths),
            force_all=force_all,
        )

        if force_all:
            debug_logger.log("INFO", "Force processing all files")
            return file_paths

        needs_processing = []

        for file_path in file_paths:
            if self.has_file_changed(file_path):
                needs_processing.append(file_path)

        debug_logger.log(
            "INFO",
            "Files needing processing determined",
            needs_processing=len(needs_processing),
            total_files=len(file_paths),
        )

        return needs_processing

    def save_cache(self) -> None:
        """Save the current cache state."""
        self.cache_manager.save_cache()

    def get_change_summary(self, changes: Dict[str, List[Path]]) -> Dict[str, Any]:
        """Get a summary of detected changes.

        Args:
            changes: Changes dictionary from detect_changes_in_directory

        Returns:
            Summary dictionary
        """
        total_files = sum(len(file_list) for file_list in changes.values())

        summary = {
            "total_files": total_files,
            "changed_count": len(changes["changed"]),
            "new_count": len(changes["new"]),
            "unchanged_count": len(changes["unchanged"]),
            "deleted_count": len(changes["deleted"]),
            "change_percentage": (
                (len(changes["changed"]) + len(changes["new"])) / total_files * 100
                if total_files > 0
                else 0
            ),
            "needs_processing": len(changes["changed"]) + len(changes["new"]) > 0,
        }

        return summary

    def cleanup_cache(self, max_age_days: int = 30) -> int:
        """Clean up stale cache entries.

        Args:
            max_age_days: Maximum age for cache entries

        Returns:
            Number of entries removed
        """
        debug_logger.log("INFO", "Cleaning up file cache", max_age_days=max_age_days)

        # Get current files
        try:
            current_files = set()
            for file_path in Path.cwd().rglob("*"):
                if file_path.is_file():
                    try:
                        relative_path = file_path.relative_to(Path.cwd())
                        if not self.ignore_matcher.should_ignore(relative_path):
                            current_files.add(str(relative_path))
                    except ValueError:
                        continue

            # Cleanup cache
            removed_count = self.cache_manager.cleanup_stale_entries(
                current_files, max_age_days
            )

            if removed_count > 0:
                self.cache_manager.save_cache()

            return removed_count

        except Exception as e:
            debug_logger.log("ERROR", "Cache cleanup failed", error=str(e))
            return 0
