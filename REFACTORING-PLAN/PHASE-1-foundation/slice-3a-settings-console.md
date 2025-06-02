# Slice 3A: Settings and Console Management

## Goal

Create a centralized settings system with environment variable support and integrated Rich terminal console for emoji replacement throughout the application.

## Context

The current monolithic code has configuration scattered throughout and uses emojis for user feedback. This slice creates the core settings management and Rich console system for emoji replacement. It focuses on the essential configuration infrastructure and terminal console, leaving file loading for slice-3b.

## Scope

**Included in this slice:**
- SpecSettings dataclass for centralized configuration
- Environment variable support for all settings
- Rich terminal console setup and emoji replacement
- Basic settings validation and error handling

**NOT included in this slice:**
- Configuration file loading (moved to slice-3b)
- Complex configuration validation (moved to slice-3b)
- User interface components (comes in PHASE-5)
- Interactive configuration setup

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for configuration errors)
- `spec_cli.logging.debug` (debug_logger for configuration operations)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging

## Files to Create

```
spec_cli/config/
├── __init__.py             # Module exports
└── settings.py             # SpecSettings class and manager with Rich console
```

**Dependencies to add:**
- `rich` library for terminal styling

## Implementation Steps

### Step 1: Add Rich dependency to pyproject.toml

```toml
[tool.poetry.dependencies]
rich = "^13.0.0"
```

### Step 2: Create spec_cli/config/__init__.py

```python
"""Configuration management for spec CLI.

This package provides centralized settings management with environment variable
support and Rich terminal console integration for emoji replacement.
"""

from .settings import (
    SpecSettings,
    SettingsManager,
    get_settings,
    get_console,
)

__all__ = [
    "SpecSettings",
    "SettingsManager", 
    "get_settings",
    "get_console",
]
```

### Step 3: Create spec_cli/config/settings.py

```python
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from rich.console import Console
from rich.theme import Theme
from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger

# Rich theme for consistent styling throughout the application
SPEC_THEME = Theme({
    "success": "bold green",
    "error": "bold red", 
    "warning": "bold yellow",
    "info": "bold blue",
    "debug": "dim white",
    "path": "bold cyan",
    "count": "bold white",
})

@dataclass
class SpecSettings:
    """Global settings for spec operations with Rich terminal styling."""
    
    # Directory paths
    root_path: Path = field(default_factory=Path.cwd)
    
    # Computed paths (set in __post_init__)
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
    
    # Terminal styling settings
    use_color: bool = field(init=False)
    console_width: Optional[int] = field(default=None)
    
    def __post_init__(self):
        """Initialize computed paths and environment settings."""
        # Computed directory paths
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
        
        # Terminal settings
        self.use_color = self._get_bool_env("SPEC_USE_COLOR", True)
        width_str = os.environ.get("SPEC_CONSOLE_WIDTH")
        if width_str:
            try:
                self.console_width = int(width_str)
                if self.console_width < 40:
                    self.console_width = 40
            except ValueError:
                debug_logger.log("WARNING", "Invalid SPEC_CONSOLE_WIDTH value", 
                               value=width_str)
        
        debug_logger.log("INFO", "Settings initialized", 
                        root_path=str(self.root_path),
                        debug_enabled=self.debug_enabled,
                        use_color=self.use_color)
    
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
                raise SpecConfigurationError(
                    f"No write permission for {self.spec_dir}",
                    {"directory": str(self.spec_dir), "permission": "write"}
                )
            if not os.access(self.specs_dir, os.W_OK):
                raise SpecConfigurationError(
                    f"No write permission for {self.specs_dir}",
                    {"directory": str(self.specs_dir), "permission": "write"}
                )

class SettingsManager:
    """Manages global settings and console instances."""
    
    _settings_instance: Optional[SpecSettings] = None
    _console_instance: Optional[Console] = None
    
    @classmethod
    def get_settings(cls, root_path: Optional[Path] = None) -> SpecSettings:
        """Get global settings instance."""
        if cls._settings_instance is None or (
            root_path and root_path != cls._settings_instance.root_path
        ):
            cls._settings_instance = SpecSettings(root_path or Path.cwd())
            # Reset console when settings change
            cls._console_instance = None
        return cls._settings_instance
    
    @classmethod
    def get_console(cls, root_path: Optional[Path] = None) -> Console:
        """Get Rich console instance with spec theming."""
        settings = cls.get_settings(root_path)
        
        if cls._console_instance is None:
            cls._console_instance = Console(
                theme=SPEC_THEME,
                force_terminal=settings.use_color,
                width=settings.console_width,
            )
            debug_logger.log("INFO", "Console initialized", 
                           use_color=settings.use_color,
                           width=settings.console_width)
        
        return cls._console_instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset settings and console for testing."""
        cls._settings_instance = None
        cls._console_instance = None

# Convenience functions for getting settings and console
def get_settings(root_path: Optional[Path] = None) -> SpecSettings:
    """Get global settings instance."""
    return SettingsManager.get_settings(root_path)

def get_console(root_path: Optional[Path] = None) -> Console:
    """Get Rich console instance."""
    return SettingsManager.get_console(root_path)
```

## Test Requirements

Create focused tests for the settings and console system:

### Test Cases (12 tests total)

**Settings Tests:**
1. **test_spec_settings_initializes_with_correct_paths**
2. **test_spec_settings_detects_debug_environment_variables**
3. **test_spec_settings_detects_terminal_environment_variables**
4. **test_spec_settings_validates_initialization_state**
5. **test_spec_settings_validates_permissions**
6. **test_spec_settings_handles_invalid_console_width**

**Settings Manager Tests:**
7. **test_settings_manager_provides_singleton_behavior**
8. **test_settings_manager_handles_root_path_changes**
9. **test_settings_manager_resets_console_when_settings_change**

**Console Integration Tests:**
10. **test_console_uses_spec_theme_consistently**
11. **test_console_respects_color_settings**
12. **test_console_handles_width_configuration**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Install Rich dependency  
poetry add rich

# Run the specific tests for this slice
poetry run pytest tests/unit/config/test_settings.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/config/test_settings.py --cov=spec_cli.config.settings --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/config/settings.py

# Check code formatting
poetry run ruff check spec_cli/config/settings.py
poetry run ruff format spec_cli/config/settings.py

# Verify imports work correctly
python -c "from spec_cli.config import get_settings, get_console; print('Import successful')"

# Test environment variable detection
SPEC_DEBUG=1 SPEC_USE_COLOR=0 python -c "
from spec_cli.config import get_settings, get_console
settings = get_settings()
console = get_console()
print(f'Debug: {settings.debug_enabled}')
print(f'Color: {settings.use_color}')
console.print('Test message', style='success')
"
```

## Definition of Done

- [ ] SpecSettings dataclass implemented with all computed paths
- [ ] Environment variable support for debug and terminal settings
- [ ] Rich console integration with spec theme
- [ ] Settings manager with singleton pattern
- [ ] Permission validation for spec directories
- [ ] All 12 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Console replaces emoji usage in settings module
- [ ] Debug logging integrated for configuration operations
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-3b (configuration loading) by providing:
- Basic SpecSettings structure that can be extended
- Rich console system for user feedback during file loading
- Environment variable patterns that file loading can build upon
- Settings manager infrastructure that can integrate file-based configuration