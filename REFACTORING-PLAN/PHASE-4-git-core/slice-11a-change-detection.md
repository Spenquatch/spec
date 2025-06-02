# Slice 11A: Change Detection and File Caching

## Goal

Implement file hash tracking, diff detection against last run, and persistent cache storage in .spec/cache.json for efficient change detection.

## Context

This slice creates the foundation for efficient file processing by implementing change detection. It tracks file hashes, compares against previous runs, and maintains a persistent cache to avoid unnecessary processing. This enables intelligent batch operations and incremental spec generation.

## Scope

**Included in this slice:**
- FileChangeDetector class for hash-based change detection
- Persistent cache management in .spec/cache.json
- File hash calculation with multiple algorithms
- Change detection against previous runs
- Cache validation and cleanup utilities

**NOT included in this slice:**
- Conflict resolution strategies (moved to slice-11b)
- Batch processing workflows (moved to slice-11c)
- File processing orchestration (moved to slice-11c)
- Rich UI integration (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for cache errors)
- `spec_cli.logging.debug` (debug_logger for change detection tracking)
- `spec_cli.config.settings` (SpecSettings for cache configuration)
- `spec_cli.file_system.file_metadata` (FileMetadataExtractor for file info)
- `spec_cli.file_system.ignore_patterns` (IgnorePatternMatcher for filtering)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `FileMetadataExtractor` from slice-5b-file-metadata
- `IgnorePatternMatcher` from slice-6a-ignore-patterns

## Files to Create

```
spec_cli/file_processing/
├── __init__.py             # Module exports
├── change_detector.py      # FileChangeDetector class
└── file_cache.py          # File cache management utilities
```

## Implementation Steps

### Step 1: Create spec_cli/file_processing/__init__.py

```python
"""File processing utilities for spec CLI.

This package provides change detection, conflict resolution, and batch processing
capabilities for efficient spec generation workflows.
"""

from .change_detector import FileChangeDetector
from .file_cache import FileCacheManager

__all__ = [
    "FileChangeDetector",
    "FileCacheManager",
]
```

### Step 2: Create spec_cli/file_processing/file_cache.py

```python
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from ..exceptions import SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class FileCacheEntry:
    """Represents a cached file entry with metadata."""
    
    def __init__(self, 
                 file_path: str,
                 hash_md5: str,
                 hash_sha256: str,
                 size: int,
                 mtime: float,
                 last_processed: float,
                 metadata: Optional[Dict[str, Any]] = None):
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
    def from_dict(cls, data: Dict[str, Any]) -> 'FileCacheEntry':
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
        self.cache_file = self.settings.spec_git_dir / "cache.json"
        self._cache: Dict[str, FileCacheEntry] = {}
        self._cache_loaded = False
        self._cache_modified = False
        
        debug_logger.log("INFO", "FileCacheManager initialized",
                        cache_file=str(self.cache_file))
    
    def load_cache(self) -> None:
        """Load cache from disk."""
        if self._cache_loaded:
            return
        
        debug_logger.log("DEBUG", "Loading file cache")
        
        try:
            if self.cache_file.exists():
                with self.cache_file.open('r', encoding='utf-8') as f:
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
                        debug_logger.log("WARNING", "Invalid cache entry",
                                       file_path=file_path, error=str(e))
                
                debug_logger.log("INFO", "File cache loaded",
                               entries=len(self._cache),
                               version=cache_version,
                               created=cache_created)
            else:
                debug_logger.log("INFO", "No existing cache file, starting fresh")
            
            self._cache_loaded = True
            
        except (json.JSONDecodeError, OSError) as e:
            debug_logger.log("WARNING", "Failed to load cache, starting fresh",
                           error=str(e))
            self._cache = {}
            self._cache_loaded = True
    
    def save_cache(self, force: bool = False) -> None:
        """Save cache to disk."""
        if not self._cache_modified and not force:
            return
        
        debug_logger.log("DEBUG", "Saving file cache",
                        entries=len(self._cache))
        
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
                }
            }
            
            # Write cache file atomically
            temp_cache_file = self.cache_file.with_suffix('.tmp')
            with temp_cache_file.open('w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, sort_keys=True)
            
            # Atomic replace
            temp_cache_file.replace(self.cache_file)
            
            self._cache_modified = False
            
            debug_logger.log("INFO", "File cache saved",
                           entries=len(self._cache))
            
        except OSError as e:
            debug_logger.log("ERROR", "Failed to save cache",
                           error=str(e))
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
        
        debug_logger.log("DEBUG", "Cache entry updated",
                        file_path=entry.file_path,
                        hash_md5=entry.hash_md5[:8])
    
    def remove_entry(self, file_path: str) -> bool:
        """Remove cache entry for a file."""
        self.load_cache()
        if file_path in self._cache:
            del self._cache[file_path]
            self._cache_modified = True
            debug_logger.log("DEBUG", "Cache entry removed",
                           file_path=file_path)
            return True
        return False
    
    def get_all_entries(self) -> Dict[str, FileCacheEntry]:
        """Get all cache entries."""
        self.load_cache()
        return self._cache.copy()
    
    def cleanup_stale_entries(self, 
                             existing_files: Set[str],
                             max_age_days: int = 30) -> int:
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
            debug_logger.log("INFO", "Cleaned up stale cache entries",
                           removed=len(stale_entries))
        
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
                file_path: entry.to_dict()
                for file_path, entry in self._cache.items()
            }
        }
        
        try:
            with export_path.open('w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, sort_keys=True)
            
            debug_logger.log("INFO", "Cache exported",
                           export_path=str(export_path),
                           entries=len(self._cache))
            
        except OSError as e:
            raise SpecFileError(f"Failed to export cache: {e}") from e
```

### Step 3: Create spec_cli/file_processing/change_detector.py

```python
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from ..exceptions import SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..file_system.file_metadata import FileMetadataExtractor
from ..file_system.ignore_patterns import IgnorePatternMatcher
from ..logging.debug import debug_logger
from .file_cache import FileCacheManager, FileCacheEntry

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
        debug_logger.log("DEBUG", "Calculating file hashes",
                        file_path=str(file_path))
        
        try:
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()
            
            with file_path.open('rb') as f:
                # Read in chunks to handle large files efficiently
                chunk_size = 8192
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            md5_result = md5_hash.hexdigest()
            sha256_result = sha256_hash.hexdigest()
            
            debug_logger.log("DEBUG", "File hashes calculated",
                           file_path=str(file_path),
                           md5=md5_result[:8],
                           sha256=sha256_result[:8])
            
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
            metadata = self.metadata_extractor.extract_metadata(file_path)
            
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
            debug_logger.log("ERROR", "Failed to get file info",
                           file_path=str(file_path), error=str(e))
            raise SpecFileError(f"Failed to get file info for {file_path}: {e}") from e
    
    def has_file_changed(self, file_path: Path) -> bool:
        """Check if a file has changed since last processing.
        
        Args:
            file_path: Path to check (relative to project root)
            
        Returns:
            True if file has changed or is not in cache
        """
        debug_logger.log("DEBUG", "Checking if file has changed",
                        file_path=str(file_path))
        
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
            debug_logger.log("DEBUG", "File not in cache, treating as changed",
                           file_path=file_path_str)
            return True
        
        # Quick check using file stats
        try:
            stat = file_path.stat()
            if cached_entry.is_stale(stat.st_mtime, stat.st_size):
                debug_logger.log("DEBUG", "File stats changed",
                               file_path=file_path_str,
                               cached_mtime=cached_entry.mtime,
                               current_mtime=stat.st_mtime)
                return True
        except OSError as e:
            debug_logger.log("WARNING", "Could not get file stats",
                           file_path=file_path_str, error=str(e))
            return True
        
        # File hasn't changed based on quick check
        debug_logger.log("DEBUG", "File unchanged based on stats",
                        file_path=file_path_str)
        return False
    
    def has_file_changed_deep(self, file_path: Path) -> bool:
        """Perform deep hash-based change detection.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file content has changed
        """
        debug_logger.log("DEBUG", "Performing deep change detection",
                        file_path=str(file_path))
        
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
            cached_entry.hash_md5 != current_md5 or
            cached_entry.hash_sha256 != current_sha256
        )
        
        if hash_changed:
            debug_logger.log("DEBUG", "File content changed (hash mismatch)",
                           file_path=file_path_str)
        else:
            debug_logger.log("DEBUG", "File content unchanged (hash match)",
                           file_path=file_path_str)
        
        return hash_changed
    
    def update_file_cache(self, file_path: Path) -> FileCacheEntry:
        """Update cache entry for a file.
        
        Args:
            file_path: Path to update cache for
            
        Returns:
            Updated cache entry
        """
        debug_logger.log("DEBUG", "Updating file cache",
                        file_path=str(file_path))
        
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
        
        debug_logger.log("DEBUG", "File cache updated",
                        file_path=str(file_path))
        
        return cache_entry
    
    def detect_changes_in_directory(self,
                                   directory: Path,
                                   deep_scan: bool = False,
                                   max_files: Optional[int] = None) -> Dict[str, List[Path]]:
        """Detect changes in all files within a directory.
        
        Args:
            directory: Directory to scan
            deep_scan: Whether to perform hash-based detection
            max_files: Maximum number of files to check
            
        Returns:
            Dictionary with 'changed', 'unchanged', 'new', 'deleted' file lists
        """
        debug_logger.log("INFO", "Detecting changes in directory",
                        directory=str(directory),
                        deep_scan=deep_scan,
                        max_files=max_files)
        
        changes = {
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
                        relative_path = file_path.relative_to(Path.cwd())
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
                        debug_logger.log("INFO", "Reached max files limit",
                                       max_files=max_files)
                        break
                
                # Check for deleted files
                all_cached_files = set(self.cache_manager.get_all_entries().keys())
                current_files_str = {str(fp) for fp in current_files}
                deleted_files = all_cached_files - current_files_str
                
                for deleted_file_str in deleted_files:
                    deleted_path = Path(deleted_file_str)
                    changes["deleted"].append(deleted_path)
                    self.cache_manager.remove_entry(deleted_file_str)
            
            debug_logger.log("INFO", "Directory change detection complete",
                           directory=str(directory),
                           changed=len(changes["changed"]),
                           new=len(changes["new"]),
                           unchanged=len(changes["unchanged"]),
                           deleted=len(changes["deleted"]))
            
            return changes
            
        except Exception as e:
            error_msg = f"Failed to detect changes in {directory}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecFileError(error_msg) from e
    
    def get_files_needing_processing(self,
                                   file_paths: List[Path],
                                   force_all: bool = False) -> List[Path]:
        """Get list of files that need processing based on change detection.
        
        Args:
            file_paths: List of file paths to check
            force_all: Whether to force processing of all files
            
        Returns:
            List of files that need processing
        """
        debug_logger.log("INFO", "Determining files needing processing",
                        total_files=len(file_paths),
                        force_all=force_all)
        
        if force_all:
            debug_logger.log("INFO", "Force processing all files")
            return file_paths
        
        needs_processing = []
        
        for file_path in file_paths:
            if self.has_file_changed(file_path):
                needs_processing.append(file_path)
        
        debug_logger.log("INFO", "Files needing processing determined",
                        needs_processing=len(needs_processing),
                        total_files=len(file_paths))
        
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
                if total_files > 0 else 0
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
        debug_logger.log("INFO", "Cleaning up file cache",
                        max_age_days=max_age_days)
        
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
```

## Test Requirements

Create comprehensive tests for change detection:

### Test Cases (16 tests total)

**File Cache Tests:**
1. **test_cache_entry_creation_and_serialization**
2. **test_cache_manager_load_save_cycle**
3. **test_cache_manager_entry_crud_operations**
4. **test_cache_cleanup_stale_entries**
5. **test_cache_statistics_and_validation**
6. **test_cache_export_functionality**

**Hash Calculation Tests:**
7. **test_file_hash_calculation_md5_sha256**
8. **test_file_hash_calculation_large_files**
9. **test_file_hash_calculation_error_handling**

**Change Detection Tests:**
10. **test_file_change_detection_stats_based**
11. **test_file_change_detection_hash_based**
12. **test_file_change_detection_new_files**
13. **test_file_change_detection_deleted_files**
14. **test_directory_change_detection**
15. **test_files_needing_processing_determination**
16. **test_change_detection_with_ignore_patterns**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_processing/test_change_detector.py tests/unit/file_processing/test_file_cache.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_processing/ --cov=spec_cli.file_processing --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_processing/

# Check code formatting
poetry run ruff check spec_cli/file_processing/
poetry run ruff format spec_cli/file_processing/

# Verify imports work correctly
python -c "from spec_cli.file_processing import FileChangeDetector, FileCacheManager; print('Import successful')"

# Test hash calculation
python -c "
from spec_cli.file_processing.change_detector import FileChangeDetector
from pathlib import Path
import tempfile

detector = FileChangeDetector()

# Create a test file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write('Hello, World!')
    test_file = Path(f.name)

try:
    # Calculate hashes
    md5_hash, sha256_hash = detector.calculate_file_hashes(test_file)
    print(f'MD5: {md5_hash}')
    print(f'SHA256: {sha256_hash}')
    
    # Get file info
    file_info = detector.get_file_info(test_file)
    print(f'File info keys: {list(file_info.keys())}')
    print(f'File size: {file_info["size"]} bytes')
finally:
    test_file.unlink()
"

# Test cache operations
python -c "
from spec_cli.file_processing.file_cache import FileCacheManager, FileCacheEntry
import time

manager = FileCacheManager()

# Create a test entry
entry = FileCacheEntry(
    file_path='test/file.py',
    hash_md5='d41d8cd98f00b204e9800998ecf8427e',
    hash_sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    size=1024,
    mtime=time.time(),
    last_processed=time.time(),
)

# Test cache operations
manager.set_entry(entry)
retrieved = manager.get_entry('test/file.py')
print(f'Entry retrieved: {retrieved is not None}')
print(f'Hash matches: {retrieved.hash_md5 == entry.hash_md5}')

# Test statistics
stats = manager.get_cache_statistics()
print(f'Cache statistics:')
for key, value in stats.items():
    print(f'  {key}: {value}')

# Clean up
manager.clear_cache()
print(f'Cache cleared: {len(manager.get_all_entries()) == 0}')
"

# Test change detection
python -c "
from spec_cli.file_processing.change_detector import FileChangeDetector
from pathlib import Path
import tempfile
import time

detector = FileChangeDetector()

# Create a test file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
    f.write('print(\"Hello, World!\")')
    test_file = Path(f.name)

try:
    # First check - should be new
    changed1 = detector.has_file_changed(test_file)
    print(f'First check (new file): {changed1}')
    
    # Update cache
    detector.update_file_cache(test_file)
    
    # Second check - should be unchanged
    changed2 = detector.has_file_changed(test_file)
    print(f'Second check (cached): {changed2}')
    
    # Modify file
    time.sleep(0.1)  # Ensure different mtime
    with test_file.open('a') as f:
        f.write('\n# Modified')
    
    # Third check - should be changed
    changed3 = detector.has_file_changed(test_file)
    print(f'Third check (modified): {changed3}')
    
    # Test deep check
    deep_changed = detector.has_file_changed_deep(test_file)
    print(f'Deep check (modified): {deep_changed}')
    
finally:
    test_file.unlink()
    
# Save cache
detector.save_cache()
print('Cache saved successfully')
"

# Test directory change detection
python -c "
from spec_cli.file_processing.change_detector import FileChangeDetector
from pathlib import Path

detector = FileChangeDetector()

# Test with current directory (limited scan)
current_dir = Path.cwd()
changes = detector.detect_changes_in_directory(
    current_dir, 
    deep_scan=False, 
    max_files=10
)

print(f'Directory change detection results:')
for change_type, files in changes.items():
    print(f'  {change_type}: {len(files)} files')

# Get summary
summary = detector.get_change_summary(changes)
print(f'Change summary:')
for key, value in summary.items():
    print(f'  {key}: {value}')

print(f'Needs processing: {summary["needs_processing"]}')
"
```

## Definition of Done

- [ ] FileChangeDetector class for hash-based change detection
- [ ] FileCacheManager for persistent cache storage in .spec/cache.json
- [ ] File hash calculation with MD5 and SHA256 algorithms
- [ ] Change detection using file stats and content hashes
- [ ] Directory-wide change detection with ignore pattern support
- [ ] Cache validation, cleanup, and maintenance utilities
- [ ] Files needing processing determination logic
- [ ] All 16 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with file metadata and ignore pattern systems
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-11b (conflict resolver) by providing:
- Change detection that conflict resolution can use to identify modified files
- File cache that conflict resolution can leverage for tracking changes
- Hash-based verification that conflict resolution can use for validation
- Foundation for intelligent conflict detection and resolution strategies