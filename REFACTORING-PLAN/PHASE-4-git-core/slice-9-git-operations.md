# Slice 9: Git Operations and Repository Interface

## Goal

Create a clean Git operations abstraction with proper error handling, path conversion utilities, and a repository interface that supports the isolated .spec repository pattern used by the spec CLI.

## Context

The current monolithic code has Git operations scattered throughout with manual environment variable management and inconsistent error handling. This slice creates a robust Git operations layer that abstracts all Git commands, handles the complex environment setup needed for the isolated .spec repository, and provides proper error handling and path conversion utilities.

## Scope

**Included in this slice:**
- GitRepository abstract interface for operations
- SpecGitRepository implementation for spec-specific Git operations
- GitOperations class for low-level Git command execution
- GitPathConverter for path handling between different contexts
- Git environment setup and isolation management

**NOT included in this slice:**
- High-level business logic (comes in slice-10-spec-repository)
- File processing workflows (comes in slice-11-file-processing)
- User interface for Git operations (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for Git operation errors)
- `spec_cli.logging.debug` (debug_logger for Git operation tracking)
- `spec_cli.config.settings` (SpecSettings for repository paths)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration

## Files to Create

```
spec_cli/git/
├── __init__.py             # Module exports
├── repository.py           # Git repository interface
├── operations.py           # Git command execution
└── path_converter.py       # Path conversion utilities
```

## Implementation Steps

### Step 1: Create spec_cli/git/__init__.py

```python
"""Git operations for spec CLI.

This package provides Git repository abstractions, command execution,
and path conversion utilities for the isolated .spec repository system.
"""

from .repository import GitRepository, SpecGitRepository
from .operations import GitOperations
from .path_converter import GitPathConverter

__all__ = [
    "GitRepository",
    "SpecGitRepository", 
    "GitOperations",
    "GitPathConverter",
]
```

### Step 2: Create spec_cli/git/repository.py

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from .operations import GitOperations
from .path_converter import GitPathConverter
from ..exceptions import SpecGitError
from ..config.settings import get_settings, SpecSettings
from ..logging.debug import debug_logger

class GitRepository(ABC):
    """Abstract interface for Git repository operations."""
    
    @abstractmethod
    def add(self, paths: List[str]) -> None:
        """Add files to Git index.
        
        Args:
            paths: List of file paths to add
            
        Raises:
            SpecGitError: If add operation fails
        """
        pass
    
    @abstractmethod
    def commit(self, message: str) -> None:
        """Create a commit with the given message.
        
        Args:
            message: Commit message
            
        Raises:
            SpecGitError: If commit operation fails
        """
        pass
    
    @abstractmethod
    def status(self) -> None:
        """Show repository status.
        
        Raises:
            SpecGitError: If status operation fails
        """
        pass
    
    @abstractmethod
    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show commit log.
        
        Args:
            paths: Optional list of paths to show log for
            
        Raises:
            SpecGitError: If log operation fails
        """
        pass
    
    @abstractmethod
    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show differences.
        
        Args:
            paths: Optional list of paths to show diff for
            
        Raises:
            SpecGitError: If diff operation fails
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if repository is initialized.
        
        Returns:
            True if repository is initialized
        """
        pass

class SpecGitRepository(GitRepository):
    """Git repository implementation for spec operations with isolated repository."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.operations = GitOperations(
            spec_dir=self.settings.spec_dir,
            specs_dir=self.settings.specs_dir,
            index_file=self.settings.index_file
        )
        self.path_converter = GitPathConverter(self.settings.specs_dir)
        
        debug_logger.log("INFO", "SpecGitRepository initialized",
                        spec_dir=str(self.settings.spec_dir),
                        specs_dir=str(self.settings.specs_dir))
    
    def add(self, paths: List[str]) -> None:
        """Add files to spec Git index.
        
        Args:
            paths: List of file paths to add (will be converted to Git work tree context)
        """
        debug_logger.log("INFO", "Adding files to spec repository", 
                        path_count=len(paths))
        
        # Convert paths to Git work tree context
        converted_paths = []
        for path in paths:
            converted_path = self.path_converter.convert_to_git_path(path)
            converted_paths.append(converted_path)
            debug_logger.log("DEBUG", "Path conversion for add", 
                           original=path, converted=converted_path)
        
        # Add files with force flag to bypass ignore rules
        git_args = ["add", "-f"] + converted_paths
        self.operations.run_git_command(git_args)
        
        debug_logger.log("INFO", "Files added to spec repository successfully",
                        files_added=len(converted_paths))
    
    def commit(self, message: str) -> None:
        """Create commit in spec repository.
        
        Args:
            message: Commit message
        """
        debug_logger.log("INFO", "Creating commit in spec repository", 
                        message=message[:50] + "..." if len(message) > 50 else message)
        
        git_args = ["commit", "-m", message]
        self.operations.run_git_command(git_args)
        
        debug_logger.log("INFO", "Commit created successfully")
    
    def status(self) -> None:
        """Show spec repository status."""
        debug_logger.log("INFO", "Showing spec repository status")
        
        git_args = ["status"]
        self.operations.run_git_command(git_args)
    
    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository log.
        
        Args:
            paths: Optional list of paths to show log for
        """
        debug_logger.log("INFO", "Showing spec repository log", 
                        path_filter=bool(paths))
        
        git_args = ["log", "--oneline", "--graph"]
        
        if paths:
            # Convert paths to Git work tree context
            converted_paths = [
                self.path_converter.convert_to_git_path(path) 
                for path in paths
            ]
            git_args.extend(["--"] + converted_paths)
            debug_logger.log("DEBUG", "Log with path filter", 
                           original_paths=paths, converted_paths=converted_paths)
        
        self.operations.run_git_command(git_args)
    
    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository diff.
        
        Args:
            paths: Optional list of paths to show diff for
        """
        debug_logger.log("INFO", "Showing spec repository diff", 
                        path_filter=bool(paths))
        
        git_args = ["diff"]
        
        if paths:
            # Convert paths to Git work tree context
            converted_paths = [
                self.path_converter.convert_to_git_path(path) 
                for path in paths
            ]
            git_args.extend(["--"] + converted_paths)
            debug_logger.log("DEBUG", "Diff with path filter", 
                           original_paths=paths, converted_paths=converted_paths)
        
        self.operations.run_git_command(git_args)
    
    def is_initialized(self) -> bool:
        """Check if spec repository is initialized.
        
        Returns:
            True if .spec directory exists and is a valid Git repository
        """
        if not self.settings.spec_dir.exists():
            debug_logger.log("DEBUG", "Spec directory does not exist")
            return False
        
        if not self.settings.spec_dir.is_dir():
            debug_logger.log("DEBUG", "Spec directory is not a directory")
            return False
        
        # Check if it's a valid Git repository by looking for Git objects
        git_objects_dir = self.settings.spec_dir / "objects"
        is_initialized = git_objects_dir.exists() and git_objects_dir.is_dir()
        
        debug_logger.log("DEBUG", "Spec repository initialization check", 
                        is_initialized=is_initialized)
        
        return is_initialized
    
    def initialize_repository(self) -> None:
        """Initialize the spec repository.
        
        Raises:
            SpecGitError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing spec repository")
        
        if self.is_initialized():
            debug_logger.log("INFO", "Spec repository already initialized")
            return
        
        # Create .spec directory if it doesn't exist
        self.settings.spec_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .specs directory if it doesn't exist
        self.settings.specs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize bare Git repository
        self.operations.initialize_repository()
        
        debug_logger.log("INFO", "Spec repository initialized successfully")
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the spec repository.
        
        Returns:
            Dictionary with repository information
        """
        info = {
            "is_initialized": self.is_initialized(),
            "spec_dir": str(self.settings.spec_dir),
            "specs_dir": str(self.settings.specs_dir),
            "index_file": str(self.settings.index_file),
        }
        
        if self.is_initialized():
            try:
                # Try to get additional repository information
                info.update({
                    "spec_dir_exists": self.settings.spec_dir.exists(),
                    "specs_dir_exists": self.settings.specs_dir.exists(),
                    "index_file_exists": self.settings.index_file.exists(),
                })
            except Exception as e:
                info["error"] = str(e)
        
        return info
```

### Step 3: Create spec_cli/git/operations.py

```python
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..exceptions import SpecGitError
from ..logging.debug import debug_logger

class GitOperations:
    """Handles low-level Git command execution with spec environment configuration."""
    
    def __init__(self, spec_dir: Path, specs_dir: Path, index_file: Path):
        self.spec_dir = spec_dir
        self.specs_dir = specs_dir
        self.index_file = index_file
        
        debug_logger.log("INFO", "GitOperations initialized",
                        spec_dir=str(spec_dir),
                        specs_dir=str(specs_dir),
                        index_file=str(index_file))
    
    def run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Execute Git command with spec environment configuration.
        
        Args:
            args: Git command arguments (without 'git' prefix)
            
        Returns:
            CompletedProcess instance
            
        Raises:
            SpecGitError: If Git command fails
        """
        env = self._prepare_git_environment()
        cmd = self._prepare_git_command(args)
        
        debug_logger.log("INFO", "Executing Git command", 
                        command=" ".join(cmd),
                        git_dir=str(self.spec_dir),
                        work_tree=str(self.specs_dir))
        
        try:
            with debug_logger.timer(f"git_{args[0]}"):
                result = subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    capture_output=False,  # Allow output to go to stdout/stderr
                    text=True,
                    cwd=str(self.specs_dir.parent)  # Run from project root
                )
            
            debug_logger.log("INFO", "Git command completed successfully",
                           command=args[0], return_code=result.returncode)
            
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(cmd)}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            
            debug_logger.log("ERROR", "Git command failed",
                           command=" ".join(cmd),
                           return_code=e.returncode,
                           error=error_msg)
            
            raise SpecGitError(error_msg) from e
            
        except FileNotFoundError as e:
            error_msg = "Git not found. Please ensure Git is installed and in PATH."
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error running Git command: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e
    
    def _prepare_git_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Git command.
        
        Returns:
            Environment dictionary with Git configuration
        """
        env = os.environ.copy()
        
        # Set spec-specific Git environment
        git_env = {
            "GIT_DIR": str(self.spec_dir),
            "GIT_WORK_TREE": str(self.specs_dir),
            "GIT_INDEX_FILE": str(self.index_file),
        }
        
        env.update(git_env)
        
        debug_logger.log("DEBUG", "Git environment prepared", **git_env)
        
        return env
    
    def _prepare_git_command(self, args: List[str]) -> List[str]:
        """Prepare Git command with required configuration flags.
        
        Args:
            args: Git command arguments
            
        Returns:
            Complete command list
        """
        cmd = [
            "git",
            # Disable global excludes file to prevent interference
            "-c", "core.excludesFile=",
            # Ensure case sensitivity for cross-platform compatibility
            "-c", "core.ignoreCase=false",
        ]
        
        # Add the actual command arguments
        cmd.extend(args)
        
        debug_logger.log("DEBUG", "Git command prepared", 
                        original_args=args, full_command=cmd)
        
        return cmd
    
    def initialize_repository(self) -> None:
        """Initialize bare Git repository for spec.
        
        Raises:
            SpecGitError: If initialization fails
        """
        debug_logger.log("INFO", "Initializing bare Git repository")
        
        try:
            # Ensure spec directory exists
            self.spec_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize bare repository
            init_cmd = ["git", "init", "--bare", str(self.spec_dir)]
            
            result = subprocess.run(
                init_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            debug_logger.log("INFO", "Bare Git repository initialized",
                           spec_dir=str(self.spec_dir),
                           stdout=result.stdout)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to initialize Git repository: {e}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error initializing repository: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecGitError(error_msg) from e
    
    def check_git_available(self) -> bool:
        """Check if Git is available in the system.
        
        Returns:
            True if Git is available
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            
            debug_logger.log("DEBUG", "Git availability check passed",
                           version=result.stdout.strip())
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            debug_logger.log("WARNING", "Git is not available")
            return False
    
    def get_git_version(self) -> Optional[str]:
        """Get Git version string.
        
        Returns:
            Git version string or None if Git is not available
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            
            version = result.stdout.strip()
            debug_logger.log("DEBUG", "Git version obtained", version=version)
            return version
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            debug_logger.log("WARNING", "Could not get Git version")
            return None
```

### Step 4: Create spec_cli/git/path_converter.py

```python
from pathlib import Path
from typing import Union
from ..logging.debug import debug_logger

class GitPathConverter:
    """Converts paths between different Git contexts (.specs/, relative, absolute)."""
    
    def __init__(self, specs_dir: Path):
        self.specs_dir = specs_dir
        debug_logger.log("INFO", "GitPathConverter initialized", 
                        specs_dir=str(specs_dir))
    
    def convert_to_git_path(self, path: Union[str, Path]) -> str:
        """Convert path to be relative to Git work tree (.specs/).
        
        Args:
            path: Path to convert (can be absolute, relative, or .specs/ prefixed)
            
        Returns:
            Path relative to Git work tree
        """
        path_obj = Path(path)
        path_str = str(path)
        
        debug_logger.log("DEBUG", "Converting path to Git context", 
                        input_path=path_str)
        
        # Handle absolute paths
        if path_obj.is_absolute():
            try:
                # Try to make it relative to .specs/ directory
                relative_path = path_obj.relative_to(self.specs_dir)
                result = str(relative_path)
                debug_logger.log("DEBUG", "Converted absolute path", 
                               absolute=path_str, relative=result)
                return result
            except ValueError:
                # Path is not under .specs/, return as-is
                debug_logger.log("DEBUG", "Absolute path not under .specs/, returning as-is", 
                               path=path_str)
                return path_str
        
        # Handle .specs/ prefixed paths
        if path_str.startswith(".specs/"):
            result = path_str.replace(".specs/", "", 1)
            debug_logger.log("DEBUG", "Removed .specs/ prefix", 
                           original=path_str, result=result)
            return result
        
        # Handle .specs\ prefixed paths (Windows)
        if path_str.startswith(".specs\\"):
            result = path_str.replace(".specs\\", "", 1).replace("\\", "/")
            debug_logger.log("DEBUG", "Removed .specs\\ prefix and normalized", 
                           original=path_str, result=result)
            return result
        
        # Path is already relative, return as-is (but normalize separators)
        result = str(path_obj).replace("\\", "/")
        debug_logger.log("DEBUG", "Path already relative, normalized separators", 
                        original=path_str, result=result)
        return result
    
    def convert_from_git_path(self, git_path: Union[str, Path]) -> Path:
        """Convert path from Git work tree context to .specs/ prefixed path.
        
        Args:
            git_path: Path relative to Git work tree
            
        Returns:
            Path with .specs/ prefix
        """
        git_path_str = str(git_path)
        
        debug_logger.log("DEBUG", "Converting from Git context", 
                        git_path=git_path_str)
        
        # Normalize path separators
        normalized_path = git_path_str.replace("\\", "/")
        
        # Add .specs/ prefix if not already present
        if not normalized_path.startswith(".specs/"):
            result = Path(".specs") / normalized_path
        else:
            result = Path(normalized_path)
        
        debug_logger.log("DEBUG", "Converted from Git context", 
                        git_path=git_path_str, result=str(result))
        
        return result
    
    def convert_to_absolute_specs_path(self, path: Union[str, Path]) -> Path:
        """Convert path to absolute path under .specs/ directory.
        
        Args:
            path: Path to convert
            
        Returns:
            Absolute path under .specs/ directory
        """
        path_str = str(path)
        
        debug_logger.log("DEBUG", "Converting to absolute .specs/ path", 
                        input_path=path_str)
        
        # Convert to Git path first (removes .specs/ prefix if present)
        git_path = self.convert_to_git_path(path)
        
        # Create absolute path under .specs/
        absolute_path = self.specs_dir / git_path
        
        debug_logger.log("DEBUG", "Converted to absolute .specs/ path", 
                        input_path=path_str, 
                        git_path=git_path,
                        absolute=str(absolute_path))
        
        return absolute_path
    
    def is_under_specs_dir(self, path: Union[str, Path]) -> bool:
        """Check if path is under the .specs/ directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is under .specs/ directory
        """
        path_obj = Path(path)
        
        # Convert to absolute path if relative
        if not path_obj.is_absolute():
            # Try to interpret as relative to .specs/
            test_path = self.specs_dir / path_obj
        else:
            test_path = path_obj
        
        try:
            test_path.relative_to(self.specs_dir)
            debug_logger.log("DEBUG", "Path is under .specs/ directory", 
                           path=str(path))
            return True
        except ValueError:
            debug_logger.log("DEBUG", "Path is not under .specs/ directory", 
                           path=str(path))
            return False
    
    def normalize_path_separators(self, path: Union[str, Path]) -> str:
        """Normalize path separators to forward slashes.
        
        Args:
            path: Path to normalize
            
        Returns:
            Path with normalized separators
        """
        normalized = str(path).replace("\\", "/")
        debug_logger.log("DEBUG", "Normalized path separators", 
                        original=str(path), normalized=normalized)
        return normalized
    
    def get_conversion_info(self, path: Union[str, Path]) -> dict:
        """Get detailed information about path conversion.
        
        Args:
            path: Path to analyze
            
        Returns:
            Dictionary with conversion information
        """
        path_str = str(path)
        path_obj = Path(path)
        
        info = {
            "original_path": path_str,
            "is_absolute": path_obj.is_absolute(),
            "has_specs_prefix": path_str.startswith((".specs/", ".specs\\")),
            "is_under_specs_dir": self.is_under_specs_dir(path),
            "git_path": self.convert_to_git_path(path),
            "specs_prefixed_path": str(self.convert_from_git_path(self.convert_to_git_path(path))),
            "absolute_specs_path": str(self.convert_to_absolute_specs_path(path)),
            "normalized_separators": self.normalize_path_separators(path),
        }
        
        debug_logger.log("DEBUG", "Path conversion info generated", 
                        original=path_str, conversions=len(info))
        
        return info
```

## Test Requirements

Create comprehensive tests for the Git operations system:

### Test Cases (25 tests total)

**GitOperations Tests:**
1. **test_git_operations_prepares_environment_correctly**
2. **test_git_operations_executes_commands_successfully**
3. **test_git_operations_handles_command_failures**
4. **test_git_operations_handles_missing_git_binary**
5. **test_git_operations_initializes_repository**
6. **test_git_operations_checks_git_availability**
7. **test_git_operations_gets_git_version**
8. **test_git_operations_logs_command_execution**

**SpecGitRepository Tests:**
9. **test_spec_git_repository_adds_files_with_force_flag**
10. **test_spec_git_repository_converts_paths_for_add**
11. **test_spec_git_repository_creates_commits**
12. **test_spec_git_repository_shows_status**
13. **test_spec_git_repository_shows_log_with_path_filter**
14. **test_spec_git_repository_shows_diff_with_path_filter**
15. **test_spec_git_repository_detects_initialization_status**
16. **test_spec_git_repository_initializes_repository**
17. **test_spec_git_repository_gets_repository_info**

**GitPathConverter Tests:**
18. **test_path_converter_converts_absolute_paths**
19. **test_path_converter_removes_specs_prefix**
20. **test_path_converter_handles_windows_separators**
21. **test_path_converter_converts_from_git_context**
22. **test_path_converter_creates_absolute_specs_paths**
23. **test_path_converter_detects_paths_under_specs_dir**
24. **test_path_converter_normalizes_path_separators**
25. **test_path_converter_provides_conversion_info**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/git/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/git/ --cov=spec_cli.git --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/git/

# Check code formatting
poetry run ruff check spec_cli/git/
poetry run ruff format spec_cli/git/

# Verify imports work correctly
python -c "from spec_cli.git import SpecGitRepository, GitOperations, GitPathConverter; print('Import successful')"

# Test Git availability check
python -c "
from spec_cli.git import GitOperations
from pathlib import Path

ops = GitOperations(Path('.spec'), Path('.specs'), Path('.spec-index'))
available = ops.check_git_available()
print(f'Git available: {available}')

if available:
    version = ops.get_git_version()
    print(f'Git version: {version}')
else:
    print('Git not found - install Git to use spec CLI')
"

# Test path conversion functionality
python -c "
from spec_cli.git import GitPathConverter
from pathlib import Path

converter = GitPathConverter(Path('.specs'))

test_paths = [
    'src/main.py',
    '.specs/src/main.py',
    Path.cwd() / '.specs' / 'src' / 'main.py',
    'docs/README.md'
]

for path in test_paths:
    git_path = converter.convert_to_git_path(path)
    specs_path = converter.convert_from_git_path(git_path)
    absolute_path = converter.convert_to_absolute_specs_path(path)
    
    print(f'Original: {path}')
    print(f'  Git path: {git_path}')
    print(f'  Specs path: {specs_path}')
    print(f'  Absolute: {absolute_path}')
    print()
"

# Test repository interface
python -c "
from spec_cli.git import SpecGitRepository
from pathlib import Path

# Test with current directory settings
try:
    repo = SpecGitRepository()
    info = repo.get_repository_info()
    print('Repository info:')
    for key, value in info.items():
        print(f'  {key}: {value}')
    
    print(f'Initialized: {repo.is_initialized()}')
    
except Exception as e:
    print(f'Repository test failed: {e}')
"

# Test Git environment preparation
python -c "
from spec_cli.git import GitOperations
from pathlib import Path
import os

ops = GitOperations(Path('.spec'), Path('.specs'), Path('.spec-index'))
env = ops._prepare_git_environment()

print('Git environment variables:')
git_vars = {k: v for k, v in env.items() if k.startswith('GIT_')}
for key, value in git_vars.items():
    print(f'  {key}: {value}')
"
```

## Definition of Done

- [ ] `GitRepository` abstract interface defining all Git operations
- [ ] `SpecGitRepository` implementation with isolated repository support
- [ ] `GitOperations` class for low-level Git command execution
- [ ] `GitPathConverter` for comprehensive path handling
- [ ] Git environment setup with proper isolation
- [ ] Git availability checking and version detection
- [ ] Comprehensive error handling for all Git scenarios
- [ ] Path conversion between different Git contexts
- [ ] All 25 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with settings and logging systems
- [ ] Repository initialization and status detection

## Next Slice Preparation

This slice enables **slice-10-spec-repository.md** by providing:
- `SpecGitRepository` for all Git operations
- `GitPathConverter` for path handling
- Git environment management and command execution
- Repository initialization and status checking

The spec repository slice will use these Git operations to provide the high-level orchestration of spec operations.