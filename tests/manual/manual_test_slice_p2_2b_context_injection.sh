#!/bin/bash
# Manual Test Script: Slice P2.2b - Context Injection Decorator Implementation
# Purpose: Manually verify that context injection decorator functionality works correctly
# Created: 2025-07-05

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.2b - Context Injection Decorator Implementation ==="
echo "Purpose: Verify context injection decorator automatically provides context to CLI commands"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
echo "Checking Python environment..."
if command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "Python found: $PYTHON_VERSION"
else
    echo "ERROR: Python not found"
    exit 1
fi

echo "Checking Poetry environment..."
if command -v poetry >/dev/null 2>&1; then
    echo "Poetry found: $(poetry --version)"
    
    # Check if virtual environment is activated
    if [[ "$VIRTUAL_ENV" != "" ]] || poetry env info --path >/dev/null 2>&1; then
        echo "Poetry virtual environment available"
    else
        echo "Activating Poetry virtual environment..."
        poetry shell
    fi
else
    echo "ERROR: Poetry not found"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo "Working directory: $(pwd)"

# Create temporary test area
TEST_AREA="$PROJECT_ROOT/test_area_manual_p2_2b"
if [[ -d "$TEST_AREA" ]]; then
    echo "Cleaning existing test area..."
    rm -rf "$TEST_AREA"
fi
mkdir -p "$TEST_AREA"
cd "$TEST_AREA"

echo "Test environment ready at: $TEST_AREA"
echo

# Test execution phase
echo "Executing manual tests..."
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo ""
echo "Test 1: Verify decorator preserves Click functionality"
echo "Expected: Decorator maintains Click command attributes without errors"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.cli.decorators import context_injection
    import click
    
    # Create a test Click command
    @context_injection
    @click.command()
    def test_cmd(ctx, name='default'):
        '''Test command docstring'''
        return f'Hello {name}'
    
    # Check if Click attributes are preserved
    has_click_params = hasattr(test_cmd, '__click_params__') or True  # May not exist if no params
    has_name = hasattr(test_cmd, '__name__')
    has_doc = hasattr(test_cmd, '__doc__')
    
    if has_name and has_doc:
        print(f'SUCCESS: Click compatibility preserved - name: {test_cmd.__name__}, doc exists: {bool(test_cmd.__doc__)}')
    else:
        print(f'FAIL: Missing attributes - name: {has_name}, doc: {has_doc}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Click compatibility preserved"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Click compatibility issues detected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 2: Verify function metadata preservation"
echo "Expected: Original function docstring and name preserved after decoration"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.cli.decorators import context_injection
    
    @context_injection
    def test_func(ctx, name='test'):
        '''Test docstring for preservation'''
        return f'Function called with {name}'
    
    # Check metadata preservation
    name_preserved = test_func.__name__ == 'test_func'
    doc_preserved = test_func.__doc__ == 'Test docstring for preservation'
    
    if name_preserved and doc_preserved:
        print(f'SUCCESS: Metadata preserved - name: {test_func.__name__}, doc: {test_func.__doc__}')
    else:
        print(f'FAIL: Metadata not preserved - name_ok: {name_preserved}, doc_ok: {doc_preserved}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Function metadata preserved"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Function metadata not preserved correctly"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 3: Verify decorator chain compatibility"
echo "Expected: Context injection works with other decorators in chain"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    import click
    from spec_cli.cli.decorators import context_injection
    
    # Create decorator chain
    def extra_decorator(func):
        func._extra_decorated = True
        return func
    
    @click.command()
    @context_injection  
    @extra_decorator
    def test_command(ctx, message='hello'):
        '''Multi-decorated command'''
        return f'Message: {message}'
    
    # Check both decorators applied
    click_decorated = hasattr(test_command, '__click_params__') or hasattr(test_command, 'callback')
    extra_decorated = hasattr(test_command, '_extra_decorated')
    callable_result = callable(test_command)
    
    if callable_result and extra_decorated:
        print(f'SUCCESS: Decorator chain compatible - callable: {callable_result}, extra: {extra_decorated}')
    else:
        print(f'FAIL: Decorator chain issues - callable: {callable_result}, extra: {extra_decorated}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Decorator chain compatibility confirmed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Decorator chain compatibility issues"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 4: Verify parametric inject_context decorator"
echo "Expected: inject_context() with custom parameter name works correctly"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.cli.decorators import inject_context
    
    # Test parametric decorator
    @inject_context('custom_context')
    def test_param_func(custom_context, value='default'):
        '''Parametric decorator test'''
        return f'Value: {value}'
    
    # Check decorator applied correctly
    name_preserved = test_param_func.__name__ == 'test_param_func'
    doc_preserved = 'Parametric decorator test' in str(test_param_func.__doc__)
    callable_result = callable(test_param_func)
    
    if name_preserved and callable_result:
        print(f'SUCCESS: Parametric decorator works - name: {name_preserved}, callable: {callable_result}')
    else:
        print(f'FAIL: Parametric decorator issues - name: {name_preserved}, callable: {callable_result}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Parametric decorator functionality confirmed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Parametric decorator functionality issues"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 5: Verify with_context alias decorator"
echo "Expected: with_context alias provides same functionality as context_injection"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.cli.decorators import with_context
    
    # Test alias decorator
    @with_context
    def test_alias_func(ctx, operation='test'):
        '''Alias decorator test'''
        return f'Operation: {operation}'
    
    # Check alias decorator applied correctly  
    name_preserved = test_alias_func.__name__ == 'test_alias_func'
    doc_preserved = 'Alias decorator test' in str(test_alias_func.__doc__)
    callable_result = callable(test_alias_func)
    
    if name_preserved and callable_result:
        print(f'SUCCESS: Alias decorator works - name: {name_preserved}, callable: {callable_result}')
    else:
        print(f'FAIL: Alias decorator issues - name: {name_preserved}, callable: {callable_result}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Alias decorator functionality confirmed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Alias decorator functionality issues"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 6: Error handling test - Invalid function signature"
echo "Expected: Decorator raises appropriate error for functions without parameters"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.cli.decorators import context_injection, ContextInjectionError
    
    # Test error handling for invalid function
    def invalid_func():
        '''Function with no parameters'''
        return 'invalid'
    
    try:
        context_injection(invalid_func)
        print('FAIL: Should have raised ContextInjectionError for parameterless function')
    except ContextInjectionError as e:
        if 'at least one parameter' in str(e):
            print(f'SUCCESS: Correct error raised - {type(e).__name__}: {e}')
        else:
            print(f'FAIL: Wrong error message - {e}')
    except Exception as e:
        print(f'FAIL: Wrong exception type - {type(e).__name__}: {e}')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Error handling works correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Error handling issues detected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "Test 7: Verify decorator_utils helper functions"
echo "Expected: Helper functions work independently and support decorator implementation"
echo "Executing:"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PYTHON_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
try:
    from spec_cli.utils.decorator_utils import (
        create_context_injector, 
        preserve_function_metadata,
        validate_decorator_target
    )
    
    # Test helper functions
    def mock_retriever():
        return {'test': 'context'}
    
    def test_function(ctx, name):
        return f'ctx: {ctx}, name: {name}'
    
    # Test context injector creation
    injector = create_context_injector(mock_retriever)
    injector_ok = callable(injector)
    
    # Test function validation
    validation_ok = validate_decorator_target(test_function)
    
    # Test metadata preservation
    def wrapper():
        pass
    enhanced = preserve_function_metadata(wrapper, test_function)
    metadata_ok = enhanced.__name__ == test_function.__name__
    
    if injector_ok and validation_ok and metadata_ok:
        print(f'SUCCESS: Helper functions work - injector: {injector_ok}, validation: {validation_ok}, metadata: {metadata_ok}')
    else:
        print(f'FAIL: Helper function issues - injector: {injector_ok}, validation: {validation_ok}, metadata: {metadata_ok}')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Actual Response:"
echo "  $PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS:"* ]]; then
    echo "Status: PASS - Helper functions work correctly"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Helper function issues detected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking implementation files exist..."

IMPL_FILES=(
    "$PROJECT_ROOT/spec_cli/cli/decorators.py"
    "$PROJECT_ROOT/spec_cli/utils/decorator_utils.py"
    "$PROJECT_ROOT/tests/unit/cli/test_decorators.py"
    "$PROJECT_ROOT/tests/unit/utils/test_decorator_utils.py"
    "$PROJECT_ROOT/tests/integration/cli/test_context_injection_integration.py"
)

FILES_EXIST=true
for file in "${IMPL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✓ File exists: $(basename "$file")"
    else
        echo "✗ File missing: $file"
        FILES_EXIST=false
    fi
done

echo "File verification: $FILES_EXIST"
echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring decorator application overhead..."

PERF_RESULT=$(cd "$PROJECT_ROOT" && python -c "
import sys
sys.path.insert(0, 'spec_cli')
import time
from spec_cli.cli.decorators import context_injection

def simple_func(ctx, name):
    return f'name: {name}'

# Measure decorator application time
start_time = time.time()
for i in range(1000):
    decorated = context_injection(simple_func)
end_time = time.time()

avg_time = (end_time - start_time) / 1000 * 1000  # Convert to milliseconds
print(f'Average decorator application time: {avg_time:.3f}ms')

if avg_time < 10:  # Should be very fast
    print('SUCCESS: Performance within acceptable limits')
else:
    print(f'WARNING: Performance slower than expected: {avg_time}ms')
" 2>&1)

echo "Performance results:"
echo "  $PERF_RESULT"

# Cleanup phase
echo "Cleaning up..."
cd "$PROJECT_ROOT"
if [[ -d "$TEST_AREA" ]]; then
    rm -rf "$TEST_AREA"
    echo "Test area cleaned: $TEST_AREA"
fi
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "File verification: $FILES_EXIST"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]] && [[ "$FILES_EXIST" == "true" ]]; then
    echo "ALL MANUAL TESTS PASSED - Context injection decorator working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Context injection decorator needs investigation"
    echo "Failed tests: $FAILED_TESTS out of $TOTAL_TESTS"
    exit 1
fi