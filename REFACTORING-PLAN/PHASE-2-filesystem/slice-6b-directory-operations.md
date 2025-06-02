# Slice 6B: Directory Operations and Management

## Goal

Create comprehensive directory management system that handles .specs/ directory creation, backup logic, and directory traversal using ignore patterns from slice-6a and file utilities from slice-5b.

## Context

This slice builds on slice-6a (Ignore Patterns) and integrates with slice-5a/5b (File Analysis) to provide complete directory management capabilities. It focuses on directory operations, spec directory creation, backup logic, and intelligent directory traversal that respects ignore patterns and file analysis results.

## Scope

**Included in this slice:**
- DirectoryManager class for spec directory operations
- Directory traversal with ignore pattern integration
- Backup and safety operations for existing files
- .specs/ directory structure management
- Integration with IgnorePatternMatcher and file analysis systems

**NOT included in this slice:**
- Pattern matching logic (handled in slice-6a)
- File metadata extraction (handled in slice-5b)
- File type detection (handled in slice-5a)
- Git operations (comes in PHASE-4)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for directory errors)
- `spec_cli.logging.debug` (debug_logger for directory operations)
- `spec_cli.config.settings` (Settings for directory paths)
- `spec_cli.file_system.path_resolver` (PathResolver from slice-4)
- `spec_cli.file_system.file_type_detector` (FileTypeDetector from slice-5a)
- `spec_cli.file_system.file_metadata` (FileMetadataExtractor from slice-5b)
- `spec_cli.file_system.ignore_patterns` (IgnorePatternMatcher from slice-6a)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` from slice-3a-settings-console
- `PathResolver` from slice-4-path-resolution
- `FileTypeDetector` from slice-5a-file-type-detection
- `FileMetadataExtractor` from slice-5b-file-metadata
- `IgnorePatternMatcher` from slice-6a-ignore-patterns

## Files to Create

```
spec_cli/file_system/
├── directory_manager.py    # DirectoryManager class
└── directory_traversal.py  # Directory traversal utilities
```

## Implementation Steps

### Step 1: Create spec_cli/file_system/directory_manager.py

```python
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..exceptions import SpecFileError, SpecPermissionError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger
from .path_resolver import PathResolver
from .ignore_patterns import IgnorePatternMatcher

class DirectoryManager:
    """Manages spec directory creation, structure, and safety operations."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.path_resolver = PathResolver(self.settings)
        self.ignore_matcher = IgnorePatternMatcher(self.settings)
    
    def ensure_specs_directory(self) -> None:
        """Ensure .specs directory exists and is properly configured."""
        specs_dir = self.settings.specs_dir
        
        debug_logger.log("INFO", "Ensuring .specs directory exists", 
                        specs_dir=str(specs_dir))
        
        try:
            if not specs_dir.exists():
                specs_dir.mkdir(parents=True, exist_ok=True)
                debug_logger.log("INFO", "Created .specs directory", 
                               specs_dir=str(specs_dir))
            
            # Verify write permissions
            if not os.access(specs_dir, os.W_OK):
                raise SpecPermissionError(
                    f"No write permission for .specs directory: {specs_dir}",
                    {"directory": str(specs_dir), "permission": "write"}
                )
            
            # Create basic structure
            self._create_basic_structure(specs_dir)
            
        except OSError as e:
            raise SpecFileError(
                f"Failed to create .specs directory: {e}",
                {"specs_dir": str(specs_dir), "os_error": str(e)}
            ) from e
    
    def _create_basic_structure(self, specs_dir: Path) -> None:
        """Create basic directory structure in .specs."""
        # Create .specignore if it doesn't exist in .specs
        specignore_in_specs = specs_dir / ".specignore"
        if not specignore_in_specs.exists():
            default_content = """# Spec-specific ignores
*.tmp
*.backup
.DS_Store
"""
            try:
                specignore_in_specs.write_text(default_content, encoding='utf-8')
                debug_logger.log("INFO", "Created default .specignore in .specs", 
                               file_path=str(specignore_in_specs))
            except OSError as e:
                debug_logger.log("WARNING", "Could not create .specignore in .specs", 
                               error=str(e))
    
    def create_spec_directory(self, file_path: Path) -> Path:
        """Create directory structure for a file's spec documentation.
        
        Args:
            file_path: Path to the source file (relative to project root)
            
        Returns:
            Path to the created spec directory
        """
        # Resolve to spec directory path
        spec_dir = self.path_resolver.resolve_spec_directory_path(file_path)
        
        debug_logger.log("INFO", "Creating spec directory", 
                        file_path=str(file_path),
                        spec_dir=str(spec_dir))
        
        try:
            # Ensure parent directories exist
            spec_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify the directory was created and is writable
            if not spec_dir.exists() or not spec_dir.is_dir():
                raise SpecFileError(f"Failed to create spec directory: {spec_dir}")
            
            if not os.access(spec_dir, os.W_OK):
                raise SpecPermissionError(
                    f"No write permission for spec directory: {spec_dir}",
                    {"directory": str(spec_dir), "permission": "write"}
                )
            
            debug_logger.log("INFO", "Successfully created spec directory", 
                           spec_dir=str(spec_dir))
            
            return spec_dir
            
        except OSError as e:
            raise SpecFileError(
                f"Failed to create spec directory {spec_dir}: {e}",
                {"spec_dir": str(spec_dir), "file_path": str(file_path), "os_error": str(e)}
            ) from e
    
    def check_existing_specs(self, spec_dir: Path) -> Dict[str, bool]:
        """Check which spec files already exist in the directory.
        
        Args:
            spec_dir: Directory to check
            
        Returns:
            Dictionary indicating which files exist
        """
        index_file = spec_dir / "index.md"
        history_file = spec_dir / "history.md"
        
        existing = {
            "index.md": index_file.exists(),
            "history.md": history_file.exists(),
            "directory": spec_dir.exists()
        }
        
        debug_logger.log("DEBUG", "Checked existing spec files", 
                        spec_dir=str(spec_dir),
                        existing=existing)
        
        return existing
    
    def backup_existing_files(self, spec_dir: Path, backup_suffix: Optional[str] = None) -> List[Path]:
        """Create backups of existing spec files.
        
        Args:
            spec_dir: Directory containing files to backup
            backup_suffix: Suffix for backup files (default: timestamp)
            
        Returns:
            List of created backup file paths
        """
        if backup_suffix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_suffix = f".backup_{timestamp}"
        
        backup_files = []
        
        if not spec_dir.exists():
            return backup_files
        
        try:
            for file_path in spec_dir.glob("*.md"):
                backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
                shutil.copy2(file_path, backup_path)
                backup_files.append(backup_path)
                
                debug_logger.log("INFO", "Created backup file", 
                               original=str(file_path),
                               backup=str(backup_path))
            
            return backup_files
            
        except OSError as e:
            raise SpecFileError(
                f"Failed to create backup files in {spec_dir}: {e}",
                {"spec_dir": str(spec_dir), "os_error": str(e)}
            ) from e
    
    def remove_spec_directory(self, spec_dir: Path, backup_first: bool = True) -> Optional[List[Path]]:
        """Remove a spec directory and optionally create backups.
        
        Args:
            spec_dir: Directory to remove
            backup_first: Whether to create backups before removal
            
        Returns:
            List of backup files if backup_first is True, None otherwise
        """
        backup_files = None
        
        if not spec_dir.exists():
            debug_logger.log("INFO", "Spec directory does not exist, nothing to remove", 
                           spec_dir=str(spec_dir))
            return backup_files
        
        try:
            if backup_first:
                backup_files = self.backup_existing_files(spec_dir)
            
            shutil.rmtree(spec_dir)
            
            debug_logger.log("INFO", "Removed spec directory", 
                           spec_dir=str(spec_dir),
                           backup_created=backup_first)
            
            return backup_files
            
        except OSError as e:
            raise SpecFileError(
                f"Failed to remove spec directory {spec_dir}: {e}",
                {"spec_dir": str(spec_dir), "os_error": str(e)}
            ) from e
    
    def setup_ignore_files(self) -> None:
        """Setup ignore files for the project."""
        # Ensure .specignore exists with sensible defaults
        ignore_file = self.settings.ignore_file
        
        if not ignore_file.exists():
            default_patterns = """# Generated files
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Testing and coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Documentation builds
docs/_build/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
            try:
                ignore_file.write_text(default_patterns, encoding='utf-8')
                debug_logger.log("INFO", "Created default .specignore file", 
                               ignore_file=str(ignore_file))
            except OSError as e:
                debug_logger.log("WARNING", "Could not create .specignore file", 
                               ignore_file=str(ignore_file), error=str(e))
    
    def update_main_gitignore(self) -> None:
        """Update main .gitignore to include spec files."""
        gitignore_file = self.settings.gitignore_file
        
        spec_patterns = [
            "# Spec CLI files",
            ".spec/",
            ".spec-index",
        ]
        
        try:
            # Read existing content
            existing_content = ""
            if gitignore_file.exists():
                existing_content = gitignore_file.read_text(encoding='utf-8')
            
            # Check if spec patterns are already present
            if ".spec/" in existing_content:
                debug_logger.log("INFO", ".gitignore already contains spec patterns")
                return
            
            # Append spec patterns
            new_content = existing_content
            if not new_content.endswith('\n') and new_content:
                new_content += '\n'
            new_content += '\n'.join(spec_patterns) + '\n'
            
            gitignore_file.write_text(new_content, encoding='utf-8')
            
            debug_logger.log("INFO", "Updated .gitignore with spec patterns", 
                           gitignore_file=str(gitignore_file))
            
        except OSError as e:
            debug_logger.log("WARNING", "Could not update .gitignore", 
                           gitignore_file=str(gitignore_file), error=str(e))
    
    def get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics about a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dictionary with directory statistics
        """
        if not directory.exists() or not directory.is_dir():
            return {"exists": False}
        
        try:
            stats = {
                "exists": True,
                "total_items": 0,
                "files": 0,
                "directories": 0,
                "total_size": 0,
                "spec_files": 0,
            }
            
            for item in directory.rglob("*"):
                stats["total_items"] += 1
                
                if item.is_file():
                    stats["files"] += 1
                    try:
                        stats["total_size"] += item.stat().st_size
                        if item.suffix == ".md" and item.parent.name != directory.name:
                            stats["spec_files"] += 1
                    except OSError:
                        pass
                elif item.is_dir():
                    stats["directories"] += 1
            
            debug_logger.log("DEBUG", "Directory statistics", 
                           directory=str(directory), stats=stats)
            
            return stats
            
        except OSError as e:
            debug_logger.log("ERROR", "Could not analyze directory", 
                           directory=str(directory), error=str(e))
            return {"exists": True, "error": str(e)}
```

### Step 2: Create spec_cli/file_system/directory_traversal.py

```python
from pathlib import Path
from typing import List, Generator, Dict, Any, Optional, Callable
from ..exceptions import SpecFileError
from ..logging.debug import debug_logger
from .ignore_patterns import IgnorePatternMatcher
from .file_type_detector import FileTypeDetector
from .file_metadata import FileMetadataExtractor

class DirectoryTraversal:
    """Handles intelligent directory traversal with filtering and analysis."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.ignore_matcher = IgnorePatternMatcher()
        self.type_detector = FileTypeDetector()
        self.metadata_extractor = FileMetadataExtractor()
    
    def find_processable_files(self, 
                              directory: Optional[Path] = None,
                              max_files: Optional[int] = None) -> List[Path]:
        """Find all processable files in a directory tree.
        
        Args:
            directory: Directory to search (defaults to root_path)
            max_files: Maximum number of files to return
            
        Returns:
            List of processable file paths
        """
        if directory is None:
            directory = self.root_path
        
        if not directory.exists() or not directory.is_dir():
            raise SpecFileError(f"Directory does not exist: {directory}")
        
        debug_logger.log("INFO", "Finding processable files", 
                        directory=str(directory),
                        max_files=max_files)
        
        processable_files = []
        total_checked = 0
        
        try:
            for file_path in self._walk_directory(directory):
                total_checked += 1
                
                # Convert to relative path for ignore checking
                try:
                    relative_path = file_path.relative_to(self.root_path)
                except ValueError:
                    # File is outside root path, skip
                    continue
                
                # Check ignore patterns
                if self.ignore_matcher.should_ignore(relative_path):
                    continue
                
                # Check if processable
                if self.type_detector.is_processable_file(file_path):
                    processable_files.append(relative_path)
                    
                    # Check max files limit
                    if max_files and len(processable_files) >= max_files:
                        debug_logger.log("INFO", "Reached max files limit", 
                                       max_files=max_files)
                        break
            
            debug_logger.log("INFO", "Processable file search complete", 
                           directory=str(directory),
                           total_checked=total_checked,
                           processable_found=len(processable_files))
            
            return processable_files
            
        except OSError as e:
            raise SpecFileError(
                f"Error traversing directory {directory}: {e}",
                {"directory": str(directory), "os_error": str(e)}
            ) from e
    
    def _walk_directory(self, directory: Path) -> Generator[Path, None, None]:
        """Walk directory tree, yielding file paths."""
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    yield item
        except OSError as e:
            debug_logger.log("WARNING", "Error accessing path during walk", 
                           path=str(item), error=str(e))
    
    def analyze_directory_structure(self, directory: Optional[Path] = None) -> Dict[str, Any]:
        """Analyze directory structure and provide detailed report.
        
        Args:
            directory: Directory to analyze (defaults to root_path)
            
        Returns:
            Dictionary with analysis results
        """
        if directory is None:
            directory = self.root_path
        
        debug_logger.log("INFO", "Analyzing directory structure", 
                        directory=str(directory))
        
        analysis = {
            "directory": str(directory),
            "total_files": 0,
            "processable_files": 0,
            "ignored_files": 0,
            "file_types": {},
            "file_categories": {},
            "largest_files": [],
            "deepest_path": "",
            "max_depth": 0,
        }
        
        try:
            max_depth = 0
            deepest_path = ""
            files_by_size = []
            
            for file_path in self._walk_directory(directory):
                analysis["total_files"] += 1
                
                # Calculate depth
                try:
                    relative_path = file_path.relative_to(directory)
                    depth = len(relative_path.parts)
                    if depth > max_depth:
                        max_depth = depth
                        deepest_path = str(relative_path)
                except ValueError:
                    continue
                
                # Check if ignored
                try:
                    relative_to_root = file_path.relative_to(self.root_path)
                    if self.ignore_matcher.should_ignore(relative_to_root):
                        analysis["ignored_files"] += 1
                        continue
                except ValueError:
                    continue
                
                # Analyze file type
                file_type = self.type_detector.get_file_type(file_path)
                analysis["file_types"][file_type] = analysis["file_types"].get(file_type, 0) + 1
                
                # Analyze file category
                category = self.type_detector.get_file_category(file_path)
                if category:
                    analysis["file_categories"][category] = analysis["file_categories"].get(category, 0) + 1
                
                # Check if processable
                if self.type_detector.is_processable_file(file_path):
                    analysis["processable_files"] += 1
                
                # Track file sizes for largest files
                try:
                    size = file_path.stat().st_size
                    files_by_size.append((file_path, size))
                except OSError:
                    continue
            
            analysis["max_depth"] = max_depth
            analysis["deepest_path"] = deepest_path
            
            # Get top 5 largest files
            files_by_size.sort(key=lambda x: x[1], reverse=True)
            for file_path, size in files_by_size[:5]:
                try:
                    relative_path = file_path.relative_to(directory)
                    analysis["largest_files"].append({
                        "path": str(relative_path),
                        "size": size,
                        "size_formatted": self._format_size(size)
                    })
                except ValueError:
                    continue
            
            debug_logger.log("INFO", "Directory analysis complete", 
                           directory=str(directory),
                           total_files=analysis["total_files"],
                           processable_files=analysis["processable_files"])
            
            return analysis
            
        except OSError as e:
            raise SpecFileError(
                f"Error analyzing directory {directory}: {e}",
                {"directory": str(directory), "os_error": str(e)}
            ) from e
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def find_files_by_pattern(self, 
                             pattern: str,
                             directory: Optional[Path] = None) -> List[Path]:
        """Find files matching a pattern.
        
        Args:
            pattern: Glob pattern to match
            directory: Directory to search (defaults to root_path)
            
        Returns:
            List of matching file paths
        """
        if directory is None:
            directory = self.root_path
        
        debug_logger.log("INFO", "Finding files by pattern", 
                        pattern=pattern, directory=str(directory))
        
        try:
            matching_files = []
            
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    try:
                        relative_path = file_path.relative_to(self.root_path)
                        if not self.ignore_matcher.should_ignore(relative_path):
                            matching_files.append(relative_path)
                    except ValueError:
                        continue
            
            debug_logger.log("INFO", "Pattern search complete", 
                           pattern=pattern, matches=len(matching_files))
            
            return matching_files
            
        except OSError as e:
            raise SpecFileError(
                f"Error searching for pattern {pattern} in {directory}: {e}",
                {"pattern": pattern, "directory": str(directory), "os_error": str(e)}
            ) from e
    
    def get_directory_summary(self, directory: Optional[Path] = None) -> Dict[str, Any]:
        """Get a summary of directory contents.
        
        Args:
            directory: Directory to summarize (defaults to root_path)
            
        Returns:
            Dictionary with directory summary
        """
        if directory is None:
            directory = self.root_path
        
        try:
            processable_files = self.find_processable_files(directory, max_files=100)
            analysis = self.analyze_directory_structure(directory)
            
            summary = {
                "directory": str(directory),
                "processable_file_count": len(processable_files),
                "total_file_count": analysis["total_files"],
                "ignored_file_count": analysis["ignored_files"],
                "primary_file_types": self._get_top_items(analysis["file_types"], 5),
                "primary_categories": self._get_top_items(analysis["file_categories"], 3),
                "directory_depth": analysis["max_depth"],
                "ready_for_spec_generation": len(processable_files) > 0,
            }
            
            return summary
            
        except Exception as e:
            debug_logger.log("ERROR", "Error creating directory summary", 
                           directory=str(directory), error=str(e))
            return {
                "directory": str(directory),
                "error": str(e),
                "ready_for_spec_generation": False,
            }
    
    def _get_top_items(self, items_dict: Dict[str, int], limit: int) -> List[Dict[str, Any]]:
        """Get top items from a count dictionary."""
        sorted_items = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)
        return [{"type": item, "count": count} for item, count in sorted_items[:limit]]
```

## Test Requirements

Create comprehensive tests for directory operations:

### Test Cases (18 tests total)

**Directory Manager Tests:**
1. **test_directory_manager_ensures_specs_directory**
2. **test_directory_manager_creates_spec_directories**
3. **test_directory_manager_checks_existing_specs**
4. **test_directory_manager_creates_backups**
5. **test_directory_manager_removes_directories_safely**
6. **test_directory_manager_sets_up_ignore_files**
7. **test_directory_manager_updates_gitignore**
8. **test_directory_manager_handles_permission_errors**

**Directory Traversal Tests:**
9. **test_directory_traversal_finds_processable_files**
10. **test_directory_traversal_respects_ignore_patterns**
11. **test_directory_traversal_respects_max_files_limit**
12. **test_directory_traversal_analyzes_structure**
13. **test_directory_traversal_finds_files_by_pattern**
14. **test_directory_traversal_creates_directory_summary**

**Integration Tests:**
15. **test_directory_operations_integrate_with_ignore_patterns**
16. **test_directory_operations_integrate_with_file_analysis**
17. **test_directory_operations_handle_complex_structures**
18. **test_directory_operations_handle_edge_cases**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_system/test_directory_manager.py tests/unit/file_system/test_directory_traversal.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_system/test_directory_manager.py tests/unit/file_system/test_directory_traversal.py --cov=spec_cli.file_system.directory_manager --cov=spec_cli.file_system.directory_traversal --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_system/directory_manager.py spec_cli/file_system/directory_traversal.py

# Check code formatting
poetry run ruff check spec_cli/file_system/directory_manager.py spec_cli/file_system/directory_traversal.py
poetry run ruff format spec_cli/file_system/directory_manager.py spec_cli/file_system/directory_traversal.py

# Verify imports work correctly
python -c "from spec_cli.file_system.directory_manager import DirectoryManager; from spec_cli.file_system.directory_traversal import DirectoryTraversal; print('Import successful')"

# Test directory operations
python -c "
from spec_cli.file_system.directory_manager import DirectoryManager
from spec_cli.file_system.directory_traversal import DirectoryTraversal
from pathlib import Path

manager = DirectoryManager()
manager.ensure_specs_directory()

traversal = DirectoryTraversal(Path.cwd())
files = traversal.find_processable_files(max_files=5)
print(f'Found {len(files)} processable files')

summary = traversal.get_directory_summary()
print(f'Directory ready for spec generation: {summary[\"ready_for_spec_generation\"]}')
"
```

## Definition of Done

- [ ] DirectoryManager class implemented with spec directory operations
- [ ] DirectoryTraversal class with intelligent file discovery
- [ ] Integration with ignore patterns from slice-6a
- [ ] Integration with file analysis from slice-5a/5b
- [ ] Backup and safety operations for existing files
- [ ] .specs/ directory structure management
- [ ] All 18 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Debug logging for all directory operations
- [ ] Comprehensive error handling for file system operations
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice completes the file system layer and enables PHASE-3 (templates) by providing:
- Directory management that template system can use for spec creation
- File discovery that template generation can leverage
- Structure validation that template operations can rely upon
- Complete file system foundation for higher-level operations