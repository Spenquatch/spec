# Slice 4: Path Resolution and Validation

## Goal

Create a robust path resolution system that handles relative/absolute paths, validates project boundaries, and provides consistent path handling for all spec operations.

## Context

The current monolithic code has path handling scattered throughout with inconsistent validation and no clear project boundary enforcement. This slice creates a centralized system that all other components will use for path operations. It builds on the foundation exception and logging systems to provide proper error handling and debugging information.

## Scope

**Included in this slice:**
- PathResolver class for consistent path handling
- Project boundary validation and enforcement
- Conversion between different path contexts (.specs/, relative, absolute)
- Path validation with clear error messages

**NOT included in this slice:**
- File existence checking (comes in slice-5-file-analysis)
- Directory creation (comes in slice-6-directory-management)
- Ignore pattern matching (comes in slice-6-directory-management)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError, SpecFileError, SpecValidationError)
- `spec_cli.logging.debug` (debug_logger)
- `spec_cli.config.settings` (SpecSettings, get_settings)

**Required functions/classes:**
- `SpecError` exception hierarchy
- `debug_logger` with timing context manager
- `SpecSettings` dataclass with path properties

## Files to Create

```
spec_cli/file_system/
├── __init__.py             # Module exports
└── path_resolver.py        # PathResolver class
```

## Implementation Steps

### Step 1: Create spec_cli/file_system/__init__.py

```python
"""File system operations for spec CLI.

This package provides abstractions for file system operations including
path resolution, file analysis, and directory management.
"""

from .path_resolver import PathResolver

__all__ = [
    "PathResolver",
]
```

### Step 2: Create spec_cli/file_system/path_resolver.py

```python
from pathlib import Path
from typing import Optional, Union
from ..exceptions import SpecFileError, SpecValidationError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class PathResolver:
    """Handles path resolution and validation for spec operations.
    
    Provides consistent path handling with project boundary enforcement,
    validation, and conversion between different path contexts.
    """
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
    
    def resolve_input_path(self, path_str: str) -> Path:
        """Resolve and validate an input path for spec operations.
        
        Args:
            path_str: Path string from user input (relative, absolute, or ".")
            
        Returns:
            Resolved path relative to project root
            
        Raises:
            SpecValidationError: If path is outside project boundaries
            SpecFileError: If path resolution fails
        """
        with debug_logger.timer(f"resolve_input_path_{Path(path_str).name}"):
            debug_logger.log("INFO", "Resolving input path", input_path=path_str)
            
            try:
                # Handle current directory shorthand
                if path_str == ".":
                    current_dir = Path.cwd()
                    debug_logger.log("INFO", "Resolving current directory", cwd=str(current_dir))
                    return self._ensure_within_project(current_dir)
                
                input_path = Path(path_str)
                
                # Handle absolute paths
                if input_path.is_absolute():
                    debug_logger.log("INFO", "Processing absolute path", path=str(input_path))
                    return self._ensure_within_project(input_path)
                
                # Handle relative paths - resolve relative to current working directory
                resolved_path = (Path.cwd() / input_path).resolve()
                debug_logger.log("INFO", "Processing relative path", 
                               original=path_str, resolved=str(resolved_path))
                return self._ensure_within_project(resolved_path)
                
            except OSError as e:
                raise SpecFileError(f"Failed to resolve path '{path_str}': {e}") from e
    
    def _ensure_within_project(self, absolute_path: Path) -> Path:
        """Ensure path is within project boundaries and return relative path.
        
        Args:
            absolute_path: Absolute path to validate
            
        Returns:
            Path relative to project root
            
        Raises:
            SpecValidationError: If path is outside project boundaries
        """
        try:
            relative_path = absolute_path.relative_to(self.settings.root_path)
            debug_logger.log("INFO", "Path within project boundaries",
                           absolute=str(absolute_path),
                           relative=str(relative_path))
            return relative_path
            
        except ValueError as e:
            raise SpecValidationError(
                f"Path '{absolute_path}' is outside project root '{self.settings.root_path}'"
            ) from e
    
    def convert_to_spec_directory_path(self, file_path: Path) -> Path:
        """Convert file path to corresponding spec directory path.
        
        Args:
            file_path: Path to source file (relative to project root)
            
        Returns:
            Path to spec directory (e.g., src/models.py -> .specs/src/models/)
        """
        debug_logger.log("INFO", "Converting to spec directory path", 
                         source_file=str(file_path))
        
        # Remove file extension and create directory path
        spec_dir = self.settings.specs_dir / file_path.parent / file_path.stem
        
        debug_logger.log("INFO", "Spec directory path created",
                         source_file=str(file_path),
                         spec_dir=str(spec_dir))
        
        return spec_dir
    
    def convert_from_specs_path(self, specs_path: Union[str, Path]) -> Path:
        """Convert path from .specs/ context to relative project path.
        
        Args:
            specs_path: Path that may be in .specs/ context
            
        Returns:
            Path relative to project root (for Git operations)
        """
        path_obj = Path(specs_path)
        
        # If absolute path, try to make relative to .specs/
        if path_obj.is_absolute():
            try:
                relative_path = path_obj.relative_to(self.settings.specs_dir)
                debug_logger.log("INFO", "Converted absolute specs path",
                                 absolute=str(path_obj),
                                 relative=str(relative_path))
                return relative_path
            except ValueError:
                # Path is not under .specs/, return as-is
                debug_logger.log("INFO", "Path not under .specs/, returning as-is",
                                 path=str(path_obj))
                return path_obj
        
        # If path starts with .specs/, remove the prefix
        path_str = str(path_obj)
        if path_str.startswith(".specs/"):
            relative_path = Path(path_str.replace(".specs/", "", 1))
            debug_logger.log("INFO", "Removed .specs/ prefix",
                             original=path_str,
                             relative=str(relative_path))
            return relative_path
        
        # Return path as-is
        debug_logger.log("INFO", "Path already relative, returning as-is",
                         path=str(path_obj))
        return path_obj
    
    def is_within_project(self, path: Path) -> bool:
        """Check if path is within the project root.
        
        Args:
            path: Path to check (can be relative or absolute)
            
        Returns:
            True if path is within project boundaries
        """
        try:
            if path.is_absolute():
                path.relative_to(self.settings.root_path)
            return True
        except ValueError:
            return False
    
    def get_absolute_path(self, relative_path: Path) -> Path:
        """Convert relative path to absolute path within project.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Absolute path
        """
        absolute_path = self.settings.root_path / relative_path
        debug_logger.log("INFO", "Converted to absolute path",
                         relative=str(relative_path),
                         absolute=str(absolute_path))
        return absolute_path
    
    def validate_path_exists(self, path: Path) -> None:
        """Validate that a path exists.
        
        Args:
            path: Path to validate (relative to project root)
            
        Raises:
            SpecFileError: If path does not exist
        """
        absolute_path = self.get_absolute_path(path) if not path.is_absolute() else path
        
        if not absolute_path.exists():
            raise SpecFileError(f"Path does not exist: {absolute_path}")
        
        debug_logger.log("INFO", "Path exists validation passed", path=str(absolute_path))
```

### Step 3: Update spec_cli/file_system/__init__.py exports

Ensure the PathResolver is properly exported and can be imported by other modules.

## Test Requirements

Create `tests/unit/file_system/test_path_resolver.py` with these specific test cases:

### Test Cases (18 tests total)

1. **test_path_resolver_initializes_with_default_settings**
2. **test_path_resolver_initializes_with_custom_settings**
3. **test_resolve_input_path_handles_current_directory**
4. **test_resolve_input_path_handles_relative_paths**
5. **test_resolve_input_path_handles_absolute_paths_within_project**
6. **test_resolve_input_path_rejects_paths_outside_project**
7. **test_resolve_input_path_handles_os_errors**
8. **test_convert_to_spec_directory_path_creates_correct_structure**
9. **test_convert_to_spec_directory_path_handles_nested_files**
10. **test_convert_to_spec_directory_path_removes_file_extension**
11. **test_convert_from_specs_path_handles_absolute_specs_paths**
12. **test_convert_from_specs_path_handles_relative_specs_paths**
13. **test_convert_from_specs_path_removes_specs_prefix**
14. **test_convert_from_specs_path_handles_non_specs_paths**
15. **test_is_within_project_accepts_valid_paths**
16. **test_is_within_project_rejects_external_paths**
17. **test_get_absolute_path_converts_correctly**
18. **test_validate_path_exists_passes_for_existing_paths**
19. **test_validate_path_exists_raises_for_missing_paths**

Each test should:
- Use proper fixtures for temporary directories and settings
- Mock the debug_logger to avoid actual logging during tests
- Test both success and error cases
- Verify debug logging calls are made with correct parameters

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_system/test_path_resolver.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_system/test_path_resolver.py --cov=spec_cli.file_system.path_resolver --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_system/path_resolver.py

# Check code formatting
poetry run ruff check spec_cli/file_system/path_resolver.py
poetry run ruff format spec_cli/file_system/path_resolver.py

# Verify imports work correctly
python -c "from spec_cli.file_system import PathResolver; print('Import successful')"

# Test basic functionality
python -c "
from spec_cli.file_system import PathResolver
from pathlib import Path
pr = PathResolver()
result = pr.convert_to_spec_directory_path(Path('src/test.py'))
print(f'Conversion result: {result}')
"
```

## Definition of Done

- [ ] `spec_cli/file_system/` package created with proper `__init__.py`
- [ ] `PathResolver` class implemented with all required methods
- [ ] All path operations use foundation exception types
- [ ] Debug logging integrated throughout with timing information
- [ ] Project boundary validation enforced consistently
- [ ] All 18 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Code formatted and linted successfully
- [ ] Integration with settings and logging systems verified

## Next Slice Preparation

This slice enables **slice-5-file-analysis.md** by providing:
- `PathResolver` class for consistent path handling
- Path validation and boundary enforcement
- Conversion utilities for different path contexts

The file analysis slice will use PathResolver to handle all path operations before analyzing file contents and metadata.