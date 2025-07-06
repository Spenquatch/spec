#!/bin/bash
# Manual Test Script: Slice P3.2c - Pre-commit Hook Integration
# Purpose: Manually verify that pre-commit hook integration prevents singleton pattern reintroduction
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.2c - Pre-commit Hook Integration ==="
echo "Purpose: Verify pre-commit hooks prevent singleton pattern reintroduction through automated detection"
echo "Timestamp: $(date)"
echo

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: Git is required but not installed"
    exit 1
fi

if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python is required but not installed"
    exit 1
fi

if ! command -v pre-commit >/dev/null 2>&1; then
    echo "WARNING: pre-commit not in PATH - will use poetry run pre-commit"
fi

echo "Prerequisites verified"

# Test variables
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_REPO_DIR="/tmp/spec_hook_test_$(date +%s)"

# Setup phase
echo "Setting up test environment..."
echo "Creating temporary test repository at: $TEST_REPO_DIR"

# Create test repository
mkdir -p "$TEST_REPO_DIR"
cd "$TEST_REPO_DIR"

# Initialize git repository
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"

# Create project structure
mkdir -p spec_cli scripts .git/hooks
mkdir -p tests/manual

# Copy hook script from project
echo "Copying singleton detection script..."
cp "/Users/spensermcconnell/__Active_Code/spec-cli/scripts/check_singletons.py" scripts/
chmod +x scripts/check_singletons.py

# Copy detection module (simplified version for testing)
mkdir -p spec_cli/utils
cat > spec_cli/utils/singleton_detection.py << 'EOF'
"""Simplified singleton detection for testing."""
import ast
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SingletonViolation:
    file_path: Path
    line_number: int
    column: int
    pattern_type: str
    description: str
    code_snippet: str

def scan_for_singleton_patterns(file_path):
    """Simplified singleton pattern detection."""
    violations = []
    try:
        content = file_path.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for singleton patterns
            if any(pattern in line for pattern in ['SingletonMeta', '@singleton', 'singleton_decorator']):
                violations.append(SingletonViolation(
                    file_path=file_path,
                    line_number=i,
                    column=0,
                    pattern_type='detected_singleton',
                    description=f'Detected singleton pattern: {line.strip()}',
                    code_snippet=line.strip()
                ))
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")

    return violations
EOF

# Create empty __init__.py files
touch spec_cli/__init__.py
touch spec_cli/utils/__init__.py

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: singleton-detection
        name: Singleton Pattern Detection
        entry: python scripts/check_singletons.py
        language: system
        files: ^spec_cli/.*\.py$
        description: 'Detect singleton patterns in Python code'
        pass_filenames: true
        require_serial: false
        additional_dependencies: []
EOF

echo "Test environment ready"

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Hook script execution with clean code"
echo "Expected: Exit code 0, no violations reported"
echo "Executing:"

# Create clean Python file
cat > spec_cli/clean_module.py << 'EOF'
"""Clean module without singleton patterns."""

class RegularClass:
    def __init__(self):
        self.value = "clean"

def regular_function():
    return "no singletons here"
EOF

# Test hook script directly
((TOTAL_TESTS++))
echo "python scripts/check_singletons.py spec_cli/clean_module.py"
if python scripts/check_singletons.py spec_cli/clean_module.py; then
    echo "Result: Exit code 0 - Clean code passed"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Exit code $? - Clean code failed unexpectedly"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 2: Hook script execution with singleton code"
echo "Expected: Exit code 1, singleton violations reported"
echo "Executing:"

# Create file with singleton pattern
cat > spec_cli/singleton_module.py << 'EOF'
"""Module with singleton pattern."""

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class MySingleton(metaclass=SingletonMeta):
    def __init__(self):
        self.value = "singleton"
EOF

# Test hook script with singleton code
((TOTAL_TESTS++))
echo "python scripts/check_singletons.py spec_cli/singleton_module.py"
SINGLETON_OUTPUT=$(python scripts/check_singletons.py spec_cli/singleton_module.py 2>&1)
SINGLETON_EXIT_CODE=$?

echo "Actual output:"
echo "$SINGLETON_OUTPUT"
echo "Exit code: $SINGLETON_EXIT_CODE"

if [[ $SINGLETON_EXIT_CODE -eq 1 ]] && [[ "$SINGLETON_OUTPUT" == *"Singleton violations found"* ]]; then
    echo "Status: PASS - Singleton detected and prevented"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected singleton detection and exit code 1"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Pre-commit hook configuration validation"
echo "Expected: Valid YAML configuration with singleton-detection hook"
echo "Executing:"

((TOTAL_TESTS++))
if command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit validate-config"
    if pre-commit validate-config; then
        echo "Result: Pre-commit configuration is valid"
        echo "Status: PASS"
        ((PASSED_TESTS++))
    else
        echo "Result: Pre-commit configuration validation failed"
        echo "Status: FAIL"
        ((FAILED_TESTS++))
    fi
else
    echo "WARNING: pre-commit not available, skipping validation"
    echo "Status: SKIP"
    ((TOTAL_TESTS--))
fi
echo ""

echo "Test 4: Git commit prevention with singleton code"
echo "Expected: Commit blocked by pre-commit hook"
echo "Executing:"

# Set up git repository with files
git add .pre-commit-config.yaml scripts/ spec_cli/
git commit -m "Initial setup" --quiet

# Try to commit singleton code
git add spec_cli/singleton_module.py

((TOTAL_TESTS++))
if command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit run singleton-detection --files spec_cli/singleton_module.py"
    PRECOMMIT_OUTPUT=$(pre-commit run singleton-detection --files spec_cli/singleton_module.py 2>&1)
    PRECOMMIT_EXIT_CODE=$?

    echo "Actual output:"
    echo "$PRECOMMIT_OUTPUT"
    echo "Exit code: $PRECOMMIT_EXIT_CODE"

    if [[ $PRECOMMIT_EXIT_CODE -ne 0 ]]; then
        echo "Status: PASS - Pre-commit hook prevented singleton commit"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Pre-commit hook should have prevented commit"
        ((FAILED_TESTS++))
    fi
else
    echo "WARNING: pre-commit not available, testing hook script directly"
    echo "python scripts/check_singletons.py spec_cli/singleton_module.py"
    DIRECT_OUTPUT=$(python scripts/check_singletons.py spec_cli/singleton_module.py 2>&1)
    DIRECT_EXIT_CODE=$?

    echo "Actual output:"
    echo "$DIRECT_OUTPUT"
    echo "Exit code: $DIRECT_EXIT_CODE"

    if [[ $DIRECT_EXIT_CODE -eq 1 ]]; then
        echo "Status: PASS - Hook script would prevent singleton commit"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Hook script should prevent singleton commit"
        ((FAILED_TESTS++))
    fi
fi
echo ""

echo "Test 5: Git commit success with clean code"
echo "Expected: Commit allowed with clean code"
echo "Executing:"

((TOTAL_TESTS++))
if command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit run singleton-detection --files spec_cli/clean_module.py"
    CLEAN_OUTPUT=$(pre-commit run singleton-detection --files spec_cli/clean_module.py 2>&1)
    CLEAN_EXIT_CODE=$?

    echo "Actual output:"
    echo "$CLEAN_OUTPUT"
    echo "Exit code: $CLEAN_EXIT_CODE"

    if [[ $CLEAN_EXIT_CODE -eq 0 ]]; then
        echo "Status: PASS - Pre-commit hook allowed clean code"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Pre-commit hook should allow clean code"
        ((FAILED_TESTS++))
    fi
else
    echo "WARNING: pre-commit not available, testing hook script directly"
    echo "python scripts/check_singletons.py spec_cli/clean_module.py"
    CLEAN_DIRECT_OUTPUT=$(python scripts/check_singletons.py spec_cli/clean_module.py 2>&1)
    CLEAN_DIRECT_EXIT_CODE=$?

    echo "Actual output:"
    echo "$CLEAN_DIRECT_OUTPUT"
    echo "Exit code: $CLEAN_DIRECT_EXIT_CODE"

    if [[ $CLEAN_DIRECT_EXIT_CODE -eq 0 ]]; then
        echo "Status: PASS - Hook script allows clean code"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Hook script should allow clean code"
        ((FAILED_TESTS++))
    fi
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking hook configuration file exists..."
if [[ -f ".pre-commit-config.yaml" ]]; then
    echo "✓ Pre-commit configuration exists"
else
    echo "✗ Pre-commit configuration missing"
fi

echo "Checking hook script exists and is executable..."
if [[ -x "scripts/check_singletons.py" ]]; then
    echo "✓ Hook script exists and is executable"
else
    echo "✗ Hook script missing or not executable"
fi

echo "Checking singleton detection module..."
if [[ -f "spec_cli/utils/singleton_detection.py" ]]; then
    echo "✓ Singleton detection module available"
else
    echo "✗ Singleton detection module missing"
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring hook execution time..."
START_TIME=$(date +%s%N)
python scripts/check_singletons.py spec_cli/clean_module.py >/dev/null 2>&1
END_TIME=$(date +%s%N)
EXECUTION_TIME=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert to milliseconds

echo "Hook execution time: ${EXECUTION_TIME}ms"
if [[ $EXECUTION_TIME -lt 1000 ]]; then
    echo "✓ Performance acceptable (< 1 second)"
else
    echo "⚠ Performance concern (>= 1 second)"
fi

# Cleanup phase
echo "Cleaning up..."
cd /
echo "Removing test repository: $TEST_REPO_DIR"
if [[ -d "$TEST_REPO_DIR" ]]; then
    rm -rf "$TEST_REPO_DIR"
    echo "✓ Test repository cleaned up"
else
    echo "⚠ Test repository already removed"
fi
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $FAILED_TESTS -eq 0 ]] && [[ $TOTAL_TESTS -gt 0 ]]; then
    echo "ALL MANUAL TESTS PASSED - Pre-commit hook integration working correctly"
    exit 0
else
    echo "SOME TESTS FAILED - Pre-commit hook integration needs investigation"
    exit 1
fi
