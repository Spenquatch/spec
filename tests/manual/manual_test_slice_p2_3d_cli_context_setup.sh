#!/bin/bash
# Manual Test Script: Slice P2.3d - CLI Application Context Setup
# Purpose: Manually verify that CLI context initialization and integration works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.3d - CLI Application Context Setup ==="
echo "Purpose: Verify CLI context initialization and SpecContext integration"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function to run test and capture result
run_test() {
    local test_name="$1"
    local expected="$2"
    shift 2
    local command="$@"

    echo "Test: $test_name"
    echo "Expected: $expected"
    echo "Executing: $command"

    ((TOTAL_TESTS++))

    if output=$(eval "$command" 2>&1); then
        echo "Actual Output:"
        echo "$output"

        # Check if expected text is in output
        if [[ "$output" == *"$expected"* ]]; then
            echo "Status: PASS"
            ((PASSED_TESTS++))
        else
            echo "Status: FAIL - Expected text not found in output"
            ((FAILED_TESTS++))
        fi
    else
        echo "Status: FAIL - Command failed with exit code $?"
        echo "Error output: $output"
        ((FAILED_TESTS++))
    fi
    echo ""
}

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

# Check if spec_cli module is available
if ! python -c "import spec_cli" 2>/dev/null; then
    echo "ERROR: spec_cli module not available"
    echo "Run: pip install -e . or poetry install"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
TEST_DIR="test_cli_context_setup"
rm -rf "$TEST_DIR" 2>/dev/null || true
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
echo "Test environment ready in: $(pwd)"
echo

# Test 1: CLI context initialization functionality
run_test "CLI context initialization" \
    "SpecContext" \
    "python -c \"
from spec_cli.utils.cli_setup_utils import initialize_cli_context
from pathlib import Path
try:
    context = initialize_cli_context(Path('.'))
    print('SUCCESS: SpecContext initialized')
    print(f'Context type: {type(context).__name__}')
    print('Has settings:', hasattr(context, 'settings'))
    print('Has console:', hasattr(context, 'console'))
    print('Has progress:', hasattr(context, 'progress'))
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 2: Click context storage setup
run_test "Click context storage setup" \
    "SUCCESS" \
    "python -c \"
import click
from spec_cli.utils.cli_setup_utils import initialize_cli_context, setup_click_context_storage
from spec_cli.cli.context_integration import retrieve_spec_context
from pathlib import Path
try:
    # Initialize context
    spec_context = initialize_cli_context(Path('.'))

    # Create Click context
    click_ctx = click.Context(click.Command('test'))

    # Setup storage
    setup_click_context_storage(click_ctx, spec_context)

    # Verify retrieval
    retrieved = retrieve_spec_context(click_ctx)
    if retrieved is not None:
        print('SUCCESS: Click context storage working')
        print(f'Retrieved context type: {type(retrieved).__name__}')
    else:
        print('ERROR: Context not retrieved')
        exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 3: CLI app creation with context
run_test "CLI app creation with context" \
    "Group" \
    "python -c \"
from spec_cli.cli.app import create_cli_app
from pathlib import Path
import click
try:
    app = create_cli_app(Path('.'))
    print('SUCCESS: CLI app created with context')
    print(f'App type: {type(app).__name__}')
    print(f'Is Click Group: {isinstance(app, click.Group)}')
    print(f'Number of commands: {len(app.commands)}')
    print(f'Available commands: {list(app.commands.keys())}')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 4: CLI app version command with context
run_test "CLI app version command with context" \
    "Spec CLI v0.1.0" \
    "python -c \"
from spec_cli.cli.app import create_cli_app
from pathlib import Path
import click.testing
try:
    app = create_cli_app(Path('.'))
    runner = click.testing.CliRunner()
    result = runner.invoke(app, ['--version'])
    print(f'Exit code: {result.exit_code}')
    print(f'Output: {result.output.strip()}')
    if result.exit_code == 0 and 'Spec CLI v0.1.0' in result.output:
        print('SUCCESS: Version command with context working')
    else:
        print(f'ERROR: Version command failed')
        exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 5: Context validation functionality
run_test "Context validation functionality" \
    "setup_complete" \
    "python -c \"
import click
from spec_cli.utils.cli_setup_utils import initialize_cli_context, setup_click_context_storage, validate_cli_context_setup
from pathlib import Path
try:
    # Setup context
    spec_context = initialize_cli_context(Path('.'))
    click_ctx = click.Context(click.Command('test'))
    setup_click_context_storage(click_ctx, spec_context)

    # Validate setup
    validation = validate_cli_context_setup(click_ctx)
    print(f'Validation result: {validation}')

    if validation.get('setup_complete', False):
        print('SUCCESS: Context validation working')
    else:
        print('ERROR: Context validation failed')
        exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 6: Integration with P1.2b factory methods
run_test "P1.2b factory integration" \
    "SUCCESS: P1.2b factory method available" \
    "python -c \"
from spec_cli.core.context import SpecContext
from pathlib import Path
import inspect
try:
    # Verify factory method exists
    if hasattr(SpecContext, 'create_for_cli'):
        print('SUCCESS: P1.2b factory method available')

        # Test factory method
        context = SpecContext.create_for_cli(Path('.'))
        print(f'Factory created context: {type(context).__name__}')

        # Verify context properties
        print('Has settings:', hasattr(context, 'settings'))
        print('Has console:', hasattr(context, 'console'))
        print('Has progress:', hasattr(context, 'progress'))
    else:
        print('ERROR: create_for_cli method not found')
        exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Test 7: Integration with P2.1b Click utilities
run_test "P2.1b Click integration" \
    "integrate_spec_context" \
    "python -c \"
from spec_cli.cli.context_integration import integrate_spec_context, retrieve_spec_context
from spec_cli.core.context import SpecContext
import click
from pathlib import Path
try:
    # Test P2.1b integration utilities
    context = SpecContext.create_for_cli(Path('.'))
    click_ctx = click.Context(click.Command('test'))

    # Test integration
    integrate_spec_context(click_ctx, context)
    print('SUCCESS: P2.1b integrate_spec_context working')

    # Test retrieval
    retrieved = retrieve_spec_context(click_ctx)
    if retrieved is not None:
        print('SUCCESS: P2.1b retrieve_spec_context working')
        print(f'Retrieved context matches: {retrieved == context}')
    else:
        print('ERROR: Context retrieval failed')
        exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
\""

# Performance validation
echo "Performance validation..."
echo "Measuring CLI context initialization time..."
PERF_RESULT=$(python -c "
import time
from spec_cli.utils.cli_setup_utils import initialize_cli_context
from pathlib import Path

# Measure initialization time
start = time.time()
for i in range(10):
    context = initialize_cli_context(Path('.'))
end = time.time()

avg_time = (end - start) / 10
print(f'Average initialization time: {avg_time:.4f} seconds')
if avg_time < 0.1:  # Should be under 100ms
    print('PASS: Performance within acceptable range')
else:
    print('WARN: Performance may be slow')
")
echo "$PERF_RESULT"
echo

# Cleanup phase
echo "Cleaning up..."
cd ..
rm -rf "$TEST_DIR"
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo "ALL MANUAL TESTS PASSED - CLI context setup working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - CLI context setup needs investigation"
    exit 1
fi
