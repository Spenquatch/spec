# Slice 6: Directory Management and Ignore Patterns

## Goal

Create a comprehensive directory management system that handles spec directory creation, ignore pattern processing, and directory traversal with proper filtering and validation.

## Context

The current monolithic code has directory operations scattered throughout with no unified ignore pattern system. This slice creates a complete directory management system that can create spec directories, process .specignore files, traverse directories with filtering, and manage the .specs/ directory structure. It builds on the path resolution and file analysis systems to provide intelligent directory operations.

## Scope

**Included in this slice:**
- DirectoryManager class for spec directory operations
- IgnorePatternMatcher for .specignore processing 
- Directory traversal with file filtering
- Spec directory structure creation and validation
- Integration with main .gitignore for .spec/ entries

**NOT included in this slice:**
- Conflict resolution for existing files (comes in PHASE-4)
- Template-based directory creation (comes in PHASE-3)
- User interface for directory operations (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for directory operation errors)
- `spec_cli.logging.debug` (debug_logger for operation tracking)
- `spec_cli.config.settings` (SpecSettings for directory paths)
- `spec_cli.file_system.path_resolver` (PathResolver for path handling)
- `spec_cli.file_system.file_analyzer` (FileAnalyzer for file filtering)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration
- `PathResolver` from slice-4-path-resolution
- `FileAnalyzer` from slice-5-file-analysis

## Files to Create

```
spec_cli/file_system/
├── directory_manager.py    # DirectoryManager class
└── ignore_patterns.py      # IgnorePatternMatcher class
```

## Implementation Steps

### Step 1: Create spec_cli/file_system/ignore_patterns.py

```python
import fnmatch
import re
from pathlib import Path
from typing import List, Set, Pattern, Optional
from ..exceptions import SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class IgnorePatternMatcher:
    """Handles .specignore pattern matching and file filtering."""
    
    # Default patterns to always ignore
    DEFAULT_IGNORE_PATTERNS = [
        # Version control
        ".git/",
        ".svn/",
        ".hg/",
        ".bzr/",
        
        # Spec directories (avoid recursion)
        ".spec/",
        ".specs/",
        
        # OS files
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        
        # Editor files
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        ".#*",
        
        # Temporary files
        "*.tmp",
        "*.temp",
        "*.log",
        
        # Build artifacts
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        ".pytest_cache/",
        ".coverage",
        "coverage/",
        "build/",
        "dist/",
        "target/",
        "bin/",
        "obj/",
        
        # Package files
        "*.egg-info/",
        ".tox/",
        ".nox/",
        ".cache/",
        
        # Large media files
        "*.mp4",
        "*.avi",
        "*.mov",
        "*.mkv",
        "*.mp3",
        "*.wav",
        "*.flac",
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.ico",
        "*.pdf",
        "*.zip",
        "*.tar.gz",
        "*.tar.bz2",
        "*.rar",
        "*.7z",
    ]
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.ignore_patterns: List[str] = []
        self.compiled_patterns: List[Pattern] = []
        self._load_ignore_patterns()
        
        debug_logger.log("INFO", "IgnorePatternMatcher initialized", 
                        pattern_count=len(self.ignore_patterns))
    
    def _load_ignore_patterns(self) -> None:
        """Load ignore patterns from .specignore file and defaults."""
        # Start with default patterns
        patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        
        # Load from .specignore file if it exists
        specignore_file = self.settings.ignore_file
        if specignore_file.exists():
            try:
                with specignore_file.open('r', encoding='utf-8') as f:
                    file_patterns = [
                        line.strip() 
                        for line in f 
                        if line.strip() and not line.startswith('#')
                    ]
                patterns.extend(file_patterns)
                debug_logger.log("INFO", "Loaded patterns from .specignore", 
                               file=str(specignore_file), 
                               patterns_loaded=len(file_patterns))
            except Exception as e:
                debug_logger.log("WARNING", "Could not read .specignore file", 
                               file=str(specignore_file), error=str(e))
        
        self.ignore_patterns = patterns
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile ignore patterns for efficient matching."""
        self.compiled_patterns = []
        
        for pattern in self.ignore_patterns:
            try:
                # Convert glob pattern to regex
                if pattern.endswith('/'):
                    # Directory pattern
                    regex_pattern = fnmatch.translate(pattern.rstrip('/'))
                    # Also match anything inside the directory
                    regex_pattern = regex_pattern.rstrip('\\Z') + r'(/.*)?\\Z'
                else:
                    # File pattern
                    regex_pattern = fnmatch.translate(pattern)
                
                compiled = re.compile(regex_pattern, re.IGNORECASE)
                self.compiled_patterns.append(compiled)
                
                debug_logger.log("DEBUG", "Compiled pattern", 
                               pattern=pattern, regex=regex_pattern)
                
            except re.error as e:
                debug_logger.log("WARNING", "Invalid ignore pattern", 
                               pattern=pattern, error=str(e))
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored based on patterns.
        
        Args:
            file_path: Path to check (relative to project root)
            
        Returns:
            True if file should be ignored
        """
        # Convert to string with forward slashes for consistent matching
        path_str = str(file_path).replace('\\', '/')
        
        # Check against all compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.match(path_str):
                debug_logger.log("DEBUG", "File matched ignore pattern", 
                               file=path_str, pattern=pattern.pattern)
                return True
        
        debug_logger.log("DEBUG", "File not ignored", file=path_str)
        return False
    
    def filter_paths(self, paths: List[Path]) -> List[Path]:
        """Filter a list of paths, removing ignored ones.
        
        Args:
            paths: List of paths to filter
            
        Returns:
            List of paths that should not be ignored
        """
        debug_logger.log("INFO", "Filtering paths", input_count=len(paths))
        
        filtered = [path for path in paths if not self.should_ignore(path)]
        
        debug_logger.log("INFO", "Path filtering complete", 
                        input_count=len(paths), 
                        output_count=len(filtered),
                        ignored_count=len(paths) - len(filtered))
        
        return filtered
    
    def add_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern.
        
        Args:
            pattern: Ignore pattern to add
        """
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            self._compile_patterns()
            debug_logger.log("INFO", "Added ignore pattern", pattern=pattern)
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove an ignore pattern.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if pattern was found and removed
        """
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
            self._compile_patterns()
            debug_logger.log("INFO", "Removed ignore pattern", pattern=pattern)
            return True
        return False
    
    def get_patterns(self) -> List[str]:
        """Get current ignore patterns."""
        return self.ignore_patterns.copy()
    
    def save_patterns_to_file(self, additional_patterns: List[str] = None) -> None:
        """Save patterns to .specignore file.
        
        Args:
            additional_patterns: Additional patterns to save
        """
        patterns_to_save = []
        
        # Add custom patterns (skip defaults)
        custom_patterns = [
            p for p in self.ignore_patterns 
            if p not in self.DEFAULT_IGNORE_PATTERNS
        ]
        patterns_to_save.extend(custom_patterns)
        
        # Add any additional patterns
        if additional_patterns:
            patterns_to_save.extend(additional_patterns)
        
        if patterns_to_save:
            try:
                with self.settings.ignore_file.open('w', encoding='utf-8') as f:
                    f.write("# Spec ignore patterns\n")
                    f.write("# This file specifies files and directories to ignore during spec generation\n\n")
                    for pattern in patterns_to_save:
                        f.write(f"{pattern}\n")
                
                debug_logger.log("INFO", "Saved patterns to .specignore", 
                               file=str(self.settings.ignore_file),
                               pattern_count=len(patterns_to_save))
            except Exception as e:
                raise SpecFileError(f"Could not save .specignore file: {e}") from e
```

### Step 2: Create spec_cli/file_system/directory_manager.py

```python
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from ..exceptions import SpecFileError, SpecPermissionError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from .path_resolver import PathResolver
from .file_analyzer import FileAnalyzer
from .ignore_patterns import IgnorePatternMatcher

class DirectoryManager:
    """Manages spec directory operations and directory traversal."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.path_resolver = PathResolver(self.settings)
        self.file_analyzer = FileAnalyzer(self.settings)
        self.ignore_matcher = IgnorePatternMatcher(self.settings)
        
        debug_logger.log("INFO", "DirectoryManager initialized")
    
    def ensure_specs_directory(self) -> None:
        """Ensure .specs directory exists with proper structure.
        
        Raises:
            SpecPermissionError: If directory cannot be created
        """
        debug_logger.log("INFO", "Ensuring .specs directory exists")
        
        try:
            if not self.settings.specs_dir.exists():
                self.settings.specs_dir.mkdir(parents=True, exist_ok=True)
                debug_logger.log("INFO", "Created .specs directory", 
                               path=str(self.settings.specs_dir))
            
            # Verify directory is writable
            if not os.access(self.settings.specs_dir, os.W_OK):
                raise SpecPermissionError(f"No write permission for {self.settings.specs_dir}")
            
            debug_logger.log("INFO", ".specs directory ready", 
                           path=str(self.settings.specs_dir))
            
        except OSError as e:
            raise SpecPermissionError(f"Could not create .specs directory: {e}") from e
    
    def create_spec_directory(self, file_path: Path) -> Path:
        """Create spec directory for a given file path.
        
        Args:
            file_path: Path to source file (relative to project root)
            
        Returns:
            Path to created spec directory
            
        Raises:
            SpecFileError: If directory cannot be created
        """
        spec_dir = self.path_resolver.convert_to_spec_directory_path(file_path)
        
        debug_logger.log("INFO", "Creating spec directory", 
                        source_file=str(file_path), 
                        spec_dir=str(spec_dir))
        
        try:
            spec_dir.mkdir(parents=True, exist_ok=True)
            debug_logger.log("INFO", "Spec directory created", path=str(spec_dir))
            return spec_dir
            
        except OSError as e:
            raise SpecFileError(f"Could not create spec directory {spec_dir}: {e}") from e
    
    def check_existing_specs(self, spec_dir: Path) -> Dict[str, bool]:
        """Check for existing spec files in directory.
        
        Args:
            spec_dir: Path to spec directory to check
            
        Returns:
            Dictionary with existence status of index.md and history.md
        """
        index_file = spec_dir / "index.md"
        history_file = spec_dir / "history.md"
        
        existing = {
            "index.md": index_file.exists(),
            "history.md": history_file.exists(),
        }
        
        debug_logger.log("INFO", "Checked existing spec files", 
                        spec_dir=str(spec_dir),
                        index_exists=existing["index.md"],
                        history_exists=existing["history.md"])
        
        return existing
    
    def backup_existing_specs(self, spec_dir: Path) -> Optional[Path]:
        """Create backup of existing spec files.
        
        Args:
            spec_dir: Directory containing spec files
            
        Returns:
            Path to backup directory, or None if no backup needed
        """
        existing = self.check_existing_specs(spec_dir)
        
        if not any(existing.values()):
            debug_logger.log("INFO", "No existing spec files to backup", 
                           spec_dir=str(spec_dir))
            return None
        
        # Create backup directory with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = spec_dir / f"backup_{timestamp}"
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, exists in existing.items():
                if exists:
                    source_file = spec_dir / filename
                    backup_file = backup_dir / filename
                    shutil.copy2(source_file, backup_file)
                    debug_logger.log("INFO", "Backed up spec file", 
                                   source=str(source_file), 
                                   backup=str(backup_file))
            
            debug_logger.log("INFO", "Spec files backed up", 
                           backup_dir=str(backup_dir))
            return backup_dir
            
        except OSError as e:
            debug_logger.log("WARNING", "Could not create backup", 
                           spec_dir=str(spec_dir), error=str(e))
            return None
    
    def find_source_files(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Find all processable source files in a directory.
        
        Args:
            directory: Directory to search
            recursive: Whether to search recursively
            
        Returns:
            List of source file paths relative to project root
            
        Raises:
            SpecFileError: If directory traversal fails
        """
        debug_logger.log("INFO", "Finding source files", 
                        directory=str(directory), recursive=recursive)
        
        source_files = []
        
        try:
            if recursive:
                # Use rglob for recursive search
                pattern = "**/*"
                files = directory.rglob("*")
            else:
                # Use glob for single directory
                files = directory.glob("*")
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Convert to relative path from project root
                try:
                    relative_path = file_path.relative_to(self.settings.root_path)
                except ValueError:
                    # File is outside project root, skip
                    continue
                
                # Apply ignore patterns
                if self.ignore_matcher.should_ignore(relative_path):
                    debug_logger.log("DEBUG", "File ignored by patterns", 
                                   file=str(relative_path))
                    continue
                
                # Check if file is processable
                if self.file_analyzer.is_processable_file(relative_path):
                    source_files.append(relative_path)
                    debug_logger.log("DEBUG", "Found processable file", 
                                   file=str(relative_path))
                else:
                    debug_logger.log("DEBUG", "File not processable", 
                                   file=str(relative_path))
            
            debug_logger.log("INFO", "Source file discovery complete", 
                           directory=str(directory),
                           files_found=len(source_files))
            
            return sorted(source_files)
            
        except OSError as e:
            raise SpecFileError(f"Failed to traverse directory {directory}: {e}") from e
    
    def get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics about a directory's contents.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dictionary with directory statistics
        """
        debug_logger.log("INFO", "Analyzing directory statistics", 
                        directory=str(directory))
        
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "processable_files": 0,
            "ignored_files": 0,
            "binary_files": 0,
            "total_size": 0,
            "file_types": {},
            "largest_files": [],
        }
        
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    stats["total_files"] += 1
                    
                    try:
                        relative_path = item.relative_to(self.settings.root_path)
                        
                        # Check file size
                        file_size = item.stat().st_size
                        stats["total_size"] += file_size
                        
                        # Track largest files (top 10)
                        stats["largest_files"].append((str(relative_path), file_size))
                        stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
                        stats["largest_files"] = stats["largest_files"][:10]
                        
                        # Check ignore status
                        if self.ignore_matcher.should_ignore(relative_path):
                            stats["ignored_files"] += 1
                            continue
                        
                        # Analyze file type
                        file_type = self.file_analyzer.get_file_type(relative_path)
                        stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
                        
                        # Check if processable
                        if self.file_analyzer.is_processable_file(relative_path):
                            stats["processable_files"] += 1
                        
                        # Check if binary
                        if self.file_analyzer.is_binary_file(relative_path):
                            stats["binary_files"] += 1
                            
                    except (ValueError, OSError):
                        # Skip files that can't be processed
                        continue
                        
                elif item.is_dir():
                    stats["total_directories"] += 1
            
            # Calculate percentages
            if stats["total_files"] > 0:
                stats["processable_percentage"] = round(
                    (stats["processable_files"] / stats["total_files"]) * 100, 1
                )
                stats["ignored_percentage"] = round(
                    (stats["ignored_files"] / stats["total_files"]) * 100, 1
                )
            
            # Format total size
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            
            debug_logger.log("INFO", "Directory analysis complete", 
                           directory=str(directory),
                           total_files=stats["total_files"],
                           processable=stats["processable_files"])
            
            return stats
            
        except OSError as e:
            raise SpecFileError(f"Failed to analyze directory {directory}: {e}") from e
    
    def setup_ignore_files(self) -> None:
        """Set up ignore files with default patterns."""
        debug_logger.log("INFO", "Setting up ignore files")
        
        # Create .specignore if it doesn't exist
        if not self.settings.ignore_file.exists():
            try:
                default_patterns = [
                    "*.log",
                    "*.tmp", 
                    "node_modules/",
                    "__pycache__/",
                    ".pytest_cache/",
                ]
                self.ignore_matcher.save_patterns_to_file(default_patterns)
                debug_logger.log("INFO", "Created default .specignore file")
            except Exception as e:
                debug_logger.log("WARNING", "Could not create .specignore file", 
                               error=str(e))
    
    def update_main_gitignore(self) -> None:
        """Update main .gitignore to exclude spec directories."""
        debug_logger.log("INFO", "Updating main .gitignore")
        
        gitignore_file = self.settings.gitignore_file
        spec_entries = [".spec/", ".spec-index"]
        
        try:
            # Read existing .gitignore
            existing_lines = []
            if gitignore_file.exists():
                with gitignore_file.open('r', encoding='utf-8') as f:
                    existing_lines = [line.rstrip() for line in f]
            
            # Check if spec entries already exist
            needs_update = False
            for entry in spec_entries:
                if entry not in existing_lines:
                    existing_lines.append(entry)
                    needs_update = True
            
            # Write back if updated
            if needs_update:
                with gitignore_file.open('w', encoding='utf-8') as f:
                    for line in existing_lines:
                        f.write(f"{line}\n")
                
                debug_logger.log("INFO", "Updated .gitignore with spec entries")
            else:
                debug_logger.log("INFO", ".gitignore already contains spec entries")
                
        except Exception as e:
            debug_logger.log("WARNING", "Could not update .gitignore", 
                           error=str(e))
```

### Step 3: Update spec_cli/file_system/__init__.py

```python
"""File system operations for spec CLI.

This package provides abstractions for file system operations including
path resolution, file analysis, and directory management.
"""

from .path_resolver import PathResolver
from .file_analyzer import FileAnalyzer
from .metadata import FileMetadataExtractor, get_file_age_days, is_recent_file, format_file_size
from .directory_manager import DirectoryManager
from .ignore_patterns import IgnorePatternMatcher

__all__ = [
    "PathResolver",
    "FileAnalyzer", 
    "FileMetadataExtractor",
    "DirectoryManager",
    "IgnorePatternMatcher",
    "get_file_age_days",
    "is_recent_file", 
    "format_file_size",
]
```

## Test Requirements

Create comprehensive tests for the directory management system:

### Test Cases (25 tests total)

**IgnorePatternMatcher Tests:**
1. **test_ignore_patterns_loads_default_patterns**
2. **test_ignore_patterns_loads_from_specignore_file**
3. **test_ignore_patterns_matches_file_patterns**
4. **test_ignore_patterns_matches_directory_patterns**
5. **test_ignore_patterns_supports_glob_patterns**
6. **test_ignore_patterns_handles_case_insensitive_matching**
7. **test_ignore_patterns_filters_path_lists**
8. **test_ignore_patterns_adds_and_removes_patterns**
9. **test_ignore_patterns_saves_to_file**
10. **test_ignore_patterns_handles_malformed_patterns**

**DirectoryManager Tests:**
11. **test_directory_manager_ensures_specs_directory**
12. **test_directory_manager_creates_spec_directories**
13. **test_directory_manager_checks_existing_specs**
14. **test_directory_manager_backs_up_existing_specs**
15. **test_directory_manager_finds_source_files_recursive**
16. **test_directory_manager_finds_source_files_non_recursive**
17. **test_directory_manager_applies_ignore_patterns**
18. **test_directory_manager_filters_processable_files**
19. **test_directory_manager_calculates_directory_stats**
20. **test_directory_manager_handles_permission_errors**
21. **test_directory_manager_sets_up_ignore_files**
22. **test_directory_manager_updates_main_gitignore**

**Integration Tests:**
23. **test_directory_operations_integrate_with_file_analyzer**
24. **test_ignore_patterns_integrate_with_path_resolver**
25. **test_directory_management_handles_complex_structures**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_system/test_directory_manager.py tests/unit/file_system/test_ignore_patterns.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_system/test_directory_manager.py tests/unit/file_system/test_ignore_patterns.py --cov=spec_cli.file_system.directory_manager --cov=spec_cli.file_system.ignore_patterns --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_system/directory_manager.py spec_cli/file_system/ignore_patterns.py

# Check code formatting  
poetry run ruff check spec_cli/file_system/directory_manager.py spec_cli/file_system/ignore_patterns.py
poetry run ruff format spec_cli/file_system/directory_manager.py spec_cli/file_system/ignore_patterns.py

# Verify imports work correctly
python -c "from spec_cli.file_system import DirectoryManager, IgnorePatternMatcher; print('Import successful')"

# Test ignore pattern functionality
python -c "
from spec_cli.file_system import IgnorePatternMatcher
from pathlib import Path
matcher = IgnorePatternMatcher()
test_paths = [
    Path('src/main.py'),
    Path('node_modules/package.json'),
    Path('.git/config'),
    Path('README.md'),
    Path('__pycache__/cache.pyc')
]
for path in test_paths:
    ignored = matcher.should_ignore(path)
    print(f'{path}: {\"IGNORED\" if ignored else \"INCLUDED\"}')
"

# Test directory management functionality
python -c "
from spec_cli.file_system import DirectoryManager
from pathlib import Path
manager = DirectoryManager()
# Test current directory analysis
current_dir = Path('.')
try:
    stats = manager.get_directory_stats(current_dir)
    print(f'Directory stats:')
    print(f'  Total files: {stats[\"total_files\"]}')
    print(f'  Processable: {stats[\"processable_files\"]}')
    print(f'  Ignored: {stats[\"ignored_files\"]}')
    print(f'  File types: {list(stats[\"file_types\"].keys())[:5]}...')
except Exception as e:
    print(f'Error analyzing directory: {e}')
"

# Test spec directory creation
python -c "
from spec_cli.file_system import DirectoryManager
from pathlib import Path
manager = DirectoryManager()
test_file = Path('test/example.py')
try:
    spec_dir = manager.create_spec_directory(test_file)
    print(f'Would create spec directory: {spec_dir}')
    existing = manager.check_existing_specs(spec_dir)
    print(f'Existing specs: {existing}')
except Exception as e:
    print(f'Directory operation test: {e}')
"
```

## Definition of Done

- [ ] `IgnorePatternMatcher` class with comprehensive pattern support
- [ ] Default ignore patterns for common development artifacts
- [ ] .specignore file loading and processing
- [ ] `DirectoryManager` class for spec directory operations
- [ ] Spec directory creation with proper structure
- [ ] Directory traversal with filtering and ignore patterns
- [ ] Backup system for existing spec files
- [ ] Directory statistics and analysis capabilities
- [ ] Integration with .gitignore for spec directories
- [ ] All 25 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with path resolver and file analyzer
- [ ] Comprehensive ignore pattern matching (glob, regex, directories)

## Next Slice Preparation

This slice completes **PHASE-2** (File System Operations) by providing:
- `DirectoryManager` for all directory operations needed by core services
- `IgnorePatternMatcher` for filtering files during processing
- Complete file system abstraction layer

This enables **PHASE-3** (Template System) which will use the directory management system to create spec directories and handle template file operations.