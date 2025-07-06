#!/bin/bash
# Manual Test Script: Slice P3.2a - Singleton Infrastructure Removal
# Purpose: Manually verify that singleton infrastructure files are completely removed
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.2a - Singleton Infrastructure Removal ==="
echo "Purpose: Verify singleton infrastructure files are completely removed with no remaining references"
echo "Timestamp: $(date)"
echo

# Test variables
PASSED_TESTS=0
TOTAL_TESTS=5

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v find >/dev/null 2>&1; then
    echo "ERROR: find command not found"
    exit 1
fi

if ! command -v grep >/dev/null 2>&1; then
    echo "ERROR: grep command not found"
    exit 1
fi

echo "Prerequisites verified - python3, find, and grep available"
echo

# Setup phase
echo "Setting up test environment..."
PROJECT_ROOT=$(pwd)
if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Not in project root directory (no pyproject.toml found)"
    exit 1
fi

if [[ ! -d "spec_cli" ]]; then
    echo "ERROR: spec_cli directory not found"
    exit 1
fi

echo "Test environment ready - project root: $PROJECT_ROOT"
echo

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Verify singleton.py infrastructure files are removed"
echo "Expected: No singleton.py files found in spec_cli directory"
echo "Executing:"
SINGLETON_FILES=$(find spec_cli -name "singleton.py" -type f 2>/dev/null || echo "")
if [[ -z "$SINGLETON_FILES" ]]; then
    echo "Result: No singleton.py files found"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Found singleton.py files: $SINGLETON_FILES"
    echo "Status: FAIL"
fi
echo ""

echo "Test 2: Verify compatibility.py files are removed"
echo "Expected: No compatibility.py files found in spec_cli directory"
echo "Executing:"
COMPATIBILITY_FILES=$(find spec_cli -name "compatibility.py" -type f 2>/dev/null || echo "")
if [[ -z "$COMPATIBILITY_FILES" ]]; then
    echo "Result: No compatibility.py files found"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Found compatibility.py files: $COMPATIBILITY_FILES"
    echo "Status: FAIL"
fi
echo ""

echo "Test 3: Verify cleanup utilities are properly implemented"
echo "Expected: cleanup_utils.py exists and contains required functions"
echo "Executing:"
CLEANUP_UTILS_FILE="spec_cli/utils/cleanup_utils.py"
if [[ -f "$CLEANUP_UTILS_FILE" ]]; then
    echo "Result: cleanup_utils.py exists"
    
    # Check for required functions
    REQUIRED_FUNCTIONS=("safe_file_removal" "validate_no_references" "cleanup_singleton_infrastructure" "cleanup_compatibility_layer")
    ALL_FUNCTIONS_FOUND=true
    
    for func in "${REQUIRED_FUNCTIONS[@]}"; do
        if grep -q "def $func" "$CLEANUP_UTILS_FILE"; then
            echo "  - Function $func: FOUND"
        else
            echo "  - Function $func: MISSING"
            ALL_FUNCTIONS_FOUND=false
        fi
    done
    
    if $ALL_FUNCTIONS_FOUND; then
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Missing required functions"
    fi
else
    echo "Result: cleanup_utils.py not found"
    echo "Status: FAIL"
fi
echo ""

echo "Test 4: Test cleanup utilities functionality"
echo "Expected: Cleanup utilities can be imported and called without errors"
echo "Executing:"
PYTHON_TEST_RESULT=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from spec_cli.utils.cleanup_utils import safe_file_removal, validate_no_references
    from pathlib import Path
    import tempfile
    
    # Test safe_file_removal with non-existent file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir) / 'test.txt'
        result = safe_file_removal(test_path)
        assert result is False
    
    # Test validate_no_references
    violations = validate_no_references(Path('.'), ['nonexistent_module'])
    assert isinstance(violations, list)
    
    print('SUCCESS: All cleanup utilities work correctly')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

echo "Result: $PYTHON_TEST_RESULT"
if [[ $PYTHON_TEST_RESULT == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
echo ""

echo "Test 5: Verify no remaining singleton infrastructure references in core modules"
echo "Expected: No references to SingletonMeta or singleton imports in core spec_cli modules"
echo "Executing:"
# Check for singleton references in core modules (excluding tests and cache)
SINGLETON_REFS=$(grep -r "SingletonMeta\|from.*singleton\|import.*singleton" spec_cli/ 2>/dev/null | grep -v __pycache__ | grep -v .pyc || echo "")

if [[ -z "$SINGLETON_REFS" ]]; then
    echo "Result: No singleton references found in core modules"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Found singleton references in core modules:"
    echo "$SINGLETON_REFS"
    echo "Status: FAIL"
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking that infrastructure removal didn't break basic functionality..."

# Basic import test
IMPORT_TEST_RESULT=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import spec_cli
    from spec_cli.utils.cleanup_utils import cleanup_singleton_infrastructure
    from spec_cli.exceptions import InfrastructureRemovalError
    print('SUCCESS: Core imports working')
except Exception as e:
    print(f'ERROR: Import failed - {e}')
    sys.exit(1)
" 2>&1)

echo "Import test result: $IMPORT_TEST_RESULT"
if [[ $IMPORT_TEST_RESULT != *"SUCCESS"* ]]; then
    echo "WARNING: Basic imports failing after infrastructure removal"
fi

echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring cleanup utility performance..."

PERFORMANCE_TEST=$(python3 -c "
import sys
import time
sys.path.insert(0, '.')
from spec_cli.utils.cleanup_utils import validate_no_references
from pathlib import Path

start_time = time.time()
violations = validate_no_references(Path('.'), ['singleton', 'compatibility'])
end_time = time.time()

duration = end_time - start_time
print(f'Reference validation completed in {duration:.2f} seconds')
print(f'Found {len(violations)} violations')

if duration < 10.0:  # Should complete within 10 seconds
    print('PERFORMANCE: ACCEPTABLE')
else:
    print('PERFORMANCE: SLOW')
" 2>&1)

echo "$PERFORMANCE_TEST"
echo

# Cleanup phase
echo "Cleaning up..."
echo "No cleanup needed - tests were read-only"
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Singleton infrastructure successfully removed"
    exit 0
else
    echo "SOME TESTS FAILED - Singleton infrastructure removal incomplete"
    exit 1
fi