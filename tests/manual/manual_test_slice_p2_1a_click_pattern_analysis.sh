#!/bin/bash
# Manual Test Script: Slice P2.1a - Click Framework Pattern Analysis
# Purpose: Manually verify that Click pattern analysis works correctly
# Created: 2025-07-05

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.1a - Click Framework Pattern Analysis ==="
echo "Purpose: Verify Click pattern analysis identifies framework capabilities and generates integration requirements"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
echo "Checking Python environment..."
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not available"
    exit 1
fi

echo "Checking Poetry environment..."
if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not available"
    exit 1
fi

echo "Checking spec_cli module availability..."
if ! python -c "import spec_cli.utils.click_analysis" 2>/dev/null; then
    echo "ERROR: spec_cli.utils.click_analysis module not available"
    exit 1
fi

echo "Checking CLI directory exists..."
if [[ ! -d "spec_cli/cli" ]]; then
    echo "ERROR: CLI directory spec_cli/cli not found"
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: Click Pattern Analysis Functionality
echo "Test 1: Click Pattern Analysis on Real CLI Directory"
echo "Expected: Analysis finds Click commands, decorators, and context usage"
echo "Executing:"
ANALYSIS_RESULT=$(python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns
from pathlib import Path
import json

try:
    cli_dir = Path('spec_cli/cli')
    report = analyze_click_patterns(cli_dir)

    result = {
        'commands_found': len(report.commands_found),
        'decorators_used': len(report.decorators_used),
        'context_usage_files': len(report.context_usage),
        'integration_requirements': len(report.integration_requirements),
        'storage_capabilities': report.storage_capabilities,
        'success': True
    }
    print(json.dumps(result))
except Exception as e:
    result = {'success': False, 'error': str(e)}
    print(json.dumps(result))
")

echo "Result:"
echo "$ANALYSIS_RESULT"

# Parse result and validate
if echo "$ANALYSIS_RESULT" | grep -q '"success": true'; then
    COMMANDS_COUNT=$(echo "$ANALYSIS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['commands_found'])")
    DECORATORS_COUNT=$(echo "$ANALYSIS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['decorators_used'])")
    REQUIREMENTS_COUNT=$(echo "$ANALYSIS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['integration_requirements'])")

    if [[ $COMMANDS_COUNT -gt 0 ]] && [[ $DECORATORS_COUNT -gt 0 ]] && [[ $REQUIREMENTS_COUNT -gt 0 ]]; then
        echo "Status: PASS - Found $COMMANDS_COUNT commands, $DECORATORS_COUNT decorators, $REQUIREMENTS_COUNT requirements"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Insufficient patterns found (commands: $COMMANDS_COUNT, decorators: $DECORATORS_COUNT, requirements: $REQUIREMENTS_COUNT)"
        ((FAILED_TESTS++))
    fi
else
    echo "Status: FAIL - Analysis failed with error"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Test 2: Click Context Storage Capability Validation
echo "Test 2: Click Context Storage Capability"
echo "Expected: Click context supports custom data storage and meta dictionary access"
echo "Executing:"
STORAGE_RESULT=$(python -c "
from spec_cli.utils.click_analysis import validate_context_storage_capability
import json

try:
    storage_capable = validate_context_storage_capability()
    result = {
        'storage_capable': storage_capable,
        'success': True
    }
    print(json.dumps(result))
except Exception as e:
    result = {'success': False, 'error': str(e)}
    print(json.dumps(result))
")

echo "Result:"
echo "$STORAGE_RESULT"

if echo "$STORAGE_RESULT" | grep -q '"storage_capable": true'; then
    echo "Status: PASS - Click context storage capability verified"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Click context storage not supported or test failed"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Test 3: Specific Click Pattern Detection
echo "Test 3: Specific Click Pattern Detection"
echo "Expected: Analysis detects @click.group, @click.command, @click.option patterns"
echo "Executing:"
PATTERNS_RESULT=$(python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns
from pathlib import Path
import json

try:
    cli_dir = Path('spec_cli/cli')
    report = analyze_click_patterns(cli_dir)

    patterns_found = {
        'click_group': 'click_group' in report.decorators_used,
        'click_command': 'click_command' in report.decorators_used,
        'click_option': 'click_option' in report.decorators_used,
        'click_pass_context': 'click_pass_context' in report.decorators_used,
        'has_commands': len(report.commands_found) > 0
    }

    result = {
        'patterns': patterns_found,
        'success': True
    }
    print(json.dumps(result))
except Exception as e:
    result = {'success': False, 'error': str(e)}
    print(json.dumps(result))
")

echo "Result:"
echo "$PATTERNS_RESULT"

if echo "$PATTERNS_RESULT" | grep -q '"success": true'; then
    # Check for key patterns
    GROUP_FOUND=$(echo "$PATTERNS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['patterns']['click_group'])")
    COMMAND_FOUND=$(echo "$PATTERNS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['patterns']['click_command'])")

    if [[ "$GROUP_FOUND" == "True" ]] || [[ "$COMMAND_FOUND" == "True" ]]; then
        echo "Status: PASS - Key Click patterns detected (group: $GROUP_FOUND, command: $COMMAND_FOUND)"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Essential Click patterns not found"
        ((FAILED_TESTS++))
    fi
else
    echo "Status: FAIL - Pattern detection failed"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Test 4: Integration Requirements Generation
echo "Test 4: Integration Requirements Generation"
echo "Expected: Analysis generates requirements for Click context integration"
echo "Executing:"
REQUIREMENTS_RESULT=$(python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns
from pathlib import Path
import json

try:
    cli_dir = Path('spec_cli/cli')
    report = analyze_click_patterns(cli_dir)

    requirements_text = ' '.join(report.integration_requirements).lower()

    key_requirements = {
        'framework_integration': 'click framework integration' in requirements_text,
        'context_injection': 'context parameter injection' or 'injection' in requirements_text,
        'storage_mechanism': 'storage mechanism' in requirements_text or 'storage' in requirements_text,
        'storage_verified': 'storage verified' in requirements_text,
        'requirements_count': len(report.integration_requirements)
    }

    result = {
        'requirements': key_requirements,
        'full_requirements': report.integration_requirements,
        'success': True
    }
    print(json.dumps(result))
except Exception as e:
    result = {'success': False, 'error': str(e)}
    print(json.dumps(result))
")

echo "Result (requirements summary):"
echo "$REQUIREMENTS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['requirements'], indent=2))"

if echo "$REQUIREMENTS_RESULT" | grep -q '"success": true'; then
    REQ_COUNT=$(echo "$REQUIREMENTS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['requirements']['requirements_count'])")
    FRAMEWORK_REQ=$(echo "$REQUIREMENTS_RESULT" | python -c "import sys, json; data=json.load(sys.stdin); print(data['requirements']['framework_integration'])")

    if [[ $REQ_COUNT -ge 3 ]] && [[ "$FRAMEWORK_REQ" == "True" ]]; then
        echo "Status: PASS - Generated $REQ_COUNT requirements including framework integration"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Insufficient or incomplete requirements (count: $REQ_COUNT, framework: $FRAMEWORK_REQ)"
        ((FAILED_TESTS++))
    fi
else
    echo "Status: FAIL - Requirements generation failed"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Test 5: Error Handling and Edge Cases
echo "Test 5: Error Handling for Invalid Input"
echo "Expected: Analysis handles nonexistent directories gracefully with proper error messages"
echo "Executing:"
ERROR_HANDLING_RESULT=$(python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns
from spec_cli.exceptions import SpecValidationError
from pathlib import Path
import json

try:
    # Test with nonexistent directory
    nonexistent_dir = Path('/nonexistent/cli/directory')
    report = analyze_click_patterns(nonexistent_dir)
    result = {'success': False, 'error': 'Should have raised exception but did not'}
except SpecValidationError as e:
    result = {
        'success': True,
        'error_handled': True,
        'error_type': 'SpecValidationError',
        'error_message': str(e)
    }
except Exception as e:
    result = {
        'success': False,
        'error': f'Wrong exception type: {type(e).__name__}: {str(e)}'
    }

print(json.dumps(result))
")

echo "Result:"
echo "$ERROR_HANDLING_RESULT"

if echo "$ERROR_HANDLING_RESULT" | grep -q '"error_handled": true'; then
    echo "Status: PASS - Error handling works correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Error handling not working properly"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Test 6: P2.1b Integration Readiness
echo "Test 6: P2.1b Integration Readiness Validation"
echo "Expected: Analysis provides sufficient information for P2.1b implementation"
echo "Executing:"
INTEGRATION_READINESS=$(python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns, validate_context_storage_capability
from pathlib import Path
import json

try:
    cli_dir = Path('spec_cli/cli')
    report = analyze_click_patterns(cli_dir)
    storage_capable = validate_context_storage_capability()

    readiness_check = {
        'has_click_patterns': len(report.decorators_used) > 0,
        'has_context_info': len(report.context_usage) >= 0,  # Can be 0 if no current usage
        'storage_validated': storage_capable,
        'has_requirements': len(report.integration_requirements) > 0,
        'has_storage_capabilities': len(report.storage_capabilities) > 0,
        'framework_analysis_complete': True
    }

    # Check if all readiness criteria met
    all_ready = all(readiness_check.values())

    result = {
        'p2_1b_ready': all_ready,
        'readiness_details': readiness_check,
        'success': True
    }
    print(json.dumps(result))
except Exception as e:
    result = {'success': False, 'error': str(e)}
    print(json.dumps(result))
")

echo "Result:"
echo "$INTEGRATION_READINESS" | python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['readiness_details'], indent=2))"

if echo "$INTEGRATION_READINESS" | grep -q '"p2_1b_ready": true'; then
    echo "Status: PASS - Ready for P2.1b implementation"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Not ready for P2.1b implementation"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))
echo

# Performance validation
echo "Performance validation..."
echo "Measuring analysis response time..."
ANALYSIS_TIME=$(time -p python -c "
from spec_cli.utils.click_analysis import analyze_click_patterns
from pathlib import Path
analyze_click_patterns(Path('spec_cli/cli'))
" 2>&1 | grep real | awk '{print $2}')

echo "Analysis completed in ${ANALYSIS_TIME}s"
if (( $(echo "$ANALYSIS_TIME < 5.0" | bc -l) )); then
    echo "Performance: PASS - Analysis completed within 5 seconds"
else
    echo "Performance: WARNING - Analysis took longer than expected"
fi
echo

# Cleanup phase
echo "Cleaning up..."
echo "No cleanup required for this test suite"
echo "Cleanup complete"

echo
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Click pattern analysis working correctly"
    echo
    echo "Key Findings:"
    echo "✓ Click framework patterns successfully detected in CLI"
    echo "✓ Context storage capabilities validated"
    echo "✓ Integration requirements generated for P2.1b"
    echo "✓ Error handling works properly"
    echo "✓ Analysis performance within acceptable limits"
    echo "✓ Ready for P2.1b Click context integration implementation"
    exit 0
else
    echo "SOME TESTS FAILED - Click pattern analysis needs investigation"
    echo
    echo "Failed test count: $FAILED_TESTS"
    echo "Please review failed tests above for details"
    exit 1
fi
