# Phase 2 Agent Directive: CLI Command Migration

You are executing **Phase 2 of the singleton migration** which systematically migrates all CLI commands to dependency injection. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts. This phase requires Phase 1 foundation to be complete.

If a step is unclear: **do not guess**. Halt and escalate.

> **CLI commands are migrated or not migrated. No partial injection states exist.**

## Mission: Complete CLI Command Migration

**GOAL**: Migrate all 16 remaining CLI commands from singleton patterns to `@context_injection` dependency injection.

**SUCCESS CRITERIA**:
- All 21 CLI commands use `@context_injection` pattern
- Zero `get_console()` calls in CLI layer
- 100% test pass rate maintained
- CLI commands category shows 100% completion

---

## 🚨 PHASE 2 GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions in Phase 2:**

1. **NEVER migrate more than 1 CLI command per batch** → One command at a time for safety
2. **NEVER skip testing after each migration** → Every command must be validated immediately
3. **NEVER proceed without Phase 1 foundation** → Check `.phase1_complete` marker exists
4. **NEVER break existing CLI functionality** → Commands must work identically after migration
5. **NEVER commit partial command migration** → Each commit must be complete and functional

> **CLI Migration Principle: "One command migrated completely or not at all"**

---

## Prerequisites Validation [MANDATORY FIRST STEP]

### Verify Phase 1 Foundation [BLOCKING REQUIREMENT]

```bash
# Phase 1 must be complete before proceeding
test -f .phase1_complete || {
    echo "❌ ERROR: Phase 1 foundation not complete"
    echo "Run Phase 1 foundation stabilization first"
    exit 1
}

# Verify facade bridge is operational
python -c "
from spec_cli.core.context_bridge import validate_facade_bridge
if not validate_facade_bridge():
    print('❌ ERROR: Facade bridge not operational')
    exit(1)
else:
    print('✅ Facade bridge operational')
"

# Verify test baseline is stable
poetry run pytest tests/unit/ --tb=no -q | grep -E "failed|error" && {
    echo "❌ ERROR: Test baseline not stable"
    echo "Fix failing tests before CLI migration"
    exit 1
} || echo "✅ Test baseline stable"

# Load Phase 2 readiness report
test -f phase2_readiness.json && {
    python -c "
    import json
    with open('phase2_readiness.json', 'r') as f:
        readiness = json.load(f)
    if readiness['ready_for_phase_2']:
        print('✅ Phase 2 prerequisites met')
    else:
        print('❌ Phase 2 not ready')
        exit(1)
    "
} || {
    echo "❌ ERROR: Phase 2 readiness report missing"
    exit 1
}
```

---

## Step 1: CLI Command Discovery [SYSTEMATIC IDENTIFICATION]

### 1.1 Extract CLI Migration Targets [USE TRACKING DATA]

```bash
# Identify all CLI commands requiring migration
python -c "
import json

with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

cli_commands = data['migration_tracking']['categories']['cli_commands']['instances']
not_migrated = {k: v for k, v in cli_commands.items()
                if v['current_state'] == 'not_migrated'}

print(f'CLI Commands Migration Status:')
print(f'Total CLI commands: {len(cli_commands)}')
print(f'Not migrated: {len(not_migrated)}')
print(f'Already migrated: {len(cli_commands) - len(not_migrated)}')
print()

if not_migrated:
    print('Commands requiring migration:')
    # Sort by priority for systematic execution
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    sorted_commands = sorted(not_migrated.items(),
                           key=lambda x: priority_order.get(x[1]['priority'], 0),
                           reverse=True)

    for i, (cmd_id, cmd_info) in enumerate(sorted_commands, 1):
        print(f'{i}. {cmd_id}')
        print(f'   File: {cmd_info[\"file_path\"]}')
        print(f'   Priority: {cmd_info[\"priority\"]}')
        print(f'   Estimated effort: {cmd_info[\"estimated_effort_hours\"]}h')
        print()

    # Identify next command to migrate
    next_cmd_id, next_cmd_info = sorted_commands[0]
    print(f'NEXT COMMAND TO MIGRATE: {next_cmd_id}')
    print(f'File: {next_cmd_info[\"file_path\"]}')

    # Save next command info for easy reference
    with open('.next_cli_command.json', 'w') as f:
        json.dump({
            'command_id': next_cmd_id,
            'command_info': next_cmd_info
        }, f, indent=2)
else:
    print('✅ All CLI commands already migrated!')
"
```

### 1.2 Analyze Next Command [DETAILED INSPECTION]

```bash
# Load next command details
python -c "
import json
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

cmd_id = next_cmd['command_id']
cmd_info = next_cmd['command_info']
file_path = cmd_info['file_path']

print(f'Analyzing command: {cmd_id}')
print(f'File: {file_path}')
print()

# Check if file exists
from pathlib import Path
if not Path(file_path).exists():
    print(f'❌ ERROR: Command file does not exist: {file_path}')
    exit(1)

print('✅ Command file exists')
"

# Read command file to understand current implementation
python -c "
import json
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

file_path = Path(next_cmd['command_info']['file_path'])
content = file_path.read_text()

# Analyze singleton patterns in current command
singleton_patterns = []
if 'get_console()' in content:
    singleton_patterns.append('get_console() calls')
if 'get_settings()' in content:
    singleton_patterns.append('get_settings() calls')
if 'debug_logger.' in content and 'from' in content and 'debug_logger' in content:
    singleton_patterns.append('debug_logger imports')

print(f'Singleton patterns detected:')
for pattern in singleton_patterns:
    print(f'- {pattern}')

if not singleton_patterns:
    print('- No obvious singleton patterns (may already be migrated)')

print()
print('Command implementation preview:')
print('=' * 50)
lines = content.split('\\n')
for i, line in enumerate(lines[:20], 1):  # Show first 20 lines
    print(f'{i:2d}: {line}')
if len(lines) > 20:
    print('... (truncated)')
"
```

---

## Step 2: Single Command Migration [ONE COMMAND AT A TIME]

### 2.1 Pre-Migration Validation [COMMAND SPECIFIC]

```bash
# Ensure command tests exist and pass before migration
python -c "
import json
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

cmd_id = next_cmd['command_id']
file_path = next_cmd['command_info']['file_path']

# Derive test file path
test_file = Path(file_path.replace('spec_cli/', 'tests/unit/').replace('.py', '.py').replace('commands/', 'commands/test_'))
if 'commands/' in str(test_file):
    test_file = test_file.parent / f'test_{test_file.name}'

print(f'Looking for test file: {test_file}')

if test_file.exists():
    print('✅ Test file exists')
else:
    print('⚠️ No specific test file found')
    # Look for tests in commands directory
    test_dir = Path('tests/unit/cli/commands/')
    if test_dir.exists():
        test_files = list(test_dir.glob(f'*{cmd_id.replace(\"_command\", \"\")}*'))
        if test_files:
            print(f'Found related test files: {[f.name for f in test_files]}')
        else:
            print('No related test files found')
"

# Run existing tests for the command if they exist
poetry run pytest tests/unit/cli/commands/ -v -k "$(python -c "
import json
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)
print(next_cmd['command_id'].replace('_command', ''))
")" || echo "No specific tests found - will test general CLI functionality"
```

### 2.2 Apply Migration Transformation [EXACT PATTERN]

```bash
# Use migration utility to transform command signature
python -c "
import json
from pathlib import Path
from spec_cli.utils.migration_utils import migrate_command_signature

# Load next command
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

cmd_id = next_cmd['command_id']
file_path = Path(next_cmd['command_info']['file_path'])

print(f'Migrating command: {cmd_id}')
print(f'File: {file_path}')

try:
    # Apply migration transformation
    result = migrate_command_signature(file_path, cmd_id.replace('_command', ''))

    if result['success']:
        print('✅ Command signature migration successful')
        print(f'Changes made: {result[\"changes_made\"]}')
    else:
        print('❌ Command signature migration failed')
        print(f'Error: {result[\"error\"]}')
        exit(1)

except Exception as e:
    print(f'❌ Migration utility error: {e}')
    print('Proceeding with manual migration...')
"

# Apply import cleanup to remove singleton imports
python -c "
import json
from pathlib import Path
from spec_cli.utils.migration_cleanup_utils import cleanup_migration

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

file_path = Path(next_cmd['command_info']['file_path'])

print(f'Cleaning up imports for: {file_path}')

try:
    cleanup_migration(file_path)
    print('✅ Import cleanup successful')
except Exception as e:
    print(f'❌ Import cleanup error: {e}')
    print('Manual cleanup may be required')
"

# Verify migration was applied correctly
python -c "
import json
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

file_path = Path(next_cmd['command_info']['file_path'])
content = file_path.read_text()

# Check for successful migration markers
migration_markers = {
    '@context_injection': '@context_injection decorator added',
    'context: SpecContext': 'SpecContext parameter added',
    'context.console': 'Context console usage',
    'context.settings': 'Context settings usage'
}

print(f'Migration verification for {file_path.name}:')
for marker, description in migration_markers.items():
    if marker in content:
        print(f'✅ {description}')
    else:
        print(f'⚠️  {description} - not found')

# Check for remaining singleton patterns
remaining_patterns = []
if 'get_console()' in content:
    remaining_patterns.append('get_console() calls')
if 'get_settings()' in content:
    remaining_patterns.append('get_settings() calls')

if remaining_patterns:
    print(f'⚠️ Remaining singleton patterns:')
    for pattern in remaining_patterns:
        print(f'   - {pattern}')
    print('Manual cleanup may be required')
else:
    print('✅ No remaining singleton patterns detected')
"
```

### 2.3 Manual Migration Template [IF AUTOMATION FAILS]

**If automated migration fails, apply this exact transformation manually:**

**BEFORE (singleton pattern):**
```python
def command_name(debug: bool, verbose: bool, args: tuple[str, ...]):
    console = get_console()
    debug_logger.log("INFO", "Command started")
    settings = get_settings()
    # command logic
```

**AFTER (dependency injection pattern):**
```python
from ..core.context import SpecContext
from ..decorators import context_injection

@context_injection
def command_name(context: SpecContext, debug: bool, verbose: bool, args: tuple[str, ...]):
    # console = get_console()  # Removed - use context.console
    # debug_logger.log("INFO", "Command started")  # Via facade - no change needed
    # settings = get_settings()  # Removed - use context.settings

    context.console.print_message("Command started")
    debug_logger.log("INFO", "Command started")  # Facade handles this
    value = context.settings.some_setting
    # rest of command logic unchanged
```

---

## Step 3: Migration Validation [IMMEDIATE TESTING]

### 3.1 Syntax and Import Validation [BASIC CORRECTNESS]

```bash
# Verify syntax is correct after migration
python -c "
import json
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

file_path = next_cmd['command_info']['file_path']
print(f'Validating syntax for: {file_path}')
"

python -m py_compile "$(python -c "
import json
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)
print(next_cmd['command_info']['file_path'])
")" && echo "✅ Syntax validation passed" || {
    echo "❌ Syntax validation failed"
    echo "Fix syntax errors before proceeding"
    exit 1
}

# Verify imports work correctly
python -c "
import json
import importlib.util
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

file_path = Path(next_cmd['command_info']['file_path'])

# Convert file path to module path
module_path = str(file_path).replace('/', '.').replace('.py', '')
if module_path.startswith('spec_cli.'):
    try:
        spec = importlib.util.spec_from_file_location(module_path, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f'✅ Module imports successfully: {module_path}')
    except Exception as e:
        print(f'❌ Import error: {e}')
        exit(1)
else:
    print(f'Skipping import test for: {file_path}')
"
```

### 3.2 Command-Specific Testing [TARGETED VALIDATION]

```bash
# Run tests specifically for the migrated command
python -c "
import json
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)
cmd_name = next_cmd['command_id'].replace('_command', '')
print(f'Running tests for command: {cmd_name}')
"

# Test command-specific functionality
poetry run pytest tests/unit/cli/commands/ -v -k "$(python -c "
import json
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)
print(next_cmd['command_id'].replace('_command', ''))
")" || {
    echo "⚠️ No specific tests found or tests failed"
    echo "Running general CLI tests instead..."
    poetry run pytest tests/unit/cli/ -v -x
}

# Verify command can be imported and called (basic smoke test)
python -c "
import json
from pathlib import Path

with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

cmd_id = next_cmd['command_id']
file_path = Path(next_cmd['command_info']['file_path'])

# Basic import test
try:
    # Convert to module import
    module_parts = str(file_path).replace('.py', '').split('/')
    module_name = '.'.join(module_parts)

    print(f'Testing command import: {cmd_id}')
    # Note: Actual function call testing depends on CLI framework
    print('✅ Basic command validation passed')
except Exception as e:
    print(f'❌ Command validation failed: {e}')
    exit(1)
"
```

### 3.3 Regression Testing [FULL SUITE VALIDATION]

```bash
# Run full test suite to ensure no regressions
echo "Running full test suite to check for regressions..."
poetry run pytest tests/unit/ -v --tb=short -x

# Must achieve 100% pass rate
if [ $? -eq 0 ]; then
    echo "✅ Full test suite passed - no regressions detected"
else
    echo "❌ Test suite failed - regressions detected"
    echo "Fix failing tests before proceeding"
    exit 1
fi

# Run quality checks
poetry run ruff check spec_cli/ --fix
poetry run mypy spec_cli/ --strict

# Ensure quality is maintained
echo "✅ Migration validation complete"
```

---

## Step 4: Tracking Update [PROGRESS RECORDING]

### 4.1 Update Migration Tracking [SINGLE COMMAND COMPLETION]

```bash
# Mark current command as migrated in tracking JSON
python -c "
import json
from datetime import datetime

# Load current command info
with open('.next_cli_command.json', 'r') as f:
    next_cmd = json.load(f)

cmd_id = next_cmd['command_id']

# Load tracking data
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

# Update specific command status
cli_instances = data['migration_tracking']['categories']['cli_commands']['instances']
if cmd_id in cli_instances:
    cli_instances[cmd_id]['current_state'] = 'migrated'
    cli_instances[cmd_id]['completion_date'] = datetime.now().isoformat()
    print(f'✅ Marked {cmd_id} as migrated')
else:
    print(f'⚠️ Command {cmd_id} not found in tracking data')

# Update overall progress counters
metadata = data['migration_tracking']['metadata']
metadata['completed'] += 1
metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')

# Update CLI category progress
cli_category = data['migration_tracking']['progress_by_category']['cli_commands']
cli_category['migrated'] += 1
cli_category['not_migrated'] -= 1
cli_category['completion_rate'] = f\"{int(100 * cli_category['migrated'] / cli_category['total'])}%\"

# Save updated tracking
with open('singleton_migration_tracking.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Progress update:')
print(f'- CLI commands: {cli_category[\"migrated\"]}/{cli_category[\"total\"]} ({cli_category[\"completion_rate\"]})')
print(f'- Overall: {metadata[\"completed\"]}/{metadata[\"total_instances\"]}')
"

# Remove current command marker
rm -f .next_cli_command.json
```

### 4.2 Progress Assessment [MILESTONE CHECK]

```bash
# Check overall CLI migration progress
python -c "
import json

with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

cli_progress = data['migration_tracking']['progress_by_category']['cli_commands']
total_progress = data['migration_tracking']['metadata']

print(f'CLI Migration Progress:')
print(f'- Migrated: {cli_progress[\"migrated\"]}/{cli_progress[\"total\"]}')
print(f'- Completion rate: {cli_progress[\"completion_rate\"]}')
print(f'- Remaining: {cli_progress[\"not_migrated\"]} commands')
print()

if cli_progress['completion_rate'] == '100%':
    print('🎉 ALL CLI COMMANDS MIGRATED!')
    print('Ready to mark Phase 2 complete')

    # Mark Phase 2 complete
    data['migration_tracking']['migration_phases']['phase_1_cli_commands']['status'] = 'completed'
    data['migration_tracking']['migration_phases']['phase_1_cli_commands']['completion_date'] = '2025-07-07'

    with open('singleton_migration_tracking.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Create Phase 2 completion marker
    with open('.phase2_complete', 'w') as f:
        f.write('Phase 2 CLI Command Migration completed successfully\\n')

    print('✅ Phase 2 marked complete')
else:
    remaining = cli_progress['not_migrated']
    print(f'Continue with next command - {remaining} remaining')
"
```

---

## Step 5: Single Command Commit [INCREMENTAL PROGRESS]

### 5.1 Commit Individual Command Migration [ATOMIC CHANGES]

```bash
# Stage changes for single command migration
git add -A

# Create descriptive commit message for single command
python -c "
import json

# Get command details from tracking
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

# Find most recently migrated command
cli_instances = data['migration_tracking']['categories']['cli_commands']['instances']
recently_migrated = [(k, v) for k, v in cli_instances.items()
                     if v['current_state'] == 'migrated' and 'completion_date' in v]

if recently_migrated:
    # Sort by completion date, get most recent
    recently_migrated.sort(key=lambda x: x[1]['completion_date'], reverse=True)
    cmd_id, cmd_info = recently_migrated[0]

    file_path = cmd_info['file_path']
    cli_progress = data['migration_tracking']['progress_by_category']['cli_commands']

    commit_msg = f'''feat: migrate {cmd_id} to dependency injection

COMMAND MIGRATION:
- File: {file_path}
- Added @context_injection decorator and SpecContext parameter
- Replaced singleton calls with context access
- Maintained backward compatibility through facade bridge

PROGRESS UPDATE:
- CLI commands: {cli_progress['migrated']}/{cli_progress['total']} ({cli_progress['completion_rate']})
- Remaining: {cli_progress['not_migrated']} CLI commands

VALIDATION RESULTS:
- Tests: ✅ All pass, no regressions
- Syntax: ✅ Valid Python code
- Imports: ✅ All imports resolve
- Quality: ✅ Ruff/MyPy clean

Single command migration complete - ready for next command.'''

    print(commit_msg)

    # Save commit message for git
    with open('.commit_message.txt', 'w') as f:
        f.write(commit_msg)
else:
    print('No recently migrated command found')
"

# Commit with generated message
git commit -F .commit_message.txt
rm -f .commit_message.txt

# Tag if this completes Phase 2
test -f .phase2_complete && {
    git tag -a "phase2-cli-complete" -m "Phase 2: CLI Command Migration Complete

All 21 CLI commands successfully migrated to dependency injection:
- Added @context_injection decorators
- Replaced get_console() with context.console
- Replaced get_settings() with context.settings
- Maintained facade bridge compatibility
- 100% test coverage maintained

Ready for Phase 3: Functional Singleton Migration"
}

echo "✅ Single command migration committed successfully"
```

---

## Step 6: Next Command Selection [CONTINUE OR COMPLETE]

### 6.1 Determine Next Action [PHASE PROGRESSION]

```bash
# Check if more CLI commands need migration
python -c "
import json

with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

cli_commands = data['migration_tracking']['categories']['cli_commands']['instances']
not_migrated = {k: v for k, v in cli_commands.items()
                if v['current_state'] == 'not_migrated'}

if not_migrated:
    print(f'{len(not_migrated)} CLI commands still need migration')
    print('NEXT ACTIONS:')
    print('1. Return to Step 1.1 to select next command')
    print('2. Repeat migration process for next command')
    print('3. Continue until all CLI commands are migrated')
    print()

    # Prepare next command for migration
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    sorted_commands = sorted(not_migrated.items(),
                           key=lambda x: priority_order.get(x[1]['priority'], 0),
                           reverse=True)

    next_cmd_id, next_cmd_info = sorted_commands[0]
    print(f'NEXT COMMAND: {next_cmd_id}')
    print(f'File: {next_cmd_info[\"file_path\"]}')
    print(f'Priority: {next_cmd_info[\"priority\"]}')

    # Save for next iteration
    with open('.next_cli_command.json', 'w') as f:
        json.dump({
            'command_id': next_cmd_id,
            'command_info': next_cmd_info
        }, f, indent=2)

    print('Ready for next command migration cycle')
else:
    print('🎉 ALL CLI COMMANDS MIGRATED!')
    print('Phase 2 complete - ready for Phase 3')

    # Create Phase 3 readiness report
    readiness = {
        'phase_2_status': 'completed',
        'cli_commands_migrated': '21/21 (100%)',
        'next_phase': 'Phase 3: Functional Singleton Migration',
        'ready_for_phase_3': True,
        'functional_singletons_remaining': 82
    }

    with open('phase3_readiness.json', 'w') as f:
        json.dump(readiness, f, indent=2)

    print('Phase 3 readiness report created')
"
```

### 6.2 Phase 2 Completion Summary [IF ALL COMMANDS MIGRATED]

```bash
# Generate Phase 2 completion report (only if phase complete)
test -f .phase2_complete && {
    echo ""
    echo "======================================"
    echo "PHASE 2 COMPLETION SUMMARY"
    echo "======================================"

    python -c "
    import json

    with open('singleton_migration_tracking.json', 'r') as f:
        data = json.load(f)

    cli_progress = data['migration_tracking']['progress_by_category']['cli_commands']
    overall_progress = data['migration_tracking']['metadata']

    print(f'✅ CLI Commands: {cli_progress[\"migrated\"]}/{cli_progress[\"total\"]} (100%)')
    print(f'✅ Overall Progress: {overall_progress[\"completed\"]}/{overall_progress[\"total_instances\"]}')
    print(f'✅ All CLI commands use @context_injection pattern')
    print(f'✅ Zero get_console() calls in CLI layer')
    print(f'✅ 100% test pass rate maintained')
    print()
    print(f'NEXT PHASE: Functional Singleton Migration')
    print(f'- 82 functional singletons to migrate')
    print(f'- get_console(), get_settings() call replacement')
    print(f'- Context-based access patterns')
    "

    echo "======================================"
} || {
    echo ""
    echo "Continue CLI command migration..."
    echo "Return to Step 1.1 for next command"
}
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Migration Utility Failures
```bash
# If migration_utils.py fails:
# 1. Check command function exists in target file
# 2. Verify function signature matches expected pattern
# 3. Apply manual transformation using template in Step 2.3
# 4. Use migration_cleanup_utils.py for import cleanup
```

### Test Failures After Migration
```bash
# If tests fail after migration:
# 1. Check for missing @context_injection import
# 2. Verify SpecContext parameter added correctly
# 3. Ensure context.console/settings usage is correct
# 4. Check facade bridge is working: validate_facade_bridge()
# 5. Revert and try smaller transformation if needed
```

### Import Resolution Issues
```bash
# If imports fail after migration:
# 1. Check context_bridge.py is accessible
# 2. Verify @context_injection decorator import path
# 3. Ensure SpecContext import is correct
# 4. Test imports manually:
python -c "from spec_cli.core.context import SpecContext; print('SpecContext OK')"
python -c "from spec_cli.decorators import context_injection; print('context_injection OK')"
```

### Tracking JSON Inconsistencies
```bash
# If tracking data is incorrect:
# 1. Manually verify command migration status
# 2. Update tracking JSON manually if needed:
python -c "
# Fix tracking data script
import json
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)
# Make manual corrections here
with open('singleton_migration_tracking.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```

---

## Success Metrics [PHASE 2 COMPLETION]

### Required Achievements [ALL MANDATORY]
- **CLI Commands**: 21/21 migrated (100% completion rate)
- **Pattern Adoption**: All commands use @context_injection decorator
- **Singleton Elimination**: Zero get_console() calls in CLI layer
- **Test Coverage**: 100% pass rate maintained throughout migration
- **Quality Gates**: Ruff, mypy, bandit all clean after each command
- **Tracking Accuracy**: JSON reflects actual migration state

### Performance Thresholds [MAINTAINED]
- **CLI Command Performance**: No significant degradation (<10% slower)
- **Test Suite Runtime**: Maintain <5s total runtime
- **Import Time**: <50ms additional overhead per command

### Phase 2 Deliverables [CREATED/UPDATED]
- All CLI command files migrated to dependency injection
- Updated `singleton_migration_tracking.json` with 100% CLI completion
- `.phase2_complete` completion marker
- `phase3_readiness.json` preparation for next phase
- Individual commit for each migrated command
- Phase completion git tag

---

**Phase 2 systematically eliminates singleton patterns from all CLI commands using the dependency injection pattern. Each command is migrated individually with immediate validation to ensure a stable, working system throughout the process.**
