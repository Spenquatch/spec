Agent Execution Directive: Singleton Migration Cleanup

This protocol governs how AI agents must systematically eliminate singleton patterns and complete the
dependency injection migration. Every instruction here is mandatory. Execution must follow the exact
sequence, respect strict scope boundaries, and maintain system stability throughout the migration.

You will work incrementally, fix test failures immediately, and validate every change against the
tracking JSON.

If a migration breaks tests: revert it. If the tracking JSON isn't updated: the work didn't happen.
If it's not green: it's broken.

---

[P0-ABSOLUTE] MIGRATION EXECUTION RULES

These rules override everything else. Violating any rule makes the migration invalid.

1. NEVER break existing tests → All tests must pass before and after each migration step
2. NEVER skip facade bridge → All singleton access must go through compatibility layer first
3. NEVER migrate more than 20 instances per batch → Small incremental changes only
4. NEVER modify working CLI commands → Only touch commands marked as "not_migrated" in tracking JSON
5. NEVER commit broken migration state → Each commit must be fully functional
6. NEVER ignore detection tool updates → Always update tracking JSON after changes

"Migration is green OR broken - no partial states exist"

---

1. Pre-Migration Baseline Checklist

Before Any Migration Work

# 1. Establish test baseline - ALL tests must pass

poetry run pytest tests/unit/ -v

# Expected: 0 failures

# 2. Validate tracking JSON structure

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Tracking
JSON valid: {len(data[\"migration_tracking\"][\"categories\"])} categories')"

# 3. Run singleton detection baseline

python tools/singleton_detector.py spec_cli/ --output=json > current_singletons.json

# Compare with tracking JSON estimates

# 4. Verify facade bridge readiness (Phase 0 dependency)

ls -la spec_cli/core/context_bridge.py || echo "ERROR: Facade bridge not implemented - Phase 0
required first"

# 5. Check current migration state

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Current
progress: {data[\"migration_tracking\"][\"metadata\"][\"completed\"]} /
{data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]} instances')"

If ANY baseline check fails: Stop and implement prerequisites first. Do not proceed with broken
foundation.

---

2. Migration Workflow [MANDATORY SEQUENCE]

Required Execution Sequence [FOLLOW EXACTLY]

Every AI agent executing singleton migration MUST follow this exact sequence:

Step 1: Task Selection & Preparation

1. Read tracking JSON completely → Identify next highest priority "not_migrated" item
2. Verify prerequisites → Ensure all "blocked_by" dependencies are resolved
3. Select batch size → Maximum 20 instances or 1 CLI command per execution
4. Document approach → Update tracking JSON with "in_progress" status

Step 2: Migration Implementation

5. Apply transformation pattern → Use exact patterns from tracking JSON "transformation_patterns"

6. For CLI commands:

# Add @context_injection decorator

from ..decorators import context_injection
from ...core.context import SpecContext

@context_injection
def command_name(context: SpecContext, debug: bool, verbose: bool, ...): # Replace get_console() with context.console # Replace get_settings() with context.settings # Replace debug_logger with context.logger (via facade)

5. For functional singleton replacements:

# Replace: get_console()

# With: context.console (requires @context_injection)

# Replace: debug_logger.log(...)

# With: debug_logger.log(...) (via facade bridge - no change needed)

6. Update imports → Apply import transformations from tracking JSON patterns
7. Validate syntax → Ensure all changes are syntactically correct
   python -m py_compile spec_cli/path/to/modified_file.py

Step 3: Testing & Validation

8. Run affected tests immediately → Test only the modified components

# For CLI commands

poetry run pytest tests/unit/cli/commands/test\_[command_name].py -v

# For utility modules

poetry run pytest tests/unit/[module_path]/test\_[module_name].py -v 9. IF tests fail → Analyze and fix issues, do not proceed until green 10. Run full test suite → Ensure no regressions
poetry run pytest tests/unit/ -v

# Must pass 100% - any failures require immediate fix

11. Update tracking JSON → Mark completed instances as "migrated"

# Update instance status to "migrated"

# Increment metadata.completed count

# Update progress_by_category completion_rate

Step 4: Detection & Progress Validation

12. Run detection tool → Verify singleton count decreased
    python tools/singleton_detector.py spec_cli/ --output=json
    --update-tracking=singleton_migration_tracking.json
13. Validate progress → Confirm tracking JSON reflects actual state

# Check progress command from tracking JSON

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Progress:
{data[\"migration_tracking\"][\"metadata\"][\"completed\"]} /
{data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]} ({100\*data[\"migration_tracking\"][ \"metadata\"][\"completed\"]//data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]}%)')" 14. Commit incremental progress → Each batch must be committed separately
git add singleton_migration_tracking.json spec_cli/[modified_files]
git commit -m "feat: migrate [X] singleton instances in [component_name]

- Migrated [specific pattern] from [old pattern] to [new pattern]
- Updated tracking JSON: [old_count] -> [new_count] instances
- Phase: [phase_name], Category: [category_name]
- Tests: ✅ All pass, No regressions"

Step 5: Batch Completion

15. Verify batch completion → All selected instances show "migrated" status
16. Run comprehensive validation → Full quality gates on modified code
    poetry run ruff check spec_cli/[modified_files] --fix
    poetry run mypy spec_cli/[modified_files]
17. IF validation fails → Fix issues and re-test before proceeding

Migration Failure Protocol [ERROR HANDLING]

IF any step fails:

- Test failures → Revert changes, analyze root cause, retry with smaller batch
- Detection tool errors → Fix tool, validate manually, update tracking
- Import errors → Check facade bridge implementation, verify relative imports
- IF 3 consecutive failures → Escalate with detailed error report including: failed command, test
  output, tracking JSON state, environment details

---

3. Migration Categories & Approaches [CATEGORY-SPECIFIC RULES]

CLI Commands (Priority: HIGH)

Pattern: Add @context_injection decorator and SpecContext parameter

# BEFORE (not_migrated)

def diff_command(debug: bool, verbose: bool, files: tuple[str, ...]):
console = get_console()
debug_logger.log("INFO", "Diff command started")

# AFTER (migrated)

@context_injection
def diff_command(context: SpecContext, debug: bool, verbose: bool, files: tuple[str, ...]): # console = get_console() # Removed # debug_logger.log("INFO", "Diff command started") # Via facade - no change
context.console.print_message("Starting diff operation")
debug_logger.log("INFO", "Diff command started") # Facade handles this

Testing Requirements:

- ✅ Unit tests required for CLI commands (verify @context_injection works)
- Test that SpecContext is properly injected
- Test that context.console/settings work correctly

Functional Singletons (Priority: MEDIUM)

Pattern: Replace with context.property access after facade

# BEFORE

from ..ui.console import get_console

def process_data():
console = get_console()
console.print_message("Processing...")

# AFTER (requires @context_injection on caller)

def process_data(context: SpecContext): # console = get_console() # Removed
context.console.print_message("Processing...")

Testing Requirements:

- ❌ No new unit tests required for simple replacements
- ✅ Update existing tests to mock SpecContext instead of singletons

Import Singletons (Priority: LOW)

Pattern: Automated replacement via facade bridge

# BEFORE

from ..logging.debug import debug_logger

# AFTER (automated via facade)

from ..core.context_bridge import debug_logger # Facade handles compatibility

Testing Requirements:

- ❌ No new unit tests required - mechanical transformation
- ✅ Verify facade bridge has comprehensive tests

Test Failures (Priority: CRITICAL)

Pattern: Fix existing functionality, no new features

Testing Requirements:

- ❌ No new unit tests required - fixing existing functionality
- ✅ Ensure fixed tests consistently pass

---

4. Tracking JSON Management [MANDATORY]

Status Updates [REQUIRED AFTER EACH BATCH]

# Update instance status

# FROM: "current_state": "not_migrated"

# TO: "current_state": "migrated"

# Update metadata counters

# INCREMENT: metadata.completed

# UPDATE: progress_by_category.[category].completion_rate

# Add completion timestamp

# ADD: "completed_date": "2025-07-07"

Progress Validation Commands

# Check overall progress

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Progress:
{data[\"migration_tracking\"][\"metadata\"][\"completed\"]} /
{data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]} ({100\*data[\"migration_tracking\"][ \"metadata\"][\"completed\"]//data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]}%)')"

# Check category progress

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); [print(f'{cat}:
{info[\"completion_rate\"]}') for cat, info in
data[\"migration_tracking\"][\"progress_by_category\"].items()]"

# Validate detection tool alignment

python tools/singleton_detector.py spec_cli/ --validate-tracking=singleton_migration_tracking.json

---

5. Phase Execution Order [STRICT DEPENDENCIES]

Phase 0: Facade Bridge (PREREQUISITE)

- Status: Must be completed first
- Validation: ls -la spec_cli/core/context_bridge.py exists
- Blocks: All other migration work

Phase 1: Test Failures (CRITICAL PATH)

- Batch Size: 1-3 test files per execution
- Validation: poetry run pytest tests/unit/ -v passes 100%
- Blocks: CLI command migration

Phase 2: CLI Commands (HIGH VALUE)

- Batch Size: 1 command per execution
- Order: Start with lowest complexity commands first
- Validation: Each command works with @context_injection

Phase 3: Debug Logger Automation (BULK WORK)

- Batch Size: 50-100 instances per execution (automated)
- Tool: Use automated codemod from tracking JSON
- Validation: Grep counts decrease as expected

---

6. Quality Gates [NO EXCEPTIONS]

Pre-Migration Gates

# All tests must pass before starting

poetry run pytest tests/unit/ -v

# Expected: 0 failures, 0 errors

# Tracking JSON must be valid

python -c "import json; json.load(open('singleton_migration_tracking.json'))"

# Expected: No JSON parse errors

Post-Migration Gates

# All tests must still pass

poetry run pytest tests/unit/ -v

# Expected: 0 failures, 0 errors

# No new linting violations

poetry run ruff check spec_cli/ --diff

# Expected: No new violations introduced

# Singleton count decreased

python tools/singleton_detector.py spec_cli/ --count-only

# Expected: Count lower than pre-migration baseline

Continuous Validation

# After every 5 batches, run comprehensive check

poetry run check-all

# Expected: All quality gates pass

# Update progress metrics

./automation_commands/progress_check

# Expected: Completion percentage increased

---

7. Automation Commands [FROM TRACKING JSON]

Detection & Progress Tracking

# Update detection results

python tools/singleton_detector.py spec_cli/ --output=json
--update-tracking=singleton_migration_tracking.json

# Check current progress

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Progress:
{data[\"migration_tracking\"][\"metadata\"][\"completed\"]} /
{data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]} ({100\*data[\"migration_tracking\"][ \"metadata\"][\"completed\"]//data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]}%)')"

# Validate tracking accuracy

python tools/singleton_detector.py spec_cli/ --validate-zero

Automated Transformations

# Apply facade bridge pattern (bulk replacement)

find spec_cli/ -name '\*.py' -exec sed -i 's/from ..logging.debug import debug_logger/from
..core.context_bridge import debug_logger/g' {} \;

# Validate transformation success

grep -r 'from.\*logging.debug import debug_logger' spec_cli/ | wc -l

# Expected: 0 occurrences

# Run validation suite after automation

poetry run pytest tests/unit/ -k 'not migration' && python tools/singleton_detector.py spec_cli/
--validate-zero

---

8. Error Recovery Protocols

Test Failures During Migration

# 1. Immediately revert changes

git checkout -- spec_cli/[modified_files]

# 2. Analyze failure cause

poetry run pytest tests/unit/[failed_test] -v -s

# 3. Try smaller batch (reduce scope by 50%)

# 4. Update tracking JSON with "blocked" status if persistent failure

Detection Tool Mismatches

# 1. Manual verification of singleton patterns

grep -r "debug_logger\." spec_cli/ | wc -l
grep -r "get_console()" spec_cli/ | wc -l
grep -r "get_settings()" spec_cli/ | wc -l

# 2. Update detection tool patterns

# 3. Re-run detection and update tracking

Facade Bridge Issues

# 1. Verify facade bridge implementation

python -c "from spec_cli.core.context_bridge import debug_logger; print('Facade working')"

# 2. If not working, escalate to Phase 0 completion first

# 3. Do not proceed with migration until facade is functional

---

9. Migration Completion Checklist

Batch Completion (After Each Execution)

- Selected instances marked "migrated" in tracking JSON
- metadata.completed count incremented correctly
- All tests pass: poetry run pytest tests/unit/ -v
- No new linting violations: poetry run ruff check spec_cli/
- Detection tool count decreased appropriately
- Changes committed with descriptive message
- Progress percentage increased

Phase Completion

- All instances in category show "migrated" status
- Category completion_rate shows 100%
- Phase success criteria met (from tracking JSON)
- All dependencies for next phase resolved
- Comprehensive quality gates pass: poetry run check-all

Full Migration Completion

- metadata.total_instances equals metadata.completed
- All categories show 100% completion_rate
- Detection tool reports zero singleton patterns: python tools/singleton_detector.py spec_cli/
  --validate-zero
- All migration phases marked complete
- CI integration prevents new singleton introductions
- Facade bridge can be removed (optional cleanup phase)

---

Quick Reference Commands

# Pre-migration baseline

poetry run pytest tests/unit/ -v && python tools/singleton_detector.py spec_cli/ --count-only

# Migration cycle (per batch)

[apply_transformations] && poetry run pytest tests/unit/ -v && python -c "import json; ..." (update
tracking)

# Progress check

python -c "import json; data=json.load(open('singleton_migration_tracking.json')); print(f'Progress:
{data[\"migration_tracking\"][\"metadata\"][\"completed\"]} /
{data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]} ({100\*data[\"migration_tracking\"][ \"metadata\"][\"completed\"]//data[\"migration_tracking\"][\"metadata\"][\"total_instances\"]}%)')"

# Validation after batch

poetry run ruff check spec_cli/ --fix && python tools/singleton_detector.py spec_cli/
--validate-tracking

# Git workflow

git add singleton_migration_tracking.json spec_cli/[modified] && git commit -m "feat: migrate [X]
instances - Progress: [Y]%"

---

Remember: Work incrementally, maintain test coverage, update tracking JSON religiously, and never
commit broken states. The facade bridge is your safety net - use it. If anything breaks, revert
immediately and try a smaller batch.
