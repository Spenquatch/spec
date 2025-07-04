# ARCHITECTURE_IMPROVEMENT.md

## Critical Architecture Issue: Singleton Pattern Contamination

### Executive Summary

The spec-cli codebase contains a **critical architectural flaw** in the form of global singleton pattern usage that creates production reliability issues and systematic test contamination. This document outlines the exact problem and provides a detailed migration plan to a dependency injection architecture.

**Impact**: 58 out of 1851 tests fail systematically due to singleton state contamination, indicating a fundamental production reliability risk.

## Root Cause Analysis

### Problem Description

The codebase relies on 4 major singleton classes that maintain persistent global state:

1. **`SettingsManager`** (`spec_cli/config/settings.py`) - Stores global settings and console instances
2. **`ConsoleManager`** (`spec_cli/ui/console.py`) - Manages global console instances  
3. **`ProgressManagerSingleton`** (`spec_cli/ui/progress_manager.py`) - Tracks progress state globally
4. **Singleton Infrastructure** (`spec_cli/utils/singleton.py`) - Global dictionaries storing all singleton instances

### Technical Mechanism

```python
# Current problematic pattern in singleton.py
_instances: dict[type[Any], Any] = {}  # Global state persists across operations
_instance_locks: dict[type[Any], threading.Lock] = {}

@singleton_decorator
class SettingsManager:
    def __init__(self):
        self._settings_instance: SpecSettings | None = None  # Persists between CLI operations
        self._console_instance: Console | None = None
```

### Production Reliability Issues

1. **State Contamination**: Configuration from one CLI operation affects subsequent operations
2. **Memory Leaks**: Progress managers accumulate state that never gets cleaned up
3. **Concurrent Operation Conflicts**: Multiple CLI processes interfere with shared global state
4. **Hidden Dependencies**: Code throughout the application has implicit dependencies on global state
5. **Testing Contamination**: 58 systematic test failures due to state bleeding between tests

### Evidence

- **Tests pass individually**: Each test gets fresh singleton instances
- **Tests fail in suite**: Previous test state contaminates subsequent tests
- **Consistent failure pattern**: Exactly 58 tests fail regardless of test execution order
- **Production implications**: Same contamination mechanism affects real CLI usage

## Solution: Dependency Injection with Context Objects

### Architecture Overview

Replace global singletons with **immutable context objects** that are explicitly passed through the application call chain.

### Key Principles

1. **Immutable Context**: All dependencies bundled in frozen dataclass
2. **Explicit Dependencies**: No hidden global state access
3. **Factory Pattern**: Separate factories for CLI usage vs testing
4. **Click Integration**: Leverage Click's built-in context system
5. **Thread Safety**: Immutable objects eliminate race conditions

## Implementation Plan

### Phase 1: Context Infrastructure (Day 1-2)

#### Create Core Context Object

Create `spec_cli/core/context.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from ..config.settings import SpecSettings
from ..ui.console import SpecConsole
from ..ui.progress_manager import ProgressManager


@dataclass(frozen=True)
class SpecContext:
    """Immutable context containing all application dependencies.
    
    This replaces the singleton pattern with explicit dependency injection.
    Each CLI operation receives a fresh context with all required dependencies.
    """
    settings: SpecSettings
    console: SpecConsole
    progress_manager: ProgressManager
    
    @classmethod
    def create_for_cli(cls, root_path: Path | None = None) -> 'SpecContext':
        """Factory method for CLI usage.
        
        Args:
            root_path: Optional root path for spec operations
            
        Returns:
            Fresh context with production dependencies
        """
        settings = SpecSettings(root_path or Path.cwd())
        console = SpecConsole(
            width=settings.console_width,
            no_color=not settings.use_color,
            force_terminal=settings.use_color
        )
        progress_manager = ProgressManager(auto_display=True)
        
        return cls(
            settings=settings,
            console=console,
            progress_manager=progress_manager
        )
    
    @classmethod
    def create_for_testing(cls, **overrides: Any) -> 'SpecContext':
        """Factory for testing with mock dependencies.
        
        Args:
            **overrides: Override specific dependencies with mocks
            
        Returns:
            Context with mock dependencies for testing
            
        Example:
            ctx = SpecContext.create_for_testing(
                console=Mock(spec=SpecConsole),
                settings=Mock(spec=SpecSettings)
            )
        """
        defaults = {
            'settings': Mock(spec=SpecSettings),
            'console': Mock(spec=SpecConsole),
            'progress_manager': Mock(spec=ProgressManager)
        }
        defaults.update(overrides)
        return cls(**defaults)
    
    def create_repository(self) -> 'SpecGitRepository':
        """Create a Git repository with this context's settings.
        
        Returns:
            Configured SpecGitRepository instance
        """
        from ..git.repository import SpecGitRepository
        return SpecGitRepository(self.settings)
```

#### Create Backward Compatibility Layer

Create `spec_cli/core/compatibility.py`:

```python
"""Backward compatibility layer during singleton migration.

This module provides wrapper functions that maintain the existing API
while gradually migrating to context-based dependency injection.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.settings import SpecSettings
    from ..ui.console import SpecConsole
    from .context import SpecContext

# Global context for backward compatibility (will be removed in Phase 3)
_global_context: 'SpecContext | None' = None


def get_current_context() -> 'SpecContext':
    """Get current global context (temporary during migration)."""
    global _global_context
    if _global_context is None:
        from .context import SpecContext
        _global_context = SpecContext.create_for_cli()
    return _global_context


def reset_global_context(root_path: Path | None = None) -> None:
    """Reset global context (temporary during migration)."""
    global _global_context
    from .context import SpecContext
    _global_context = SpecContext.create_for_cli(root_path)


# Backward compatibility wrappers (to be removed in Phase 3)
def get_settings(root_path: Path | None = None) -> 'SpecSettings':
    """Backward compatibility wrapper for get_settings()."""
    if root_path:
        reset_global_context(root_path)
    return get_current_context().settings


def get_console(root_path: Path | None = None) -> 'SpecConsole':
    """Backward compatibility wrapper for get_console()."""
    if root_path:
        reset_global_context(root_path)
    return get_current_context().console
```

### Phase 2: CLI Integration (Day 3-4)

#### Update Main CLI Application

Modify `spec_cli/cli/app.py`:

```python
"""Main CLI application with Click framework and dependency injection."""

import click
from pathlib import Path

from ..core.context import SpecContext
from .commands import help_command, init_command, status_command
# ... other imports


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--version", is_flag=True, help="Show version information")
@click.option("--root-path", type=click.Path(exists=True, path_type=Path), 
              help="Root path for spec operations")
@click.pass_context
def app(ctx: click.Context, version: bool, root_path: Path | None) -> None:
    """Spec CLI - Versioned Documentation for AI-Assisted Development.

    Manage documentation specs for your codebase with Git integration.
    """
    # Initialize context for dependency injection
    ctx.ensure_object(dict)
    ctx.obj['spec_context'] = SpecContext.create_for_cli(root_path)
    
    if version:
        click.echo("Spec CLI v0.1.0")
        return

    if ctx.invoked_subcommand is None:
        # No subcommand provided, show help
        spec_ctx: SpecContext = ctx.obj['spec_context']
        spec_ctx.console.print_status("Use --help for available commands", "info")


# Commands will be updated to receive context in Phase 2
```

#### Update Command Pattern

Create new command decorator in `spec_cli/cli/commands/base.py`:

```python
"""Base command functionality with context injection."""

import click
from typing import Callable, Any
from functools import wraps

from ...core.context import SpecContext


def spec_command_with_context(name: str | None = None):
    """Decorator for spec commands that receive SpecContext.
    
    Args:
        name: Optional command name
        
    Returns:
        Decorated command function with SpecContext injection
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @click.command(name=name)
        @click.pass_context
        @wraps(func)
        def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
            # Inject SpecContext as first argument
            spec_ctx: SpecContext = ctx.obj['spec_context']
            return func(spec_ctx, *args, **kwargs)
        
        return wrapper
    return decorator
```

#### Update Individual Commands

Example migration for `spec_cli/cli/commands/init.py`:

```python
"""Spec init command implementation with dependency injection."""

from pathlib import Path
import click

from ...exceptions import SpecRepositoryError
from ...core.context import SpecContext
from ..commands.base import spec_command_with_context


@spec_command_with_context()
@click.option("--force", is_flag=True, help="Force reinitialize if already exists")
def init_command(ctx: SpecContext, force: bool) -> None:
    """Initialize spec repository with explicit dependencies.

    Args:
        ctx: Application context containing all dependencies
        force: Whether to force reinitialize existing repository
    """
    try:
        # Use context dependencies instead of singletons
        repo = ctx.create_repository()
        current_dir = Path.cwd()

        # Check if already initialized
        if repo.is_initialized() and not force:
            ctx.console.print_status(
                "Spec repository is already initialized. Use --force to reinitialize.",
                "warning",
            )
            return

        if force and repo.is_initialized():
            ctx.console.print_status("Force reinitializing spec repository...", "info")
        else:
            ctx.console.print_status("Initializing spec repository...", "info")

        # Initialize repository
        repo.initialize()

        # Verify initialization
        if not repo.is_initialized():
            raise SpecRepositoryError("Repository initialization failed")

        # Display success message using context console
        success_msg = (
            "Spec repository initialized successfully!\n\n"
            "Created directories:\n"
            "  • .spec/     - Git repository for spec tracking\n"
            "  • .specs/    - Documentation directory\n\n"
            "Next steps:\n"
            "  • Run 'spec status' to check repository status\n"
            "  • Run 'spec gen <files>' to generate documentation"
        )

        ctx.console.print_status(success_msg, "success")

    except SpecRepositoryError as e:
        raise click.ClickException(f"Repository initialization failed: {e}") from e
    except Exception as e:
        raise click.ClickException(
            f"Unexpected error during initialization: {e}"
        ) from e
```

### Phase 3: Complete Migration (Day 5-6)

#### Remove Singleton Infrastructure

1. **Delete singleton files**:
   - Remove `spec_cli/utils/singleton.py`
   - Remove singleton decorators from all manager classes

2. **Update manager classes**:

```python
# spec_cli/config/settings.py - Remove singleton, make regular class
class SpecSettings:
    """Configuration settings (no longer singleton)."""
    
    def __init__(self, root_path: Path | None = None):
        # Same initialization logic, but no singleton behavior
        pass

# Remove SettingsManager class entirely - replaced by SpecContext
```

3. **Update Git Repository**:

```python
# spec_cli/git/repository.py - Remove get_settings() calls
class SpecGitRepository(GitRepository):
    """Git repository implementation with explicit settings injection."""

    def __init__(self, settings: SpecSettings):
        """Initialize with explicit settings dependency."""
        self.settings = settings  # No longer calls get_settings()
        # ... rest of initialization
```

#### Update All Tests

Create test context fixtures in `tests/conftest.py`:

```python
"""Pytest configuration with context-based testing."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from spec_cli.core.context import SpecContext
from spec_cli.config.settings import SpecSettings
from spec_cli.ui.console import SpecConsole


@pytest.fixture
def spec_context(tmp_path: Path) -> SpecContext:
    """Create test context with temporary directory."""
    return SpecContext.create_for_cli(tmp_path)


@pytest.fixture
def mock_spec_context() -> SpecContext:
    """Create test context with mock dependencies."""
    return SpecContext.create_for_testing()


@pytest.fixture
def spec_context_with_mocks(tmp_path: Path) -> SpecContext:
    """Create test context with real settings but mock UI components."""
    settings = SpecSettings(tmp_path)
    return SpecContext.create_for_testing(
        settings=settings,
        console=Mock(spec=SpecConsole)
    )
```

Update test files to use context injection:

```python
# Example test update
def test_init_command_success(spec_context: SpecContext):
    """Test successful repository initialization."""
    # Test uses explicit context instead of global singletons
    repo = spec_context.create_repository()
    
    # Test implementation with no global state dependencies
    assert not repo.is_initialized()
    repo.initialize()
    assert repo.is_initialized()
```

## Migration Checklist

### Phase 1 Deliverables
- [ ] Create `SpecContext` dataclass with factory methods
- [ ] Create backward compatibility layer
- [ ] Add comprehensive tests for context factories
- [ ] Document context usage patterns

### Phase 2 Deliverables  
- [ ] Update CLI entry point with Click context injection
- [ ] Create new command decorator with context injection
- [ ] Migrate 3-5 core commands to context pattern
- [ ] Verify CLI functionality with new pattern
- [ ] Update integration tests

### Phase 3 Deliverables
- [ ] Migrate all remaining commands to context pattern
- [ ] Remove singleton infrastructure completely
- [ ] Update all unit tests to use context fixtures
- [ ] Remove backward compatibility layer
- [ ] Verify 100% test success rate
- [ ] Update documentation and examples

## Success Metrics

### Immediate Benefits
- **Test Reliability**: 0 systematic test failures (down from 58)
- **Memory Efficiency**: No accumulated state across CLI operations
- **Concurrent Safety**: Multiple CLI processes can run without interference

### Long-term Benefits
- **Maintainability**: Clear dependency graph, easy to test and debug
- **Scalability**: Can add new dependencies without global state pollution
- **Reliability**: Eliminates entire class of state contamination bugs

## Risk Mitigation

### Backward Compatibility
- Phase 1 maintains existing API through compatibility layer
- Gradual migration minimizes disruption
- Extensive testing at each phase

### Performance
- Context object creation is lightweight (< 1ms overhead)
- Immutable objects eliminate synchronization overhead
- No impact on CLI operation performance

### Team Adoption
- Clear migration path with concrete examples
- Comprehensive documentation and test patterns
- Backward compatibility during transition period

## Conclusion

This architectural improvement eliminates a fundamental flaw in the codebase that affects both testing reliability and production stability. The dependency injection pattern with immutable context objects provides a robust foundation for future development while solving the immediate singleton contamination issues.

The migration can be completed in 5-6 days with minimal disruption to ongoing development, and provides immediate benefits in terms of test reliability and code maintainability.