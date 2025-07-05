#!/bin/bash
# Manual Test Script: Slice P2.3c - Status Command Migration
# Purpose: Manually verify that the migrated status command works correctly with context injection
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.3c - Status Command Migration ==="
echo "Purpose: Verify status command migration to context injection pattern"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

if [ ! -f "pyproject.toml" ]; then
    echo "ERROR: Not in spec-cli project directory"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
TEST_DIR="test_area_p2_3c"
if [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
fi
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize spec repository for testing
echo "Initializing spec repository..."
poetry run spec init --force 2>/dev/null || echo "Init command may have issues (expected during migration)"
echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Basic status command execution"
echo "Expected: Status command executes and displays repository information"
echo "Executing:"
((TOTAL_TESTS++))

OUTPUT1=$(poetry run spec status 2>&1 || echo "COMMAND_FAILED")
echo "Result:"
echo "$OUTPUT1"

if [[ "$OUTPUT1" != *"COMMAND_FAILED"* ]]; then
    echo "Status: PASS - Status command executed"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Status command failed to execute"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 2: Status command with context injection verification"
echo "Expected: Status command has context parameter in signature"
echo "Executing:"
((TOTAL_TESTS++))

SIGNATURE_CHECK=$(python -c "
import sys
sys.path.insert(0, '../')
try:
    import inspect
    from spec_cli.cli.commands.status import status_command
    sig = inspect.signature(status_command)
    params = list(sig.parameters.keys())
    if params[0] == 'context' and len(params) == 6:
        print('CONTEXT_INJECTION_SUCCESS')
    else:
        print(f'CONTEXT_INJECTION_FAILED: params={params}')
except Exception as e:
    print(f'SIGNATURE_CHECK_ERROR: {e}')
" 2>&1)

echo "Result: $SIGNATURE_CHECK"

if [[ "$SIGNATURE_CHECK" == *"CONTEXT_INJECTION_SUCCESS"* ]]; then
    echo "Status: PASS - Context injection properly implemented"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Context injection not properly implemented"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Status command decorator verification"
echo "Expected: Status command has context_injection decorator applied"
echo "Executing:"
((TOTAL_TESTS++))

DECORATOR_CHECK=$(python -c "
import sys
sys.path.insert(0, '../')
try:
    from spec_cli.cli.commands.status import status_command
    if hasattr(status_command, '__wrapped__'):
        print('DECORATOR_SUCCESS')
    else:
        print('DECORATOR_FAILED')
except Exception as e:
    print(f'DECORATOR_ERROR: {e}')
" 2>&1)

echo "Result: $DECORATOR_CHECK"

if [[ "$DECORATOR_CHECK" == *"DECORATOR_SUCCESS"* ]]; then
    echo "Status: PASS - Context injection decorator applied"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Context injection decorator not applied"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 4: Status command options verification"
echo "Expected: All original command options still available"
echo "Executing:"
((TOTAL_TESTS++))

OPTIONS_OUTPUT=$(poetry run spec status --help 2>&1 || echo "HELP_FAILED")
echo "Result:"
echo "$OPTIONS_OUTPUT"

if [[ "$OPTIONS_OUTPUT" == *"--health"* && "$OPTIONS_OUTPUT" == *"--git"* && "$OPTIONS_OUTPUT" == *"--summary"* ]]; then
    echo "Status: PASS - All command options available"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Command options missing"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 5: Status command with health option"
echo "Expected: Health check executes without errors"
echo "Executing:"
((TOTAL_TESTS++))

HEALTH_OUTPUT=$(poetry run spec status --health 2>&1 || echo "HEALTH_FAILED")
echo "Result:"
echo "$HEALTH_OUTPUT"

if [[ "$HEALTH_OUTPUT" != *"HEALTH_FAILED"* ]]; then
    echo "Status: PASS - Health option works"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Health option failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 6: Status command with git option"
echo "Expected: Git status information displayed"
echo "Executing:"
((TOTAL_TESTS++))

GIT_OUTPUT=$(poetry run spec status --git 2>&1 || echo "GIT_FAILED")
echo "Result:"
echo "$GIT_OUTPUT"

if [[ "$GIT_OUTPUT" != *"GIT_FAILED"* ]]; then
    echo "Status: PASS - Git option works"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Git option failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 7: Status command with summary option"
echo "Expected: Processing summary displayed"
echo "Executing:"
((TOTAL_TESTS++))

SUMMARY_OUTPUT=$(poetry run spec status --summary 2>&1 || echo "SUMMARY_FAILED")
echo "Result:"
echo "$SUMMARY_OUTPUT"

if [[ "$SUMMARY_OUTPUT" != *"SUMMARY_FAILED"* ]]; then
    echo "Status: PASS - Summary option works"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Summary option failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 8: Migration utility compatibility verification"
echo "Expected: Migration utilities are properly reused from P2.3b"
echo "Executing:"
((TOTAL_TESTS++))

MIGRATION_CHECK=$(python -c "
import sys
sys.path.insert(0, '../')
try:
    from spec_cli.utils.migration_utils import get_migration_requirements
    from spec_cli.cli.commands.status import status_command
    
    # Test that migration utilities work with status command
    reqs = get_migration_requirements(status_command.__wrapped__)
    if reqs['function_name'] == 'status_command':
        print('MIGRATION_UTILS_SUCCESS')
    else:
        print(f'MIGRATION_UTILS_FAILED: {reqs}')
except Exception as e:
    print(f'MIGRATION_UTILS_ERROR: {e}')
" 2>&1)

echo "Result: $MIGRATION_CHECK"

if [[ "$MIGRATION_CHECK" == *"MIGRATION_UTILS_SUCCESS"* ]]; then
    echo "Status: PASS - Migration utilities compatible"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Migration utilities not compatible"
    ((FAILED_TESTS++))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking that status command preserves behavior..."

# Create some test content to verify status reporting
echo "# Test content" > .specs/test_content.md
poetry run spec add .specs/test_content.md 2>/dev/null || echo "Add may have issues during migration"

FINAL_STATUS=$(poetry run spec status 2>&1 || echo "FINAL_FAILED")
echo "Final status check result:"
echo "$FINAL_STATUS"

if [[ "$FINAL_STATUS" != *"FINAL_FAILED"* ]]; then
    echo "Verification: PASS - Status command behavior preserved"
else
    echo "Verification: FAIL - Status command behavior changed"
fi

echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring status command response time..."

START_TIME=$(date +%s%N)
poetry run spec status >/dev/null 2>&1 || true
END_TIME=$(date +%s%N)
DURATION_MS=$(( ($END_TIME - $START_TIME) / 1000000 ))

echo "Status command execution time: ${DURATION_MS}ms"

if [ $DURATION_MS -lt 5000 ]; then
    echo "Performance: PASS - Command executes in reasonable time"
else
    echo "Performance: WARNING - Command execution slow (>${DURATION_MS}ms)"
fi
echo

# Cleanup phase
echo "Cleaning up..."
cd ..
rm -rf "$TEST_DIR"
echo "Cleanup complete"
echo

# Summary
echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Status command migration working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Status command migration needs investigation"
    exit 1
fi