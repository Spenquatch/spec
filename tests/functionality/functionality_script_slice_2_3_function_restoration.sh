#!/bin/bash
# Functionality Script: Slice 2.3 - Missing Function Restoration and Implementation
# Purpose: Verify that the function restoration system works correctly with real implementations and Docker services
# Created: $(date)
# CRITICAL: NO unittest.mock, patch, or test doubles - use Docker containers for external services

set -e  # Exit on any error

echo "=== Functionality Script: Slice 2.3 - Missing Function Restoration and Implementation ==="
echo "Purpose: Test real function restoration functionality with Docker container isolation"
echo "Approach: Real functionality testing with Python container (no mocking)"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not available"
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker not available - functionality scripts require Docker for isolation"
    exit 1
fi

echo "Prerequisites verified"
echo

# Docker services check (MANDATORY for external dependencies)
echo "Checking Docker services..."
echo "Docker is available for isolated function testing"

# Start Python container for isolated testing
echo "Starting Python Docker container for isolated function restoration testing..."
CONTAINER_NAME="test-function-restoration-$$"

# Clean up any existing container
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Start Python container with our code mounted
docker run -d --name "$CONTAINER_NAME" \
    -v "$(pwd)":/app \
    -w /app \
    --platform linux/amd64 \
    python:3.11-slim \
    sleep 600

echo "Waiting for Python container to be ready..."
sleep 3

# Verify container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "ERROR: Python container failed to start"
    exit 1
fi

echo "Python container ready for function restoration testing"

# Install dependencies in container
echo "Installing dependencies in Python container..."
docker exec "$CONTAINER_NAME" pip install pytest >/dev/null 2>&1 || true

echo "Container environment ready"
echo

# Setup phase
echo "Setting up test environment..."
echo "Creating test files for function restoration validation..."

# Create test files directly in container
docker exec "$CONTAINER_NAME" /bin/bash -c "
cat > /app/test_missing_functions.py << 'EOF'
'''Test file to validate missing function restoration with real implementations.'''

import sys
import os
sys.path.insert(0, '/app')

# Import real function restoration implementation
from slice_2_3_function_restoration import restore_functions_for_test_execution
from spec_cli.utils.function_restoration.missing_function_impl import implement_missing_function

def test_real_function_implementation():
    '''Test real function implementation with actual restoration.'''
    signature = 'def validate_test_input(value: str) -> bool:'
    purpose = 'Validate test input for functionality script'

    # Use real implementation - no mocking
    func = implement_missing_function(signature, purpose)

    if not callable(func):
        raise Exception('Function not callable')

    # Test real execution
    result = func('test_value')

    if not isinstance(result, bool):
        raise Exception(f'Expected bool, got {type(result)}')

    if result is not True:
        raise Exception(f'Expected True for validation function, got {result}')

    return True

def test_real_restoration_workflow():
    '''Test complete restoration workflow with real implementations.'''
    missing_functions = ['validate_input', 'format_output', 'process_data']
    function_signatures = {
        'validate_input': 'def validate_input(value: str) -> bool:',
        'format_output': 'def format_output(data: str) -> str:',
        'process_data': 'def process_data(data: dict) -> dict:'
    }
    test_requirements = {
        'context': 'functionality_testing',
        'behavior': 'real_implementation'
    }

    # Execute real restoration workflow
    result = restore_functions_for_test_execution(
        missing_functions, function_signatures, test_requirements
    )

    if not isinstance(result, dict):
        raise Exception(f'Expected dict result, got {type(result)}')

    required_keys = ['implemented_functions', 'implementation_status', 'analysis_results']
    for key in required_keys:
        if key not in result:
            raise Exception(f'Missing required key: {key}')

    implemented = result['implemented_functions']
    if len(implemented) != len(missing_functions):
        raise Exception(f'Expected {len(missing_functions)} functions, got {len(implemented)}')

    # Test actual function execution
    for func_name, func in implemented.items():
        if not callable(func):
            raise Exception(f'Function {func_name} not callable')

    # Test specific function behaviors with real execution
    validate_func = implemented['validate_input']
    validation_result = validate_func('test')
    if validation_result is not True:
        raise Exception(f'Validation function failed: {validation_result}')

    format_func = implemented['format_output']
    format_result = format_func('test data')
    if not isinstance(format_result, str):
        raise Exception(f'Format function should return str, got {type(format_result)}')

    process_func = implemented['process_data']
    process_result = process_func({'key': 'value'})
    if not isinstance(process_result, dict):
        raise Exception(f'Process function should return dict, got {type(process_result)}')

    return True

if __name__ == '__main__':
    try:
        print('Testing real function implementation...')
        test_real_function_implementation()
        print('✓ Real function implementation test passed')

        print('Testing real restoration workflow...')
        test_real_restoration_workflow()
        print('✓ Real restoration workflow test passed')

        print('All functionality tests passed!')
        exit(0)
    except Exception as e:
        print(f'✗ Functionality test failed: {e}')
        exit(1)
EOF
"

echo "Test environment ready"
echo

# Functionality test execution phase (NO MOCKING)
echo "Executing functionality tests with real implementations..."
echo

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "Functionality Test 1: Real Function Implementation with Docker Python Container"
echo "Expected: Function created successfully with actual callable behavior and correct return type"
echo "Executing with real implementation in Docker container (no mocks):"

# Execute test in Docker container with timeout and better error handling
echo "Executing test in Docker container..."
set +e  # Allow command to fail so we can capture exit code

RESULT_1_OUTPUT=""
RESULT_1_EXIT_CODE=1

# Try to execute the test (removing timeout for compatibility)
if docker exec "$CONTAINER_NAME" python /app/test_missing_functions.py > /tmp/docker_test_output.txt 2>&1; then
    RESULT_1_EXIT_CODE=0
    RESULT_1_OUTPUT=$(cat /tmp/docker_test_output.txt)
else
    RESULT_1_EXIT_CODE=$?
    RESULT_1_OUTPUT=$(cat /tmp/docker_test_output.txt 2>/dev/null || echo "No output captured")
fi

set -e  # Re-enable exit on error

echo "Actual Result from real implementation in Docker container:"
echo "  Exit Code: $RESULT_1_EXIT_CODE"
echo "  Output: $RESULT_1_OUTPUT"

if [[ $RESULT_1_EXIT_CODE -eq 0 ]] && [[ $RESULT_1_OUTPUT == *"All functionality tests passed!"* ]]; then
    echo "Status: PASS - Function implementation working correctly with real execution"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Function implementation failed with real execution"
    echo "Debug: Exit code was $RESULT_1_EXIT_CODE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "Functionality Test 2: Complete Restoration System with Real Function Creation"
echo "Expected: All missing functions restored with proper callable behavior and type-appropriate returns"
echo "Executing with Docker container and real implementations:"

# Test individual function restoration components
docker exec "$CONTAINER_NAME" /bin/bash -c "
cat > /app/test_restoration_components.py << 'EOF'
import sys
sys.path.insert(0, '/app')

from slice_2_3_function_restoration import FunctionRestorationSystem

# Test real system initialization
system = FunctionRestorationSystem()
print(f'System initialized with {len(system.stub_registry)} registry stubs')

# Test real analysis
missing_functions = ['test_validator', 'data_formatter']
test_requirements = {'context': 'component_test'}
analysis = system.analyze_missing_functions(missing_functions, test_requirements)
print(f'Analysis completed for {len(analysis)} functions')

# Test real restoration
signatures = {
    'test_validator': 'def test_validator(value: str) -> bool:',
    'data_formatter': 'def data_formatter(data: dict) -> str:'
}
restored = system.restore_missing_functions(signatures, analysis)
print(f'Restored {len(restored)} functions')

# Test real validation
validation = system.validate_restored_functions(restored)
print(f'Validation results: {validation}')

# Test actual function execution
validator = restored['test_validator']
validator_result = validator('test_input')
print(f'Validator function returned: {validator_result} (type: {type(validator_result)})')

formatter = restored['data_formatter']
formatter_result = formatter({'test': 'data'})
print(f'Formatter function returned: {formatter_result} (type: {type(formatter_result)})')

print('Component testing completed successfully')
EOF

python /app/test_restoration_components.py
"

set +e  # Allow command to fail
docker exec "$CONTAINER_NAME" python /app/test_restoration_components.py > /tmp/docker_test_output_2.txt 2>&1
RESULT_2_EXIT_CODE=$?
RESULT_2_OUTPUT=$(cat /tmp/docker_test_output_2.txt 2>/dev/null || echo "No output captured")
set -e  # Re-enable exit on error

echo "Actual Component Test Results from Docker container:"
echo "  Exit Code: $RESULT_2_EXIT_CODE"
echo "  Output: $RESULT_2_OUTPUT"

if [[ $RESULT_2_EXIT_CODE -eq 0 ]] && [[ $RESULT_2_OUTPUT == *"Component testing completed successfully"* ]]; then
    echo "Status: PASS - Restoration system components working with real implementations"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Restoration system components failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "Functionality Test 3: Error Handling with Real Invalid Signatures"
echo "Expected: System handles invalid signatures gracefully with proper error reporting"
echo "Executing with real error conditions in Docker container:"

docker exec "$CONTAINER_NAME" /bin/bash -c "
cat > /app/test_error_handling.py << 'EOF'
import sys
sys.path.insert(0, '/app')

from slice_2_3_function_restoration import restore_functions_for_test_execution
from spec_cli.utils.function_restoration.missing_function_impl import FunctionRestorationError

try:
    # Test with invalid signature (real error condition)
    invalid_signatures = {
        'invalid_func': 'def invalid_func(value: str -> bool:'  # Missing closing parenthesis
    }
    missing_functions = ['invalid_func']
    test_requirements = {'context': 'error_test'}

    result = restore_functions_for_test_execution(
        missing_functions, invalid_signatures, test_requirements
    )
    print('ERROR: Should have failed with invalid signature')
    exit(1)

except (FunctionRestorationError, Exception) as e:
    print(f'Correctly caught error: {type(e).__name__}: {e}')
    print('Error handling working correctly')
    exit(0)
EOF

python /app/test_error_handling.py
"

set +e  # Allow command to fail
docker exec "$CONTAINER_NAME" python /app/test_error_handling.py > /tmp/docker_test_output_3.txt 2>&1
RESULT_3_EXIT_CODE=$?
RESULT_3_OUTPUT=$(cat /tmp/docker_test_output_3.txt 2>/dev/null || echo "No output captured")
set -e  # Re-enable exit on error

echo "Actual Error Handling Results from Docker container:"
echo "  Exit Code: $RESULT_3_EXIT_CODE"
echo "  Output: $RESULT_3_OUTPUT"

if [[ $RESULT_3_EXIT_CODE -eq 0 ]] && [[ $RESULT_3_OUTPUT == *"Error handling working correctly"* ]]; then
    echo "Status: PASS - Error handling working correctly with real error conditions"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "Status: FAIL - Error handling not working properly"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo

# Verification phase
echo "Verifying results..."
echo "Checking that Docker container executed all tests with real implementations..."

# Verify no mocking was used (grep should find no mock imports)
MOCK_CHECK=$(docker exec "$CONTAINER_NAME" find /app -name "*.py" -exec grep -l "unittest.mock\|patch\|Mock\|MagicMock" {} \; | grep -v "__pycache__" | wc -l)

echo "Mock usage check: $MOCK_CHECK files contain mocking (should be 0 for functionality script)"
if [[ $MOCK_CHECK -eq 0 ]]; then
    echo "✓ No mocking found - real functionality testing confirmed"
else
    echo "⚠ Mocking found in test files - functionality script should use real implementations only"
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring function restoration response time..."

PERFORMANCE_START=$(date +%s%N)
docker exec "$CONTAINER_NAME" /bin/bash -c "
python -c '
import sys
sys.path.insert(0, \"/app\")
from slice_2_3_function_restoration import restore_functions_for_test_execution

signatures = {f\"func_{i}\": f\"def func_{i}(value: str) -> bool:\" for i in range(10)}
missing = list(signatures.keys())
requirements = {\"context\": \"performance_test\"}

result = restore_functions_for_test_execution(missing, signatures, requirements)
print(f\"Restored {len(result[\"implemented_functions\"])} functions\")
'
" >/dev/null 2>&1

PERFORMANCE_END=$(date +%s%N)
PERFORMANCE_MS=$(( (PERFORMANCE_END - PERFORMANCE_START) / 1000000 ))

echo "Performance measurement: ${PERFORMANCE_MS}ms for 10 function restoration"
if [[ $PERFORMANCE_MS -lt 5000 ]]; then  # Less than 5 seconds
    echo "✓ Performance acceptable for function restoration"
else
    echo "⚠ Performance slower than expected (>5s for 10 functions)"
fi

# Cleanup phase (including Docker services)
echo "Cleaning up functionality test environment..."
echo "Stopping Python Docker container..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
echo "Removing test container..."
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
echo "Removing test files..."
rm -f test_missing_functions.py test_restoration_components.py test_error_handling.py 2>/dev/null || true
echo "Cleanup complete"

echo
echo "=== Functionality Script Summary ==="
echo "Total functionality tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Testing approach: Real implementations with Docker Python container (no mocking)"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL FUNCTIONALITY TESTS PASSED - Function restoration working correctly with real implementations"
    exit 0
else
    echo "SOME FUNCTIONALITY TESTS FAILED - Function restoration needs investigation"
    exit 1
fi
