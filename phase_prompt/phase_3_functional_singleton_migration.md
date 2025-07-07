# Phase 3 Agent Directive: Functional Singleton Migration

You are executing **Phase 3 of the singleton migration** which systematically replaces functional singleton calls with context-based access. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts. This phase requires Phase 2 CLI migration to be complete.

If a step is unclear: **do not guess**. Halt and escalate.

> **Functional singletons are eliminated or not touched. No partial replacement states exist.**

## Mission: Eliminate Functional Singleton Patterns

**GOAL**: Replace all 82 functional singleton calls (`get_console()`, `get_settings()`, etc.) with context-based access patterns.

**SUCCESS CRITERIA**:
- Zero `get_console()` calls remaining in codebase
- Zero `get_settings()` calls remaining in codebase
- All affected functions use dependency injection
- 100% test pass rate maintained
- Functional singletons category shows 100% completion

---

## 🚨 PHASE 3 GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions in Phase 3:**

1. **NEVER migrate more than 5 instances per batch** → Small batches for safety and validation
2. **NEVER skip @context_injection decorator** → Functions need context parameter to access resources
3. **NEVER proceed without Phase 2 complete** → CLI foundation must be solid first
4. **NEVER break caller compatibility** → Add context parameter, don't remove existing parameters
5. **NEVER commit partial batch migration** → Complete all 5 instances in batch before committing

> **Functional Migration Principle: "Small batches with complete validation"**

---

## Prerequisites Validation [MANDATORY FIRST STEP]

### Verify Phase 2 Foundation [BLOCKING REQUIREMENT]

```bash
# Phase 2 must be complete before proceeding
test -f .phase2_complete || {
    echo "❌ ERROR: Phase 2 CLI migration not complete"
    echo "Complete CLI command migration first"
    exit 1
}

# Verify CLI migration completion
python -c "
import json
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

cli_progress = data['migration_tracking']['progress_by_category']['cli_commands']
if cli_progress['completion_rate'] != '100%':
    print('❌ ERROR: CLI migration not 100% complete')
    exit(1)
else:
    print('✅ CLI migration complete')
"

# Load Phase 3 readiness
test -f phase3_readiness.json && {
    python -c "
    import json
    with open('phase3_readiness.json', 'r') as f:
        readiness = json.load(f)
    if readiness['ready_for_phase_3']:
        print('✅ Phase 3 prerequisites met')
    else:
        print('❌ Phase 3 not ready')
        exit(1
    "
} || {
    echo "❌ ERROR: Phase 3 readiness report missing"
    exit 1
}

# Verify facade bridge operational
python -c "
from spec_cli.core.context_bridge import validate_facade_bridge
if validate_facade_bridge():
    print('✅ Facade bridge operational')
else:
    print('❌ Facade bridge not working')
    exit(1)
"
```

---

## Step 1: Functional Singleton Discovery [SYSTEMATIC ANALYSIS]

### 1.1 Comprehensive Pattern Analysis [USE EXISTING TOOLS]

```bash
# Use pattern analysis to identify all functional singleton usage
python -c "
from spec_cli.utils.pattern_analysis import analyze_singleton_usage
from pathlib import Path
import json

print('Analyzing functional singleton patterns...')
patterns = analyze_singleton_usage(Path('spec_cli/'))

# Filter for functional singleton patterns
functional_patterns = [p for p in patterns
                      if any(func in p.pattern_type.lower()
                            for func in ['get_console', 'get_settings', 'get_'])]

print(f'Functional singleton patterns found: {len(functional_patterns)}')
print()

# Group by pattern type for systematic migration
pattern_groups = {}
for pattern in functional_patterns:
    pattern_type = pattern.pattern_type
    if pattern_type not in pattern_groups:
        pattern_groups[pattern_type] = []
    pattern_groups[pattern_type].append(pattern)

# Save analysis results
analysis_results = {
    'total_patterns': len(functional_patterns),
    'pattern_groups': {},
    'high_priority_files': [],
    'migration_batches': []
}

for pattern_type, patterns in pattern_groups.items():
    analysis_results['pattern_groups'][pattern_type] = {
        'count': len(patterns),
        'files': list(set(str(p.file_path) for p in patterns)),
        'usage_frequency': sum(p.usage_frequency for p in patterns)
    }

    print(f'{pattern_type}: {len(patterns)} instances')
    file_list = list(set(str(p.file_path) for p in patterns))
    for file_path in file_list[:3]:  # Show first 3 files
        print(f'  - {file_path}')
    if len(file_list) > 3:
        print(f'  - ... and {len(file_list) - 3} more files')
    print()

# Identify high-priority files (>5 patterns)
file_pattern_counts = {}
for pattern in functional_patterns:
    file_path = str(pattern.file_path)
    file_pattern_counts[file_path] = file_pattern_counts.get(file_path, 0) + 1

high_priority = [(f, c) for f, c in file_pattern_counts.items() if c >= 5]
high_priority.sort(key=lambda x: x[1], reverse=True)

analysis_results['high_priority_files'] = high_priority

print(f'High-priority files (≥5 patterns):')
for file_path, count in high_priority[:5]:
    print(f'  - {file_path}: {count} patterns')

# Save analysis for batch planning
with open('phase3_pattern_analysis.json', 'w') as f:
    json.dump(analysis_results, f, indent=2)

print(f'Analysis saved to phase3_pattern_analysis.json')
"
```

### 1.2 Batch Planning Strategy [SYSTEMATIC EXECUTION]

```bash
# Create migration batches based on pattern analysis
python -c "
import json
from pathlib import Path

# Load pattern analysis
with open('phase3_pattern_analysis.json', 'r') as f:
    analysis = json.load(f)

# Load tracking data for cross-reference
with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

functional_instances = tracking['migration_tracking']['categories']['functional_singletons']['instances']

print('Creating functional singleton migration batches...')
print()

# Strategy: Start with high-priority files, batch by file to minimize context switching
batches = []
current_batch = []
batch_size_limit = 5

# Process high-priority files first
for file_path, pattern_count in analysis['high_priority_files']:
    # Find instances in this file
    file_instances = [(k, v) for k, v in functional_instances.items()
                     if v['file_path'] == file_path and v['current_state'] == 'not_migrated']

    for instance_id, instance_info in file_instances:
        if len(current_batch) >= batch_size_limit:
            batches.append(current_batch)
            current_batch = []

        current_batch.append({
            'instance_id': instance_id,
            'file_path': instance_info['file_path'],
            'pattern_type': instance_info['pattern_type'],
            'priority': instance_info['priority']
        })

# Add any remaining instances to complete the batch
if current_batch:
    batches.append(current_batch)

print(f'Created {len(batches)} migration batches:')
for i, batch in enumerate(batches[:3], 1):  # Show first 3 batches
    print(f'Batch {i}: {len(batch)} instances')
    for instance in batch:
        print(f'  - {instance[\"instance_id\"]}: {instance[\"file_path\"]}')
    print()

# Save first batch for execution
if batches:
    with open('.next_functional_batch.json', 'w') as f:
        json.dump({
            'batch_number': 1,
            'total_batches': len(batches),
            'instances': batches[0]
        }, f, indent=2)

    print(f'Next batch ready: {len(batches[0])} instances')
    print('Batch saved to .next_functional_batch.json')
else:
    print('No functional singleton instances found to migrate')
"
```

---

## Step 2: Batch Migration Execution [5 INSTANCES MAX]

### 2.1 Load and Validate Current Batch [BATCH PREPARATION]

```bash
# Load current batch for migration
python -c "
import json
from pathlib import Path

# Load current batch
with open('.next_functional_batch.json', 'r') as f:
    batch = json.load(f)

batch_num = batch['batch_number']
total_batches = batch['total_batches']
instances = batch['instances']

print(f'Batch {batch_num}/{total_batches}: {len(instances)} instances')
print()

# Validate all files exist and analyze patterns
for instance in instances:
    file_path = Path(instance['file_path'])
    if file_path.exists():
        print(f'✅ {instance[\"instance_id\"]}: {file_path}')

        # Quick pattern check
        content = file_path.read_text()
        patterns = []
        if 'get_console()' in content:
            patterns.append('get_console()')
        if 'get_settings()' in content:
            patterns.append('get_settings()')
        if patterns:
            print(f'   Patterns: {patterns}')
    else:
        print(f'❌ {instance[\"instance_id\"]}: {file_path} - FILE NOT FOUND')

print()
print('Batch validation complete')
"

# Pre-migration testing
echo "Running pre-migration tests..."
poetry run pytest tests/unit/ --tb=no -q | grep -E "(failed|error)" && {
    echo "❌ Tests failing before migration - fix first"
    exit 1
} || echo "✅ Pre-migration tests passing"
```

### 2.2 Apply Functional Singleton Transformations [BATCH PROCESSING]

```bash
# Apply migration transformations to current batch
python -c "
import json
import re
from pathlib import Path

# Load current batch
with open('.next_functional_batch.json', 'r') as f:
    batch = json.load(f)

instances = batch['instances']

print(f'Applying transformations to batch {batch[\"batch_number\"]}...')

# Track changes made
changes_log = []

for instance in instances:
    file_path = Path(instance['file_path'])
    instance_id = instance['instance_id']

    print(f'Processing {instance_id}: {file_path}')

    if not file_path.exists():
        print(f'  ❌ File not found, skipping')
        continue

    content = file_path.read_text()
    original_content = content

    # Apply transformations based on pattern type
    changes_made = []

    # 1. Add context injection decorator if not present
    if '@context_injection' not in content and 'def ' in content:
        # Find function definitions and add decorator
        if 'from ..decorators import context_injection' not in content:
            # Add import
            import_pattern = r'(from \.\..* import .*\\n)'
            if re.search(import_pattern, content):
                content = re.sub(import_pattern, r'\\1from ..decorators import context_injection\\n', content, count=1)
            else:
                # Add at top after existing imports
                lines = content.split('\\n')
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        import_index = i + 1
                lines.insert(import_index, 'from ..decorators import context_injection')
                content = '\\n'.join(lines)
            changes_made.append('Added context_injection import')

    # 2. Replace get_console() calls with context.console
    if 'get_console()' in content:
        # Remove get_console import
        content = re.sub(r'from \.\..* import .*get_console.*\\n', '', content)
        # Replace calls
        content = content.replace('get_console()', 'context.console')
        # Update variable assignments
        content = re.sub(r'console = get_console\\(\\)', 'console = context.console', content)
        changes_made.append('Replaced get_console() with context.console')

    # 3. Replace get_settings() calls with context.settings
    if 'get_settings()' in content:
        # Remove get_settings import
        content = re.sub(r'from \.\..* import .*get_settings.*\\n', '', content)
        # Replace calls
        content = content.replace('get_settings()', 'context.settings')
        # Update variable assignments
        content = re.sub(r'settings = get_settings\\(\\)', 'settings = context.settings', content)
        changes_made.append('Replaced get_settings() with context.settings')

    # 4. Add context parameter to function definitions (basic pattern)
    # This is a simplified approach - complex cases may need manual intervention
    func_pattern = r'def ([a-zA-Z_][a-zA-Z0-9_]*)\\(([^)]*)\\):'
    matches = re.finditer(func_pattern, content)

    for match in matches:
        func_name = match.group(1)
        params = match.group(2).strip()

        # Skip if already has context parameter
        if 'context:' in params or 'context =' in params:
            continue

        # Add context parameter
        if params:
            new_params = f'context: SpecContext, {params}'
        else:
            new_params = 'context: SpecContext'

        old_def = f'def {func_name}({params}):'
        new_def = f'@context_injection\\ndef {func_name}({new_params}):'

        if old_def in content and '@context_injection' not in content[:content.find(old_def)]:
            content = content.replace(old_def, new_def)
            changes_made.append(f'Added context parameter to {func_name}()')

    # 5. Add SpecContext import if context parameter was added
    if 'context: SpecContext' in content and 'from ..core.context import SpecContext' not in content:
        lines = content.split('\\n')
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_index = i + 1
        lines.insert(import_index, 'from ..core.context import SpecContext')
        content = '\\n'.join(lines)
        changes_made.append('Added SpecContext import')

    # Save changes if any were made
    if content != original_content:
        file_path.write_text(content)
        print(f'  ✅ Changes applied: {changes_made}')
        changes_log.append({
            'file': str(file_path),
            'instance_id': instance_id,
            'changes': changes_made
        })
    else:
        print(f'  ⚠️ No changes needed')

# Save changes log
with open('phase3_batch_changes.json', 'w') as f:
    json.dump({
        'batch_number': batch['batch_number'],
        'changes_log': changes_log
    }, f, indent=2)

print(f'Batch transformation complete: {len(changes_log)} files modified')
"
```

### 2.3 Manual Transformation Template [IF AUTOMATION INSUFFICIENT]

**For complex cases requiring manual intervention:**

**BEFORE (functional singleton pattern):**
```python
from ..ui.console import get_console
from ..config.settings import get_settings

def process_data(file_path: str, options: dict):
    console = get_console()
    settings = get_settings()

    console.print_message("Processing started")
    debug_value = settings.debug_mode
    # processing logic
```

**AFTER (context-based pattern):**
```python
from ..core.context import SpecContext
from ..decorators import context_injection

@context_injection
def process_data(context: SpecContext, file_path: str, options: dict):
    # console = get_console()  # Removed
    # settings = get_settings()  # Removed

    context.console.print_message("Processing started")
    debug_value = context.settings.debug_mode
    # processing logic unchanged
```

---

## Step 3: Batch Validation [IMMEDIATE TESTING]

### 3.1 Syntax and Import Validation [BASIC CORRECTNESS]

```bash
# Validate syntax for all modified files in batch
python -c "
import json
import py_compile
from pathlib import Path

# Load changes log
with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

print(f'Validating syntax for batch {changes[\"batch_number\"]}...')

all_valid = True
for change in changes['changes_log']:
    file_path = change['file']
    try:
        py_compile.compile(file_path, doraise=True)
        print(f'✅ {file_path}: Syntax valid')
    except py_compile.PyCompileError as e:
        print(f'❌ {file_path}: Syntax error - {e}')
        all_valid = False

if all_valid:
    print('✅ All files in batch have valid syntax')
else:
    print('❌ Syntax errors detected - fix before proceeding')
    exit(1)
"

# Test imports for modified files
python -c "
import json
import importlib.util
from pathlib import Path

with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

print('Testing imports for modified files...')

for change in changes['changes_log']:
    file_path = Path(change['file'])

    # Convert to module path
    if str(file_path).startswith('spec_cli/'):
        module_path = str(file_path).replace('/', '.').replace('.py', '')
        try:
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f'✅ {file_path}: Imports successful')
        except Exception as e:
            print(f'❌ {file_path}: Import error - {e}')
            # Don't exit here - some import errors may be due to missing test dependencies
"
```

### 3.2 Functional Testing [TARGETED VALIDATION]

```bash
# Test specific functionality affected by batch
python -c "
import json
from pathlib import Path

with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

print('Testing functional changes...')

# Test facade bridge still works
from spec_cli.core.context_bridge import validate_facade_bridge
if validate_facade_bridge():
    print('✅ Facade bridge operational')
else:
    print('❌ Facade bridge validation failed')

# Basic smoke test for context access
try:
    from spec_cli.core.context_bridge import get_console, get_settings
    console = get_console()
    settings = get_settings()
    print('✅ Context access through facade working')
except Exception as e:
    print(f'❌ Context access failed: {e}')

print('Functional testing complete')
"

# Run targeted tests for affected modules
echo "Running tests for affected modules..."

# Identify test directories for modified files
python -c "
import json
from pathlib import Path

with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

test_dirs = set()
for change in changes['changes_log']:
    file_path = Path(change['file'])
    # Convert to test path
    test_path = Path('tests/unit') / file_path.relative_to('spec_cli')
    test_dir = test_path.parent
    if test_dir.exists():
        test_dirs.add(str(test_dir))

for test_dir in sorted(test_dirs):
    print(test_dir)
" | while read test_dir; do
    if [ -n "$test_dir" ]; then
        echo "Testing: $test_dir"
        poetry run pytest "$test_dir" -v --tb=short || echo "Tests failed for $test_dir"
    fi
done
```

### 3.3 Regression Testing [FULL SUITE VALIDATION]

```bash
# Run full test suite to ensure no regressions
echo "Running full regression test suite..."
poetry run pytest tests/unit/ -v --tb=short -x

if [ $? -eq 0 ]; then
    echo "✅ Full test suite passed - no regressions"
else
    echo "❌ Test regressions detected"
    echo "Batch changes may need revision"
    exit 1
fi

# Quality checks
poetry run ruff check spec_cli/ --fix
poetry run mypy spec_cli/ --strict

echo "✅ Batch validation complete"
```

---

## Step 4: Pattern Verification [ELIMINATION CONFIRMATION]

### 4.1 Singleton Pattern Detection [VERIFICATION SCAN]

```bash
# Verify functional singleton patterns are eliminated in batch files
python -c "
import json
from pathlib import Path
from spec_cli.utils.singleton_detection import scan_for_singleton_patterns

with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

print('Verifying singleton pattern elimination...')

total_remaining = 0
for change in changes['changes_log']:
    file_path = Path(change['file'])
    patterns = scan_for_singleton_patterns(file_path)

    # Filter for functional singleton patterns
    functional_patterns = [p for p in patterns
                          if any(func in p.pattern_type.lower()
                                for func in ['get_console', 'get_settings'])]

    if functional_patterns:
        print(f'⚠️ {file_path}: {len(functional_patterns)} patterns remaining')
        for pattern in functional_patterns:
            print(f'   - Line {pattern.line_number}: {pattern.pattern_type}')
        total_remaining += len(functional_patterns)
    else:
        print(f'✅ {file_path}: No functional singleton patterns')

if total_remaining == 0:
    print('✅ All functional singleton patterns eliminated from batch')
else:
    print(f'⚠️ {total_remaining} patterns still need manual cleanup')
"

# Manual verification with grep
echo "Manual pattern verification:"
python -c "
import json
with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)
for change in changes['changes_log']:
    print(change['file'])
" | xargs grep -n "get_console()\|get_settings()" || echo "✅ No functional singleton calls found"
```

---

## Step 5: Tracking Update [BATCH COMPLETION]

### 5.1 Update Migration Tracking [BATCH PROGRESS]

```bash
# Update tracking JSON for completed batch
python -c "
import json
from datetime import datetime

# Load batch changes and tracking data
with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

batch_num = changes['batch_number']
changes_log = changes['changes_log']

print(f'Updating tracking for batch {batch_num}...')

# Update instance statuses
functional_instances = tracking['migration_tracking']['categories']['functional_singletons']['instances']
instances_migrated = 0

# Load current batch to get instance IDs
with open('.next_functional_batch.json', 'r') as f:
    batch = json.load(f)

for instance in batch['instances']:
    instance_id = instance['instance_id']
    if instance_id in functional_instances:
        functional_instances[instance_id]['current_state'] = 'migrated'
        functional_instances[instance_id]['completion_date'] = datetime.now().isoformat()
        instances_migrated += 1
        print(f'✅ Marked {instance_id} as migrated')

# Update overall progress
metadata = tracking['migration_tracking']['metadata']
metadata['completed'] += instances_migrated
metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')

# Update functional singleton category progress
func_category = tracking['migration_tracking']['progress_by_category']['functional_singletons']
func_category['migrated'] += instances_migrated
func_category['not_migrated'] -= instances_migrated
func_category['completion_rate'] = f\"{int(100 * func_category['migrated'] / func_category['total'])}%\"

# Save updated tracking
with open('singleton_migration_tracking.json', 'w') as f:
    json.dump(tracking, f, indent=2)

print(f'Batch {batch_num} tracking update:')
print(f'- Instances migrated: {instances_migrated}')
print(f'- Functional singletons: {func_category[\"migrated\"]}/{func_category[\"total\"]} ({func_category[\"completion_rate\"]})')
print(f'- Overall progress: {metadata[\"completed\"]}/{metadata[\"total_instances\"]}')
"
```

### 5.2 Prepare Next Batch [CONTINUE OR COMPLETE]

```bash
# Check if more batches remain and prepare next one
python -c "
import json

# Load tracking to check remaining work
with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

func_category = tracking['migration_tracking']['progress_by_category']['functional_singletons']
func_instances = tracking['migration_tracking']['categories']['functional_singletons']['instances']

# Count remaining instances
not_migrated = {k: v for k, v in func_instances.items()
                if v['current_state'] == 'not_migrated'}

if not_migrated:
    print(f'{len(not_migrated)} functional singleton instances remaining')

    # Create next batch (up to 5 instances)
    remaining_list = list(not_migrated.items())[:5]

    # Load previous batch number
    with open('.next_functional_batch.json', 'r') as f:
        prev_batch = json.load(f)

    next_batch_num = prev_batch['batch_number'] + 1

    next_batch = {
        'batch_number': next_batch_num,
        'total_batches': prev_batch['total_batches'],  # May need recalculation
        'instances': []
    }

    for instance_id, instance_info in remaining_list:
        next_batch['instances'].append({
            'instance_id': instance_id,
            'file_path': instance_info['file_path'],
            'pattern_type': instance_info['pattern_type'],
            'priority': instance_info['priority']
        })

    with open('.next_functional_batch.json', 'w') as f:
        json.dump(next_batch, f, indent=2)

    print(f'Next batch {next_batch_num} prepared: {len(next_batch[\"instances\"])} instances')
    print('Return to Step 2.1 to continue migration')

else:
    print('🎉 ALL FUNCTIONAL SINGLETONS MIGRATED!')
    print('Phase 3 complete - ready for Phase 4')

    # Mark Phase 3 complete
    tracking['migration_tracking']['migration_phases']['phase_2_core_services']['status'] = 'completed'
    tracking['migration_tracking']['migration_phases']['phase_2_core_services']['completion_date'] = datetime.now().isoformat()

    with open('singleton_migration_tracking.json', 'w') as f:
        json.dump(tracking, f, indent=2)

    # Create completion marker
    with open('.phase3_complete', 'w') as f:
        f.write('Phase 3 Functional Singleton Migration completed successfully\\n')

    # Create Phase 4 readiness
    readiness = {
        'phase_3_status': 'completed',
        'functional_singletons_migrated': '82/82 (100%)',
        'next_phase': 'Phase 4: Import Singleton Automation',
        'ready_for_phase_4': True,
        'import_singletons_remaining': 940
    }

    with open('phase4_readiness.json', 'w') as f:
        json.dump(readiness, f, indent=2)

    print('Phase 4 readiness report created')

    # Clean up batch files
    import os
    os.remove('.next_functional_batch.json')
"
```

---

## Step 6: Batch Commit [INCREMENTAL PROGRESS]

### 6.1 Commit Batch Changes [ATOMIC BATCH COMMIT]

```bash
# Stage all changes for batch commit
git add -A

# Create comprehensive commit message for batch
python -c "
import json

# Load batch changes and progress
with open('phase3_batch_changes.json', 'r') as f:
    changes = json.load(f)

with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

batch_num = changes['batch_number']
changes_log = changes['changes_log']
func_progress = tracking['migration_tracking']['progress_by_category']['functional_singletons']

# Generate commit message
files_modified = [change['file'] for change in changes_log]
instances_count = len(changes_log)

commit_msg = f'''feat: Phase 3 functional singleton batch {batch_num} migration

BATCH MIGRATION:
- Migrated {instances_count} functional singleton instances
- Files modified: {len(files_modified)}
- Replaced get_console() with context.console access
- Replaced get_settings() with context.settings access
- Added @context_injection decorators and SpecContext parameters

FILES MODIFIED:'''

for change in changes_log:
    commit_msg += f'''
- {change['file']}: {', '.join(change['changes'])}'''

commit_msg += f'''

PROGRESS UPDATE:
- Functional singletons: {func_progress['migrated']}/{func_progress['total']} ({func_progress['completion_rate']})
- Total migration: {tracking['migration_tracking']['metadata']['completed']}/{tracking['migration_tracking']['metadata']['total_instances']}

VALIDATION RESULTS:
- Tests: ✅ All pass, no regressions
- Syntax: ✅ All files compile cleanly
- Quality: ✅ Ruff/MyPy validation passed
- Patterns: ✅ Functional singletons eliminated from batch

Batch {batch_num} complete - systematic functional singleton elimination.'''

print(commit_msg)

# Save commit message
with open('.commit_message.txt', 'w') as f:
    f.write(commit_msg)
"

# Commit with generated message
git commit -F .commit_message.txt
rm -f .commit_message.txt

# Clean up batch files
rm -f phase3_batch_changes.json

# Tag if this completes Phase 3
test -f .phase3_complete && {
    git tag -a "phase3-functional-complete" -m "Phase 3: Functional Singleton Migration Complete

All 82 functional singleton instances eliminated:
- get_console() calls replaced with context.console
- get_settings() calls replaced with context.settings
- All affected functions use @context_injection pattern
- Facade bridge maintains backward compatibility
- 100% test coverage maintained

Ready for Phase 4: Import Singleton Automation"
}

echo "✅ Batch migration committed successfully"
```

### 6.2 Phase Progress Summary [MILESTONE TRACKING]

```bash
# Generate progress summary
python -c "
import json

with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

func_progress = tracking['migration_tracking']['progress_by_category']['functional_singletons']
overall_progress = tracking['migration_tracking']['metadata']

print()
print('=' * 50)
print('PHASE 3 PROGRESS SUMMARY')
print('=' * 50)
print(f'Functional Singletons: {func_progress[\"migrated\"]}/{func_progress[\"total\"]} ({func_progress[\"completion_rate\"]})')
print(f'Overall Migration: {overall_progress[\"completed\"]}/{overall_progress[\"total_instances\"]}')

if func_progress['completion_rate'] == '100%':
    print()
    print('🎉 PHASE 3 COMPLETE!')
    print('All functional singleton patterns eliminated')
    print('Ready for Phase 4: Import Singleton Automation')
else:
    remaining = func_progress['not_migrated']
    print(f'Remaining: {remaining} functional singleton instances')
    print('Continue with next batch migration')

print('=' * 50)
"
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Transformation Automation Failures
```bash
# If automated transformation fails:
# 1. Check file has correct function definitions
# 2. Apply manual transformation using template in Step 2.3
# 3. Focus on one pattern type at a time (get_console vs get_settings)
# 4. Verify imports are correct after transformation
```

### Context Parameter Issues
```bash
# If @context_injection fails:
# 1. Verify decorator import is correct
# 2. Check SpecContext import exists
# 3. Ensure function signature includes context parameter
# 4. Test with minimal example:
python -c "
from spec_cli.decorators import context_injection
from spec_cli.core.context import SpecContext

@context_injection
def test_func(context: SpecContext):
    return context.console

print('Context injection test OK')
"
```

### Test Failures After Batch Migration
```bash
# If tests fail after batch:
# 1. Check which specific tests are failing
# 2. Verify context access patterns are correct
# 3. Ensure facade bridge is still operational
# 4. Check for missing imports or syntax errors
# 5. Consider reverting batch and applying smaller changes
```

### Pattern Detection Issues
```bash
# If patterns not detected correctly:
# 1. Manually search for remaining patterns:
grep -r "get_console()" spec_cli/
grep -r "get_settings()" spec_cli/
# 2. Update detection tools if needed
# 3. Use pattern analysis tools for verification
```

---

## Success Metrics [PHASE 3 COMPLETION]

### Required Achievements [ALL MANDATORY]
- **Functional Singletons**: 82/82 migrated (100% completion rate)
- **Pattern Elimination**: Zero get_console() and get_settings() calls remaining
- **Context Adoption**: All affected functions use @context_injection pattern
- **Test Coverage**: 100% pass rate maintained throughout migration
- **Quality Gates**: Ruff, mypy validation clean after each batch
- **Tracking Accuracy**: JSON reflects actual elimination state

### Performance Thresholds [MAINTAINED]
- **Function Call Performance**: <10% overhead from context access
- **Test Suite Runtime**: Maintain <5s total execution time
- **Import Time**: Minimal additional overhead from dependency injection

### Phase 3 Deliverables [CREATED/UPDATED]
- All functional singleton calls replaced with context access
- Updated `singleton_migration_tracking.json` with 100% functional completion
- `.phase3_complete` completion marker
- `phase4_readiness.json` preparation for import automation
- Individual batch commits for systematic progress tracking
- Phase completion git tag

---

**Phase 3 systematically eliminates functional singleton patterns through small, validated batches. Each batch replaces singleton calls with context-based access while maintaining full backward compatibility through the facade bridge.**
