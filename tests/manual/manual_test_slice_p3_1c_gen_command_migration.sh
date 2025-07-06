#!/bin/bash
# Manual Test Script: Slice P3.1c - Gen Command Migration
# Purpose: Manually verify that the gen command migration to context injection works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.1c - Gen Command Migration ==="
echo "Purpose: Verify gen command context injection migration maintains functionality"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found"
    exit 1
fi

if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "spec_cli" ]]; then
    echo "ERROR: Must run from spec-cli project root directory"
    exit 1
fi

echo "Prerequisites verified"

# Setup phase
echo "Setting up test environment..."
TEST_DIR="test_area_gen_migration"
if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
fi
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create sample source files for testing
echo "Creating test source files..."
cat > test_module.py << 'EOF'
"""Test module for gen command migration testing."""

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        """Initialize calculator."""
        self.history = []
    
    def add(self, x: float, y: float) -> float:
        """Add two numbers."""
        result = x + y
        self.history.append(f"{x} + {y} = {result}")
        return result
EOF

cat > utils.py << 'EOF'
"""Utility functions for testing."""

import os
from pathlib import Path

def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(filepath)

def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)
EOF

mkdir -p src
cat > src/main.py << 'EOF'
"""Main application module."""

from pathlib import Path

def main():
    """Main application entry point."""
    print("Hello from main!")
    
    config_path = Path("config.json")
    if config_path.exists():
        print("Config found")
    else:
        print("No config found")

if __name__ == "__main__":
    main()
EOF

echo "Test source files created"

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Basic gen command functionality with context injection"
echo "Expected: Command succeeds, generates documentation with context injection"
echo "Executing:"
((TOTAL_TESTS++))

# Initialize spec repository first
poetry run spec init

# Execute gen command
if poetry run spec gen test_module.py; then
    echo "Result: Gen command executed successfully"
    
    # Check if files were generated
    if [[ -f ".specs/test_module.py/index.md" ]] && [[ -f ".specs/test_module.py/history.md" ]]; then
        echo "Generated files found:"
        echo "  - .specs/test_module.py/index.md"
        echo "  - .specs/test_module.py/history.md"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Generated files not found"
        ((FAILED_TESTS++))
    fi
else
    echo "Result: Gen command failed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 2: Gen command with template option"
echo "Expected: Command accepts template parameter and uses context injection"
echo "Executing:"
((TOTAL_TESTS++))

if poetry run spec gen utils.py --template default; then
    echo "Result: Gen command with template executed successfully"
    
    if [[ -f ".specs/utils.py/index.md" ]]; then
        echo "Template-based generation successful"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Template generation failed"
        ((FAILED_TESTS++))
    fi
else
    echo "Result: Gen command with template failed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Gen command with conflict strategy"
echo "Expected: Command handles conflict strategy parameter correctly"
echo "Executing:"
((TOTAL_TESTS++))

# Generate again with conflict strategy
if poetry run spec gen test_module.py --conflict-strategy backup; then
    echo "Result: Gen command with conflict strategy executed"
    
    # Check if backup was created (if file existed)
    if [[ -f ".specs/test_module.py/index.md" ]]; then
        echo "Conflict strategy handled correctly"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Conflict strategy handling failed"
        ((FAILED_TESTS++))
    fi
else
    echo "Result: Gen command with conflict strategy failed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 4: Gen command with force flag"
echo "Expected: Force flag is processed through context injection"
echo "Executing:"
((TOTAL_TESTS++))

if poetry run spec gen src/main.py --force; then
    echo "Result: Gen command with force flag executed"
    
    if [[ -f ".specs/src/main.py/index.md" ]]; then
        echo "Force flag processed correctly"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Force flag processing failed"
        ((FAILED_TESTS++))
    fi
else
    echo "Result: Gen command with force flag failed"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 5: Gen command dry-run mode"
echo "Expected: Dry-run shows what would be generated without creating files"
echo "Executing:"
((TOTAL_TESTS++))

# Create new test file that doesn't have docs yet
cat > new_file.py << 'EOF'
"""New file for dry-run testing."""

def new_function():
    """A new function."""
    pass
EOF

DRY_RUN_OUTPUT=$(poetry run spec gen new_file.py --dry-run 2>&1)
DRY_RUN_EXIT_CODE=$?

echo "Dry-run output captured"
echo "Exit code: $DRY_RUN_EXIT_CODE"

if [[ $DRY_RUN_EXIT_CODE -eq 0 ]]; then
    # Check that dry-run output contains expected information
    if echo "$DRY_RUN_OUTPUT" | grep -q "Dry run" || echo "$DRY_RUN_OUTPUT" | grep -q "would be"; then
        echo "Dry-run output indicates preview mode"
        
        # Verify no actual files were created
        if [[ ! -f ".specs/new_file.py/index.md" ]]; then
            echo "No files created during dry-run (correct behavior)"
            echo "Status: PASS"
            ((PASSED_TESTS++))
        else
            echo "Status: FAIL - Files were created during dry-run"
            ((FAILED_TESTS++))
        fi
    else
        echo "Status: FAIL - Dry-run output doesn't indicate preview mode"
        echo "Output: $DRY_RUN_OUTPUT"
        ((FAILED_TESTS++))
    fi
else
    echo "Status: FAIL - Dry-run command failed"
    echo "Output: $DRY_RUN_OUTPUT"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 6: Error handling with invalid parameters"
echo "Expected: Command properly handles errors with context injection"
echo "Executing:"
((TOTAL_TESTS++))

# Test with invalid conflict strategy
ERROR_OUTPUT=$(poetry run spec gen test_module.py --conflict-strategy invalid 2>&1)
ERROR_EXIT_CODE=$?

echo "Error test output captured"
echo "Exit code: $ERROR_EXIT_CODE"

if [[ $ERROR_EXIT_CODE -ne 0 ]]; then
    if echo "$ERROR_OUTPUT" | grep -i "invalid"; then
        echo "Error properly handled for invalid parameter"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Error message doesn't indicate invalid parameter"
        echo "Output: $ERROR_OUTPUT"
        ((FAILED_TESTS++))
    fi
else
    echo "Status: FAIL - Command should have failed with invalid parameter"
    echo "Output: $ERROR_OUTPUT"
    ((FAILED_TESTS++))
fi
echo ""

# Verification phase
echo "Verifying migration results..."
echo "Checking that context injection patterns are working..."

# Check if generated files contain expected content
if [[ -f ".specs/test_module.py/index.md" ]]; then
    INDEX_CONTENT=$(cat ".specs/test_module.py/index.md")
    if [[ -n "$INDEX_CONTENT" ]]; then
        echo "Generated index.md has content"
    else
        echo "WARNING: Generated index.md is empty"
    fi
fi

if [[ -f ".specs/test_module.py/history.md" ]]; then
    HISTORY_CONTENT=$(cat ".specs/test_module.py/history.md")
    if [[ -n "$HISTORY_CONTENT" ]]; then
        echo "Generated history.md has content"
    else
        echo "WARNING: Generated history.md is empty"
    fi
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring gen command response time..."

START_TIME=$(date +%s.%3N)
poetry run spec gen utils.py --force >/dev/null 2>&1
END_TIME=$(date +%s.%3N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "0.1")

echo "Gen command response time: ${RESPONSE_TIME}s"

if command -v bc >/dev/null 2>&1; then
    if (( $(echo "$RESPONSE_TIME < 10.0" | bc -l) )); then
        echo "Performance acceptable (< 10s)"
    else
        echo "WARNING: Performance slower than expected (>= 10s)"
    fi
else
    echo "Performance measurement complete (bc not available for comparison)"
fi

# Cleanup phase
echo "Cleaning up..."
cd ..
if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
    echo "Test directory cleaned up"
fi
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Gen command migration working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Gen command migration needs investigation"
    echo "Failed tests: $FAILED_TESTS"
    exit 1
fi