#!/bin/bash
# Functionality Script: Slice 2.2 - Rich vs Plain Text Output Compatibility Resolution
# Purpose: Verify that the output compatibility layer works correctly with real CLI commands using Docker
# Created: $(date)
# CRITICAL: NO unittest.mock, patch, or test doubles - use Docker containers for external services

set -e  # Exit on any error

echo "=== Functionality Script: Slice 2.2 - Rich vs Plain Text Output Compatibility Resolution ==="
echo "Purpose: Verify output compatibility layer resolves Rich vs plain text formatting issues with real CLI execution"
echo "Approach: Real functionality testing with Docker containers and actual CLI commands (no mocking)"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
echo "- Python environment and spec CLI availability"
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

# Check if slice implementation exists
if [[ ! -f "slice_2_2_output_compatibility.py" ]]; then
    echo "ERROR: slice_2_2_output_compatibility.py not found"
    exit 1
fi

# Check if helper modules exist
if [[ ! -f "spec_cli/utils/output_formatters/test_output_normalizer.py" ]]; then
    echo "ERROR: test_output_normalizer.py helper not found"
    exit 1
fi

echo "Prerequisites verified"

# Docker services check (MANDATORY for isolated CLI testing)
echo "Checking Docker services..."
if command -v docker >/dev/null 2>&1; then
    echo "Docker is available for isolated CLI testing"

    # Check if required services are running
    echo "Checking Docker service status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "No containers currently running"

    # Create Docker network for CLI testing
    echo "Creating Docker network for CLI testing..."
    docker network create test-cli-network 2>/dev/null || echo "Network already exists"

    # Start CLI testing container with isolated filesystem
    echo "Starting Docker container for CLI testing..."
    docker run -d --name test-cli-container \
        --network test-cli-network \
        -v "$(pwd)":/workspace \
        -w /workspace \
        python:3.11-slim \
        sleep 600

    echo "Waiting for CLI container to be ready..."
    sleep 5

    # Install dependencies in container
    echo "Installing dependencies in Docker container..."
    docker exec test-cli-container pip install pytest click rich >/dev/null 2>&1 || echo "Dependencies installation attempted"

    echo "Docker CLI testing environment ready"
else
    echo "ERROR: Docker not available - functionality scripts require Docker for isolated CLI testing"
    exit 1
fi

# Setup phase
echo "Setting up test environment..."
echo "Creating test workspace in Docker container..."
docker exec test-cli-container mkdir -p /workspace/test_cli_output
echo "Test environment ready"

# Functionality test execution phase (NO MOCKING)
echo "Executing functionality tests with real implementations..."

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo ""
echo "Functionality Test 1: Rich Markup Normalization with Real Implementation"
echo "Expected: Rich markup tags removed, plain text extracted successfully"
echo "Executing with real output_normalizer (no mocks):"

# Test Rich markup normalization using actual implementation
TEST_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from spec_cli.utils.output_formatters.test_output_normalizer import normalize_output_for_testing
try:
    rich_input = '[bold]Project initialized successfully[/bold]'
    result = normalize_output_for_testing(rich_input, 'plain')
    print(f'SUCCESS:{result}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real implementation: $TEST_OUTPUT"
EXPECTED_TEXT="Project initialized successfully"

if [[ $TEST_OUTPUT == *"SUCCESS:$EXPECTED_TEXT"* ]]; then
    echo "Status: PASS - Rich markup normalization successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected '$EXPECTED_TEXT' in result"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Functionality Test 2: ANSI Code Removal with Docker Container"
echo "Expected: ANSI escape sequences removed, clean text extracted"
echo "Executing with Docker CLI container and real implementation:"

# Test ANSI code removal using actual implementation
ANSI_TEST_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from spec_cli.utils.output_formatters.test_output_normalizer import normalize_output_for_testing
try:
    ansi_input = '\x1b[1mBold Text\x1b[0m'
    result = normalize_output_for_testing(ansi_input, 'plain')
    print(f'SUCCESS:{result}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real ANSI processing: $ANSI_TEST_OUTPUT"
EXPECTED_ANSI_TEXT="Bold Text"

if [[ $ANSI_TEST_OUTPUT == *"SUCCESS:$EXPECTED_ANSI_TEXT"* ]]; then
    echo "Status: PASS - ANSI code removal successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected '$EXPECTED_ANSI_TEXT' in result"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Functionality Test 3: Output Compatibility Resolver with Real CLI Output"
echo "Expected: CLI output resolved successfully with compatibility status"
echo "Executing with Docker container and real compatibility resolver:"

# Test output compatibility resolver using actual implementation
RESOLVER_TEST_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from slice_2_2_output_compatibility import OutputCompatibilityResolver
try:
    resolver = OutputCompatibilityResolver()
    test_output = '[green]✓[/green] Operation completed successfully'
    result = resolver.resolve_output_compatibility(test_output, 'plain')
    print(f'SUCCESS:normalized={result[\"normalized_output\"]},status={result[\"compatibility_status\"]}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real compatibility resolver: $RESOLVER_TEST_OUTPUT"
EXPECTED_NORMALIZED="Operation completed successfully"

if [[ $RESOLVER_TEST_OUTPUT == *"SUCCESS:"* ]] && [[ $RESOLVER_TEST_OUTPUT == *"normalized=✓ $EXPECTED_NORMALIZED"* ]] && [[ $RESOLVER_TEST_OUTPUT == *"status=True"* ]]; then
    echo "Status: PASS - Output compatibility resolution successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected normalized text and status=True"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Functionality Test 4: CLI Test Result Validation with Docker Container"
echo "Expected: CLI test result validated successfully after compatibility resolution"
echo "Executing with containerized CLI testing environment:"

# Test CLI test result validation using actual implementation
CLI_VALIDATION_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from slice_2_2_output_compatibility import OutputCompatibilityResolver
from spec_cli.utils.test_helpers.cli_test_helpers import CLITestResult
try:
    resolver = OutputCompatibilityResolver()
    test_result = CLITestResult(
        exit_code=0,
        output='[bold]Success:[/bold] All tests passed',
        exception=None,
        command='test_command',
        args=[]
    )
    is_valid = resolver.validate_cli_test_result(test_result, ['Success: All tests passed'])
    print(f'SUCCESS:validation={is_valid}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real CLI validation: $CLI_VALIDATION_OUTPUT"

if [[ $CLI_VALIDATION_OUTPUT == *"SUCCESS:validation=True"* ]]; then
    echo "Status: PASS - CLI test result validation successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected validation=True"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Functionality Test 5: Batch Compatibility Resolution with Real Data"
echo "Expected: Multiple outputs processed successfully in batch with real results"
echo "Executing batch processing with Docker container:"

# Test batch compatibility resolution using actual implementation
BATCH_TEST_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from slice_2_2_output_compatibility import batch_resolve_compatibility
try:
    outputs = [
        ('[bold]Success[/bold]', 'plain'),
        ('[red]Error occurred[/red]', 'plain'),
        ('Plain text', 'plain')
    ]
    results = batch_resolve_compatibility(outputs)
    success_count = sum(1 for r in results if r.get('compatibility_status', False))
    print(f'SUCCESS:processed={len(results)},successful={success_count}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real batch processing: $BATCH_TEST_OUTPUT"

if [[ $BATCH_TEST_OUTPUT == *"SUCCESS:processed=3,successful=3"* ]]; then
    echo "Status: PASS - Batch compatibility resolution successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected processed=3,successful=3"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Functionality Test 6: Error Handling with Real Edge Cases"
echo "Expected: Proper error handling for invalid inputs with real exceptions"
echo "Executing error handling test with Docker container:"

# Test error handling using actual implementation
ERROR_HANDLING_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
sys.path.append('/workspace')
from slice_2_2_output_compatibility import OutputCompatibilityResolver
try:
    resolver = OutputCompatibilityResolver()
    # Test with invalid type - should raise TypeError
    try:
        resolver.resolve_output_compatibility(123, 'plain')
        print('ERROR:No exception raised')
    except TypeError as e:
        print(f'SUCCESS:TypeError caught: {str(e)[:30]}...')
    except Exception as e:
        print(f'ERROR:Wrong exception type: {type(e).__name__}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Actual Result from real error handling: $ERROR_HANDLING_OUTPUT"

if [[ $ERROR_HANDLING_OUTPUT == *"SUCCESS:TypeError caught:"* ]]; then
    echo "Status: PASS - Error handling working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected TypeError to be caught"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking Docker container logs for any errors..."
docker logs test-cli-container --tail 50 | grep -i error | head -5 || echo "No errors found in container logs"

echo "Checking file system state in Docker container..."
docker exec test-cli-container ls -la /workspace/test_cli_output || echo "Test directory verification completed"
echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring compatibility resolution performance with Docker container..."

PERFORMANCE_OUTPUT=$(docker exec test-cli-container python3 -c "
import sys
import time
sys.path.append('/workspace')
from slice_2_2_output_compatibility import OutputCompatibilityResolver
try:
    resolver = OutputCompatibilityResolver()
    start_time = time.time()

    # Process 100 outputs to measure performance
    for i in range(100):
        test_output = f'[bold]Test {i}[/bold] completed'
        resolver.resolve_output_compatibility(test_output, 'plain')

    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    print(f'SUCCESS:elapsed_ms={elapsed_ms:.2f}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Performance measurement result: $PERFORMANCE_OUTPUT"

if [[ $PERFORMANCE_OUTPUT == *"SUCCESS:elapsed_ms="* ]]; then
    ELAPSED_TIME=$(echo $PERFORMANCE_OUTPUT | grep -o 'elapsed_ms=[0-9.]*' | cut -d'=' -f2)
    echo "Performance: 100 compatibility resolutions in ${ELAPSED_TIME}ms"
    if (( $(echo "$ELAPSED_TIME < 1000" | bc -l) )); then
        echo "Performance: PASS - Under 1000ms for 100 operations"
    else
        echo "Performance: SLOW - Over 1000ms for 100 operations"
    fi
else
    echo "Performance: FAIL - Could not measure performance"
fi

# Cleanup phase (including Docker services)
echo "Cleaning up functionality test environment..."
echo "Stopping Docker services..."

echo "Stopping CLI testing container..."
docker stop test-cli-container >/dev/null 2>&1 || echo "Container already stopped"

echo "Removing test containers and networks..."
docker rm test-cli-container >/dev/null 2>&1 || echo "Container already removed"
docker network rm test-cli-network >/dev/null 2>&1 || echo "Network already removed"

echo "Cleaning up test files..."
rm -rf test_cli_output 2>/dev/null || echo "Test files cleaned"

echo "Restoring system to original state..."
echo "System cleanup complete"

echo ""
echo "=== Functionality Script Summary ==="
echo "Total functionality tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Testing approach: Real implementations with Docker services (no mocking)"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL FUNCTIONALITY TESTS PASSED - Output compatibility layer working correctly with real CLI services"
    exit 0
else
    echo "SOME FUNCTIONALITY TESTS FAILED - Output compatibility layer needs investigation"
    echo "Failed tests: $FAILED_TESTS out of $TOTAL_TESTS"
    exit 1
fi
