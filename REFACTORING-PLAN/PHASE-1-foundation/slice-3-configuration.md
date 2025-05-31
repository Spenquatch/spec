# Slice 3: Configuration Management with Terminal Styling

## Goal

Create a centralized configuration management system with environment variable support, file loading, and integrated Rich terminal styling to replace emoji usage throughout the application.

## Context

The current monolithic code has configuration scattered throughout and uses emojis for user feedback. This slice creates a unified configuration system while integrating Rich terminal styling (addressing the terminal styling maintenance item). It builds on the exception and logging systems to provide proper error handling and debugging during configuration operations.

## Scope

**Included in this slice:**
- SpecSettings dataclass for centralized configuration
- Configuration file loading with precedence (environment > file > defaults)
- Environment variable support for all settings
- Rich terminal styling integration and emoji replacement
- Settings validation and error handling

**NOT included in this slice:**
- User interface components (comes in PHASE-5)
- Interactive configuration setup
- Configuration persistence/writing

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
├── settings.py             # SpecSettings class and manager
├── loader.py               # Configuration file loading
└── validation.py           # Configuration validation
```

**Dependencies to add:**
- `rich` library for terminal styling

## Implementation Steps

### Step 1: Add Rich dependency to pyproject.toml

```toml
[tool.poetry.dependencies]
rich = "^13.7.0"
```

### Step 2: Create spec_cli/config/__init__.py

```python
"""Configuration management for spec CLI.

This package provides centralized configuration with file loading,
environment variable support, and settings validation.
"""

from .settings import SpecSettings, SettingsManager, get_settings
from .loader import ConfigurationLoader
from .validation import ConfigurationValidator

__all__ = [
    "SpecSettings",
    "SettingsManager", 
    "get_settings",
    "ConfigurationLoader",
    "ConfigurationValidator",
]
```

### Step 3: Create spec_cli/config/settings.py

```python
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console
from rich.theme import Theme
from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger

# Rich theme for consistent terminal styling
SPEC_THEME = Theme({
    "success": "bold green",
    "warning": "bold yellow", 
    "error": "bold red",
    "info": "bold blue",
    "highlight": "bold cyan",
    "muted": "dim white",
    "path": "bold magenta",
    "file": "green",
    "directory": "blue",
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
    force_terminal: bool = field(init=False)
    
    # Rich console instance
    console: Console = field(init=False)
    
    def __post_init__(self):
        """Initialize computed paths and environment settings."""
        debug_logger.log("INFO", "Initializing SpecSettings", root_path=str(self.root_path))
        
        # Computed directory paths
        self.spec_dir = self.root_path / ".spec"
        self.specs_dir = self.root_path / ".specs"
        self.index_file = self.root_path / ".spec-index"
        self.ignore_file = self.root_path / ".specignore"
        self.template_file = self.root_path / ".spectemplate"
        self.gitignore_file = self.root_path / ".gitignore"
        
        # Environment-based debug settings
        self.debug_enabled = self._get_bool_env("SPEC_DEBUG", False)
        self.debug_level = os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
        self.debug_timing = self._get_bool_env("SPEC_DEBUG_TIMING", False)
        
        # Terminal styling settings
        self.use_color = not self._get_bool_env("NO_COLOR", False)
        self.force_terminal = self._get_bool_env("FORCE_TERMINAL", False)
        
        # Initialize Rich console with theme
        self.console = Console(
            theme=SPEC_THEME,
            force_terminal=self.force_terminal,
            width=self.console_width,
            color_system="auto" if self.use_color else None
        )
        
        debug_logger.log("INFO", "SpecSettings initialized", 
                        debug_enabled=self.debug_enabled,
                        use_color=self.use_color,
                        spec_dir=str(self.spec_dir))
    
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
        initialized = (
            self.spec_dir.exists() and 
            self.spec_dir.is_dir() and
            self.specs_dir.exists() and
            self.specs_dir.is_dir()
        )
        
        debug_logger.log("INFO", "Checking initialization status", 
                        initialized=initialized,
                        spec_dir_exists=self.spec_dir.exists(),
                        specs_dir_exists=self.specs_dir.exists())
        
        return initialized
    
    def validate_permissions(self) -> None:
        """Validate required permissions for spec operations."""
        debug_logger.log("INFO", "Validating permissions")
        
        if self.is_initialized():
            if not os.access(self.spec_dir, os.W_OK):
                raise SpecConfigurationError(f"No write permission for {self.spec_dir}")
            if not os.access(self.specs_dir, os.W_OK):
                raise SpecConfigurationError(f"No write permission for {self.specs_dir}")
        
        debug_logger.log("INFO", "Permission validation passed")
    
    def print_styled(self, message: str, style: str = "info") -> None:
        """Print message with Rich styling and emoji replacement."""
        # Emoji replacement mapping
        emoji_replacements = {
            "✅": "[success]✓[/success]",
            "❌": "[error]✗[/error]",
            "⚠️": "[warning]![/warning]",
            "📝": "[info]→[/info]",
            "📁": "[directory]DIR[/directory]",
            "📄": "[file]FILE[/file]",
            "🔍": "[muted]DEBUG[/muted]",
            "🚀": "[success]START[/success]",
            "💾": "[info]SAVE[/info]",
            "🔄": "[warning]UPDATE[/warning]",
            "⏭️": "[muted]SKIP[/muted]",
            "🎉": "[success]COMPLETE[/success]",
            "ℹ️": "[info]INFO[/info]",
        }
        
        # Replace emojis with styled equivalents
        styled_message = message
        for emoji, replacement in emoji_replacements.items():
            styled_message = styled_message.replace(emoji, replacement)
        
        # Apply style wrapper
        if style in ["success", "error", "warning", "info", "highlight", "muted", "path"]:
            styled_message = f"[{style}]{styled_message}[/{style}]"
        
        self.console.print(styled_message)
    
    def print_success(self, message: str) -> None:
        """Print success message with styling."""
        self.print_styled(f"✓ {message}", "success")
    
    def print_error(self, message: str) -> None:
        """Print error message with styling."""
        self.print_styled(f"✗ {message}", "error")
    
    def print_warning(self, message: str) -> None:
        """Print warning message with styling."""
        self.print_styled(f"! {message}", "warning")
    
    def print_info(self, message: str) -> None:
        """Print info message with styling."""
        self.print_styled(f"→ {message}", "info")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "root_path": str(self.root_path),
            "debug_enabled": self.debug_enabled,
            "debug_level": self.debug_level,
            "debug_timing": self.debug_timing,
            "use_color": self.use_color,
            "force_terminal": self.force_terminal,
        }

class SettingsManager:
    """Manages global settings instance with singleton pattern."""
    
    _instance: Optional[SpecSettings] = None
    _console_cache: Dict[str, Console] = {}
    
    @classmethod
    def get_settings(cls, root_path: Optional[Path] = None) -> SpecSettings:
        """Get global settings instance.
        
        Args:
            root_path: Optional root path override
            
        Returns:
            Global SpecSettings instance
        """
        if cls._instance is None or (root_path and root_path != cls._instance.root_path):
            debug_logger.log("INFO", "Creating new SpecSettings instance", 
                           root_path=str(root_path) if root_path else "default")
            cls._instance = SpecSettings(root_path or Path.cwd())
        
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset settings for testing."""
        debug_logger.log("INFO", "Resetting SettingsManager")
        cls._instance = None
        cls._console_cache.clear()
    
    @classmethod
    def get_console(cls, root_path: Optional[Path] = None) -> Console:
        """Get Rich console instance from settings.
        
        Args:
            root_path: Optional root path for settings
            
        Returns:
            Rich Console instance with spec theme
        """
        cache_key = str(root_path) if root_path else "default"
        
        if cache_key not in cls._console_cache:
            settings = cls.get_settings(root_path)
            cls._console_cache[cache_key] = settings.console
        
        return cls._console_cache[cache_key]

# Convenience functions for easy access
def get_settings(root_path: Optional[Path] = None) -> SpecSettings:
    """Get global settings instance."""
    return SettingsManager.get_settings(root_path)

def get_console(root_path: Optional[Path] = None) -> Console:
    """Get Rich console instance."""
    return SettingsManager.get_console(root_path)
```

### Step 4: Create spec_cli/config/loader.py

```python
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger

class ConfigurationLoader:
    """Loads configuration from various sources with precedence handling."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.config_sources = [
            root_path / ".specconfig.yaml",
            root_path / ".specconfig.yml",
            root_path / "pyproject.toml",
        ]
        debug_logger.log("INFO", "ConfigurationLoader initialized", 
                        root_path=str(root_path),
                        config_sources=[str(s) for s in self.config_sources])
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from available sources.
        
        Returns:
            Merged configuration dictionary
            
        Raises:
            SpecConfigurationError: If configuration loading fails
        """
        debug_logger.log("INFO", "Loading configuration from sources")
        config = {}
        
        # Load from each source in order (later sources override earlier ones)
        for source in self.config_sources:
            if source.exists():
                try:
                    debug_logger.log("INFO", f"Loading config from {source}")
                    source_config = self._load_from_file(source)
                    config.update(source_config)
                    debug_logger.log("INFO", f"Successfully loaded config from {source}",
                                   keys_loaded=list(source_config.keys()))
                except Exception as e:
                    error_msg = f"Failed to load configuration from {source}: {e}"
                    debug_logger.log("ERROR", error_msg)
                    raise SpecConfigurationError(error_msg) from e
            else:
                debug_logger.log("INFO", f"Config file not found: {source}")
        
        # Environment variables override file configuration
        env_config = self._load_from_environment()
        if env_config:
            config.update(env_config)
            debug_logger.log("INFO", "Applied environment variable overrides",
                           env_keys=list(env_config.keys()))
        
        debug_logger.log("INFO", "Configuration loading complete", 
                        final_keys=list(config.keys()))
        return config
    
    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a specific file."""
        if file_path.name == "pyproject.toml":
            return self._load_from_pyproject_toml(file_path)
        elif file_path.suffix in [".yaml", ".yml"]:
            return self._load_from_yaml(file_path)
        else:
            debug_logger.log("WARNING", f"Unknown config file type: {file_path}")
            return {}
    
    def _load_from_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data or {}
        except yaml.YAMLError as e:
            raise SpecConfigurationError(f"Invalid YAML in {file_path}: {e}") from e
    
    def _load_from_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from pyproject.toml [tool.spec] section."""
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli
            except ImportError:
                debug_logger.log("WARNING", "No TOML library available, skipping pyproject.toml")
                return {}
        
        try:
            with file_path.open("rb") as f:
                data = tomli.load(f)
            return data.get("tool", {}).get("spec", {})
        except Exception as e:
            raise SpecConfigurationError(f"Error reading pyproject.toml: {e}") from e
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Map environment variables to config keys
        env_mappings = {
            "SPEC_DEBUG": ("debug_enabled", lambda x: x.lower() in ["1", "true", "yes"]),
            "SPEC_DEBUG_LEVEL": ("debug_level", lambda x: x.upper()),
            "SPEC_DEBUG_TIMING": ("debug_timing", lambda x: x.lower() in ["1", "true", "yes"]),
            "NO_COLOR": ("use_color", lambda x: not x.lower() in ["1", "true", "yes"]),
            "FORCE_TERMINAL": ("force_terminal", lambda x: x.lower() in ["1", "true", "yes"]),
        }
        
        import os
        for env_var, (config_key, transform) in env_mappings.items():
            if env_var in os.environ:
                try:
                    value = transform(os.environ[env_var])
                    env_config[config_key] = value
                    debug_logger.log("INFO", f"Environment override: {config_key} = {value}")
                except Exception as e:
                    debug_logger.log("WARNING", f"Failed to parse {env_var}: {e}")
        
        return env_config
    
    def get_available_sources(self) -> List[Path]:
        """Get list of available configuration sources."""
        return [source for source in self.config_sources if source.exists()]
```

### Step 5: Create spec_cli/config/validation.py

```python
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger

class ConfigurationValidator:
    """Validates configuration values and provides helpful error messages."""
    
    def __init__(self):
        self.required_fields = set()
        self.field_validators = {
            "debug_level": self._validate_debug_level,
            "root_path": self._validate_path,
            "console_width": self._validate_console_width,
        }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of issues.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of validation error messages
        """
        debug_logger.log("INFO", "Validating configuration", config_keys=list(config.keys()))
        issues = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in config:
                issues.append(f"Required field '{field}' is missing")
        
        # Validate individual fields
        for field, value in config.items():
            if field in self.field_validators:
                try:
                    self.field_validators[field](value)
                    debug_logger.log("DEBUG", f"Validation passed for {field}")
                except ValueError as e:
                    issues.append(f"Invalid value for '{field}': {e}")
                    debug_logger.log("WARNING", f"Validation failed for {field}: {e}")
        
        debug_logger.log("INFO", "Configuration validation complete", 
                        issue_count=len(issues))
        return issues
    
    def _validate_debug_level(self, value: Any) -> None:
        """Validate debug level setting."""
        if not isinstance(value, str):
            raise ValueError("Debug level must be a string")
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if value.upper() not in valid_levels:
            raise ValueError(f"Debug level must be one of: {', '.join(valid_levels)}")
    
    def _validate_path(self, value: Any) -> None:
        """Validate path setting."""
        if isinstance(value, str):
            try:
                Path(value)
            except Exception as e:
                raise ValueError(f"Invalid path format: {e}") from e
        elif not isinstance(value, Path):
            raise ValueError("Path must be a string or Path object")
    
    def _validate_console_width(self, value: Any) -> None:
        """Validate console width setting."""
        if value is not None:
            if not isinstance(value, int):
                raise ValueError("Console width must be an integer")
            if value < 20 or value > 500:
                raise ValueError("Console width must be between 20 and 500")
    
    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """Validate configuration and raise exception if invalid.
        
        Args:
            config: Configuration to validate
            
        Raises:
            SpecConfigurationError: If configuration is invalid
        """
        issues = self.validate_configuration(config)
        if issues:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {issue}" for issue in issues)
            raise SpecConfigurationError(error_msg)
```

## Test Requirements

Create comprehensive tests for the configuration system:

### Test Cases (25 tests total)

**Settings Tests:**
1. **test_spec_settings_initializes_with_correct_paths**
2. **test_spec_settings_detects_debug_environment_variables**
3. **test_spec_settings_initializes_rich_console_with_theme**
4. **test_spec_settings_replaces_emojis_in_print_methods**
5. **test_spec_settings_validates_initialization_state**
6. **test_spec_settings_validates_permissions**
7. **test_spec_settings_handles_no_color_environment**
8. **test_settings_manager_provides_singleton_behavior**

**Loader Tests:**
9. **test_configuration_loader_loads_from_yaml**
10. **test_configuration_loader_loads_from_pyproject_toml**
11. **test_configuration_loader_handles_missing_files**
12. **test_configuration_loader_respects_precedence_order**
13. **test_configuration_loader_handles_malformed_files**
14. **test_configuration_loader_loads_environment_variables**
15. **test_configuration_loader_handles_toml_import_error**

**Validation Tests:**
16. **test_configuration_validator_accepts_valid_config**
17. **test_configuration_validator_rejects_invalid_debug_level**
18. **test_configuration_validator_validates_path_fields**
19. **test_configuration_validator_validates_console_width**
20. **test_configuration_validator_provides_helpful_errors**

**Integration Tests:**
21. **test_rich_console_integration_with_theme**
22. **test_emoji_replacement_system_comprehensive**
23. **test_environment_variable_precedence**
24. **test_settings_to_dict_serialization**
25. **test_console_caching_and_reuse**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Install Rich dependency
poetry add rich

# Run the specific tests for this slice
poetry run pytest tests/unit/config/ -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/config/ --cov=spec_cli.config --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/config/

# Check code formatting
poetry run ruff check spec_cli/config/
poetry run ruff format spec_cli/config/

# Verify imports work correctly
python -c "from spec_cli.config import get_settings, get_console; print('Import successful')"

# Test Rich console functionality
python -c "
from spec_cli.config import get_settings
settings = get_settings()
settings.print_success('✅ This should show styled success message')
settings.print_error('❌ This should show styled error message')
settings.print_info('📝 This should show styled info message')
"

# Test environment variable handling
SPEC_DEBUG=1 NO_COLOR=0 python -c "
from spec_cli.config import get_settings
settings = get_settings()
print(f'Debug enabled: {settings.debug_enabled}')
print(f'Use color: {settings.use_color}')
"

# Verify no emojis remain in output
python -c "
from spec_cli.config import get_settings
settings = get_settings()
import io
import contextlib
output = io.StringIO()
with contextlib.redirect_stdout(output):
    settings.print_styled('✅🔍📁 Test emoji replacement')
result = output.getvalue()
print(f'Styled output: {repr(result)}')
"
```

## Definition of Done

- [ ] `spec_cli/config/` package created with all required modules
- [ ] SpecSettings dataclass with Rich console integration
- [ ] Configuration loading with file and environment precedence
- [ ] Comprehensive emoji replacement system implemented
- [ ] Settings validation with helpful error messages
- [ ] Singleton pattern for global settings management
- [ ] Rich dependency added to pyproject.toml
- [ ] All 25 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with exception and logging systems verified
- [ ] Terminal styling replaces emoji usage throughout

## Next Slice Preparation

This slice enables **PHASE-2** by providing:
- `SpecSettings` with path management and validation
- `get_settings()` function for accessing global configuration
- Rich console system for styled output
- Debug logging integration for all file system operations

The next phase (filesystem) will use these settings for path resolution and the Rich console for user feedback.