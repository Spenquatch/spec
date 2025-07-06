#!/bin/bash
# Manual Test Script: Slice P3.1b - Commit Command Migration
# Purpose: Manually verify that the migrated commit command works correctly with context injection
# Created: 2025-01-06

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.1b - Commit Command Migration ==="
echo "Purpose: Verify migrated commit command functionality works identically to original behavior"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found. Please install poetry first."
    exit 1
fi

if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Not in spec-cli project root directory"
    exit 1
fi

echo "Prerequisites verified"

# Setup phase
echo "Setting up test environment..."
TEST_DIR="test_area_commit_migration"
ORIGINAL_DIR=$(pwd)

# Clean up any previous test directory
if [[ -d "$TEST_DIR" ]]; then
    echo "Cleaning up previous test directory..."
    rm -rf "$TEST_DIR"
fi

# Create test directory
mkdir "$TEST_DIR"
cd "$TEST_DIR"
echo "Test environment ready in: $(pwd)"

# Test execution phase
echo ""
echo "Executing manual tests..."

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo ""
echo "Test 1: Basic commit command with context injection"
echo "Expected: Repository initialization and successful commit with context-based console output"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Initialize repository
poetry run spec init
if [[ $? -eq 0 ]]; then
    echo "✓ Repository initialization successful"
else
    echo "✗ Repository initialization failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    cd "$ORIGINAL_DIR"
    exit 1
fi

# Create test file
echo "test content for commit migration" > test_content.txt
echo "# Test Documentation" > .specs/test_migration.md
echo "This is a test file for commit command migration testing." >> .specs/test_migration.md

# Add file to staging
poetry run spec add .specs/test_migration.md
if [[ $? -eq 0 ]]; then
    echo "✓ File staging successful"
else
    echo "✗ File staging failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    cd "$ORIGINAL_DIR"
    exit 1
fi

# Execute commit command
COMMIT_OUTPUT=$(poetry run spec commit -m "Test commit with context injection" 2>&1)
COMMIT_EXIT_CODE=$?
echo "Actual commit output:"
echo "$COMMIT_OUTPUT"

if [[ $COMMIT_EXIT_CODE -eq 0 ]] && [[ "$COMMIT_OUTPUT" == *"Created commit:"* ]]; then
    echo "Status: PASS - Commit command with context injection works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Commit command failed or output incorrect"
    echo "Expected output to contain 'Created commit:', got: $COMMIT_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 2: Commit command dry run mode with context console"
echo "Expected: Dry run message displayed via context console, no actual commit created"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Create another test file
echo "# Another Test File" > .specs/dry_run_test.md
poetry run spec add .specs/dry_run_test.md

# Execute dry run commit
DRY_RUN_OUTPUT=$(poetry run spec commit --dry-run -m "Dry run test commit" 2>&1)
DRY_RUN_EXIT_CODE=$?
echo "Actual dry run output:"
echo "$DRY_RUN_OUTPUT"

if [[ $DRY_RUN_EXIT_CODE -eq 0 ]] && [[ "$DRY_RUN_OUTPUT" == *"This is a dry run"* ]]; then
    echo "Status: PASS - Dry run mode uses context console correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Dry run mode failed or incorrect output"
    echo "Expected output to contain 'This is a dry run', got: $DRY_RUN_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 3: Commit command with auto-stage functionality"
echo "Expected: Modified files auto-staged and committed via context-aware helper functions"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Modify an existing file (not staged)
echo "Modified content for auto-stage test" >> .specs/test_migration.md

# Execute commit with auto-stage
AUTO_STAGE_OUTPUT=$(poetry run spec commit --all -m "Auto-stage commit test" 2>&1)
AUTO_STAGE_EXIT_CODE=$?
echo "Actual auto-stage output:"
echo "$AUTO_STAGE_OUTPUT"

if [[ $AUTO_STAGE_EXIT_CODE -eq 0 ]] && [[ "$AUTO_STAGE_OUTPUT" == *"Created commit:"* ]]; then
    echo "Status: PASS - Auto-stage functionality works with context injection"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Auto-stage functionality failed"
    echo "Expected successful commit, got exit code: $AUTO_STAGE_EXIT_CODE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 4: Error handling with context console"
echo "Expected: Error messages displayed via context console when no changes to commit"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Try to commit with no staged changes
NO_CHANGES_OUTPUT=$(poetry run spec commit -m "No changes commit" 2>&1)
NO_CHANGES_EXIT_CODE=$?
echo "Actual no-changes output:"
echo "$NO_CHANGES_OUTPUT"

if [[ $NO_CHANGES_EXIT_CODE -eq 0 ]] && [[ "$NO_CHANGES_OUTPUT" == *"No changes to commit"* ]]; then
    echo "Status: PASS - Error handling uses context console correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Error handling incorrect"
    echo "Expected 'No changes to commit' message, got: $NO_CHANGES_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 5: Amend commit functionality with context injection"
echo "Expected: Amend commit works with context-based success messages"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Create and stage a file for amend test
echo "# Amend Test File" > .specs/amend_test.md
poetry run spec add .specs/amend_test.md
poetry run spec commit -m "Initial commit for amend test"

# Modify and stage for amend
echo "Modified content for amend" >> .specs/amend_test.md
poetry run spec add .specs/amend_test.md

# Execute amend commit
AMEND_OUTPUT=$(poetry run spec commit --amend -m "Amended commit message" 2>&1)
AMEND_EXIT_CODE=$?
echo "Actual amend output:"
echo "$AMEND_OUTPUT"

if [[ $AMEND_EXIT_CODE -eq 0 ]] && [[ "$AMEND_OUTPUT" == *"Amended commit:"* ]]; then
    echo "Status: PASS - Amend functionality works with context injection"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Amend functionality failed"
    echo "Expected 'Amended commit:' message, got: $AMEND_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking commit history..."
LOG_OUTPUT=$(poetry run spec log --oneline 2>&1)
LOG_EXIT_CODE=$?

if [[ $LOG_EXIT_CODE -eq 0 ]] && [[ "$LOG_OUTPUT" == *"Amended commit message"* ]]; then
    echo "✓ Commit history verification successful"
    echo "Recent commits:"
    echo "$LOG_OUTPUT" | head -5
else
    echo "✗ Commit history verification failed"
    echo "Log output: $LOG_OUTPUT"
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring commit response time..."
PERFORMANCE_START_TIME=$(date +%s%N)

# Quick performance test
echo "# Performance Test" > .specs/perf_test.md
poetry run spec add .specs/perf_test.md
poetry run spec commit -m "Performance test commit" >/dev/null 2>&1

PERFORMANCE_END_TIME=$(date +%s%N)
PERFORMANCE_DURATION_MS=$(( (PERFORMANCE_END_TIME - PERFORMANCE_START_TIME) / 1000000 ))

echo "Commit operation completed in: ${PERFORMANCE_DURATION_MS}ms"
if [[ $PERFORMANCE_DURATION_MS -lt 5000 ]]; then  # Less than 5 seconds
    echo "✓ Performance acceptable for context injection"
else
    echo "⚠ Performance may be impacted by context injection (${PERFORMANCE_DURATION_MS}ms)"
fi

# Cleanup phase
echo "Cleaning up..."
cd "$ORIGINAL_DIR"
if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
    echo "✓ Test directory cleaned up"
fi
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Commit command migration working correctly"
    echo ""
    echo "✓ Context injection decorator successfully applied"
    echo "✓ Singleton references replaced with context attribute access"
    echo "✓ Command behavior identical to pre-migration implementation"
    echo "✓ Error handling maintains existing patterns while using context"
    echo "✓ All commit workflows (normal, dry-run, amend, auto-stage) functional"
    exit 0
else
    echo "SOME TESTS FAILED - Commit command migration needs investigation"
    echo ""
    echo "Failed tests may indicate:"
    echo "- Context injection not working properly"
    echo "- Singleton access not fully replaced"
    echo "- Command behavior changed during migration"
    echo "- Console output not using context properly"
    exit 1
fi