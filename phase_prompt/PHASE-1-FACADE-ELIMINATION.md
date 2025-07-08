# Phase 1: Facade Elimination Agent Directive

This protocol governs the systematic elimination of singleton facade functions from the context bridge. Every instruction here is mandatory. Execution must follow the exact sequence, enforce all quality gates, and respect strict complexity, security, and scope boundaries.

You will not skip steps, alter scope, or improvise beyond the facade elimination definition.

> **If a step fails: fix it. If a rule is unclear: escalate. If facades remain: it's incomplete.**

---

## **[P0-ABSOLUTE]** EXECUTION RULES

*These rules override everything else. Violating any rule makes the implementation invalid.*

1. **NEVER break CLI functionality** → All commands must continue working identically
2. **NEVER skip deprecation warnings** → All facade calls must be warned before elimination
3. **NEVER leave orphaned callers** → All facade usage must be migrated to dependency injection
4. **NEVER compromise backward compatibility** → Migration must be gradual and safe
5. **NEVER exceed McCabe complexity ≤ 7** → Each function max 7 decision points
6. **NEVER modify unrelated code** → Focus only on facade elimination and caller migration

> **"Facades eliminated OR not touched - no partial states exist"**

---

## 1. Mission: Eliminate Singleton Facades

### **TARGET FACADES (2 calls)**
- `spec_cli/core/context_bridge.py:123` - `get_console()` facade function
- `spec_cli/core/context_bridge.py:160` - `get_settings()` facade function

### **SUCCESS CRITERIA**
- Zero facade function calls remaining in business logic
- All facade callers migrated to dependency injection
- CLI functionality completely preserved
- All tests passing

---

## 2. Pre-Implementation Checklist

### Before Writing Any Code
```bash
# 1. Establish baseline - ALL tests must pass
poetry run pytest tests/unit/ -v

# 2. Identify all facade callers
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import"

# 3. Verify context injection is working
python -c "from spec_cli.cli.decorators import context_injection; print('✅ Context injection available')"

# 4. Check current CLI functionality
python -m spec_cli --help | head -5

# 5. Verify cross-platform compatibility
python scripts/check_platform_compatibility.py
```

**If ANY baseline check fails:** Stop and escalate - do not proceed with broken foundation.

---

## 3. Implementation Workflow **[MANDATORY SEQUENCE]**

### **WEEK 1-2: DEPRECATION WARNINGS**

#### Step 1: Add Deprecation Infrastructure
```python
# Add to spec_cli/core/context_bridge.py
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.settings import SpecSettings
    from ..ui.console import Console

def get_console() -> "Console":
    """Get console instance - DEPRECATED.
    
    DEPRECATED: This function is deprecated and will be removed in a future version.
    Use dependency injection instead:
    
    Example:
        # OLD (deprecated)
        console = get_console()
        
        # NEW (recommended)
        @click.command()
        @click.pass_context
        def my_command(ctx):
            console = ctx.obj.console
            
        # OR in functions that accept console parameter
        def my_function(console: Console):
            # Use console parameter
    
    Returns:
        Console instance
    """
    warnings.warn(
        "get_console() is deprecated and will be removed in a future version. "
        "Use dependency injection instead. "
        "Pass console as parameter or get from Click context (ctx.obj.console).",
        DeprecationWarning,
        stacklevel=2
    )
    return _original_get_console()

def get_settings() -> "SpecSettings":
    """Get settings instance - DEPRECATED.
    
    DEPRECATED: This function is deprecated and will be removed in a future version.
    Use dependency injection instead:
    
    Example:
        # OLD (deprecated)
        settings = get_settings()
        
        # NEW (recommended)
        @click.command()
        @click.pass_context
        def my_command(ctx):
            settings = ctx.obj.settings
            
        # OR in functions that accept settings parameter
        def my_function(settings: SpecSettings):
            # Use settings parameter
    
    Returns:
        SpecSettings instance
    """
    warnings.warn(
        "get_settings() is deprecated and will be removed in a future version. "
        "Use dependency injection instead. "
        "Pass settings as parameter or get from Click context (ctx.obj.settings).",
        DeprecationWarning,
        stacklevel=2
    )
    return _original_get_settings()
```

#### Step 2: Validate Deprecation Warnings
```bash
# Test deprecation warnings work
python -c "
import warnings
warnings.simplefilter('always')
from spec_cli.core.context_bridge import get_console, get_settings
try:
    get_console()
    get_settings()
except:
    pass
print('✅ Deprecation warnings active')
"
```

### **WEEK 3-4: CALLER MIGRATION**

#### Step 3: Discover All Facade Callers
```bash
# Create comprehensive caller audit
echo "=== FACADE CALLER AUDIT ===" > facade_callers.txt
echo "Date: $(date)" >> facade_callers.txt
echo "" >> facade_callers.txt

echo "get_console() callers:" >> facade_callers.txt
find spec_cli -name "*.py" | xargs grep -n "get_console()" | grep -v "def get_console" | grep -v "from.*import" >> facade_callers.txt

echo "" >> facade_callers.txt
echo "get_settings() callers:" >> facade_callers.txt
find spec_cli -name "*.py" | xargs grep -n "get_settings()" | grep -v "def get_settings" | grep -v "from.*import" >> facade_callers.txt

echo "" >> facade_callers.txt
echo "TOTAL CALLERS TO MIGRATE: $(find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | wc -l)" >> facade_callers.txt

cat facade_callers.txt
```

#### Step 4: Migrate Each Caller Systematically

**For each caller in facade_callers.txt:**

**Pattern 1: CLI Commands with Context Injection**
```python
# BEFORE: Using facade
def some_command(ctx):
    console = get_console()
    settings = get_settings()
    
# AFTER: Using dependency injection
@click.command()
@click.pass_context
def some_command(ctx):
    console = ctx.obj.console
    settings = ctx.obj.settings
```

**Pattern 2: Functions with Available Context**
```python
# BEFORE: Using facade
def some_function(param):
    settings = get_settings()
    console = get_console()
    
# AFTER: Accept as parameters
def some_function(param, settings: SpecSettings, console: Console):
    # Use parameters directly
```

**Pattern 3: Classes with Dependency Injection**
```python
# BEFORE: Using facade in class
class SomeClass:
    def __init__(self):
        self.settings = get_settings()
        
# AFTER: Constructor injection
class SomeClass:
    def __init__(self, settings: SpecSettings):
        self.settings = settings
```

#### Step 5: Update All Callers
```bash
# For each file with facade calls:
# 1. Read the file
# 2. Identify the facade usage pattern
# 3. Apply appropriate migration pattern
# 4. Test the specific functionality
# 5. Verify no regressions

# Example migration command per file:
# Replace facade calls with dependency injection
```

### **WEEK 5: FACADE REMOVAL**

#### Step 6: Verify Zero Facade Callers
```bash
# Comprehensive caller check
REMAINING_CALLERS=$(find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings" | wc -l)

echo "Remaining facade callers: $REMAINING_CALLERS"

if [ "$REMAINING_CALLERS" -ne 0 ]; then
    echo "❌ MIGRATION INCOMPLETE - Still have facade callers:"
    find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings"
    exit 1
else
    echo "✅ All facade callers migrated"
fi
```

#### Step 7: Remove Facade Functions
```python
# Remove from spec_cli/core/context_bridge.py
# DELETE these functions entirely:
# - get_console()
# - get_settings()

# Keep only the original implementations:
# - _original_get_console()
# - _original_get_settings()
```

#### Step 8: Update Import Statements
```bash
# Find and update all imports
find spec_cli -name "*.py" | xargs grep -l "from.*context_bridge import.*get_console\|from.*context_bridge import.*get_settings" | while read file; do
    echo "Updating imports in: $file"
    # Remove get_console and get_settings from imports
    # Update code to use dependency injection
done
```

---

## 4. Quality Gates **[STRICT ENFORCEMENT]**

### Functional Testing
```bash
# CLI functionality must be preserved
python -m spec_cli --help
python -m spec_cli init --help
python -m spec_cli status --help
python -m spec_cli gen --help

# Test specific commands if possible
cd /tmp && mkdir test_phase1 && cd test_phase1
python -m spec_cli init
echo "test content" > test.txt
python -m spec_cli status
cd .. && rm -rf test_phase1
```

### Unit Testing
```bash
# All existing tests must pass
poetry run pytest tests/unit/ -v

# No deprecation warnings in tests
poetry run pytest tests/unit/ -v -W error::DeprecationWarning
```

### Code Quality
```bash
# Standard quality gates
poetry run ruff check spec_cli/ tests/ --output-format=full
poetry run ruff format spec_cli/ tests/
poetry run mypy spec_cli/
poetry run check-all
```

### Integration Validation
```bash
# Verify CLI integration works
python -c "
from spec_cli.cli.app import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli, ['--help'])
assert result.exit_code == 0
print('✅ CLI integration works')
"
```

---

## 5. Completion Checklist

### Before Marking Phase Complete
```bash
# MANDATORY VERIFICATION
- [ ] Zero facade function calls in business logic
- [ ] All facade callers migrated to dependency injection
- [ ] CLI commands work identically to before
- [ ] All unit tests pass
- [ ] No deprecation warnings in test suite
- [ ] Quality gates pass
- [ ] Integration tests validate
- [ ] Git commit follows conventional format
- [ ] Performance requirements met
- [ ] Cross-platform compatibility verified
```

### Success Confirmation
**Phase 1 is complete when:**
- `find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings"` returns zero results
- `poetry run check-all` passes without warnings
- `python -m spec_cli --help` works correctly
- All CLI commands function identically to before migration
- No facade functions remain in `spec_cli/core/context_bridge.py`

---

## 6. Error Handling Protocol

### When Migration Fails
```bash
# 1. Identify the failing caller
grep -n "get_console()\|get_settings()" [failing_file]

# 2. Determine the appropriate migration pattern
# - CLI command: Use ctx.obj.console, ctx.obj.settings
# - Function: Add parameters
# - Class: Constructor injection

# 3. Apply the migration pattern
# 4. Test the specific functionality
# 5. Verify no regressions
```

### Escalation Report Format
```
PHASE 1 FACADE ELIMINATION FAILURE REPORT
Failed Step: [step_number_and_name]
Failing File: [file_with_facade_calls]
Facade Usage Pattern: [describe_how_facade_is_used]
Error Output: [full_error_message]
Migration Attempted: [describe_what_was_tried]
Environment: Python [version], Poetry [version]
Platform: [OS and version]
CLI Test Results: [output of python -m spec_cli --help]
```

---

## 7. Concurrent Execution Notes

### **SAFE TO RUN CONCURRENTLY WITH:**
- **Phase 2 (Factory Modernization)** - Different files, no conflicts
- **Phase 3 (Architectural Validation)** - Can prepare validation while migration in progress

### **CONFLICTS WITH:**
- None - This phase is isolated to context_bridge.py and its callers

### **PREREQUISITES:**
- All 11 HIGH PRIORITY singleton calls must be eliminated (completed)
- Context injection decorator must be functional
- CLI infrastructure must be stable

---

## Quick Reference Commands

```bash
# Phase 1 workflow
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings" | wc -l

# Test CLI functionality
python -m spec_cli --help && python -m spec_cli init --help && python -m spec_cli status --help

# Quality validation
poetry run pytest tests/unit/ -v && poetry run check-all

# Success verification
echo "Facade elimination complete: $(find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings" | wc -l) calls remaining"
```

---

*Remember: This phase eliminates backward compatibility facades and forces explicit dependency management. Every facade call must be migrated to dependency injection. CLI functionality must remain identical throughout the migration process.*