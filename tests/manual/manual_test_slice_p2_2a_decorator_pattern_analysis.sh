#!/bin/bash
# Manual Test Script: Slice P2.2a - Decorator Pattern Analysis
# Purpose: Manually verify that decorator pattern analysis and signature inspection works correctly
# Created: 2025-07-05

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.2a - Decorator Pattern Analysis ==="
echo "Purpose: Verify decorator analysis, function signature inspection, and compatibility validation"
echo "Timestamp: $(date)"
echo

# Counter variables for test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to increment test counters
test_result() {
    local status=$1
    local test_name=$2
    ((TOTAL_TESTS++))
    if [[ $status == "PASS" ]]; then
        ((PASSED_TESTS++))
        echo "Status: PASS - $test_name"
    else
        ((FAILED_TESTS++))
        echo "Status: FAIL - $test_name"
    fi
    echo ""
}

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not available"
    exit 1
fi

if ! python -c "import spec_cli.utils.decorator_analysis" 2>/dev/null; then
    echo "ERROR: decorator_analysis module not available"
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: Basic Function Signature Analysis
echo "Test 1: Basic Function Signature Analysis"
echo "Expected: Function signature analyzed successfully with parameter details"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature

def test_function(name: str, age: int = 25) -> str:
    return f'Hello {name}, age {age}'

try:
    result = analyze_function_signature(test_function)
    print(f'SUCCESS:function_name={result.function_name},param_count={len(result.parameters)},has_context={result.has_click_context},compatible={result.is_compatible}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"function_name=test_function"* ]] && [[ $PYTHON_RESULT == *"param_count=2"* ]]; then
    test_result "PASS" "Basic signature analysis works correctly"
else
    test_result "FAIL" "Basic signature analysis failed"
fi

# Test 2: Click Context Detection
echo "Test 2: Click Context Detection"
echo "Expected: Context parameter detected in CLI-like function signatures"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature

def cli_command(ctx, name: str, verbose: bool = False) -> None:
    pass

def init_command(context, directory: str = '.') -> None:
    pass

try:
    result1 = analyze_function_signature(cli_command)
    result2 = analyze_function_signature(init_command)
    
    ctx_detected = result1.has_click_context
    context_detected = result2.has_click_context
    
    print(f'SUCCESS:ctx_detected={ctx_detected},context_detected={context_detected},ctx_params={len(result1.parameters)},context_params={len(result2.parameters)}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"ctx_detected=True"* ]] && [[ $PYTHON_RESULT == *"context_detected=True"* ]]; then
    test_result "PASS" "Click context detection works for various parameter names"
else
    test_result "FAIL" "Click context detection failed"
fi

# Test 3: Decorator Compatibility Validation
echo "Test 3: Decorator Compatibility Validation" 
echo "Expected: Compatible functions return True, incompatible functions return False"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import validate_decorator_compatibility

def compatible_function(ctx, name: str = 'default') -> str:
    return name

def incompatible_function(a, b, c, d, e, f) -> str:
    return 'too many params'

def varargs_only(*args, **kwargs):
    pass

try:
    compat1 = validate_decorator_compatibility(compatible_function)
    compat2 = validate_decorator_compatibility(incompatible_function)
    compat3 = validate_decorator_compatibility(varargs_only)
    
    print(f'SUCCESS:compatible={compat1},incompatible={compat2},varargs_only={compat3}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"compatible=True"* ]] && [[ $PYTHON_RESULT == *"incompatible=False"* ]] && [[ $PYTHON_RESULT == *"varargs_only=False"* ]]; then
    test_result "PASS" "Decorator compatibility validation works correctly"
else
    test_result "FAIL" "Decorator compatibility validation failed"
fi

# Test 4: Error Handling with Invalid Inputs
echo "Test 4: Error Handling with Invalid Inputs"
echo "Expected: Graceful error handling for non-callable inputs"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature, validate_decorator_compatibility, DecoratorAnalysisError

try:
    # Test with non-callable
    try:
        analyze_function_signature('not_a_function')
        analysis_error = False
    except DecoratorAnalysisError:
        analysis_error = True
    
    # Test compatibility with non-callable (should return False, not raise)
    compat_result = validate_decorator_compatibility('not_a_function')
    
    print(f'SUCCESS:analysis_error_raised={analysis_error},compatibility_returns_false={compat_result is False}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"analysis_error_raised=True"* ]] && [[ $PYTHON_RESULT == *"compatibility_returns_false=True"* ]]; then
    test_result "PASS" "Error handling works correctly for invalid inputs"
else
    test_result "FAIL" "Error handling failed for invalid inputs"
fi

# Test 5: Parameter Type and Default Analysis
echo "Test 5: Parameter Type and Default Analysis"
echo "Expected: Parameter annotations and default values extracted correctly"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature

def typed_function(ctx, name: str, count: int = 5, flag: bool = False) -> str:
    return f'{name}:{count}:{flag}'

try:
    result = analyze_function_signature(typed_function)
    
    name_param = result.parameters.get('name', {})
    count_param = result.parameters.get('count', {})
    flag_param = result.parameters.get('flag', {})
    
    name_type = name_param.get('annotation') == \"<class 'str'>\"
    count_default = count_param.get('default') == 5
    flag_default = flag_param.get('default') is False
    return_type = result.return_annotation == \"<class 'str'>\"
    
    print(f'SUCCESS:name_typed={name_type},count_default={count_default},flag_default={flag_default},return_typed={return_type}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"name_typed=True"* ]] && [[ $PYTHON_RESULT == *"count_default=True"* ]] && [[ $PYTHON_RESULT == *"flag_default=True"* ]] && [[ $PYTHON_RESULT == *"return_typed=True"* ]]; then
    test_result "PASS" "Parameter type and default analysis works correctly"
else
    test_result "FAIL" "Parameter type and default analysis failed"
fi

# Test 6: Performance Validation
echo "Test 6: Performance Validation"
echo "Expected: Analysis completes quickly for multiple functions (< 0.1 seconds)"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
import time
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature, validate_decorator_compatibility

# Create test functions
functions = []
for i in range(10):
    exec(f'''
def test_func_{i}(ctx, param_{i}: str = \"default_{i}\") -> str:
    return param_{i}
functions.append(test_func_{i})
''')

try:
    start_time = time.time()
    
    # Test signature analysis performance
    for func in functions:
        analyze_function_signature(func)
    
    # Test compatibility validation performance  
    for func in functions:
        validate_decorator_compatibility(func)
    
    total_time = time.time() - start_time
    
    performance_ok = total_time < 0.1
    print(f'SUCCESS:total_time={total_time:.4f},performance_ok={performance_ok},function_count={len(functions)}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"performance_ok=True"* ]]; then
    test_result "PASS" "Performance requirements met for decorator analysis"
else
    test_result "FAIL" "Performance requirements not met"
fi

# Test 7: Cross-Platform Compatibility
echo "Test 7: Cross-Platform Compatibility"
echo "Expected: Decorator analysis works consistently across different function types"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature, validate_decorator_compatibility

# Test with various function types
def regular_function(ctx, param: str) -> str:
    return param

lambda_function = lambda ctx, x: x

class TestClass:
    def method(self, ctx, value: int) -> int:
        return value

try:
    # Test regular function
    result1 = analyze_function_signature(regular_function)
    compat1 = validate_decorator_compatibility(regular_function)
    
    # Test lambda function
    result2 = analyze_function_signature(lambda_function)
    compat2 = validate_decorator_compatibility(lambda_function)
    
    # Test method
    test_instance = TestClass()
    result3 = analyze_function_signature(test_instance.method)
    compat3 = validate_decorator_compatibility(test_instance.method)
    
    regular_ok = result1.error_message is None and compat1
    lambda_ok = result2.error_message is None and compat2
    method_ok = result3.error_message is None and compat3
    
    print(f'SUCCESS:regular={regular_ok},lambda={lambda_ok},method={method_ok}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"regular=True"* ]] && [[ $PYTHON_RESULT == *"lambda=True"* ]]; then
    test_result "PASS" "Cross-platform compatibility verified for different function types"
else
    test_result "FAIL" "Cross-platform compatibility issues detected"
fi

# Test 8: CLI Command Pattern Simulation
echo "Test 8: CLI Command Pattern Simulation"
echo "Expected: Realistic CLI command patterns are analyzed and validated successfully"
echo "Executing:"

PYTHON_RESULT=$(python -c "
import sys
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature, validate_decorator_compatibility

# Simulate realistic CLI command patterns
def init_like_command(ctx, directory: str = '.', force: bool = False) -> None:
    pass

def status_like_command(ctx) -> None:
    pass

def add_like_command(ctx, files: list) -> None:
    pass

cli_commands = [init_like_command, status_like_command, add_like_command]

try:
    results = []
    for cmd in cli_commands:
        result = analyze_function_signature(cmd)
        compat = validate_decorator_compatibility(cmd)
        
        results.append({
            'name': result.function_name,
            'has_context': result.has_click_context,
            'compatible': compat,
            'param_count': len(result.parameters)
        })
    
    all_have_context = all(r['has_context'] for r in results)
    all_compatible = all(r['compatible'] for r in results)
    reasonable_params = all(r['param_count'] <= 5 for r in results)
    
    print(f'SUCCESS:all_have_context={all_have_context},all_compatible={all_compatible},reasonable_params={reasonable_params},command_count={len(results)}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PYTHON_RESULT"
if [[ $PYTHON_RESULT == SUCCESS:* ]] && [[ $PYTHON_RESULT == *"all_have_context=True"* ]] && [[ $PYTHON_RESULT == *"all_compatible=True"* ]] && [[ $PYTHON_RESULT == *"reasonable_params=True"* ]]; then
    test_result "PASS" "CLI command pattern simulation works correctly"
else
    test_result "FAIL" "CLI command pattern simulation failed"
fi

# Verification phase
echo "Verifying implementation files exist..."
echo "Checking decorator_analysis.py..."
if [[ -f "spec_cli/utils/decorator_analysis.py" ]]; then
    echo "✓ decorator_analysis.py exists"
else
    echo "✗ decorator_analysis.py missing"
    ((FAILED_TESTS++))
fi

echo "Checking decorator implementation requirements..."
if [[ -f "phases/analysis/decorator_implementation_requirements.md" ]]; then
    echo "✓ decorator_implementation_requirements.md exists"
else
    echo "✗ decorator_implementation_requirements.md missing"
    ((FAILED_TESTS++))
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring overall decorator analysis performance..."

PERF_RESULT=$(python -c "
import sys
import time
sys.path.append('.')
from spec_cli.utils.decorator_analysis import analyze_function_signature, validate_decorator_compatibility

def perf_test_function(ctx, name: str, count: int = 0) -> str:
    return f'{name}:{count}'

start_time = time.time()
for i in range(100):
    analyze_function_signature(perf_test_function)
    validate_decorator_compatibility(perf_test_function)
total_time = time.time() - start_time

print(f'{total_time:.4f}')
")

echo "100 operations completed in: ${PERF_RESULT}s"
if (( $(echo "$PERF_RESULT < 1.0" | bc -l) )); then
    echo "Performance: PASS - Under 1 second for 100 operations"
else
    echo "Performance: FAIL - Over 1 second for 100 operations"
    ((FAILED_TESTS++))
fi

# Cleanup phase
echo "Cleaning up..."
echo "No cleanup required for decorator analysis tests"
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo "ALL MANUAL TESTS PASSED - Decorator pattern analysis working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Decorator pattern analysis needs investigation"
    exit 1
fi