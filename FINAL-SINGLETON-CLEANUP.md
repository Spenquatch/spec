# Final Singleton Cleanup Agent Directive

You are executing **Final singleton cleanup** which eliminates the last remaining singleton calls with dependency injection. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **All singleton calls are eliminated or not touched. No partial states exist.**

## Mission: Eliminate Final 11 Singleton Calls

**GOAL**: Replace the final 11 actual singleton calls with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero functional singleton calls remaining in codebase
- All components use dependency injection
- 100% test pass rate maintained
- All functionality preserved

**REMAINING CALLS TO MIGRATE**:
- **CLI Utilities**: 7 calls across 4 files
- **Core Context**: 1 call 
- **UI Theme**: 1 call
- **Context Bridge**: 2 calls

---

## 🚨 FINAL CLEANUP GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break CLI functionality** → Commands must continue working identically
2. **NEVER modify Click context contracts** → Preserve existing CLI patterns
3. **NEVER break theme/styling** → UI appearance must remain unchanged
4. **NEVER compromise context bridge** → Facade must continue working
5. **NEVER proceed without testing each fix** → Validate behavior after each change

> **Final Cleanup Principle: "Complete elimination with preserved functionality"**

---

## Step 1: CLI Utilities Migration [7 CALLS - HIGHEST PRIORITY]

### 1.1 CLI Options Migration [1 CALL]

**File**: `spec_cli/cli/options.py:139`

**Current Code**:
```python
def require_repository():
    """Decorator that ensures command is run in a spec repository."""
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    try:
        settings = get_settings()  # SINGLETON CALL - LINE 139
        repo = SpecGitRepository(settings)
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
```

**Target Pattern**:
```python
def require_repository(settings=None):
    """Decorator that ensures command is run in a spec repository."""
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    def decorator(func):
        @click.pass_context
        def wrapper(ctx, *args, **kwargs):
            # Get settings from context or parameter
            actual_settings = settings or ctx.obj.settings
            repo = SpecGitRepository(actual_settings)
            if not repo.is_initialized():
                raise click.ClickException(
                    "Not in a spec repository. Run 'spec init' to initialize."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Migration Steps**:
1. Convert `require_repository()` from direct function to decorator factory
2. Use Click context to access settings
3. Update all usages: `@require_repository` → `@require_repository()`

### 1.2 CLI Utils Migration [2 CALLS]

**File**: `spec_cli/cli/utils.py:163` and `spec_cli/cli/utils.py:226`

**Current Code Line 163**:
```python
def get_spec_repository():
    """Get initialized spec repository for CLI commands."""
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    try:
        settings = get_settings()  # SINGLETON CALL - LINE 163
        repo = SpecGitRepository(settings)
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return repo
```

**Current Code Line 226**:
```python
def format_validation_errors(errors: list[ValidationError]) -> str:
    """Format validation errors for CLI display."""
    if not errors:
        return ""

    settings = get_settings()  # SINGLETON CALL - LINE 226
    if settings.verbose_errors:
        # Detailed formatting
```

**Target Pattern**:
```python
def get_spec_repository(settings=None):
    """Get initialized spec repository for CLI commands."""
    from ..exceptions import SpecRepositoryError
    from ..git.repository import SpecGitRepository

    # Accept settings parameter or get from Click context
    if settings is None:
        try:
            import click
            ctx = click.get_current_context()
            settings = ctx.obj.settings
        except RuntimeError:
            raise click.ClickException("Settings not available - call from CLI context")

    try:
        repo = SpecGitRepository(settings)
        if not repo.is_initialized():
            raise click.ClickException(
                "Not in a spec repository. Run 'spec init' to initialize."
            )
        return repo
```

**Migration Steps**:
1. Add optional `settings` parameter to both functions
2. Use Click context fallback when settings not provided
3. Update all callers to pass settings when available

### 1.3 Generation Prompts Migration [2 CALLS]

**File**: `spec_cli/cli/commands/generation/prompts.py:198` and `spec_cli/cli/commands/generation/prompts.py:341`

**Current Code Line 198**:
```python
def __init__(self, console: ConsoleType, settings: SpecSettings | None = None) -> None:
    """Initialize generation prompts with selector, resolver, and console."""
    self.settings = settings or get_settings()  # SINGLETON CALL - LINE 198
```

**Current Code Line 341**:
```python
def show_template_selection_prompt(
    templates: list[str], console: ConsoleType, settings: SpecSettings | None = None
) -> str:
    """Show interactive template selection prompt."""
    settings = settings or get_settings()  # SINGLETON CALL - LINE 341
```

**Target Pattern**:
```python
def __init__(self, console: ConsoleType, settings: SpecSettings) -> None:
    """Initialize generation prompts with selector, resolver, and console."""
    if settings is None:
        raise ValueError("GenerationPrompts requires a settings instance")
    self.settings = settings

def show_template_selection_prompt(
    templates: list[str], console: ConsoleType, settings: SpecSettings
) -> str:
    """Show interactive template selection prompt."""
    if settings is None:
        raise ValueError("show_template_selection_prompt requires settings")
```

**Migration Steps**:
1. Remove `None` default from settings parameters
2. Require settings to be passed explicitly
3. Update all callers to provide settings from CLI context

### 1.4 Generation Workflows Migration [2 CALLS]

**File**: `spec_cli/cli/commands/generation/workflows.py:313` and `spec_cli/cli/commands/generation/workflows.py:429`

**Current Code Line 313**:
```python
def get_related_spec_files(source_file: Path) -> list[Path]:
    """Get existing spec files related to a source file."""
    from ....core.context_bridge import get_settings
    from ....file_system.path_resolver import PathResolver

    settings = get_settings()  # SINGLETON CALL - LINE 313
    path_resolver = PathResolver(settings)
```

**Current Code Line 429**:
```python
def __init__(self, console: ConsoleType, settings: SpecSettings | None = None) -> None:
    """Initialize batch generation workflow."""
    self.settings = settings or get_settings()  # SINGLETON CALL - LINE 429
```

**Target Pattern**:
```python
def get_related_spec_files(source_file: Path, settings: SpecSettings) -> list[Path]:
    """Get existing spec files related to a source file."""
    from ....file_system.path_resolver import PathResolver

    path_resolver = PathResolver(settings)

def __init__(self, console: ConsoleType, settings: SpecSettings) -> None:
    """Initialize batch generation workflow."""
    if settings is None:
        raise ValueError("BatchGenerationWorkflow requires a settings instance")
    self.settings = settings
```

**Migration Steps**:
1. Add `settings` parameter to `get_related_spec_files()`
2. Remove singleton fallback in `__init__`
3. Update all callers to pass settings

---

## Step 2: Core Context Migration [1 CALL]

### 2.1 Core Context Migration

**File**: `spec_cli/core/context.py:466`

**Current Code**:
```python
# Create CLI settings with real configuration using actual implementations
from ..core.context_bridge import get_settings
from ..ui.console import SpecConsole
from ..ui.progress_manager import ProgressManager

cli_settings = get_settings()  # SINGLETON CALL - LINE 466
cli_console = SpecConsole()
cli_progress = ProgressManager(console=cli_console.console)
```

**Target Pattern**:
```python
# Create CLI settings with real configuration using actual implementations
from ..config.settings import SpecSettings
from ..ui.console import SpecConsole
from ..ui.progress_manager import ProgressManager

cli_settings = SpecSettings()  # Direct instantiation instead of singleton
cli_console = SpecConsole()
cli_progress = ProgressManager(console=cli_console.console)
```

**Migration Steps**:
1. Replace `get_settings()` with direct `SpecSettings()` instantiation
2. Remove singleton import
3. Test context initialization works correctly

---

## Step 3: UI Theme Migration [1 CALL]

### 3.1 UI Theme Migration

**File**: `spec_cli/ui/theme.py:206`

**Current Code**:
```python
def apply_theme(theme_name: str, settings: SpecSettings | None = None) -> None:
    """Apply a theme to the console."""
    settings = settings or get_settings()  # SINGLETON CALL - LINE 206
```

**Target Pattern**:
```python
def apply_theme(theme_name: str, settings: SpecSettings) -> None:
    """Apply a theme to the console."""
    if settings is None:
        raise ValueError("apply_theme requires a settings instance")
```

**Migration Steps**:
1. Remove `None` default from settings parameter
2. Require settings to be passed explicitly
3. Update all callers to provide settings

---

## Step 4: Context Bridge Cleanup [2 CALLS]

### 4.1 Context Bridge Internal Usage

**File**: `spec_cli/core/context_bridge.py:218` and `spec_cli/core/context_bridge.py:222`

**Current Code**:
```python
def validate_facade_bridge() -> bool:
    """Validate that the facade bridge is working correctly."""
    try:
        # Test console access
        console = get_console()  # SINGLETON CALL - LINE 218
        
        # Test settings access  
        get_settings()  # SINGLETON CALL - LINE 222
        
        return True
    except Exception:
        return False
```

**Target Pattern**:
```python
def validate_facade_bridge() -> bool:
    """Validate that the facade bridge is working correctly."""
    try:
        # Test console access through facade
        console = _original_get_console()
        
        # Test settings access through facade
        _original_get_settings()
        
        return True
    except Exception:
        return False
```

**Migration Steps**:
1. Replace facade calls with direct original calls
2. This validates the underlying implementations work
3. Test that validation function still works

---

## Step 5: Caller Site Updates [DEPENDENCY PLUMBING]

### 5.1 Update CLI Command Callers

**Critical**: All CLI commands that call the updated functions must pass settings.

**Discovery Commands**:
```bash
# Find usages of updated functions
grep -r "require_repository\|get_spec_repository\|show_template_selection_prompt" spec_cli/cli/commands/
grep -r "get_related_spec_files\|apply_theme" spec_cli/
```

**CLI Integration Pattern**:
```python
# In CLI commands
@click.command()
@click.pass_context
def some_command(ctx):
    settings = ctx.obj.settings
    
    # Pass settings to updated functions
    repo = get_spec_repository(settings)
    apply_theme("default", settings)
```

### 5.2 Update Generation Command Integration

**Pattern**: Generation commands need to pass settings to workflows and prompts.

```python
# In generation commands
@click.command()
@click.pass_context
def gen_command(ctx):
    settings = ctx.obj.settings
    console = ctx.obj.console
    
    # Pass both settings and console
    prompts = GenerationPrompts(console, settings)
    workflow = BatchGenerationWorkflow(console, settings)
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Function Call Validation

```bash
# Verify all singleton calls are eliminated
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "string\|comment"

# Should return only:
# - Factory implementations (ui/console.py, ui/progress_manager.py)
# - Context bridge facade implementations
# - Test utilities
```

### 6.2 CLI Functionality Testing

```bash
# Test CLI commands still work
python -m spec_cli --help
python -m spec_cli init
python -m spec_cli status

# Test generation commands
python -m spec_cli gen --help

# Test error handling
python -m spec_cli status  # Should fail gracefully if not in repo
```

### 6.3 Integration Testing

**Test Script**:
```python
# test_final_cleanup.py
import click
from click.testing import CliRunner
from spec_cli.cli.app import cli

def test_final_singleton_cleanup():
    runner = CliRunner()
    
    # Test commands work without singleton calls
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    
    # Test error handling
    result = runner.invoke(cli, ['status'])
    assert "Not in a spec repository" in result.output or result.exit_code == 0
    
    print("✅ Final singleton cleanup successful")

if __name__ == "__main__":
    test_final_singleton_cleanup()
```

---

## Step 7: Final Verification [COMPLETE ELIMINATION]

### 7.1 Comprehensive Singleton Scan

```bash
# Final verification - should show only acceptable patterns
echo "=== FINAL SINGLETON VERIFICATION ==="
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import"

echo ""
echo "Acceptable remaining patterns:"
echo "✅ Factory implementations (ui/console.py, ui/progress_manager.py)"
echo "✅ Context bridge facade (core/context_bridge.py facade functions)"
echo "✅ Test utilities (utils/test_migration_utils.py)"
echo "✅ Comments (cli/commands/diff.py)"
echo ""
echo "❌ Should be ZERO functional singleton calls in business logic"
```

### 7.2 Success Metrics

**Required Achievements [ALL MANDATORY]**:
- **Zero functional singleton calls**: No business logic uses singletons
- **CLI functionality preserved**: All commands work identically
- **Generation workflows preserved**: Template generation still works
- **UI theming preserved**: Styling and themes still apply
- **Test coverage maintained**: All tests pass

### 7.3 Final Test Commands

```bash
# Run complete test suite
poetry run pytest tests/unit/ -v

# Test CLI end-to-end
cd /tmp && mkdir test_final && cd test_final
python -m spec_cli init
echo "test" > test.txt
python -m spec_cli add .specs/test.md
python -m spec_cli commit -m "test"
python -m spec_cli log

# Should complete without singleton-related errors
echo "🎉 SINGLETON MIGRATION 100% COMPLETE!"
```

---

## Success Metrics [MIGRATION COMPLETE]

### Final State Verification
- **Functional singletons eliminated**: 0/0 remaining
- **CLI commands working**: All preserved
- **Generation workflows working**: All preserved  
- **UI components working**: All preserved
- **Test coverage**: 100% pass rate

### Completion Checklist
- [ ] CLI utilities accept settings parameters
- [ ] Core context uses direct instantiation
- [ ] UI theme requires settings parameter
- [ ] Context bridge uses original implementations
- [ ] All callers updated to pass dependencies
- [ ] All tests passing
- [ ] CLI commands work end-to-end
- [ ] Zero functional singleton calls remaining

**Final singleton migration eliminates the last 11 singleton calls through systematic dependency injection while preserving 100% of application functionality.**