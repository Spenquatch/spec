# Code Refactoring Plan: Eliminate Duplicate Code

## Overview

This plan addresses duplicate code and architectural issues identified in the comprehensive codebase audit. We'll work in vertical slices, implementing one improvement at a time with full testing and validation.

## Implementation Strategy

**Vertical Slice Approach**: Complete each slice from implementation → testing → validation before moving to the next slice.

**Quality Gates**: Every slice must pass:
- Unit tests with 80%+ coverage
- Type checking with mypy
- Linting with ruff
- Pre-commit hooks

---

## PHASE 1: Critical Foundation Utilities (HIGH PRIORITY)

### Slice 1.1: Create Centralized Error Handling Utilities

**Goal**: Eliminate duplicate try/catch patterns and error message formatting across 15+ modules.

**Scope**:
- Create `spec_cli/utils/error_handling.py` with common error patterns
- Focus on `OSError`, `CalledProcessError`, and `SpecError` handling
- Does NOT include complex workflow error handling

#### **New Files and Components**

**1. File: `spec_cli/utils/__init__.py`**
```python
"""Utility modules for common operations."""
```

**2. File: `spec_cli/utils/error_handling.py`**

**Functions/Classes to Create:**

**A. `handle_os_error` decorator**
- **Parameters**: `operation: str, reraise_as: type[Exception] = SpecFileError`
- **Returns**: `Callable[[Callable], Callable]`
- **Purpose**: Decorator that catches OSError and reraises as SpecError with context

**B. `handle_subprocess_error` decorator**
- **Parameters**: `operation: str, command_info: bool = True`
- **Returns**: `Callable[[Callable], Callable]`
- **Purpose**: Decorator for Git subprocess operations with detailed error context

**C. `create_error_context` function**
- **Parameters**: `operation: str, **kwargs: Any`
- **Returns**: `Dict[str, Any]`
- **Purpose**: Standardized error context dictionary creation

**D. `ErrorHandler` class**
- **Methods**: `log_and_raise`, `format_error_message`, `add_context`
- **Purpose**: Centralized error handling with consistent logging and formatting

#### **✅ Good Example (Best Practices)**

```python
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar
import subprocess
from pathlib import Path

from ..exceptions import SpecFileError, SpecGitError
from ..logging.debug import debug_logger

F = TypeVar('F', bound=Callable[..., Any])

def handle_os_error(
    operation: str,
    reraise_as: Type[Exception] = SpecFileError,
    include_path: bool = True
) -> Callable[[F], F]:
    """Decorator to handle OSError with consistent logging and context.

    Args:
        operation: Human-readable operation description
        reraise_as: Exception type to raise (must inherit from SpecError)
        include_path: Whether to include file path in error context

    Returns:
        Decorated function with error handling

    Raises:
        TypeError: If reraise_as is not a SpecError subclass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except OSError as e:
                context = create_error_context(
                    operation=operation,
                    function=func.__name__,
                    args_count=len(args),
                    os_error=str(e),
                    errno=getattr(e, 'errno', None)
                )

                # Add path context if available and requested
                if include_path and args:
                    first_arg = args[0]
                    if isinstance(first_arg, (str, Path)):
                        context['path'] = str(first_arg)

                error_msg = f"Failed to {operation}: {e}"
                debug_logger.log("ERROR", error_msg, **context)
                raise reraise_as(error_msg, context) from e
        return wrapper
    return decorator

def handle_subprocess_error(
    operation: str,
    include_command: bool = True
) -> Callable[[F], F]:
    """Decorator for subprocess operations with detailed error context."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except subprocess.CalledProcessError as e:
                context = create_error_context(
                    operation=operation,
                    return_code=e.returncode,
                    stdout=e.stdout.decode() if e.stdout else None,
                    stderr=e.stderr.decode() if e.stderr else None
                )

                if include_command and hasattr(e, 'cmd'):
                    context['command'] = ' '.join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)

                error_msg = f"Command failed during {operation}"
                if e.stderr:
                    error_msg += f": {e.stderr.decode().strip()}"

                debug_logger.log("ERROR", error_msg, **context)
                raise SpecGitError(error_msg, context) from e
        return wrapper
    return decorator

def create_error_context(operation: str, **kwargs: Any) -> Dict[str, Any]:
    """Create standardized error context dictionary."""
    context = {
        'operation': operation,
        'timestamp': debug_logger._get_timestamp(),
    }

    # Filter out None values and add provided context
    for key, value in kwargs.items():
        if value is not None:
            context[key] = value

    return context

class ErrorHandler:
    """Centralized error handling with consistent patterns."""

    def __init__(self, default_context: Optional[Dict[str, Any]] = None):
        self.default_context = default_context or {}

    def log_and_raise(
        self,
        error: Exception,
        operation: str,
        reraise_as: Type[Exception] = SpecFileError,
        **additional_context: Any
    ) -> None:
        """Log error with context and reraise as specified type."""
        context = {**self.default_context, **additional_context}
        context.update(create_error_context(operation, original_error=str(error)))

        error_msg = f"Failed to {operation}: {error}"
        debug_logger.log("ERROR", error_msg, **context)
        raise reraise_as(error_msg, context) from error
```

#### **Required Tests**

**File: `tests/unit/utils/test_error_handling.py`**

**Test Functions Needed:**
```python
class TestHandleOsError:
    def test_handle_os_error_when_no_error_then_returns_result(self)
    def test_handle_os_error_when_os_error_then_reraises_as_spec_error(self)
    def test_handle_os_error_when_custom_exception_type_then_uses_custom_type(self)
    def test_handle_os_error_when_path_in_args_then_includes_path_context(self)
    def test_handle_os_error_when_include_path_false_then_excludes_path(self)

class TestHandleSubprocessError:
    def test_handle_subprocess_error_when_success_then_returns_result(self)
    def test_handle_subprocess_error_when_called_process_error_then_reraises_git_error(self)
    def test_handle_subprocess_error_when_stderr_present_then_includes_stderr(self)
    def test_handle_subprocess_error_when_include_command_false_then_excludes_command(self)

class TestCreateErrorContext:
    def test_create_error_context_when_called_then_includes_operation_and_timestamp(self)
    def test_create_error_context_when_kwargs_provided_then_includes_all_values(self)
    def test_create_error_context_when_none_values_then_filters_none(self)

class TestErrorHandler:
    def test_error_handler_when_default_context_then_includes_in_all_errors(self)
    def test_log_and_raise_when_called_then_logs_and_reraises_correctly(self)
```

**Required Mocks and Fixtures:**
```python
@pytest.fixture
def mock_debug_logger():
    return Mock(spec=['log'])

@pytest.fixture
def sample_os_error():
    return OSError("Permission denied")

@pytest.fixture
def sample_subprocess_error():
    return subprocess.CalledProcessError(1, ['git', 'status'], stderr=b"fatal: not a git repository")
```

**Files to Create/Modify**:
- `spec_cli/utils/__init__.py` (new)
- `spec_cli/utils/error_handling.py` (new)
- `tests/unit/utils/test_error_handling.py` (new)
- Update: `spec_cli/git/operations.py`, `spec_cli/file_system/directory_manager.py`

---

### Slice 1.2: Consolidate Path Operations

**Goal**: Create centralized utilities for common path operations (relative_to, mkdir patterns).

**Scope**:
- Add utilities to `spec_cli/file_system/path_utils.py`
- Focus on try/except patterns for `relative_to()` operations
- Standardize directory creation patterns

#### **New Functions in `spec_cli/file_system/path_utils.py`**

**A. `safe_relative_to` function**
- **Parameters**: `path: Union[str, Path], root: Union[str, Path], strict: bool = True`
- **Returns**: `Path`
- **Purpose**: Safe relative_to with consistent error handling

**B. `safe_mkdir` function**
- **Parameters**: `path: Union[str, Path], parents: bool = True, exist_ok: bool = True, mode: int = 0o755`
- **Returns**: `Path`
- **Purpose**: Directory creation with error handling and logging

**C. `normalize_path` function**
- **Parameters**: `path: Union[str, Path], resolve_symlinks: bool = False`
- **Returns**: `Path`
- **Purpose**: Consistent path normalization across platforms

#### **✅ Good Example (Best Practices)**

```python
from pathlib import Path
from typing import Union
import os

from ..exceptions import SpecValidationError, SpecFileError
from ..logging.debug import debug_logger
from .error_handling import handle_os_error

def safe_relative_to(
    path: Union[str, Path],
    root: Union[str, Path],
    strict: bool = True
) -> Path:
    """Safely compute relative path with consistent error handling."""
    if not isinstance(path, (str, Path)):
        raise TypeError(f"path must be str or Path, got {type(path)}")
    if not isinstance(root, (str, Path)):
        raise TypeError(f"root must be str or Path, got {type(root)}")

    path_obj = Path(path).resolve()
    root_obj = Path(root).resolve()

    try:
        relative = path_obj.relative_to(root_obj)
        debug_logger.log(
            "DEBUG",
            "Successfully computed relative path",
            original_path=str(path_obj),
            root_path=str(root_obj),
            relative_path=str(relative)
        )
        return relative

    except ValueError as e:
        if strict:
            error_msg = f"Path '{path_obj}' is outside root '{root_obj}'"
            debug_logger.log(
                "ERROR",
                error_msg,
                path=str(path_obj),
                root=str(root_obj),
                strict=strict
            )
            raise SpecValidationError(error_msg) from e

        # Non-strict mode: return original path
        debug_logger.log(
            "WARNING",
            "Path outside root, returning original path",
            path=str(path_obj),
            root=str(root_obj)
        )
        return path_obj

@handle_os_error("create directory")
def safe_mkdir(
    path: Union[str, Path],
    parents: bool = True,
    exist_ok: bool = True,
    mode: int = 0o755
) -> Path:
    """Safely create directory with consistent error handling."""
    if not isinstance(path, (str, Path)):
        raise TypeError(f"path must be str or Path, got {type(path)}")

    path_obj = Path(path)

    # Check if already exists and handle accordingly
    if path_obj.exists():
        if path_obj.is_dir():
            if exist_ok:
                debug_logger.log("DEBUG", "Directory already exists", path=str(path_obj))
                return path_obj
            else:
                raise SpecFileError(f"Directory already exists: {path_obj}")
        else:
            raise SpecFileError(f"Path exists but is not a directory: {path_obj}")

    # Create directory with specified permissions
    path_obj.mkdir(parents=parents, exist_ok=exist_ok, mode=mode)

    debug_logger.log(
        "INFO",
        "Directory created successfully",
        path=str(path_obj),
        parents=parents,
        mode=oct(mode)
    )

    return path_obj

def normalize_path(
    path: Union[str, Path],
    resolve_symlinks: bool = False
) -> Path:
    """Normalize path with consistent cross-platform handling."""
    if not isinstance(path, (str, Path)):
        raise TypeError(f"path must be str or Path, got {type(path)}")

    path_obj = Path(path)

    # Resolve symlinks if requested
    if resolve_symlinks:
        path_obj = path_obj.resolve()
    else:
        # Just normalize without resolving symlinks
        path_obj = path_obj.expanduser().absolute()

    debug_logger.log(
        "DEBUG",
        "Path normalized",
        original=str(path),
        normalized=str(path_obj),
        resolved_symlinks=resolve_symlinks
    )

    return path_obj
```

#### **Required Tests**

**File: `tests/unit/file_system/test_path_utils.py` (extend existing)**

**Additional Test Functions:**
```python
class TestSafeRelativeTo:
    def test_safe_relative_to_when_path_inside_root_then_returns_relative(self)
    def test_safe_relative_to_when_path_outside_root_and_strict_then_raises_error(self)
    def test_safe_relative_to_when_path_outside_root_and_not_strict_then_returns_original(self)
    def test_safe_relative_to_when_invalid_path_type_then_raises_type_error(self)

class TestSafeMkdir:
    def test_safe_mkdir_when_directory_not_exists_then_creates_successfully(self)
    def test_safe_mkdir_when_directory_exists_and_exist_ok_then_succeeds(self)
    def test_safe_mkdir_when_directory_exists_and_not_exist_ok_then_raises_error(self)
    def test_safe_mkdir_when_path_is_file_then_raises_error(self)

class TestNormalizePath:
    def test_normalize_path_when_relative_path_then_returns_absolute(self)
    def test_normalize_path_when_symlink_and_resolve_then_follows_link(self)
    def test_normalize_path_when_symlink_and_not_resolve_then_preserves_link(self)
```

**Files to Create/Modify**:
- `spec_cli/file_system/path_utils.py` (extend existing)
- `tests/unit/file_system/test_path_utils.py` (extend existing)
- Update: `spec_cli/file_system/directory_traversal.py`, `spec_cli/file_system/file_metadata.py`

---

### Slice 1.3: Create CLI Command Base Class

**Goal**: Eliminate duplicate argument validation and setup patterns across CLI commands.

**Scope**:
- Create base command class with common patterns
- Focus on file path validation, error handling, and setup
- Does NOT include complex workflow logic

#### **New File: `spec_cli/cli/base_command.py`**

**A. `BaseCommand` class**
- **Methods**: `validate_files`, `setup_console`, `handle_dry_run`, `execute`
- **Purpose**: Common CLI command patterns and validation

**B. `CommandContext` dataclass**
- **Fields**: `console`, `debug`, `verbose`, `dry_run`, `force`
- **Purpose**: Shared command context

#### **✅ Good Example (Best Practices)**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Any

import click
from rich.console import Console

from ..utils.error_handling import ErrorHandler
from ..ui.console import get_console
from ..ui.error_display import show_message
from ..utils import validate_file_paths
from ..logging.debug import debug_logger

@dataclass
class CommandContext:
    """Shared context for CLI commands."""
    console: Console
    debug: bool
    verbose: bool
    dry_run: bool = False
    force: bool = False

    def __post_init__(self) -> None:
        """Validate context after initialization."""
        if not isinstance(self.console, Console):
            raise TypeError("console must be Rich Console instance")

class BaseCommand(ABC):
    """Base class for CLI commands with common patterns."""

    def __init__(self, context: CommandContext):
        """Initialize command with context."""
        if not isinstance(context, CommandContext):
            raise TypeError("context must be CommandContext instance")

        self.context = context
        self.error_handler = ErrorHandler(default_context={
            'command': self.__class__.__name__,
            'debug': context.debug,
            'verbose': context.verbose
        })

    def validate_files(
        self,
        file_paths: Tuple[str, ...],
        require_exists: bool = True,
        min_files: int = 1
    ) -> List[Path]:
        """Validate and convert file paths with consistent error handling."""
        try:
            validated_paths = validate_file_paths(
                list(file_paths),
                require_exists=require_exists
            )

            if len(validated_paths) < min_files:
                raise click.BadParameter(
                    f"At least {min_files} file(s) required, got {len(validated_paths)}"
                )

            debug_logger.log(
                "INFO",
                "File paths validated successfully",
                file_count=len(validated_paths),
                paths=[str(p) for p in validated_paths]
            )

            return validated_paths

        except Exception as e:
            self.error_handler.log_and_raise(
                e,
                "validate file paths",
                reraise_as=click.BadParameter,
                file_paths=list(file_paths),
                require_exists=require_exists
            )

    def handle_dry_run(self, operation_name: str, preview_data: Any) -> bool:
        """Handle dry run mode with consistent messaging."""
        if not self.context.dry_run:
            return True

        self.context.console.print(f"\n[bold cyan]Dry Run Preview: {operation_name}[/bold cyan]")

        # Display preview data based on type
        if isinstance(preview_data, dict):
            for key, value in preview_data.items():
                self.context.console.print(f"  {key}: [yellow]{value}[/yellow]")
        elif isinstance(preview_data, (list, tuple)):
            for item in preview_data:
                self.context.console.print(f"  • [yellow]{item}[/yellow]")
        else:
            self.context.console.print(f"  [yellow]{preview_data}[/yellow]")

        show_message("This is a dry run. No changes would be made.", "info")
        return False

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> None:
        """Execute the command. Must be implemented by subclasses."""
        pass

    def run_with_error_handling(self, *args: Any, **kwargs: Any) -> None:
        """Execute command with consistent error handling."""
        try:
            self.setup_console()
            self.execute(*args, **kwargs)

        except click.BadParameter:
            raise  # Re-raise click parameter errors
        except Exception as e:
            self.error_handler.log_and_raise(
                e,
                f"execute {self.__class__.__name__}",
                reraise_as=click.ClickException,
                args=args,
                kwargs=kwargs
            )

def create_command_context(
    debug: bool,
    verbose: bool,
    dry_run: bool = False,
    force: bool = False
) -> CommandContext:
    """Create command context with validation."""
    console = get_console()

    return CommandContext(
        console=console,
        debug=debug,
        verbose=verbose,
        dry_run=dry_run,
        force=force
    )
```

#### **Required Tests**

**File: `tests/unit/cli/test_base_command.py`**

**Test Functions:**
```python
class TestCommandContext:
    def test_command_context_when_valid_params_then_creates_successfully(self)
    def test_command_context_when_invalid_console_then_raises_type_error(self)

class TestBaseCommand:
    def test_base_command_when_valid_context_then_initializes_successfully(self)
    def test_validate_files_when_valid_paths_then_returns_path_objects(self)
    def test_validate_files_when_insufficient_files_then_raises_bad_parameter(self)
    def test_handle_dry_run_when_dry_run_true_then_shows_preview_and_returns_false(self)
    def test_handle_dry_run_when_dry_run_false_then_returns_true(self)
    def test_run_with_error_handling_when_exception_then_converts_to_click_exception(self)
```

**Files to Create/Modify**:
- `spec_cli/cli/base_command.py` (new)
- `tests/unit/cli/test_base_command.py` (new)
- Update: `spec_cli/cli/commands/add.py`, `spec_cli/cli/commands/gen.py`

---

## PHASE 2: Configuration and Architecture (MEDIUM PRIORITY)

### Slice 2.1: Fix Configuration Singleton Pattern

**Goal**: Consolidate the 3 different singleton implementations into a reusable pattern.

**Context**: Currently there are 3 different singleton implementations in settings.py, theme.py, and console.py with inconsistent patterns and missing thread safety.

**Scope**:
- Create `spec_cli/utils/singleton.py` with thread-safe singleton decorator
- Update SpecSettings, theme, and console to use common pattern
- Fix missing configuration attributes
- Does NOT include complex workflow singletons

#### **New Files and Components**

**1. File: `spec_cli/utils/singleton.py`**

**Functions/Classes to Create:**

**A. `singleton` decorator**
- **Parameters**: `cls: Type[T]`
- **Returns**: `Type[T]`
- **Purpose**: Thread-safe singleton decorator with instance caching

**B. `SingletonMeta` metaclass**
- **Parameters**: `name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]`
- **Returns**: `SingletonMeta`
- **Purpose**: Alternative metaclass-based singleton implementation

**C. `reset_singleton` function**
- **Parameters**: `cls: Type[Any]`
- **Returns**: `None`
- **Purpose**: Reset singleton instance for testing

#### **✅ Good Example (Best Practices)**

```python
import threading
from typing import Any, Dict, Type, TypeVar, cast
from functools import wraps

T = TypeVar('T')

# Thread-safe singleton instances storage
_instances: Dict[Type[Any], Any] = {}
_instance_locks: Dict[Type[Any], threading.Lock] = {}
_global_lock = threading.Lock()

def singleton(cls: Type[T]) -> Type[T]:
    """Thread-safe singleton decorator.

    Args:
        cls: Class to make singleton

    Returns:
        Decorated class with singleton behavior

    Raises:
        TypeError: If cls is not a class

    Example:
        @singleton
        class MyService:
            def __init__(self):
                self.initialized = True
    """
    if not isinstance(cls, type):
        raise TypeError("singleton can only be applied to classes")

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        """Get or create singleton instance with thread safety."""
        if cls not in _instances:
            with _global_lock:
                if cls not in _instances:
                    _instance_locks[cls] = threading.Lock()
                    instance = cls(*args, **kwargs)
                    _instances[cls] = instance

        return cast(T, _instances[cls])

    # Preserve class metadata
    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    get_instance.__module__ = cls.__module__
    get_instance.__qualname__ = cls.__qualname__

    # Add class attributes for introspection
    get_instance._original_class = cls  # type: ignore
    get_instance._is_singleton = True  # type: ignore

    return cast(Type[T], get_instance)

class SingletonMeta(type):
    """Metaclass-based singleton implementation."""

    _instances: Dict[Type[Any], Any] = {}
    _locks: Dict[Type[Any], threading.Lock] = {}
    _global_lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Thread-safe instance creation."""
        if cls not in cls._instances:
            with cls._global_lock:
                if cls not in cls._instances:
                    cls._locks[cls] = threading.Lock()
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance

        return cls._instances[cls]

def reset_singleton(cls: Type[Any]) -> None:
    """Reset singleton instance for testing purposes."""
    if not hasattr(cls, '_is_singleton') and not isinstance(cls, SingletonMeta):
        raise ValueError(f"Class {cls.__name__} is not a singleton")

    with _global_lock:
        if cls in _instances:
            del _instances[cls]
        if cls in _instance_locks:
            del _instance_locks[cls]
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Not thread-safe, mutable class variable
class BadSingleton:
    _instance = None  # Race condition possible

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # No thread safety
        return cls._instance

# BAD: Missing type hints and error handling
def bad_singleton(cls):
    instance = None
    def get_instance():
        nonlocal instance
        if instance is None:
            instance = cls()  # No args/kwargs support
        return instance
    return get_instance
```

#### **Required Tests**

**File: `tests/unit/utils/test_singleton.py`**

**Test Functions Needed:**
```python
class TestSingletonDecorator:
    def test_singleton_when_multiple_calls_then_returns_same_instance(self)
    def test_singleton_when_concurrent_access_then_thread_safe(self)
    def test_singleton_when_different_classes_then_separate_instances(self)
    def test_singleton_when_reset_then_creates_new_instance(self)
    def test_singleton_when_applied_to_non_class_then_raises_type_error(self)

class TestSingletonMeta:
    def test_singleton_meta_when_inheritance_then_separate_instances_per_class(self)
    def test_singleton_meta_when_multiple_instances_then_returns_same(self)
    def test_singleton_meta_when_reset_instance_then_creates_new(self)

class TestSingletonUtilities:
    def test_reset_singleton_when_valid_singleton_then_resets_successfully(self)
    def test_reset_singleton_when_not_singleton_then_raises_value_error(self)
    def test_is_singleton_when_singleton_class_then_returns_true(self)
    def test_is_singleton_when_regular_class_then_returns_false(self)
    def test_get_singleton_info_when_active_instances_then_returns_statistics(self)
```

**Required Mocks and Fixtures:**
```python
@pytest.fixture
def sample_singleton_class():
    @singleton
    class TestClass:
        def __init__(self, value: int = 42):
            self.value = value
    return TestClass

@pytest.fixture
def sample_metaclass_singleton():
    class TestMeta(SingletonMeta):
        def __init__(self, name: str = "test"):
            self.name = name
    return TestMeta

@pytest.fixture
def thread_pool():
    return concurrent.futures.ThreadPoolExecutor(max_workers=10)
```

**Files to Create/Modify**:
- `spec_cli/utils/singleton.py` (new)
- `tests/unit/utils/test_singleton.py` (new)
- Update: `spec_cli/config/settings.py`, `spec_cli/ui/theme.py`, `spec_cli/ui/console.py`

---

### Slice 2.2: Consolidate Environment Variable Handling

**Goal**: Centralize all environment variable reading in settings.py.

**Context**: Currently environment variables are read directly in debug.py and inconsistently throughout the codebase, causing circular dependencies.

**Scope**:
- Move environment variable parsing from `debug.py` to `settings.py`
- Create centralized environment variable utilities
- Fix circular dependencies between settings/logging/ui
- Does NOT include complex application-specific environment handling

#### **New Functions in `spec_cli/config/settings.py`**

**A. `get_env_bool` function**
- **Parameters**: `key: str, default: bool = False, true_values: Set[str] = None`
- **Returns**: `bool`
- **Purpose**: Parse boolean environment variables with flexible true value detection

**B. `get_env_int` function**
- **Parameters**: `key: str, default: int = 0, min_value: Optional[int] = None, max_value: Optional[int] = None`
- **Returns**: `int`
- **Purpose**: Parse integer environment variables with validation

**C. `get_env_string` function**
- **Parameters**: `key: str, default: str = "", allowed_values: Optional[Set[str]] = None`
- **Returns**: `str`
- **Purpose**: Parse string environment variables with allowed value validation

**D. `EnvironmentConfig` dataclass**
- **Fields**: `debug_enabled`, `debug_level`, `debug_timing`, `log_level`
- **Purpose**: Centralized environment configuration

#### **✅ Good Example (Best Practices)**

```python
import os
from dataclasses import dataclass
from typing import Optional, Set, Union, Any, Dict
from enum import Enum

from ..logging.debug import debug_logger

class LogLevel(Enum):
    """Valid log levels for environment configuration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

DEFAULT_TRUE_VALUES: Set[str] = {"1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"}

def get_env_bool(
    key: str,
    default: bool = False,
    true_values: Optional[Set[str]] = None
) -> bool:
    """Parse boolean environment variable with flexible true value detection.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        true_values: Set of values considered True (uses defaults if None)

    Returns:
        Parsed boolean value

    Raises:
        TypeError: If key is not a string

    Example:
        debug_enabled = get_env_bool("SPEC_DEBUG", False)
        timing_enabled = get_env_bool("SPEC_TIMING", True, {"1", "enabled"})
    """
    if not isinstance(key, str):
        raise TypeError("Environment variable key must be a string")

    if true_values is None:
        true_values = DEFAULT_TRUE_VALUES

    value = os.environ.get(key)
    if value is None:
        debug_logger.log(
            "DEBUG",
            "Environment variable not set, using default",
            key=key,
            default=default
        )
        return default

    # Handle empty string as False
    if not value.strip():
        debug_logger.log(
            "DEBUG",
            "Environment variable empty, treating as False",
            key=key
        )
        return False

    result = value in true_values
    debug_logger.log(
        "DEBUG",
        "Environment boolean parsed",
        key=key,
        value=value,
        result=result
    )

    return result

def get_env_int(
    key: str,
    default: int = 0,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None
) -> int:
    """Parse integer environment variable with validation.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        Parsed integer value

    Raises:
        TypeError: If key is not a string
        ValueError: If min_value > max_value

    Example:
        timeout = get_env_int("SPEC_TIMEOUT", 30, min_value=1, max_value=300)
        workers = get_env_int("SPEC_WORKERS", 4, min_value=1)
    """
    if not isinstance(key, str):
        raise TypeError("Environment variable key must be a string")

    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError(f"min_value ({min_value}) cannot be greater than max_value ({max_value})")

    value = os.environ.get(key)
    if value is None:
        debug_logger.log(
            "DEBUG",
            "Environment variable not set, using default",
            key=key,
            default=default
        )
        return default

    try:
        parsed_value = int(value.strip())

        # Validate range
        if min_value is not None and parsed_value < min_value:
            debug_logger.log(
                "WARNING",
                "Environment variable below minimum, using default",
                key=key,
                value=parsed_value,
                min_value=min_value,
                default=default
            )
            return default

        if max_value is not None and parsed_value > max_value:
            debug_logger.log(
                "WARNING",
                "Environment variable above maximum, using default",
                key=key,
                value=parsed_value,
                max_value=max_value,
                default=default
            )
            return default

        debug_logger.log(
            "DEBUG",
            "Environment integer parsed",
            key=key,
            value=parsed_value
        )

        return parsed_value

    except ValueError as e:
        debug_logger.log(
            "WARNING",
            "Environment variable not a valid integer, using default",
            key=key,
            value=value,
            default=default,
            error=str(e)
        )
        return default

@dataclass
class EnvironmentConfig:
    """Centralized environment configuration."""
    debug_enabled: bool
    debug_level: str
    debug_timing: bool
    log_level: str
    max_workers: int
    timeout_seconds: int

    @classmethod
    def from_environment(cls) -> 'EnvironmentConfig':
        """Create configuration from environment variables."""
        return cls(
            debug_enabled=get_env_bool("SPEC_DEBUG", False),
            debug_level=get_env_string(
                "SPEC_DEBUG_LEVEL",
                "INFO",
                allowed_values={e.value for e in LogLevel}
            ),
            debug_timing=get_env_bool("SPEC_DEBUG_TIMING", False),
            log_level=get_env_string(
                "SPEC_LOG_LEVEL",
                "WARNING",
                allowed_values={e.value for e in LogLevel}
            ),
            max_workers=get_env_int("SPEC_MAX_WORKERS", 4, min_value=1, max_value=16),
            timeout_seconds=get_env_int("SPEC_TIMEOUT", 30, min_value=1, max_value=300)
        )
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Direct os.environ access without validation
import os
debug_enabled = bool(os.environ.get("SPEC_DEBUG"))  # Wrong: "false" -> True

# BAD: Inconsistent parsing logic scattered across modules
def get_debug_flag():
    value = os.environ.get("SPEC_DEBUG", "false").lower()
    return value in ["true", "1", "yes"]  # Different logic each time

# BAD: No error handling or logging
def get_timeout():
    return int(os.environ["SPEC_TIMEOUT"])  # Can crash on missing/invalid
```

#### **Required Tests**

**File: `tests/unit/config/test_environment_variables.py`**

**Test Functions Needed:**
```python
class TestGetEnvBool:
    def test_get_env_bool_when_true_values_then_returns_true(self)
    def test_get_env_bool_when_false_values_then_returns_false(self)
    def test_get_env_bool_when_not_set_then_returns_default(self)
    def test_get_env_bool_when_custom_true_values_then_uses_custom_set(self)
    def test_get_env_bool_when_empty_string_then_returns_false(self)
    def test_get_env_bool_when_invalid_key_type_then_raises_type_error(self)

class TestGetEnvInt:
    def test_get_env_int_when_valid_integer_then_returns_parsed_value(self)
    def test_get_env_int_when_within_range_then_returns_value(self)
    def test_get_env_int_when_below_minimum_then_returns_default(self)
    def test_get_env_int_when_above_maximum_then_returns_default(self)
    def test_get_env_int_when_invalid_integer_then_returns_default(self)
    def test_get_env_int_when_min_greater_than_max_then_raises_value_error(self)

class TestEnvironmentConfig:
    def test_environment_config_when_from_environment_then_parses_all_values(self)
    def test_environment_config_when_validate_then_returns_errors_for_invalid_values(self)
    def test_environment_config_when_to_dict_then_returns_complete_dictionary(self)
```

**Required Mocks and Fixtures:**
```python
@pytest.fixture
def clean_environment(monkeypatch):
    """Remove all SPEC_ environment variables for clean testing."""
    for key in list(os.environ.keys()):
        if key.startswith('SPEC_'):
            monkeypatch.delenv(key, raising=False)

@pytest.fixture
def mock_environment(monkeypatch):
    """Set up test environment variables."""
    test_vars = {
        'SPEC_DEBUG': 'true',
        'SPEC_DEBUG_LEVEL': 'INFO',
        'SPEC_TIMEOUT': '60'
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    return test_vars
```

**Files to Create/Modify**:
- Update: `spec_cli/config/settings.py`, `spec_cli/logging/debug.py`
- `tests/unit/config/test_environment_variables.py` (new)

---

### Slice 2.3: Unify Validation Patterns

**Goal**: Create base validator class to eliminate duplicate validation logic.

**Context**: Currently `ConfigurationValidator` and `TemplateValidator` have duplicate validation patterns with inconsistent error handling and return formats.

**Scope**:
- Extract common patterns from existing validators
- Create `spec_cli/utils/validation.py` with base validator
- Update existing validators to inherit from base
- Does NOT include domain-specific validation logic

#### **New File: `spec_cli/utils/validation.py`**

**A. `BaseValidator` class**
- **Methods**: `validate`, `add_error`, `add_warning`, `format_errors`, `is_valid`
- **Purpose**: Common validation patterns and error collection

**B. `ValidationResult` dataclass**
- **Fields**: `is_valid`, `errors`, `warnings`, `context`
- **Purpose**: Standardized validation result format

**C. `ValidationError` exception**
- **Parameters**: `message: str, errors: List[str], context: Dict[str, Any]`
- **Purpose**: Specialized validation exception

#### **✅ Good Example (Best Practices)**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Set
from pathlib import Path
import re

from ..exceptions import SpecError
from ..logging.debug import debug_logger

@dataclass
class ValidationResult:
    """Standardized validation result with errors, warnings, and context."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str, **context_data: Any) -> None:
        """Add validation error with optional context."""
        self.errors.append(message)
        self.is_valid = False

        # Add context data
        for key, value in context_data.items():
            self.context[f"error_{len(self.errors)}_{key}"] = value

    def add_warning(self, message: str, **context_data: Any) -> None:
        """Add validation warning with optional context."""
        self.warnings.append(message)

        # Add context data
        for key, value in context_data.items():
            self.context[f"warning_{len(self.warnings)}_{key}"] = value

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge another validation result into this one."""
        merged_context = {**self.context, **other.context}

        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            context=merged_context
        )

class ValidationError(SpecError):
    """Specialized validation exception with structured error information."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.errors = errors or []
        self.context = context or {}

class BaseValidator(ABC):
    """Base validator class with common validation patterns."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.result = ValidationResult(is_valid=True)

    @abstractmethod
    def validate_impl(self, data: Any) -> ValidationResult:
        """Implement specific validation logic."""
        pass

    def validate(self, data: Any, raise_on_error: bool = False) -> ValidationResult:
        """Validate data with error handling and logging."""
        debug_logger.log(
            "DEBUG",
            "Starting validation",
            validator=self.__class__.__name__,
            strict_mode=self.strict_mode
        )

        try:
            self.result = ValidationResult(is_valid=True)
            result = self.validate_impl(data)

            # Apply strict mode
            if self.strict_mode and result.warnings:
                for warning in result.warnings:
                    result.add_error(f"Warning treated as error: {warning}")
                result.warnings.clear()

            if not result.is_valid and raise_on_error:
                raise ValidationError(
                    f"Validation failed in {self.__class__.__name__}",
                    errors=result.errors,
                    context=result.context
                )

            return result

        except Exception as e:
            error_msg = f"Validation error in {self.__class__.__name__}: {e}"
            debug_logger.log("ERROR", error_msg)

            if raise_on_error:
                raise ValidationError(error_msg, context={"original_error": str(e)}) from e

            error_result = ValidationResult(is_valid=False)
            error_result.add_error(error_msg, original_error=str(e))
            return error_result

    def validate_required_string(
        self,
        value: Any,
        field_name: str,
        min_length: int = 1,
        max_length: Optional[int] = None
    ) -> bool:
        """Validate required string field with length constraints."""
        if value is None:
            self.result.add_error(f"{field_name} is required but not provided")
            return False

        if not isinstance(value, str):
            self.result.add_error(
                f"{field_name} must be a string, got {type(value).__name__}",
                actual_type=type(value).__name__,
                field_name=field_name
            )
            return False

        if len(value) < min_length:
            self.result.add_error(
                f"{field_name} must be at least {min_length} characters, got {len(value)}",
                min_length=min_length,
                actual_length=len(value)
            )
            return False

        return True
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Inconsistent error handling across validators
class BadValidator:
    def validate(self, data):
        errors = []  # Sometimes list, sometimes dict, sometimes string
        if not data.get("name"):
            errors.append("Name missing")  # No context
        return len(errors) == 0  # Returns bool instead of structured result

# BAD: No base class, duplicate patterns everywhere
class AnotherBadValidator:
    def check_stuff(self, thing):  # Inconsistent method names
        if not thing:
            print("Error!")  # Direct printing instead of logging
            return False
        return True
```

#### **Required Tests**

**File: `tests/unit/utils/test_validation.py`**

**Test Functions Needed:**
```python
class TestValidationResult:
    def test_validation_result_when_add_error_then_sets_invalid_and_stores_error(self)
    def test_validation_result_when_add_warning_then_stores_warning_keeps_valid(self)
    def test_validation_result_when_merge_then_combines_results_correctly(self)
    def test_validation_result_when_format_summary_then_creates_readable_output(self)

class TestValidationError:
    def test_validation_error_when_created_with_errors_then_formats_with_error_list(self)
    def test_validation_error_when_created_without_errors_then_uses_basic_format(self)

class TestBaseValidator:
    def test_base_validator_when_validate_required_string_valid_then_returns_true(self)
    def test_base_validator_when_validate_required_string_invalid_then_adds_error(self)
    def test_base_validator_when_validate_path_exists_then_returns_true(self)
    def test_base_validator_when_validate_path_missing_and_required_then_adds_error(self)
    def test_base_validator_when_strict_mode_then_treats_warnings_as_errors(self)
```

**Required Mocks and Fixtures:**
```python
@pytest.fixture
def sample_validator():
    class TestValidator(BaseValidator):
        def validate_impl(self, data):
            result = ValidationResult(is_valid=True)
            if not data.get("valid"):
                result.add_error("Data is invalid")
            return result
    return TestValidator()

@pytest.fixture
def invalid_data():
    return {"valid": False, "name": "test"}

@pytest.fixture
def valid_data():
    return {"valid": True, "name": "test"}
```

**Files to Create/Modify**:
- `spec_cli/utils/validation.py` (new)
- `tests/unit/utils/test_validation.py` (new)
- Update: `spec_cli/config/validation.py`, `spec_cli/templates/config.py`

---

## PHASE 3: Import Structure and Dependencies (LOW PRIORITY)

### Slice 3.1: Standardize Import Patterns

**Goal**: Establish consistent import style and fix architectural violations.

**Context**: Currently the codebase mixes absolute and relative imports, and core modules import UI components creating tight coupling.

**Scope**:
- Choose absolute vs relative import strategy
- Fix core modules importing UI components
- Create import aggregation modules for common imports
- Does NOT include external dependency reorganization

#### **New Files and Components**

**1. File: `spec_cli/common/__init__.py`**

**Functions/Classes to Create:**

**A. `ImportValidator` class**
- **Methods**: `validate_import_structure`, `check_circular_dependencies`, `analyze_coupling`
- **Purpose**: Validate import structure and detect architectural violations

**B. Common import aggregations**
- **Variables**: `CORE_IMPORTS`, `UI_IMPORTS`, `EXTERNAL_IMPORTS`
- **Purpose**: Centralized import management

#### **✅ Good Example (Best Practices)**

```python
# spec_cli/common/__init__.py
"""Common imports and utilities for consistent import management."""

from typing import Dict, List, Set, Any, Optional
from pathlib import Path
import ast
import importlib.util
from dataclasses import dataclass

from ..exceptions import SpecArchitectureError
from ..logging.debug import debug_logger

@dataclass
class ImportAnalysis:
    """Analysis result for import structure."""
    module_path: str
    absolute_imports: List[str]
    relative_imports: List[str]
    external_imports: List[str]
    architectural_violations: List[str]
    circular_dependencies: List[str]

    @property
    def has_violations(self) -> bool:
        """Check if module has any architectural violations."""
        return bool(self.architectural_violations or self.circular_dependencies)

class ImportValidator:
    """Validates import structure and architectural constraints."""

    # Define architectural boundaries
    LAYER_HIERARCHY = {
        'cli': {'core', 'config', 'ui', 'file_system', 'git', 'templates', 'exceptions', 'logging'},
        'core': {'config', 'file_system', 'git', 'templates', 'exceptions', 'logging'},
        'ui': {'config', 'exceptions', 'logging'},  # UI should not import from core
        'file_system': {'config', 'exceptions', 'logging'},
        'git': {'config', 'exceptions', 'logging'},
        'templates': {'config', 'file_system', 'exceptions', 'logging'},
        'config': {'exceptions', 'logging'},
        'exceptions': {'logging'},
        'logging': set()  # Logging has no dependencies
    }

    def __init__(self, project_root: Path):
        if not project_root.is_dir():
            raise ValueError(f"Project root must be a directory: {project_root}")

        self.project_root = project_root
        self.spec_cli_root = project_root / "spec_cli"
        self._import_cache: Dict[str, Set[str]] = {}

    def validate_import_structure(self, module_path: Path) -> ImportAnalysis:
        """Validate import structure for a module."""
        try:
            if not module_path.suffix == '.py':
                raise SpecArchitectureError(f"Module must be .py file: {module_path}")

            # Parse module AST
            with module_path.open('r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(module_path))

            # Extract imports
            imports = self._extract_imports(tree)

            # Analyze architectural violations
            violations = self._check_architectural_violations(module_path, imports)

            # Check for circular dependencies
            circular_deps = self._check_circular_dependencies(module_path, imports)

            # Categorize imports
            categorized = self._categorize_imports(imports)

            analysis = ImportAnalysis(
                module_path=str(module_path.relative_to(self.project_root)),
                absolute_imports=categorized['absolute'],
                relative_imports=categorized['relative'],
                external_imports=categorized['external'],
                architectural_violations=violations,
                circular_dependencies=circular_deps
            )

            return analysis

        except Exception as e:
            error_msg = f"Failed to analyze imports for {module_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecArchitectureError(error_msg) from e

# Import aggregation for common patterns
CORE_IMPORTS = {
    'pathlib': ['Path'],
    'typing': ['Any', 'Dict', 'List', 'Optional', 'Union'],
    'dataclasses': ['dataclass'],
    'abc': ['ABC', 'abstractmethod']
}

UI_IMPORTS = {
    'rich.console': ['Console'],
    'rich.table': ['Table'],
    'rich.progress': ['Progress', 'TaskID'],
    'rich.text': ['Text']
}

EXTERNAL_IMPORTS = {
    'click': ['command', 'option', 'argument'],
    'pytest': ['fixture', 'raises'],
    'pathlib': ['Path']
}
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Mixing import styles inconsistently
from spec_cli.core import workflow  # Absolute
from ..ui import console            # Relative
import spec_cli.logging.debug       # Mixed style

# BAD: Core module importing UI (violates architecture)
from spec_cli.core.workflow import WorkflowManager
from spec_cli.ui.console import get_console  # Architecture violation

# BAD: No import organization or validation
def some_function():
    import random_module  # Import inside function
    from somewhere import *  # Star imports
```

#### **Required Tests**

**File: `tests/unit/common/test_import_validator.py`**

**Test Functions Needed:**
```python
class TestImportValidator:
    def test_import_validator_when_valid_module_then_analyzes_successfully(self)
    def test_import_validator_when_architectural_violation_then_detects_violation(self)
    def test_import_validator_when_circular_dependency_then_detects_cycle(self)
    def test_import_validator_when_non_python_file_then_raises_error(self)
    def test_import_validator_when_analyze_project_then_returns_all_modules(self)

class TestImportAnalysis:
    def test_import_analysis_when_has_violations_then_returns_true(self)
    def test_import_analysis_when_no_violations_then_returns_false(self)
    def test_import_analysis_when_get_violation_summary_then_formats_correctly(self)

class TestImportUtilities:
    def test_get_standard_imports_when_valid_category_then_returns_imports(self)
    def test_get_standard_imports_when_invalid_category_then_raises_value_error(self)
```

**Files to Create/Modify**:
- `spec_cli/common/__init__.py` (new)
- `tests/unit/common/test_import_validator.py` (new)
- Update: Multiple files to fix import patterns
- Document: Add import standards to CLAUDE.md

---

### Slice 3.2: Improve Package Structure

**Goal**: Better package exports and dependency organization.

**Context**: Currently package `__init__.py` files lack proper exports and the Rich library imports are scattered throughout UI modules.

**Scope**:
- Update `__init__.py` files with proper exports
- Create rich library import aggregation
- Fix missing imports and circular dependencies
- Does NOT include major package restructuring

#### **New Files and Components**

**1. File: `spec_cli/ui/rich_imports.py`**

**Functions/Classes to Create:**

**A. Rich component aggregation**
- **Variables**: `Console`, `Table`, `Progress`, `Spinner`, `Text`
- **Purpose**: Centralized Rich library imports

**B. `RichComponentFactory` class**
- **Methods**: `create_console`, `create_table`, `create_progress_bar`
- **Purpose**: Factory for Rich components with consistent configuration

#### **✅ Good Example (Best Practices)**

```python
# spec_cli/ui/rich_imports.py
"""Centralized Rich library imports and component factory."""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from rich.console import Console as RichConsole
from rich.table import Table as RichTable
from rich.progress import (
    Progress as RichProgress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskID
)
from rich.spinner import Spinner as RichSpinner
from rich.text import Text as RichText

from ..config.settings import get_settings
from ..logging.debug import debug_logger

# Re-export for clean imports
__all__ = [
    'Console', 'Table', 'Progress', 'Spinner', 'Text',
    'RichComponentFactory'
]

# Direct exports for backward compatibility
Console = RichConsole
Table = RichTable
Progress = RichProgress
Spinner = RichSpinner
Text = RichText

class RichComponentFactory:
    """Factory for Rich components with consistent configuration."""

    def __init__(self, settings: Optional[Any] = None):
        self.settings = settings or get_settings()
        self._console_cache: Optional[RichConsole] = None

    def create_console(
        self,
        force_terminal: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        color_system: Optional[str] = None
    ) -> RichConsole:
        """Create Rich console with project-specific configuration."""
        # Use cached console if no specific configuration requested
        if (self._console_cache is not None and
            force_terminal is None and width is None and
            height is None and color_system is None):
            return self._console_cache

        # Determine configuration from settings
        config = {
            'force_terminal': force_terminal,
            'width': width,
            'height': height,
            'color_system': color_system
        }

        # Remove None values to use Rich defaults
        config = {k: v for k, v in config.items() if v is not None}

        console = RichConsole(**config)

        # Cache if using default configuration
        if not config:
            self._console_cache = console

        debug_logger.log(
            "DEBUG",
            "Rich console created",
            config=config,
            cached=not config
        )

        return console

    def create_table(
        self,
        title: Optional[str] = None,
        show_header: bool = True,
        show_lines: bool = False,
        expand: bool = False
    ) -> RichTable:
        """Create Rich table with project-specific styling."""
        config = {
            'title': title,
            'show_header': show_header,
            'show_lines': show_lines,
            'expand': expand
        }

        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}

        table = RichTable(**config)

        debug_logger.log(
            "DEBUG",
            "Rich table created",
            title=title,
            show_header=show_header
        )

        return table

# Convenience factory instance
_default_factory: Optional[RichComponentFactory] = None

def get_rich_factory() -> RichComponentFactory:
    """Get default Rich component factory."""
    global _default_factory
    if _default_factory is None:
        _default_factory = RichComponentFactory()
    return _default_factory
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Scattered Rich imports throughout modules
from rich.console import Console  # In module A
from rich.table import Table      # In module B
from rich.console import Console  # Duplicate in module C

# BAD: No factory pattern, inconsistent configuration
def create_console_somewhere():
    return Console(force_terminal=True, width=80)  # Hard-coded config

def create_console_elsewhere():
    return Console()  # Different config
```

#### **Required Tests**

**File: `tests/unit/ui/test_rich_imports.py`**

**Test Functions Needed:**
```python
class TestRichComponentFactory:
    def test_rich_component_factory_when_create_console_then_returns_console(self)
    def test_rich_component_factory_when_create_table_then_returns_configured_table(self)
    def test_rich_component_factory_when_create_progress_bar_then_returns_progress(self)
    def test_rich_component_factory_when_console_caching_then_reuses_instance(self)

class TestRichImportAggregation:
    def test_rich_imports_when_imported_then_all_components_available(self)
    def test_get_rich_factory_when_called_then_returns_same_instance(self)
    def test_convenience_functions_when_called_then_create_components(self)
```

**Files to Create/Modify**:
- `spec_cli/ui/rich_imports.py` (new)
- `tests/unit/ui/test_rich_imports.py` (new)
- Update: `spec_cli/__init__.py` and other package `__init__.py` files
- Test: Import structure validation

---

## PHASE 4: Template System Consolidation (MEDIUM PRIORITY)

### Slice 4.1: Create Template Service Layer

**Goal**: Centralize template loading, validation, and caching.

**Context**: Currently template loading is scattered across generator.py and loader.py with duplicate validation and no caching mechanism.

**Scope**:
- Create `TemplateService` class with caching and validation
- Consolidate template loading patterns across modules
- Add template performance monitoring
- Does NOT include complex template transformation logic

#### **New File: `spec_cli/templates/service.py`**

**A. `TemplateService` class**
- **Methods**: `load_template`, `validate_template`, `get_template_info`, `clear_cache`
- **Purpose**: Centralized template management with caching

**B. `TemplateCache` class**
- **Methods**: `get`, `put`, `invalidate`, `get_stats`
- **Purpose**: Template caching with TTL and size limits

**C. `TemplateMetrics` dataclass**
- **Fields**: `load_time`, `cache_hits`, `cache_misses`, `validation_time`
- **Purpose**: Template performance monitoring

#### **✅ Good Example (Best Practices)**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
import hashlib
import time
from threading import Lock

from .config import TemplateConfig
from .loader import TemplateLoader
from .validation import TemplateValidator
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger
from ..config.settings import get_settings

@dataclass
class CacheEntry:
    """Template cache entry with metadata."""
    template: TemplateConfig
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    file_hash: Optional[str] = None

    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

@dataclass
class TemplateMetrics:
    """Template service performance metrics."""
    total_loads: int = 0
    total_load_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    validation_time: float = 0.0
    error_count: int = 0

    @property
    def average_load_time(self) -> float:
        """Calculate average load time."""
        return self.total_load_time / max(self.total_loads, 1)

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total_requests = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total_requests, 1)

class TemplateCache:
    """Thread-safe template cache with TTL and size limits."""

    def __init__(
        self,
        max_size: int = 50,
        ttl_seconds: float = 3600.0,  # 1 hour
        cleanup_interval: float = 300.0  # 5 minutes
    ):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._last_cleanup = datetime.now()

    def get(self, template_path: Path) -> Optional[TemplateConfig]:
        """Get template from cache."""
        key = self._generate_key(template_path)

        with self._lock:
            # Cleanup if needed
            if self._should_cleanup():
                self._cleanup_expired()

            entry = self._cache.get(key)
            if entry is None:
                return None

            # Check if expired
            if entry.is_expired(self.ttl_seconds):
                del self._cache[key]
                return None

            # Update access time
            entry.touch()

            debug_logger.log(
                "DEBUG",
                "Template cache hit",
                key=key,
                access_count=entry.access_count
            )

            return entry.template

class TemplateService:
    """Centralized template management service with caching and validation."""

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_size: int = 50,
        cache_ttl: float = 3600.0,
        strict_validation: bool = False
    ):
        self.cache_enabled = cache_enabled
        self.strict_validation = strict_validation

        # Initialize components
        self.loader = TemplateLoader()
        self.validator = TemplateValidator(strict_mode=strict_validation)

        # Initialize cache if enabled
        self.cache: Optional[TemplateCache] = None
        if cache_enabled:
            self.cache = TemplateCache(
                max_size=cache_size,
                ttl_seconds=cache_ttl
            )

        # Initialize metrics
        self.metrics = TemplateMetrics()
        self._metrics_lock = Lock()

    def load_template(
        self,
        template_path: Path,
        use_cache: bool = True,
        validate: bool = True
    ) -> TemplateConfig:
        """Load template with caching and validation."""
        start_time = time.time()

        try:
            # Check cache first
            cached_template = None
            if self.cache_enabled and use_cache and self.cache:
                cached_template = self.cache.get(template_path)

                if cached_template is not None:
                    with self._metrics_lock:
                        self.metrics.cache_hits += 1

                    debug_logger.log(
                        "DEBUG",
                        "Template loaded from cache",
                        path=str(template_path)
                    )

                    return cached_template

            # Cache miss - load from file
            with self._metrics_lock:
                if self.cache_enabled:
                    self.metrics.cache_misses += 1
                self.metrics.total_loads += 1

            # Load template
            template = self.loader.load_template(template_path)

            # Validate if requested
            if validate:
                validation_start = time.time()
                validation_result = self.validator.validate(template, raise_on_error=True)

                with self._metrics_lock:
                    self.metrics.validation_time += time.time() - validation_start

                if not validation_result.is_valid:
                    error_msg = f"Template validation failed: {validation_result.format_summary()}"
                    raise SpecTemplateError(error_msg)

            # Cache if enabled
            if self.cache_enabled and use_cache and self.cache:
                self.cache.put(template_path, template)

            # Update metrics
            load_time = time.time() - start_time
            with self._metrics_lock:
                self.metrics.total_load_time += load_time

            debug_logger.log(
                "INFO",
                "Template loaded successfully",
                path=str(template_path),
                load_time=load_time,
                validated=validate
            )

            return template

        except Exception as e:
            with self._metrics_lock:
                self.metrics.error_count += 1

            error_msg = f"Failed to load template from {template_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: No caching, loads template every time
def load_template_bad(path):
    with open(path) as f:
        return f.read()  # No validation, no error handling

# BAD: Global state without thread safety
TEMPLATE_CACHE = {}  # Shared state, race conditions

def bad_cache_get(path):
    if path in TEMPLATE_CACHE:  # No TTL, no size limits
        return TEMPLATE_CACHE[path]
    return None
```

#### **Required Tests**

**File: `tests/unit/templates/test_service.py`**

**Test Functions Needed:**
```python
class TestTemplateCache:
    def test_template_cache_when_put_and_get_then_returns_template(self)
    def test_template_cache_when_expired_entry_then_returns_none(self)
    def test_template_cache_when_max_size_exceeded_then_evicts_lru(self)
    def test_template_cache_when_cleanup_then_removes_expired_entries(self)
    def test_template_cache_when_invalidate_then_removes_entry(self)

class TestTemplateService:
    def test_template_service_when_load_template_then_returns_template(self)
    def test_template_service_when_cache_enabled_then_uses_cache(self)
    def test_template_service_when_validation_fails_then_raises_error(self)
    def test_template_service_when_get_template_info_then_returns_info(self)
    def test_template_service_when_get_metrics_then_returns_statistics(self)

class TestTemplateMetrics:
    def test_template_metrics_when_calculate_averages_then_returns_correct_values(self)
    def test_template_metrics_when_to_dict_then_returns_complete_data(self)
```

**Files to Create/Modify**:
- `spec_cli/templates/service.py` (new)
- `tests/unit/templates/test_service.py` (new)
- Update: Template-using modules

---

### Slice 4.2: Unify Variable Preparation Logic

**Goal**: Consolidate variable generation and formatting logic.

**Context**: Currently variable preparation logic is duplicated between generator.py and substitution.py with different formatting approaches.

**Scope**:
- Move variable preparation to centralized location
- Standardize built-in variable generation
- Consolidate formatting utilities
- Does NOT include template-specific variable logic

#### **New Functions in `spec_cli/templates/variables.py`**

**A. `VariableProvider` class**
- **Methods**: `get_file_variables`, `get_template_variables`, `get_builtin_variables`
- **Purpose**: Centralized variable generation

**B. `VariableFormatter` class**
- **Methods**: `format_file_size`, `format_timestamp`, `format_path`
- **Purpose**: Consistent variable formatting

**C. `combine_variables` function**
- **Parameters**: `*variable_sources: Dict[str, Any], precedence_order: List[str]`
- **Returns**: `Dict[str, Any]`
- **Purpose**: Merge variables with precedence rules

#### **✅ Good Example (Best Practices)**

```python
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import platform
import getpass

from ..file_system.file_metadata import FileMetadataExtractor
from ..file_system.file_utils import format_file_size
from ..config.settings import get_settings
from ..logging.debug import debug_logger

@dataclass
class VariableContext:
    """Context for variable generation."""
    source_file: Path
    template_name: str
    custom_variables: Dict[str, Any]
    include_system_vars: bool = True
    include_file_vars: bool = True
    include_template_vars: bool = True

    def __post_init__(self) -> None:
        """Validate context after initialization."""
        if not isinstance(self.source_file, Path):
            raise TypeError("source_file must be a Path object")
        if not isinstance(self.custom_variables, dict):
            raise TypeError("custom_variables must be a dictionary")

class VariableFormatter:
    """Handles consistent formatting of variable values."""

    @staticmethod
    def format_file_size(size_bytes: Union[int, float]) -> str:
        """Format file size in human-readable format."""
        if not isinstance(size_bytes, (int, float)):
            return "unknown"

        try:
            return format_file_size(int(size_bytes))
        except (ValueError, OverflowError):
            return "unknown"

    @staticmethod
    def format_timestamp(
        timestamp: Union[int, float, datetime],
        format_string: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """Format timestamp in human-readable format."""
        try:
            if isinstance(timestamp, datetime):
                dt = timestamp
            elif isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                return "unknown"

            return dt.strftime(format_string)
        except (ValueError, OSError, OverflowError):
            return "unknown"

class VariableProvider:
    """Provides standardized variable generation for templates."""

    def __init__(self, formatter: Optional[VariableFormatter] = None):
        self.formatter = formatter or VariableFormatter()
        self.metadata_extractor = FileMetadataExtractor()
        self.settings = get_settings()

    def get_builtin_variables(self) -> Dict[str, Any]:
        """Get built-in system and environment variables."""
        now = datetime.now()

        variables = {
            # Date and time
            'creation_date': now.strftime('%Y-%m-%d'),
            'creation_time': now.strftime('%H:%M:%S'),
            'creation_datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'creation_timestamp': int(now.timestamp()),

            # System information
            'system_platform': platform.system(),
            'system_architecture': platform.machine(),
            'python_version': platform.python_version(),

            # User information
            'user_name': getpass.getuser(),

            # Project information
            'project_root': self.formatter.format_path(self.settings.root_path),
            'specs_directory': self.formatter.format_path(self.settings.specs_dir),
        }

        debug_logger.log(
            "DEBUG",
            "Built-in variables generated",
            variable_count=len(variables)
        )

        return variables

    def get_file_variables(self, file_path: Path) -> Dict[str, Any]:
        """Get variables based on file information."""
        try:
            # Basic file information
            variables = {
                'filename': file_path.name,
                'file_stem': file_path.stem,
                'file_extension': file_path.suffix.lstrip('.') or 'txt',
                'filepath': self.formatter.format_path(file_path),
                'filepath_posix': self.formatter.format_path(file_path, style='posix'),
                'parent_directory': file_path.parent.name,
                'relative_path': self.formatter.format_path(
                    file_path,
                    relative_to=self.settings.root_path
                ),
            }

            # File existence and properties
            if file_path.exists():
                stat_info = file_path.stat()
                variables.update({
                    'file_exists': True,
                    'file_size_bytes': stat_info.st_size,
                    'file_size': self.formatter.format_file_size(stat_info.st_size),
                    'file_modified': self.formatter.format_timestamp(stat_info.st_mtime),
                    'file_modified_timestamp': int(stat_info.st_mtime),
                    'file_is_readable': file_path.is_file() and file_path.exists(),
                })
            else:
                variables.update({
                    'file_exists': False,
                    'file_size_bytes': 0,
                    'file_size': 'unknown',
                    'file_modified': 'unknown',
                    'file_modified_timestamp': 0,
                    'file_is_readable': False,
                })

            return variables

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Failed to generate file variables",
                file_path=str(file_path),
                error=str(e)
            )

            # Return minimal variables on error
            return {
                'filename': file_path.name,
                'file_stem': file_path.stem,
                'file_extension': file_path.suffix.lstrip('.') or 'txt',
                'filepath': str(file_path),
                'file_exists': False,
                'file_type': 'unknown',
            }

def combine_variables(
    *variable_sources: Dict[str, Any],
    precedence_order: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Combine multiple variable dictionaries with precedence rules."""
    if not variable_sources:
        return {}

    if precedence_order is not None and len(precedence_order) != len(variable_sources):
        raise ValueError(
            f"precedence_order length ({len(precedence_order)}) must match "
            f"variable_sources length ({len(variable_sources)})"
        )

    combined = {}
    conflicts = []

    for i, variables in enumerate(variable_sources):
        if not isinstance(variables, dict):
            raise TypeError(f"Variable source {i} must be a dictionary")

        source_name = precedence_order[i] if precedence_order else f"source_{i}"

        for key, value in variables.items():
            if key in combined:
                conflicts.append((key, source_name, combined[key], value))
            combined[key] = value

    # Log conflicts for debugging
    if conflicts:
        debug_logger.log(
            "DEBUG",
            "Variable conflicts resolved by precedence",
            conflicts=[
                f"{key}: {old_val} -> {new_val} (from {source})"
                for key, source, old_val, new_val in conflicts
            ]
        )

    return combined
```

#### **❌ Bad Example (Anti-Patterns)**

```python
# BAD: Duplicate variable generation in multiple modules
def get_file_vars_module_a(path):
    return {'name': path.name, 'size': path.stat().st_size}  # No error handling

def get_file_vars_module_b(file_path):
    return {'filename': file_path.name, 'filesize': file_path.stat().st_size}  # Different keys

# BAD: No formatting consistency
def format_size_inconsistent(size):
    return f"{size} bytes"  # Raw bytes, no human-readable format

def format_timestamp_inconsistent(ts):
    return str(ts)  # Raw timestamp, no formatting
```

#### **Required Tests**

**File: `tests/unit/templates/test_variables.py`**

**Test Functions Needed:**
```python
class TestVariableFormatter:
    def test_variable_formatter_when_format_file_size_then_returns_readable_size(self)
    def test_variable_formatter_when_format_timestamp_then_returns_formatted_date(self)
    def test_variable_formatter_when_format_path_then_uses_correct_separators(self)

class TestVariableProvider:
    def test_variable_provider_when_get_builtin_variables_then_includes_system_info(self)
    def test_variable_provider_when_get_file_variables_then_includes_file_info(self)
    def test_variable_provider_when_get_template_variables_then_includes_template_info(self)
    def test_variable_provider_when_generate_all_variables_then_combines_all_sources(self)

class TestCombineVariables:
    def test_combine_variables_when_multiple_sources_then_applies_precedence(self)
    def test_combine_variables_when_conflicts_then_later_overrides_earlier(self)
    def test_combine_variables_when_invalid_precedence_order_then_raises_error(self)
```

**Files to Create/Modify**:
- `spec_cli/templates/variables.py` (new)
- `tests/unit/templates/test_variables.py` (new)
- Update: `spec_cli/templates/generator.py`, `spec_cli/templates/substitution.py`

---

## Systematic Refactoring Process

Following the same methodology as testing improvements:

### Step 1: Identify Target Module
- Select module with highest code duplication
- Focus on utility functions and common patterns
- Avoid complex workflow methods initially

**Command:**
```bash
# Find modules with duplicate patterns
grep -r "def.*format.*size" spec_cli/ | wc -l
grep -r "try:" spec_cli/ | head -10
```

### Step 2: Analyze Code Implementation
- Read the target files to understand duplication
- Identify common patterns and utilities
- Focus on methods with clear inputs/outputs

**Commands:**
```bash
# Find function definitions
grep -n "def " "/path/to/target/file.py"
# Use Read tool to examine implementation
```

### Step 3: Create Centralized Utilities
- Extract common logic into utilities module
- Create 1-2 focused utility functions
- Use descriptive names and clear interfaces

### Step 4: Test Utilities in Isolation
- Run only the new utility tests
- Catch import issues and logic errors early

**Command:**
```bash
poetry run pytest tests/unit/utils/test_new_utility.py -v
```

### Step 5: Update Existing Code
- Replace duplicate code with utility calls
- Update 2-3 modules per slice
- Maintain backward compatibility

### Step 6: Validate Integration
- Run tests for updated modules
- Ensure all existing functionality works

**Command:**
```bash
poetry run pytest tests/unit/path/to/updated/ -v
```

### Step 7: Run Full Test Suite
- Execute complete test suite
- Verify no regressions introduced

**Command:**
```bash
poetry run pytest tests/unit/ -v
```

### Step 8: Quality Validation
- Run all quality checks
- Ensure code meets standards

**Command:**
```bash
poetry run pre-commit run --all-files
```

### Step 9: Coverage and Type Checking
- Verify improved code coverage
- Run type checking validation

**Commands:**
```bash
poetry run pytest --cov=spec_cli tests/unit/ --cov-report=term-missing
poetry run mypy spec_cli/
```

### Key Success Principles

1. **Focus on High-Impact Utilities**: Target duplicate code that appears 3+ times
2. **Incremental Progress**: 3-5 files updated per slice
3. **Utility Isolation**: Always test new utilities independently
4. **Quality First**: Never compromise code quality for deduplication
5. **Systematic Approach**: Complete all 9 steps before moving to next slice
6. **One Task In Progress**: Mark only one todo as in_progress at a time
7. **Immediate Completion**: Mark todos completed as soon as each step finishes

## Implementation Order Rationale

1. **Phase 1**: Foundation utilities that many modules depend on
2. **Phase 2**: Configuration that affects module initialization
3. **Phase 3**: Import structure that affects all modules
4. **Phase 4**: Template system specific improvements

Each phase builds on the previous, ensuring a stable foundation for subsequent improvements.

## Success Metrics

- **Code Duplication Reduction**: 30-40% reduction in duplicate code
- **Test Coverage Maintenance**: Keep 80%+ coverage throughout
- **No Regressions**: All existing tests continue to pass
- **Improved Maintainability**: Centralized utilities for common patterns
- **Better Architecture**: Clean dependency structure and imports

## Risk Mitigation

- **Small Increments**: Each slice touches only 3-5 files
- **Comprehensive Testing**: Test utilities independently before integration
- **Gradual Migration**: Update modules progressively, not all at once
- **Quality Gates**: Every slice must pass all quality checks
- **Rollback Plan**: Each slice is independently revertible if issues arise
