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

### Slice 1.1: Create Centralized Error Handling Utilities (Split into 1.1a + 1.1b)

**Goal**: Eliminate duplicate try/catch patterns and error message formatting across 15+ modules.

**Scope**:
- Create `spec_cli/utils/error_handling.py` with common error patterns
- Focus on `OSError`, `CalledProcessError`, and `SpecError` handling
- Does NOT include complex workflow error handling

---

#### Slice 1.1a: Error Utilities Only

**Goal**: Create standalone error handling functions without integration.

**New Files and Components**

**1. File: `spec_cli/utils/__init__.py`**
```python
"""Utility modules for common operations."""
```

**2. File: `spec_cli/utils/error_utils.py`**

**Functions to Create:**

**A. `handle_os_error` function**
- **Parameters**: `exc: OSError`
- **Returns**: `str`
- **Purpose**: Format OSError messages with consistent context

**B. `handle_subprocess_error` function**
- **Parameters**: `exc: subprocess.SubprocessError`
- **Returns**: `str`
- **Purpose**: Format subprocess errors with command details

**C. `create_error_context` function**
- **Parameters**: `code_path: Path`
- **Returns**: `Dict[str, Any]`
- **Purpose**: Create standardized error context dictionary

**Required Tests**

**File: `tests/unit/utils/test_error_utils.py`**

**Test Functions Needed:**
```python
class TestHandleOsError:
    def test_handle_os_error_when_permission_denied_then_returns_formatted_message(self)
    def test_handle_os_error_when_file_not_found_then_returns_descriptive_message(self)
    def test_handle_os_error_when_generic_error_then_includes_errno(self)

class TestHandleSubprocessError:
    def test_handle_subprocess_error_when_called_process_error_then_includes_stderr(self)
    def test_handle_subprocess_error_when_timeout_expired_then_returns_timeout_message(self)
    def test_handle_subprocess_error_when_command_list_then_formats_command(self)

class TestCreateErrorContext:
    def test_create_error_context_when_path_provided_then_includes_path_info(self)
    def test_create_error_context_when_minimal_info_then_returns_basic_context(self)
```

**No Integration**: Do not import these functions into any existing modules yet. Just commit error_utils.py and its tests.

**Files to Create:**
- `spec_cli/utils/__init__.py` (new)
- `spec_cli/utils/error_utils.py` (new)
- `tests/unit/utils/test_error_utils.py` (new)

---

#### Slice 1.1b: ErrorHandler Class + Integration

**Goal**: Create ErrorHandler class and integrate into 2 modules.

**New Files and Components**

**1. File: `spec_cli/core/error_handler.py`**

**Class to Create:**

**A. `ErrorHandler` class**
- **Methods**: `__init__(logger)`, `wrap(func)`, `report(exc)`
- **Purpose**: Centralized error handling using utilities from error_utils.py
- **Integration**: Uses the three helper functions from error_utils.py

**Integration Steps:**

1. Import ErrorHandler in exactly two modules:
   - `spec_cli/cli/main.py` - Wrap main entry point
   - `spec_cli/services/runner.py` (or similar self-contained module)

2. Example integration:
```python
from spec_cli.core.error_handler import ErrorHandler
handler = ErrorHandler()

@handler.wrap
def some_entrypoint(...):
    ...
```

**Required Tests**

**File: `tests/unit/core/test_error_handler.py`**

**Test Functions Needed:**
```python
class TestErrorHandler:
    def test_error_handler_when_wrap_function_then_catches_exceptions(self)
    def test_error_handler_when_report_called_then_logs_with_context(self)
    def test_error_handler_when_os_error_then_uses_handle_os_error(self)
    def test_error_handler_when_subprocess_error_then_uses_handle_subprocess_error(self)
```

**File: `tests/unit/core/test_error_handler_integration.py`**

**Minimal smoke tests:**
```python
def test_main_entry_wrapped_with_error_handler()
def test_runner_wrapped_with_error_handler()
```

**Files to Create/Modify:**
- `spec_cli/core/error_handler.py` (new)
- `tests/unit/core/test_error_handler.py` (new)
- `tests/unit/core/test_error_handler_integration.py` (new)
- Update: `spec_cli/cli/main.py`, `spec_cli/services/runner.py` (or similar)

---

### Slice 1.2: Consolidate Path Operations (Keep as single slice if duplication is high)

**Goal**: Create centralized utilities for common path operations (relative_to, mkdir patterns).

**Scope**:
- Create new `spec_cli/utils/path_utils.py` (not in file_system to avoid circular deps)
- Focus on try/except patterns for `relative_to()` operations
- Standardize directory creation patterns

**Decision Point**: If this touches too many files, split into 1.2a/1.2b as shown below.

#### Option A: Keep as Slice 1.2 (if duplication is very high)

**New File: `spec_cli/utils/path_utils.py`**

**Functions to Create:**

**A. `resolve_project_root` function**
- **Parameters**: None
- **Returns**: `Path`
- **Purpose**: Find project root directory consistently

**B. `ensure_directory` function**
- **Parameters**: `path: Path`
- **Returns**: `None`
- **Purpose**: Create directory if it doesn't exist

**C. `normalize_path` function**
- **Parameters**: `p: Union[str, Path]`
- **Returns**: `Path`
- **Purpose**: Consistent path normalization

**Integration:**
- Modify two existing modules: `spec_cli/config/settings.py` and `spec_cli/core/launcher.py`
- Replace ad-hoc Path() logic with these utilities
- Total files touched: 1 new + 2 updates = 3

#### Option B: Split into 1.2a + 1.2b

**Slice 1.2a: Resolve + Ensure Directory Only**

**New File: `spec_cli/utils/path_utils.py`**
- Implement only `resolve_project_root()` and `ensure_directory()`
- Write tests in `tests/unit/utils/test_path_utils_a.py`
- No existing files modified yet

**Slice 1.2b: Normalize Path + Integration**

- Add `normalize_path()` to same file
- Write tests in `tests/unit/utils/test_path_utils_b.py`
- Update exactly two modules to use the utilities

**Required Tests**

**File: `tests/unit/utils/test_path_utils.py` (or split into _a.py and _b.py)**

**Test Functions:**
```python
class TestResolveProjectRoot:
    def test_resolve_project_root_when_git_repo_then_returns_git_root(self)
    def test_resolve_project_root_when_no_git_then_returns_current_dir(self)

class TestEnsureDirectory:
    def test_ensure_directory_when_not_exists_then_creates(self)
    def test_ensure_directory_when_exists_then_no_error(self)
    def test_ensure_directory_when_file_exists_then_raises_error(self)

class TestNormalizePath:
    def test_normalize_path_when_string_then_returns_path(self)
    def test_normalize_path_when_relative_then_returns_absolute(self)
```

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

**Files to Create/Modify**:
- `spec_cli/utils/path_utils.py` (new)
- `tests/unit/utils/test_path_utils.py` (new or split)
- Update: `spec_cli/config/settings.py`, `spec_cli/core/launcher.py`

---

### Slice 1.3: Create CLI Command Base Class (Split into 1.3a + 1.3b)

**Goal**: Eliminate duplicate argument validation and setup patterns across CLI commands.

**Scope**:
- Create base command class with common patterns
- Focus on file path validation, error handling, and setup
- Does NOT include complex workflow logic

---

#### Slice 1.3a: Scaffold BaseCommand & Tests

**New File: `spec_cli/cli/base.py`**

**Classes to Create:**

**A. `CommandContext` class**
```python
class CommandContext:
    def __init__(self, args: Dict[str, Any]):
        self.args = args
```

**B. `BaseCommand` class**
```python
class BaseCommand:
    def __init__(self, ctx: CommandContext):
        self.ctx = ctx

    def run(self) -> None:
        raise NotImplementedError
```

**No callers** - no modifications in other modules yet.

**Required Tests**

**File: `tests/unit/cli/test_base.py`**
- Test BaseCommand can be instantiated
- Test run() raises NotImplementedError

**Files to Create:**
- `spec_cli/cli/base.py` (new)
- `tests/unit/cli/test_base.py` (new)

---

#### Slice 1.3b: Migrate add & gen Commands

**Goal**: Migrate two commands to use BaseCommand.

**Modifications:**

1. Update `spec_cli/cli/commands/add.py`:
```python
from spec_cli.cli.base import BaseCommand, CommandContext

class AddCommand(BaseCommand):
    def __init__(self, ctx: CommandContext):
        super().__init__(ctx)

    def run(self):
        # existing logic here
```

2. Update `spec_cli/cli/commands/gen.py` similarly

3. Update entry-point registration in `spec_cli/cli/main.py`

**Required Tests**

**File: `tests/unit/cli/test_commands_integration.py`**
- Test AddCommand with dummy CommandContext
- Test GenCommand with dummy CommandContext
- Ensure no regressions
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
---

---

### Slice 2.2: Consolidate Environment Variable Handling (Split into 2.2a + 2.2b + 2.2c)

**Goal**: Centralize all environment variable reading in settings.py.

**Context**: Currently environment variables are read directly in debug.py and inconsistently throughout the codebase, causing circular dependencies.

**Scope**:
- Create centralized environment variable utilities
- Fix circular dependencies between settings/logging/ui
- Does NOT include complex application-specific environment handling

---

#### Slice 2.2a: Basic Getters Only

**New File: `spec_cli/utils/env_utils.py`**

**Functions to Create:**

**A. `get_env_str` function**
- **Parameters**: `key: str, default: str = ""`
- **Returns**: `str`
- **Purpose**: Get string environment variable

**B. `get_env_int` function**
- **Parameters**: `key: str, default: int = 0`
- **Returns**: `int`
- **Purpose**: Get integer environment variable

**C. `get_env_bool` function**
- **Parameters**: `key: str, default: bool = False`
- **Returns**: `bool`
- **Purpose**: Get boolean environment variable

**Required Tests**

**File: `tests/unit/utils/test_env_utils_a.py`**
- Test each getter with valid values
- Test defaults when not set
- Test invalid values fall back to defaults

**No changes to logging.py or settings.py yet**.

---

#### Slice 2.2b: EnvironmentConfig Dataclass

**Same File: `spec_cli/utils/env_utils.py`**

**Add:**
```python
@dataclass
class EnvironmentConfig:
    debug: bool
    port: int
    api_key: str
```

**Required Tests**

**File: `tests/unit/utils/test_env_utils_b.py`**
- Test EnvironmentConfig instantiation
- Test from environment variables using monkeypatch

---

#### Slice 2.2c: Migrate logging & settings

**Goal**: Apply environment utilities to existing modules.

**Modifications:**

1. Update `spec_cli/logging.py`:
   - Replace direct `os.getenv()` calls with `get_env_str/int/bool`
   - Remove hardcoded defaults

2. Update `spec_cli/config/settings.py`:
   - Import EnvironmentConfig
   - Load fields from EnvironmentConfig

**Required Tests**

**Files: `tests/unit/config/test_logging_env_integration.py` & `tests/unit/config/test_settings_env_integration.py`**
- Test environment variables are properly loaded
- Test defaults work correctly

**Files to Modify:**
- `spec_cli/utils/env_utils.py` (already created)
- `spec_cli/logging.py`
- `spec_cli/config/settings.py`
- Two new test files

---

### Slice 2.3: Unify Validation Patterns (Keep as single slice or split if needed)

**Goal**: Create base validator class to eliminate duplicate validation logic.

**Context**: Currently `ConfigurationValidator` and `TemplateValidator` have duplicate validation patterns with inconsistent error handling and return formats.

**Scope**:
- Extract common patterns from existing validators
- Create `spec_cli/validation/base_validator.py` with base validator
- Update existing validators to inherit from base
- Does NOT include domain-specific validation logic

#### Option A: Keep as Slice 2.3

**New File: `spec_cli/validation/base_validator.py`**

**Classes to Create:**

**A. `ValidationErrorDetail` dataclass**
- **Fields**: `field: str`, `message: str`
- **Purpose**: Structured error details

**B. `BaseValidator` class**
- **Methods**: `validate(data: Dict[str, Any]) -> List[ValidationErrorDetail]`
- **Purpose**: Abstract base for validators

**Integration:**
- Modify two existing validators: `spec_cli/validation/json_validator.py` and `spec_cli/validation/schema_validator.py`
- Make them subclass BaseValidator

**Required Tests**

**File: `tests/unit/validation/test_base_validator.py`**
- Test ValidationErrorDetail creation
- Test BaseValidator abstract methods
- Test subclass behavior

#### Option B: Split into 2.3a + 2.3b

**Slice 2.3a: Validation Dataclass Only**
- Add only ValidationErrorDetail dataclass
- Test in `tests/unit/validation/test_validator_dataclass.py`
- No changes to existing validators

**Slice 2.3b: BaseValidator + Integration**
- Add BaseValidator class
- Update two existing validators
- Integration tests

**Files to Create/Modify**:
- `spec_cli/validation/base_validator.py` (new)
- `tests/unit/validation/test_base_validator.py` (new)
- Update: `spec_cli/validation/json_validator.py`, `spec_cli/validation/schema_validator.py`

---

---

## PHASE 3: Import Structure and Dependencies (LOW PRIORITY)

### Slice 3.1: Import Validator / Import Policy (Split into 3.1a + 3.1b + 3.1c)

**Goal**: Establish consistent import style and fix architectural violations.

**Context**: Currently the codebase mixes absolute and relative imports, and core modules import UI components creating tight coupling.

**Scope**:
- Create import validation tooling
- Fix core modules importing UI components
- Does NOT include external dependency reorganization

---

#### Slice 3.1a: Core Dataclass + Stub Validator

**New File: `spec_cli/validation/import_validator.py`**

**Classes to Create:**

**A. `ImportViolation` dataclass**
```python
@dataclass
class ImportViolation:
    module_name: str
    line_no: int
    reason: str
```

**B. `ImportValidator` class (stub)**
```python
class ImportValidator:
    def __init__(self, tree: ast.AST):
        self.tree = tree

    def validate(self) -> List[ImportViolation]:
        return []  # stub
```

**Required Tests**

**File: `tests/unit/validation/test_import_validator_a.py`**
- Test ImportValidator instantiation
- Test validate returns empty list

**No AST logic yet** - no modifications in any other module.

---

#### Slice 3.1b: AST Extraction Helpers

**Same File: `spec_cli/validation/import_validator.py`**

**Add Helper Functions:**

**A. `extract_import_nodes` function**
- **Parameters**: `tree: ast.AST`
- **Returns**: `List[ast.Import]`
- **Purpose**: Extract import statements

**B. `extract_from_import_nodes` function**
- **Parameters**: `tree: ast.AST`
- **Returns**: `List[ast.ImportFrom]`
- **Purpose**: Extract from-import statements

**Required Tests**

**File: `tests/unit/validation/test_import_validator_b.py`**
- Test extraction on small Python snippet
- Verify correct node lists returned

**Do not add policy checks** or integrate into validate() yet.

---

#### Slice 3.1c: Violation Checks & First Integration

**In `spec_cli/validation/import_validator.py`:**

1. Implement `validate()` method:
   - Call extract helpers
   - Check against hardcoded disallowed modules (e.g., {'os', 'sys'})
   - Return ImportViolations

2. Modify one consumer: Add CLI flag in `spec_cli/cli/commands/check_imports.py`

**Required Tests**

**File: `tests/unit/validation/test_import_validator_c.py`**
- Feed toy Python file that imports os
- Verify one ImportViolation returned
**Files to Create/Modify**:
- `spec_cli/validation/import_validator.py` (new)
- `tests/unit/validation/test_import_validator_a.py` (new)
- `tests/unit/validation/test_import_validator_b.py` (new)
- `tests/unit/validation/test_import_validator_c.py` (new)
- `spec_cli/cli/commands/check_imports.py` (new or update)

---

### Slice 3.2: Rich Import Aggregator

**Goal**: Create centralized Rich library imports.

**Context**: Currently Rich imports are scattered throughout UI modules.

**Scope**:
- Create rich library import aggregation
- Does NOT include major package restructuring

This slice is already small enough (just builds a factory/aggregator for multiple validators). No change needed.

**New File: `spec_cli/ui/rich_imports.py`**

**Components to Create:**
- Import all Rich components
- Create factory for consistent configuration
- Export commonly used components

**Required Tests**

**File: `tests/unit/ui/test_rich_imports.py`**
- Test imports work correctly
- Test factory creates components

**Files to Create:**
- `spec_cli/ui/rich_imports.py` (new)
- `tests/unit/ui/test_rich_imports.py` (new)

---

---

## Summary of Alpha-Suffixes

**Phase 1: Foundation Utilities**
- 1.1 → 1.1a, 1.1b (Error handling split into utilities + integration)
- 1.2 → Keep as-is or split into 1.2a, 1.2b if needed (Path utilities)
- 1.3 → 1.3a, 1.3b (CLI base class scaffold + command migration)

**Phase 2: Configuration and Architecture**
- 2.1 → 2.1a, 2.1b, 2.1c (Singleton: decorator + settings + theme/console)
- 2.2 → 2.2a, 2.2b, 2.2c (Env vars: getters + dataclass + migration)
- 2.3 → Keep as-is or split into 2.3a, 2.3b if needed (Validation patterns)

**Phase 3: Import Structure**
- 3.1 → 3.1a, 3.1b, 3.1c (Import validator: dataclass + AST + integration)
- 3.2 → Keep as-is (Rich aggregator - already small)

## Key Implementation Principles

1. **Each α-suffix is truly minimal**: 1-2 new files/functions, 2-3 file updates max
2. **No integration in 'a' slices**: Create utilities/classes without wiring them up
3. **Progressive integration**: 'b' and 'c' slices wire up to 2-3 modules only
4. **Test isolation first**: Always test new utilities in isolation before integration
5. **Clear boundaries**: Each slice has explicit "touch only these files" limits

## Implementation Order Rationale

1. **Phase 1**: Foundation utilities that many modules depend on
2. **Phase 2**: Configuration that affects module initialization
3. **Phase 3**: Import structure that affects all modules

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
