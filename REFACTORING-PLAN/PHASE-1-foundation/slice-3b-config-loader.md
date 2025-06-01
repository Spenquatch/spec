# Slice 3B: Configuration File Loading and Validation

## Goal

Create configuration file loading system with precedence handling and comprehensive validation for YAML/TOML configuration sources.

## Context

This slice builds on slice-3a (Settings and Console) to add file-based configuration loading from `.specconfig.yaml` and `pyproject.toml` sources. It focuses specifically on the file parsing, precedence handling, and validation logic without mixing Rich theming or environment variable concerns.

## Scope

**Included in this slice:**
- Configuration file loading with precedence (file → environment → defaults)
- YAML and TOML file parsing
- Configuration validation with helpful error messages
- Integration with existing SpecSettings from slice-3a

**NOT included in this slice:**
- Settings dataclass or environment variables (handled in slice-3a)
- Rich terminal styling (handled in slice-3a)
- User interface components (comes in PHASE-5)
- Interactive configuration setup

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for configuration errors)
- `spec_cli.logging.debug` (debug_logger for configuration operations)
- `spec_cli.config.settings` (SpecSettings and SettingsManager from slice-3a)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings`, `SettingsManager` from slice-3a-settings-console

## Files to Create

```
spec_cli/config/
├── loader.py               # Configuration file loading
└── validation.py           # Configuration validation
```

**Dependencies to add:**
- `pyyaml` for YAML parsing (may already exist)
- `tomli` or `tomllib` for TOML parsing

## Implementation Steps

### Step 1: Update pyproject.toml dependencies

```toml
[tool.poetry.dependencies]
PyYAML = "^6.0.0"
tomli = "^2.0.0"  # For Python < 3.11, fallback to tomllib for 3.11+
```

### Step 2: Update spec_cli/config/__init__.py

```python
"""Configuration management for spec CLI.

This package provides centralized settings management with environment variable
support, file loading, and Rich terminal console integration.
"""

from .settings import (
    SpecSettings,
    SettingsManager,
    get_settings,
    get_console,
)
from .loader import ConfigurationLoader
from .validation import ConfigurationValidator

__all__ = [
    "SpecSettings",
    "SettingsManager", 
    "get_settings",
    "get_console",
    "ConfigurationLoader",
    "ConfigurationValidator",
]
```

### Step 3: Create spec_cli/config/loader.py

```python
import yaml
import os
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
            root_path / "pyproject.toml",
        ]
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from available sources with precedence.
        
        Precedence order (later overrides earlier):
        1. .specconfig.yaml
        2. pyproject.toml [tool.spec] section
        3. Environment variables (handled in SpecSettings)
        """
        config = {}
        
        debug_logger.log("INFO", "Loading configuration", 
                        sources=len(self.config_sources),
                        root_path=str(self.root_path))
        
        # Load from each source in order (later sources override earlier ones)
        for source in self.config_sources:
            if source.exists():
                try:
                    source_config = self._load_from_file(source)
                    if source_config:
                        config.update(source_config)
                        debug_logger.log("INFO", "Loaded config from file", 
                                       source=str(source), 
                                       keys=list(source_config.keys()))
                except Exception as e:
                    raise SpecConfigurationError(
                        f"Failed to load configuration from {source}: {e}",
                        {"source_file": str(source), "error_type": type(e).__name__}
                    ) from e
        
        if not config:
            debug_logger.log("INFO", "No configuration files found, using defaults")
        
        return config
    
    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a specific file."""
        if file_path.name == "pyproject.toml":
            return self._load_from_pyproject_toml(file_path)
        elif file_path.suffix in [".yaml", ".yml"]:
            return self._load_from_yaml(file_path)
        else:
            debug_logger.log("WARNING", "Unknown config file type", 
                           file_path=str(file_path))
            return {}
    
    def _load_from_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data or {}
        except yaml.YAMLError as e:
            raise SpecConfigurationError(
                f"Invalid YAML syntax in {file_path}: {e}",
                {"file_path": str(file_path), "yaml_error": str(e)}
            ) from e
        except UnicodeDecodeError as e:
            raise SpecConfigurationError(
                f"Unable to read {file_path} - file encoding issue: {e}",
                {"file_path": str(file_path), "encoding_error": str(e)}
            ) from e
    
    def _load_from_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from pyproject.toml [tool.spec] section."""
        try:
            # Try Python 3.11+ tomllib first
            try:
                import tomllib as tomli
                mode = "rb"
            except ImportError:
                # Fallback to tomli for older Python versions
                import tomli
                mode = "rb"
        except ImportError:
            debug_logger.log("WARNING", "No TOML parser available, skipping pyproject.toml")
            return {}
        
        try:
            with file_path.open(mode) as f:
                data = tomli.load(f)
            
            # Extract [tool.spec] section
            return data.get("tool", {}).get("spec", {})
            
        except tomli.TOMLDecodeError as e:
            raise SpecConfigurationError(
                f"Invalid TOML syntax in {file_path}: {e}",
                {"file_path": str(file_path), "toml_error": str(e)}
            ) from e
        except UnicodeDecodeError as e:
            raise SpecConfigurationError(
                f"Unable to read {file_path} - file encoding issue: {e}",
                {"file_path": str(file_path), "encoding_error": str(e)}
            ) from e
    
    def get_available_sources(self) -> List[Path]:
        """Get list of available configuration sources."""
        return [source for source in self.config_sources if source.exists()]
    
    def validate_source_syntax(self, source_path: Path) -> bool:
        """Validate syntax of configuration source without loading."""
        try:
            self._load_from_file(source_path)
            return True
        except SpecConfigurationError:
            return False
```

### Step 4: Create spec_cli/config/validation.py

```python
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from ..exceptions import SpecConfigurationError, SpecValidationError

class ConfigurationValidator:
    """Validates configuration values and provides helpful error messages."""
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Validate debug settings
        debug_config = config.get("debug", {})
        if debug_config:
            errors.extend(self._validate_debug_config(debug_config))
        
        # Validate terminal settings
        terminal_config = config.get("terminal", {})
        if terminal_config:
            errors.extend(self._validate_terminal_config(terminal_config))
        
        # Validate path settings
        path_config = config.get("paths", {})
        if path_config:
            errors.extend(self._validate_path_config(path_config))
        
        # Validate template settings
        template_config = config.get("template", {})
        if template_config:
            errors.extend(self._validate_template_config(template_config))
        
        return errors
    
    def _validate_debug_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate debug configuration section."""
        errors = []
        
        # Check debug level
        level = config.get("level")
        if level is not None:
            if not isinstance(level, str):
                errors.append(f"debug.level must be a string, got {type(level).__name__}")
            elif level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                errors.append(f"Invalid debug level '{level}'. Must be one of: DEBUG, INFO, WARNING, ERROR")
        
        # Check boolean values
        for key in ["enabled", "timing"]:
            value = config.get(key)
            if value is not None and not isinstance(value, bool):
                errors.append(f"debug.{key} must be a boolean value, got {type(value).__name__}")
        
        return errors
    
    def _validate_terminal_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate terminal configuration section."""
        errors = []
        
        # Check use_color
        use_color = config.get("use_color")
        if use_color is not None and not isinstance(use_color, bool):
            errors.append(f"terminal.use_color must be a boolean value, got {type(use_color).__name__}")
        
        # Check console width
        width = config.get("console_width")
        if width is not None:
            if not isinstance(width, int):
                errors.append(f"terminal.console_width must be an integer, got {type(width).__name__}")
            elif width < 40:
                errors.append(f"terminal.console_width must be at least 40, got {width}")
            elif width > 1000:
                errors.append(f"terminal.console_width must be at most 1000, got {width}")
        
        return errors
    
    def _validate_path_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate path configuration section."""
        errors = []
        
        # Check root_path if specified
        root_path = config.get("root_path")
        if root_path is not None:
            if not isinstance(root_path, str):
                errors.append(f"paths.root_path must be a string, got {type(root_path).__name__}")
            else:
                path_obj = Path(root_path)
                if not path_obj.exists():
                    errors.append(f"Specified root_path does not exist: {root_path}")
                elif not path_obj.is_dir():
                    errors.append(f"Specified root_path is not a directory: {root_path}")
        
        # Check template_file if specified
        template_file = config.get("template_file")
        if template_file is not None:
            if not isinstance(template_file, str):
                errors.append(f"paths.template_file must be a string, got {type(template_file).__name__}")
        
        return errors
    
    def _validate_template_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate template configuration section."""
        errors = []
        
        # Check template sections
        for section in ["index", "history"]:
            value = config.get(section)
            if value is not None:
                if not isinstance(value, str):
                    errors.append(f"template.{section} must be a string, got {type(value).__name__}")
                elif not value.strip():
                    errors.append(f"template.{section} cannot be empty")
                elif "{{filename}}" not in value:
                    errors.append(f"template.{section} must contain {{{{filename}}}} placeholder")
        
        return errors
    
    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """Validate configuration and raise exception if invalid."""
        errors = self.validate_configuration(config)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise SpecConfigurationError(
                error_msg,
                {"validation_errors": errors, "config_keys": list(config.keys())}
            )
    
    def get_validation_schema(self) -> Dict[str, Any]:
        """Get the expected configuration schema for documentation."""
        return {
            "debug": {
                "enabled": "boolean - Enable debug logging",
                "level": "string - One of: DEBUG, INFO, WARNING, ERROR", 
                "timing": "boolean - Enable timing measurements"
            },
            "terminal": {
                "use_color": "boolean - Enable colored output",
                "console_width": "integer - Console width (40-1000)"
            },
            "paths": {
                "root_path": "string - Project root directory path",
                "template_file": "string - Custom template file path"
            },
            "template": {
                "index": "string - Template for index.md files",
                "history": "string - Template for history.md files"
            }
        }
```

## Test Requirements

Create comprehensive tests for file loading and validation:

### Test Cases (13 tests total)

**Configuration Loader Tests:**
1. **test_configuration_loader_loads_from_yaml**
2. **test_configuration_loader_loads_from_pyproject_toml**
3. **test_configuration_loader_handles_missing_files**
4. **test_configuration_loader_respects_precedence_order**
5. **test_configuration_loader_handles_malformed_yaml**
6. **test_configuration_loader_handles_malformed_toml**
7. **test_configuration_loader_handles_encoding_errors**

**Configuration Validator Tests:**
8. **test_configuration_validator_accepts_valid_config**
9. **test_configuration_validator_rejects_invalid_debug_config**
10. **test_configuration_validator_rejects_invalid_terminal_config**
11. **test_configuration_validator_rejects_invalid_path_config**
12. **test_configuration_validator_rejects_invalid_template_config**
13. **test_configuration_validator_provides_helpful_error_messages**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Install YAML and TOML dependencies
poetry add PyYAML tomli

# Run the specific tests for this slice
poetry run pytest tests/unit/config/test_loader.py tests/unit/config/test_validation.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/config/test_loader.py tests/unit/config/test_validation.py --cov=spec_cli.config.loader --cov=spec_cli.config.validation --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/config/loader.py spec_cli/config/validation.py

# Check code formatting
poetry run ruff check spec_cli/config/loader.py spec_cli/config/validation.py
poetry run ruff format spec_cli/config/loader.py spec_cli/config/validation.py

# Verify imports work correctly
python -c "from spec_cli.config import ConfigurationLoader, ConfigurationValidator; print('Import successful')"

# Test configuration loading with sample files
echo "debug:" > .specconfig.yaml
echo "  enabled: true" >> .specconfig.yaml
echo "  level: DEBUG" >> .specconfig.yaml
python -c "
from spec_cli.config import ConfigurationLoader
from pathlib import Path
loader = ConfigurationLoader(Path.cwd())
config = loader.load_configuration()
print(f'Loaded config: {config}')
"
rm .specconfig.yaml
```

## Definition of Done

- [ ] ConfigurationLoader implemented with YAML and TOML support
- [ ] File loading with proper precedence handling
- [ ] Comprehensive error handling for malformed files
- [ ] ConfigurationValidator with detailed validation rules
- [ ] Helpful error messages for all validation failures
- [ ] All 13 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with existing SpecSettings from slice-3a
- [ ] Debug logging for all configuration operations
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice completes the configuration system foundation and enables:
- PHASE-2 file system operations that can use configuration settings
- PHASE-3 template system that can load configuration from files
- Full configuration integration across all subsequent phases
- File-based configuration for development and deployment settings