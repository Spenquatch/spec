# Slice 5B: File Metadata and Utilities

## Goal

Create file metadata extraction capabilities, directory composition helpers, and file utility functions that build upon the file type detection from slice-5a.

## Context

This slice builds on slice-5a (File Type Detection) to add comprehensive metadata extraction and file utility functions. It focuses on gathering detailed information about files and providing helpful utilities for directory analysis and file composition. This enables more sophisticated file processing decisions in later phases.

## Scope

**Included in this slice:**
- FileMetadataExtractor class for detailed file information
- Directory composition analysis utilities  
- File utility functions for size formatting, permission checking
- Integration with FileTypeDetector from slice-5a

**NOT included in this slice:**
- Directory traversal logic (comes in slice-6b)
- Ignore pattern matching (comes in slice-6a)
- File content analysis (focus is on file-level metadata)
- File modification or creation operations

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for file operation errors)
- `spec_cli.logging.debug` (debug_logger for file analysis operations)
- `spec_cli.config.settings` (Settings for configuration)
- `spec_cli.file_system.path_resolver` (PathResolver from slice-4)
- `spec_cli.file_system.file_type_detector` (FileTypeDetector from slice-5a)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` from slice-3a-settings-console
- `PathResolver` from slice-4-path-resolution
- `FileTypeDetector` from slice-5a-file-type-detection

## Files to Create

```
spec_cli/file_system/
├── file_metadata.py        # FileMetadataExtractor class
└── file_utils.py           # File utility functions and helpers
```

## Implementation Steps

### Step 1: Create spec_cli/file_system/file_metadata.py

```python
import stat
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..exceptions import SpecFileError
from ..logging.debug import debug_logger
from .file_type_detector import FileTypeDetector

class FileMetadataExtractor:
    """Extracts comprehensive metadata from files for analysis and reporting."""
    
    def __init__(self):
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
                "is_hidden": file_path.name.startswith('.'),
                "is_empty": stat_info.st_size == 0,
                "line_count": None,  # Will be populated if text file
            }
            
            # Add line count for text files (if reasonable size)
            if (not metadata["is_binary"] and 
                metadata["is_processable"] and 
                stat_info.st_size < 1_048_576):  # 1MB limit
                try:
                    metadata["line_count"] = self._count_lines(file_path)
                except Exception as e:
                    debug_logger.log("WARNING", "Could not count lines", 
                                   file_path=str(file_path), error=str(e))
            
            debug_logger.log("DEBUG", "Extracted file metadata", 
                           file_path=str(file_path),
                           file_type=metadata["file_type"],
                           size_bytes=metadata["size_bytes"])
            
            return metadata
            
        except OSError as e:
            raise SpecFileError(
                f"Cannot access file metadata for {file_path}: {e}",
                {"file_path": str(file_path), "os_error": str(e)}
            ) from e
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a text file."""
        try:
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with file_path.open('r', encoding='latin-1') as f:
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
        
        composition = {
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
                        composition["file_types"][file_type] = composition["file_types"].get(file_type, 0) + 1
                        
                        # Track file categories
                        category = metadata["file_category"]
                        if category:
                            composition["file_categories"][category] = composition["file_categories"].get(category, 0) + 1
                        
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
                                "size": metadata["size_formatted"]
                            }
                        
                        # Track newest file
                        if metadata["modified_time"] > newest_time:
                            newest_time = metadata["modified_time"]
                            composition["newest_file"] = {
                                "path": metadata["path"],
                                "modified": metadata["modified_datetime"].isoformat()
                            }
                            
                    except SpecFileError as e:
                        debug_logger.log("WARNING", "Could not analyze file in directory", 
                                       file_path=str(item), error=str(e))
                        continue
            
            # Add formatted total size
            composition["total_size_formatted"] = self._format_file_size(composition["total_size"])
            
            debug_logger.log("INFO", "Directory composition analyzed", 
                           directory=str(directory_path),
                           total_files=composition["total_files"],
                           processable_files=composition["processable_files"])
            
            return composition
            
        except OSError as e:
            raise SpecFileError(
                f"Cannot analyze directory composition for {directory_path}: {e}",
                {"directory_path": str(directory_path), "os_error": str(e)}
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
                "newer_file": file1 if meta1["modified_time"] > meta2["modified_time"] else file2,
                "larger_file": file1 if meta1["size_bytes"] > meta2["size_bytes"] else file2,
                "both_processable": meta1["is_processable"] and meta2["is_processable"],
            }
            
            return comparison
            
        except Exception as e:
            raise SpecFileError(f"Cannot compare files: {e}") from e
```

### Step 2: Create spec_cli/file_system/file_utils.py

```python
import os
from pathlib import Path
from typing import List, Optional, Set, Iterator
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
        debug_logger.log("WARNING", "Path is not a regular file", file_path=str(file_path))
        return False
    
    if not os.access(file_path, os.R_OK):
        debug_logger.log("WARNING", "File is not readable", file_path=str(file_path))
        return False
    
    return True

def get_file_extension_stats(files: List[Path]) -> dict:
    """Get statistics about file extensions in a list of files.
    
    Args:
        files: List of file paths to analyze
        
    Returns:
        Dictionary with extension statistics
    """
    extension_stats = {}
    
    for file_path in files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if not ext:
                ext = "no_extension"
            extension_stats[ext] = extension_stats.get(ext, 0) + 1
    
    debug_logger.log("DEBUG", "File extension statistics", 
                    unique_extensions=len(extension_stats),
                    total_files=len(files))
    
    return extension_stats

def find_largest_files(directory: Path, limit: int = 10) -> List[dict]:
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
                    files_with_size.append({
                        "path": file_path,
                        "size": size,
                        "size_formatted": format_file_size(size)
                    })
                except OSError:
                    continue
        
        # Sort by size (largest first) and return top N
        files_with_size.sort(key=lambda x: x["size"], reverse=True)
        return files_with_size[:limit]
        
    except OSError as e:
        raise SpecFileError(f"Cannot search directory {directory}: {e}") from e

def find_recently_modified_files(directory: Path, limit: int = 10) -> List[dict]:
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
                    files_with_time.append({
                        "path": file_path,
                        "modified_time": mtime,
                        "modified_formatted": format_timestamp(mtime)
                    })
                except OSError:
                    continue
        
        # Sort by modification time (newest first) and return top N
        files_with_time.sort(key=lambda x: x["modified_time"], reverse=True)
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
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_timestamp(timestamp: float) -> str:
    """Format Unix timestamp in human-readable format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string
    """
    from datetime import datetime
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
    
    operation_map = {
        'read': os.R_OK,
        'write': os.W_OK, 
        'execute': os.X_OK
    }
    
    if operation not in operation_map:
        debug_logger.log("ERROR", "Unknown file operation", operation=operation)
        return False
    
    try:
        return os.access(file_path, operation_map[operation])
    except OSError as e:
        debug_logger.log("ERROR", "File operation check failed", 
                        file_path=str(file_path), 
                        operation=operation,
                        error=str(e))
        return False

def get_unique_extensions(files: List[Path]) -> Set[str]:
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

def filter_files_by_size(files: List[Path], min_size: int = 0, max_size: Optional[int] = None) -> List[Path]:
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
    
    debug_logger.log("DEBUG", "Filtered files by size",
                    original_count=len(files),
                    filtered_count=len(filtered),
                    min_size=min_size,
                    max_size=max_size)
    
    return filtered
```

## Test Requirements

Create comprehensive tests for metadata extraction and utilities:

### Test Cases (15 tests total)

**Metadata Extraction Tests:**
1. **test_file_metadata_extracts_basic_information**
2. **test_file_metadata_handles_binary_files**
3. **test_file_metadata_counts_lines_for_text_files**
4. **test_file_metadata_handles_permission_errors**
5. **test_file_metadata_formats_sizes_correctly**
6. **test_directory_composition_analyzes_mixed_files**
7. **test_directory_composition_handles_empty_directory**
8. **test_file_comparison_identifies_differences**

**File Utilities Tests:**
9. **test_ensure_file_readable_validates_accessibility**
10. **test_file_extension_stats_counts_correctly**
11. **test_largest_files_finder_sorts_by_size**
12. **test_recently_modified_finder_sorts_by_time**
13. **test_safe_file_operation_checks_permissions**
14. **test_file_filtering_by_size_works_correctly**
15. **test_utility_functions_handle_edge_cases**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_system/test_file_metadata.py tests/unit/file_system/test_file_utils.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_system/test_file_metadata.py tests/unit/file_system/test_file_utils.py --cov=spec_cli.file_system.file_metadata --cov=spec_cli.file_system.file_utils --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_system/file_metadata.py spec_cli/file_system/file_utils.py

# Check code formatting
poetry run ruff check spec_cli/file_system/file_metadata.py spec_cli/file_system/file_utils.py
poetry run ruff format spec_cli/file_system/file_metadata.py spec_cli/file_system/file_utils.py

# Verify imports work correctly
python -c "from spec_cli.file_system.file_metadata import FileMetadataExtractor; from spec_cli.file_system.file_utils import format_file_size; print('Import successful')"

# Test metadata extraction
python -c "
from spec_cli.file_system.file_metadata import FileMetadataExtractor
from pathlib import Path
extractor = FileMetadataExtractor()
metadata = extractor.get_file_metadata(Path('pyproject.toml'))
print(f'File type: {metadata[\"file_type\"]}')
print(f'Size: {metadata[\"size_formatted\"]}')
print(f'Processable: {metadata[\"is_processable\"]}')
"
```

## Definition of Done

- [ ] FileMetadataExtractor class implemented with comprehensive file analysis
- [ ] Directory composition analysis with statistics and summaries
- [ ] File utility functions for common file operations
- [ ] Integration with FileTypeDetector from slice-5a
- [ ] Proper error handling for all file access operations
- [ ] All 15 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Debug logging for all metadata operations
- [ ] Helpful utility functions for file filtering and analysis
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-6a and slice-6b by providing:
- File metadata that ignore pattern logic can use for decisions
- Directory composition tools that directory operations can leverage
- File utility functions that directory traversal can build upon
- Comprehensive file analysis that directory management can integrate