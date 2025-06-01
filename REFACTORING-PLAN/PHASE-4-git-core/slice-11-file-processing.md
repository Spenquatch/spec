# Slice 11: File Processing Workflows and Batch Operations [DEPRECATED - SPLIT INTO 11A/11B/11C]

**NOTE: This slice has been split into focused components for better implementation:**
- **[slice-11a-change-detection.md](./slice-11a-change-detection.md)**: File change detection and caching
- **[slice-11b-conflict-resolver.md](./slice-11b-conflict-resolver.md)**: Conflict resolution strategies and merge helpers
- **[slice-11c-batch-processor.md](./slice-11c-batch-processor.md)**: Batch processing and progress events

Please implement the individual slices instead of this combined version.

## Goal

Create comprehensive file processing workflows that handle batch operations, file discovery, processing pipelines, and advanced conflict resolution for complex spec generation scenarios.

## Context

Building on the spec repository orchestration from slice-10, this slice implements the advanced file processing workflows that handle complex scenarios like batch processing entire directories, detecting changes, handling conflicts, and providing sophisticated processing pipelines. This completes the core logic layer by providing the high-level workflows that the CLI and UI will use.

## Scope

**Included in this slice:**
- FileProcessor class for advanced file processing workflows
- Batch processing capabilities for directories and file lists
- Change detection and incremental processing
- Conflict resolution for existing spec files
- Processing pipeline with hooks and validation
- Progress tracking and reporting for long operations

**NOT included in this slice:**
- Rich UI integration (comes in slice-12-rich-ui)
- CLI command implementations (comes in slice-13-cli-commands)
- AI content generation implementation (extension points only)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for processing errors)
- `spec_cli.logging.debug` (debug_logger for processing tracking)
- `spec_cli.config.settings` (SpecSettings for processing configuration)
- `spec_cli.core.spec_repository` (SpecRepository for repository operations)
- `spec_cli.file_system.directory_manager` (DirectoryManager for file discovery)
- `spec_cli.file_system.file_analyzer` (FileAnalyzer for file filtering)
- `spec_cli.templates.generator` (SpecContentGenerator for content generation)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration
- `SpecRepository` from slice-10-spec-repository
- `DirectoryManager` from slice-6-directory-management
- `FileAnalyzer` from slice-5-file-analysis
- `SpecContentGenerator` from slice-8-template-generation

## Files to Create

```
spec_cli/processing/
├── __init__.py             # Module exports
├── file_processor.py       # FileProcessor class and workflows
├── batch_operations.py     # Batch processing capabilities
├── change_detection.py     # Change detection and incremental processing
└── conflict_resolution.py  # Conflict resolution strategies
```

## Implementation Steps

### Step 1: Create spec_cli/processing/__init__.py

```python
"""File processing workflows for spec CLI.

This package provides advanced file processing capabilities including
batch operations, change detection, and conflict resolution.
"""

from .file_processor import FileProcessor
from .batch_operations import BatchProcessor, BatchOperationResult
from .change_detection import ChangeDetector, FileChangeTracker
from .conflict_resolution import ConflictResolver, ConflictResolutionStrategy

__all__ = [
    "FileProcessor",
    "BatchProcessor",
    "BatchOperationResult",
    "ChangeDetector", 
    "FileChangeTracker",
    "ConflictResolver",
    "ConflictResolutionStrategy",
]
```

### Step 2: Create spec_cli/processing/conflict_resolution.py

```python
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from ..exceptions import SpecConflictError
from ..logging.debug import debug_logger

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts with existing spec files."""
    ASK_USER = "ask_user"
    OVERWRITE = "overwrite"
    BACKUP_AND_REPLACE = "backup_and_replace"
    MERGE = "merge"
    SKIP = "skip"
    FAIL = "fail"

class ConflictResolver:
    """Handles conflicts when generating specs for files that already have documentation."""
    
    def __init__(self, default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE):
        self.default_strategy = default_strategy
        self.interactive_callback: Optional[Callable] = None
        
        debug_logger.log("INFO", "ConflictResolver initialized", 
                        default_strategy=default_strategy.value)
    
    def set_interactive_callback(self, callback: Callable[[Dict[str, Any]], ConflictResolutionStrategy]) -> None:
        """Set callback function for interactive conflict resolution.
        
        Args:
            callback: Function that takes conflict info and returns resolution strategy
        """
        self.interactive_callback = callback
        debug_logger.log("INFO", "Interactive callback set for conflict resolution")
    
    def resolve_conflict(self, 
                        spec_dir: Path,
                        existing_files: Dict[str, bool],
                        strategy: Optional[ConflictResolutionStrategy] = None) -> Dict[str, Any]:
        """Resolve conflict with existing spec files.
        
        Args:
            spec_dir: Directory containing spec files
            existing_files: Dict of {filename: exists} for spec files
            strategy: Override strategy for this conflict
            
        Returns:
            Dictionary with resolution details
            
        Raises:
            SpecConflictError: If conflict cannot be resolved
        """
        active_strategy = strategy or self.default_strategy
        
        debug_logger.log("INFO", "Resolving spec file conflict",
                        spec_dir=str(spec_dir),
                        existing_files=existing_files,
                        strategy=active_strategy.value)
        
        conflict_info = {
            "spec_directory": str(spec_dir),
            "existing_files": existing_files,
            "conflicting_files": [name for name, exists in existing_files.items() if exists],
        }
        
        # Use interactive callback if available and strategy is ASK_USER
        if active_strategy == ConflictResolutionStrategy.ASK_USER and self.interactive_callback:
            try:
                active_strategy = self.interactive_callback(conflict_info)
                debug_logger.log("INFO", "Interactive conflict resolution",
                               selected_strategy=active_strategy.value)
            except Exception as e:
                debug_logger.log("WARNING", "Interactive resolution failed, using default",
                               error=str(e))
                active_strategy = self.default_strategy
        
        # Apply resolution strategy
        resolution_result = self._apply_resolution_strategy(spec_dir, existing_files, active_strategy)
        
        debug_logger.log("INFO", "Conflict resolution complete",
                        strategy=active_strategy.value,
                        action_taken=resolution_result.get("action"))
        
        return resolution_result
    
    def _apply_resolution_strategy(self,
                                 spec_dir: Path,
                                 existing_files: Dict[str, bool],
                                 strategy: ConflictResolutionStrategy) -> Dict[str, Any]:
        """Apply the specified resolution strategy."""
        
        if strategy == ConflictResolutionStrategy.OVERWRITE:
            return self._handle_overwrite(spec_dir, existing_files)
        
        elif strategy == ConflictResolutionStrategy.BACKUP_AND_REPLACE:
            return self._handle_backup_and_replace(spec_dir, existing_files)
        
        elif strategy == ConflictResolutionStrategy.MERGE:
            return self._handle_merge(spec_dir, existing_files)
        
        elif strategy == ConflictResolutionStrategy.SKIP:
            return self._handle_skip(spec_dir, existing_files)
        
        elif strategy == ConflictResolutionStrategy.FAIL:
            return self._handle_fail(spec_dir, existing_files)
        
        else:
            raise SpecConflictError(f"Unknown conflict resolution strategy: {strategy}")
    
    def _handle_overwrite(self, spec_dir: Path, existing_files: Dict[str, bool]) -> Dict[str, Any]:
        """Handle overwrite strategy - simply overwrite existing files."""
        return {
            "action": "overwrite",
            "strategy": ConflictResolutionStrategy.OVERWRITE.value,
            "backup_created": False,
            "files_to_overwrite": [name for name, exists in existing_files.items() if exists],
            "proceed": True,
        }
    
    def _handle_backup_and_replace(self, spec_dir: Path, existing_files: Dict[str, bool]) -> Dict[str, Any]:
        """Handle backup and replace strategy."""
        try:
            # Create backup using directory manager
            from ..file_system.directory_manager import DirectoryManager
            from ..config.settings import get_settings
            
            directory_manager = DirectoryManager(get_settings())
            backup_dir = directory_manager.backup_existing_specs(spec_dir)
            
            return {
                "action": "backup_and_replace",
                "strategy": ConflictResolutionStrategy.BACKUP_AND_REPLACE.value,
                "backup_created": backup_dir is not None,
                "backup_directory": str(backup_dir) if backup_dir else None,
                "files_backed_up": [name for name, exists in existing_files.items() if exists],
                "proceed": True,
            }
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to create backup", error=str(e))
            raise SpecConflictError(f"Could not create backup: {e}") from e
    
    def _handle_merge(self, spec_dir: Path, existing_files: Dict[str, bool]) -> Dict[str, Any]:
        """Handle merge strategy - preserve manual edits where possible."""
        merge_plan = {
            "action": "merge",
            "strategy": ConflictResolutionStrategy.MERGE.value,
            "backup_created": False,
            "merge_actions": {},
            "proceed": True,
        }
        
        # For each existing file, determine merge approach
        for filename, exists in existing_files.items():
            if not exists:
                merge_plan["merge_actions"][filename] = "create_new"
                continue
            
            file_path = spec_dir / filename
            
            try:
                # Read existing content to check for manual edits
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple heuristic: check for custom content
                if self._appears_manually_edited(content, filename):
                    merge_plan["merge_actions"][filename] = "preserve_and_extend"
                    debug_logger.log("INFO", "File appears manually edited, will preserve",
                                   file=filename)
                else:
                    merge_plan["merge_actions"][filename] = "replace"
                    debug_logger.log("INFO", "File appears auto-generated, will replace",
                                   file=filename)
                
            except Exception as e:
                debug_logger.log("WARNING", "Could not analyze file for merge",
                               file=filename, error=str(e))
                merge_plan["merge_actions"][filename] = "backup_and_replace"
        
        return merge_plan
    
    def _handle_skip(self, spec_dir: Path, existing_files: Dict[str, bool]) -> Dict[str, Any]:
        """Handle skip strategy - don't modify existing files."""
        return {
            "action": "skip",
            "strategy": ConflictResolutionStrategy.SKIP.value,
            "backup_created": False,
            "skipped_files": [name for name, exists in existing_files.items() if exists],
            "proceed": False,
            "reason": "Existing spec files found, skipping as requested",
        }
    
    def _handle_fail(self, spec_dir: Path, existing_files: Dict[str, bool]) -> Dict[str, Any]:
        """Handle fail strategy - raise error on conflicts."""
        conflicting_files = [name for name, exists in existing_files.items() if exists]
        error_msg = f"Spec files already exist in {spec_dir}: {', '.join(conflicting_files)}"
        raise SpecConflictError(error_msg)
    
    def _appears_manually_edited(self, content: str, filename: str) -> bool:
        """Heuristic to determine if content appears manually edited."""
        
        # Check for common indicators of manual editing
        manual_indicators = [
            "# Custom",
            "# Manual",
            "# User added",
            "# TODO:",
            "# FIXME:",
            "# NOTE:",
            "[manually added]",
            "[custom content]",
        ]
        
        content_lower = content.lower()
        for indicator in manual_indicators:
            if indicator.lower() in content_lower:
                debug_logger.log("DEBUG", "Manual edit indicator found",
                               file=filename, indicator=indicator)
                return True
        
        # Check for content significantly different from template
        if filename == "index.md":
            # Look for sections that don't match standard template structure
            if "## Custom" in content or "## Additional" in content:
                return True
        
        elif filename == "history.md":
            # Look for multiple dated entries (indicates manual maintenance)
            import re
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            dates_found = re.findall(date_pattern, content)
            if len(dates_found) > 2:  # More than initial creation entries
                return True
        
        # Default to considering it auto-generated
        return False
    
    def get_conflict_summary(self, spec_dir: Path) -> Dict[str, Any]:
        """Get summary of potential conflicts without resolving them.
        
        Args:
            spec_dir: Directory to check for conflicts
            
        Returns:
            Dictionary with conflict summary
        """
        from ..file_system.directory_manager import DirectoryManager
        from ..config.settings import get_settings
        
        directory_manager = DirectoryManager(get_settings())
        existing_files = directory_manager.check_existing_specs(spec_dir)
        
        has_conflicts = any(existing_files.values())
        
        summary = {
            "has_conflicts": has_conflicts,
            "spec_directory": str(spec_dir),
            "existing_files": existing_files,
            "conflicting_files": [name for name, exists in existing_files.items() if exists],
            "recommended_strategy": self._recommend_strategy(spec_dir, existing_files),
        }
        
        debug_logger.log("INFO", "Conflict summary generated",
                        spec_dir=str(spec_dir),
                        has_conflicts=has_conflicts,
                        conflicting_count=len(summary["conflicting_files"]))
        
        return summary
    
    def _recommend_strategy(self, spec_dir: Path, existing_files: Dict[str, bool]) -> ConflictResolutionStrategy:
        """Recommend appropriate conflict resolution strategy."""
        
        if not any(existing_files.values()):
            return ConflictResolutionStrategy.OVERWRITE  # No conflicts
        
        # Check if files appear manually edited
        manually_edited_count = 0
        for filename, exists in existing_files.items():
            if not exists:
                continue
            
            try:
                file_path = spec_dir / filename
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                
                if self._appears_manually_edited(content, filename):
                    manually_edited_count += 1
                    
            except Exception:
                pass
        
        if manually_edited_count > 0:
            return ConflictResolutionStrategy.MERGE
        else:
            return ConflictResolutionStrategy.BACKUP_AND_REPLACE
```

### Step 3: Create spec_cli/processing/change_detection.py

```python
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from ..exceptions import SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from ..file_system.file_analyzer import FileAnalyzer

class FileChangeTracker:
    """Tracks changes to source files for incremental spec generation."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.cache_file = self.settings.root_path / ".spec-cache.json"
        self.file_analyzer = FileAnalyzer(self.settings)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        
        debug_logger.log("INFO", "FileChangeTracker initialized",
                        cache_file=str(self.cache_file))
    
    def _load_cache(self) -> None:
        """Load the change tracking cache from disk."""
        if self.cache_file.exists():
            try:
                with self.cache_file.open('r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                
                debug_logger.log("INFO", "Change tracking cache loaded",
                               tracked_files=len(self._cache))
                
            except (json.JSONDecodeError, OSError) as e:
                debug_logger.log("WARNING", "Could not load change tracking cache",
                               error=str(e))
                self._cache = {}
        else:
            debug_logger.log("INFO", "No existing change tracking cache found")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save the change tracking cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self.cache_file.open('w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
            
            debug_logger.log("INFO", "Change tracking cache saved",
                           tracked_files=len(self._cache))
            
        except OSError as e:
            debug_logger.log("ERROR", "Could not save change tracking cache",
                           error=str(e))
    
    def track_file(self, file_path: Path) -> None:
        """Add a file to change tracking.
        
        Args:
            file_path: Path to the file to track
        """
        try:
            file_info = self._get_file_info(file_path)
            self._cache[str(file_path)] = file_info
            
            debug_logger.log("DEBUG", "File added to change tracking",
                           file=str(file_path))
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not track file",
                           file=str(file_path), error=str(e))
    
    def has_changed(self, file_path: Path) -> bool:
        """Check if a file has changed since last tracking.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has changed or is not tracked
        """
        file_path_str = str(file_path)
        
        if file_path_str not in self._cache:
            debug_logger.log("DEBUG", "File not in cache, considering changed",
                           file=str(file_path))
            return True
        
        try:
            current_info = self._get_file_info(file_path)
            cached_info = self._cache[file_path_str]
            
            # Compare relevant fields
            changed = (
                current_info["size"] != cached_info["size"] or
                current_info["mtime"] != cached_info["mtime"] or
                current_info["content_hash"] != cached_info["content_hash"]
            )
            
            debug_logger.log("DEBUG", "File change check",
                           file=str(file_path), changed=changed)
            
            return changed
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not check file changes",
                           file=str(file_path), error=str(e))
            return True  # Assume changed if we can't check
    
    def update_tracking(self, file_path: Path) -> None:
        """Update tracking information for a file.
        
        Args:
            file_path: Path to the file to update
        """
        self.track_file(file_path)  # Same implementation
        self._save_cache()
    
    def get_changed_files(self, file_paths: List[Path]) -> List[Path]:
        """Get list of files that have changed.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            List of file paths that have changed
        """
        debug_logger.log("INFO", "Checking for changed files",
                        file_count=len(file_paths))
        
        changed_files = []
        for file_path in file_paths:
            if self.has_changed(file_path):
                changed_files.append(file_path)
        
        debug_logger.log("INFO", "Changed file check complete",
                        total_files=len(file_paths),
                        changed_files=len(changed_files))
        
        return changed_files
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get tracking information for a file."""
        absolute_path = file_path if file_path.is_absolute() else self.settings.root_path / file_path
        
        if not absolute_path.exists():
            raise SpecFileError(f"File does not exist: {file_path}")
        
        stat_info = absolute_path.stat()
        
        # Calculate content hash for change detection
        content_hash = None
        if stat_info.st_size < 10 * 1024 * 1024:  # Only hash files under 10MB
            try:
                with absolute_path.open('rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()
            except Exception as e:
                debug_logger.log("WARNING", "Could not calculate content hash",
                               file=str(file_path), error=str(e))
        
        return {
            "size": stat_info.st_size,
            "mtime": stat_info.st_mtime,
            "content_hash": content_hash,
            "tracked_at": datetime.now().isoformat(),
        }
    
    def clear_cache(self) -> None:
        """Clear the change tracking cache."""
        self._cache = {}
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                debug_logger.log("INFO", "Change tracking cache cleared")
            except OSError as e:
                debug_logger.log("WARNING", "Could not remove cache file", error=str(e))
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get statistics about change tracking.
        
        Returns:
            Dictionary with tracking statistics
        """
        return {
            "tracked_files": len(self._cache),
            "cache_file": str(self.cache_file),
            "cache_exists": self.cache_file.exists(),
            "cache_size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
        }

class ChangeDetector:
    """Detects changes in source files and determines what needs to be regenerated."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.file_tracker = FileChangeTracker(self.settings)
        self.file_analyzer = FileAnalyzer(self.settings)
        
        debug_logger.log("INFO", "ChangeDetector initialized")
    
    def detect_changes(self, file_paths: List[Path], force_check: bool = False) -> Dict[str, Any]:
        """Detect changes in the provided files.
        
        Args:
            file_paths: List of file paths to check for changes
            force_check: If True, ignore cache and check all files
            
        Returns:
            Dictionary with change detection results
        """
        debug_logger.log("INFO", "Detecting changes in files",
                        file_count=len(file_paths), force_check=force_check)
        
        with debug_logger.timer("change_detection"):
            if force_check:
                changed_files = file_paths.copy()
                new_files = []
                unchanged_files = []
            else:
                changed_files = self.file_tracker.get_changed_files(file_paths)
                new_files = [f for f in file_paths if str(f) not in self.file_tracker._cache]
                unchanged_files = [f for f in file_paths if f not in changed_files and f not in new_files]
            
            # Categorize by change type
            results = {
                "total_files": len(file_paths),
                "changed_files": [str(f) for f in changed_files],
                "new_files": [str(f) for f in new_files],
                "unchanged_files": [str(f) for f in unchanged_files],
                "files_requiring_update": changed_files + new_files,
                "change_summary": {
                    "has_changes": len(changed_files) > 0 or len(new_files) > 0,
                    "changed_count": len(changed_files),
                    "new_count": len(new_files),
                    "unchanged_count": len(unchanged_files),
                },
                "force_check": force_check,
            }
            
            debug_logger.log("INFO", "Change detection complete",
                           changed=len(changed_files),
                           new=len(new_files),
                           unchanged=len(unchanged_files))
            
            return results
    
    def detect_spec_staleness(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Detect if spec files are stale compared to source files.
        
        Args:
            file_paths: List of source file paths to check
            
        Returns:
            Dictionary with staleness detection results
        """
        debug_logger.log("INFO", "Detecting spec staleness",
                        file_count=len(file_paths))
        
        stale_specs = []
        missing_specs = []
        up_to_date_specs = []
        
        for file_path in file_paths:
            try:
                # Convert to spec directory path
                from ..file_system.path_resolver import PathResolver
                path_resolver = PathResolver(self.settings)
                spec_dir = path_resolver.convert_to_spec_directory_path(file_path)
                
                index_file = spec_dir / "index.md"
                history_file = spec_dir / "history.md"
                
                # Check if spec files exist
                if not index_file.exists() and not history_file.exists():
                    missing_specs.append(str(file_path))
                    continue
                
                # Check if source file is newer than spec files
                source_path = path_resolver.convert_to_absolute_path(file_path)
                if not source_path.exists():
                    continue
                
                source_mtime = source_path.stat().st_mtime
                
                spec_files_outdated = False
                if index_file.exists():
                    spec_mtime = index_file.stat().st_mtime
                    if source_mtime > spec_mtime:
                        spec_files_outdated = True
                
                if history_file.exists():
                    spec_mtime = history_file.stat().st_mtime
                    if source_mtime > spec_mtime:
                        spec_files_outdated = True
                
                if spec_files_outdated:
                    stale_specs.append(str(file_path))
                else:
                    up_to_date_specs.append(str(file_path))
                
            except Exception as e:
                debug_logger.log("WARNING", "Could not check spec staleness",
                               file=str(file_path), error=str(e))
        
        results = {
            "stale_specs": stale_specs,
            "missing_specs": missing_specs,
            "up_to_date_specs": up_to_date_specs,
            "staleness_summary": {
                "has_stale_specs": len(stale_specs) > 0,
                "has_missing_specs": len(missing_specs) > 0,
                "stale_count": len(stale_specs),
                "missing_count": len(missing_specs),
                "up_to_date_count": len(up_to_date_specs),
            },
        }
        
        debug_logger.log("INFO", "Spec staleness detection complete",
                        stale=len(stale_specs),
                        missing=len(missing_specs),
                        up_to_date=len(up_to_date_specs))
        
        return results
    
    def update_change_tracking(self, file_paths: List[Path]) -> None:
        """Update change tracking for the provided files.
        
        Args:
            file_paths: List of file paths to update tracking for
        """
        debug_logger.log("INFO", "Updating change tracking",
                        file_count=len(file_paths))
        
        for file_path in file_paths:
            try:
                self.file_tracker.update_tracking(file_path)
            except Exception as e:
                debug_logger.log("WARNING", "Could not update tracking for file",
                               file=str(file_path), error=str(e))
        
        debug_logger.log("INFO", "Change tracking update complete")
```

### Step 4: Create spec_cli/processing/batch_operations.py

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from ..exceptions import SpecOperationError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from ..file_system.directory_manager import DirectoryManager
from ..file_system.file_analyzer import FileAnalyzer
from .change_detection import ChangeDetector
from .conflict_resolution import ConflictResolver, ConflictResolutionStrategy

class BatchOperationType(Enum):
    """Types of batch operations."""
    GENERATE_SPECS = "generate_specs"
    UPDATE_SPECS = "update_specs"
    VALIDATE_SPECS = "validate_specs"
    CLEANUP_SPECS = "cleanup_specs"

@dataclass
class BatchOperationResult:
    """Result of a batch operation."""
    operation_type: BatchOperationType
    total_files: int
    successful_files: List[str]
    failed_files: List[Dict[str, str]]  # [{"file": path, "error": message}]
    skipped_files: List[str]
    processing_time: float
    additional_info: Dict[str, Any]

class BatchProcessor:
    """Handles batch processing operations for multiple files."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.directory_manager = DirectoryManager(self.settings)
        self.file_analyzer = FileAnalyzer(self.settings)
        self.change_detector = ChangeDetector(self.settings)
        self.conflict_resolver = ConflictResolver()
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        debug_logger.log("INFO", "BatchProcessor initialized")
    
    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback function for progress updates.
        
        Args:
            callback: Function that receives progress information
        """
        self.progress_callback = callback
        debug_logger.log("INFO", "Progress callback set for batch operations")
    
    def process_directory(self,
                         directory: Path,
                         operation_type: BatchOperationType,
                         recursive: bool = True,
                         file_filter: Optional[Callable[[Path], bool]] = None,
                         **operation_kwargs) -> BatchOperationResult:
        """Process all files in a directory.
        
        Args:
            directory: Directory to process
            operation_type: Type of batch operation to perform
            recursive: Whether to process files recursively
            file_filter: Optional function to filter files
            **operation_kwargs: Additional arguments for the operation
            
        Returns:
            BatchOperationResult with processing results
        """
        debug_logger.log("INFO", "Processing directory",
                        directory=str(directory),
                        operation=operation_type.value,
                        recursive=recursive)
        
        start_time = time.time()
        
        try:
            # Discover files
            source_files = self.directory_manager.find_source_files(directory, recursive)
            
            # Apply file filter if provided
            if file_filter:
                source_files = [f for f in source_files if file_filter(f)]
            
            debug_logger.log("INFO", "Files discovered for batch processing",
                           total_files=len(source_files))
            
            # Process files
            result = self.process_files(source_files, operation_type, **operation_kwargs)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            debug_logger.log("INFO", "Directory processing complete",
                           directory=str(directory),
                           total_files=result.total_files,
                           successful=len(result.successful_files),
                           failed=len(result.failed_files),
                           time=f"{processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process directory {directory}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def process_files(self,
                     file_paths: List[Path],
                     operation_type: BatchOperationType,
                     max_workers: int = 4,
                     **operation_kwargs) -> BatchOperationResult:
        """Process a list of files in parallel.
        
        Args:
            file_paths: List of file paths to process
            operation_type: Type of batch operation to perform
            max_workers: Maximum number of parallel workers
            **operation_kwargs: Additional arguments for the operation
            
        Returns:
            BatchOperationResult with processing results
        """
        debug_logger.log("INFO", "Processing files in batch",
                        file_count=len(file_paths),
                        operation=operation_type.value,
                        max_workers=max_workers)
        
        start_time = time.time()
        
        successful_files = []
        failed_files = []
        skipped_files = []
        additional_info = {"operation_details": {}}
        
        # Progress tracking
        total_files = len(file_paths)
        processed_count = 0
        
        self._update_progress({
            "operation": operation_type.value,
            "total_files": total_files,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "stage": "starting",
        })
        
        try:
            # Process files with thread pool
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(self._process_single_file, file_path, operation_type, **operation_kwargs): file_path
                    for file_path in file_paths
                }
                
                # Process completed tasks
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    processed_count += 1
                    
                    try:
                        result = future.result()
                        
                        if result["status"] == "success":
                            successful_files.append(str(file_path))
                        elif result["status"] == "skipped":
                            skipped_files.append(str(file_path))
                        else:
                            failed_files.append({
                                "file": str(file_path),
                                "error": result.get("error", "Unknown error"),
                            })
                        
                        # Update additional info
                        if result.get("details"):
                            additional_info["operation_details"][str(file_path)] = result["details"]
                        
                    except Exception as e:
                        failed_files.append({
                            "file": str(file_path),
                            "error": str(e),
                        })
                        debug_logger.log("ERROR", "File processing failed",
                                       file=str(file_path), error=str(e))
                    
                    # Update progress
                    self._update_progress({
                        "operation": operation_type.value,
                        "total_files": total_files,
                        "processed": processed_count,
                        "successful": len(successful_files),
                        "failed": len(failed_files),
                        "skipped": len(skipped_files),
                        "stage": "processing",
                        "current_file": str(file_path),
                    })
            
            processing_time = time.time() - start_time
            
            # Final progress update
            self._update_progress({
                "operation": operation_type.value,
                "total_files": total_files,
                "processed": processed_count,
                "successful": len(successful_files),
                "failed": len(failed_files),
                "skipped": len(skipped_files),
                "stage": "complete",
                "processing_time": processing_time,
            })
            
            result = BatchOperationResult(
                operation_type=operation_type,
                total_files=total_files,
                successful_files=successful_files,
                failed_files=failed_files,
                skipped_files=skipped_files,
                processing_time=processing_time,
                additional_info=additional_info,
            )
            
            debug_logger.log("INFO", "Batch file processing complete",
                           operation=operation_type.value,
                           total=total_files,
                           successful=len(successful_files),
                           failed=len(failed_files),
                           skipped=len(skipped_files),
                           time=f"{processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def _process_single_file(self,
                           file_path: Path,
                           operation_type: BatchOperationType,
                           **operation_kwargs) -> Dict[str, Any]:
        """Process a single file based on operation type."""
        
        try:
            if operation_type == BatchOperationType.GENERATE_SPECS:
                return self._generate_spec_for_file(file_path, **operation_kwargs)
            
            elif operation_type == BatchOperationType.UPDATE_SPECS:
                return self._update_spec_for_file(file_path, **operation_kwargs)
            
            elif operation_type == BatchOperationType.VALIDATE_SPECS:
                return self._validate_spec_for_file(file_path, **operation_kwargs)
            
            elif operation_type == BatchOperationType.CLEANUP_SPECS:
                return self._cleanup_spec_for_file(file_path, **operation_kwargs)
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation type: {operation_type}",
                }
                
        except Exception as e:
            debug_logger.log("ERROR", "Single file processing failed",
                           file=str(file_path), operation=operation_type.value, error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _generate_spec_for_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Generate spec for a single file."""
        
        # Check if file should be skipped
        skip_existing = kwargs.get("skip_existing", False)
        conflict_strategy = kwargs.get("conflict_strategy", ConflictResolutionStrategy.BACKUP_AND_REPLACE)
        
        # Create spec directory
        spec_dir = self.directory_manager.create_spec_directory(file_path)
        
        # Check for existing files
        existing_files = self.directory_manager.check_existing_specs(spec_dir)
        has_existing = any(existing_files.values())
        
        if has_existing and skip_existing:
            return {
                "status": "skipped",
                "reason": "Existing spec files found and skip_existing=True",
                "details": {"existing_files": existing_files},
            }
        
        # Handle conflicts if needed
        if has_existing:
            try:
                resolution = self.conflict_resolver.resolve_conflict(
                    spec_dir, existing_files, conflict_strategy
                )
                
                if not resolution.get("proceed", True):
                    return {
                        "status": "skipped",
                        "reason": f"Conflict resolution: {resolution['action']}",
                        "details": resolution,
                    }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Conflict resolution failed: {e}",
                }
        
        # Generate spec content (placeholder for now)
        try:
            # This would call the actual spec generation
            # For now, just indicate success
            return {
                "status": "success",
                "details": {
                    "spec_directory": str(spec_dir),
                    "files_generated": ["index.md", "history.md"],
                    "existing_files_handled": has_existing,
                },
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Spec generation failed: {e}",
            }
    
    def _update_spec_for_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Update spec for a single file."""
        
        # Check if file has changed
        force_update = kwargs.get("force_update", False)
        
        if not force_update:
            change_result = self.change_detector.detect_changes([file_path])
            if str(file_path) not in change_result["files_requiring_update"]:
                return {
                    "status": "skipped",
                    "reason": "File has not changed since last update",
                    "details": {"change_detection": change_result},
                }
        
        # Proceed with update (similar to generate but preserving existing content)
        return self._generate_spec_for_file(file_path, **kwargs)
    
    def _validate_spec_for_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Validate spec for a single file."""
        
        from ..file_system.path_resolver import PathResolver
        path_resolver = PathResolver(self.settings)
        spec_dir = path_resolver.convert_to_spec_directory_path(file_path)
        
        validation_issues = []
        
        # Check if spec files exist
        index_file = spec_dir / "index.md"
        history_file = spec_dir / "history.md"
        
        if not index_file.exists():
            validation_issues.append("index.md file is missing")
        
        if not history_file.exists():
            validation_issues.append("history.md file is missing")
        
        # Check file contents if they exist
        for spec_file in [index_file, history_file]:
            if spec_file.exists():
                try:
                    with spec_file.open('r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if not content.strip():
                        validation_issues.append(f"{spec_file.name} is empty")
                    elif len(content) < 50:
                        validation_issues.append(f"{spec_file.name} appears incomplete (< 50 characters)")
                        
                except Exception as e:
                    validation_issues.append(f"Could not read {spec_file.name}: {e}")
        
        if validation_issues:
            return {
                "status": "error",
                "error": f"Validation failed: {'; '.join(validation_issues)}",
                "details": {"validation_issues": validation_issues},
            }
        else:
            return {
                "status": "success",
                "details": {"validation_status": "All checks passed"},
            }
    
    def _cleanup_spec_for_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Clean up spec for a single file."""
        
        # Check if source file still exists
        absolute_path = self.settings.root_path / file_path
        
        if absolute_path.exists():
            return {
                "status": "skipped",
                "reason": "Source file still exists, no cleanup needed",
            }
        
        # Remove orphaned spec directory
        from ..file_system.path_resolver import PathResolver
        path_resolver = PathResolver(self.settings)
        spec_dir = path_resolver.convert_to_spec_directory_path(file_path)
        
        if spec_dir.exists():
            try:
                import shutil
                shutil.rmtree(spec_dir)
                
                return {
                    "status": "success",
                    "details": {
                        "action": "removed_orphaned_spec",
                        "spec_directory": str(spec_dir),
                    },
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Could not remove spec directory: {e}",
                }
        else:
            return {
                "status": "skipped",
                "reason": "No spec directory found to clean up",
            }
    
    def _update_progress(self, progress_info: Dict[str, Any]) -> None:
        """Update progress via callback if available."""
        if self.progress_callback:
            try:
                self.progress_callback(progress_info)
            except Exception as e:
                debug_logger.log("WARNING", "Progress callback failed", error=str(e))
    
    def get_processing_statistics(self, result: BatchOperationResult) -> Dict[str, Any]:
        """Get detailed statistics from a batch operation result.
        
        Args:
            result: BatchOperationResult to analyze
            
        Returns:
            Dictionary with detailed statistics
        """
        stats = {
            "operation_type": result.operation_type.value,
            "summary": {
                "total_files": result.total_files,
                "successful": len(result.successful_files),
                "failed": len(result.failed_files),
                "skipped": len(result.skipped_files),
                "processing_time": result.processing_time,
            },
            "rates": {},
            "error_analysis": {},
        }
        
        if result.total_files > 0:
            stats["rates"]["success_rate"] = len(result.successful_files) / result.total_files
            stats["rates"]["failure_rate"] = len(result.failed_files) / result.total_files
            stats["rates"]["skip_rate"] = len(result.skipped_files) / result.total_files
        
        if result.processing_time > 0:
            stats["rates"]["files_per_second"] = result.total_files / result.processing_time
        
        # Analyze error patterns
        if result.failed_files:
            error_types = {}
            for failed_file in result.failed_files:
                error = failed_file["error"]
                error_type = error.split(":")[0] if ":" in error else "Unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            stats["error_analysis"]["error_types"] = error_types
            stats["error_analysis"]["most_common_error"] = max(error_types.items(), key=lambda x: x[1])
        
        return stats
```

### Step 5: Create spec_cli/processing/file_processor.py

```python
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from ..exceptions import SpecOperationError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from ..core.spec_repository import SpecRepository
from .batch_operations import BatchProcessor, BatchOperationType, BatchOperationResult
from .change_detection import ChangeDetector
from .conflict_resolution import ConflictResolver, ConflictResolutionStrategy

class FileProcessor:
    """High-level file processing workflows coordinating all processing capabilities."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.spec_repository = SpecRepository(self.settings)
        self.batch_processor = BatchProcessor(self.settings)
        self.change_detector = ChangeDetector(self.settings)
        self.conflict_resolver = ConflictResolver()
        
        debug_logger.log("INFO", "FileProcessor initialized")
    
    def process_files_for_specs(self,
                               file_paths: List[str],
                               template_name: Optional[str] = None,
                               ai_enabled: bool = False,
                               conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE,
                               incremental: bool = True,
                               commit_changes: bool = False,
                               commit_message: Optional[str] = None) -> Dict[str, Any]:
        """Process files to generate spec documentation with full workflow.
        
        Args:
            file_paths: List of file paths to process
            template_name: Optional template preset name
            ai_enabled: Whether to use AI for content generation
            conflict_strategy: How to handle existing spec files
            incremental: Whether to use change detection for incremental processing
            commit_changes: Whether to commit changes to Git
            commit_message: Optional commit message
            
        Returns:
            Dictionary with comprehensive processing results
        """
        debug_logger.log("INFO", "Processing files for spec generation",
                        file_count=len(file_paths),
                        template=template_name,
                        ai_enabled=ai_enabled,
                        incremental=incremental,
                        commit_changes=commit_changes)
        
        try:
            with debug_logger.timer("file_processing_workflow"):
                # Initialize repository if needed
                if not self.spec_repository.is_initialized():
                    debug_logger.log("INFO", "Initializing spec repository")
                    self.spec_repository.initialize()
                
                # Convert string paths to Path objects
                path_objects = [Path(p) for p in file_paths]
                
                # Perform change detection if incremental
                files_to_process = path_objects
                change_info = None
                
                if incremental:
                    debug_logger.log("INFO", "Performing incremental change detection")
                    change_info = self.change_detector.detect_changes(path_objects)
                    files_to_process = change_info["files_requiring_update"]
                    
                    if not files_to_process:
                        debug_logger.log("INFO", "No files require processing (no changes detected)")
                        return {
                            "status": "success",
                            "operation": "process_files_for_specs",
                            "files_processed": 0,
                            "files_skipped": len(file_paths),
                            "reason": "No changes detected",
                            "change_detection": change_info,
                        }
                
                # Set up conflict resolution
                self.conflict_resolver.default_strategy = conflict_strategy
                
                # Process files using batch processor
                debug_logger.log("INFO", "Starting batch spec generation",
                               files_to_process=len(files_to_process))
                
                batch_result = self.batch_processor.process_files(
                    files_to_process,
                    BatchOperationType.GENERATE_SPECS,
                    template_name=template_name,
                    ai_enabled=ai_enabled,
                    conflict_strategy=conflict_strategy,
                )
                
                # Generate spec files using repository
                if batch_result.successful_files:
                    debug_logger.log("INFO", "Generating specs via repository",
                                   successful_files=len(batch_result.successful_files))
                    
                    generation_result = self.spec_repository.generate_specs(
                        batch_result.successful_files,
                        template_name=template_name,
                        ai_enabled=ai_enabled,
                        backup_existing=(conflict_strategy == ConflictResolutionStrategy.BACKUP_AND_REPLACE),
                    )
                else:
                    generation_result = {"generated_files": [], "successful_count": 0}
                
                # Add generated files to Git
                if generation_result["generated_files"]:
                    spec_files_to_add = []
                    for gen_file in generation_result["generated_files"]:
                        spec_files_to_add.extend([
                            gen_file["index_file"],
                            gen_file["history_file"],
                        ])
                    
                    debug_logger.log("INFO", "Adding generated spec files to Git",
                                   spec_files=len(spec_files_to_add))
                    
                    self.spec_repository.add_files(spec_files_to_add, force=True)
                
                # Update change tracking
                if incremental and files_to_process:
                    debug_logger.log("INFO", "Updating change tracking")
                    self.change_detector.update_change_tracking(files_to_process)
                
                # Commit changes if requested
                commit_result = None
                if commit_changes and generation_result["generated_files"]:
                    message = commit_message or f"Generate specs for {len(generation_result['generated_files'])} files"
                    debug_logger.log("INFO", "Committing changes to Git", message=message)
                    commit_result = self.spec_repository.commit_changes(message)
                
                # Compile final results
                result = {
                    "status": "success",
                    "operation": "process_files_for_specs",
                    "input_files": file_paths,
                    "files_processed": len(files_to_process),
                    "files_skipped": len(path_objects) - len(files_to_process),
                    "generation_result": generation_result,
                    "batch_result": {
                        "successful": len(batch_result.successful_files),
                        "failed": len(batch_result.failed_files),
                        "skipped": len(batch_result.skipped_files),
                        "processing_time": batch_result.processing_time,
                    },
                    "change_detection": change_info,
                    "commit_result": commit_result,
                    "settings": {
                        "template_name": template_name,
                        "ai_enabled": ai_enabled,
                        "conflict_strategy": conflict_strategy.value,
                        "incremental": incremental,
                        "commit_changes": commit_changes,
                    },
                }
                
                debug_logger.log("INFO", "File processing workflow complete",
                               processed=len(files_to_process),
                               generated=generation_result["successful_count"],
                               committed=commit_result is not None)
                
                return result
                
        except Exception as e:
            error_msg = f"File processing workflow failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def process_directory_for_specs(self,
                                   directory: Path,
                                   recursive: bool = True,
                                   file_patterns: Optional[List[str]] = None,
                                   **processing_kwargs) -> Dict[str, Any]:
        """Process entire directory for spec generation.
        
        Args:
            directory: Directory to process
            recursive: Whether to process recursively
            file_patterns: Optional list of file patterns to include
            **processing_kwargs: Additional arguments for file processing
            
        Returns:
            Dictionary with processing results
        """
        debug_logger.log("INFO", "Processing directory for specs",
                        directory=str(directory),
                        recursive=recursive,
                        patterns=file_patterns)
        
        try:
            # Create file filter if patterns provided
            file_filter = None
            if file_patterns:
                import fnmatch
                def pattern_filter(file_path: Path) -> bool:
                    return any(fnmatch.fnmatch(file_path.name, pattern) for pattern in file_patterns)
                file_filter = pattern_filter
            
            # Use batch processor to discover and process files
            batch_result = self.batch_processor.process_directory(
                directory,
                BatchOperationType.GENERATE_SPECS,
                recursive=recursive,
                file_filter=file_filter,
                **processing_kwargs
            )
            
            # If successful files were found, process them through the full workflow
            if batch_result.successful_files:
                workflow_result = self.process_files_for_specs(
                    batch_result.successful_files,
                    **processing_kwargs
                )
                
                # Combine results
                return {
                    "status": "success",
                    "operation": "process_directory_for_specs",
                    "directory": str(directory),
                    "directory_processing": {
                        "files_discovered": batch_result.total_files,
                        "files_eligible": len(batch_result.successful_files),
                    },
                    "workflow_result": workflow_result,
                    "batch_result": batch_result,
                }
            else:
                return {
                    "status": "success",
                    "operation": "process_directory_for_specs",
                    "directory": str(directory),
                    "files_processed": 0,
                    "reason": "No eligible files found in directory",
                    "batch_result": batch_result,
                }
                
        except Exception as e:
            error_msg = f"Directory processing failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def update_specs_incrementally(self,
                                  file_paths: Optional[List[str]] = None,
                                  force_update: bool = False,
                                  commit_changes: bool = False) -> Dict[str, Any]:
        """Update specs incrementally based on file changes.
        
        Args:
            file_paths: Optional list of specific files to check (all tracked files if None)
            force_update: Whether to force update regardless of changes
            commit_changes: Whether to commit changes
            
        Returns:
            Dictionary with update results
        """
        debug_logger.log("INFO", "Performing incremental spec updates",
                        specific_files=file_paths is not None,
                        force_update=force_update)
        
        try:
            # Determine files to check
            if file_paths:
                check_files = [Path(p) for p in file_paths]
            else:
                # Get all tracked files from change tracker
                tracking_stats = self.change_detector.file_tracker.get_tracking_stats()
                if tracking_stats["tracked_files"] == 0:
                    return {
                        "status": "success",
                        "operation": "update_specs_incrementally",
                        "files_updated": 0,
                        "reason": "No files are currently tracked for changes",
                    }
                
                # For now, skip automatic discovery of all tracked files
                # This would require extending the change tracker
                return {
                    "status": "error",
                    "operation": "update_specs_incrementally",
                    "error": "Automatic discovery of tracked files not yet implemented",
                }
            
            # Detect changes
            if not force_update:
                change_result = self.change_detector.detect_changes(check_files)
                files_to_update = change_result["files_requiring_update"]
                
                if not files_to_update:
                    return {
                        "status": "success",
                        "operation": "update_specs_incrementally",
                        "files_checked": len(check_files),
                        "files_updated": 0,
                        "reason": "No files have changed",
                        "change_detection": change_result,
                    }
            else:
                files_to_update = check_files
                change_result = None
            
            # Process updates using batch processor
            batch_result = self.batch_processor.process_files(
                files_to_update,
                BatchOperationType.UPDATE_SPECS,
                force_update=force_update,
            )
            
            # Update change tracking
            if files_to_update:
                self.change_detector.update_change_tracking(files_to_update)
            
            # Commit if requested and there were updates
            commit_result = None
            if commit_changes and batch_result.successful_files:
                message = f"Update specs for {len(batch_result.successful_files)} changed files"
                commit_result = self.spec_repository.commit_changes(message)
            
            return {
                "status": "success",
                "operation": "update_specs_incrementally",
                "files_checked": len(check_files) if file_paths else 0,
                "files_updated": len(batch_result.successful_files),
                "change_detection": change_result,
                "batch_result": batch_result,
                "commit_result": commit_result,
            }
            
        except Exception as e:
            error_msg = f"Incremental update failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def validate_all_specs(self) -> Dict[str, Any]:
        """Validate all existing spec files.
        
        Returns:
            Dictionary with validation results
        """
        debug_logger.log("INFO", "Validating all spec files")
        
        try:
            # Find all existing spec files
            if not self.settings.specs_dir.exists():
                return {
                    "status": "success",
                    "operation": "validate_all_specs",
                    "specs_validated": 0,
                    "reason": "No .specs directory found",
                }
            
            # Get all spec directories
            spec_dirs = [
                d for d in self.settings.specs_dir.rglob("*")
                if d.is_dir() and any((d / f).exists() for f in ["index.md", "history.md"])
            ]
            
            if not spec_dirs:
                return {
                    "status": "success",
                    "operation": "validate_all_specs",
                    "specs_validated": 0,
                    "reason": "No spec directories found",
                }
            
            # Convert spec directories back to source file paths for validation
            from ..file_system.path_resolver import PathResolver
            path_resolver = PathResolver(self.settings)
            
            source_files = []
            for spec_dir in spec_dirs:
                try:
                    relative_spec_path = spec_dir.relative_to(self.settings.specs_dir)
                    source_path = Path(relative_spec_path)
                    source_files.append(source_path)
                except ValueError:
                    debug_logger.log("WARNING", "Could not determine source file for spec",
                                   spec_dir=str(spec_dir))
            
            # Validate using batch processor
            batch_result = self.batch_processor.process_files(
                source_files,
                BatchOperationType.VALIDATE_SPECS,
            )
            
            return {
                "status": "success",
                "operation": "validate_all_specs",
                "specs_validated": batch_result.total_files,
                "validation_results": {
                    "valid_specs": len(batch_result.successful_files),
                    "invalid_specs": len(batch_result.failed_files),
                    "skipped_specs": len(batch_result.skipped_files),
                },
                "batch_result": batch_result,
            }
            
        except Exception as e:
            error_msg = f"Spec validation failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def cleanup_orphaned_specs(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up orphaned spec files (specs without corresponding source files).
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Dictionary with cleanup results
        """
        debug_logger.log("INFO", "Cleaning up orphaned specs", dry_run=dry_run)
        
        try:
            # Use repository cleanup method
            cleanup_result = self.spec_repository.cleanup_repository(dry_run)
            
            return {
                "status": "success",
                "operation": "cleanup_orphaned_specs",
                "dry_run": dry_run,
                "cleanup_result": cleanup_result,
            }
            
        except Exception as e:
            error_msg = f"Orphaned spec cleanup failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecOperationError(error_msg) from e
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of processing capabilities and status.
        
        Returns:
            Dictionary with processing summary
        """
        debug_logger.log("INFO", "Generating processing summary")
        
        try:
            # Get repository status
            repo_status = self.spec_repository.get_status()
            
            # Get change tracking stats
            tracking_stats = self.change_detector.file_tracker.get_tracking_stats()
            
            # Get operation statistics
            operation_stats = self.spec_repository.operation_manager.get_operation_statistics()
            
            summary = {
                "repository_status": repo_status,
                "change_tracking": tracking_stats,
                "operation_statistics": operation_stats,
                "capabilities": {
                    "batch_processing": True,
                    "incremental_updates": True,
                    "conflict_resolution": True,
                    "change_detection": True,
                    "spec_validation": True,
                    "orphan_cleanup": True,
                },
                "supported_operations": [op.value for op in BatchOperationType],
                "conflict_strategies": [strategy.value for strategy in ConflictResolutionStrategy],
            }
            
            debug_logger.log("INFO", "Processing summary generated")
            
            return summary
            
        except Exception as e:
            debug_logger.log("ERROR", "Failed to generate processing summary", error=str(e))
            return {
                "error": str(e),
                "status": "error",
            }
```

## Test Requirements

Create comprehensive tests for the file processing workflows:

### Test Cases (35 tests total)

**FileProcessor Tests:**
1. **test_file_processor_processes_files_for_specs**
2. **test_file_processor_handles_incremental_processing**
3. **test_file_processor_processes_directory_recursively**
4. **test_file_processor_applies_file_filters**
5. **test_file_processor_updates_specs_incrementally**
6. **test_file_processor_validates_all_specs**
7. **test_file_processor_cleans_up_orphaned_specs**
8. **test_file_processor_gets_processing_summary**
9. **test_file_processor_handles_initialization**
10. **test_file_processor_commits_changes_when_requested**

**BatchProcessor Tests:**
11. **test_batch_processor_processes_files_in_parallel**
12. **test_batch_processor_processes_directory_with_filters**
13. **test_batch_processor_handles_different_operation_types**
14. **test_batch_processor_tracks_progress**
15. **test_batch_processor_generates_statistics**
16. **test_batch_processor_handles_processing_errors**
17. **test_batch_processor_respects_max_workers_limit**

**ChangeDetector Tests:**
18. **test_change_detector_detects_file_changes**
19. **test_change_detector_detects_spec_staleness**
20. **test_change_detector_updates_change_tracking**
21. **test_change_detector_handles_cache_operations**
22. **test_change_detector_tracks_new_files**

**ConflictResolver Tests:**
23. **test_conflict_resolver_handles_overwrite_strategy**
24. **test_conflict_resolver_creates_backups**
25. **test_conflict_resolver_merges_manual_edits**
26. **test_conflict_resolver_skips_on_conflicts**
27. **test_conflict_resolver_fails_on_conflicts**
28. **test_conflict_resolver_detects_manual_edits**
29. **test_conflict_resolver_gets_conflict_summary**
30. **test_conflict_resolver_recommends_strategies**

**Integration Tests:**
31. **test_processing_integrates_with_spec_repository**
32. **test_processing_integrates_with_template_system**
33. **test_processing_handles_complex_workflows**
34. **test_processing_coordinates_all_subsystems**
35. **test_processing_handles_error_scenarios**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/processing/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/processing/ --cov=spec_cli.processing --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/processing/

# Check code formatting
poetry run ruff check spec_cli/processing/
poetry run ruff format spec_cli/processing/

# Verify imports work correctly
python -c "from spec_cli.processing import FileProcessor, BatchProcessor, ChangeDetector, ConflictResolver; print('Import successful')"

# Test file processing workflow
python -c "
from spec_cli.processing import FileProcessor
from spec_cli.processing.conflict_resolution import ConflictResolutionStrategy

processor = FileProcessor()

# Get processing summary
summary = processor.get_processing_summary()
print(f'Processing capabilities: {summary[\"capabilities\"]}')
print(f'Supported operations: {summary[\"supported_operations\"]}')
print(f'Repository initialized: {summary[\"repository_status\"][\"initialized\"]}')
"

# Test batch processing capabilities
python -c "
from spec_cli.processing import BatchProcessor, BatchOperationType
from pathlib import Path

batch_processor = BatchProcessor()

# Test with sample files
test_files = [Path('spec_cli/__main__.py'), Path('README.md')]
existing_files = [f for f in test_files if f.exists()]

if existing_files:
    print(f'Testing batch processing with {len(existing_files)} files')
    
    # Note: This would typically process files, but we'll just test the setup
    print('Batch processor initialized successfully')
else:
    print('No test files found, skipping batch processing test')
"

# Test change detection
python -c "
from spec_cli.processing import ChangeDetector
from pathlib import Path

detector = ChangeDetector()

# Get tracking statistics
stats = detector.file_tracker.get_tracking_stats()
print(f'Change tracking stats: {stats}')

# Test change detection on a file
test_file = Path('spec_cli/__main__.py')
if test_file.exists():
    has_changed = detector.file_tracker.has_changed(test_file)
    print(f'File {test_file} has changed: {has_changed}')
else:
    print('Test file not found for change detection')
"

# Test conflict resolution
python -c "
from spec_cli.processing import ConflictResolver
from spec_cli.processing.conflict_resolution import ConflictResolutionStrategy
from pathlib import Path

resolver = ConflictResolver()

# Test conflict strategies
print('Available conflict resolution strategies:')
for strategy in ConflictResolutionStrategy:
    print(f'  {strategy.value}')

# Test conflict summary for a hypothetical spec directory
print(f'Default strategy: {resolver.default_strategy.value}')
"

# Test file processing workflow (dry run)
python -c "
from spec_cli.processing import FileProcessor
from pathlib import Path

processor = FileProcessor()

# Test directory processing (would process if files exist)
test_dir = Path('spec_cli')
if test_dir.exists() and test_dir.is_dir():
    print(f'Would process directory: {test_dir}')
    print('FileProcessor workflow ready for directory processing')
else:
    print('Test directory not found')

# Test validation workflow
try:
    validation_result = processor.validate_all_specs()
    print(f'Spec validation result: {validation_result[\"status\"]}')
    print(f'Specs validated: {validation_result[\"specs_validated\"]}')
except Exception as e:
    print(f'Validation test: {e}')
"
```

## Definition of Done

- [ ] `FileProcessor` class with comprehensive workflow orchestration
- [ ] Batch processing capabilities for parallel file operations
- [ ] Change detection system with file tracking and cache management
- [ ] Conflict resolution with multiple strategies and smart recommendations
- [ ] Integration of all processing subsystems (Git, templates, file system)
- [ ] Progress tracking and reporting for long-running operations
- [ ] Incremental processing based on file changes
- [ ] Comprehensive validation and cleanup operations
- [ ] All 35 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Full integration with spec repository orchestration
- [ ] Advanced error handling and recovery capabilities

## Next Slice Preparation

This slice completes **PHASE-4** (Git and Core Logic) by providing:
- Complete file processing workflows that coordinate all subsystems
- Advanced batch processing and change detection capabilities
- Comprehensive conflict resolution and validation systems
- The final core logic layer that CLI commands will use

This enables **PHASE-5** (Rich UI and CLI) which will use these processing workflows to provide user-friendly command interfaces and rich terminal output.