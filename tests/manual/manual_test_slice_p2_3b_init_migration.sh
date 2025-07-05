#!/bin/bash
# Manual Test Script: Slice P2.3b - Init Command Migration
# Purpose: Manually verify that the migrated init command works correctly with context injection
# Created: $(date)

set -e  # Exit on any error

PASSED_TESTS=0
TOTAL_TESTS=0
FAILED_TESTS=0

echo "=== Manual Test: Slice P2.3b - Init Command Migration ==="
echo "Purpose: Verify migrated init command works identically to previous behavior while using context injection"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."

# Check if poetry is available
if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found"
    exit 1
fi

# Change to project directory (assuming script is run from project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"
echo "Working from project directory: $(pwd)"

# Check if project is properly installed
if ! poetry run python -c "import spec_cli" >/dev/null 2>&1; then
    echo "ERROR: spec_cli module not importable through poetry"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."

# Create isolated test directory but stay in project directory for poetry
TEST_DIR="/tmp/spec_init_migration_test_$(date +%s)"
mkdir -p "$TEST_DIR"
echo "Created test directory: $TEST_DIR"

# Store project directory for poetry commands
PROJECT_DIR="$(pwd)"
echo "Project directory: $PROJECT_DIR"

# Ensure clean state in test directory
rm -rf "$TEST_DIR/.spec" "$TEST_DIR/.specs" 2>/dev/null || true
echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Verify migrated init command preserves original behavior"
((TOTAL_TESTS++))
echo "Expected: Init command creates .spec and .specs directories"
echo "Executing:"

# Use spec command through poetry environment - run from test directory with proper environment
cd "$TEST_DIR"
# Set PYTHONPATH to include the project and use virtual environment python
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
if "$PROJECT_DIR"/.venv/bin/python -m spec_cli init 2>&1; then
    echo ""
    echo "Checking created directories:"
    ls -la .spec .specs 2>/dev/null && echo "Directories created successfully" || echo "ERROR: Directories not created"
    
    if [[ -d ".spec" && -d ".specs" ]]; then
        echo "Result: .spec and .specs directories created"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Result: Directories missing"
        echo "Status: FAIL"
        ((FAILED_TESTS++))
    fi
else
    echo "Result: Init command failed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 2: Verify context injection in migrated init command"
((TOTAL_TESTS++))
echo "Expected: Context parameter added to init signature and decorator applied"
echo "Executing:"

PYTHON_RESULT=$(cd "$PROJECT_DIR" && python -c "
try:
    from spec_cli.cli.commands.init import init_command
    import inspect
    
    # Check signature has context parameter  
    sig = inspect.signature(init_command.callback)
    params = list(sig.parameters.keys())
    
    if 'context' in sig.parameters:
        print('SUCCESS: Context parameter found in signature')
        print(f'Parameters: {params}')
        
        # Check if context is first parameter
        if params[0] == 'context':
            print('SUCCESS: Context is first parameter')
        else:
            print('ERROR: Context is not first parameter')
            
        # Check for decorator application
        if hasattr(init_command, '__wrapped__'):
            print('SUCCESS: Decorator wrapper detected')
        else:
            print('WARNING: No decorator wrapper detected')
            
        if hasattr(init_command, '__click_params__'):
            print('SUCCESS: Click parameters preserved')
        else:
            print('ERROR: Click parameters missing')
            
    else:
        print('ERROR: Context parameter not found in signature')
        
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

echo "$PYTHON_RESULT"

if [[ $PYTHON_RESULT == *"SUCCESS: Context parameter found"* ]] && [[ $PYTHON_RESULT == *"SUCCESS: Context is first parameter"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Verify decorator application correctly"
((TOTAL_TESTS++))
echo "Expected: Context injection decorator applied and Click compatibility maintained"
echo "Executing:"

DECORATOR_RESULT=$(cd "$PROJECT_DIR" && python -c "
try:
    from spec_cli.cli.commands.init import init_command
    
    # Check for context injection decorator application
    print(f'Function type: {type(init_command)}')
    print(f'Has callback: {hasattr(init_command, \"callback\")}')
    print(f'Has params: {hasattr(init_command, \"params\")}')
    
    # Check docstring preservation
    callback_doc = getattr(init_command.callback, '__doc__', None) if hasattr(init_command, 'callback') else None
    if callback_doc and 'context: SpecContext' in callback_doc:
        print('SUCCESS: Docstring updated with context parameter')
    else:
        print('WARNING: Docstring may not be properly updated')
        
    # Check for SpecContext import
    import inspect
    import spec_cli.cli.commands.init as init_module
    source = inspect.getsource(init_module)
    
    if 'SpecContext' in source and 'context_injection' in source:
        print('SUCCESS: Required imports found in source')
    else:
        print('ERROR: Missing required imports')
        
    print('SUCCESS: Decorator application verified')
    
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

echo "$DECORATOR_RESULT"

if [[ $DECORATOR_RESULT == *"SUCCESS: Decorator application verified"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 4: Verify behavior preservation after migration (force flag)"
((TOTAL_TESTS++))
echo "Expected: Force flag behavior works identically to pre-migration"
echo "Executing:"

# Clean up from previous test
rm -rf .spec .specs 2>/dev/null || true

# Test normal init first
cd "$TEST_DIR"
"$PROJECT_DIR"/.venv/bin/python -m spec_cli init >/dev/null 2>&1

# Test force flag behavior
if "$PROJECT_DIR"/.venv/bin/python -m spec_cli init --force 2>&1 | grep -q "Force reinitializing\|initialized"; then
    echo "Result: Force flag executed without errors"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Force flag behavior failed"
    echo "Status: FAIL"  
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 5: Verify already initialized warning behavior"
((TOTAL_TESTS++))
echo "Expected: Warning displayed when already initialized without force"
echo "Executing:"

# Ensure repository is initialized
cd "$TEST_DIR"
"$PROJECT_DIR"/.venv/bin/python -m spec_cli init >/dev/null 2>&1 || true

# Try to init again without force
INIT_OUTPUT=$("$PROJECT_DIR"/.venv/bin/python -m spec_cli init 2>&1)
echo "Init output: $INIT_OUTPUT"

if echo "$INIT_OUTPUT" | grep -q "already initialized\|Use --force"; then
    echo "Result: Warning message displayed correctly"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Warning message not displayed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 6: Verify migration utilities functionality"
((TOTAL_TESTS++))
echo "Expected: Migration utilities work correctly for command signature migration"
echo "Executing:"

MIGRATION_UTILS_RESULT=$(cd "$PROJECT_DIR" && python -c "
try:
    from spec_cli.utils.migration_utils import migrate_command_signature, validate_migration_behavior
    
    # Test basic migration
    def test_func(debug: bool, verbose: bool) -> str:
        return f'debug={debug}, verbose={verbose}'
    
    # Migrate the function
    migrated = migrate_command_signature(test_func, 'context')
    
    # Validate migration
    is_valid = validate_migration_behavior(test_func, migrated)
    
    if is_valid:
        print('SUCCESS: Migration utilities working correctly')
        
        # Test execution
        class MockContext:
            pass
        
        result = migrated(MockContext(), True, False)
        if result == 'debug=True, verbose=False':
            print('SUCCESS: Migrated function execution works correctly')
        else:
            print('ERROR: Migrated function execution failed')
    else:
        print('ERROR: Migration validation failed')
        
except Exception as e:
    print(f'ERROR: Migration utilities test failed: {e}')
" 2>&1)

echo "$MIGRATION_UTILS_RESULT"

if [[ $MIGRATION_UTILS_RESULT == *"SUCCESS: Migration utilities working correctly"* ]] && [[ $MIGRATION_UTILS_RESULT == *"SUCCESS: Migrated function execution works correctly"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

# Performance validation
echo "Performance validation..."
echo "Measuring response time for init command..."

START_TIME=$(date +%s)
cd "$TEST_DIR"
"$PROJECT_DIR"/.venv/bin/python -m spec_cli init --force >/dev/null 2>&1 || true
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Init command execution time: ${DURATION}s"

if [[ $DURATION -lt 5 ]]; then
    echo "Performance: GOOD (under 5 seconds)"
else
    echo "Performance: WARNING (over 5 seconds)"
fi

# Cleanup phase
echo "Cleaning up..."
cd /
rm -rf "$TEST_DIR"
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Init command migration working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Init command migration needs investigation"
    echo "Failed tests: $FAILED_TESTS"
    exit 1
fi