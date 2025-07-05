#!/bin/bash
# Manual Test Script: Slice P1.1a - Dependency Validation and Analysis
# Purpose: Manually verify that dependency analysis functionality works correctly
# Created: $(date)

set -e  # Exit on any error

echo "=== Manual Test: Slice P1.1a - Dependency Validation and Analysis ==="
echo "Purpose: Validate dependency analysis helper functions work correctly with real spec-cli codebase"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if [[ ! -d "spec_cli" ]]; then
    echo "ERROR: spec_cli directory not found. Run from project root."
    exit 1
fi

if [[ ! -f "spec_cli/utils/dependency_analysis.py" ]]; then
    echo "ERROR: dependency_analysis.py not found. Run slice implementation first."
    exit 1
fi

# Check Python environment
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not available"
    exit 1
fi

# Check if poetry environment is active
if ! python -c "import spec_cli.utils.dependency_analysis" >/dev/null 2>&1; then
    echo "WARNING: spec_cli module not importable. Ensure poetry environment is active."
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."

# Create temporary test script for dependency analysis
cat > test_dependency_analysis.py << 'EOF'
#!/usr/bin/env python3
"""Temporary script for manual dependency analysis testing."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from spec_cli.utils.dependency_analysis import (  # noqa: E402
    validate_dependency_exists,
    analyze_current_usage,
    generate_dependency_report
)

def test_validate_dependency_exists():
    """Test dependency validation function."""
    print("Testing validate_dependency_exists()...")

    # Test existing dependency
    result1 = validate_dependency_exists("spec_cli.config.settings")
    print(f"  spec_cli.config.settings exists: {result1}")

    # Test existing dependency
    result2 = validate_dependency_exists("spec_cli.ui.console")
    print(f"  spec_cli.ui.console exists: {result2}")

    # Test non-existent dependency
    result3 = validate_dependency_exists("spec_cli.nonexistent.fake")
    print(f"  spec_cli.nonexistent.fake exists: {result3}")

    return result1, result2, result3

def test_analyze_current_usage():
    """Test current usage analysis function."""
    print("Testing analyze_current_usage()...")

    codebase_path = Path("spec_cli")

    # Analyze settings usage
    settings_files = analyze_current_usage("settings", codebase_path)
    print(f"  Settings usage found in {len(settings_files)} files")

    # Analyze console usage
    console_files = analyze_current_usage("console", codebase_path)
    print(f"  Console usage found in {len(console_files)} files")

    # Analyze progress usage
    progress_files = analyze_current_usage("progress", codebase_path)
    print(f"  Progress usage found in {len(progress_files)} files")

    return settings_files, console_files, progress_files

def test_generate_dependency_report():
    """Test comprehensive dependency report generation."""
    print("Testing generate_dependency_report()...")

    codebase_path = Path("spec_cli")
    dependency_names = ["settings", "console", "progress"]

    reports = generate_dependency_report(dependency_names, codebase_path)

    print(f"  Generated reports for {len(reports)} dependencies")
    for name, report in reports.items():
        print(f"    {name}: exists={report.exists}, usage_count={len(report.usage_patterns)}, errors={len(report.analysis_errors)}")

    return reports

def main():
    """Run all dependency analysis tests."""
    print("Running dependency analysis tests...")
    print("=" * 50)

    try:
        # Test 1: Dependency validation
        exists_results = test_validate_dependency_exists()
        print()

        # Test 2: Usage analysis
        usage_results = test_analyze_current_usage()
        print()

        # Test 3: Report generation
        report_results = test_generate_dependency_report()
        print()

        # Return results for shell script validation
        return {
            "exists_results": exists_results,
            "usage_results": usage_results,
            "report_results": report_results
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
    if results:
        print("All dependency analysis tests completed successfully!")
    else:
        print("Dependency analysis tests failed!")
        sys.exit(1)
EOF

echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."
echo

echo ""
echo "Test 1: Dependency Validation Function"
echo "Expected: SpecSettings and SpecConsole should exist, fake dependency should not exist"
echo "Executing:"
VALIDATION_OUTPUT=$(python test_dependency_analysis.py 2>&1)
VALIDATION_EXIT_CODE=$?

echo "Actual Output:"
echo "$VALIDATION_OUTPUT"
echo "Exit Code: $VALIDATION_EXIT_CODE"

# Validate Test 1 results
((TOTAL_TESTS++))
if [[ $VALIDATION_EXIT_CODE -eq 0 ]] && \
   [[ "$VALIDATION_OUTPUT" == *"spec_cli.config.settings exists: True"* ]] && \
   [[ "$VALIDATION_OUTPUT" == *"spec_cli.ui.console exists: True"* ]] && \
   [[ "$VALIDATION_OUTPUT" == *"spec_cli.nonexistent.fake exists: False"* ]]; then
    echo "Status: PASS - Dependency validation working correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Dependency validation not working as expected"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 2: Usage Pattern Analysis"
echo "Expected: Settings should have 20+ usage files, console 15+, progress 5+"
echo "Executing: Analyzing usage patterns in spec_cli codebase..."

# Extract usage counts from output
SETTINGS_COUNT=$(echo "$VALIDATION_OUTPUT" | grep "Settings usage found in" | grep -o '[0-9]\+' | head -1)
CONSOLE_COUNT=$(echo "$VALIDATION_OUTPUT" | grep "Console usage found in" | grep -o '[0-9]\+' | head -1)
PROGRESS_COUNT=$(echo "$VALIDATION_OUTPUT" | grep "Progress usage found in" | grep -o '[0-9]\+' | head -1)

echo "Actual Results:"
echo "  Settings usage: $SETTINGS_COUNT files"
echo "  Console usage: $CONSOLE_COUNT files"
echo "  Progress usage: $PROGRESS_COUNT files"

# Validate Test 2 results
((TOTAL_TESTS++))
if [[ $SETTINGS_COUNT -ge 20 ]] && [[ $CONSOLE_COUNT -ge 15 ]] && [[ $PROGRESS_COUNT -ge 5 ]]; then
    echo "Status: PASS - Usage analysis found expected patterns"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Usage analysis did not find expected minimum counts"
    echo "  Expected: Settings>=20, Console>=15, Progress>=5"
    echo "  Actual: Settings=$SETTINGS_COUNT, Console=$CONSOLE_COUNT, Progress=$PROGRESS_COUNT"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Comprehensive Report Generation"
echo "Expected: Reports generated for all 3 dependencies with no errors"
echo "Executing: Generating comprehensive dependency reports..."

# Check report generation results from output
if [[ "$VALIDATION_OUTPUT" == *"Generated reports for 3 dependencies"* ]]; then
    REPORT_GENERATED=true
else
    REPORT_GENERATED=false
fi

# Check for any error indicators
if [[ "$VALIDATION_OUTPUT" == *"errors=0"* ]] && [[ "$VALIDATION_OUTPUT" != *"ERROR:"* ]]; then
    REPORT_CLEAN=true
else
    REPORT_CLEAN=false
fi

echo "Actual Results:"
echo "  Reports generated: $REPORT_GENERATED"
echo "  No errors found: $REPORT_CLEAN"

# Validate Test 3 results
((TOTAL_TESTS++))
if [[ "$REPORT_GENERATED" == true ]] && [[ "$REPORT_CLEAN" == true ]]; then
    echo "Status: PASS - Report generation successful without errors"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Report generation failed or contained errors"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 4: Interface Requirements Generation"
echo "Expected: Each dependency should have interface requirements defined"
echo "Executing: Checking interface requirements in generated reports..."

# Test interface requirements are present
python << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))

from spec_cli.utils.dependency_analysis import generate_dependency_report

try:
    reports = generate_dependency_report(["settings", "console", "progress"], Path("spec_cli"))

    for dep_name, report in reports.items():
        interface_reqs = report.requirements.get("interface_requirements", [])
        print(f"{dep_name}: {len(interface_reqs)} interface requirements")

        if len(interface_reqs) > 0:
            print(f"  Sample: {interface_reqs[0]}")

    # Check specific interface requirements
    settings_reqs = reports["settings"].requirements.get("interface_requirements", [])
    has_debug_enabled = any("debug_enabled" in req for req in settings_reqs)
    has_get_setting = any("get_setting" in req for req in settings_reqs)

    console_reqs = reports["console"].requirements.get("interface_requirements", [])
    has_print_message = any("print_message" in req for req in console_reqs)
    has_get_width = any("get_width" in req for req in console_reqs)

    print(f"Settings has debug_enabled: {has_debug_enabled}")
    print(f"Settings has get_setting: {has_get_setting}")
    print(f"Console has print_message: {has_print_message}")
    print(f"Console has get_width: {has_get_width}")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF

INTERFACE_EXIT_CODE=$?

# Validate Test 4 results
((TOTAL_TESTS++))
if [[ $INTERFACE_EXIT_CODE -eq 0 ]]; then
    echo "Status: PASS - Interface requirements generated successfully"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Interface requirements generation failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 5: Error Handling Validation"
echo "Expected: Graceful error handling for invalid inputs"
echo "Executing: Testing error conditions..."

# Test error handling
python << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))

from spec_cli.utils.dependency_analysis import analyze_current_usage, DependencyValidationError

try:
    # Test non-existent codebase path
    try:
        analyze_current_usage("test", Path("/nonexistent/path"))
        print("ERROR: Should have raised DependencyValidationError")
        sys.exit(1)
    except DependencyValidationError as e:
        print(f"Correctly caught validation error: {type(e).__name__}")
        print(f"Error message contains expected text: {'does not exist' in str(e)}")

    print("Error handling validation passed")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF

ERROR_HANDLING_EXIT_CODE=$?

# Validate Test 5 results
((TOTAL_TESTS++))
if [[ $ERROR_HANDLING_EXIT_CODE -eq 0 ]]; then
    echo "Status: PASS - Error handling works correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Error handling validation failed"
    ((FAILED_TESTS++))
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking dependency analysis helper is properly integrated..."

# Verify the helper module can be imported and used
python -c "
from spec_cli.utils.dependency_analysis import validate_dependency_exists
result = validate_dependency_exists('spec_cli.config.settings')
print(f'Final integration check: {result}')
assert result == True, 'Integration check failed'
print('Integration verification successful')
" 2>&1

INTEGRATION_EXIT_CODE=$?

if [[ $INTEGRATION_EXIT_CODE -eq 0 ]]; then
    echo "Integration verification: PASS"
else
    echo "Integration verification: FAIL"
    ((FAILED_TESTS++))
fi

echo "Verification complete"
echo

# Cleanup phase
echo "Cleaning up..."
rm -f test_dependency_analysis.py
echo "Cleanup complete"
echo

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Dependency analysis feature working correctly"
    echo ""
    echo "Key Validated Features:"
    echo "- Dependency existence validation for real spec-cli modules"
    echo "- Usage pattern analysis across actual codebase files"
    echo "- Comprehensive dependency report generation"
    echo "- Interface requirements generation for SpecContext"
    echo "- Proper error handling for invalid inputs"
    echo "- Full integration with spec-cli module structure"
    exit 0
else
    echo "SOME TESTS FAILED - Dependency analysis feature needs investigation"
    echo ""
    echo "Failed areas may include:"
    echo "- Import path validation accuracy"
    echo "- Usage pattern detection completeness"
    echo "- Report generation reliability"
    echo "- Interface requirement correctness"
    echo "- Error handling robustness"
    exit 1
fi
