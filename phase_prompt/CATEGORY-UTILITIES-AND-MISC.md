# Utilities and Miscellaneous Agent Directive: Mixed Singleton Elimination

You are executing **Utilities and miscellaneous singleton migration** which systematically replaces remaining singleton calls with dependency injection in utility and miscellaneous modules. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **Utility singleton access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Remaining Singletons in Utilities and Misc

**GOAL**: Replace all remaining singleton calls across utility and miscellaneous modules with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero singleton calls remaining in utility/misc modules
- All utility functions accept dependencies via parameters
- 100% test pass rate maintained
- Utility functionality preserved

**TARGET FILES**:
- `spec_cli/utils/test_migration_utils.py` (2 get_settings() + 1 get_console()) - **TEST UTILITIES**
- `spec_cli/cli/decorators.py` (1 get_console() + 1 get_settings()) - **CLI DECORATORS**
- `spec_cli/cli/base_command.py` (1 get_settings()) - **BASE COMMAND**

---

## 🚨 UTILITIES MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break test utilities** → Test infrastructure must continue functioning
2. **NEVER modify decorator behavior** → CLI decorators must preserve functionality
3. **NEVER break base command patterns** → Command inheritance must work
4. **NEVER compromise utility reusability** → Utilities must remain composable
5. **NEVER proceed without testing each module** → Validate utility behavior after each change

> **Utilities Principle: "Dependency injection with preserved utility composability"**

---

## Step 1: Test Migration Utilities [CRITICAL - 3 CALLS]

### 1.1 Test Migration Utils Analysis [TEST INFRASTRUCTURE]

**File**: `spec_cli/utils/test_migration_utils.py`

**Critical Consideration**: This file contains utilities for testing migration itself - breaking it could cascade to test failures.

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ..config.settings import get_settings
from ..ui.console import get_console

class TestMigrationUtils:
    def __init__(self):
        pass
    
    def validate_migration(self):
        settings = get_settings()  # SINGLETON CALL
        console = get_console()   # SINGLETON CALL
        debug_mode = settings.debug_mode
        console.print("Validating migration...")
```

**Target Pattern**:
```python
# Dependency injection pattern
from ..config.settings import Settings
from rich.console import Console

class TestMigrationUtils:
    def __init__(self, settings: Settings = None, console: Console = None):
        if settings is None:
            raise ValueError("TestMigrationUtils requires settings instance")
        if console is None:
            raise ValueError("TestMigrationUtils requires console instance")
        self.settings = settings
        self.console = console
    
    def validate_migration(self):
        debug_mode = self.settings.debug_mode
        self.console.print("Validating migration...")
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/utils/test_migration_utils.py spec_cli/utils/test_migration_utils.py.backup

# 2. Find all singleton calls
grep -n "get_settings()\|get_console()" spec_cli/utils/test_migration_utils.py

# 3. Identify all functions and classes in test utils
grep -n "class\|def " spec_cli/utils/test_migration_utils.py
```

**Special Considerations for Test Utils**:
```bash
# Check if this utility is used in actual tests
grep -r "TestMigrationUtils\|test_migration_utils" tests/

# Check usage in migration scripts
grep -r "test_migration_utils" spec_cli/
```

**Transformation Steps**:

1. **Remove singleton imports**:
   ```python
   # REMOVE
   from ..config.settings import get_settings
   from ..ui.console import get_console
   
   # ADD (if not present)
   from ..config.settings import Settings
   from rich.console import Console
   ```

2. **Modify class/function signatures**:
   ```python
   # BEFORE
   def migration_validator():
       settings = get_settings()
       console = get_console()
   
   # AFTER  
   def migration_validator(settings: Settings, console: Console):
       # Use parameters directly
   ```

3. **Update all callers of test utilities**:
   ```bash
   # Find all usage of test migration utils
   grep -r "migration_validator\|TestMigrationUtils" spec_cli/ tests/
   
   # Each caller must now pass dependencies:
   # BEFORE: migration_validator()
   # AFTER:  migration_validator(settings, console)
   ```

---

## Step 2: CLI Decorators Migration [DECORATOR LOGIC - 2 CALLS]

### 2.1 CLI Decorators Analysis [DECORATOR PATTERNS]

**File**: `spec_cli/cli/decorators.py`

**Critical Consideration**: Decorators are used across CLI commands and must not break existing command interfaces.

**Current Pattern Analysis**:
```python
# Current problematic patterns in decorators
from ..config.settings import get_settings
from ..ui.console import get_console

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        settings = get_settings()  # SINGLETON
        console = get_console()    # SINGLETON
        
        if settings.enable_timing:
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            console.print(f"Command took {duration:.2f}s")
            return result
        return func(*args, **kwargs)
    return wrapper
```

**Target Pattern Options**:

**Option 1: Access from Click Context**:
```python
import click

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        settings = ctx.obj.settings
        console = ctx.obj.console
        
        if settings.enable_timing:
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            console.print(f"Command took {duration:.2f}s")
            return result
        return func(*args, **kwargs)
    return wrapper
```

**Option 2: Decorator Factory Pattern**:
```python
def timing_decorator(settings: Settings = None, console: Console = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided settings and console
            if settings and settings.enable_timing:
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                if console:
                    console.print(f"Command took {duration:.2f}s")
                return result
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Migration Commands**:
```bash
# Analyze decorator usage patterns
grep -n -A10 -B5 "get_settings\|get_console" spec_cli/cli/decorators.py

# Find where decorators are used
grep -r "@.*decorator" spec_cli/cli/commands/

# Check Click context availability
grep -r "click.get_current_context\|ctx.obj" spec_cli/cli/
```

### 2.2 Decorator Migration Strategy

**Recommended Approach**: Use Click context access (Option 1) for consistency with CLI patterns.

**Implementation**:
```python
# Updated decorator implementation
import click
import functools
import time

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            ctx = click.get_current_context()
            settings = ctx.obj.settings if ctx.obj else None
            console = ctx.obj.console if ctx.obj else None
            
            if settings and settings.enable_timing and console:
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                console.print(f"[dim]Command completed in {duration:.2f}s[/dim]")
                return result
        except RuntimeError:
            # No Click context available, run without timing
            pass
        
        return func(*args, **kwargs)
    return wrapper

def error_handler_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            ctx = click.get_current_context()
            console = ctx.obj.console if ctx.obj else None
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if console:
                    console.print(f"[red]Error: {e}[/red]")
                raise
        except RuntimeError:
            # No Click context available, run without error handling
            return func(*args, **kwargs)
    return wrapper
```

---

## Step 3: Base Command Migration [BASE CLASS - 1 CALL]

### 3.1 Base Command Analysis [COMMAND INHERITANCE]

**File**: `spec_cli/cli/base_command.py`

**Critical Consideration**: Base command is likely inherited by multiple CLI commands.

**Current Pattern Analysis**:
```python
# Current base command pattern
from ..config.settings import get_settings

class BaseCommand:
    def __init__(self):
        pass
    
    def setup(self):
        self.settings = get_settings()  # SINGLETON
        self.debug_mode = self.settings.debug_mode
```

**Target Pattern**:
```python
# Dependency injection pattern
from ..config.settings import Settings

class BaseCommand:
    def __init__(self, settings: Settings = None):
        if settings is None:
            # Try to get from Click context if available
            try:
                import click
                ctx = click.get_current_context()
                settings = ctx.obj.settings
            except (RuntimeError, AttributeError):
                raise ValueError("BaseCommand requires settings instance")
        
        self.settings = settings
        self.debug_mode = self.settings.debug_mode
```

**Migration Commands**:
```bash
# Analyze base command structure
grep -n -A10 -B5 "get_settings" spec_cli/cli/base_command.py

# Find all classes that inherit from BaseCommand
grep -r "BaseCommand" spec_cli/cli/commands/

# Check inheritance patterns
grep -r "class.*Command.*BaseCommand" spec_cli/cli/
```

**Inheritance Update Pattern**:
```python
# Commands that inherit from BaseCommand
# BEFORE
class AddCommand(BaseCommand):
    def __init__(self):
        super().__init__()

# AFTER (if needed)
class AddCommand(BaseCommand):
    def __init__(self, settings: Settings = None):
        super().__init__(settings)
```

---

## Step 4: Utility Function Migration Patterns

### 4.1 Module-Level Utility Functions

**Pattern**: For standalone utility functions that use singletons.

**Before Pattern**:
```python
# Utility function with singleton
def format_output(data):
    console = get_console()
    settings = get_settings()
    
    if settings.json_output:
        console.print_json(data)
    else:
        console.print(data)
```

**After Pattern**:
```python
# Utility function with parameters
def format_output(data, console: Console, settings: Settings):
    if settings.json_output:
        console.print_json(data)
    else:
        console.print(data)
```

### 4.2 Utility Class Migration

**Pattern**: For utility classes that encapsulate multiple functions.

**Migration Strategy**:
```python
# Utility class with injected dependencies
class MigrationHelper:
    def __init__(self, settings: Settings, console: Console):
        self.settings = settings
        self.console = console
    
    def log_migration_step(self, step_name):
        if self.settings.verbose_migration:
            self.console.print(f"[blue]Migration:[/blue] {step_name}")
    
    def validate_migration_state(self):
        # Use self.settings and self.console
        pass
```

---

## Step 5: Cross-Module Integration

### 5.1 Test Integration Updates

**Critical**: Update test utilities to work with new dependency patterns.

**Test Helper Updates**:
```python
# test_helpers.py updates
from spec_cli.config.settings import Settings
from rich.console import Console
from spec_cli.utils.test_migration_utils import TestMigrationUtils

def create_test_migration_utils():
    """Factory for creating test migration utils in tests."""
    settings = Settings()  # Test settings
    console = Console()    # Test console
    return TestMigrationUtils(settings, console)

def create_test_dependencies():
    """Create standard test dependencies."""
    return {
        'settings': Settings(),
        'console': Console()
    }
```

### 5.2 CLI Integration Updates

**Ensure**: CLI commands can access utilities with proper dependencies.

**CLI Integration Pattern**:
```python
# In CLI command
@click.command()
@click.pass_context
def test_command(ctx):
    settings = ctx.obj.settings
    console = ctx.obj.console
    
    # Pass dependencies to utilities
    test_utils = TestMigrationUtils(settings, console)
    test_utils.validate_migration()
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Syntax and Import Validation

```bash
# Validate syntax for all modified utility files
python -c "
import py_compile

utility_files = [
    'spec_cli/utils/test_migration_utils.py',
    'spec_cli/cli/decorators.py', 
    'spec_cli/cli/base_command.py'
]

for file in utility_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.utils.test_migration_utils
import spec_cli.cli.decorators
import spec_cli.cli.base_command
print('✅ All utility imports successful')
"
```

### 6.2 Decorator Functionality Tests

```bash
# Test CLI decorators still work
poetry run pytest tests/unit/cli/ -k "decorator" -v

# Test base command inheritance
poetry run pytest tests/unit/cli/ -k "base" -v
```

### 6.3 Utility Integration Tests

**Test Script**:
```python
# test_utility_integration.py
from spec_cli.config.settings import Settings
from rich.console import Console
from spec_cli.utils.test_migration_utils import TestMigrationUtils
from spec_cli.cli.base_command import BaseCommand

def test_utility_dependency_injection():
    settings = Settings()
    console = Console()
    
    try:
        # Test utility creation
        test_utils = TestMigrationUtils(settings, console)
        print("✅ Test migration utils accepts dependencies")
        
        # Test base command creation
        base_cmd = BaseCommand(settings)
        print("✅ Base command accepts dependencies")
        
        # Test functionality
        if hasattr(test_utils, 'validate_migration'):
            print("✅ Test utilities maintain functionality")
        
    except Exception as e:
        print(f"❌ Utility integration failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_utility_dependency_injection()
```

### 6.4 Decorator Testing

**Decorator Test Script**:
```python
# test_decorator_functionality.py
import click
from click.testing import CliRunner
from spec_cli.cli.decorators import timing_decorator
from spec_cli.config.settings import Settings
from rich.console import Console

@timing_decorator
@click.command()
@click.pass_context
def test_command(ctx):
    ctx.obj = {
        'settings': Settings(),
        'console': Console()
    }
    click.echo("Test command executed")

def test_decorators():
    runner = CliRunner()
    result = runner.invoke(test_command)
    
    if result.exit_code == 0:
        print("✅ Decorators work with dependency injection")
    else:
        print(f"❌ Decorator test failed: {result.output}")

if __name__ == "__main__":
    test_decorators()
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Test Utility Failures
```bash
# If test utilities break:
# 1. Check that test dependencies are properly injected
# 2. Verify test utility callers pass required parameters
# 3. Ensure test settings and console are valid instances
```

### Decorator Issues
```bash
# If decorators break CLI commands:
# 1. Verify Click context is available when decorators run
# 2. Check that ctx.obj contains settings and console
# 3. Ensure decorators handle missing context gracefully
```

### Base Command Inheritance Problems
```bash
# If command inheritance breaks:
# 1. Check that derived commands call super().__init__ properly
# 2. Verify settings are passed down inheritance chain
# 3. Ensure Click context access works in base class
```

### Missing Dependencies
```bash
# If utilities can't access dependencies:
# 1. Trace dependency flow from CLI entry point
# 2. Verify Click context setup includes all needed objects
# 3. Check that utility callers have access to dependencies
```

---

## Success Metrics [UTILITIES MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_console()` or `get_settings()` in utility modules
- **Preserved functionality**: All utilities work identically to before
- **Test infrastructure intact**: Test migration utilities continue working
- **Decorator compatibility**: CLI decorators maintain existing behavior
- **Base command inheritance**: Command inheritance patterns preserved

### Validation Commands
```bash
# Final validation
find spec_cli/utils/test_migration_utils.py spec_cli/cli/decorators.py spec_cli/cli/base_command.py | xargs grep -n "get_settings\|get_console" || echo "✅ Utilities migration complete"

# Test utilities work
python test_utility_integration.py

# Test decorators work  
python test_decorator_functionality.py

# Run utility tests
poetry run pytest tests/unit/utils/ tests/unit/cli/ -v
```

### End-to-End Utility Test
```bash
# Test complete utility workflow
python -c "
from spec_cli.config.settings import Settings
from rich.console import Console
from spec_cli.utils.test_migration_utils import TestMigrationUtils
from spec_cli.cli.base_command import BaseCommand

# Test full utility chain
settings = Settings()
console = Console()

test_utils = TestMigrationUtils(settings, console)
base_cmd = BaseCommand(settings)

print('✅ Utilities end-to-end test passed')
"
```

**Utilities migration eliminates the final singleton calls through systematic dependency injection while preserving all utility functionality and test infrastructure.**

---

## Final Migration Verification

After completing ALL category migrations, run this comprehensive verification:

```bash
# Verify NO singleton calls remain anywhere
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" && echo "❌ Singleton calls still exist" || echo "✅ ALL SINGLETON CALLS ELIMINATED"

# Run complete test suite
poetry run pytest tests/unit/ -v

# Test CLI functionality
python -m spec_cli --help

echo "🎉 SINGLETON MIGRATION COMPLETE!"
```