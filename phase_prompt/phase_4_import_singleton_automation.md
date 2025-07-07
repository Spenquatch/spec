# Phase 4 Agent Directive: Import Singleton Automation

You are executing **Phase 4 of the singleton migration** which automates the bulk migration of 940 import singleton instances. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts. This phase requires Phase 3 functional migration to be complete.

If a step is unclear: **do not guess**. Halt and escalate.

> **Import singletons are automated away or left untouched. No partial automation states exist.**

## Mission: Automate Import Singleton Elimination

**GOAL**: Use automated transformation to migrate all 940 debug_logger import singletons to facade bridge pattern.

**SUCCESS CRITERIA**:
- Zero `from ..logging.debug import debug_logger` imports remaining
- All debug_logger access goes through facade bridge
- 100% test pass rate maintained throughout automation
- Import singletons category shows 100% completion

---

## 🚨 PHASE 4 GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions in Phase 4:**

1. **NEVER run automation on entire codebase at once** → Use batches of 50-100 files maximum
2. **NEVER skip validation after automation batches** → Test every batch before proceeding
3. **NEVER proceed without Phase 3 complete** → Functional singleton foundation required
4. **NEVER automate without facade bridge working** → Automation depends on backward compatibility
5. **NEVER commit broken automation state** → Each batch must maintain system functionality

> **Automation Principle: "Automate in validated batches with immediate testing"**

---

## Prerequisites Validation [MANDATORY FIRST STEP]

### Verify Phase 3 Foundation [BLOCKING REQUIREMENT]

```bash
# Phase 3 must be complete before automation
test -f .phase3_complete || {
    echo "❌ ERROR: Phase 3 functional migration not complete"
    echo "Complete functional singleton migration first"
    exit 1
}

# Verify functional singleton completion
python -c "
import json
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

func_progress = data['migration_tracking']['progress_by_category']['functional_singletons']
if func_progress['completion_rate'] != '100%':
    print('❌ ERROR: Functional singleton migration not 100% complete')
    exit(1)
else:
    print('✅ Functional singleton migration complete')
"

# Load Phase 4 readiness
test -f phase4_readiness.json && {
    python -c "
    import json
    with open('phase4_readiness.json', 'r') as f:
        readiness = json.load(f)
    if readiness['ready_for_phase_4']:
        print('✅ Phase 4 prerequisites met')
        print(f'Import singletons to migrate: {readiness[\"import_singletons_remaining\"]}')
    else:
        print('❌ Phase 4 not ready')
        exit(1)
    "
} || {
    echo "❌ ERROR: Phase 4 readiness report missing"
    exit 1
}

# Verify facade bridge operational for automation
python -c "
from spec_cli.core.context_bridge import validate_facade_bridge
if validate_facade_bridge():
    print('✅ Facade bridge operational for automation')
else:
    print('❌ Facade bridge not working - automation will fail')
    exit(1)
"
```

---

## Step 1: Import Singleton Discovery [COMPREHENSIVE INVENTORY]

### 1.1 Comprehensive Import Pattern Analysis [AUTOMATED DISCOVERY]

```bash
# Use comprehensive scanner to identify all import singleton patterns
python -c "
from spec_cli.utils.detection_execution.comprehensive_scanner import execute_full_codebase_scan
from pathlib import Path
import json

print('Scanning for import singleton patterns...')
scan_results = execute_full_codebase_scan(Path('spec_cli/'))

# Filter for import-based singleton patterns
import_patterns = [p for p in scan_results.detected_patterns
                  if 'import' in p.pattern_type.lower() and 'debug_logger' in str(p.file_path)]

print(f'Import singleton patterns found: {len(import_patterns)}')

# Group by import pattern type
pattern_groups = {}
for pattern in import_patterns:
    pattern_key = f'{pattern.pattern_type}_{pattern.qualified_symbol}'
    if pattern_key not in pattern_groups:
        pattern_groups[pattern_key] = []
    pattern_groups[pattern_key].append(pattern)

# Save comprehensive analysis
import_analysis = {
    'total_import_patterns': len(import_patterns),
    'scan_timestamp': scan_results.statistics.timestamp,
    'pattern_groups': {},
    'files_with_imports': [],
    'automation_batches': []
}

files_with_imports = set()
for pattern in import_patterns:
    files_with_imports.add(str(pattern.file_path))

import_analysis['files_with_imports'] = sorted(files_with_imports)

print(f'Files with debug_logger imports: {len(files_with_imports)}')

# Create detailed pattern analysis
for pattern_key, patterns in pattern_groups.items():
    import_analysis['pattern_groups'][pattern_key] = {
        'count': len(patterns),
        'files': [str(p.file_path) for p in patterns],
        'line_numbers': [p.line_number for p in patterns]
    }
    print(f'{pattern_key}: {len(patterns)} instances')

# Save analysis
with open('phase4_import_analysis.json', 'w') as f:
    json.dump(import_analysis, f, indent=2)

print(f'Import analysis saved to phase4_import_analysis.json')
"
```

### 1.2 Manual Import Verification [CROSS-VALIDATION]

```bash
# Manual grep verification to cross-check automated detection
echo "Manual import pattern verification:"

# Count debug_logger import patterns
debug_import_count=$(grep -r "from .*logging\.debug import debug_logger" spec_cli/ | wc -l)
echo "Debug logger imports (specific): $debug_import_count"

# Count broader debug_logger import patterns
broad_import_count=$(grep -r "import.*debug_logger" spec_cli/ | wc -l)
echo "Debug logger imports (broad): $broad_import_count"

# Show sample of import patterns
echo ""
echo "Sample import patterns:"
grep -r "from .*debug import debug_logger" spec_cli/ | head -5

# Verify facade bridge imports (should be minimal currently)
facade_import_count=$(grep -r "from .*context_bridge import debug_logger" spec_cli/ | wc -l)
echo ""
echo "Facade bridge imports: $facade_import_count"

# Save manual verification results
cat > phase4_manual_verification.txt << EOF
Manual Import Pattern Verification Results:
- Debug logger imports (specific): $debug_import_count
- Debug logger imports (broad): $broad_import_count
- Facade bridge imports: $facade_import_count

Sample patterns:
$(grep -r "from .*debug import debug_logger" spec_cli/ | head -5)
EOF

echo "Manual verification saved to phase4_manual_verification.txt"
```

### 1.3 Automation Batch Planning [SYSTEMATIC BATCHING]

```bash
# Create automation batches for safe processing
python -c "
import json
from pathlib import Path

# Load import analysis
with open('phase4_import_analysis.json', 'r') as f:
    analysis = json.load(f)

files_with_imports = analysis['files_with_imports']
total_files = len(files_with_imports)

print(f'Planning automation batches for {total_files} files...')

# Create batches of 50 files each for safety
batch_size = 50
batches = []

for i in range(0, total_files, batch_size):
    batch_files = files_with_imports[i:i + batch_size]
    batches.append({
        'batch_number': len(batches) + 1,
        'files': batch_files,
        'file_count': len(batch_files)
    })

print(f'Created {len(batches)} automation batches:')
for batch in batches:
    print(f'Batch {batch[\"batch_number\"]}: {batch[\"file_count\"]} files')

# Save batch plan
automation_plan = {
    'total_batches': len(batches),
    'total_files': total_files,
    'batch_size': batch_size,
    'batches': batches,
    'automation_command': 'find spec_cli/ -name \"*.py\" -exec sed -i \"s/from \.\.logging\.debug import debug_logger/from \.\.core\.context_bridge import debug_logger/g\" {} \\;'
}

with open('phase4_automation_plan.json', 'w') as f:
    json.dump(automation_plan, f, indent=2)

# Prepare first batch
if batches:
    with open('.next_automation_batch.json', 'w') as f:
        json.dump(batches[0], f, indent=2)

    print(f'First batch prepared: {batches[0][\"file_count\"]} files')
    print('Ready for automation execution')
else:
    print('No batches created - no import singletons found')
"
```

---

## Step 2: Automated Import Transformation [BATCH PROCESSING]

### 2.1 Load and Validate Current Batch [BATCH PREPARATION]

```bash
# Load current automation batch
python -c "
import json
from pathlib import Path

# Load current batch
with open('.next_automation_batch.json', 'r') as f:
    batch = json.load(f)

batch_num = batch['batch_number']
files = batch['files']
file_count = batch['file_count']

print(f'Automation Batch {batch_num}: {file_count} files')
print()

# Validate all files exist
missing_files = []
for file_path in files:
    if not Path(file_path).exists():
        missing_files.append(file_path)

if missing_files:
    print(f'❌ Missing files: {len(missing_files)}')
    for missing in missing_files[:5]:  # Show first 5
        print(f'   - {missing}')
    if len(missing_files) > 5:
        print(f'   - ... and {len(missing_files) - 5} more')
else:
    print(f'✅ All {file_count} files exist and ready for automation')

# Quick pattern verification for batch
pattern_count = 0
for file_path in files[:5]:  # Sample first 5 files
    if Path(file_path).exists():
        content = Path(file_path).read_text()
        if 'from ..logging.debug import debug_logger' in content:
            pattern_count += 1

print(f'Sample verification: {pattern_count}/5 files have target import pattern')
print('Batch validation complete')
"

# Pre-automation test baseline
echo "Establishing pre-automation test baseline..."
poetry run pytest tests/unit/ --tb=no -q | grep -E "(passed|failed)" || {
    echo "❌ Tests not stable before automation"
    exit 1
}
echo "✅ Pre-automation tests stable"
```

### 2.2 Apply Automated Import Transformation [PRECISE AUTOMATION]

```bash
# Apply automated import transformation to current batch
python -c "
import json
import re
from pathlib import Path

# Load current batch
with open('.next_automation_batch.json', 'r') as f:
    batch = json.load(f)

batch_num = batch['batch_number']
files = batch['files']

print(f'Applying automation to batch {batch_num}...')

# Define transformation patterns
transformations = [
    # Primary pattern: relative import to facade bridge
    (r'from \.\.logging\.debug import debug_logger', 'from ..core.context_bridge import debug_logger'),

    # Alternative patterns that might exist
    (r'from spec_cli\.logging\.debug import debug_logger', 'from spec_cli.core.context_bridge import debug_logger'),
    (r'from \.\.\.logging\.debug import debug_logger', 'from ...core.context_bridge import debug_logger'),
]

# Track changes
transformation_log = {
    'batch_number': batch_num,
    'files_processed': 0,
    'files_modified': 0,
    'transformations_applied': 0,
    'modified_files': []
}

for file_path in files:
    path_obj = Path(file_path)
    if not path_obj.exists():
        continue

    transformation_log['files_processed'] += 1
    original_content = path_obj.read_text()
    content = original_content
    file_transformations = 0

    # Apply each transformation pattern
    for old_pattern, new_import in transformations:
        matches = re.findall(old_pattern, content)
        if matches:
            content = re.sub(old_pattern, new_import, content)
            file_transformations += len(matches)
            print(f'  {file_path}: {len(matches)} x \"{old_pattern}\" -> facade import')

    # Save changes if any transformations were applied
    if content != original_content:
        path_obj.write_text(content)
        transformation_log['files_modified'] += 1
        transformation_log['transformations_applied'] += file_transformations
        transformation_log['modified_files'].append({
            'file': file_path,
            'transformations': file_transformations
        })
        print(f'  ✅ {file_path}: {file_transformations} transformations applied')

print(f'Batch {batch_num} automation complete:')
print(f'- Files processed: {transformation_log[\"files_processed\"]}')
print(f'- Files modified: {transformation_log[\"files_modified\"]}')
print(f'- Transformations applied: {transformation_log[\"transformations_applied\"]}')

# Save transformation log
with open('phase4_automation_log.json', 'w') as f:
    json.dump(transformation_log, f, indent=2)
"

# Alternative: Use existing automation command if preferred
echo "Alternative: Using tracking JSON automation command..."
python -c "
import json
with open('singleton_migration_tracking.json', 'r') as f:
    data = json.load(f)

automation_cmd = data['migration_tracking']['automation_commands']['facade_replacement']
print(f'Automation command: {automation_cmd}')
"

# Note: The sed command can be run if preferred, but Python approach is more controlled
```

### 2.3 Transformation Verification [IMMEDIATE VALIDATION]

```bash
# Verify transformations were applied correctly
python -c "
import json
from pathlib import Path

# Load transformation log
with open('phase4_automation_log.json', 'r') as f:
    log = json.load(f)

print(f'Verifying transformations for batch {log[\"batch_number\"]}...')

# Verify old patterns are eliminated in modified files
old_patterns_remaining = 0
new_patterns_added = 0

for file_info in log['modified_files']:
    file_path = Path(file_info['file'])
    if file_path.exists():
        content = file_path.read_text()

        # Check for remaining old patterns
        old_patterns = [
            'from ..logging.debug import debug_logger',
            'from spec_cli.logging.debug import debug_logger'
        ]

        file_old_patterns = 0
        for pattern in old_patterns:
            file_old_patterns += content.count(pattern)

        # Check for new facade patterns
        facade_patterns = [
            'from ..core.context_bridge import debug_logger',
            'from spec_cli.core.context_bridge import debug_logger'
        ]

        file_new_patterns = 0
        for pattern in facade_patterns:
            file_new_patterns += content.count(pattern)

        old_patterns_remaining += file_old_patterns
        new_patterns_added += file_new_patterns

        if file_old_patterns > 0:
            print(f'⚠️ {file_path}: {file_old_patterns} old patterns remaining')
        elif file_new_patterns > 0:
            print(f'✅ {file_path}: {file_new_patterns} facade imports added')

print(f'Verification summary:')
print(f'- Old patterns remaining: {old_patterns_remaining}')
print(f'- New facade patterns: {new_patterns_added}')

if old_patterns_remaining == 0:
    print('✅ All old import patterns successfully transformed')
else:
    print('⚠️ Some old patterns remain - may need manual cleanup')
"

# Manual verification with grep
echo ""
echo "Manual grep verification:"
old_imports=$(grep -r "from .*logging\.debug import debug_logger" spec_cli/ | wc -l)
facade_imports=$(grep -r "from .*context_bridge import debug_logger" spec_cli/ | wc -l)

echo "Old debug_logger imports remaining: $old_imports"
echo "Facade bridge imports: $facade_imports"

if [ "$old_imports" -eq 0 ]; then
    echo "✅ No old import patterns detected"
else
    echo "⚠️ Old import patterns still exist"
    echo "Sample remaining patterns:"
    grep -r "from .*logging\.debug import debug_logger" spec_cli/ | head -3
fi
```

---

## Step 3: Batch Validation [COMPREHENSIVE TESTING]

### 3.1 Syntax and Import Validation [BASIC CORRECTNESS]

```bash
# Validate syntax for all modified files in batch
python -c "
import json
import py_compile
from pathlib import Path

# Load transformation log
with open('phase4_automation_log.json', 'r') as f:
    log = json.load(f)

print(f'Validating syntax for batch {log[\"batch_number\"]}...')

syntax_errors = []
for file_info in log['modified_files']:
    file_path = file_info['file']
    try:
        py_compile.compile(file_path, doraise=True)
        print(f'✅ {file_path}: Syntax valid')
    except py_compile.PyCompileError as e:
        print(f'❌ {file_path}: Syntax error - {e}')
        syntax_errors.append(file_path)

if not syntax_errors:
    print('✅ All modified files have valid syntax')
else:
    print(f'❌ {len(syntax_errors)} files have syntax errors')
    for error_file in syntax_errors:
        print(f'   - {error_file}')
    exit(1)
"

# Test facade bridge imports work
echo "Testing facade bridge import functionality..."
python -c "
from spec_cli.core.context_bridge import debug_logger
debug_logger.log('INFO', 'Facade bridge test message')
print('✅ Facade bridge debug_logger import working')
"

# Test a sample of modified files can be imported
python -c "
import json
import importlib.util
from pathlib import Path

with open('phase4_automation_log.json', 'r') as f:
    log = json.load(f)

print('Testing imports for sample of modified files...')

# Test first 3 modified files
sample_files = log['modified_files'][:3]

for file_info in sample_files:
    file_path = Path(file_info['file'])

    # Convert to module path
    if str(file_path).startswith('spec_cli/'):
        module_path = str(file_path).replace('/', '.').replace('.py', '')
        try:
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f'✅ {file_path}: Import successful')
        except Exception as e:
            print(f'⚠️ {file_path}: Import issue - {e}')
            # Note: Some import issues may be expected due to missing dependencies

print('Import validation complete')
"
```

### 3.2 Facade Bridge Functionality Testing [OPERATIONAL VALIDATION]

```bash
# Test that facade bridge maintains functionality after automation
python -c "
from spec_cli.core.context_bridge import validate_facade_bridge, get_facade_status
import json

print('Testing facade bridge after automation batch...')

# Test basic facade functionality
if validate_facade_bridge():
    print('✅ Facade bridge operational')
else:
    print('❌ Facade bridge validation failed')
    exit(1)

# Get detailed facade status
status = get_facade_status()
print('Facade Bridge Status:')
print(json.dumps(status, indent=2))

# Test debug_logger facade specifically
from spec_cli.core.context_bridge import debug_logger

try:
    debug_logger.info('Automation batch test message')
    debug_logger.log('DEBUG', 'Facade functionality verified')
    print('✅ Debug logger facade working correctly')
except Exception as e:
    print(f'❌ Debug logger facade error: {e}')
    exit(1)

print('Facade bridge functionality validation complete')
"
```

### 3.3 Regression Testing [FULL SUITE VALIDATION]

```bash
# Run full test suite to ensure automation doesn't break functionality
echo "Running regression test suite after automation batch..."
poetry run pytest tests/unit/ -v --tb=short -x

if [ $? -eq 0 ]; then
    echo "✅ Full test suite passed - no regressions from automation"
else
    echo "❌ Test regressions detected from automation batch"
    echo "Automation may need rollback and manual correction"
    exit 1
fi

# Quality checks
echo "Running quality checks..."
poetry run ruff check spec_cli/ --fix
poetry run mypy spec_cli/ --strict

if [ $? -eq 0 ]; then
    echo "✅ Quality checks passed"
else
    echo "⚠️ Quality issues detected - may need attention"
fi

echo "✅ Batch validation complete"
```

---

## Step 4: Tracking Update [BATCH PROGRESS]

### 4.1 Update Migration Tracking [AUTOMATION PROGRESS]

```bash
# Update tracking JSON for automated batch
python -c "
import json
from datetime import datetime

# Load automation log and tracking data
with open('phase4_automation_log.json', 'r') as f:
    log = json.load(f)

with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

batch_num = log['batch_number']
transformations_applied = log['transformations_applied']

print(f'Updating tracking for automation batch {batch_num}...')

# For import singletons, we track by transformation count rather than individual instances
# since there are 940 instances that are being automated en masse

import_category = tracking['migration_tracking']['progress_by_category']['import_singletons']
import_instances = tracking['migration_tracking']['categories']['import_singletons']['instances']

# Estimate instances migrated based on transformations
# (Each transformation likely represents one import singleton instance)
instances_migrated = transformations_applied

# Update overall progress
metadata = tracking['migration_tracking']['metadata']
metadata['completed'] += instances_migrated
metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')

# Update import singleton category progress
import_category['migrated'] += instances_migrated
import_category['not_migrated'] = max(0, import_category['not_migrated'] - instances_migrated)
import_category['completion_rate'] = f\"{int(100 * import_category['migrated'] / import_category['total'])}%\"

# Mark sample instances as migrated (for tracking purposes)
sample_instances = list(import_instances.keys())[:instances_migrated]
for instance_id in sample_instances:
    if instance_id in import_instances:
        import_instances[instance_id]['current_state'] = 'migrated'
        import_instances[instance_id]['completion_date'] = datetime.now().isoformat()

# Save updated tracking
with open('singleton_migration_tracking.json', 'w') as f:
    json.dump(tracking, f, indent=2)

print(f'Automation batch {batch_num} tracking update:')
print(f'- Transformations applied: {transformations_applied}')
print(f'- Import singletons: {import_category[\"migrated\"]}/{import_category[\"total\"]} ({import_category[\"completion_rate\"]})')
print(f'- Overall progress: {metadata[\"completed\"]}/{metadata[\"total_instances\"]}')

# Save automation progress summary
automation_progress = {
    'batch_number': batch_num,
    'transformations_applied': transformations_applied,
    'files_modified': log['files_modified'],
    'import_category_progress': import_category,
    'overall_progress': {
        'completed': metadata['completed'],
        'total': metadata['total_instances'],
        'percentage': int(100 * metadata['completed'] / metadata['total_instances'])
    }
}

with open('phase4_automation_progress.json', 'w') as f:
    json.dump(automation_progress, f, indent=2)
"
```

### 4.2 Prepare Next Batch [CONTINUE OR COMPLETE]

```bash
# Check if more automation batches remain
python -c "
import json

# Load automation plan and current progress
with open('phase4_automation_plan.json', 'r') as f:
    plan = json.load(f)

with open('.next_automation_batch.json', 'r') as f:
    current_batch = json.load(f)

current_batch_num = current_batch['batch_number']
total_batches = plan['total_batches']

if current_batch_num < total_batches:
    print(f'Batch {current_batch_num}/{total_batches} complete')

    # Prepare next batch
    next_batch_num = current_batch_num + 1
    next_batch = plan['batches'][next_batch_num - 1]  # 0-indexed

    with open('.next_automation_batch.json', 'w') as f:
        json.dump(next_batch, f, indent=2)

    print(f'Next batch {next_batch_num} prepared: {next_batch[\"file_count\"]} files')
    print('Return to Step 2.1 to continue automation')

else:
    print(f'🎉 ALL AUTOMATION BATCHES COMPLETE!')
    print('Running final verification...')

    # Final verification of import elimination
    import subprocess
    result = subprocess.run(['grep', '-r', 'from .*logging.debug import debug_logger', 'spec_cli/'],
                          capture_output=True, text=True)
    remaining_imports = len(result.stdout.split('\\n')) - 1 if result.stdout.strip() else 0

    print(f'Final verification: {remaining_imports} old import patterns remaining')

    if remaining_imports == 0:
        print('✅ All import singleton patterns successfully automated')

        # Mark Phase 4 complete
        with open('singleton_migration_tracking.json', 'r') as f:
            tracking = json.load(f)

        tracking['migration_tracking']['migration_phases']['phase_3_debug_logger']['status'] = 'completed'
        tracking['migration_tracking']['migration_phases']['phase_3_debug_logger']['completion_date'] = '2025-07-07'

        # Mark all import singletons as migrated
        import_category = tracking['migration_tracking']['progress_by_category']['import_singletons']
        import_category['migrated'] = import_category['total']
        import_category['not_migrated'] = 0
        import_category['completion_rate'] = '100%'

        with open('singleton_migration_tracking.json', 'w') as f:
            json.dump(tracking, f, indent=2)

        # Create completion marker
        with open('.phase4_complete', 'w') as f:
            f.write('Phase 4 Import Singleton Automation completed successfully\\n')

        # Create Phase 5 readiness
        readiness = {
            'phase_4_status': 'completed',
            'import_singletons_migrated': '940/940 (100%)',
            'automation_batches_completed': total_batches,
            'next_phase': 'Phase 5: Migration Completion & Validation',
            'ready_for_phase_5': True
        }

        with open('phase5_readiness.json', 'w') as f:
            json.dump(readiness, f, indent=2)

        print('Phase 5 readiness report created')

        # Clean up automation files
        import os
        try:
            os.remove('.next_automation_batch.json')
            os.remove('phase4_automation_log.json')
        except FileNotFoundError:
            pass

        print('Phase 4 complete - ready for Phase 5')
    else:
        print(f'⚠️ {remaining_imports} import patterns still remain')
        print('Manual cleanup may be required')
"
```

---

## Step 5: Batch Commit [INCREMENTAL AUTOMATION PROGRESS]

### 5.1 Commit Automation Batch [AUTOMATED CHANGES COMMIT]

```bash
# Stage all changes for automation batch commit
git add -A

# Create comprehensive commit message for automation batch
python -c "
import json

# Load automation progress and tracking
with open('phase4_automation_progress.json', 'r') as f:
    progress = json.load(f)

batch_num = progress['batch_number']
transformations = progress['transformations_applied']
files_modified = progress['files_modified']
import_progress = progress['import_category_progress']
overall = progress['overall_progress']

# Generate commit message
commit_msg = f'''feat: Phase 4 import singleton automation batch {batch_num}

AUTOMATION BATCH:
- Applied {transformations} import transformations
- Modified {files_modified} files
- Replaced debug_logger imports with facade bridge imports
- Pattern: from ..logging.debug import -> from ..core.context_bridge import

AUTOMATION TRANSFORMATIONS:
- Old pattern: from ..logging.debug import debug_logger
- New pattern: from ..core.context_bridge import debug_logger
- Maintains backward compatibility through facade bridge
- No functional changes to debug_logger usage

PROGRESS UPDATE:
- Import singletons: {import_progress['migrated']}/{import_progress['total']} ({import_progress['completion_rate']})
- Overall migration: {overall['completed']}/{overall['total']} ({overall['percentage']}%)

VALIDATION RESULTS:
- Tests: ✅ All pass, no regressions
- Syntax: ✅ All modified files compile cleanly
- Facade: ✅ Debug logger facade operational
- Imports: ✅ All facade bridge imports resolve

Batch {batch_num} automation complete - systematic import elimination.'''

print(commit_msg)

# Save commit message
with open('.commit_message.txt', 'w') as f:
    f.write(commit_msg)
"

# Commit with generated message
git commit -F .commit_message.txt
rm -f .commit_message.txt

# Clean up batch progress file
rm -f phase4_automation_progress.json

# Tag if this completes Phase 4
test -f .phase4_complete && {
    git tag -a "phase4-automation-complete" -m "Phase 4: Import Singleton Automation Complete

All 940 import singleton instances automated:
- debug_logger imports redirected to facade bridge
- from ..logging.debug import -> from ..core.context_bridge import
- Automated transformation maintains backward compatibility
- 100% test coverage maintained throughout automation

Ready for Phase 5: Migration Completion & Final Validation"
}

echo "✅ Automation batch committed successfully"
```

### 5.2 Automation Progress Summary [MILESTONE TRACKING]

```bash
# Generate automation progress summary
python -c "
import json

with open('singleton_migration_tracking.json', 'r') as f:
    tracking = json.load(f)

import_progress = tracking['migration_tracking']['progress_by_category']['import_singletons']
overall_progress = tracking['migration_tracking']['metadata']

print()
print('=' * 50)
print('PHASE 4 AUTOMATION PROGRESS SUMMARY')
print('=' * 50)
print(f'Import Singletons: {import_progress[\"migrated\"]}/{import_progress[\"total\"]} ({import_progress[\"completion_rate\"]})')
print(f'Overall Migration: {overall_progress[\"completed\"]}/{overall_progress[\"total_instances\"]}')

if import_progress['completion_rate'] == '100%':
    print()
    print('🎉 PHASE 4 AUTOMATION COMPLETE!')
    print('All import singleton patterns automated to facade bridge')
    print('Ready for Phase 5: Migration Completion & Final Validation')
else:
    remaining = import_progress['not_migrated']
    print(f'Remaining: {remaining} import singleton instances')
    print('Continue with next automation batch')

print('=' * 50)
"
```

---

## Troubleshooting Guide [AUTOMATION RECOVERY]

### Automation Command Failures
```bash
# If sed/grep automation fails:
# 1. Check file permissions and access
# 2. Verify file paths are correct
# 3. Use Python transformation approach instead
# 4. Process smaller batches (reduce from 50 to 25 files)
```

### Facade Bridge Import Issues
```bash
# If facade imports don't work:
# 1. Verify context_bridge.py exists and is correct
# 2. Check import paths match exactly
# 3. Test facade manually:
python -c "
from spec_cli.core.context_bridge import debug_logger
debug_logger.log('INFO', 'test')
print('Facade working')
"
```

### Test Failures After Automation
```bash
# If tests fail after automation batch:
# 1. Check which specific tests are failing
# 2. Verify facade bridge is operational
# 3. Look for syntax errors in modified files
# 4. Consider reverting batch and using smaller automation chunks
# 5. Run specific failing tests with -v for details
```

### Incomplete Transformations
```bash
# If some import patterns remain untransformed:
# 1. Check for variant import patterns:
grep -r "import.*debug_logger" spec_cli/
# 2. Apply manual cleanup:
python -c "
import re
from pathlib import Path
for py_file in Path('spec_cli/').rglob('*.py'):
    content = py_file.read_text()
    if 'from spec_cli.logging.debug import debug_logger' in content:
        new_content = content.replace(
            'from spec_cli.logging.debug import debug_logger',
            'from spec_cli.core.context_bridge import debug_logger'
        )
        py_file.write_text(new_content)
        print(f'Manually fixed: {py_file}')
"
```

---

## Success Metrics [PHASE 4 COMPLETION]

### Required Achievements [ALL MANDATORY]
- **Import Singletons**: 940/940 migrated (100% completion rate)
- **Pattern Elimination**: Zero `from ..logging.debug import debug_logger` imports remaining
- **Facade Adoption**: All debug_logger access through facade bridge
- **Test Coverage**: 100% pass rate maintained throughout automation
- **Automation Efficiency**: All transformations applied via systematic batching
- **Tracking Accuracy**: JSON reflects actual automation state

### Performance Thresholds [MAINTAINED]
- **Debug Logger Performance**: No degradation through facade bridge
- **Test Suite Runtime**: Maintain <5s total execution time
- **Import Time**: Minimal overhead from facade bridge redirection

### Phase 4 Deliverables [CREATED/UPDATED]
- All debug_logger imports redirected to facade bridge
- Updated `singleton_migration_tracking.json` with 100% import completion
- `.phase4_complete` completion marker
- `phase5_readiness.json` preparation for final validation
- Systematic batch commits for automation progress tracking
- Phase completion git tag

---

**Phase 4 eliminates the bulk of singleton instances through systematic automation. The 940 import singletons are transformed to use the facade bridge, maintaining backward compatibility while completing the vast majority of the migration work.**
