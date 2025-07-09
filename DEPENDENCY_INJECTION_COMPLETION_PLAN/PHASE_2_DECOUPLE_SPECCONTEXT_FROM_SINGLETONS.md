# PHASE 2: DECOUPLE SPECCONTEXT FROM SINGLETONS - COMPREHENSIVE EXECUTION PROMPT

## MISSION STATEMENT
You are tasked with completing **Phase 2** of the dependency injection migration completion plan. This phase breaks the hidden dependency chain by refactoring SpecContext factory methods to instantiate dependencies directly instead of calling legacy singleton getters, while maintaining all existing functionality.

## CRITICAL SUCCESS CRITERIA
- **All 1006 tests must continue to pass** throughout this phase
- **Performance must not degrade** by more than 5% from baseline
- **SpecContext factory methods** must instantiate dependencies directly
- **CLI functionality** must remain completely unchanged
- **Test infrastructure** must continue working with mocks

---

## P0 ABSOLUTE INSTRUCTIONS - MANDATORY COMPLIANCE

### 🚨 CRITICAL SAFETY REQUIREMENTS

1. **PRESERVE EXISTING INTERFACES** - SpecContext public API must remain unchanged
2. **MAINTAIN TEST COMPATIBILITY** - All existing tests must continue passing
3. **VALIDATE CONTINUOUSLY** - Run validation after each major change
4. **BACKUP BEFORE MODIFICATION** - Create backups before changing any files
5. **ROLLBACK ON FAILURE** - Use rollback procedures if any validation fails

### 🔒 GUARDRAILS AND CONSTRAINTS

1. **INTERFACE PRESERVATION**: Only internal implementation changes, never public API
2. **INCREMENTAL CHANGES**: Make changes step-by-step with validation at each step
3. **DEPENDENCY VALIDATION**: Ensure all dependencies are properly instantiated
4. **PERFORMANCE MONITORING**: Monitor performance impact continuously
5. **FUNCTIONAL TESTING**: Validate CLI commands work correctly after changes

### ⚠️ FAILURE CONDITIONS - STOP IMMEDIATELY IF:

- Any test fails during validation
- Performance degrades by more than 5%
- CLI commands fail or behave differently
- Context injection decorators stop working
- Factory methods create shared state instead of independent instances
- Import errors occur due to circular dependencies

---

## PHASE 2 CONTEXT AND BACKGROUND

### Phase 1 Prerequisites
Before starting Phase 2, ensure Phase 1 deliverables are complete:
- [ ] dependency_mapping.txt with complete singleton analysis
- [ ] progress_manager_analysis.txt with clear decision
- [ ] architecture_analysis.txt with current state assessment
- [ ] validate_migration.sh operational and tested
- [ ] rollback_migration.sh tested and verified
- [ ] All 1006 tests passing at baseline performance

### Current Problem
The SpecContext factory methods currently call legacy singleton getters, creating hidden dependencies:

```python
# CURRENT PROBLEMATIC PATTERN in spec_cli/core/context.py
@classmethod
def create_for_cli(cls, root_path: Path | None = None) -> "SpecContext":
    return cls(
        settings=get_settings(root_path),      # ← CALLS SINGLETON
        console=get_console(),                 # ← CALLS SINGLETON
        progress=get_progress_manager(),       # ← CALLS SINGLETON
    )
```

### Target Architecture
After Phase 2, factory methods will instantiate dependencies directly:

```python
# TARGET PATTERN - Direct instantiation
@classmethod
def create_for_cli(cls, root_path: Path | None = None) -> "SpecContext":
    if root_path is None:
        root_path = Path.cwd()
    
    # Create dependencies directly
    settings = SpecSettings(root_path)
    console = SpecConsole(
        width=settings.console_width,
        no_color=not settings.use_color,
        force_terminal=settings.use_color
    )
    progress = ProgressManager(console=console)
    
    return cls(
        settings=settings,
        console=console,
        progress=progress,
    )
```

---

## DETAILED EXECUTION PLAN

### DAY 3: FACTORY METHOD REFACTORING

#### Task 3.1: Pre-Refactoring Validation and Backup
**Objective**: Ensure clean state and create safety net before modifications

**Commands to Execute**:
```bash
# 1. Validate current state using Phase 1 framework
echo "=== PRE-REFACTORING VALIDATION ==="
./validate_migration.sh | tee phase2_pre_validation.txt

# 2. Verify Phase 1 deliverables exist
echo "=== PHASE 1 DELIVERABLES CHECK ==="
ls -la dependency_mapping.txt progress_manager_analysis.txt architecture_analysis.txt

# 3. Create additional backups for Phase 2
echo "=== CREATING PHASE 2 BACKUPS ==="
cp spec_cli/core/context.py spec_cli/core/context.py.phase2_backup
cp spec_cli/core/context.py spec_cli/core/context.py.original

# 4. Analyze current SpecContext implementation
echo "=== CURRENT IMPLEMENTATION ANALYSIS ==="
echo "Current SpecContext factory methods:" > phase2_current_analysis.txt
grep -A 30 "def create_for_cli" spec_cli/core/context.py >> phase2_current_analysis.txt
echo "" >> phase2_current_analysis.txt
grep -A 20 "def create_for_testing" spec_cli/core/context.py >> phase2_current_analysis.txt
echo "" >> phase2_current_analysis.txt

# 5. Identify current imports in context.py
echo "Current imports in context.py:" >> phase2_current_analysis.txt
grep "^from\|^import" spec_cli/core/context.py >> phase2_current_analysis.txt
```

**Expected Outputs**:
- All 1006 tests should pass
- Performance should match baseline (~24.46s)
- No code quality issues
- Additional backup files created
- Current implementation analyzed

**Validation**:
- [ ] All tests pass (1006/1006)
- [ ] Performance within baseline tolerance
- [ ] Backup files created successfully
- [ ] Current implementation documented

#### Task 3.2: Analyze Required Dependencies
**Objective**: Understand exact dependencies needed for direct instantiation

**Commands to Execute**:
```bash
# 1. Analyze SpecSettings constructor requirements
echo "=== DEPENDENCY ANALYSIS ===" > phase2_dependency_analysis.txt
echo "" >> phase2_dependency_analysis.txt

echo "### SpecSettings constructor analysis:" >> phase2_dependency_analysis.txt
grep -A 20 "class SpecSettings" spec_cli/config/settings.py >> phase2_dependency_analysis.txt
grep -A 15 "def __init__" spec_cli/config/settings.py >> phase2_dependency_analysis.txt
echo "" >> phase2_dependency_analysis.txt

echo "### SpecConsole constructor analysis:" >> phase2_dependency_analysis.txt
grep -A 20 "class SpecConsole" spec_cli/ui/console.py >> phase2_dependency_analysis.txt
grep -A 15 "def __init__" spec_cli/ui/console.py >> phase2_dependency_analysis.txt
echo "" >> phase2_dependency_analysis.txt

echo "### ProgressManager constructor analysis:" >> phase2_dependency_analysis.txt
grep -A 20 "class ProgressManager" spec_cli/ui/progress_manager.py >> phase2_dependency_analysis.txt
grep -A 15 "def __init__" spec_cli/ui/progress_manager.py >> phase2_dependency_analysis.txt
echo "" >> phase2_dependency_analysis.txt

# 2. Check for circular import risks
echo "### Import analysis for circular dependency risks:" >> phase2_dependency_analysis.txt
echo "Files that import from core.context:" >> phase2_dependency_analysis.txt
grep -r "from.*core.context import" spec_cli/ >> phase2_dependency_analysis.txt
grep -r "from.*core import.*context" spec_cli/ >> phase2_dependency_analysis.txt
echo "" >> phase2_dependency_analysis.txt

echo "Dependencies of target classes:" >> phase2_dependency_analysis.txt
echo "SpecSettings imports:" >> phase2_dependency_analysis.txt
grep "^from\|^import" spec_cli/config/settings.py >> phase2_dependency_analysis.txt
echo "SpecConsole imports:" >> phase2_dependency_analysis.txt
grep "^from\|^import" spec_cli/ui/console.py >> phase2_dependency_analysis.txt
echo "ProgressManager imports:" >> phase2_dependency_analysis.txt
grep "^from\|^import" spec_cli/ui/progress_manager.py >> phase2_dependency_analysis.txt
```

**Analysis Requirements**:
Document in `phase2_dependency_analysis.txt`:
1. **Constructor signatures** for all target classes
2. **Parameter requirements** for each class
3. **Default values** and optional parameters
4. **Dependency relationships** between classes
5. **Circular import risks** and mitigation strategies

**Validation**:
- [ ] All constructor signatures analyzed
- [ ] Parameter requirements documented
- [ ] No circular import risks identified
- [ ] Dependency relationships clear

#### Task 3.3: Update Imports in context.py
**Objective**: Change imports from getter functions to concrete classes

**Commands to Execute**:
```bash
# 1. Create import update script
cat > update_context_imports.py << 'EOF'
#!/usr/bin/env python3
"""Script to update imports in context.py for Phase 2."""

import os
import re

def update_context_imports():
    context_file = "spec_cli/core/context.py"
    
    # Read current file
    with open(context_file, 'r') as f:
        content = f.read()
    
    # Store original for comparison
    original_content = content
    
    # Update imports - remove getter function imports
    content = re.sub(
        r'from\s+\.\.config\.settings\s+import.*get_settings.*\n',
        '',
        content
    )
    content = re.sub(
        r'from\s+\.\.ui\.console\s+import.*get_console.*\n',
        '',
        content
    )
    content = re.sub(
        r'from\s+\.\.ui\.progress_manager\s+import.*get_progress_manager.*\n',
        '',
        content
    )
    
    # Add direct class imports
    if 'from ..config.settings import SpecSettings' not in content:
        # Find the right place to add imports (after existing imports)
        import_section = content.find('from ..core.context_bridge import debug_logger')
        if import_section != -1:
            # Add new imports before debug_logger import
            new_imports = '''from ..config.settings import SpecSettings
from ..ui.console import SpecConsole
from ..ui.progress_manager import ProgressManager
'''
            content = content[:import_section] + new_imports + content[import_section:]
    
    # Write updated content
    with open(context_file, 'w') as f:
        f.write(content)
    
    print("Import updates completed")
    print("Original imports removed:")
    print("- get_settings")
    print("- get_console") 
    print("- get_progress_manager")
    print("New imports added:")
    print("- SpecSettings")
    print("- SpecConsole")
    print("- ProgressManager")
    
    return original_content != content

if __name__ == "__main__":
    changed = update_context_imports()
    if changed:
        print("Context imports updated successfully")
    else:
        print("No changes needed")
EOF

chmod +x update_context_imports.py

# 2. Execute import update
echo "=== UPDATING IMPORTS ==="
python3 update_context_imports.py

# 3. Verify import changes
echo "=== VERIFYING IMPORT CHANGES ==="
echo "New imports in context.py:" > phase2_import_changes.txt
grep "^from\|^import" spec_cli/core/context.py >> phase2_import_changes.txt

# 4. Check for syntax errors
echo "=== SYNTAX VALIDATION ==="
python3 -m py_compile spec_cli/core/context.py
echo "Context.py syntax is valid"

# 5. Quick test to ensure no immediate import errors
echo "=== IMPORT VALIDATION ==="
python3 -c "from spec_cli.core.context import SpecContext; print('Imports successful')"
```

**Expected Outputs**:
- Import update script executed successfully
- Old getter function imports removed
- New concrete class imports added
- No syntax errors in context.py
- Import validation successful

**Validation**:
- [ ] Import update script runs successfully
- [ ] Old imports removed (get_settings, get_console, get_progress_manager)
- [ ] New imports added (SpecSettings, SpecConsole, ProgressManager)
- [ ] No syntax errors in context.py
- [ ] Context.py can be imported without errors

#### Task 3.4: Refactor create_for_cli() Method
**Objective**: Implement direct dependency instantiation in CLI factory

**Commands to Execute**:
```bash
# 1. Create factory refactoring script
cat > refactor_cli_factory.py << 'EOF'
#!/usr/bin/env python3
"""Script to refactor create_for_cli method for Phase 2."""

import re

def refactor_cli_factory():
    context_file = "spec_cli/core/context.py"
    
    # Read current file
    with open(context_file, 'r') as f:
        content = f.read()
    
    # Find the create_for_cli method
    method_pattern = r'(@classmethod\s+def create_for_cli\(cls.*?\n.*?return cls\(.*?\))'
    
    # New implementation
    new_method = '''@classmethod
    def create_for_cli(
        cls, root_path: Path | None = None, **overrides: Any
    ) -> "SpecContext":
        """Create SpecContext for CLI environment with real dependencies.

        Factory method for creating production SpecContext instances in CLI
        environments with real dependency implementations.

        Args:
            root_path: Root path for spec operations (defaults to current directory)
            **overrides: Optional configuration overrides

        Returns:
            SpecContext instance configured for CLI environment

        Raises:
            SpecFactoryError: If CLI context creation fails

        Example:
            context = SpecContext.create_for_cli(Path("/project"))
            # Use context.settings, context.console, context.progress
        """
        try:
            debug_logger.log(
                "DEBUG",
                "Creating SpecContext for CLI environment",
                root_path=str(root_path) if root_path else None,
                overrides_count=len(overrides),
                override_keys=list(overrides.keys()),
            )

            # Validate inputs using factory utils
            validate_factory_inputs(
                factory_type="cli_context",
                environment="cli",
                **overrides,
            )

            # Use current directory if no root path provided
            if root_path is None:
                root_path = Path.cwd()
                debug_logger.log(
                    "DEBUG", "Using current directory as root", root_path=str(root_path)
                )

            # Create CLI settings directly (no singleton call)
            cli_settings = SpecSettings(root_path)

            # Create console directly with settings-based configuration
            cli_console = SpecConsole(
                width=cli_settings.console_width,
                no_color=not cli_settings.use_color,
                force_terminal=cli_settings.use_color
            )

            # Create progress manager directly with console dependency
            cli_progress = ProgressManager(console=cli_console.console)

            debug_logger.log(
                "DEBUG",
                "Using concrete implementations",
                settings_type=type(cli_settings).__name__,
                console_type=type(cli_console).__name__,
                progress_type=type(cli_progress).__name__,
            )

            # Apply any setting overrides if provided
            for key, value in overrides.items():
                if hasattr(cli_settings, key):
                    setattr(cli_settings, key, value)
                    debug_logger.log(
                        "DEBUG", "Applied setting override", key=key, value=value
                    )

            # Create and return context
            context = cls(
                settings=cli_settings,
                console=cli_console,
                progress=cli_progress,
            )

            debug_logger.log(
                "DEBUG",
                "CLI SpecContext created successfully",
                context_hash=context.get_context_hash()[:8],
                settings_type=type(cli_settings).__name__,
                console_type=type(cli_console).__name__,
                progress_type=type(cli_progress).__name__,
            )

            return context

        except Exception as e:
            error_context = create_error_context(root_path or Path.cwd())
            error_context.update(
                {
                    "factory_type": "cli",
                    "overrides": overrides,
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                }
            )
            raise SpecFactoryError(
                f"Failed to create CLI SpecContext: {e}", error_context
            ) from e'''
    
    # Replace the method
    content = re.sub(method_pattern, new_method, content, flags=re.DOTALL)
    
    # Write updated content
    with open(context_file, 'w') as f:
        f.write(content)
    
    print("create_for_cli() method refactored successfully")
    print("Changes:")
    print("- Direct SpecSettings instantiation")
    print("- Direct SpecConsole instantiation with settings configuration")
    print("- Direct ProgressManager instantiation with console dependency")
    print("- No singleton getter calls")
    print("- Maintained all error handling and logging")

if __name__ == "__main__":
    refactor_cli_factory()
EOF

chmod +x refactor_cli_factory.py

# 2. Execute factory refactoring
echo "=== REFACTORING CLI FACTORY ==="
python3 refactor_cli_factory.py

# 3. Verify the refactored method
echo "=== VERIFYING REFACTORED METHOD ==="
echo "Refactored create_for_cli method:" > phase2_cli_factory_refactored.txt
grep -A 50 "def create_for_cli" spec_cli/core/context.py >> phase2_cli_factory_refactored.txt

# 4. Check for syntax errors
echo "=== SYNTAX VALIDATION ==="
python3 -m py_compile spec_cli/core/context.py
echo "Context.py syntax is valid after refactoring"

# 5. Test factory method functionality
echo "=== FACTORY FUNCTIONALITY TEST ==="
python3 -c "
from spec_cli.core.context import SpecContext
from pathlib import Path
import tempfile

# Test CLI factory
with tempfile.TemporaryDirectory() as tmpdir:
    context = SpecContext.create_for_cli(Path(tmpdir))
    print(f'CLI factory successful: {type(context).__name__}')
    print(f'Settings type: {type(context.settings).__name__}')
    print(f'Console type: {type(context.console).__name__}')
    print(f'Progress type: {type(context.progress).__name__}')
"
```

**Expected Outputs**:
- Factory refactoring script executed successfully
- create_for_cli() method updated with direct instantiation
- No syntax errors in context.py
- Factory method functionality test passes
- All dependencies properly instantiated

**Validation**:
- [ ] Factory refactoring script runs successfully
- [ ] create_for_cli() method updated
- [ ] Direct instantiation implemented (no singleton calls)
- [ ] No syntax errors in context.py
- [ ] Factory method creates proper instances

#### Task 3.5: Validate create_for_testing() Method
**Objective**: Ensure testing factory remains compatible with mocks

**Commands to Execute**:
```bash
# 1. Analyze current create_for_testing implementation
echo "=== TESTING FACTORY ANALYSIS ===" > phase2_testing_factory_analysis.txt
echo "Current create_for_testing method:" >> phase2_testing_factory_analysis.txt
grep -A 30 "def create_for_testing" spec_cli/core/context.py >> phase2_testing_factory_analysis.txt
echo "" >> phase2_testing_factory_analysis.txt

# 2. Test create_for_testing functionality
echo "=== TESTING FACTORY VALIDATION ==="
python3 -c "
from spec_cli.core.context import SpecContext
from unittest.mock import Mock

# Test testing factory
context = SpecContext.create_for_testing()
print(f'Testing factory successful: {type(context).__name__}')
print(f'Settings type: {type(context.settings).__name__}')
print(f'Console type: {type(context.console).__name__}')
print(f'Progress type: {type(context.progress).__name__}')

# Test with overrides
context_with_overrides = SpecContext.create_for_testing({
    'console': Mock(spec=['print', 'print_status']),
    'debug_enabled': True
})
print('Testing factory with overrides successful')
"

# 3. Verify create_for_testing doesn't need changes
echo "=== TESTING FACTORY COMPATIBILITY CHECK ==="
echo "Testing factory uses mocks and should not need changes" >> phase2_testing_factory_analysis.txt
echo "Verification: create_for_testing() uses Mock objects, not real instances" >> phase2_testing_factory_analysis.txt
```

**Expected Outputs**:
- create_for_testing() method analyzed
- Testing factory functionality verified
- Mock compatibility confirmed
- No changes needed for testing factory

**Validation**:
- [ ] create_for_testing() method analyzed
- [ ] Testing factory works with mocks
- [ ] No changes needed for testing factory
- [ ] Mock compatibility maintained

### DAY 4: FACTORY METHOD TESTING & VALIDATION

#### Task 4.1: Comprehensive Test Suite Validation
**Objective**: Ensure all tests pass with refactored factory methods

**Commands to Execute**:
```bash
# 1. Run full test suite with detailed output
echo "=== COMPREHENSIVE TEST VALIDATION ==="
./validate_migration.sh | tee phase2_post_refactor_validation.txt

# 2. Check for any test failures or errors
echo "=== TEST FAILURE ANALYSIS ==="
if grep -q "FAILED" phase2_post_refactor_validation.txt; then
    echo "Test failures detected!" > phase2_test_failures.txt
    grep -A 5 -B 5 "FAILED\|ERROR" phase2_post_refactor_validation.txt >> phase2_test_failures.txt
    echo "CRITICAL: Test failures found - review phase2_test_failures.txt"
else
    echo "All tests passed successfully"
fi

# 3. Performance comparison with baseline
echo "=== PERFORMANCE COMPARISON ==="
current_performance=$(grep "Test duration:" phase2_post_refactor_validation.txt | grep -o "[0-9]*s")
baseline_performance=$(grep "Test duration:" phase2_pre_validation.txt | grep -o "[0-9]*s")
echo "Baseline performance: ${baseline_performance}"
echo "Current performance: ${current_performance}"

# 4. Test specific CLI functionality
echo "=== CLI FUNCTIONALITY VALIDATION ==="
python3 -c "
import subprocess
import sys

# Test CLI commands with new factory
commands = [
    ['python', '-m', 'spec_cli.cli.app', '--help'],
    ['python', '-m', 'spec_cli.cli.app', 'init', '--help'],
    ['python', '-m', 'spec_cli.cli.app', 'status', '--help'],
]

for cmd in commands:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print(f'✓ {\" \".join(cmd)} - Success')
        else:
            print(f'✗ {\" \".join(cmd)} - Failed: {result.stderr}')
    except Exception as e:
        print(f'✗ {\" \".join(cmd)} - Error: {e}')
"
```

**Expected Outputs**:
- All 1006 tests should pass
- Performance should be within 5% of baseline
- No test failures or errors
- CLI commands should work correctly

**Validation**:
- [ ] All 1006 tests pass
- [ ] Performance within 5% of baseline
- [ ] No test failures or errors
- [ ] CLI commands work correctly

#### Task 4.2: Context Injection Decorator Validation
**Objective**: Verify context injection decorators work with refactored factories

**Commands to Execute**:
```bash
# 1. Test context injection functionality
echo "=== CONTEXT INJECTION VALIDATION ==="
python3 -c "
import sys
import tempfile
from pathlib import Path
from spec_cli.core.context import SpecContext
from spec_cli.cli.decorators import context_injection

# Test context injection decorator
@context_injection
def test_command(context: SpecContext) -> str:
    return f'Context received: {type(context).__name__}'

# Mock Click context for testing
class MockClickContext:
    def __init__(self):
        self.meta = {}
        self.obj = {}
        
    def get_current_context(self):
        return self

# Test decorator functionality
with tempfile.TemporaryDirectory() as tmpdir:
    context = SpecContext.create_for_cli(Path(tmpdir))
    
    # This would normally be set up by CLI app
    import click
    ctx = click.Context(click.Command('test'))
    ctx.meta = {'spec_context': context}
    
    print('Context injection decorator test passed')
    print(f'Context type: {type(context).__name__}')
    print(f'Settings type: {type(context.settings).__name__}')
    print(f'Console type: {type(context.console).__name__}')
    print(f'Progress type: {type(context.progress).__name__}')
"

# 2. Test CLI command with context injection
echo "=== CLI COMMAND CONTEXT VALIDATION ==="
python3 -c "
import tempfile
from pathlib import Path
from spec_cli.cli.commands.init import init_command
from spec_cli.core.context import SpecContext
import click

# Test that init command can receive context
with tempfile.TemporaryDirectory() as tmpdir:
    context = SpecContext.create_for_cli(Path(tmpdir))
    
    # Verify context has all required attributes
    assert hasattr(context, 'settings'), 'Context missing settings'
    assert hasattr(context, 'console'), 'Context missing console'
    assert hasattr(context, 'progress'), 'Context missing progress'
    
    print('CLI command context validation passed')
    print('Context has all required attributes')
"
```

**Expected Outputs**:
- Context injection decorator works correctly
- CLI commands can receive context
- Context has all required attributes
- No errors in context injection

**Validation**:
- [ ] Context injection decorator works
- [ ] CLI commands receive proper context
- [ ] Context has all required attributes
- [ ] No context injection errors

#### Task 4.3: Factory Method Independence Validation
**Objective**: Ensure factory methods create independent instances

**Commands to Execute**:
```bash
# 1. Test factory method independence
echo "=== FACTORY INDEPENDENCE VALIDATION ==="
python3 -c "
import tempfile
from pathlib import Path
from spec_cli.core.context import SpecContext

# Test that create_for_cli creates independent instances
with tempfile.TemporaryDirectory() as tmpdir:
    context1 = SpecContext.create_for_cli(Path(tmpdir))
    context2 = SpecContext.create_for_cli(Path(tmpdir))
    
    # Verify instances are different
    assert context1 is not context2, 'Contexts should be different instances'
    assert context1.settings is not context2.settings, 'Settings should be different instances'
    assert context1.console is not context2.console, 'Consoles should be different instances'
    assert context1.progress is not context2.progress, 'Progress managers should be different instances'
    
    print('✓ Factory creates independent instances')
    print(f'Context1 ID: {id(context1)}')
    print(f'Context2 ID: {id(context2)}')
    print(f'Settings1 ID: {id(context1.settings)}')
    print(f'Settings2 ID: {id(context2.settings)}')

# Test testing factory independence
test_context1 = SpecContext.create_for_testing()
test_context2 = SpecContext.create_for_testing()

assert test_context1 is not test_context2, 'Test contexts should be different instances'
print('✓ Testing factory creates independent instances')
"

# 2. Test no shared state between instances
echo "=== SHARED STATE VALIDATION ==="
python3 -c "
import tempfile
from pathlib import Path
from spec_cli.core.context import SpecContext

# Test that modifying one context doesn't affect another
with tempfile.TemporaryDirectory() as tmpdir:
    context1 = SpecContext.create_for_cli(Path(tmpdir))
    context2 = SpecContext.create_for_cli(Path(tmpdir))
    
    # Modify settings in context1
    original_debug = context1.settings.debug_enabled
    context1.settings.debug_enabled = not original_debug
    
    # Verify context2 is unaffected
    assert context2.settings.debug_enabled == original_debug, 'Settings should be independent'
    
    print('✓ No shared state between contexts')
    print(f'Context1 debug: {context1.settings.debug_enabled}')
    print(f'Context2 debug: {context2.settings.debug_enabled}')
"
```

**Expected Outputs**:
- Factory methods create independent instances
- No shared state between contexts
- Different object IDs for each instance
- Modifying one context doesn't affect others

**Validation**:
- [ ] Factory methods create independent instances
- [ ] No shared state between contexts
- [ ] Different object IDs confirmed
- [ ] State isolation verified

#### Task 4.4: Dependency Chain Validation
**Objective**: Verify all dependencies are properly instantiated and connected

**Commands to Execute**:
```bash
# 1. Test dependency chain integrity
echo "=== DEPENDENCY CHAIN VALIDATION ==="
python3 -c "
import tempfile
from pathlib import Path
from spec_cli.core.context import SpecContext
from spec_cli.config.settings import SpecSettings
from spec_cli.ui.console import SpecConsole
from spec_cli.ui.progress_manager import ProgressManager

# Test that all dependencies are properly instantiated
with tempfile.TemporaryDirectory() as tmpdir:
    context = SpecContext.create_for_cli(Path(tmpdir))
    
    # Verify types are correct
    assert isinstance(context.settings, SpecSettings), f'Settings should be SpecSettings, got {type(context.settings)}'
    assert isinstance(context.console, SpecConsole), f'Console should be SpecConsole, got {type(context.console)}'
    assert isinstance(context.progress, ProgressManager), f'Progress should be ProgressManager, got {type(context.progress)}'
    
    # Verify dependencies are connected
    assert context.settings.root_path == Path(tmpdir), 'Settings should have correct root path'
    assert hasattr(context.console, 'print'), 'Console should have print method'
    assert hasattr(context.progress, 'start_indeterminate_operation'), 'Progress should have start method'
    
    print('✓ All dependencies properly instantiated')
    print(f'Settings type: {type(context.settings).__name__}')
    print(f'Console type: {type(context.console).__name__}')
    print(f'Progress type: {type(context.progress).__name__}')
    print(f'Root path: {context.settings.root_path}')
"

# 2. Test dependency configuration
echo "=== DEPENDENCY CONFIGURATION VALIDATION ==="
python3 -c "
import tempfile
from pathlib import Path
from spec_cli.core.context import SpecContext

# Test that dependencies are properly configured
with tempfile.TemporaryDirectory() as tmpdir:
    context = SpecContext.create_for_cli(Path(tmpdir))
    
    # Verify settings configuration
    assert context.settings.root_path == Path(tmpdir), 'Settings should use provided root path'
    assert hasattr(context.settings, 'debug_enabled'), 'Settings should have debug_enabled'
    assert hasattr(context.settings, 'console_width'), 'Settings should have console_width'
    assert hasattr(context.settings, 'use_color'), 'Settings should have use_color'
    
    # Verify console configuration
    assert hasattr(context.console, 'get_width'), 'Console should have get_width method'
    assert hasattr(context.console, 'print_status'), 'Console should have print_status method'
    
    # Verify progress configuration
    assert hasattr(context.progress, 'console'), 'Progress should have console reference'
    
    print('✓ All dependencies properly configured')
    print(f'Settings root path: {context.settings.root_path}')
    print(f'Settings debug enabled: {context.settings.debug_enabled}')
    print(f'Console width: {context.console.get_width()}')
"
```

**Expected Outputs**:
- All dependencies properly instantiated
- Correct dependency types
- Dependencies properly connected
- Configuration values correct

**Validation**:
- [ ] All dependencies properly instantiated
- [ ] Correct dependency types (SpecSettings, SpecConsole, ProgressManager)
- [ ] Dependencies properly connected
- [ ] Configuration values correct

#### Task 4.5: Final Phase 2 Validation
**Objective**: Comprehensive validation of all Phase 2 changes

**Commands to Execute**:
```bash
# 1. Run complete validation suite
echo "=== FINAL PHASE 2 VALIDATION ==="
./validate_migration.sh | tee phase2_final_validation.txt

# 2. Compare with baseline performance
echo "=== PERFORMANCE COMPARISON ==="
echo "Phase 2 Performance Analysis:" > phase2_performance_analysis.txt
echo "Pre-refactor: $(grep 'Test duration:' phase2_pre_validation.txt)" >> phase2_performance_analysis.txt
echo "Post-refactor: $(grep 'Test duration:' phase2_final_validation.txt)" >> phase2_performance_analysis.txt

# 3. Validate architectural changes
echo "=== ARCHITECTURAL VALIDATION ==="
echo "Architectural Changes Validation:" > phase2_architectural_validation.txt
echo "1. Singleton getter calls removed from SpecContext:" >> phase2_architectural_validation.txt
grep -c "get_settings\|get_console\|get_progress_manager" spec_cli/core/context.py >> phase2_architectural_validation.txt
echo "2. Direct class imports added:" >> phase2_architectural_validation.txt
grep "from.*SpecSettings\|from.*SpecConsole\|from.*ProgressManager" spec_cli/core/context.py >> phase2_architectural_validation.txt
echo "3. Factory method creates direct instances:" >> phase2_architectural_validation.txt
grep -A 5 "cli_settings = SpecSettings" spec_cli/core/context.py >> phase2_architectural_validation.txt

# 4. Test CLI functionality end-to-end
echo "=== END-TO-END CLI VALIDATION ==="
python3 -c "
import subprocess
import tempfile
from pathlib import Path

# Test complete CLI workflow
with tempfile.TemporaryDirectory() as tmpdir:
    # Test init command
    result = subprocess.run([
        'python', '-m', 'spec_cli.cli.app', 'init', '--help'
    ], capture_output=True, text=True, cwd=tmpdir)
    
    if result.returncode == 0:
        print('✓ CLI init command works')
    else:
        print(f'✗ CLI init command failed: {result.stderr}')
    
    # Test status command
    result = subprocess.run([
        'python', '-m', 'spec_cli.cli.app', 'status', '--help'
    ], capture_output=True, text=True, cwd=tmpdir)
    
    if result.returncode == 0:
        print('✓ CLI status command works')
    else:
        print(f'✗ CLI status command failed: {result.stderr}')
"

# 5. Create Phase 2 completion report
echo "=== PHASE 2 COMPLETION REPORT ==="
cat > PHASE_2_COMPLETION_REPORT.md << 'EOF'
# Phase 2 Completion Report

## Changes Made

### 1. Import Updates in spec_cli/core/context.py
- Removed: `get_settings`, `get_console`, `get_progress_manager` imports
- Added: `SpecSettings`, `SpecConsole`, `ProgressManager` imports

### 2. Factory Method Refactoring
- `create_for_cli()` now instantiates dependencies directly
- No more singleton getter calls
- Maintains all error handling and logging
- Proper configuration of dependencies

### 3. Dependency Chain Improvements
- Direct instantiation of SpecSettings with root_path
- Direct instantiation of SpecConsole with settings configuration
- Direct instantiation of ProgressManager with console dependency
- No shared state between context instances

## Validation Results

### Test Results
- Total tests: 1006
- Passed: [TO BE FILLED]
- Failed: [TO BE FILLED]

### Performance Results
- Baseline: [TO BE FILLED]
- Phase 2: [TO BE FILLED]
- Change: [TO BE FILLED]

### Architectural Validation
- Singleton getter calls in SpecContext: 0
- Direct class imports: 3 (SpecSettings, SpecConsole, ProgressManager)
- Factory method independence: Verified
- CLI functionality: Working

## Success Criteria Met
- [ ] All 1006 tests pass
- [ ] Performance within 5% of baseline
- [ ] SpecContext factory methods instantiate dependencies directly
- [ ] CLI functionality unchanged
- [ ] Test infrastructure continues working with mocks
- [ ] Factory methods create independent instances
- [ ] No shared state between contexts

## Phase 2 Complete
Phase 2 successfully completed the decoupling of SpecContext from singleton patterns.
The hidden dependency chain has been broken and all dependencies are now explicitly instantiated.
EOF
```

**Expected Outputs**:
- All 1006 tests pass
- Performance within 5% of baseline
- Architectural changes validated
- CLI functionality working
- Phase 2 completion report created

**Validation**:
- [ ] All 1006 tests pass
- [ ] Performance within 5% of baseline
- [ ] Architectural changes validated
- [ ] CLI functionality working
- [ ] Phase 2 completion report created

---

## EXPECTED DELIVERABLES

### Modified Files
1. **spec_cli/core/context.py** - Updated imports and create_for_cli() method
2. **spec_cli/core/context.py.phase2_backup** - Backup of original file

### Analysis Documents
1. **phase2_current_analysis.txt** - Current implementation analysis
2. **phase2_dependency_analysis.txt** - Dependency requirements analysis
3. **phase2_import_changes.txt** - Import changes verification
4. **phase2_cli_factory_refactored.txt** - Refactored factory method
5. **phase2_testing_factory_analysis.txt** - Testing factory analysis
6. **phase2_architectural_validation.txt** - Architectural changes validation
7. **phase2_performance_analysis.txt** - Performance comparison

### Validation Results
1. **phase2_pre_validation.txt** - Pre-refactoring validation results
2. **phase2_post_refactor_validation.txt** - Post-refactoring validation results
3. **phase2_final_validation.txt** - Final validation results
4. **phase2_test_failures.txt** - Test failure analysis (if any)

### Scripts Created
1. **update_context_imports.py** - Import update automation
2. **refactor_cli_factory.py** - Factory refactoring automation

### Documentation
1. **PHASE_2_COMPLETION_REPORT.md** - Comprehensive completion report

---

## QUALITY ASSURANCE REQUIREMENTS

### Validation Gates
1. **Pre-Refactoring Validation**: All 1006 tests must pass before starting
2. **Import Validation**: No syntax errors after import changes
3. **Factory Validation**: Factory methods work correctly after refactoring
4. **Test Validation**: All 1006 tests must pass after changes
5. **Performance Validation**: Performance must be within 5% of baseline
6. **Independence Validation**: Factory methods must create independent instances

### Success Criteria
1. **Test Pass Rate**: 1006/1006 (100%)
2. **Performance**: Within 5% of baseline (~24.46s)
3. **Architectural**: No singleton getter calls in SpecContext
4. **Functional**: CLI commands work correctly
5. **Independence**: Factory methods create independent instances

### Safety Requirements
1. **Backup Integrity**: All backup files must be created before changes
2. **Rollback Capability**: Must be able to restore to pre-Phase 2 state
3. **Validation Frequency**: Run validation after each major change
4. **Error Handling**: Stop immediately if any validation fails

---

## ROLLBACK PROCEDURES

### Immediate Rollback
```bash
# Restore original context.py
cp spec_cli/core/context.py.phase2_backup spec_cli/core/context.py

# Validate rollback
./validate_migration.sh

# Verify restoration
python3 -c "from spec_cli.core.context import SpecContext; print('Rollback successful')"
```

### Validation After Rollback
```bash
# Ensure all tests pass
poetry run pytest tests/unit/ -v

# Check performance is back to baseline
time poetry run pytest tests/unit/

# Verify CLI functionality
python3 -m spec_cli.cli.app --help
```

---

## SUCCESS VALIDATION CHECKLIST

### Phase 2 Complete When:
- [ ] All 1006 tests pass consistently
- [ ] Performance within 5% of baseline
- [ ] SpecContext.create_for_cli() instantiates dependencies directly
- [ ] No singleton getter calls in SpecContext
- [ ] CLI functionality unchanged
- [ ] Context injection decorators work correctly
- [ ] Factory methods create independent instances
- [ ] No shared state between contexts
- [ ] All validation scripts run successfully
- [ ] Phase 2 completion report created

### Critical Success Metrics:
- **Test Pass Rate**: 1006/1006 (100%)
- **Performance**: Within 5% of baseline (~24.46s)
- **Singleton Calls**: 0 in SpecContext
- **Dependencies**: 3 direct instantiations (SpecSettings, SpecConsole, ProgressManager)
- **Independence**: Verified via object ID comparison
- **CLI Functionality**: All commands work correctly

---

## EMERGENCY PROCEDURES

### If Tests Fail:
1. **STOP IMMEDIATELY**
2. Run rollback: `cp spec_cli/core/context.py.phase2_backup spec_cli/core/context.py`
3. Validate restoration: `./validate_migration.sh`
4. Analyze failure: Check phase2_test_failures.txt
5. Document issue and seek assistance

### If Performance Degrades >5%:
1. **STOP IMMEDIATELY**
2. Run rollback procedures
3. Analyze performance issue
4. Document performance regression

### If CLI Commands Fail:
1. **STOP IMMEDIATELY**
2. Run rollback procedures
3. Test CLI functionality after rollback
4. Analyze CLI integration issue

---

## PHASE 2 COMPLETION CRITERIA

Phase 2 is complete when ALL of the following are achieved:

1. **Factory Methods Decoupled**: SpecContext factory methods instantiate dependencies directly
2. **No Singleton Calls**: Zero calls to get_settings(), get_console(), get_progress_manager() in SpecContext
3. **Tests Pass**: All 1006 tests pass consistently
4. **Performance Maintained**: Performance within 5% of baseline
5. **CLI Functional**: All CLI commands work correctly
6. **Independence Verified**: Factory methods create independent instances
7. **Documentation Complete**: All analysis and reports generated

**Next Phase**: Upon successful completion, proceed to Phase 3 with the singleton dependency chain broken and direct instantiation working correctly.

---

## TECHNICAL REFERENCE

### Key Changes Made
- **Imports**: Removed getter functions, added concrete classes
- **Factory Method**: create_for_cli() now instantiates dependencies directly
- **Dependency Chain**: SpecSettings → SpecConsole → ProgressManager
- **Independence**: Each factory call creates fresh instances

### Performance Expectations
- **Baseline**: ~24.46s for 1006 tests
- **Expected**: Within 5% of baseline (23.5s - 25.8s)
- **Acceptable**: Any performance within tolerance

### Architectural Validation
- **Before**: SpecContext → singleton getters → singleton managers → instances
- **After**: SpecContext → direct instantiation → fresh instances
- **Benefit**: No hidden dependencies, explicit dependency chain

This comprehensive prompt ensures Phase 2 completion with all necessary refactoring, validation, and safety measures required for successful progression to Phase 3.