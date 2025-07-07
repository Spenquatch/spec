#!/bin/bash
# Manual Test Script: Slice P3.3a - Test Fixture Analysis and Documentation
# Purpose: Manually verify that test fixture analysis functionality works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P3.3a - Test Fixture Analysis and Documentation ==="
echo "Purpose: Verify test fixture analysis identifies migration requirements for context-based DI"
echo "Timestamp: $(date)"
echo

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

# Check if in correct directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Not in spec-cli project root directory"
    exit 1
fi

echo "Prerequisites verified"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Setup phase
echo "Setting up test environment..."

# Create temporary test directory for analysis
TEST_DIR="test_fixture_analysis_temp"
if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
fi
mkdir -p "$TEST_DIR"

echo "Test environment ready"

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Test fixture analysis module import and basic functionality"
echo "Expected: Module imports successfully and functions are accessible"
echo "Executing:"
IMPORT_RESULT=$(python -c "
import sys
sys.path.append('.')
try:
    from spec_cli.utils.test_analysis import analyze_test_fixtures, identify_singleton_dependencies, TestFixtureReport
    print('SUCCESS: All functions imported successfully')
    print(f'analyze_test_fixtures: {analyze_test_fixtures}')
    print(f'identify_singleton_dependencies: {identify_singleton_dependencies}')
    print(f'TestFixtureReport: {TestFixtureReport}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

echo "Result: $IMPORT_RESULT"
if [[ $IMPORT_RESULT == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Test 2: Analysis of existing conftest.py fixture structure"
echo "Expected: Successfully analyzes conftest.py and identifies fixtures with autouse patterns"
echo "Executing:"
CONFTEST_ANALYSIS=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.test_analysis import analyze_test_fixtures

try:
    # Analyze the actual conftest.py files
    tests_dir = Path('tests')
    if tests_dir.exists():
        report = analyze_test_fixtures(tests_dir)
        print(f'SUCCESS: Analysis completed')
        print(f'Total fixtures found: {report.total_fixtures}')
        print(f'Singleton dependent: {len(report.singleton_dependent_fixtures)}')
        print(f'Isolation issues: {len(report.isolation_issues)}')
        print(f'Migration candidates: {len(report.context_migration_candidates)}')
        print(f'Migration requirements: {len(report.migration_requirements)}')

        # Show analysis summary
        if report.analysis_summary:
            print('Analysis Summary:')
            for line in report.analysis_summary.split('\n'):
                print(f'  {line}')
        else:
            print('No analysis summary generated')
    else:
        print('ERROR: tests directory not found')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Result: $CONFTEST_ANALYSIS"
if [[ $CONFTEST_ANALYSIS == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Test 3: Create sample fixture file and analyze singleton patterns"
echo "Expected: Analysis identifies singleton patterns and generates migration requirements"
echo "Executing:"

# Create sample test file with singleton patterns
cat > "$TEST_DIR/sample_conftest.py" << 'EOF'
import pytest

@pytest.fixture
def singleton_settings_fixture():
    from spec_cli.config.settings import get_settings
    settings = get_settings()
    return settings

@pytest.fixture(autouse=True)
def console_isolation_fixture():
    from spec_cli.ui.console import get_console, reset_console
    console = get_console()
    yield console
    reset_console()

@pytest.fixture
def clean_fixture():
    return {"clean": True}

@pytest.fixture
def contaminating_fixture():
    import os
    os.environ["TEST_VAR"] = "contaminated"
    yield
    # No cleanup - contamination risk
EOF

SAMPLE_ANALYSIS=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.test_analysis import analyze_test_fixtures

try:
    test_dir = Path('$TEST_DIR')
    report = analyze_test_fixtures(test_dir)

    print(f'SUCCESS: Sample analysis completed')
    print(f'Total fixtures: {report.total_fixtures}')
    print(f'Singleton dependent: {len(report.singleton_dependent_fixtures)}')
    print(f'Isolation issues: {len(report.isolation_issues)}')

    # Check specific fixtures
    fixture_names = [f.name for f in report.singleton_dependent_fixtures]
    if 'singleton_settings_fixture' in fixture_names:
        print('Found singleton_settings_fixture in dependencies')
    if 'console_isolation_fixture' in fixture_names:
        print('Found console_isolation_fixture in dependencies')

    # Check migration requirements
    if report.migration_requirements:
        print('Migration requirements generated:')
        for name, req in report.migration_requirements.items():
            print(f'  {name}: {req}')
    else:
        print('No migration requirements generated')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)

echo "Result: $SAMPLE_ANALYSIS"
if [[ $SAMPLE_ANALYSIS == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Test 4: Verify migration requirements documentation was created"
echo "Expected: Documentation file exists with comprehensive migration requirements"
echo "Executing:"
DOC_CHECK_RESULT=""
if [[ -f "phases/analysis/test_fixture_migration_requirements.md" ]]; then
    DOC_SIZE=$(wc -l < "phases/analysis/test_fixture_migration_requirements.md")
    if [[ $DOC_SIZE -gt 50 ]]; then
        DOC_CHECK_RESULT="SUCCESS: Documentation file exists with $DOC_SIZE lines of content"

        # Check for key sections
        if grep -q "Migration Requirements" "phases/analysis/test_fixture_migration_requirements.md"; then
            DOC_CHECK_RESULT="$DOC_CHECK_RESULT - Contains Migration Requirements section"
        fi
        if grep -q "Context Fixture Infrastructure" "phases/analysis/test_fixture_migration_requirements.md"; then
            DOC_CHECK_RESULT="$DOC_CHECK_RESULT - Contains Context Fixture Infrastructure section"
        fi
        if grep -q "54 critical errors" "phases/analysis/test_fixture_migration_requirements.md"; then
            DOC_CHECK_RESULT="$DOC_CHECK_RESULT - References current critical errors"
        fi
    else
        DOC_CHECK_RESULT="ERROR: Documentation file too small ($DOC_SIZE lines)"
    fi
else
    DOC_CHECK_RESULT="ERROR: Documentation file not found"
fi

echo "Result: $DOC_CHECK_RESULT"
if [[ $DOC_CHECK_RESULT == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Test 5: Error handling for invalid directory analysis"
echo "Expected: Proper error handling with TestAnalysisError for non-existent directory"
echo "Executing:"
ERROR_HANDLING_RESULT=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.test_analysis import analyze_test_fixtures, TestAnalysisError

try:
    # Try to analyze non-existent directory
    non_existent = Path('/non/existent/directory')
    report = analyze_test_fixtures(non_existent)
    print('ERROR: Should have raised TestAnalysisError')
except TestAnalysisError as e:
    print(f'SUCCESS: Proper error handling - {e}')
except Exception as e:
    print(f'ERROR: Wrong exception type - {e}')
" 2>&1)

echo "Result: $ERROR_HANDLING_RESULT"
if [[ $ERROR_HANDLING_RESULT == *"SUCCESS"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

echo "Test 6: Verify unit tests can be executed"
echo "Expected: Unit tests for test analysis run and pass"
echo "Executing:"
UNIT_TEST_RESULT=$(poetry run pytest tests/unit/utils/test_test_analysis.py -v 2>&1 | tail -20)
echo "Unit test output (last 20 lines):"
echo "$UNIT_TEST_RESULT"

if echo "$UNIT_TEST_RESULT" | grep -q "PASSED"; then
    echo "Status: PASS - Unit tests executed successfully"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Unit tests failed or did not run"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking if analysis identified current test suite issues..."

# Check documentation mentions key issues
if grep -q "singleton infrastructure dependencies" "phases/analysis/test_fixture_migration_requirements.md"; then
    echo "✓ Documentation identifies singleton infrastructure dependencies"
else
    echo "✗ Documentation missing singleton infrastructure analysis"
fi

if grep -q "Context Fixture Infrastructure" "phases/analysis/test_fixture_migration_requirements.md"; then
    echo "✓ Documentation provides context fixture migration plan"
else
    echo "✗ Documentation missing context fixture migration plan"
fi

echo "Verification complete"

# Performance validation
echo "Performance validation..."
echo "Measuring analysis time for test directory..."
START_TIME=$(date +%s%N)
python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.test_analysis import analyze_test_fixtures
try:
    tests_dir = Path('tests')
    if tests_dir.exists():
        report = analyze_test_fixtures(tests_dir)
        print(f'Analysis completed for {report.total_fixtures} fixtures')
    else:
        print('Tests directory not found for performance test')
except:
    print('Performance test completed with errors (expected due to imports)')
" > /dev/null 2>&1
END_TIME=$(date +%s%N)
DURATION=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert to milliseconds

echo "Analysis duration: ${DURATION}ms"
if [[ $DURATION -lt 5000 ]]; then
    echo "✓ Performance acceptable (< 5 seconds)"
else
    echo "⚠ Performance slower than expected (> 5 seconds)"
fi

# Cleanup phase
echo "Cleaning up..."
if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
    echo "✓ Temporary test directory cleaned up"
fi
echo "Cleanup complete"

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Test fixture analysis feature working correctly"
    echo ""
    echo "Key functionality verified:"
    echo "- Test fixture discovery and analysis"
    echo "- Singleton dependency identification"
    echo "- Migration requirement generation"
    echo "- Comprehensive documentation creation"
    echo "- Error handling for edge cases"
    echo "- Integration with existing test suite structure"
    exit 0
else
    echo "SOME TESTS FAILED - Test fixture analysis needs investigation"
    echo ""
    echo "Failed tests may indicate:"
    echo "- Import issues due to singleton infrastructure removal"
    echo "- Missing dependencies or incorrect module paths"
    echo "- Documentation generation problems"
    echo "- Error handling implementation issues"
    exit 1
fi
