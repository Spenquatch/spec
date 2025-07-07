#!/bin/bash
# Manual Test Script: Slice P3.2b - Singleton Detection System Implementation
# Purpose: Manually verify that the singleton detection system accurately identifies singleton patterns
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.2b - Singleton Detection System Implementation ==="
echo "Purpose: Verify singleton detection system accurately identifies patterns and provides clear violation reports"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required but not installed"
    exit 1
fi

if [[ ! -f "tools/singleton_detector.py" ]]; then
    echo "ERROR: singleton_detector.py tool not found"
    exit 1
fi

if [[ ! -f "spec_cli/utils/singleton_detection.py" ]]; then
    echo "ERROR: singleton_detection.py utility not found"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
TEST_DIR="manual_test_temp_$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Test environment ready"
echo

# Test 1: Metaclass Singleton Detection
echo "Test 1: Metaclass Singleton Pattern Detection"
echo "Expected: Detection system identifies metaclass singleton pattern and reports violation"
echo "Executing:"

cat > test_metaclass_singleton.py << 'EOF'
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class TestSingleton(metaclass=SingletonMeta):
    def __init__(self):
        self.value = "singleton_instance"
EOF

echo "Created test file with metaclass singleton pattern"
echo "Running detection tool..."

DETECTION_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
DETECTION_EXIT_CODE=$?

echo "Detection tool output:"
echo "$DETECTION_OUTPUT"
echo "Exit code: $DETECTION_EXIT_CODE"

if [[ $DETECTION_EXIT_CODE -eq 1 ]] && echo "$DETECTION_OUTPUT" | grep -q "metaclass_singleton"; then
    echo "Result: Detection system correctly identified metaclass singleton pattern"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Detection system failed to identify metaclass singleton pattern"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 2: Decorator Singleton Detection
echo "Test 2: Decorator Singleton Pattern Detection"
echo "Expected: Detection system identifies decorator singleton pattern and reports violation"
echo "Executing:"

cat > test_decorator_singleton.py << 'EOF'
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class DecoratedSingleton:
    def __init__(self):
        self.value = "decorated_singleton"
EOF

echo "Created test file with decorator singleton pattern"
echo "Running detection tool..."

DETECTION_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
DETECTION_EXIT_CODE=$?

echo "Detection tool output:"
echo "$DETECTION_OUTPUT"
echo "Exit code: $DETECTION_EXIT_CODE"

if [[ $DETECTION_EXIT_CODE -eq 1 ]] && echo "$DETECTION_OUTPUT" | grep -q -E "(decorator_singleton|singleton)"; then
    echo "Result: Detection system correctly identified decorator singleton pattern"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Detection system failed to identify decorator singleton pattern"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 3: Import Singleton Detection
echo "Test 3: Import-based Singleton Pattern Detection"
echo "Expected: Detection system identifies singleton imports and reports violation"
echo "Executing:"

cat > test_import_singleton.py << 'EOF'
from utils.singleton import singleton_decorator
import singleton

class RegularClass:
    def __init__(self):
        pass

def get_singleton_instance():
    return singleton.getInstance()
EOF

echo "Created test file with singleton import patterns"
echo "Running detection tool..."

DETECTION_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
DETECTION_EXIT_CODE=$?

echo "Detection tool output:"
echo "$DETECTION_OUTPUT"
echo "Exit code: $DETECTION_EXIT_CODE"

if [[ $DETECTION_EXIT_CODE -eq 1 ]] && echo "$DETECTION_OUTPUT" | grep -q -E "(import.*singleton|singleton.*import)"; then
    echo "Result: Detection system correctly identified import singleton patterns"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Detection system failed to identify import singleton patterns"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 4: Clean Code Validation
echo "Test 4: Clean Code Validation (No False Positives)"
echo "Expected: Detection system reports no violations for clean dependency injection code"
echo "Executing:"

cat > test_clean_code.py << 'EOF'
from typing import Protocol

class CacheProtocol(Protocol):
    def get(self, key: str) -> str: ...
    def set(self, key: str, value: str) -> None: ...

class InMemoryCache:
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> str:
        return self._cache.get(key, "")

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value

class DataService:
    def __init__(self, cache: CacheProtocol):
        self.cache = cache

    def process(self, data: str) -> str:
        return f"Processed: {data}"
EOF

echo "Created test file with clean dependency injection code"
echo "Running detection tool..."

DETECTION_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
DETECTION_EXIT_CODE=$?

echo "Detection tool output:"
echo "$DETECTION_OUTPUT"
echo "Exit code: $DETECTION_EXIT_CODE"

# For clean code, the tool should find violations from previous test files but NOT from this clean file
if echo "$DETECTION_OUTPUT" | grep -q "test_clean_code.py"; then
    echo "Result: Detection system incorrectly flagged clean code (false positive)"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
else
    echo "Result: Detection system correctly ignored clean dependency injection code"
    echo "Status: PASS"
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 5: Multiple Patterns in Single File
echo "Test 5: Multiple Singleton Patterns Detection"
echo "Expected: Detection system identifies all singleton patterns in a complex file"
echo "Executing:"

cat > test_multiple_patterns.py << 'EOF'
from singleton_utils import SingletonMeta
import singleton_config

class LegacyManager(metaclass=SingletonMeta):
    def __init__(self):
        self.config = {}

@singleton_decorator
class CacheManager:
    def __init__(self):
        self.cache = {}

def singleton_function():
    return LegacyManager()

@singleton
def get_cache():
    return CacheManager()
EOF

echo "Created test file with multiple singleton patterns"
echo "Running detection tool..."

DETECTION_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
DETECTION_EXIT_CODE=$?

echo "Detection tool output:"
echo "$DETECTION_OUTPUT"
echo "Exit code: $DETECTION_EXIT_CODE"

# Count the number of different violation types detected
VIOLATION_COUNT=$(echo "$DETECTION_OUTPUT" | grep -c -E "(metaclass_singleton|decorator_singleton|import.*singleton|singleton.*import)" || echo "0")

if [[ $DETECTION_EXIT_CODE -eq 1 ]] && [[ $VIOLATION_COUNT -ge 3 ]]; then
    echo "Result: Detection system identified multiple singleton patterns ($VIOLATION_COUNT violations)"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Detection system missed some singleton patterns (found $VIOLATION_COUNT violations, expected >= 3)"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 6: Tool Output Format Validation
echo "Test 6: Tool Output Format and Reporting"
echo "Expected: Detection tool provides structured output with file paths, line numbers, and descriptions"
echo "Executing:"

echo "Running detection tool with verbose output..."
VERBOSE_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive --verbose 2>&1)
echo "Verbose output sample:"
echo "$VERBOSE_OUTPUT" | head -20

# Check if output contains expected structured information
if echo "$VERBOSE_OUTPUT" | grep -q -E "Line [0-9]+:" && echo "$VERBOSE_OUTPUT" | grep -q -E "Description:" && echo "$VERBOSE_OUTPUT" | grep -q -E "Code:"; then
    echo "Result: Tool provides structured output with line numbers, descriptions, and code snippets"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Tool output lacks required structured information"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Test 7: Error Handling Validation
echo "Test 7: Error Handling for Invalid Files"
echo "Expected: Detection system handles invalid Python files gracefully"
echo "Executing:"

cat > invalid_syntax.py << 'EOF'
class BrokenClass(
    def __init__(self):
        pass
EOF

echo "Created file with invalid Python syntax"
echo "Running detection tool..."

INVALID_OUTPUT=$(../../tools/singleton_detector.py . --no-recursive 2>&1)
INVALID_EXIT_CODE=$?

echo "Detection tool output for invalid file:"
echo "$INVALID_OUTPUT"
echo "Exit code: $INVALID_EXIT_CODE"

# Tool should handle errors gracefully and not crash
if [[ $INVALID_EXIT_CODE -ne 2 ]] && echo "$INVALID_OUTPUT" | grep -q -E "(error|Error|ERROR|failed|Failed)"; then
    echo "Result: Detection system handled invalid syntax gracefully with appropriate error reporting"
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Result: Detection system crashed or failed to handle invalid syntax properly"
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking that all test files were created successfully..."
for file in test_metaclass_singleton.py test_decorator_singleton.py test_import_singleton.py test_clean_code.py test_multiple_patterns.py invalid_syntax.py; do
    if [[ -f "$file" ]]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
    fi
done
echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring response time for detection across all test files..."
START_TIME=$(date +%s.%N)
../../tools/singleton_detector.py . --no-recursive >/dev/null 2>&1
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "unknown")

if command -v bc >/dev/null 2>&1; then
    echo "Detection completed in: ${DURATION}s"
    # Performance should be reasonable (under 10 seconds for small test files)
    if (( $(echo "$DURATION < 10.0" | bc -l) )); then
        echo "Performance: ACCEPTABLE (under 10 seconds)"
    else
        echo "Performance: SLOW (over 10 seconds)"
    fi
else
    echo "Performance measurement skipped (bc not available)"
fi
echo

# Cleanup phase
echo "Cleaning up..."
cd ..
rm -rf "$TEST_DIR"
echo "Cleanup complete"
echo

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Singleton detection system working correctly"
    echo ""
    echo "✓ Metaclass singleton patterns detected correctly"
    echo "✓ Decorator singleton patterns detected correctly"
    echo "✓ Import singleton patterns detected correctly"
    echo "✓ Clean code validation (no false positives)"
    echo "✓ Multiple patterns detection in single file"
    echo "✓ Structured output format with line numbers and descriptions"
    echo "✓ Error handling for invalid files"
    echo ""
    echo "The singleton detection system is ready for continuous validation workflows."
    exit 0
else
    echo "SOME TESTS FAILED - Singleton detection system needs investigation"
    echo ""
    echo "Failed tests require debugging before the detection system can be used reliably."
    echo "Check the test output above for specific failure details."
    exit 1
fi
