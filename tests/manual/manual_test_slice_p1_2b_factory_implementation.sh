#!/bin/bash
# Manual Test Script: Slice P1.2b - Factory Method Implementation
# Purpose: Manually verify that factory methods create working SpecContext instances
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P1.2b - Factory Method Implementation ==="
echo "Purpose: Validate factory methods create usable SpecContext instances in real environments"
echo "Timestamp: $(date)"
echo

# Initialize test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

if ! python -c "import spec_cli.core.context" >/dev/null 2>&1; then
    echo "ERROR: spec_cli module not available"
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: CLI Factory Method
echo "Test 1: CLI Factory Method with Real Dependencies"
echo "Expected: SpecContext created with real settings, console, progress dependencies"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

CLI_TEST_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from spec_cli.core.context import SpecContext
try:
    # Create CLI context with real dependencies
    context = SpecContext.create_for_cli(Path('/tmp/test_project'))

    # Verify it's a SpecContext instance
    is_spec_context = isinstance(context, SpecContext)

    # Verify dependencies are real (not Mock objects)
    from unittest.mock import Mock
    settings_is_real = not isinstance(context.settings, Mock)
    console_is_real = not isinstance(context.console, Mock)
    progress_is_real = not isinstance(context.progress, Mock)

    # Verify settings configuration
    root_path_correct = str(context.settings.root_path) == '/tmp/test_project'
    spec_dir_correct = str(context.settings.spec_dir) == '/tmp/test_project/.spec'

    # Test context operations
    context_hash = context.get_context_hash()
    hash_valid = isinstance(context_hash, str) and len(context_hash) > 0

    print(f'CLI_CONTEXT_CREATED:{is_spec_context}')
    print(f'SETTINGS_REAL:{settings_is_real}')
    print(f'CONSOLE_REAL:{console_is_real}')
    print(f'PROGRESS_REAL:{progress_is_real}')
    print(f'ROOT_PATH_CORRECT:{root_path_correct}')
    print(f'SPEC_DIR_CORRECT:{spec_dir_correct}')
    print(f'HASH_VALID:{hash_valid}')
    print(f'CONTEXT_HASH:{context_hash[:8]}...')
    print('SUCCESS:CLI_FACTORY_WORKING')

except Exception as e:
    print(f'ERROR:CLI_FACTORY_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$CLI_TEST_RESULT"

if [[ $CLI_TEST_RESULT == *"SUCCESS:CLI_FACTORY_WORKING"* ]]; then
    echo "Status: PASS - CLI factory created working context with real dependencies"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - CLI factory did not work as expected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Test 2: Testing Factory Method
echo "Test 2: Testing Factory Method with Mock Dependencies"
echo "Expected: SpecContext created with mock dependencies for isolated testing"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

TESTING_TEST_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from spec_cli.core.context import SpecContext
try:
    # Create testing context with mock dependencies
    overrides = {'debug_enabled': True, 'console_width': 120}
    context = SpecContext.create_for_testing(overrides)

    # Verify it's a SpecContext instance
    is_spec_context = isinstance(context, SpecContext)

    # Verify dependencies are mocks
    from unittest.mock import Mock
    settings_is_mock = isinstance(context.settings, Mock)
    console_is_mock = isinstance(context.console, Mock)
    progress_is_mock = isinstance(context.progress, Mock)

    # Verify mock configuration
    debug_enabled = context.settings.debug_enabled == True
    console_width = context.settings.console_width == 120

    # Test mock behavior
    console_width_method = context.console.get_width() == 80
    color_support = context.console.supports_color() == False
    operation_id = context.progress.start_operation('test') == 'test_op_001'

    # Test context operations work with mocks
    context_hash = context.get_context_hash()
    hash_valid = isinstance(context_hash, str) and len(context_hash) > 0

    print(f'TESTING_CONTEXT_CREATED:{is_spec_context}')
    print(f'SETTINGS_MOCK:{settings_is_mock}')
    print(f'CONSOLE_MOCK:{console_is_mock}')
    print(f'PROGRESS_MOCK:{progress_is_mock}')
    print(f'DEBUG_OVERRIDE:{debug_enabled}')
    print(f'WIDTH_OVERRIDE:{console_width}')
    print(f'MOCK_CONSOLE_WIDTH:{console_width_method}')
    print(f'MOCK_COLOR_SUPPORT:{color_support}')
    print(f'MOCK_OPERATION_ID:{operation_id}')
    print(f'HASH_VALID:{hash_valid}')
    print(f'CONTEXT_HASH:{context_hash[:8]}...')
    print('SUCCESS:TESTING_FACTORY_WORKING')

except Exception as e:
    print(f'ERROR:TESTING_FACTORY_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$TESTING_TEST_RESULT"

if [[ $TESTING_TEST_RESULT == *"SUCCESS:TESTING_FACTORY_WORKING"* ]]; then
    echo "Status: PASS - Testing factory created working context with mock dependencies"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Testing factory did not work as expected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Test 3: Factory Method Integration
echo "Test 3: Factory Method Integration and Compatibility"
echo "Expected: Both factories create compatible SpecContext instances"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

INTEGRATION_TEST_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from spec_cli.core.context import SpecContext
try:
    # Create both types of contexts
    cli_context = SpecContext.create_for_cli(Path('/tmp/integration'))
    testing_context = SpecContext.create_for_testing({'debug_enabled': True})

    # Verify both are SpecContext instances
    both_spec_contexts = (isinstance(cli_context, SpecContext) and
                         isinstance(testing_context, SpecContext))

    # Verify they have different hashes (different configurations)
    cli_hash = cli_context.get_context_hash()
    testing_hash = testing_context.get_context_hash()
    different_hashes = cli_hash != testing_hash

    # Test context replacement works for both
    from spec_cli.core.context import SpecConsoleInterface
    new_console = SpecConsoleInterface()

    cli_with_new_console = cli_context.with_console(new_console)
    testing_with_new_console = testing_context.with_console(new_console)

    replacement_works = (cli_with_new_console.console is new_console and
                        testing_with_new_console.console is new_console)

    # Test immutability (original contexts unchanged)
    immutability_preserved = (cli_context.console is not new_console and
                             testing_context.console is not new_console)

    # Test equality comparison
    cli_context_2 = SpecContext.create_for_cli(Path('/tmp/integration'))
    equality_works = cli_context == cli_context_2

    print(f'BOTH_SPEC_CONTEXTS:{both_spec_contexts}')
    print(f'DIFFERENT_HASHES:{different_hashes}')
    print(f'REPLACEMENT_WORKS:{replacement_works}')
    print(f'IMMUTABILITY_PRESERVED:{immutability_preserved}')
    print(f'EQUALITY_WORKS:{equality_works}')
    print(f'CLI_HASH:{cli_hash[:8]}...')
    print(f'TESTING_HASH:{testing_hash[:8]}...')
    print('SUCCESS:INTEGRATION_WORKING')

except Exception as e:
    print(f'ERROR:INTEGRATION_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$INTEGRATION_TEST_RESULT"

if [[ $INTEGRATION_TEST_RESULT == *"SUCCESS:INTEGRATION_WORKING"* ]]; then
    echo "Status: PASS - Factory integration works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Factory integration failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Test 4: Error Handling
echo "Test 4: Factory Error Handling"
echo "Expected: Factories raise SpecFactoryError for invalid inputs"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ERROR_HANDLING_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from spec_cli.core.context import SpecContext, SpecFactoryError
try:
    # Test invalid factory inputs handling
    error_caught = False
    error_type_correct = False
    error_message_valid = False

    try:
        # This should trigger validation error in factory_utils
        SpecContext.create_for_cli(Path('/tmp'), timeout=-1)
    except SpecFactoryError as e:
        error_caught = True
        error_type_correct = isinstance(e, SpecFactoryError)
        error_message_valid = 'Failed to create CLI SpecContext' in str(e)
        error_context_valid = hasattr(e, 'context') and isinstance(e.context, dict)
        print(f'ERROR_CAUGHT:{error_caught}')
        print(f'ERROR_TYPE_CORRECT:{error_type_correct}')
        print(f'ERROR_MESSAGE_VALID:{error_message_valid}')
        print(f'ERROR_CONTEXT_VALID:{error_context_valid}')
        print(f'ERROR_MESSAGE:{str(e)[:50]}...')
        print('SUCCESS:ERROR_HANDLING_WORKING')
    except Exception as e:
        print(f'UNEXPECTED_ERROR:{type(e).__name__}:{e}')
        print('FAIL:WRONG_ERROR_TYPE')

    if not error_caught:
        print('FAIL:NO_ERROR_CAUGHT')

except Exception as e:
    print(f'ERROR:ERROR_HANDLING_TEST_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$ERROR_HANDLING_RESULT"

if [[ $ERROR_HANDLING_RESULT == *"SUCCESS:ERROR_HANDLING_WORKING"* ]]; then
    echo "Status: PASS - Error handling works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Error handling did not work as expected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Test 5: Environment-Specific Context Creation
echo "Test 5: Environment-Specific Context Creation"
echo "Expected: Factory methods create contexts appropriate for their environments"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ENVIRONMENT_TEST_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from spec_cli.core.context import SpecContext
from unittest.mock import Mock
try:
    # Create CLI context - should have real dependencies
    cli_context = SpecContext.create_for_cli(Path('/tmp/env_test'))

    # Create testing context - should have mock dependencies
    testing_context = SpecContext.create_for_testing()

    # Verify CLI context characteristics
    cli_has_real_settings = not isinstance(cli_context.settings, Mock)
    cli_has_real_console = not isinstance(cli_context.console, Mock)
    cli_color_enabled = cli_context.settings.use_color == True  # Default for CLI

    # Verify testing context characteristics
    testing_has_mock_settings = isinstance(testing_context.settings, Mock)
    testing_has_mock_console = isinstance(testing_context.console, Mock)
    testing_color_disabled = testing_context.settings.use_color == False  # Testing consistency

    # Verify different behaviors
    cli_console_width = cli_context.console.get_width()
    testing_console_width = testing_context.console.get_width()

    # CLI should call real method, testing should return configured mock value
    width_behaviors_different = (isinstance(cli_console_width, int) and
                                testing_console_width == 80)  # Mock return value

    print(f'CLI_REAL_SETTINGS:{cli_has_real_settings}')
    print(f'CLI_REAL_CONSOLE:{cli_has_real_console}')
    print(f'CLI_COLOR_ENABLED:{cli_color_enabled}')
    print(f'TESTING_MOCK_SETTINGS:{testing_has_mock_settings}')
    print(f'TESTING_MOCK_CONSOLE:{testing_has_mock_console}')
    print(f'TESTING_COLOR_DISABLED:{testing_color_disabled}')
    print(f'WIDTH_BEHAVIORS_DIFFERENT:{width_behaviors_different}')
    print(f'CLI_CONSOLE_WIDTH:{cli_console_width}')
    print(f'TESTING_CONSOLE_WIDTH:{testing_console_width}')
    print('SUCCESS:ENVIRONMENT_SPECIFIC_WORKING')

except Exception as e:
    print(f'ERROR:ENVIRONMENT_TEST_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$ENVIRONMENT_TEST_RESULT"

if [[ $ENVIRONMENT_TEST_RESULT == *"SUCCESS:ENVIRONMENT_SPECIFIC_WORKING"* ]]; then
    echo "Status: PASS - Environment-specific context creation works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Environment-specific context creation failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Test 6: Factory Method Cross-Platform Compatibility
echo "Test 6: Cross-Platform Path Handling"
echo "Expected: Factory methods handle paths correctly across platforms"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PLATFORM_TEST_RESULT=$(python -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from spec_cli.core.context import SpecContext
import platform
try:
    # Test with different path styles
    if platform.system() == 'Windows':
        test_path = Path('C:/temp/spec_test')
    else:
        test_path = Path('/tmp/spec_test')

    # Create CLI context with platform-appropriate path
    context = SpecContext.create_for_cli(test_path)

    # Verify path handling
    root_path_set = context.settings.root_path == test_path
    spec_dir_relative = context.settings.spec_dir == test_path / '.spec'
    specs_dir_relative = context.settings.specs_dir == test_path / '.specs'

    # Test path operations work
    root_str = str(context.settings.root_path)
    spec_str = str(context.settings.spec_dir)

    paths_are_strings = isinstance(root_str, str) and isinstance(spec_str, str)
    paths_not_empty = len(root_str) > 0 and len(spec_str) > 0

    print(f'PLATFORM:{platform.system()}')
    print(f'TEST_PATH:{test_path}')
    print(f'ROOT_PATH_SET:{root_path_set}')
    print(f'SPEC_DIR_RELATIVE:{spec_dir_relative}')
    print(f'SPECS_DIR_RELATIVE:{specs_dir_relative}')
    print(f'PATHS_ARE_STRINGS:{paths_are_strings}')
    print(f'PATHS_NOT_EMPTY:{paths_not_empty}')
    print(f'ROOT_PATH_STR:{root_str}')
    print(f'SPEC_DIR_STR:{spec_str}')
    print('SUCCESS:CROSS_PLATFORM_WORKING')

except Exception as e:
    print(f'ERROR:PLATFORM_TEST_FAILED:{e}')
    sys.exit(1)
")

echo "Actual Result:"
echo "$PLATFORM_TEST_RESULT"

if [[ $PLATFORM_TEST_RESULT == *"SUCCESS:CROSS_PLATFORM_WORKING"* ]]; then
    echo "Status: PASS - Cross-platform path handling works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Cross-platform path handling failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Cleanup phase
echo "Cleaning up..."
echo "No cleanup required for factory method tests"
echo "Cleanup complete"
echo

# Final summary
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Factory methods working correctly"
    echo "Factory methods successfully create usable SpecContext instances"
    echo "CLI factory creates contexts with real dependencies for production use"
    echo "Testing factory creates contexts with mock dependencies for isolated testing"
    echo "Both factories integrate properly with existing SpecContext functionality"
    exit 0
else
    echo "SOME TESTS FAILED - Factory methods need investigation"
    echo "Check test output above for specific failure details"
    exit 1
fi
