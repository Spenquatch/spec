# Codebase Refactoring Vertical Slices - Detailed Plan

This document outlines comprehensive vertical slices for refactoring the current monolithic `__main__.py` (1340+ lines) into a modular, maintainable, and extensible architecture following industry best practices for AI/ML/CLI pipelines.

## Current State Analysis

### Issues with Current Architecture
1. **Monolithic Design**: Single 1340+ line file with mixed concerns
2. **No Separation of Concerns**: CLI, business logic, and data access mixed together
3. **Difficult Testing**: Tightly coupled components make unit testing challenging
4. **Poor Extensibility**: Hard to add features like AI integration and Git hooks
5. **Code Duplication**: Similar patterns repeated throughout
6. **No Error Handling Strategy**: Ad-hoc error handling without consistent patterns
7. **Configuration Scattered**: Settings and configuration mixed throughout code

### Current Functionality to Preserve
- All existing CLI commands (`init`, `add`, `commit`, `log`, `diff`, `status`, `gen`)
- Template system with `.spectemplate` support
- Git integration with isolated repository
- File filtering and ignore patterns
- Debug logging and timing
- Conflict resolution workflows
- Directory traversal and file processing

## Target Architecture

### Architectural Principles
- **Single Responsibility Principle**: Each module has one clear purpose
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Interface Segregation**: Small, focused interfaces
- **Command Pattern**: Commands as objects for better testing and extensibility
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Centralized object creation
- **Plugin Architecture**: Easy extension for AI and Git hooks

### Target Structure
```
spec_cli/
├── __init__.py
├── __main__.py              # Thin entry point only (~50 lines)
├── cli/                     # Command-line interface layer
│   ├── __init__.py
│   ├── commands.py          # Command definitions and parsing
│   ├── runner.py            # Command execution coordination
│   └── validators.py        # CLI input validation
├── core/                    # Core business logic
│   ├── __init__.py
│   ├── spec_repository.py   # Main spec operations orchestration
│   ├── file_processor.py    # File processing logic
│   ├── conflict_resolver.py # Conflict handling logic
│   └── workflow_manager.py  # Multi-step operation coordination
├── git/                     # Git operations abstraction
│   ├── __init__.py
│   ├── repository.py        # Git repository interface
│   ├── operations.py        # Git command wrapper
│   └── path_converter.py    # Path conversion utilities
├── templates/               # Shared template system
│   ├── __init__.py
│   ├── config.py            # TemplateConfig and validation
│   ├── loader.py            # Template loading from files
│   ├── generator.py         # Content generation
│   └── substitution.py     # Variable substitution
├── file_system/             # File system operations
│   ├── __init__.py
│   ├── path_resolver.py     # Path resolution and validation
│   ├── directory_manager.py # Directory creation and management
│   ├── file_analyzer.py     # File type detection and analysis
│   └── ignore_patterns.py   # .specignore handling
├── config/                  # Configuration management
│   ├── __init__.py
│   ├── settings.py          # Global settings and environment
│   ├── loader.py            # Configuration file loading
│   └── validation.py        # Configuration validation
├── exceptions.py            # Custom exception hierarchy
├── logging/                 # Logging and debugging
│   ├── __init__.py
│   ├── debug.py             # Debug logging utilities
│   ├── timing.py            # Performance timing
│   └── formatters.py        # Log formatters
└── utils/                   # Shared utilities
    ├── __init__.py
    ├── decorators.py         # Common decorators
    └── helpers.py            # Helper functions
```

## Technology Stack

### Core Libraries (Existing)
- **pathlib**: File system operations
- **subprocess**: Git command execution
- **yaml**: Configuration file parsing
- **pydantic**: Data validation and settings

### New Libraries for Improved Architecture
- **abc**: Abstract base classes for interfaces
- **typing**: Enhanced type hints
- **dataclasses**: Data structures
- **functools**: Decorators and utilities
- **contextlib**: Context managers

## Vertical Slice Breakdown

### Slice 1: Core Infrastructure and Exception Hierarchy
**Goal**: Establish foundational infrastructure with proper exception handling

**Implementation Details**:
- Create custom exception hierarchy for different error types
- Implement logging infrastructure with structured debugging
- Create base interfaces and abstract classes
- Establish typing patterns and data structures
- Set up performance timing infrastructure

**Files to Create**:
```
spec_cli/exceptions.py
spec_cli/logging/
├── __init__.py
├── debug.py
├── timing.py
└── formatters.py
spec_cli/utils/
├── __init__.py
├── decorators.py
└── helpers.py
```

**Detailed Implementation**:

**spec_cli/exceptions.py**:
```python
from typing import Dict, Any, Optional, List

class SpecError(Exception):
    """Base exception for all spec-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return self.message
    
    def get_context(self) -> Dict[str, Any]:
        """Get error context for debugging."""
        return self.context

class SpecNotInitializedError(SpecError):
    """Raised when spec operations are attempted in uninitialized directory."""
    pass

class SpecPermissionError(SpecError):
    """Raised when permission is denied for spec operations."""
    pass

class SpecGitError(SpecError):
    """Raised when Git operations fail."""
    pass

class SpecConfigurationError(SpecError):
    """Raised when configuration is invalid."""
    pass

class SpecTemplateError(SpecError):
    """Raised when template processing fails."""
    pass

class SpecFileError(SpecError):
    """Raised when file operations fail."""
    pass

class SpecValidationError(SpecError):
    """Raised when validation fails."""
    pass
```

**spec_cli/logging/debug.py**:
```python
import logging
import os
import time
from typing import Any, Dict, Optional
from contextlib import contextmanager

class DebugLogger:
    """Enhanced debug logging with structured output."""
    
    def __init__(self):
        self.enabled = self._is_debug_enabled()
        self.level = self._get_debug_level()
        self.timing_enabled = self._is_timing_enabled()
        self.logger = self._setup_logger()
    
    def _is_debug_enabled(self) -> bool:
        return os.environ.get("SPEC_DEBUG", "").lower() in ["1", "true", "yes"]
    
    def _get_debug_level(self) -> str:
        return os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
    
    def _is_timing_enabled(self) -> bool:
        return os.environ.get("SPEC_DEBUG_TIMING", "").lower() in ["1", "true", "yes"]
    
    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message with structured data."""
        if not self.enabled:
            return
        
        # Format structured data
        extra_data = ""
        if kwargs:
            extra_parts = [f"{key}={value}" for key, value in kwargs.items()]
            extra_data = f" ({', '.join(extra_parts)})"
        
        full_message = f"{message}{extra_data}"
        level_method = getattr(self.logger, level.lower(), self.logger.info)
        level_method(full_message)
    
    @contextmanager
    def timer(self, operation_name: str):
        """Context manager for timing operations."""
        if not self.timing_enabled:
            yield
            return
        
        start_time = time.perf_counter()
        self.log("INFO", f"Starting {operation_name}")
        
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.log("INFO", f"Completed {operation_name}", 
                    duration_ms=f"{elapsed * 1000:.2f}ms")

# Global instance
debug_logger = DebugLogger()
```

**spec_cli/utils/decorators.py**:
```python
from functools import wraps
from typing import Callable, Any
from ..exceptions import SpecError
from ..logging.debug import debug_logger

def handle_errors(error_type: type = SpecError):
    """Decorator to handle and convert exceptions to SpecError types."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except error_type:
                raise  # Re-raise SpecError types
            except Exception as e:
                # Convert other exceptions to SpecError
                context = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
                raise SpecError(f"Error in {func.__name__}: {e}", context) from e
        return wrapper
    return decorator

def debug_timing(operation_name: str = None):
    """Decorator to add debug timing to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            name = operation_name or func.__name__
            with debug_logger.timer(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Tests to Write** (15 comprehensive tests):
- `tests/unit/test_exceptions.py`:
  - `test_spec_error_includes_context_information`
  - `test_spec_error_provides_user_friendly_messages`
  - `test_exception_hierarchy_inheritance_correct`
  - `test_custom_exceptions_preserve_original_traceback`

- `tests/unit/logging/test_debug.py`:
  - `test_debug_logger_respects_environment_variables`
  - `test_debug_logger_formats_structured_data`
  - `test_debug_timing_measures_operation_duration`
  - `test_debug_logger_handles_different_log_levels`

- `tests/unit/utils/test_decorators.py`:
  - `test_handle_errors_decorator_converts_exceptions`
  - `test_handle_errors_decorator_preserves_spec_errors`
  - `test_debug_timing_decorator_logs_operation_time`
  - `test_decorators_preserve_function_metadata`
  - `test_decorators_work_with_async_functions`
  - `test_error_handling_includes_function_context`
  - `test_timing_decorator_handles_exceptions_gracefully`

**Quality Checks**:
```bash
poetry run pytest tests/unit/test_exceptions.py tests/unit/logging/ tests/unit/utils/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80
poetry run mypy spec_cli/exceptions.py spec_cli/logging/ spec_cli/utils/
poetry run ruff check --fix spec_cli/exceptions.py spec_cli/logging/ spec_cli/utils/
```

**Commit**: `feat: implement slice 1 - core infrastructure and exception hierarchy`

### Slice 2: Configuration Management System
**Goal**: Extract and centralize all configuration handling with proper validation

**Implementation Details**:
- Create centralized configuration management system
- Extract environment variable handling
- Implement configuration file loading with precedence
- Add configuration validation and defaults
- Create settings injection for dependency management

**Files to Create**:
```
spec_cli/config/
├── __init__.py
├── settings.py          # Global settings and environment
├── loader.py            # Configuration file loading
└── validation.py        # Configuration validation
```

**Detailed Implementation**:

**spec_cli/config/settings.py**:
```python
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from ..exceptions import SpecConfigurationError

@dataclass
class SpecSettings:
    """Global settings for spec operations."""
    
    # Directory paths
    root_path: Path = field(default_factory=Path.cwd)
    spec_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)
    index_file: Path = field(init=False)
    ignore_file: Path = field(init=False)
    template_file: Path = field(init=False)
    gitignore_file: Path = field(init=False)
    
    # Debug settings
    debug_enabled: bool = field(init=False)
    debug_level: str = field(init=False)
    debug_timing: bool = field(init=False)
    
    def __post_init__(self):
        """Initialize computed paths and environment settings."""
        self.spec_dir = self.root_path / ".spec"
        self.specs_dir = self.root_path / ".specs"
        self.index_file = self.root_path / ".spec-index"
        self.ignore_file = self.root_path / ".specignore"
        self.template_file = self.root_path / ".spectemplate"
        self.gitignore_file = self.root_path / ".gitignore"
        
        # Environment-based settings
        self.debug_enabled = self._get_bool_env("SPEC_DEBUG", False)
        self.debug_level = os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
        self.debug_timing = self._get_bool_env("SPEC_DEBUG_TIMING", False)
    
    def _get_bool_env(self, var_name: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.environ.get(var_name, "").lower()
        if value in ["1", "true", "yes"]:
            return True
        elif value in ["0", "false", "no"]:
            return False
        return default
    
    def is_initialized(self) -> bool:
        """Check if spec is initialized in the directory."""
        return (
            self.spec_dir.exists() and 
            self.spec_dir.is_dir() and
            self.specs_dir.exists() and
            self.specs_dir.is_dir()
        )
    
    def validate_permissions(self) -> None:
        """Validate required permissions for spec operations."""
        if self.is_initialized():
            if not os.access(self.spec_dir, os.W_OK):
                raise SpecConfigurationError(f"No write permission for {self.spec_dir}")
            if not os.access(self.specs_dir, os.W_OK):
                raise SpecConfigurationError(f"No write permission for {self.specs_dir}")

class SettingsManager:
    """Manages global settings instance."""
    
    _instance: Optional[SpecSettings] = None
    
    @classmethod
    def get_settings(cls, root_path: Optional[Path] = None) -> SpecSettings:
        """Get global settings instance."""
        if cls._instance is None or (root_path and root_path != cls._instance.root_path):
            cls._instance = SpecSettings(root_path or Path.cwd())
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset settings for testing."""
        cls._instance = None

# Convenience function for getting settings
def get_settings(root_path: Optional[Path] = None) -> SpecSettings:
    return SettingsManager.get_settings(root_path)
```

**spec_cli/config/loader.py**:
```python
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..exceptions import SpecConfigurationError

class ConfigurationLoader:
    """Loads configuration from various sources with precedence."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.config_sources = [
            root_path / ".specconfig.yaml",
            root_path / "pyproject.toml",
        ]
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from available sources."""
        config = {}
        
        # Load from each source in order (later sources override earlier ones)
        for source in self.config_sources:
            if source.exists():
                try:
                    source_config = self._load_from_file(source)
                    config.update(source_config)
                except Exception as e:
                    raise SpecConfigurationError(
                        f"Failed to load configuration from {source}: {e}"
                    ) from e
        
        # Environment variables override file configuration
        env_config = self._load_from_environment()
        config.update(env_config)
        
        return config
    
    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a specific file."""
        if file_path.name == "pyproject.toml":
            return self._load_from_pyproject_toml(file_path)
        elif file_path.suffix in [".yaml", ".yml"]:
            return self._load_from_yaml(file_path)
        else:
            return {}
    
    def _load_from_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    
    def _load_from_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from pyproject.toml [tool.spec] section."""
        try:
            import tomli
        except ImportError:
            import tomllib as tomli
        
        with file_path.open("rb") as f:
            data = tomli.load(f)
        
        return data.get("tool", {}).get("spec", {})
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        # Implementation for environment variable configuration
        return {}
```

**Tests to Write** (18 comprehensive tests):
- `tests/unit/config/test_settings.py`:
  - `test_spec_settings_initializes_with_correct_paths`
  - `test_spec_settings_detects_debug_environment_variables`
  - `test_spec_settings_validates_initialization_state`
  - `test_spec_settings_validates_permissions`
  - `test_settings_manager_provides_singleton_behavior`
  - `test_settings_manager_handles_root_path_changes`

- `tests/unit/config/test_loader.py`:
  - `test_configuration_loader_loads_from_yaml`
  - `test_configuration_loader_loads_from_pyproject_toml`
  - `test_configuration_loader_handles_missing_files`
  - `test_configuration_loader_respects_precedence_order`
  - `test_configuration_loader_handles_malformed_files`
  - `test_configuration_loader_loads_environment_variables`

- `tests/unit/config/test_validation.py`:
  - `test_configuration_validation_accepts_valid_config`
  - `test_configuration_validation_rejects_invalid_config`
  - `test_configuration_validation_provides_helpful_errors`
  - `test_configuration_validation_handles_missing_sections`
  - `test_configuration_validation_validates_file_paths`
  - `test_configuration_validation_validates_environment_settings`

**Quality Checks**: 80%+ coverage including error scenarios

**Commit**: `feat: implement slice 2 - configuration management system`

### Slice 3: File System Operations Abstraction
**Goal**: Extract all file system operations into organized, testable modules

**Implementation Details**:
- Create path resolution and validation utilities
- Implement directory management operations
- Extract file type detection and analysis
- Organize ignore pattern handling
- Create file operation abstractions with proper error handling

**Files to Create**:
```
spec_cli/file_system/
├── __init__.py
├── path_resolver.py     # Path resolution and validation
├── directory_manager.py # Directory creation and management
├── file_analyzer.py     # File type detection and analysis
└── ignore_patterns.py   # .specignore handling
```

**Detailed Implementation**:

**spec_cli/file_system/path_resolver.py**:
```python
from pathlib import Path
from typing import List, Optional
from ..exceptions import SpecFileError, SpecValidationError
from ..config.settings import get_settings
from ..utils.decorators import handle_errors

class PathResolver:
    """Handles path resolution and validation for spec operations."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
    
    @handle_errors(SpecFileError)
    def resolve_file_path(self, path_str: str) -> Path:
        """Resolve and validate a file path for spec generation."""
        input_path = Path(path_str)
        
        # Handle "." for current directory
        if path_str == ".":
            return Path.cwd()
        
        # Handle absolute paths - convert to relative to root
        if input_path.is_absolute():
            try:
                resolved_path = input_path.relative_to(self.settings.root_path)
            except ValueError as e:
                raise SpecValidationError(
                    f"Path is outside project root: {input_path}"
                ) from e
        else:
            # Relative path - resolve relative to current working directory
            resolved_path = input_path.resolve().relative_to(self.settings.root_path)
        
        # Validate file existence and type
        full_path = self.settings.root_path / resolved_path
        
        if not full_path.exists():
            raise SpecFileError(f"File not found: {full_path}")
        
        if full_path.is_dir():
            return resolved_path  # Directory is valid for gen command
        
        if not full_path.is_file():
            raise SpecValidationError(f"Path is not a regular file: {full_path}")
        
        return resolved_path
    
    def resolve_spec_directory_path(self, file_path: Path) -> Path:
        """Convert file path to corresponding spec directory path."""
        # e.g., src/models.py -> .specs/src/models/
        return self.settings.specs_dir / file_path.parent / file_path.stem
    
    def resolve_relative_to_specs(self, path: Path) -> Path:
        """Convert path to be relative to .specs directory."""
        if path.is_absolute():
            try:
                return path.relative_to(self.settings.specs_dir)
            except ValueError:
                return path
        elif str(path).startswith(".specs/"):
            return Path(str(path).replace(".specs/", "", 1))
        return path
    
    def is_within_project(self, path: Path) -> bool:
        """Check if path is within the project root."""
        try:
            if path.is_absolute():
                path.relative_to(self.settings.root_path)
            return True
        except ValueError:
            return False
```

**spec_cli/file_system/file_analyzer.py**:
```python
from pathlib import Path
from typing import Set, Dict, Any, List
import stat
from ..exceptions import SpecFileError
from ..utils.decorators import handle_errors

class FileAnalyzer:
    """Analyzes files for type detection, filtering, and metadata extraction."""
    
    # File type mappings
    LANGUAGE_EXTENSIONS = {
        # Programming languages
        ".py": "python", ".pyx": "python", ".pyi": "python",
        ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript",
        ".java": "java", ".class": "java",
        ".c": "c", ".h": "c",
        ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp",
        ".rs": "rust",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin", ".kts": "kotlin",
        ".scala": "scala",
        ".cs": "csharp",
        ".vb": "visualbasic",
        
        # Web technologies
        ".html": "html", ".htm": "html",
        ".css": "css", ".scss": "css", ".sass": "css", ".less": "css",
        ".xml": "xml", ".xsl": "xml", ".xsd": "xml",
        
        # Data formats
        ".json": "json",
        ".yaml": "yaml", ".yml": "yaml",
        ".toml": "toml",
        ".csv": "csv",
        ".sql": "sql",
        
        # Documentation
        ".md": "markdown", ".markdown": "markdown",
        ".rst": "restructuredtext",
        ".txt": "text",
        
        # Configuration
        ".conf": "config", ".config": "config", ".cfg": "config", ".ini": "config",
        ".env": "environment",
        
        # Build files
        ".mk": "build", ".make": "build",
    }
    
    SPECIAL_FILENAMES = {
        "makefile": "build",
        "dockerfile": "build", 
        "vagrantfile": "build",
        "rakefile": "build",
        ".env": "environment",
    }
    
    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".a", ".lib",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
        ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav", ".flac",
    }
    
    @handle_errors(SpecFileError)
    def get_file_type(self, file_path: Path) -> str:
        """Determine the file type category based on file extension and name."""
        extension = file_path.suffix.lower()
        filename = file_path.name.lower()
        
        # Check special filenames first
        if filename in self.SPECIAL_FILENAMES:
            return self.SPECIAL_FILENAMES[filename]
        
        # Check extensions
        if extension in self.LANGUAGE_EXTENSIONS:
            return self.LANGUAGE_EXTENSIONS[extension]
        
        # No extension or unknown
        if not extension:
            return "no_extension"
        
        return "unknown"
    
    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary based on extension."""
        extension = file_path.suffix.lower()
        return extension in self.BINARY_EXTENSIONS
    
    def is_processable_file(self, file_path: Path) -> bool:
        """Check if file should be processed for spec generation."""
        if self.is_binary_file(file_path):
            return False
        
        file_type = self.get_file_type(file_path)
        if file_type == "unknown":
            return False
        
        # Check file size (skip very large files)
        try:
            full_path = file_path if file_path.is_absolute() else Path.cwd() / file_path
            if full_path.exists() and full_path.stat().st_size > 1_048_576:  # 1MB
                return False
        except OSError:
            pass
        
        return True
    
    @handle_errors(SpecFileError)
    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata about a file."""
        try:
            full_path = file_path if file_path.is_absolute() else Path.cwd() / file_path
            stat_info = full_path.stat()
            
            return {
                "size": stat_info.st_size,
                "modified_time": stat_info.st_mtime,
                "permissions": stat.filemode(stat_info.st_mode),
                "file_type": self.get_file_type(file_path),
                "is_binary": self.is_binary_file(file_path),
                "is_processable": self.is_processable_file(file_path),
            }
        except OSError as e:
            raise SpecFileError(f"Cannot access file metadata for {file_path}: {e}") from e
```

**Tests to Write** (22 comprehensive tests):
- `tests/unit/file_system/test_path_resolver.py`:
  - `test_path_resolver_resolves_relative_paths`
  - `test_path_resolver_resolves_absolute_paths`
  - `test_path_resolver_handles_current_directory`
  - `test_path_resolver_validates_file_existence`
  - `test_path_resolver_rejects_paths_outside_project`
  - `test_path_resolver_converts_to_spec_directory_paths`
  - `test_path_resolver_handles_specs_relative_paths`

- `tests/unit/file_system/test_file_analyzer.py`:
  - `test_file_analyzer_detects_programming_languages`
  - `test_file_analyzer_detects_web_technologies`
  - `test_file_analyzer_detects_data_formats`
  - `test_file_analyzer_detects_special_filenames`
  - `test_file_analyzer_identifies_binary_files`
  - `test_file_analyzer_determines_processable_files`
  - `test_file_analyzer_extracts_file_metadata`
  - `test_file_analyzer_handles_missing_files`
  - `test_file_analyzer_handles_permission_errors`

- `tests/unit/file_system/test_directory_manager.py`:
  - `test_directory_manager_creates_spec_directories`
  - `test_directory_manager_handles_existing_directories`
  - `test_directory_manager_validates_permissions`

- `tests/unit/file_system/test_ignore_patterns.py`:
  - `test_ignore_patterns_loads_from_specignore_file`
  - `test_ignore_patterns_applies_default_patterns`
  - `test_ignore_patterns_matches_files_correctly`
  - `test_ignore_patterns_handles_directory_patterns`
  - `test_ignore_patterns_supports_glob_patterns`

**Quality Checks**: 80%+ coverage including error paths

**Commit**: `feat: implement slice 3 - file system operations abstraction`

### Slice 4: Template System Refactoring (Shared Module)
**Goal**: Extract template system into shared module for use by cmd_gen and future git hooks

**Implementation Details**:
- Move template-related code from `__main__.py` to dedicated module
- Create clean interfaces for template loading and generation
- Add comprehensive validation and error handling
- Ensure backward compatibility with existing `.spectemplate` files
- Design for extensibility (AI content injection, custom templates)

**Files to Create**:
```
spec_cli/templates/
├── __init__.py           # Public API exports
├── config.py            # TemplateConfig and validation
├── loader.py            # Template loading from files
├── generator.py         # Content generation
└── substitution.py      # Variable substitution engine
```

**Detailed Implementation**:

**spec_cli/templates/config.py**:
```python
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from pathlib import Path
from ..exceptions import SpecTemplateError

class TemplateConfig(BaseModel):
    """Configuration for spec template generation."""
    
    index: str = Field(
        default=\"\"\"# {{filename}}

**Location**: {{filepath}}

**Purpose**: {{purpose}}

**Responsibilities**:
{{responsibilities}}

**Requirements**:
{{requirements}}

**Example Usage**:
```{{file_extension}}
{{example_usage}}
```

**Notes**:
{{notes}}
\"\"\",
        description="Template for index.md file",
    )
    
    history: str = Field(
        default=\"\"\"# History for {{filename}}

## {{date}} - Initial Creation

**Purpose**: Created initial specification for {{filename}}

**Context**: {{context}}

**Decisions**: {{decisions}}

**Lessons Learned**: {{lessons}}
\"\"\",
        description="Template for history.md file",
    )
    
    @validator('index', 'history')
    def validate_template_syntax(cls, v):
        """Validate template syntax and required placeholders."""
        if not v.strip():
            raise ValueError("Template cannot be empty")
        
        # Check for basic placeholders
        required_placeholders = ['{{filename}}']
        for placeholder in required_placeholders:
            if placeholder not in v:
                raise ValueError(f"Template must contain {placeholder} placeholder")
        
        return v
    
    def get_available_variables(self) -> Dict[str, str]:
        """Get all available template variables with descriptions."""
        return {
            "filename": "Name of the source file",
            "filepath": "Full path to the source file",
            "date": "Current date in YYYY-MM-DD format",
            "file_extension": "File extension without the dot",
            "purpose": "Purpose of the file (AI-generated or placeholder)",
            "responsibilities": "Responsibilities of the file (AI-generated or placeholder)",
            "requirements": "Requirements and dependencies (AI-generated or placeholder)",
            "example_usage": "Example usage code (AI-generated or placeholder)",
            "notes": "Additional notes (AI-generated or placeholder)",
            "context": "Context for creation (AI-generated or placeholder)",
            "decisions": "Decisions made (AI-generated or placeholder)",
            "lessons": "Lessons learned (AI-generated or placeholder)",
        }

class TemplateValidator:
    """Validates template configuration and syntax."""
    
    def validate_config(self, config: TemplateConfig) -> List[str]:
        """Validate template configuration and return list of issues."""
        issues = []
        
        # Check for common template issues
        for template_name, template_content in [("index", config.index), ("history", config.history)]:
            issues.extend(self._validate_template_content(template_name, template_content))
        
        return issues
    
    def _validate_template_content(self, name: str, content: str) -> List[str]:
        """Validate individual template content."""
        issues = []
        
        # Check for unmatched braces
        open_braces = content.count('{{')
        close_braces = content.count('}}')
        if open_braces != close_braces:
            issues.append(f"{name} template has unmatched template braces")
        
        # Check for malformed placeholders
        import re
        malformed = re.findall(r'{[^{]|[^}]}', content)
        if malformed:
            issues.append(f"{name} template has malformed placeholders: {malformed}")
        
        return issues
```

**spec_cli/templates/loader.py**:
```python
import yaml
from pathlib import Path
from typing import Optional
from .config import TemplateConfig, TemplateValidator
from ..config.settings import get_settings
from ..exceptions import SpecTemplateError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class TemplateLoader:
    """Loads template configuration from files or provides defaults."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.validator = TemplateValidator()
    
    @handle_errors(SpecTemplateError)
    def load_template(self) -> TemplateConfig:
        """Load template configuration from .spectemplate file or use defaults."""
        template_file = self.settings.template_file
        
        if not template_file.exists():
            debug_logger.log("INFO", "No .spectemplate file found, using default template")
            return TemplateConfig()
        
        try:
            with template_file.open("r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)
            
            debug_logger.log("INFO", "Loaded template from file", 
                           template_file=str(template_file))
            
            # Handle empty YAML file
            if template_data is None:
                template_data = {}
            
            # Validate before creating config
            config = TemplateConfig(**template_data)
            validation_issues = self.validator.validate_config(config)
            
            if validation_issues:
                raise SpecTemplateError(
                    f"Template validation failed: {'; '.join(validation_issues)}"
                )
            
            return config
            
        except yaml.YAMLError as e:
            raise SpecTemplateError(
                f"Invalid YAML in template file {template_file}: {e}"
            ) from e
        except Exception as e:
            raise SpecTemplateError(
                f"Failed to load template configuration from {template_file}: {e}"
            ) from e
    
    def save_template(self, config: TemplateConfig) -> None:
        """Save template configuration to .spectemplate file."""
        try:
            template_data = {
                "index": config.index,
                "history": config.history
            }
            
            with self.settings.template_file.open("w", encoding="utf-8") as f:
                yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
                
            debug_logger.log("INFO", "Saved template configuration",
                           template_file=str(self.settings.template_file))
                           
        except Exception as e:
            raise SpecTemplateError(
                f"Failed to save template configuration: {e}"
            ) from e

# Convenience function for backward compatibility
def load_template() -> TemplateConfig:
    """Load template configuration (backward compatibility function)."""
    loader = TemplateLoader()
    return loader.load_template()
```

**spec_cli/templates/generator.py**:
```python
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .config import TemplateConfig
from .substitution import TemplateSubstitution
from ..config.settings import get_settings
from ..exceptions import SpecTemplateError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class SpecContentGenerator:
    """Generates spec content files using template substitution."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.substitution = TemplateSubstitution()
    
    @handle_errors(SpecTemplateError)
    def generate_spec_content(
        self, 
        file_path: Path, 
        spec_dir: Path, 
        template: TemplateConfig,
        custom_variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """Generate spec content files using template substitution."""
        
        # Prepare base substitution variables
        substitutions = self._prepare_substitutions(file_path, custom_variables or {})
        
        try:
            # Generate index.md content
            index_content = self.substitution.substitute(template.index, substitutions)
            index_file = spec_dir / "index.md"
            index_file.write_text(index_content, encoding="utf-8")
            
            # Generate history.md content
            history_content = self.substitution.substitute(template.history, substitutions)
            history_file = spec_dir / "history.md"
            history_file.write_text(history_content, encoding="utf-8")
            
            debug_logger.log(
                "INFO",
                "Generated spec content files",
                index_chars=len(index_content),
                history_chars=len(history_content),
                spec_dir=str(spec_dir)
            )
            
        except OSError as e:
            raise SpecTemplateError(f"Failed to write spec files to {spec_dir}: {e}") from e
    
    def _prepare_substitutions(self, file_path: Path, custom_variables: Dict[str, Any]) -> Dict[str, str]:
        """Prepare template substitution variables."""
        now = datetime.now()
        
        base_substitutions = {
            "filename": file_path.name,
            "filepath": str(file_path),
            "date": now.strftime("%Y-%m-%d"),
            "file_extension": file_path.suffix.lstrip(".") or "txt",
            # Default placeholder values (can be overridden by AI or custom variables)
            "purpose": "[Generated by spec-cli - to be filled]",
            "responsibilities": "[Generated by spec-cli - to be filled]",
            "requirements": "[Generated by spec-cli - to be filled]",
            "example_usage": "[Generated by spec-cli - to be filled]",
            "notes": "[Generated by spec-cli - to be filled]",
            "context": "[Generated by spec-cli - to be filled]",
            "decisions": "[Generated by spec-cli - to be filled]",
            "lessons": "[Generated by spec-cli - to be filled]",
        }
        
        # Custom variables override defaults
        base_substitutions.update(custom_variables)
        
        return base_substitutions

# Convenience function for backward compatibility
def generate_spec_content(file_path: Path, spec_dir: Path, template: TemplateConfig) -> None:
    """Generate spec content (backward compatibility function)."""
    generator = SpecContentGenerator()
    generator.generate_spec_content(file_path, spec_dir, template)
```

**Tests to Write** (25 comprehensive tests):
- `tests/unit/templates/test_config.py`:
  - `test_template_config_validates_required_placeholders`
  - `test_template_config_provides_default_templates`
  - `test_template_config_validates_template_syntax`
  - `test_template_config_lists_available_variables`
  - `test_template_validator_detects_unmatched_braces`
  - `test_template_validator_detects_malformed_placeholders`

- `tests/unit/templates/test_loader.py`:
  - `test_template_loader_loads_from_spectemplate_file`
  - `test_template_loader_uses_defaults_when_file_missing`
  - `test_template_loader_handles_empty_yaml_file`
  - `test_template_loader_validates_loaded_templates`
  - `test_template_loader_handles_invalid_yaml`
  - `test_template_loader_saves_template_configuration`

- `tests/unit/templates/test_generator.py`:
  - `test_generator_creates_index_and_history_files`
  - `test_generator_substitutes_variables_correctly`
  - `test_generator_handles_custom_variables`
  - `test_generator_uses_proper_file_encoding`
  - `test_generator_handles_file_write_errors`
  - `test_generator_logs_generation_operations`

- `tests/unit/templates/test_substitution.py`:
  - `test_substitution_replaces_all_placeholders`
  - `test_substitution_handles_missing_placeholders_gracefully`
  - `test_substitution_preserves_non_template_content`
  - `test_substitution_handles_special_characters`

- `tests/unit/templates/test_integration.py`:
  - `test_templates_maintain_backward_compatibility`
  - `test_templates_work_with_existing_spectemplate_files`
  - `test_templates_integrate_with_config_system`
  - `test_templates_support_extensibility_for_ai`

**Backward Compatibility**:
Ensure existing imports continue to work:
```python
# These should still work after refactoring
from spec_cli.templates import load_template, generate_spec_content, TemplateConfig
```

**Quality Checks**: 80%+ coverage including template validation

**Commit**: `feat: implement slice 4 - template system refactoring (shared module)`

### Slice 5: Git Operations Abstraction
**Goal**: Extract Git operations into clean, testable interface

**Implementation Details**:
- Abstract Git command execution with proper error handling
- Create repository interface for Git operations
- Extract path conversion utilities for Git work tree
- Add Git operation validation and safety checks
- Design interface to support git hooks integration

**Files to Create**:
```
spec_cli/git/
├── __init__.py
├── repository.py        # Git repository interface
├── operations.py        # Git command wrapper
└── path_converter.py    # Path conversion utilities
```

**Detailed Implementation**:

**spec_cli/git/repository.py**:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..exceptions import SpecGitError

class GitRepository(ABC):
    """Abstract interface for Git repository operations."""
    
    @abstractmethod
    def add(self, paths: List[str]) -> None:
        """Add files to Git index."""
        pass
    
    @abstractmethod
    def commit(self, message: str) -> None:
        """Create a commit with the given message."""
        pass
    
    @abstractmethod
    def status(self) -> None:
        """Show repository status."""
        pass
    
    @abstractmethod
    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show commit log."""
        pass
    
    @abstractmethod
    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show differences."""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if repository is initialized."""
        pass

class SpecGitRepository(GitRepository):
    """Git repository implementation for spec operations."""
    
    def __init__(self, root_path: Path, spec_dir: Path, specs_dir: Path, index_file: Path):
        self.root_path = root_path
        self.spec_dir = spec_dir
        self.specs_dir = specs_dir
        self.index_file = index_file
        self.operations = GitOperations(
            spec_dir=spec_dir,
            specs_dir=specs_dir, 
            index_file=index_file
        )
        self.path_converter = GitPathConverter(specs_dir)
    
    def add(self, paths: List[str]) -> None:
        """Add files to spec Git index."""
        converted_paths = [self.path_converter.convert_to_git_path(path) for path in paths]
        self.operations.run_git_command(["add", "-f"] + converted_paths)
    
    def commit(self, message: str) -> None:
        """Create commit in spec repository."""
        self.operations.run_git_command(["commit", "-m", message])
    
    def status(self) -> None:
        """Show spec repository status."""
        self.operations.run_git_command(["status"])
    
    def log(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository log."""
        cmd = ["log"]
        if paths:
            converted_paths = [self.path_converter.convert_to_git_path(path) for path in paths]
            cmd.extend(["--"] + converted_paths)
        self.operations.run_git_command(cmd)
    
    def diff(self, paths: Optional[List[str]] = None) -> None:
        """Show spec repository diff."""
        cmd = ["diff"]
        if paths:
            converted_paths = [self.path_converter.convert_to_git_path(path) for path in paths]
            cmd.extend(["--"] + converted_paths)
        self.operations.run_git_command(cmd)
    
    def is_initialized(self) -> bool:
        """Check if spec repository is initialized."""
        return self.spec_dir.exists() and self.spec_dir.is_dir()
```

**spec_cli/git/operations.py**:
```python
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any
from ..exceptions import SpecGitError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class GitOperations:
    """Handles low-level Git command execution."""
    
    def __init__(self, spec_dir: Path, specs_dir: Path, index_file: Path):
        self.spec_dir = spec_dir
        self.specs_dir = specs_dir
        self.index_file = index_file
    
    @handle_errors(SpecGitError)
    def run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Execute Git command with spec environment configuration."""
        env = self._prepare_git_environment()
        cmd = self._prepare_git_command(args)
        
        debug_logger.log("INFO", "Running git command", command=" ".join(cmd))
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                check=True,
                capture_output=False,  # Let output go to stdout/stderr
                text=True
            )
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(cmd)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            raise SpecGitError(error_msg) from e
        except FileNotFoundError as e:
            raise SpecGitError("Git not found. Please ensure Git is installed and in PATH.") from e
    
    def _prepare_git_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Git command."""
        env = os.environ.copy()
        env.update({
            "GIT_DIR": str(self.spec_dir),
            "GIT_WORK_TREE": str(self.specs_dir),
            "GIT_INDEX_FILE": str(self.index_file),
        })
        
        debug_logger.log("DEBUG", "Git environment variables", 
                        git_dir=str(self.spec_dir),
                        git_work_tree=str(self.specs_dir),
                        git_index_file=str(self.index_file))
        
        return env
    
    def _prepare_git_command(self, args: List[str]) -> List[str]:
        """Prepare Git command with required flags."""
        return [
            "git",
            "-c", "core.excludesFile=",
            "-c", "core.ignoresCase=false",
            *args
        ]
    
    def initialize_repository(self) -> None:
        """Initialize bare Git repository for spec."""
        if not self.spec_dir.exists():
            self.spec_dir.mkdir(parents=True)
            subprocess.run(
                ["git", "init", "--bare", str(self.spec_dir)],
                check=True,
                capture_output=True
            )
            debug_logger.log("INFO", "Initialized spec Git repository", 
                           spec_dir=str(self.spec_dir))

class GitPathConverter:
    """Converts paths between different Git contexts."""
    
    def __init__(self, specs_dir: Path):
        self.specs_dir = specs_dir
    
    def convert_to_git_path(self, path: str) -> str:
        """Convert path to be relative to Git work tree."""
        path_obj = Path(path)
        
        # Convert absolute paths to relative to SPECS_DIR
        if path_obj.is_absolute():
            try:
                return str(path_obj.relative_to(self.specs_dir))
            except ValueError:
                return path  # Path is not under specs dir
        
        # Convert .specs/file.md to file.md
        if path.startswith(".specs/"):
            return path.replace(".specs/", "", 1)
        
        return path
```

**Tests to Write** (20 comprehensive tests):
- `tests/unit/git/test_repository.py`:
  - `test_spec_git_repository_adds_files_with_force_flag`
  - `test_spec_git_repository_creates_commits`
  - `test_spec_git_repository_shows_status`
  - `test_spec_git_repository_shows_log_with_paths`
  - `test_spec_git_repository_shows_diff_with_paths`
  - `test_spec_git_repository_detects_initialization_status`
  - `test_spec_git_repository_converts_paths_correctly`

- `tests/unit/git/test_operations.py`:
  - `test_git_operations_prepares_environment_correctly`
  - `test_git_operations_executes_commands_successfully`
  - `test_git_operations_handles_command_failures`
  - `test_git_operations_handles_missing_git_binary`
  - `test_git_operations_logs_command_execution`
  - `test_git_operations_initializes_repository`

- `tests/unit/git/test_path_converter.py`:
  - `test_path_converter_converts_absolute_paths`
  - `test_path_converter_converts_specs_relative_paths`
  - `test_path_converter_handles_regular_relative_paths`
  - `test_path_converter_handles_paths_outside_specs_dir`

- `tests/unit/git/test_integration.py`:
  - `test_git_operations_integrate_with_config_system`
  - `test_git_operations_maintain_backward_compatibility`
  - `test_git_operations_support_hook_integration`

**Quality Checks**: 80%+ coverage including Git error scenarios

**Commit**: `feat: implement slice 5 - Git operations abstraction`

### Slice 6: Core Business Logic Extraction
**Goal**: Extract core business logic into organized, testable services

**Implementation Details**:
- Create spec repository service for orchestrating operations
- Extract file processing logic with proper separation of concerns
- Implement conflict resolution as a separate service
- Create workflow manager for multi-step operations
- Design services for easy testing and extension

**Files to Create**:
```
spec_cli/core/
├── __init__.py
├── spec_repository.py   # Main spec operations orchestration
├── file_processor.py    # File processing logic
├── conflict_resolver.py # Conflict handling logic
└── workflow_manager.py  # Multi-step operation coordination
```

**Detailed Implementation**:

**spec_cli/core/spec_repository.py**:
```python
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..config.settings import get_settings, SpecSettings
from ..git.repository import SpecGitRepository
from ..templates.loader import TemplateLoader
from ..file_system.path_resolver import PathResolver
from ..file_system.directory_manager import DirectoryManager
from ..exceptions import SpecError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class SpecRepository:
    """Main service for spec repository operations."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.git_repo = SpecGitRepository(
            root_path=self.settings.root_path,
            spec_dir=self.settings.spec_dir,
            specs_dir=self.settings.specs_dir,
            index_file=self.settings.index_file
        )
        self.template_loader = TemplateLoader(self.settings)
        self.path_resolver = PathResolver(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
    
    @handle_errors(SpecError)
    def initialize(self) -> None:
        """Initialize spec repository."""
        with debug_logger.timer("spec_repository_initialization"):
            # Initialize Git repository
            if not self.git_repo.is_initialized():
                self.git_repo.operations.initialize_repository()
                debug_logger.log("INFO", "Initialized .spec/ repository")
            
            # Create .specs directory
            self.directory_manager.ensure_specs_directory()
            
            # Setup ignore files
            self.directory_manager.setup_ignore_files()
            
            # Update .gitignore
            self.directory_manager.update_main_gitignore()
    
    def add_files(self, paths: List[str]) -> None:
        """Add files to spec repository."""
        self.git_repo.add(paths)
    
    def commit_changes(self, message: str) -> None:
        """Commit changes to spec repository."""
        self.git_repo.commit(message)
    
    def show_status(self) -> None:
        """Show repository status."""
        self.git_repo.status()
    
    def show_log(self, paths: Optional[List[str]] = None) -> None:
        """Show commit log."""
        self.git_repo.log(paths)
    
    def show_diff(self, paths: Optional[List[str]] = None) -> None:
        """Show differences."""
        self.git_repo.diff(paths)
    
    def is_initialized(self) -> bool:
        """Check if spec repository is initialized."""
        return self.settings.is_initialized()
    
    def validate_operation(self, operation: str) -> None:
        """Validate that operation can be performed."""
        if operation != "init" and not self.is_initialized():
            raise SpecError("Spec repository not initialized. Run 'spec init' first.")
        
        if operation in ["add", "commit", "gen"]:
            self.settings.validate_permissions()
```

**spec_cli/core/file_processor.py**:
```python
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from ..file_system.file_analyzer import FileAnalyzer
from ..file_system.path_resolver import PathResolver
from ..file_system.directory_manager import DirectoryManager
from ..file_system.ignore_patterns import IgnorePatternMatcher
from ..templates.generator import SpecContentGenerator
from ..templates.loader import TemplateLoader
from ..core.conflict_resolver import ConflictResolver
from ..config.settings import get_settings, SpecSettings
from ..exceptions import SpecFileError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class FileProcessor:
    """Handles file processing operations for spec generation."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.file_analyzer = FileAnalyzer()
        self.path_resolver = PathResolver(self.settings)
        self.directory_manager = DirectoryManager(self.settings)
        self.ignore_matcher = IgnorePatternMatcher(self.settings)
        self.content_generator = SpecContentGenerator(self.settings)
        self.template_loader = TemplateLoader(self.settings)
        self.conflict_resolver = ConflictResolver(self.settings)
    
    @handle_errors(SpecFileError)
    def process_single_file(self, path_str: str, force: bool = False) -> bool:
        """Process a single file for spec generation."""
        with debug_logger.timer(f"process_single_file_{Path(path_str).name}"):
            # Resolve and validate path
            file_path = self.path_resolver.resolve_file_path(path_str)
            
            # Check if file should be processed
            if not self._should_process_file(file_path):
                debug_logger.log("INFO", "File skipped by filtering", 
                               file_path=str(file_path),
                               reason="filtered_out")
                return False
            
            # Create spec directory
            spec_dir = self.directory_manager.create_spec_directory(file_path)
            
            # Load template
            template = self.template_loader.load_template()
            
            # Handle conflicts if any exist
            if not force:
                existing_files = self.directory_manager.check_existing_specs(spec_dir)
                if any(existing_files.values()):
                    action = self.conflict_resolver.resolve_conflict(spec_dir, existing_files)
                    if not self.conflict_resolver.process_conflict_action(spec_dir, action):
                        return False
            
            # Generate content
            self.content_generator.generate_spec_content(file_path, spec_dir, template)
            
            debug_logger.log("INFO", "Successfully processed file",
                           file_path=str(file_path),
                           spec_dir=str(spec_dir))
            
            return True
    
    @handle_errors(SpecFileError)
    def process_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Process all files in a directory for spec generation."""
        with debug_logger.timer("process_directory"):
            # Find all processable files
            source_files = self._find_source_files(directory_path)
            
            if not source_files:
                return {
                    "total_files": 0,
                    "processed_count": 0,
                    "skipped_count": 0,
                    "error_count": 0,
                    "errors": []
                }
            
            # Load template once for all files
            template = self.template_loader.load_template()
            
            # Process files
            results = {
                "total_files": len(source_files),
                "processed_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "errors": []
            }
            
            for file_path in source_files:
                try:
                    relative_path = file_path.relative_to(self.settings.root_path)
                    
                    if not self._should_process_file(relative_path):
                        results["skipped_count"] += 1
                        continue
                    
                    # Create spec directory and generate content
                    spec_dir = self.directory_manager.create_spec_directory(relative_path)
                    
                    # Auto-resolve conflicts for batch processing
                    existing_files = self.directory_manager.check_existing_specs(spec_dir)
                    if any(existing_files.values()):
                        self.conflict_resolver.process_conflict_action(spec_dir, "overwrite")
                    
                    self.content_generator.generate_spec_content(relative_path, spec_dir, template)
                    results["processed_count"] += 1
                    
                except Exception as e:
                    results["error_count"] += 1
                    results["errors"].append({"file": str(file_path), "error": str(e)})
                    debug_logger.log("ERROR", "Error processing file",
                                   file_path=str(file_path), error=str(e))
            
            return results
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Determine if file should be processed."""
        # Check ignore patterns
        if self.ignore_matcher.should_ignore(file_path):
            return False
        
        # Check if file is processable
        return self.file_analyzer.is_processable_file(file_path)
    
    def _find_source_files(self, directory: Path) -> List[Path]:
        """Find all source files in directory recursively."""
        source_files = []
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Convert to relative path for consistent checking
                    try:
                        relative_path = file_path.relative_to(self.settings.root_path)
                        if self._should_process_file(relative_path):
                            source_files.append(file_path)
                    except ValueError:
                        # File is outside project root, skip
                        continue
        
        except OSError as e:
            raise SpecFileError(f"Failed to traverse directory {directory}: {e}") from e
        
        return sorted(source_files)
```

**Tests to Write** (25 comprehensive tests):
- `tests/unit/core/test_spec_repository.py`:
  - `test_spec_repository_initializes_correctly`
  - `test_spec_repository_validates_operations`
  - `test_spec_repository_handles_git_operations`
  - `test_spec_repository_checks_initialization_status`
  - `test_spec_repository_integrates_with_all_services`

- `tests/unit/core/test_file_processor.py`:
  - `test_file_processor_processes_single_file`
  - `test_file_processor_handles_file_conflicts`
  - `test_file_processor_processes_directory_batch`
  - `test_file_processor_filters_files_correctly`
  - `test_file_processor_handles_processing_errors`
  - `test_file_processor_creates_spec_directories`
  - `test_file_processor_generates_content_with_templates`
  - `test_file_processor_respects_ignore_patterns`

- `tests/unit/core/test_conflict_resolver.py`:
  - `test_conflict_resolver_detects_existing_files`
  - `test_conflict_resolver_provides_resolution_options`
  - `test_conflict_resolver_handles_user_choices`
  - `test_conflict_resolver_creates_backups_when_requested`
  - `test_conflict_resolver_processes_conflict_actions`

- `tests/unit/core/test_workflow_manager.py`:
  - `test_workflow_manager_coordinates_multi_step_operations`
  - `test_workflow_manager_handles_workflow_failures`
  - `test_workflow_manager_provides_progress_tracking`
  - `test_workflow_manager_supports_rollback_operations`

- `tests/unit/core/test_integration.py`:
  - `test_core_services_integrate_properly`
  - `test_core_services_handle_cross_cutting_concerns`
  - `test_core_services_maintain_transaction_boundaries`
  - `test_core_services_support_dependency_injection`
  - `test_core_services_provide_consistent_error_handling`

**Quality Checks**: 80%+ coverage including business logic edge cases

**Commit**: `feat: implement slice 6 - core business logic extraction`

### Slice 7: CLI Layer Refactoring
**Goal**: Create clean CLI layer with command pattern and minimal business logic

**Implementation Details**:
- Implement command pattern for all CLI operations
- Create thin CLI layer that delegates to core services
- Extract argument parsing and validation
- Implement command runner with proper error handling
- Design CLI for easy testing and extension

**Files to Create**:
```
spec_cli/cli/
├── __init__.py
├── commands.py          # Command definitions and implementations
├── runner.py            # Command execution coordination
└── validators.py        # CLI input validation
```

**Detailed Implementation**:

**spec_cli/cli/commands.py**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..core.spec_repository import SpecRepository
from ..core.file_processor import FileProcessor
from ..config.settings import get_settings
from ..exceptions import SpecError
from ..utils.decorators import handle_errors
from ..logging.debug import debug_logger

class Command(ABC):
    """Abstract base class for all CLI commands."""
    
    def __init__(self):
        self.settings = get_settings()
        self.spec_repo = SpecRepository(self.settings)
    
    @abstractmethod
    def execute(self, args: List[str]) -> None:
        """Execute the command with given arguments."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name."""
        pass
    
    @property
    def description(self) -> str:
        """Command description for help."""
        return f"Execute {self.name} command"

class InitCommand(Command):
    """Initialize spec repository."""
    
    @property
    def name(self) -> str:
        return "init"
    
    @property
    def description(self) -> str:
        return "Initialize spec documentation repository"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Initialize spec repository."""
        with debug_logger.timer("init_command"):
            self.spec_repo.initialize()
            print("✓ Spec repository initialized successfully")

class AddCommand(Command):
    """Add files to spec repository."""
    
    @property
    def name(self) -> str:
        return "add"
    
    @property
    def description(self) -> str:
        return "Add documentation files to spec repository"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Add files to spec repository."""
        if not args:
            raise SpecError("Please specify files to add")
        
        # Validate operation
        self.spec_repo.validate_operation("add")
        
        with debug_logger.timer("add_command"):
            self.spec_repo.add_files(args)
            print(f"✓ Staged documentation files: {', '.join(args)}")

class CommitCommand(Command):
    """Commit changes to spec repository."""
    
    @property
    def name(self) -> str:
        return "commit"
    
    @property
    def description(self) -> str:
        return "Commit documentation changes"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Commit changes to spec repository."""
        # Parse message from args
        if args and args[0] == "-m" and len(args) > 1:
            message = " ".join(args[1:])
        else:
            message = " ".join(args) if args else "spec update"
        
        # Validate operation
        self.spec_repo.validate_operation("commit")
        
        with debug_logger.timer("commit_command"):
            self.spec_repo.commit_changes(message)
            print(f"✓ Committed changes: {message}")

class StatusCommand(Command):
    """Show spec repository status."""
    
    @property
    def name(self) -> str:
        return "status"
    
    @property
    def description(self) -> str:
        return "Show documentation repository status"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Show repository status."""
        self.spec_repo.validate_operation("status")
        self.spec_repo.show_status()

class LogCommand(Command):
    """Show spec repository log."""
    
    @property
    def name(self) -> str:
        return "log"
    
    @property
    def description(self) -> str:
        return "Show documentation commit history"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Show commit log."""
        self.spec_repo.validate_operation("log")
        self.spec_repo.show_log(args if args else None)

class DiffCommand(Command):
    """Show spec repository diff."""
    
    @property
    def name(self) -> str:
        return "diff"
    
    @property
    def description(self) -> str:
        return "Show documentation changes"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Show differences."""
        self.spec_repo.validate_operation("diff")
        self.spec_repo.show_diff(args if args else None)

class GenCommand(Command):
    """Generate spec documentation."""
    
    @property
    def name(self) -> str:
        return "gen"
    
    @property
    def description(self) -> str:
        return "Generate documentation for files or directories"
    
    @handle_errors(SpecError)
    def execute(self, args: List[str]) -> None:
        """Generate documentation."""
        if not args:
            raise SpecError("Please specify a file or directory to generate specs for")
        
        # Validate operation
        self.spec_repo.validate_operation("gen")
        
        path_str = args[0]
        path = Path(path_str)
        
        # Use file processor for generation
        file_processor = FileProcessor(self.settings)
        
        with debug_logger.timer("gen_command"):
            if path.is_file():
                # Process single file
                success = file_processor.process_single_file(path_str)
                if success:
                    print(f"✓ Generated documentation for: {path}")
                else:
                    print(f"⏭ Skipped: {path}")
            
            elif path.is_dir():
                # Process directory
                print(f"📁 Generating documentation for directory: {path}")
                results = file_processor.process_directory(path)
                
                print(f"\n🎉 Directory processing complete!")
                print(f"   ✓ Processed: {results['processed_count']} files")
                print(f"   ⏭ Skipped: {results['skipped_count']} files")
                if results['error_count'] > 0:
                    print(f"   ❌ Errors: {results['error_count']} files")
            
            else:
                raise SpecError(f"Path is neither a file nor directory: {path}")

# Command registry
COMMANDS: Dict[str, Command] = {
    "init": InitCommand(),
    "add": AddCommand(),
    "commit": CommitCommand(),
    "status": StatusCommand(),
    "log": LogCommand(),
    "diff": DiffCommand(),
    "gen": GenCommand(),
}
```

**spec_cli/cli/runner.py**:
```python
import sys
from typing import List, Optional, Dict, Any
from .commands import COMMANDS, Command
from ..exceptions import SpecError
from ..logging.debug import debug_logger

class CommandRunner:
    """Executes CLI commands with proper error handling."""
    
    def __init__(self):
        self.commands = COMMANDS
    
    def run(self, argv: Optional[List[str]] = None) -> None:
        """Run command from command line arguments."""
        argv = argv or sys.argv[1:]
        
        try:
            if not argv:
                self._show_help()
                sys.exit(1)
            
            command_name = argv[0]
            command_args = argv[1:]
            
            # Handle help
            if command_name in ["-h", "--help", "help"]:
                self._show_help()
                return
            
            # Find and execute command
            if command_name not in self.commands:
                print(f"Error: Unknown command '{command_name}'")
                self._show_help()
                sys.exit(1)
            
            command = self.commands[command_name]
            
            debug_logger.log("INFO", "Executing command", 
                           command=command_name, args=command_args)
            
            command.execute(command_args)
            
        except SpecError as e:
            print(f"Error: {e.get_user_message()}")
            if debug_logger.enabled:
                debug_logger.log("ERROR", "Command failed", 
                               error=str(e), context=e.get_context())
            sys.exit(1)
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(130)  # Standard exit code for SIGINT
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            if debug_logger.enabled:
                import traceback
                debug_logger.log("ERROR", "Unexpected error", 
                               error=str(e), traceback=traceback.format_exc())
            else:
                print("Run with SPEC_DEBUG=1 for detailed error information")
            sys.exit(1)
    
    def _show_help(self) -> None:
        """Show help message with available commands."""
        print("Usage: spec <command> [options]")
        print("\nAvailable commands:")
        
        for name, command in self.commands.items():
            print(f"  {name:<10} {command.description}")
        
        print("\nFor help with a specific command: spec <command> --help")
        print("Set SPEC_DEBUG=1 for detailed debugging output")

def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point for CLI."""
    runner = CommandRunner()
    runner.run(argv)
```

**spec_cli/__main__.py** (Updated to be thin entry point):
```python
#!/usr/bin/env python3
"""
Spec CLI - Versioned documentation for AI-assisted development.

This is the main entry point that delegates to the CLI runner.
"""

from .cli.runner import main

if __name__ == "__main__":
    main()
```

**Tests to Write** (22 comprehensive tests):
- `tests/unit/cli/test_commands.py`:
  - `test_init_command_initializes_repository`
  - `test_add_command_validates_arguments`
  - `test_add_command_adds_files_to_repository`
  - `test_commit_command_parses_message_correctly`
  - `test_commit_command_creates_commit`
  - `test_status_command_shows_repository_status`
  - `test_log_command_shows_history`
  - `test_diff_command_shows_changes`
  - `test_gen_command_processes_single_file`
  - `test_gen_command_processes_directory`
  - `test_gen_command_validates_paths`

- `tests/unit/cli/test_runner.py`:
  - `test_command_runner_executes_valid_commands`
  - `test_command_runner_handles_unknown_commands`
  - `test_command_runner_shows_help_for_help_flag`
  - `test_command_runner_handles_spec_errors_gracefully`
  - `test_command_runner_handles_keyboard_interrupt`
  - `test_command_runner_handles_unexpected_errors`
  - `test_command_runner_provides_debug_information`

- `tests/unit/cli/test_integration.py`:
  - `test_cli_integrates_with_core_services`
  - `test_cli_maintains_backward_compatibility`
  - `test_cli_handles_edge_cases_gracefully`
  - `test_cli_provides_consistent_user_experience`
  - `test_cli_supports_extension_points`

**Quality Checks**: 80%+ coverage including CLI error scenarios

**Commit**: `feat: implement slice 7 - CLI layer refactoring with command pattern`

### Slice 8: Integration, Testing, and Finalization
**Goal**: Integrate all components, ensure backward compatibility, and comprehensive testing

**Implementation Details**:
- Update imports and exports for backward compatibility
- Integrate all modules with proper dependency injection
- Update existing tests to work with new architecture
- Add comprehensive integration tests
- Performance testing and optimization
- Documentation updates

**Files to Update/Create**:
```
spec_cli/__init__.py     # Update public API exports
tests/integration/       # Integration tests
tests/performance/       # Performance tests (temporary)
```

**Detailed Implementation**:

**spec_cli/__init__.py**:
```python
"""
Spec CLI - Versioned documentation for AI-assisted development.

This package provides tools for maintaining versioned documentation that helps
AI agents understand your codebase without polluting your main Git history.
"""

from .cli.runner import main
from .core.spec_repository import SpecRepository
from .templates.config import TemplateConfig
from .templates.loader import load_template
from .templates.generator import generate_spec_content
from .config.settings import get_settings, SpecSettings
from .exceptions import (
    SpecError,
    SpecNotInitializedError,
    SpecPermissionError,
    SpecGitError,
    SpecConfigurationError,
    SpecTemplateError,
    SpecFileError,
    SpecValidationError,
)

# Version information
__version__ = "0.1.0"
__author__ = "Spec CLI Team"

# Backward compatibility exports
# These ensure existing imports continue to work
__all__ = [
    # Main entry points
    "main",
    "SpecRepository",
    
    # Template system (for external use)
    "TemplateConfig",
    "load_template", 
    "generate_spec_content",
    
    # Configuration
    "get_settings",
    "SpecSettings",
    
    # Exceptions
    "SpecError",
    "SpecNotInitializedError", 
    "SpecPermissionError",
    "SpecGitError",
    "SpecConfigurationError",
    "SpecTemplateError",
    "SpecFileError",
    "SpecValidationError",
    
    # Version info
    "__version__",
    "__author__",
]
```

**Integration Test Structure**:
```python
# tests/integration/test_full_workflow.py
def test_complete_spec_workflow():
    """Test complete workflow from init to commit."""
    # Initialize repository
    # Generate documentation 
    # Add and commit changes
    # Verify results
    pass

def test_template_system_integration():
    """Test template system works with all components."""
    pass

def test_git_operations_integration():
    """Test Git operations work correctly with file system."""
    pass

def test_error_handling_integration():
    """Test error handling works across all layers."""
    pass
```

**Migration Strategy**:
1. **Phase 1**: Deploy new architecture alongside old code
2. **Phase 2**: Update imports gradually with deprecation warnings
3. **Phase 3**: Remove old code after verification
4. **Phase 4**: Optimize and clean up

**Backward Compatibility Checklist**:
- [ ] All existing CLI commands work identically
- [ ] All existing template functionality preserved
- [ ] All existing debug logging works
- [ ] All existing configuration files supported
- [ ] All existing Git operations work correctly
- [ ] Performance is maintained or improved

**Tests to Write** (30 comprehensive tests):
- `tests/integration/test_full_workflow.py`:
  - `test_complete_init_to_commit_workflow`
  - `test_directory_processing_workflow`
  - `test_template_customization_workflow`
  - `test_conflict_resolution_workflow`
  - `test_debug_logging_integration`

- `tests/integration/test_backward_compatibility.py`:
  - `test_all_cli_commands_maintain_compatibility`
  - `test_template_loading_maintains_compatibility`
  - `test_git_operations_maintain_compatibility`
  - `test_configuration_loading_maintains_compatibility`
  - `test_debug_features_maintain_compatibility`

- `tests/integration/test_error_scenarios.py`:
  - `test_uninitialized_repository_errors`
  - `test_permission_denied_errors`
  - `test_invalid_configuration_errors`
  - `test_git_operation_errors`
  - `test_template_processing_errors`

- `tests/integration/test_cross_component.py`:
  - `test_services_interact_correctly`
  - `test_dependency_injection_works`
  - `test_error_propagation_across_layers`
  - `test_logging_works_across_components`

- `tests/performance/test_performance.py`:
  - `test_startup_time_performance`
  - `test_large_directory_processing_performance`
  - `test_memory_usage_reasonable`
  - `test_git_operations_performance`

- `tests/unit/test_public_api.py`:
  - `test_public_api_exports_correct_functions`
  - `test_backward_compatibility_imports_work`
  - `test_version_information_available`

**Quality Assurance**:
```bash
# Run all tests with coverage
poetry run pytest tests/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/

# Run linting
poetry run ruff check --fix .
poetry run ruff format .

# Run pre-commit hooks
poetry run pre-commit run --all-files

# Performance benchmark
python -m pytest tests/performance/ -v

# Integration test with real workflow
cd test_area && spec init && spec gen . && spec add . && spec commit -m "test"
```

**Quality Checks**: 80%+ overall coverage, all integration tests passing

**Commit**: `feat: implement slice 8 - integration, testing, and finalization`

## Dependencies to Add

### Core Dependencies (New)
```toml
[tool.poetry.dependencies]
# Enhanced typing support
typing-extensions = "^4.8.0"

# Better error handling
rich-traceback = "^1.0.0"  # Optional for better error display
```

### Development Dependencies (New)
```toml
[tool.poetry.group.dev.dependencies]
# Performance testing
pytest-benchmark = "^4.0.0"

# Memory profiling  
memory-profiler = "^0.61.0"

# Integration testing
pytest-integration = "^0.2.3"
```

## Quality Standards Summary

### Test Coverage Requirements
- **Total Tests Planned**: 157 comprehensive tests across all slices
- **Overall Coverage**: Minimum 80% per slice, 85% overall
- **Integration Coverage**: End-to-end workflows tested
- **Performance Coverage**: Memory and timing benchmarks
- **Compatibility Coverage**: All existing functionality preserved

### Performance Requirements
- [ ] Startup time under 200ms (vs current ~150ms)
- [ ] Memory usage under 50MB for typical operations
- [ ] Directory processing scales linearly with file count
- [ ] Git operations maintain current performance
- [ ] Module import time minimized through lazy loading

### Architecture Quality Requirements
- [ ] All modules follow single responsibility principle
- [ ] Clean interfaces between all layers
- [ ] Dependency injection used throughout
- [ ] Error handling consistent across all modules
- [ ] Logging integrated throughout all operations
- [ ] Configuration centralized and validated
- [ ] Extensibility points for AI and Git hooks
- [ ] Type hints throughout with mypy compliance

### Success Criteria
- [ ] All 8 slices implemented with 80%+ test coverage
- [ ] Complete backward compatibility maintained
- [ ] Performance meets or exceeds current implementation
- [ ] Clean architecture enables easy AI and Git hook integration
- [ ] Code maintainability significantly improved
- [ ] Extensibility points clearly defined and documented
- [ ] Error handling provides clear user guidance
- [ ] Logging supports effective debugging