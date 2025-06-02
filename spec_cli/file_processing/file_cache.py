import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecFileError
from ..logging.debug import debug_logger


class FileCacheEntry:
    """Represents a cached file entry with metadata."""

    def __init__(
        self,
        file_path: str,
        hash_md5: str,
        hash_sha256: str,
        size: int,
        mtime: float,
        last_processed: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.file_path = file_path
        self.hash_md5 = hash_md5
        self.hash_sha256 = hash_sha256
        self.size = size
        self.mtime = mtime
        self.last_processed = last_processed
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "hash_md5": self.hash_md5,
            "hash_sha256": self.hash_sha256,
            "size": self.size,
            "mtime": self.mtime,
            "last_processed": self.last_processed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileCacheEntry":
        """Create from dictionary."""
        return cls(
            file_path=data["file_path"],
            hash_md5=data["hash_md5"],
            hash_sha256=data["hash_sha256"],
            size=data["size"],
            mtime=data["mtime"],
            last_processed=data["last_processed"],
            metadata=data.get("metadata", {}),
        )

    def is_stale(self, current_mtime: float, current_size: int) -> bool:
        """Check if cache entry is stale compared to current file state."""
        return self.mtime != current_mtime or self.size != current_size

    def age_hours(self) -> float:
        """Get age of last processing in hours."""
        return (time.time() - self.last_processed) / 3600


class FileCacheManager:
    """Manages persistent file cache for change detection."""

    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.cache_file = self.settings.spec_dir / "cache.json"
        self._cache: Dict[str, FileCacheEntry] = {}
        self._cache_loaded = False
        self._cache_modified = False

        debug_logger.log(
            "INFO", "FileCacheManager initialized", cache_file=str(self.cache_file)
        )

    def load_cache(self) -> None:
        """Load cache from disk."""
        if self._cache_loaded:
            return

        debug_logger.log("DEBUG", "Loading file cache")

        try:
            if self.cache_file.exists():
                with self.cache_file.open("r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Load cache metadata
                cache_version = cache_data.get("version", "1.0")
                cache_created = cache_data.get("created")

                # Load file entries
                entries_data = cache_data.get("entries", {})
                for file_path, entry_data in entries_data.items():
                    try:
                        entry = FileCacheEntry.from_dict(entry_data)
                        self._cache[file_path] = entry
                    except (KeyError, TypeError) as e:
                        debug_logger.log(
                            "WARNING",
                            "Invalid cache entry",
                            file_path=file_path,
                            error=str(e),
                        )

                debug_logger.log(
                    "INFO",
                    "File cache loaded",
                    entries=len(self._cache),
                    version=cache_version,
                    created=cache_created,
                )
            else:
                debug_logger.log("INFO", "No existing cache file, starting fresh")

            self._cache_loaded = True

        except (json.JSONDecodeError, OSError) as e:
            debug_logger.log(
                "WARNING", "Failed to load cache, starting fresh", error=str(e)
            )
            self._cache = {}
            self._cache_loaded = True

    def save_cache(self, force: bool = False) -> None:
        """Save cache to disk."""
        if not self._cache_modified and not force:
            return

        debug_logger.log("DEBUG", "Saving file cache", entries=len(self._cache))

        try:
            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare cache data
            cache_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "entries": {
                    file_path: entry.to_dict()
                    for file_path, entry in self._cache.items()
                },
                "statistics": {
                    "total_entries": len(self._cache),
                    "cache_size_bytes": self._estimate_cache_size(),
                },
            }

            # Write cache file atomically
            temp_cache_file = self.cache_file.with_suffix(".tmp")
            with temp_cache_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, sort_keys=True)

            # Atomic replace
            temp_cache_file.replace(self.cache_file)

            self._cache_modified = False

            debug_logger.log("INFO", "File cache saved", entries=len(self._cache))

        except OSError as e:
            debug_logger.log("ERROR", "Failed to save cache", error=str(e))
            raise SpecFileError(f"Failed to save file cache: {e}") from e

    def get_entry(self, file_path: str) -> Optional[FileCacheEntry]:
        """Get cache entry for a file."""
        self.load_cache()
        return self._cache.get(file_path)

    def set_entry(self, entry: FileCacheEntry) -> None:
        """Set cache entry for a file."""
        self.load_cache()
        self._cache[entry.file_path] = entry
        self._cache_modified = True

        debug_logger.log(
            "DEBUG",
            "Cache entry updated",
            file_path=entry.file_path,
            hash_md5=entry.hash_md5[:8],
        )

    def remove_entry(self, file_path: str) -> bool:
        """Remove cache entry for a file."""
        self.load_cache()
        if file_path in self._cache:
            del self._cache[file_path]
            self._cache_modified = True
            debug_logger.log("DEBUG", "Cache entry removed", file_path=file_path)
            return True
        return False

    def get_all_entries(self) -> Dict[str, FileCacheEntry]:
        """Get all cache entries."""
        self.load_cache()
        return self._cache.copy()

    def cleanup_stale_entries(
        self, existing_files: Set[str], max_age_days: int = 30
    ) -> int:
        """Clean up stale cache entries.

        Args:
            existing_files: Set of file paths that currently exist
            max_age_days: Maximum age in days for cache entries

        Returns:
            Number of entries removed
        """
        self.load_cache()

        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        stale_entries = []

        for file_path, entry in self._cache.items():
            # Remove entries for files that no longer exist
            if file_path not in existing_files:
                stale_entries.append(file_path)
                continue

            # Remove very old entries
            if entry.last_processed < cutoff_time:
                stale_entries.append(file_path)
                continue

        # Remove stale entries
        for file_path in stale_entries:
            del self._cache[file_path]

        if stale_entries:
            self._cache_modified = True
            debug_logger.log(
                "INFO", "Cleaned up stale cache entries", removed=len(stale_entries)
            )

        return len(stale_entries)

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self.load_cache()

        if not self._cache:
            return {
                "total_entries": 0,
                "cache_size_bytes": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "average_age_hours": 0,
            }

        current_time = time.time()
        ages = [current_time - entry.last_processed for entry in self._cache.values()]
        oldest_entry = min(self._cache.values(), key=lambda e: e.last_processed)
        newest_entry = max(self._cache.values(), key=lambda e: e.last_processed)

        return {
            "total_entries": len(self._cache),
            "cache_size_bytes": self._estimate_cache_size(),
            "oldest_entry": {
                "file_path": oldest_entry.file_path,
                "age_hours": oldest_entry.age_hours(),
            },
            "newest_entry": {
                "file_path": newest_entry.file_path,
                "age_hours": newest_entry.age_hours(),
            },
            "average_age_hours": sum(ages) / len(ages) / 3600,
        }

    def _estimate_cache_size(self) -> int:
        """Estimate cache size in bytes."""
        if self.cache_file.exists():
            try:
                return self.cache_file.stat().st_size
            except OSError:
                pass

        # Rough estimate if file doesn't exist
        return len(self._cache) * 200  # ~200 bytes per entry estimate

    def validate_cache_integrity(self) -> List[str]:
        """Validate cache integrity and return issues.

        Returns:
            List of integrity issues found
        """
        self.load_cache()
        issues = []

        for file_path, entry in self._cache.items():
            # Check required fields
            if not entry.file_path:
                issues.append(f"Entry missing file_path: {file_path}")

            if not entry.hash_md5 or len(entry.hash_md5) != 32:
                issues.append(f"Invalid MD5 hash for {file_path}")

            if not entry.hash_sha256 or len(entry.hash_sha256) != 64:
                issues.append(f"Invalid SHA256 hash for {file_path}")

            if entry.size < 0:
                issues.append(f"Invalid file size for {file_path}")

            if entry.mtime <= 0 or entry.last_processed <= 0:
                issues.append(f"Invalid timestamps for {file_path}")

        return issues

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self._cache = {}
        self._cache_modified = True
        debug_logger.log("INFO", "File cache cleared")

    def export_cache(self, export_path: Path) -> None:
        """Export cache to a file for backup or analysis."""
        self.load_cache()

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "cache_file": str(self.cache_file),
            "statistics": self.get_cache_statistics(),
            "entries": {
                file_path: entry.to_dict() for file_path, entry in self._cache.items()
            },
        }

        try:
            with export_path.open("w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, sort_keys=True)

            debug_logger.log(
                "INFO",
                "Cache exported",
                export_path=str(export_path),
                entries=len(self._cache),
            )

        except OSError as e:
            raise SpecFileError(f"Failed to export cache: {e}") from e
