# Slice 6A: Ignore Patterns and Filtering

## Goal

Create focused ignore pattern processing system that parses .specignore files, compiles regex patterns, and provides efficient file filtering for directory operations.

## Context

The current monolithic code has no unified ignore pattern system. This slice creates a focused pattern matching system that can process .specignore files and provide efficient filtering decisions. It focuses specifically on the pattern matching logic, leaving directory operations for slice-6b.

## Scope

**Included in this slice:**
- IgnorePatternMatcher class for .specignore processing
- Pattern compilation and matching with regex support
- Gitignore-style pattern syntax support
- Efficient file path filtering logic

**NOT included in this slice:**
- Directory traversal operations (moved to slice-6b)
- Spec directory creation (moved to slice-6b)
- Backup and safety operations (moved to slice-6b)
- File system modification operations

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for pattern errors)
- `spec_cli.logging.debug` (debug_logger for pattern operations)
- `spec_cli.config.settings` (Settings for ignore file paths)
- `spec_cli.file_system.path_resolver` (PathResolver from slice-4)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` from slice-3a-settings-console
- `PathResolver` from slice-4-path-resolution

## Files to Create

```
spec_cli/file_system/
└── ignore_patterns.py      # IgnorePatternMatcher class
```

## Implementation Steps

### Step 1: Create spec_cli/file_system/ignore_patterns.py

```python
import re
from pathlib import Path
from typing import List, Set, Optional, Pattern
from ..exceptions import SpecFileError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class IgnorePatternMatcher:
    """Handles .specignore pattern matching with gitignore-style syntax."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.patterns: List[Pattern] = []
        self.raw_patterns: List[str] = []
        self.negation_patterns: List[Pattern] = []
        self.loaded_from: Optional[Path] = None
        
        # Default patterns to always ignore
        self.default_ignore_patterns = [
            # Spec-related
            ".spec",
            ".spec/*",
            ".spec-index",
            
            # Version control
            ".git",
            ".git/*",
            ".gitignore",
            ".svn",
            ".hg",
            
            # IDE and editor files
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "*~",
            ".DS_Store",
            "Thumbs.db",
            
            # Build and cache directories
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".coverage",
            "htmlcov",
            
            # Temporary and backup files
            "*.tmp",
            "*.temp",
            "*.bak",
            "*.backup",
        ]
        
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load ignore patterns from .specignore file and defaults."""
        # Start with default patterns
        all_patterns = self.default_ignore_patterns.copy()
        
        # Load from .specignore if it exists
        ignore_file = self.settings.ignore_file
        if ignore_file.exists():
            try:
                with ignore_file.open('r', encoding='utf-8') as f:
                    file_patterns = [
                        line.strip() 
                        for line in f 
                        if line.strip() and not line.strip().startswith('#')
                    ]
                all_patterns.extend(file_patterns)
                self.loaded_from = ignore_file
                
                debug_logger.log("INFO", "Loaded ignore patterns from file", 
                               ignore_file=str(ignore_file),
                               pattern_count=len(file_patterns))
            except Exception as e:
                debug_logger.log("WARNING", "Could not load .specignore file", 
                               ignore_file=str(ignore_file), error=str(e))
        
        # Compile all patterns
        self.raw_patterns = all_patterns
        self._compile_patterns(all_patterns)
        
        debug_logger.log("INFO", "Ignore patterns compiled", 
                        total_patterns=len(self.patterns),
                        negation_patterns=len(self.negation_patterns))
    
    def _compile_patterns(self, patterns: List[str]) -> None:
        """Compile patterns into regex objects."""
        self.patterns = []
        self.negation_patterns = []
        
        for pattern in patterns:
            if not pattern:
                continue
            
            try:
                # Handle negation patterns (starting with !)
                is_negation = pattern.startswith('!')
                if is_negation:
                    pattern = pattern[1:]
                
                # Convert gitignore-style pattern to regex
                regex_pattern = self._gitignore_to_regex(pattern)
                compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
                
                if is_negation:
                    self.negation_patterns.append(compiled_pattern)
                else:
                    self.patterns.append(compiled_pattern)
                    
                debug_logger.log("DEBUG", "Compiled ignore pattern", 
                               original=pattern, 
                               regex=regex_pattern,
                               is_negation=is_negation)
                
            except re.error as e:
                debug_logger.log("WARNING", "Invalid ignore pattern", 
                               pattern=pattern, error=str(e))
                continue
    
    def _gitignore_to_regex(self, pattern: str) -> str:
        """Convert gitignore-style pattern to regex."""
        # Escape special regex characters except *, ?, and /
        pattern = re.escape(pattern)
        
        # Restore gitignore special characters
        pattern = pattern.replace(r'\*', '.*')  # * matches any characters except /
        pattern = pattern.replace(r'\?', '.')   # ? matches any single character
        pattern = pattern.replace(r'\/', '/')   # / is literal
        
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            pattern = pattern[:-1] + '(/.*)?$'
        else:
            # Pattern can match file or directory
            pattern = pattern + '(/.*)?$'
        
        # Handle patterns starting with / (absolute from root)
        if pattern.startswith('/'):
            pattern = '^' + pattern[1:]
        else:
            # Pattern can match at any level
            pattern = '(^|/)' + pattern
        
        return pattern
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file path should be ignored.
        
        Args:
            file_path: Path to check (relative to project root)
            
        Returns:
            True if file should be ignored, False otherwise
        """
        # Convert to string for pattern matching
        path_str = str(file_path).replace('\\', '/')  # Normalize path separators
        
        # Remove leading ./ if present
        if path_str.startswith('./'):
            path_str = path_str[2:]
        
        debug_logger.log("DEBUG", "Checking ignore patterns", 
                        file_path=path_str)
        
        # Check if any ignore pattern matches
        ignored = False
        for pattern in self.patterns:
            if pattern.search(path_str):
                ignored = True
                debug_logger.log("DEBUG", "File matched ignore pattern", 
                               file_path=path_str,
                               pattern=pattern.pattern)
                break
        
        # Check negation patterns (! patterns override ignore)
        if ignored:
            for neg_pattern in self.negation_patterns:
                if neg_pattern.search(path_str):
                    ignored = False
                    debug_logger.log("DEBUG", "File matched negation pattern", 
                                   file_path=path_str,
                                   pattern=neg_pattern.pattern)
                    break
        
        debug_logger.log("DEBUG", "Ignore check result", 
                        file_path=path_str, 
                        should_ignore=ignored)
        
        return ignored
    
    def filter_paths(self, paths: List[Path]) -> List[Path]:
        """Filter a list of paths, removing ignored ones.
        
        Args:
            paths: List of paths to filter
            
        Returns:
            Filtered list with ignored paths removed
        """
        filtered = []
        ignored_count = 0
        
        for path in paths:
            if self.should_ignore(path):
                ignored_count += 1
            else:
                filtered.append(path)
        
        debug_logger.log("INFO", "Filtered paths using ignore patterns", 
                        original_count=len(paths),
                        filtered_count=len(filtered),
                        ignored_count=ignored_count)
        
        return filtered
    
    def get_pattern_summary(self) -> dict:
        """Get summary of loaded patterns for debugging."""
        return {
            "total_patterns": len(self.patterns),
            "negation_patterns": len(self.negation_patterns),
            "raw_patterns": self.raw_patterns,
            "loaded_from": str(self.loaded_from) if self.loaded_from else "defaults only",
            "default_pattern_count": len(self.default_ignore_patterns)
        }
    
    def test_pattern(self, pattern: str, test_path: str) -> bool:
        """Test a single pattern against a path (for debugging).
        
        Args:
            pattern: Pattern to test
            test_path: Path to test against
            
        Returns:
            True if pattern matches path
        """
        try:
            regex_pattern = self._gitignore_to_regex(pattern)
            compiled = re.compile(regex_pattern, re.IGNORECASE)
            result = bool(compiled.search(test_path))
            
            debug_logger.log("DEBUG", "Pattern test", 
                           pattern=pattern,
                           test_path=test_path,
                           regex=regex_pattern,
                           matches=result)
            
            return result
            
        except re.error as e:
            debug_logger.log("ERROR", "Invalid pattern for testing", 
                           pattern=pattern, error=str(e))
            return False
    
    def add_runtime_pattern(self, pattern: str) -> bool:
        """Add a pattern at runtime (for dynamic filtering).
        
        Args:
            pattern: Pattern to add
            
        Returns:
            True if pattern was added successfully
        """
        try:
            regex_pattern = self._gitignore_to_regex(pattern)
            compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
            
            if pattern.startswith('!'):
                self.negation_patterns.append(compiled_pattern)
            else:
                self.patterns.append(compiled_pattern)
            
            self.raw_patterns.append(pattern)
            
            debug_logger.log("INFO", "Added runtime ignore pattern", 
                           pattern=pattern)
            
            return True
            
        except re.error as e:
            debug_logger.log("ERROR", "Could not add runtime pattern", 
                           pattern=pattern, error=str(e))
            return False
    
    def reload_patterns(self) -> None:
        """Reload patterns from .specignore file."""
        debug_logger.log("INFO", "Reloading ignore patterns")
        self._load_patterns()
```

## Test Requirements

Create comprehensive tests for ignore pattern matching:

### Test Cases (12 tests total)

**Pattern Loading Tests:**
1. **test_ignore_patterns_loads_default_patterns**
2. **test_ignore_patterns_loads_from_specignore_file**
3. **test_ignore_patterns_handles_missing_specignore_file**
4. **test_ignore_patterns_handles_malformed_specignore_file**

**Pattern Compilation Tests:**
5. **test_gitignore_to_regex_handles_wildcards**
6. **test_gitignore_to_regex_handles_directory_patterns**
7. **test_gitignore_to_regex_handles_negation_patterns**

**Pattern Matching Tests:**
8. **test_should_ignore_matches_file_patterns**
9. **test_should_ignore_matches_directory_patterns**
10. **test_should_ignore_respects_negation_patterns**
11. **test_filter_paths_removes_ignored_files**
12. **test_runtime_pattern_addition_works**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/file_system/test_ignore_patterns.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/file_system/test_ignore_patterns.py --cov=spec_cli.file_system.ignore_patterns --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/file_system/ignore_patterns.py

# Check code formatting
poetry run ruff check spec_cli/file_system/ignore_patterns.py
poetry run ruff format spec_cli/file_system/ignore_patterns.py

# Verify imports work correctly
python -c "from spec_cli.file_system.ignore_patterns import IgnorePatternMatcher; print('Import successful')"

# Test pattern matching
echo "*.pyc" > .specignore
echo "__pycache__" >> .specignore
python -c "
from spec_cli.file_system.ignore_patterns import IgnorePatternMatcher
from pathlib import Path
matcher = IgnorePatternMatcher()
print(f'Ignore test.pyc: {matcher.should_ignore(Path(\"test.pyc\"))}')
print(f'Ignore __pycache__: {matcher.should_ignore(Path(\"__pycache__\"))}')
print(f'Ignore test.py: {matcher.should_ignore(Path(\"test.py\"))}')
"
rm .specignore
```

## Definition of Done

- [ ] IgnorePatternMatcher class implemented with gitignore-style syntax
- [ ] Pattern loading from .specignore files with sensible defaults
- [ ] Regex compilation with proper escaping and pattern conversion
- [ ] Efficient file path filtering with negation pattern support
- [ ] Runtime pattern addition for dynamic filtering
- [ ] All 12 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Debug logging for all pattern operations
- [ ] Comprehensive pattern testing utilities for debugging
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-6b (directory operations) by providing:
- Efficient file filtering that directory traversal can use
- Pattern matching system that directory operations can integrate
- Ignore logic that directory creation can respect
- Foundation for intelligent directory management