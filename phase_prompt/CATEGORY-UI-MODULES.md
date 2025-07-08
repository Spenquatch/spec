# UI Modules Agent Directive: Console Singleton Elimination

You are executing **UI module singleton migration** which systematically replaces `get_console()` calls with dependency injection in UI components. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **UI console access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Console Singletons in UI Layer

**GOAL**: Replace all 17 `get_console()` calls across 7 UI module files with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero `get_console()` calls remaining in UI modules
- All UI components accept console via constructor/parameter
- 100% test pass rate maintained
- UI rendering functionality preserved

**TARGET FILES**:
- `spec_cli/ui/error_display.py` (8 calls) - **HIGHEST PRIORITY**
- `spec_cli/ui/progress_manager.py` (2 calls) 
- `spec_cli/ui/spinner.py` (2 calls)
- `spec_cli/ui/tables.py` (1 call)
- `spec_cli/ui/progress_bar.py` (1 call)
- `spec_cli/ui/console.py` (1 call)
- `spec_cli/ui/theme.py` (1 call)

---

## 🚨 UI MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break rich console rendering** → UI components must maintain visual fidelity
2. **NEVER modify console interface contracts** → Preserve existing console API usage
3. **NEVER inject console into static methods** → Convert to instance methods first
4. **NEVER break progress/spinner lifecycle** → Stateful widgets require careful handling
5. **NEVER proceed without testing each file** → Validate UI rendering after each change

> **UI Principle: "Dependency injection with preserved rendering behavior"**

---

## Step 1: High-Priority File Migration [START HERE]

### 1.1 Error Display Migration [CRITICAL - 8 CALLS]

**File**: `spec_cli/ui/error_display.py`

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ..ui.console import get_console

class ErrorDisplay:
    def __init__(self):
        self.console = get_console().console  # SINGLETON CALL
    
    def show_error(self, message):
        self.console = get_console().console  # REPEATED CALLS
```

**Target Pattern**:
```python
# Dependency injection pattern
from rich.console import Console

class ErrorDisplay:
    def __init__(self, console: Console = None):
        self.console = console
        if self.console is None:
            raise ValueError("Console must be provided")
    
    def show_error(self, message):
        # Use self.console directly - no singleton calls
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/ui/error_display.py spec_cli/ui/error_display.py.backup

# 2. Find all get_console() calls in error_display.py
grep -n "get_console()" spec_cli/ui/error_display.py

# 3. Identify class constructors and methods that need modification
grep -n "class\|def " spec_cli/ui/error_display.py
```

**Transformation Steps**:

1. **Remove singleton import**:
   ```python
   # REMOVE
   from ..ui.console import get_console
   
   # ADD (if not present)
   from rich.console import Console
   ```

2. **Modify class constructor**:
   ```python
   # BEFORE
   def __init__(self):
       self.console = console or get_console().console
   
   # AFTER  
   def __init__(self, console: Console = None):
       if console is None:
           raise ValueError("ErrorDisplay requires a console instance")
       self.console = console
   ```

3. **Remove all get_console() calls in methods**:
   ```python
   # BEFORE
   def show_validation_error(self, message):
       console = console or get_console().console
       
   # AFTER
   def show_validation_error(self, message):
       # Use self.console directly
   ```

4. **Update caller sites** (trace backwards from error_display.py usage):
   ```bash
   # Find all files that instantiate ErrorDisplay
   grep -r "ErrorDisplay()" spec_cli/
   
   # Each caller must now pass console:
   # BEFORE: ErrorDisplay()
   # AFTER:  ErrorDisplay(console)
   ```

### 1.2 Progress Manager Migration [STATEFUL - 2 CALLS]

**File**: `spec_cli/ui/progress_manager.py`

**Critical Consideration**: Progress managers are stateful rich widgets that manage terminal state.

**Current Pattern**:
```python
class ProgressManager:
    def start_progress(self):
        console = get_console()  # SINGLETON
        self.progress = Progress(console=console.console)
```

**Target Pattern**:
```python
class ProgressManager:
    def __init__(self, console: Console):
        self.console = console
    
    def start_progress(self):
        self.progress = Progress(console=self.console)
```

**Migration Commands**:
```bash
# Analyze current progress manager implementation
grep -n -A5 -B5 "get_console" spec_cli/ui/progress_manager.py

# Find all ProgressManager instantiations
grep -r "ProgressManager(" spec_cli/
```

### 1.3 Spinner Migration [STATEFUL - 2 CALLS]

**File**: `spec_cli/ui/spinner.py`

**Similar to progress manager - stateful rich component requiring careful console lifecycle management.**

```python
# Target pattern for spinner
class Spinner:
    def __init__(self, console: Console):
        self.console = console
    
    def start(self, message: str):
        self.status = self.console.status(message)
        self.status.start()
```

---

## Step 2: Simple UI Component Migration

### 2.1 Tables, Progress Bar, Theme Migration [1 CALL EACH]

**Files**: 
- `spec_cli/ui/tables.py` (1 call)
- `spec_cli/ui/progress_bar.py` (1 call)  
- `spec_cli/ui/theme.py` (1 call)

**Simple Pattern**:
```python
# BEFORE
def render_table(data):
    console = get_console().console
    
# AFTER
def render_table(data, console: Console):
    # Use console parameter directly
```

**Batch Migration Commands**:
```bash
# Process each simple file
for file in tables.py progress_bar.py theme.py; do
    echo "Processing spec_cli/ui/$file"
    
    # Find singleton calls
    grep -n "get_console" "spec_cli/ui/$file"
    
    # Apply transformation pattern
    # 1. Remove singleton import
    # 2. Add console parameter to functions
    # 3. Update callers
done
```

---

## Step 3: Console Module Self-Reference [SPECIAL CASE]

### 3.1 Console.py Internal Cleanup

**File**: `spec_cli/ui/console.py` (1 call)

**Issue**: The console module itself contains a `get_console()` call - likely in its own factory method.

**Analysis Commands**:
```bash
# Examine the console module structure
grep -n -A10 -B10 "get_console" spec_cli/ui/console.py

# Understand the console factory pattern
grep -n "class\|def " spec_cli/ui/console.py
```

**Likely Pattern**:
```python
# Current internal recursion
def get_console():
    if not hasattr(_console_cache, 'instance'):
        _console_cache.instance = ConsoleManager().get_console()  # RECURSIVE
    return _console_cache.instance
```

**Resolution**: Remove internal recursion, implement proper singleton if needed, or eliminate the pattern entirely.

---

## Step 4: Caller Site Updates [DEPENDENCY PLUMBING]

### 4.1 Trace UI Component Usage

**Critical**: After modifying UI classes to require console injection, ALL instantiation sites must be updated.

**Discovery Commands**:
```bash
# Find all UI component instantiations
grep -r "ErrorDisplay(" spec_cli/
grep -r "ProgressManager(" spec_cli/
grep -r "Spinner(" spec_cli/

# Trace back to CLI command entry points
grep -r "from.*ui.*import" spec_cli/cli/
```

### 4.2 CLI Command Integration

**Pattern**: CLI commands typically have access to console through click context or application setup.

**Typical Integration**:
```python
# In CLI command file
@click.command()
@click.pass_context
def some_command(ctx):
    console = ctx.obj.console  # Or however console is accessed
    
    # BEFORE
    error_display = ErrorDisplay()
    
    # AFTER
    error_display = ErrorDisplay(console)
```

**Integration Commands**:
```bash
# Find CLI context patterns
grep -r "click.pass_context\|ctx.obj" spec_cli/cli/

# Find console access in CLI
grep -r "console.*=" spec_cli/cli/
```

---

## Step 5: Validation & Testing [MANDATORY]

### 5.1 Syntax and Import Validation

```bash
# Validate syntax for all modified UI files
python -c "
import py_compile
import glob

ui_files = glob.glob('spec_cli/ui/*.py')
for file in ui_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.ui.error_display
import spec_cli.ui.progress_manager
import spec_cli.ui.spinner
print('✅ All UI imports successful')
"
```

### 5.2 UI Rendering Tests

```bash
# Run UI-specific tests
poetry run pytest tests/unit/ui/ -v

# Run integration tests that use UI components
poetry run pytest tests/ -k "ui" -v

# Verify no get_console() calls remain in UI modules
find spec_cli/ui -name "*.py" | xargs grep "get_console()" && echo "❌ Still has singleton calls" || echo "✅ No singleton calls found"
```

### 5.3 Manual UI Verification

**Test Script**:
```python
# test_ui_injection.py
from rich.console import Console
from spec_cli.ui.error_display import ErrorDisplay
from spec_cli.ui.progress_manager import ProgressManager
from spec_cli.ui.spinner import Spinner

# Test dependency injection works
console = Console()

try:
    error_display = ErrorDisplay(console)
    progress_manager = ProgressManager(console)
    spinner = Spinner(console)
    print("✅ All UI components accept console injection")
except Exception as e:
    print(f"❌ UI injection failed: {e}")
    exit(1)
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Import Errors After Migration
```bash
# If imports fail, check for missing console parameters
grep -r "ErrorDisplay()" spec_cli/ | grep -v "console"
# Each should be: ErrorDisplay(console)
```

### Rich Console Widget Issues
```bash
# If progress/spinner widgets behave incorrectly:
# 1. Verify console is a rich.Console instance
# 2. Check widget lifecycle (start/stop) isn't broken
# 3. Ensure no double-wrapping of console objects
```

### Caller Site Mismatches
```bash
# If callers don't have console access:
# 1. Trace up to CLI command entry point
# 2. Pass console down through intermediate functions
# 3. Consider adding console to application context
```

---

## Success Metrics [UI MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_console()` remaining in UI modules
- **Constructor injection**: All UI classes accept console via __init__
- **Preserved functionality**: UI rendering works identically to before
- **Test coverage**: All UI tests pass, no regressions
- **Clean imports**: No hanging singleton import statements

### Validation Commands
```bash
# Final validation
find spec_cli/ui -name "*.py" | xargs grep -n "get_console" || echo "✅ UI migration complete"
poetry run pytest tests/unit/ui/ -v
python -c "from spec_cli.ui.error_display import ErrorDisplay; from rich.console import Console; ErrorDisplay(Console())"
```

**UI module migration eliminates 17 singleton calls through systematic dependency injection while preserving all rich console rendering capabilities.**