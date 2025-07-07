#!/bin/bash
# Manual Test Script: Slice P3.3b - Context-Based Fixture Migration
# Purpose: Manually verify that context-based fixture migration works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.3b - Context-Based Fixture Migration ==="
echo "Purpose: Verify that migrated test fixtures provide isolated contexts for testing"
echo "Timestamp: $(date)"
echo

# Test result counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test results
log_test_result() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    local status="$4"

    echo "Test: $test_name"
    echo "Expected: $expected"
    echo "Actual: $actual"
    echo "Status: $status"
    echo

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [[ "$status" == "PASS" ]]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Prerequisites check
echo "Checking prerequisites..."
if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Must run from project root directory"
    exit 1
fi

if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found. Please install poetry."
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: Verify test migration utils module exists and imports
echo "Test 1: Test migration utils module import"
echo "Expected: Module imports successfully without errors"
IMPORT_RESULT=$(python -c "
try:
    from spec_cli.utils.test_migration_utils import (
        create_context_fixture,
        validate_test_isolation,
        create_mock_context_fixture,
        migrate_singleton_fixture
    )
    print('SUCCESS: All migration utils imported successfully')
except ImportError as e:
    print(f'ERROR: Import failed - {e}')
except Exception as e:
    print(f'ERROR: Unexpected error - {e}')
" 2>&1)

if [[ $IMPORT_RESULT == SUCCESS:* ]]; then
    log_test_result "Migration utils import" "Successful import" "$IMPORT_RESULT" "PASS"
else
    log_test_result "Migration utils import" "Successful import" "$IMPORT_RESULT" "FAIL"
fi

# Test 2: Verify SpecContext factory methods work
echo "Test 2: SpecContext factory methods"
echo "Expected: SpecContext.create_for_testing() creates valid context"
CONTEXT_RESULT=$(python -c "
try:
    from spec_cli.core.context import SpecContext
    context = SpecContext.create_for_testing()
    print(f'SUCCESS: Context created with hash {context.get_context_hash()[:8]}')
except Exception as e:
    print(f'ERROR: Context creation failed - {e}')
" 2>&1)

if [[ $CONTEXT_RESULT == SUCCESS:* ]]; then
    log_test_result "SpecContext factory" "Valid context created" "$CONTEXT_RESULT" "PASS"
else
    log_test_result "SpecContext factory" "Valid context created" "$CONTEXT_RESULT" "FAIL"
fi

# Test 3: Verify conftest.py fixtures are importable
echo "Test 3: Context fixtures from conftest.py"
echo "Expected: Context fixtures can be imported and used"
CONFTEST_RESULT=$(python -c "
import sys
sys.path.append('tests')
try:
    import conftest
    # Check that key fixtures exist
    fixtures = ['spec_context', 'isolated_test_context', 'mock_spec_settings', 'mock_spec_console']
    missing = []
    for fixture_name in fixtures:
        if not hasattr(conftest, fixture_name):
            missing.append(fixture_name)

    if missing:
        print(f'ERROR: Missing fixtures - {missing}')
    else:
        print('SUCCESS: All required context fixtures found in conftest.py')
except Exception as e:
    print(f'ERROR: conftest.py fixture check failed - {e}')
" 2>&1)

if [[ $CONFTEST_RESULT == SUCCESS:* ]]; then
    log_test_result "Conftest fixtures" "All fixtures available" "$CONFTEST_RESULT" "PASS"
else
    log_test_result "Conftest fixtures" "All fixtures available" "$CONFTEST_RESULT" "FAIL"
fi

# Test 4: Run unit tests for migration utils
echo "Test 4: Unit tests for test migration utils"
echo "Expected: All unit tests pass for migration utilities"
echo "Executing: poetry run pytest tests/unit/utils/test_test_migration_utils.py -v"

if poetry run pytest tests/unit/utils/test_test_migration_utils.py -v --tb=short >/dev/null 2>&1; then
    UNIT_TEST_RESULT="SUCCESS: All unit tests passed"
    log_test_result "Migration utils unit tests" "All tests pass" "$UNIT_TEST_RESULT" "PASS"
else
    UNIT_TEST_RESULT="ERROR: Some unit tests failed"
    log_test_result "Migration utils unit tests" "All tests pass" "$UNIT_TEST_RESULT" "FAIL"
fi

# Test 5: Test context fixture creation and isolation
echo "Test 5: Context fixture isolation validation"
echo "Expected: Different fixture instances provide isolated contexts"
ISOLATION_RESULT=$(python -c "
try:
    from spec_cli.utils.test_migration_utils import create_context_fixture
    from spec_cli.core.context import SpecContext

    def test_factory():
        return SpecContext.create_for_testing()

    fixture_func = create_context_fixture(test_factory)

    # Create two contexts
    context1 = fixture_func()
    context2 = fixture_func()

    # Verify isolation
    if context1 is context2:
        print('ERROR: Contexts are the same instance (no isolation)')
    elif context1.get_context_hash() == context2.get_context_hash():
        print('ERROR: Contexts have same hash (potential state sharing)')
    else:
        print('SUCCESS: Contexts are properly isolated')

except Exception as e:
    print(f'ERROR: Context isolation test failed - {e}')
" 2>&1)

if [[ $ISOLATION_RESULT == SUCCESS:* ]]; then
    log_test_result "Context isolation" "Isolated contexts" "$ISOLATION_RESULT" "PASS"
else
    log_test_result "Context isolation" "Isolated contexts" "$ISOLATION_RESULT" "FAIL"
fi

# Test 6: Test validation of test isolation patterns
echo "Test 6: Test isolation pattern validation"
echo "Expected: validate_test_isolation detects good and bad patterns"
VALIDATION_RESULT=$(python -c "
try:
    from spec_cli.utils.test_migration_utils import validate_test_isolation

    def good_test(spec_context):
        return spec_context.settings.debug_enabled

    def bad_test():
        import os
        return os.environ.get('SPEC_DEBUG', False)

    good_result = validate_test_isolation(good_test)
    bad_result = validate_test_isolation(bad_test)

    if good_result is True and bad_result is False:
        print('SUCCESS: Validation correctly identifies good and bad patterns')
    else:
        print(f'ERROR: Validation failed - good: {good_result}, bad: {bad_result}')

except Exception as e:
    print(f'ERROR: Isolation validation test failed - {e}')
" 2>&1)

if [[ $VALIDATION_RESULT == SUCCESS:* ]]; then
    log_test_result "Isolation validation" "Correct pattern detection" "$VALIDATION_RESULT" "PASS"
else
    log_test_result "Isolation validation" "Correct pattern detection" "$VALIDATION_RESULT" "FAIL"
fi

# Test 7: Run integration test for fixture migration
echo "Test 7: Integration test for context-based fixture migration"
echo "Expected: Integration test passes, validating end-to-end fixture migration"
echo "Executing: poetry run pytest tests/integration/test_context_based_fixture_migration.py -v"

if poetry run pytest tests/integration/test_context_based_fixture_migration.py -v --tb=short >/dev/null 2>&1; then
    INTEGRATION_RESULT="SUCCESS: Integration test passed"
    log_test_result "Fixture migration integration" "Integration test passes" "$INTEGRATION_RESULT" "PASS"
else
    INTEGRATION_RESULT="ERROR: Integration test failed"
    log_test_result "Fixture migration integration" "Integration test passes" "$INTEGRATION_RESULT" "FAIL"
fi

# Test 8: Verify mock context fixture customization
echo "Test 8: Mock context fixture customization"
echo "Expected: Mock fixtures can be customized with overrides"
MOCK_RESULT=$(python -c "
try:
    from spec_cli.utils.test_migration_utils import create_mock_context_fixture

    # Create mock fixture with overrides
    mock_fixture = create_mock_context_fixture(
        settings_overrides={'debug_enabled': True, 'console_width': 120},
        console_overrides={'supports_color': False}
    )

    context = mock_fixture()

    # Verify overrides were applied
    if (context.settings.debug_enabled is True and
        context.settings.console_width == 120):
        print('SUCCESS: Mock context fixture customization works')
    else:
        print(f'ERROR: Overrides not applied correctly')

except Exception as e:
    print(f'ERROR: Mock fixture customization failed - {e}')
" 2>&1)

if [[ $MOCK_RESULT == SUCCESS:* ]]; then
    log_test_result "Mock fixture customization" "Overrides applied correctly" "$MOCK_RESULT" "PASS"
else
    log_test_result "Mock fixture customization" "Overrides applied correctly" "$MOCK_RESULT" "FAIL"
fi

# Test 9: Performance validation - fixture creation speed
echo "Test 9: Fixture creation performance"
echo "Expected: Context fixtures create quickly without performance issues"
PERFORMANCE_RESULT=$(python -c "
import time
try:
    from spec_cli.core.context import SpecContext
    from spec_cli.utils.test_migration_utils import create_context_fixture

    def test_factory():
        return SpecContext.create_for_testing()

    fixture_func = create_context_fixture(test_factory)

    # Time fixture creation
    start_time = time.time()
    for i in range(10):
        context = fixture_func()
    end_time = time.time()

    avg_time = (end_time - start_time) / 10

    if avg_time < 0.1:  # Less than 100ms per fixture
        print(f'SUCCESS: Fixture creation is fast ({avg_time:.3f}s average)')
    else:
        print(f'WARNING: Fixture creation is slow ({avg_time:.3f}s average)')

except Exception as e:
    print(f'ERROR: Performance test failed - {e}')
" 2>&1)

if [[ $PERFORMANCE_RESULT == SUCCESS:* ]]; then
    log_test_result "Fixture performance" "Fast fixture creation" "$PERFORMANCE_RESULT" "PASS"
else
    log_test_result "Fixture performance" "Fast fixture creation" "$PERFORMANCE_RESULT" "FAIL"
fi

# Test 10: Error handling verification
echo "Test 10: Error handling in migration utilities"
echo "Expected: Proper error handling for invalid inputs"
ERROR_HANDLING_RESULT=$(python -c "
try:
    from spec_cli.utils.test_migration_utils import (
        create_context_fixture,
        validate_test_isolation,
        TestMigrationError
    )

    errors_caught = 0

    # Test invalid factory method
    try:
        create_context_fixture('not_callable')
    except TestMigrationError:
        errors_caught += 1

    # Test invalid test function
    try:
        validate_test_isolation('not_callable')
    except TestMigrationError:
        errors_caught += 1

    if errors_caught == 2:
        print('SUCCESS: Error handling works correctly')
    else:
        print(f'ERROR: Error handling incomplete - caught {errors_caught}/2 errors')

except Exception as e:
    print(f'ERROR: Error handling test failed - {e}')
" 2>&1)

if [[ $ERROR_HANDLING_RESULT == SUCCESS:* ]]; then
    log_test_result "Error handling" "Proper error catching" "$ERROR_HANDLING_RESULT" "PASS"
else
    log_test_result "Error handling" "Proper error catching" "$ERROR_HANDLING_RESULT" "FAIL"
fi

# Cleanup phase
echo "Cleaning up..."
# No specific cleanup needed for this test
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Context-based fixture migration working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Context-based fixture migration needs investigation"
    exit 1
fi
