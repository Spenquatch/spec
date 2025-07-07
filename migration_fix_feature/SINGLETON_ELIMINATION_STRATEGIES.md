# Singleton Elimination Strategies

## Overview

This document provides specific elimination strategies for each type of singleton pattern identified in the codebase, with detailed implementation guidance and code examples.

## Strategy Categories

### 1. Direct Replacement Strategy
**Best for**: Simple singleton instances with minimal dependencies
**Complexity**: Low
**Timeline**: 1-2 days per pattern

### 2. Factory Pattern Strategy  
**Best for**: Complex singletons with initialization logic
**Complexity**: Medium
**Timeline**: 3-5 days per pattern

### 3. Contextual Injection Strategy
**Best for**: Singletons that need to be scoped to operations
**Complexity**: Medium-High
**Timeline**: 5-7 days per pattern

### 4. Wrapper Compatibility Strategy
**Best for**: Legacy singletons with many access points
**Complexity**: High
**Timeline**: 7-10 days per pattern

## Pattern-Specific Strategies

### CLI Context Singletons

**Pattern Type**: Global context access
**Strategy**: Direct Replacement with Dependency Injection
**Complexity**: Low-Medium
**Estimated Effort**: 2 weeks

**Current Pattern:**
```python
# Anti-pattern: Singleton context access
from spec_cli.core.context import get_context

def some_command():
    context = get_context()  # Singleton access
    settings = context.settings
    console = context.console
```

**Target Pattern:**
```python
# Target: Dependency injection
from spec_cli.core.decorators import inject_context

@inject_context
def some_command(context):
    settings = context.settings
    console = context.console
```

**Migration Steps:**
1. Update command function signatures to accept context parameter
2. Replace `@click.command()` with `@inject_context` decorator
3. Remove all `get_context()` calls within command functions
4. Update test fixtures to provide mock context instances

**Validation Criteria:**
- Zero `get_context()` calls in command implementations
- All CLI commands accept context through dependency injection
- Test coverage maintains 100%
- Command behavior identical to pre-migration

### Configuration Manager Singletons

**Pattern Type**: Global configuration access
**Strategy**: Factory Pattern with Context Injection
**Complexity**: Medium
**Estimated Effort**: 2 weeks

**Current Pattern:**
```python
# Anti-pattern: Singleton configuration
from spec_cli.config.settings import get_settings

def process_file():
    settings = get_settings()  # Singleton access
    max_size = settings.max_file_size
    debug_mode = settings.debug_enabled
```

**Target Pattern:**
```python
# Target: Injected configuration
def process_file(context):
    settings = context.settings  # Injected through context
    max_size = settings.max_file_size
    debug_mode = settings.debug_enabled
```

**Migration Steps:**
1. Create `SettingsFactory` in context initialization
2. Update context to provide settings instance via factory
3. Replace all `get_settings()` calls with context.settings access
4. Update configuration loading to use factory pattern
5. Migrate test fixtures to provide mock settings through context

**Validation Criteria:**
- Zero global settings access outside of factory
- All configuration access through context dependency chain
- Settings initialization controlled by context factory
- Configuration validation maintained

### Logger Singletons

**Pattern Type**: Global logger instances
**Strategy**: Contextual Injection
**Complexity**: Low
**Estimated Effort**: 1 week

**Current Pattern:**
```python
# Anti-pattern: Global logger singleton
from spec_cli.logging.debug import debug_logger

def analyze_pattern():
    debug_logger.log("INFO", "Starting analysis")  # Singleton access
    # ... processing ...
    debug_logger.log("DEBUG", "Pattern found", pattern_type="metaclass")
```

**Target Pattern:**
```python
# Target: Injected logger
def analyze_pattern(context):
    logger = context.logger  # Injected logger
    logger.log("INFO", "Starting analysis")
    # ... processing ...
    logger.log("DEBUG", "Pattern found", pattern_type="metaclass")
```

**Migration Steps:**
1. Update context to provide logger instance
2. Replace all `debug_logger` imports with context.logger access
3. Maintain logger configuration and hierarchy through context
4. Update utility functions to accept logger parameter or context

**Validation Criteria:**
- Zero direct debug_logger imports in non-test code
- All logging through context-provided logger instances
- Logging hierarchy and configuration preserved
- Log output format and levels unchanged

### Progress Manager Singletons

**Pattern Type**: UI state management singletons
**Strategy**: Contextual Injection with Factory
**Complexity**: Medium
**Estimated Effort**: 1 week

**Current Pattern:**
```python
# Anti-pattern: Global progress manager
from spec_cli.ui.progress_manager import get_progress_manager

def long_operation():
    progress = get_progress_manager()  # Singleton access
    progress.start_operation("Processing files")
    for file in files:
        progress.update_progress(file.name)
    progress.complete_operation()
```

**Target Pattern:**
```python
# Target: Context-provided progress manager
def long_operation(context):
    progress = context.progress_manager  # Injected instance
    progress.start_operation("Processing files")
    for file in files:
        progress.update_progress(file.name)
    progress.complete_operation()
```

**Migration Steps:**
1. Create progress manager factory in context
2. Update context to provide progress manager instances
3. Replace all global progress manager access with context access
4. Update UI components to use injected progress managers

**Validation Criteria:**
- Zero global progress manager access
- Progress tracking through context-provided instances
- UI behavior identical to pre-migration
- Progress state properly scoped to operations

### Utility Class Singletons

**Pattern Type**: Stateless utility singletons
**Strategy**: Static Method Conversion
**Complexity**: Low
**Estimated Effort**: 3-5 days

**Current Pattern:**
```python
# Anti-pattern: Singleton utility class
class FileUtils:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def normalize_path(self, path):
        return str(Path(path).resolve())

# Usage
utils = FileUtils()  # Singleton access
normalized = utils.normalize_path(file_path)
```

**Target Pattern:**
```python
# Target: Static utility functions
class FileUtils:
    @staticmethod
    def normalize_path(path: Path | str) -> str:
        return str(Path(path).resolve())

# Usage
normalized = FileUtils.normalize_path(file_path)
```

**Migration Steps:**
1. Convert singleton methods to static methods
2. Remove singleton construction logic
3. Update all instantiation sites to direct static calls
4. Add type hints and proper error handling

**Validation Criteria:**
- Zero singleton construction patterns
- All utility methods accessible as static functions
- Same functionality with better type safety
- No state sharing between utility calls

### Cache Manager Singletons

**Pattern Type**: Shared cache instances
**Strategy**: Context-Scoped Factory
**Complexity**: Medium-High
**Estimated Effort**: 1 week

**Current Pattern:**
```python
# Anti-pattern: Global cache singleton
from spec_cli.utils.cache import get_cache

def expensive_operation(data):
    cache = get_cache()  # Singleton access
    if cache.has(data.key):
        return cache.get(data.key)
    
    result = process_data(data)
    cache.set(data.key, result)
    return result
```

**Target Pattern:**
```python
# Target: Context-scoped cache
def expensive_operation(data, context):
    cache = context.cache  # Scoped to context
    if cache.has(data.key):
        return cache.get(data.key)
    
    result = process_data(data)
    cache.set(data.key, result)
    return result
```

**Migration Steps:**
1. Create cache factory with configurable scope (operation, session, global)
2. Update context to provide appropriate cache instances
3. Replace global cache access with context-provided caches
4. Implement cache cleanup and lifecycle management

**Validation Criteria:**
- Cache scope properly managed by context
- No global cache state leakage between operations
- Cache performance maintained or improved
- Memory usage controlled by context lifecycle

## Implementation Guidelines

### Phase Sequencing
1. **Phase 1**: CLI Context Singletons (highest impact, foundation for others)
2. **Phase 2**: Configuration Manager Singletons (enables better testing)
3. **Phase 3**: Logger Singletons (supports better debugging)
4. **Phase 4**: Progress Manager and UI Singletons (visible improvements)
5. **Phase 5**: Utility and Cache Singletons (cleanup and optimization)

### Quality Gates per Strategy
Each strategy implementation must meet:
- **Functionality**: Identical behavior to singleton version
- **Performance**: No more than 5% performance degradation
- **Testability**: Improved or maintained test coverage
- **Maintainability**: Clearer dependency relationships

### Risk Mitigation
- **Compatibility Wrappers**: Maintain during transition period
- **Gradual Migration**: One pattern type at a time
- **Comprehensive Testing**: Before and after migration validation
- **Rollback Capability**: Each phase can be independently reverted

### Validation Framework
Each eliminated singleton must pass:
1. **Functional Tests**: All existing functionality works
2. **Performance Tests**: No significant performance regression
3. **Integration Tests**: Proper interaction with other components
4. **Security Tests**: No new vulnerabilities introduced
5. **Singleton Detection**: Zero violations in detection pipeline

## Success Metrics

### Quantitative Measures
- **Singleton Count**: Target zero singleton patterns in production code
- **Test Coverage**: Maintain 100% coverage throughout migration
- **Performance**: Stay within 5% of baseline performance
- **Memory Usage**: No significant increase in memory footprint

### Qualitative Measures
- **Code Clarity**: Improved dependency visibility
- **Testability**: Easier unit testing with dependency injection
- **Maintainability**: Clearer separation of concerns
- **Debugging**: Better traceability of component interactions

This strategy document provides the detailed implementation guidance needed to systematically eliminate all singleton patterns while maintaining system stability and functionality.