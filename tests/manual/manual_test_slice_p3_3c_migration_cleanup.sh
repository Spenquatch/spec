#!/bin/bash
# Manual Test Script: Slice P3.3c - Migration Cleanup and Validation
# Purpose: Manually verify that the migration cleanup functionality works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.3c - Migration Cleanup and Validation ==="
echo "Purpose: Verify complete singleton import cleanup and migration validation"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
TEST_DIR="tests/manual/migration_test_workspace"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create test files with singleton imports
echo "Creating test files with singleton imports..."
mkdir -p test_project/spec_cli/config
mkdir -p test_project/spec_cli/ui
mkdir -p test_project/spec_cli/utils

# Test file 1: Settings with singleton imports
cat > test_project/spec_cli/config/settings.py << 'EOF'
"""Test settings module with singleton imports."""
from ..utils.singleton import reset_singleton, singleton_decorator
from pathlib import Path

@singleton_decorator
class SettingsManager:
    def __init__(self):
        self.value = "test"
    
    def get_value(self):
        return self.value

def get_settings():
    return SettingsManager()
EOF

# Test file 2: Console with singleton imports  
cat > test_project/spec_cli/ui/console.py << 'EOF'
"""Test console module with singleton imports."""
from ..utils.singleton import singleton_decorator
from rich.console import Console

@singleton_decorator
class ConsoleManager:
    def __init__(self):
        self.console = Console()
    
    def print(self, text):
        self.console.print(text)
EOF

# Test file 3: Clean file without singleton imports
cat > test_project/spec_cli/utils/helper.py << 'EOF'
"""Clean helper module without singleton imports."""
from pathlib import Path

class Helper:
    def __init__(self):
        pass
    
    def help(self):
        return "helper"
EOF

echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Migration cleanup utility functionality"
echo "Expected: Successful cleanup of singleton imports with detailed report"
echo "Executing:"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

cd ../../../..
CLEANUP_RESULT=$(python -c "
from spec_cli.utils.migration_cleanup_utils import cleanup_migration
from pathlib import Path
import sys

try:
    report = cleanup_migration(Path('tests/manual/migration_test_workspace/test_project'))
    print(f'SUCCESS: Migration cleanup completed')
    print(f'  Files processed: {report.files_processed}')
    print(f'  Imports removed: {report.imports_removed}')
    print(f'  Context imports added: {report.context_imports_added}')
    print(f'  Success: {report.success}')
    print(f'  Errors: {len(report.errors)}')
    sys.exit(0 if report.success else 1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

echo "Result: $CLEANUP_RESULT"
CLEANUP_EXIT_CODE=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [[ $CLEANUP_EXIT_CODE -eq 0 ]]; then
    echo "Status: PASS - Migration cleanup utility functional"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Migration cleanup utility failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 2: Verify singleton imports removed"
echo "Expected: No singleton import statements remain in processed files"
echo "Executing:"
SINGLETON_COUNT=$(grep -r "from.*utils\.singleton\|import.*singleton" tests/manual/migration_test_workspace/test_project/ 2>/dev/null | wc -l || echo "0")
echo "Actual: $SINGLETON_COUNT singleton imports found"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$SINGLETON_COUNT" -eq 0 ]; then
    echo "Status: PASS - No singleton imports remain"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - $SINGLETON_COUNT singleton imports still present"
    echo "Details:"
    grep -r "from.*utils\.singleton\|import.*singleton" tests/manual/migration_test_workspace/test_project/ 2>/dev/null || echo "No matches found"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 3: Verify context imports added"
echo "Expected: Context imports added to appropriate files"
echo "Executing:"
CONTEXT_COUNT=$(grep -r "from.*core\.context import SpecContext" tests/manual/migration_test_workspace/test_project/ 2>/dev/null | wc -l || echo "0")
echo "Actual: $CONTEXT_COUNT context imports found"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ "$CONTEXT_COUNT" -gt 0 ]; then
    echo "Status: PASS - Context imports added"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - No context imports added"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 4: Migration validation functionality"
echo "Expected: Migration validation reports completion status"
echo "Executing:"
VALIDATION_RESULT=$(python -c "
from spec_cli.utils.migration_cleanup_utils import validate_migration_complete
import sys

try:
    report = validate_migration_complete()
    print(f'SUCCESS: Migration validation completed')
    print(f'  Success: {report.success}')
    print(f'  Files processed: {report.files_processed}')
    print(f'  Singleton violations: {len(report.singleton_violations)}')
    print(f'  Errors: {len(report.errors)}')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

echo "Result: $VALIDATION_RESULT"
VALIDATION_EXIT_CODE=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [[ $VALIDATION_EXIT_CODE -eq 0 ]]; then
    echo "Status: PASS - Migration validation functional"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Migration validation failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 5: File structure preservation"
echo "Expected: Original file structure and functionality preserved after cleanup"
echo "Executing:"
FILES_PRESERVED=0
TOTAL_FILES=3

# Check if all test files still exist
if [[ -f "tests/manual/migration_test_workspace/test_project/spec_cli/config/settings.py" ]]; then
    FILES_PRESERVED=$((FILES_PRESERVED + 1))
fi

if [[ -f "tests/manual/migration_test_workspace/test_project/spec_cli/ui/console.py" ]]; then
    FILES_PRESERVED=$((FILES_PRESERVED + 1))
fi

if [[ -f "tests/manual/migration_test_workspace/test_project/spec_cli/utils/helper.py" ]]; then
    FILES_PRESERVED=$((FILES_PRESERVED + 1))
fi

echo "Actual: $FILES_PRESERVED out of $TOTAL_FILES files preserved"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [[ $FILES_PRESERVED -eq $TOTAL_FILES ]]; then
    echo "Status: PASS - File structure preserved"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Some files missing after cleanup"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 6: Code functionality preservation"
echo "Expected: Class definitions and methods remain intact"
echo "Executing:"
CLASSES_FOUND=0

if grep -q "class SettingsManager:" tests/manual/migration_test_workspace/test_project/spec_cli/config/settings.py; then
    CLASSES_FOUND=$((CLASSES_FOUND + 1))
fi

if grep -q "class ConsoleManager:" tests/manual/migration_test_workspace/test_project/spec_cli/ui/console.py; then
    CLASSES_FOUND=$((CLASSES_FOUND + 1))
fi

if grep -q "class Helper:" tests/manual/migration_test_workspace/test_project/spec_cli/utils/helper.py; then
    CLASSES_FOUND=$((CLASSES_FOUND + 1))
fi

echo "Actual: $CLASSES_FOUND out of 3 class definitions found"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [[ $CLASSES_FOUND -eq 3 ]]; then
    echo "Status: PASS - Code functionality preserved"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Some class definitions missing"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking processed files for expected content..."

# Check settings file
if [[ -f "tests/manual/migration_test_workspace/test_project/spec_cli/config/settings.py" ]]; then
    SETTINGS_CONTENT=$(cat tests/manual/migration_test_workspace/test_project/spec_cli/config/settings.py)
    echo "Settings file content sample:"
    echo "$SETTINGS_CONTENT" | head -5
    echo "..."
fi

echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring cleanup operation time..."
START_TIME=$(date +%s%N)

python -c "
from spec_cli.utils.migration_cleanup_utils import validate_migration_complete
validate_migration_complete()
" > /dev/null 2>&1

END_TIME=$(date +%s%N)
DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))

echo "Validation completed in: ${DURATION_MS}ms"

if [[ $DURATION_MS -lt 5000 ]]; then
    echo "Performance: PASS - Under 5 second threshold"
else
    echo "Performance: SLOW - Over 5 second threshold"
fi
echo

# Cleanup phase
echo "Cleaning up..."
rm -rf tests/manual/migration_test_workspace/
echo "Cleanup complete"
echo

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Performance: Validation completed in ${DURATION_MS}ms"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Migration cleanup working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Migration cleanup needs investigation"
    exit 1
fi