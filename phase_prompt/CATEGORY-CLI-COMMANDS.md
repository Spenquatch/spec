# CLI Commands Agent Directive: Console Singleton Elimination

You are executing **CLI command singleton migration** which systematically replaces `get_console()` calls with dependency injection in command implementations. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **CLI console access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Console Singletons in CLI Commands

**GOAL**: Replace all 13 `get_console()` calls across 8 CLI command files with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero `get_console()` calls remaining in CLI command modules
- All CLI commands receive console via Click context or parameters
- 100% test pass rate maintained
- CLI output functionality preserved

**TARGET FILES**:
- `spec_cli/cli/commands/history/formatters.py` (3 calls) - **OUTPUT FORMATTING**
- `spec_cli/cli/commands/generation/prompts.py` (3 calls) - **PROMPT DISPLAY**
- `spec_cli/cli/commands/generation/workflows.py` (2 calls) - **WORKFLOW OUTPUT**
- `spec_cli/cli/commands/history/diff_viewer.py` (1 call) - **DIFF DISPLAY**
- `spec_cli/cli/commands/history/content_viewer.py` (1 call) - **CONTENT VIEW**
- `spec_cli/cli/commands/gen_command.py` (1 call) - **GENERATION CMD**
- `spec_cli/cli/commands/diff.py` (1 call) - **DIFF CMD**
- `spec_cli/cli/commands/add_command.py` (1 call) - **ADD CMD**
- `spec_cli/cli/app.py` (1 call) - **APP LEVEL**
- `spec_cli/cli/decorators.py` (1 call) - **DECORATOR UTILS**

---

## 🚨 CLI MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break Click command interfaces** → Preserve existing command signatures and options
2. **NEVER modify Click context contracts** → Use standard Click patterns for dependency access
3. **NEVER break command output formatting** → CLI output must remain visually identical
4. **NEVER inject console into Click decorators incorrectly** → Follow Click's dependency injection patterns
5. **NEVER proceed without testing each command** → Validate CLI behavior after each change

> **CLI Principle: "Click context dependency injection with preserved command behavior"**

---

## Step 1: High-Volume Command Migration [START HERE]

### 1.1 History Formatters Migration [CRITICAL - 3 CALLS]

**File**: `spec_cli/cli/commands/history/formatters.py`

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ....ui.console import get_console

def format_commit_history(commits):
    console = get_console().console  # SINGLETON CALL
    for commit in commits:
        console.print(f"[green]{commit.hash}[/green] {commit.message}")
```

**Target Pattern**:
```python
# Click context injection pattern
from rich.console import Console

def format_commit_history(commits, console: Console):
    for commit in commits:
        console.print(f"[green]{commit.hash}[/green] {commit.message}")
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/cli/commands/history/formatters.py spec_cli/cli/commands/history/formatters.py.backup

# 2. Find all get_console() calls
grep -n "get_console()" spec_cli/cli/commands/history/formatters.py

# 3. Identify function signatures that need console parameter
grep -n "def " spec_cli/cli/commands/history/formatters.py
```

**Transformation Steps**:

1. **Remove singleton import**:
   ```python
   # REMOVE
   from ....ui.console import get_console
   
   # ADD (if not present)
   from rich.console import Console
   ```

2. **Add console parameters to functions**:
   ```python
   # BEFORE
   def format_commit_history(commits):
       console = get_console().console
   
   # AFTER  
   def format_commit_history(commits, console: Console):
       # Use console parameter directly
   ```

3. **Update caller sites** (find where formatters are called):
   ```bash
   # Find all calls to formatter functions
   grep -r "format_commit_history\|format_" spec_cli/cli/commands/
   
   # Each caller must now pass console:
   # BEFORE: format_commit_history(commits)
   # AFTER:  format_commit_history(commits, console)
   ```

### 1.2 Generation Prompts Migration [CRITICAL - 3 CALLS]

**File**: `spec_cli/cli/commands/generation/prompts.py`

**Current Pattern**:
```python
def display_generation_prompt(prompt_text):
    console = get_console()  # SINGLETON
    console.print_rich_text(prompt_text)
```

**Target Pattern**:
```python
def display_generation_prompt(prompt_text, console: Console):
    console.print_rich_text(prompt_text)
```

**Migration Commands**:
```bash
# Analyze generation prompts implementation
grep -n -A3 -B3 "get_console" spec_cli/cli/commands/generation/prompts.py

# Find all prompt display function calls
grep -r "display.*prompt\|show.*prompt" spec_cli/cli/commands/
```

### 1.3 Generation Workflows Migration [WORKFLOW - 2 CALLS]

**File**: `spec_cli/cli/commands/generation/workflows.py`

**Critical Consideration**: Workflows may have complex output patterns and progress tracking.

**Analysis Commands**:
```bash
# Examine workflow console usage patterns
grep -n -A5 -B5 "get_console" spec_cli/cli/commands/generation/workflows.py

# Check for progress tracking or complex output
grep -n "progress\|status\|workflow" spec_cli/cli/commands/generation/workflows.py
```

---

## Step 2: Click Command Integration [CONTEXT PLUMBING]

### 2.1 Click Context Setup

**Critical Pattern**: CLI commands need console access through Click context.

**Current Click Setup Analysis**:
```bash
# Find how console is currently set up in Click context
grep -r "click.pass_context\|ctx.obj" spec_cli/cli/

# Find console initialization in CLI app
grep -n -A10 -B10 "console" spec_cli/cli/app.py
```

**Target Click Pattern**:
```python
# In CLI command
@click.command()
@click.pass_context
def history_command(ctx):
    console = ctx.obj.console  # Get console from context
    
    # Pass console to functions that need it
    format_commit_history(commits, console)
```

**Context Setup Commands**:
```bash
# Check if console is already in Click context
grep -n "ctx.obj.*console\|obj.*console" spec_cli/cli/

# If not present, find where ctx.obj is initialized
grep -n "ctx.obj\s*=" spec_cli/cli/
```

### 2.2 Application-Level Console Setup

**File**: `spec_cli/cli/app.py` (1 call)

**Analysis**:
```bash
# Examine app-level console usage
grep -n -A10 -B10 "get_console" spec_cli/cli/app.py

# Check Click application setup
grep -n "click.group\|@click" spec_cli/cli/app.py
```

**Typical Pattern**:
```python
# App level setup
@click.group()
@click.pass_context
def cli(ctx):
    # Ensure console is available in context
    if ctx.obj is None:
        ctx.obj = {}
    
    # Initialize console once at app level
    from rich.console import Console
    ctx.obj['console'] = Console()
```

---

## Step 3: Utility and Decorator Migration

### 3.1 CLI Decorators Migration [DECORATOR UTILS - 1 CALL]

**File**: `spec_cli/cli/decorators.py`

**Special Consideration**: Decorators may need to access console for logging or output.

**Analysis Commands**:
```bash
# Examine decorator console usage
grep -n -A10 -B10 "get_console" spec_cli/cli/decorators.py

# Understand decorator structure
grep -n "def \|@\|decorator" spec_cli/cli/decorators.py
```

**Decorator Pattern Options**:
```python
# OPTION 1: Decorator accesses console from Click context
def some_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        console = ctx.obj.console
        # Use console for decorator logic
        return func(*args, **kwargs)
    return wrapper

# OPTION 2: Pass console through decorator factory
def some_decorator(console: Console):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use console parameter
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Step 4: Command-Specific Migrations

### 4.1 Individual Command Files [1 CALL EACH]

**Files**:
- `spec_cli/cli/commands/history/diff_viewer.py` (1 call)
- `spec_cli/cli/commands/history/content_viewer.py` (1 call)
- `spec_cli/cli/commands/gen_command.py` (1 call)
- `spec_cli/cli/commands/diff.py` (1 call)
- `spec_cli/cli/commands/add_command.py` (1 call)

**Batch Migration Pattern**:
```bash
# Process each command file
for file in diff_viewer.py content_viewer.py gen_command.py diff.py add_command.py; do
    echo "Processing CLI command: $file"
    
    # Find singleton calls
    find spec_cli/cli/commands -name "$file" | xargs grep -n "get_console"
    
    # Apply transformation pattern
    # 1. Remove singleton import
    # 2. Access console from Click context
    # 3. Pass console to helper functions
done
```

**Standard Command Pattern**:
```python
# BEFORE
@click.command()
def some_command():
    console = get_console()
    console.print("Command output")

# AFTER
@click.command()
@click.pass_context
def some_command(ctx):
    console = ctx.obj.console
    console.print("Command output")
```

### 4.2 Complex Command Migration

**For commands with helper functions**:
```python
# BEFORE
@click.command()
def complex_command():
    result = helper_function()
    
def helper_function():
    console = get_console()  # SINGLETON
    console.print("Helper output")

# AFTER
@click.command()
@click.pass_context
def complex_command(ctx):
    console = ctx.obj.console
    result = helper_function(console)
    
def helper_function(console: Console):
    console.print("Helper output")
```

---

## Step 5: Context Integration Verification

### 5.1 Console Context Setup Validation

**Ensure console is available in Click context**:
```python
# test_console_context.py
import click
from spec_cli.cli.app import cli

def test_console_in_context():
    runner = click.testing.CliRunner()
    
    @click.command()
    @click.pass_context
    def test_cmd(ctx):
        console = ctx.obj.console
        console.print("Test output")
    
    # Test that console is accessible
    result = runner.invoke(test_cmd)
    assert "Test output" in result.output
```

### 5.2 Command Chain Validation

**Test that console flows through command chain**:
```bash
# Create test script
cat > test_cli_console_flow.py << 'EOF'
from click.testing import CliRunner
from spec_cli.cli.app import cli
from spec_cli.cli.commands.history.formatters import format_commit_history

def test_console_flow():
    runner = CliRunner()
    
    # Test that commands can access console and pass to helpers
    result = runner.invoke(cli, ['log'])  # Or appropriate command
    
    # Should not crash with missing console
    assert result.exit_code == 0
    print("✅ Console flows correctly through CLI")

if __name__ == "__main__":
    test_console_flow()
EOF

python test_cli_console_flow.py
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Syntax and Import Validation

```bash
# Validate syntax for all modified CLI files
python -c "
import py_compile
import glob

cli_files = glob.glob('spec_cli/cli/commands/**/*.py', recursive=True)
cli_files.extend(glob.glob('spec_cli/cli/*.py'))

for file in cli_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.cli.commands.history.formatters
import spec_cli.cli.commands.generation.prompts
import spec_cli.cli.app
print('✅ All CLI imports successful')
"
```

### 6.2 CLI Command Testing

```bash
# Run CLI-specific tests
poetry run pytest tests/unit/cli/ -v

# Test individual commands
poetry run pytest tests/ -k "command" -v

# Verify no get_console() calls remain in CLI modules
find spec_cli/cli -name "*.py" | xargs grep "get_console()" && echo "❌ Still has singleton calls" || echo "✅ No singleton calls found"
```

### 6.3 Interactive CLI Testing

**Manual Command Verification**:
```bash
# Test actual CLI commands work
python -m spec_cli --help
python -m spec_cli log
python -m spec_cli status
python -m spec_cli diff

# Each should work without console errors
```

**Click Context Testing**:
```python
# test_click_context.py
from click.testing import CliRunner
from spec_cli.cli.app import cli

def test_all_commands_have_console():
    runner = CliRunner()
    
    # Test major commands
    commands = ['init', 'add', 'commit', 'log', 'status', 'diff']
    
    for cmd in commands:
        try:
            result = runner.invoke(cli, [cmd, '--help'])
            assert result.exit_code == 0
            print(f"✅ {cmd}: Command accessible")
        except Exception as e:
            print(f"❌ {cmd}: {e}")

if __name__ == "__main__":
    test_all_commands_have_console()
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Click Context Missing Console
```bash
# If ctx.obj.console doesn't exist:
# 1. Check CLI app setup in spec_cli/cli/app.py
# 2. Ensure console is initialized in main group
# 3. Verify ctx.obj is not None before accessing console
```

### Command Parameter Mismatches
```bash
# If functions need console parameter but callers don't provide:
grep -r "format_commit_history(" spec_cli/ | grep -v "console"
# Each caller should pass console parameter
```

### Import Circular Dependencies
```bash
# If CLI imports create circles:
# 1. Check import structure with:
python -c "
import ast, glob
for file in glob.glob('spec_cli/cli/**/*.py', recursive=True):
    print(f'=== {file} ===')
    with open(file) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and 'cli' in str(node.module):
            print(f'  imports: {node.module}')
"
```

### Click Decorator Issues
```bash
# If decorators break Click commands:
# 1. Ensure decorators preserve function signatures
# 2. Use @functools.wraps correctly
# 3. Test Click context access in decorators
```

---

## Success Metrics [CLI MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_console()` remaining in CLI modules
- **Click context integration**: Console accessible via ctx.obj.console
- **Preserved functionality**: All CLI commands work identically to before
- **Test coverage**: All CLI tests pass, no regressions
- **Clean imports**: No hanging singleton import statements

### Validation Commands
```bash
# Final validation
find spec_cli/cli -name "*.py" | xargs grep -n "get_console" || echo "✅ CLI migration complete"
poetry run pytest tests/unit/cli/ -v
python -m spec_cli --help
python test_click_context.py
```

### End-to-End CLI Test
```bash
# Test complete CLI workflow
cd /tmp
mkdir test_spec_cli
cd test_spec_cli

# Test CLI commands work end-to-end
python -m spec_cli init
echo "Test content" > test.md
python -m spec_cli add .specs/test.md
python -m spec_cli commit -m "Test commit"
python -m spec_cli log
python -m spec_cli status

# Should complete without console errors
echo "✅ CLI end-to-end test passed"
```

**CLI command migration eliminates 13 singleton calls through Click context dependency injection while preserving all command functionality and output formatting.**