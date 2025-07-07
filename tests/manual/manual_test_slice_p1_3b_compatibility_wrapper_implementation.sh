#!/bin/bash
# Manual Test Script: Slice P1.3b - Compatibility Wrapper Implementation
# Purpose: Manually verify that the implemented compatibility wrapper works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P1.3b - Compatibility Wrapper Implementation ==="
echo "Purpose: Validate compatibility wrapper implementation preserves singleton behavior"
echo "Timestamp: $(date)"
echo

PASSED_TESTS=0
TOTAL_TESTS=0

# Function to increment test counters
pass_test() {
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    echo "Status: PASS"
}

fail_test() {
    ((TOTAL_TESTS++))
    echo "Status: FAIL"
}

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Must run from project root directory"
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: Basic compatibility wrapper creation
echo "Test 1: Basic Compatibility Wrapper Creation"
echo "Expected: Wrapper created successfully with working delegation"
echo "Executing:"
TEST1_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.compatibility_utils import create_singleton_wrapper

class TestSingleton:
    def __init__(self):
        self.value = 'test_value'

    def get_value(self):
        return self.value

try:
    wrapper = create_singleton_wrapper(TestSingleton)
    result = wrapper.get_value()
    print(f'SUCCESS:wrapper_created:value={result}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST1_RESULT"
if [[ $TEST1_RESULT == SUCCESS:wrapper_created:value=test_value ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 2: ProgressManagerWrapper functionality
echo "Test 2: ProgressManagerWrapper Functionality"
echo "Expected: ProgressManagerWrapper delegates to mock singleton correctly"
echo "Executing:"
TEST2_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import ProgressManagerWrapper
from unittest.mock import Mock

class MockProgressManagerSingleton:
    def __init__(self):
        self.manager = Mock()
        self.manager.start_task.return_value = 'task_123'

    def get_progress_manager(self):
        return self.manager

    def set_progress_manager(self, new_manager):
        self.manager = new_manager

try:
    wrapper = ProgressManagerWrapper(MockProgressManagerSingleton)
    manager = wrapper.get_progress_manager()
    task_id = manager.start_task('test_task')
    print(f'SUCCESS:manager_access:task_id={task_id}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST2_RESULT"
if [[ $TEST2_RESULT == SUCCESS:manager_access:task_id=task_123 ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 3: Compatibility Layer wrapper caching
echo "Test 3: Compatibility Layer Wrapper Caching"
echo "Expected: Multiple calls return the same wrapper instance"
echo "Executing:"
TEST3_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import CompatibilityLayer
from unittest.mock import patch, Mock

class MockSingleton:
    def __init__(self):
        pass

try:
    layer = CompatibilityLayer()
    with patch('spec_cli.ui.progress_manager.ProgressManagerSingleton', MockSingleton):
        wrapper1 = layer.get_progress_manager_wrapper()
        wrapper2 = layer.get_progress_manager_wrapper()
        same_instance = wrapper1 is wrapper2
        print(f'SUCCESS:caching_test:same_instance={same_instance}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST3_RESULT"
if [[ $TEST3_RESULT == SUCCESS:caching_test:same_instance=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 4: Transparent method delegation
echo "Test 4: Transparent Method Delegation"
echo "Expected: Wrapper transparently delegates method calls to singleton"
echo "Executing:"
TEST4_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.compatibility_utils import SingletonCompatibilityWrapper

class StatefulSingleton:
    def __init__(self):
        self.counter = 0

    def increment(self):
        self.counter += 1
        return self.counter

    def get_counter(self):
        return self.counter

try:
    wrapper = SingletonCompatibilityWrapper(StatefulSingleton)

    # Test method calls modify singleton state
    count1 = wrapper.increment()
    count2 = wrapper.increment()
    final_count = wrapper.get_counter()

    success = (count1 == 1 and count2 == 2 and final_count == 2)
    print(f'SUCCESS:delegation_test:counts={count1},{count2},{final_count}:success={success}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST4_RESULT"
if [[ $TEST4_RESULT == SUCCESS:delegation_test:counts=1,2,2:success=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 5: Error handling and context preservation
echo "Test 5: Error Handling and Context Preservation"
echo "Expected: Wrapper properly handles and propagates singleton errors"
echo "Executing:"
TEST5_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import ProgressManagerWrapper

class ErroringSingleton:
    def __init__(self):
        pass

    def working_method(self):
        return 'success'

    def failing_method(self):
        raise ValueError('Singleton error')

try:
    wrapper = ProgressManagerWrapper(ErroringSingleton)

    # Test working method
    success_result = wrapper.working_method()

    # Test error propagation
    try:
        wrapper.failing_method()
        error_handled = False
    except ValueError as e:
        error_handled = 'Singleton error' in str(e)

    success = (success_result == 'success' and error_handled)
    print(f'SUCCESS:error_handling:working={success_result}:error_handled={error_handled}:success={success}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST5_RESULT"
if [[ $TEST5_RESULT == SUCCESS:error_handling:working=success:error_handled=True:success=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 6: Thread safety validation
echo "Test 6: Thread Safety Validation"
echo "Expected: Wrapper maintains thread safety during concurrent access"
echo "Executing:"
TEST6_RESULT=$(python -c "
import sys
sys.path.append('.')
import threading
import time
from spec_cli.utils.compatibility_utils import SingletonCompatibilityWrapper

class ThreadSafeSingleton:
    def __init__(self):
        self.counter = 0
        self.lock = threading.Lock()

    def safe_increment(self):
        with self.lock:
            current = self.counter
            time.sleep(0.001)  # Simulate work
            self.counter = current + 1
            return self.counter

try:
    wrapper = SingletonCompatibilityWrapper(ThreadSafeSingleton)
    results = []

    def worker():
        for _ in range(3):
            result = wrapper.safe_increment()
            results.append(result)

    # Start 2 threads
    threads = []
    for _ in range(2):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Check results
    expected_count = 6  # 2 threads * 3 increments
    actual_count = len(results)
    max_value = max(results) if results else 0

    success = (actual_count == expected_count and max_value == expected_count)
    print(f'SUCCESS:thread_safety:count={actual_count}:max={max_value}:success={success}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST6_RESULT"
if [[ $TEST6_RESULT == SUCCESS:thread_safety:count=6:max=6:success=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 7: Global compatibility layer access
echo "Test 7: Global Compatibility Layer Access"
echo "Expected: Global helper function provides working wrapper"
echo "Executing:"
TEST7_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import get_progress_manager_compatibility
from unittest.mock import patch, Mock

class GlobalTestSingleton:
    def __init__(self):
        self.accessed = True

    def get_progress_manager(self):
        return Mock(global_access=True)

try:
    with patch('spec_cli.ui.progress_manager.ProgressManagerSingleton', GlobalTestSingleton):
        wrapper = get_progress_manager_compatibility()
        manager = wrapper.get_progress_manager()

        has_global_access = hasattr(manager, 'global_access') and manager.global_access
        print(f'SUCCESS:global_access:wrapper_available=True:global_access={has_global_access}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST7_RESULT"
if [[ $TEST7_RESULT == SUCCESS:global_access:wrapper_available=True:global_access=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 8: Wrapper behavior validation
echo "Test 8: Wrapper Behavior Validation"
echo "Expected: Wrapper validation confirms behavior matches original"
echo "Executing:"
TEST8_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.compatibility_utils import validate_wrapper_behavior
from unittest.mock import Mock

try:
    # Create original with test methods
    original = Mock()
    original.test_method = Mock(return_value='test_result')
    original.test_attribute = 'test_value'

    # Create wrapper with same interface
    wrapper = Mock()
    wrapper.test_method = Mock(return_value='test_result')
    wrapper.test_attribute = 'test_value'

    validation_result = validate_wrapper_behavior(wrapper, original)
    print(f'SUCCESS:validation:result={validation_result}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST8_RESULT"
if [[ $TEST8_RESULT == SUCCESS:validation:result=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 9: P1.3a compatibility requirements validation
echo "Test 9: P1.3a Compatibility Requirements Validation"
echo "Expected: Wrapper satisfies all P1.3a compatibility requirements"
echo "Executing:"
TEST9_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import ProgressManagerWrapper
from unittest.mock import Mock, patch

class P1_3aCompliantSingleton:
    def __init__(self):
        self.manager = Mock()

    def get_progress_manager(self):
        return self.manager

    def set_progress_manager(self, manager):
        self.manager = manager

    def reset(self):
        self.manager = Mock()

try:
    wrapper = ProgressManagerWrapper(P1_3aCompliantSingleton)

    # Test P1.3a requirements
    has_get_manager = hasattr(wrapper, 'get_progress_manager')
    has_set_manager = hasattr(wrapper, 'set_progress_manager')
    has_reset = hasattr(wrapper, 'reset_progress_manager')
    has_thread_safety = hasattr(wrapper, '_lock')

    # Test functionality
    manager = wrapper.get_progress_manager()
    custom_manager = Mock()
    wrapper.set_progress_manager(custom_manager)

    all_requirements = all([has_get_manager, has_set_manager, has_reset, has_thread_safety])
    print(f'SUCCESS:p1_3a_compliance:requirements={all_requirements}:manager_access=True')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST9_RESULT"
if [[ $TEST9_RESULT == SUCCESS:p1_3a_compliance:requirements=True:manager_access=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Test 10: Migration readiness validation
echo "Test 10: Migration Readiness Validation"
echo "Expected: Wrapper provides bridge for Phase 2 migration to DI"
echo "Executing:"
TEST10_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.core.compatibility import get_progress_manager_compatibility
from unittest.mock import patch, Mock

class MigrationReadySingleton:
    def __init__(self):
        self.mode = 'singleton'
        self.di_ready = True

    def get_progress_manager(self):
        return Mock(mode=self.mode, di_ready=self.di_ready)

try:
    with patch('spec_cli.ui.progress_manager.ProgressManagerSingleton', MigrationReadySingleton):
        wrapper = get_progress_manager_compatibility()
        manager = wrapper.get_progress_manager()

        migration_ready = (manager.mode == 'singleton' and manager.di_ready == True)
        supports_di_bridge = hasattr(wrapper, 'set_progress_manager')

        success = migration_ready and supports_di_bridge
        print(f'SUCCESS:migration_readiness:ready={migration_ready}:di_bridge={supports_di_bridge}:success={success}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result: $TEST10_RESULT"
if [[ $TEST10_RESULT == SUCCESS:migration_readiness:ready=True:di_bridge=True:success=True ]]; then
    pass_test
else
    fail_test
fi
echo

# Cleanup phase (if needed)
echo "Cleaning up..."
echo "No cleanup required for compatibility wrapper tests"
echo "Cleanup complete"
echo

# Summary
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Compatibility wrapper working correctly"
    echo
    echo "=== Compatibility Wrapper Validation Results ==="
    echo "✓ Basic wrapper creation and delegation functional"
    echo "✓ ProgressManagerWrapper preserves singleton behavior"
    echo "✓ Compatibility layer caching works correctly"
    echo "✓ Transparent method delegation operational"
    echo "✓ Error handling and propagation working"
    echo "✓ Thread safety maintained during concurrent access"
    echo "✓ Global compatibility access available"
    echo "✓ Wrapper behavior validation functional"
    echo "✓ P1.3a compatibility requirements satisfied"
    echo "✓ Migration readiness for Phase 2 DI integration confirmed"
    echo
    echo "CONCLUSION: Slice P1.3b compatibility wrapper implementation is SUCCESSFUL"
    echo "- Backward compatibility fully preserved"
    echo "- Transparent access to singleton functionality maintained"
    echo "- Bridge for Phase 2 CLI integration established"
    echo "- All P1.3a requirements satisfied"
    exit 0
else
    echo "SOME TESTS FAILED - Compatibility wrapper needs investigation"
    echo
    echo "Failed tests need attention:"
    echo "- Check implementation against P1.3a requirements"
    echo "- Verify singleton delegation logic"
    echo "- Validate thread safety mechanisms"
    echo "- Review error handling paths"
    exit 1
fi
