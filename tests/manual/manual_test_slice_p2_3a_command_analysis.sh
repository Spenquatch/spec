#!/bin/bash
# Manual Test Script: Slice P2.3a - Command Structure Analysis
# Purpose: Manually verify that command analysis functionality works correctly
# Created: 2025-07-05

set -e  # Exit on any error

echo "=== Manual Test: Slice P2.3a - Command Structure Analysis ==="
echo "Purpose: Verify command analysis identifies CLI structure and singleton patterns"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
if [[ ! -f "spec_cli/utils/command_analysis.py" ]]; then
    echo "ERROR: command_analysis.py not found"
    exit 1
fi

if [[ ! -d "spec_cli/cli" ]]; then
    echo "ERROR: CLI directory not found"
    exit 1
fi

echo "Prerequisites verified"
echo

# Setup phase
echo "Setting up test environment..."
# Ensure we're in project root
if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Not in project root directory"
    exit 1
fi

# Activate virtual environment if needed
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    echo "Virtual environment activated"
fi

echo "Test environment ready"
echo

# Test execution phase
echo "Executing manual tests..."

echo ""
echo "Test 1: Basic CLI Structure Analysis"
((TOTAL_TESTS++))
echo "Expected: Analysis finds 30+ files, 10+ commands, 40+ singleton patterns"
echo "Executing:"
ANALYSIS_OUTPUT=$(python -c "
from spec_cli.utils.command_analysis import analyze_command_structure
from pathlib import Path
result = analyze_command_structure(Path('spec_cli/cli'))
print(f'Files: {result.file_count}')
print(f'Commands: {len(result.commands)}')
print(f'Click patterns: {len(result.click_patterns)}')  
print(f'Singleton usage: {len(result.singleton_usage)}')
print(f'Errors: {len(result.analysis_errors)}')
")

echo "Result:"
echo "$ANALYSIS_OUTPUT"

# Parse results for validation
FILE_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep "Files:" | awk '{print $2}')
COMMAND_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep "Commands:" | awk '{print $2}')
SINGLETON_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep "Singleton usage:" | awk '{print $3}')
ERROR_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep "Errors:" | awk '{print $2}')

if [[ $FILE_COUNT -ge 30 && $COMMAND_COUNT -ge 10 && $SINGLETON_COUNT -ge 40 && $ERROR_COUNT -eq 0 ]]; then
    echo "Status: PASS - CLI structure analysis successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected: Files>=30, Commands>=10, Singletons>=40, Errors=0"
    echo "         Actual: Files=$FILE_COUNT, Commands=$COMMAND_COUNT, Singletons=$SINGLETON_COUNT, Errors=$ERROR_COUNT"
fi
echo ""

echo "Test 2: Singleton Pattern Detection in init.py"
((TOTAL_TESTS++))
echo "Expected: Detects SpecGitRepository direct instantiation"
echo "Executing:"
INIT_ANALYSIS=$(python -c "
from spec_cli.utils.command_analysis import identify_singleton_usage
from pathlib import Path
result = identify_singleton_usage(Path('spec_cli/cli/commands/init.py'))
for usage in result:
    print(f'Class: {usage.singleton_class}')
    print(f'Pattern: {usage.usage_pattern}')
    print(f'Line: {usage.line_number}')
    print(f'Context: {usage.context}')
")

echo "Result:"
echo "$INIT_ANALYSIS"

if echo "$INIT_ANALYSIS" | grep -q "SpecGitRepository" && echo "$INIT_ANALYSIS" | grep -q "direct_instantiation"; then
    echo "Status: PASS - init.py singleton pattern detected correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected SpecGitRepository direct_instantiation pattern"
fi
echo ""

echo "Test 3: Singleton Pattern Detection in status.py"
((TOTAL_TESTS++))
echo "Expected: Detects get_console() and get_spec_repository() factory calls"
echo "Executing:"
STATUS_ANALYSIS=$(python -c "
from spec_cli.utils.command_analysis import identify_singleton_usage
from pathlib import Path
result = identify_singleton_usage(Path('spec_cli/cli/commands/status.py'))
for usage in result:
    print(f'Class: {usage.singleton_class}')
    print(f'Pattern: {usage.usage_pattern}')  
    print(f'Context: {usage.context}')
print(f'Total patterns: {len(result)}')
")

echo "Result:"
echo "$STATUS_ANALYSIS"

if echo "$STATUS_ANALYSIS" | grep -q "Console" && echo "$STATUS_ANALYSIS" | grep -q "factory_function"; then
    echo "Status: PASS - status.py singleton patterns detected correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected Console and SpecGitRepository factory_function patterns"
fi
echo ""

echo "Test 4: Click Command Detection"
((TOTAL_TESTS++))
echo "Expected: Detects Click command decorators and function names"
echo "Executing:"
CLICK_ANALYSIS=$(python -c "
from spec_cli.utils.command_analysis import analyze_command_structure
from pathlib import Path
result = analyze_command_structure(Path('spec_cli/cli'))
print('Commands found:')
for cmd in result.commands[:5]:
    print(f'  {cmd[\"name\"]} in {cmd[\"file\"]}')
print('Click patterns:')
for pattern in result.click_patterns[:5]:
    print(f'  @{pattern.decorator_name} -> {pattern.function_name}')
")

echo "Result:"
echo "$CLICK_ANALYSIS"

if echo "$CLICK_ANALYSIS" | grep -q "command" && echo "$CLICK_ANALYSIS" | grep -q "spec_command"; then
    echo "Status: PASS - Click command detection successful"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected command and spec_command detection"
fi
echo ""

echo "Test 5: Migration Requirements Analysis"
((TOTAL_TESTS++))
echo "Expected: Analysis provides migration data for P2.3b and P2.3c"
echo "Executing:"
MIGRATION_ANALYSIS=$(python -c "
from spec_cli.utils.command_analysis import analyze_command_structure
from pathlib import Path
result = analyze_command_structure(Path('spec_cli/cli'))

# Count patterns by command
init_patterns = [u for u in result.singleton_usage if 'init.py' in u.file_path]
status_patterns = [u for u in result.singleton_usage if 'status.py' in u.file_path]

print(f'Init command singleton patterns: {len(init_patterns)}')
for pattern in init_patterns:
    print(f'  {pattern.singleton_class} ({pattern.usage_pattern})')

print(f'Status command singleton patterns: {len(status_patterns)}')
for pattern in status_patterns:
    print(f'  {pattern.singleton_class} ({pattern.usage_pattern})')

# Migration guidance
direct_count = len([u for u in result.singleton_usage if u.usage_pattern == 'direct_instantiation'])
factory_count = len([u for u in result.singleton_usage if u.usage_pattern == 'factory_function'])
print(f'Direct instantiation patterns: {direct_count}')
print(f'Factory function patterns: {factory_count}')
")

echo "Result:"
echo "$MIGRATION_ANALYSIS"

if echo "$MIGRATION_ANALYSIS" | grep -q "Init command singleton patterns: [1-9]" && \
   echo "$MIGRATION_ANALYSIS" | grep -q "Status command singleton patterns: [1-9]"; then
    echo "Status: PASS - Migration requirements analysis provides actionable data"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Expected singleton patterns in both init and status commands"
fi
echo ""

echo "Test 6: Error Handling Validation"
((TOTAL_TESTS++))
echo "Expected: Graceful handling of invalid files and directories"
echo "Executing:"
ERROR_HANDLING_TEST=$(python -c "
from spec_cli.utils.command_analysis import analyze_command_structure, identify_singleton_usage, CommandAnalysisError
from pathlib import Path

# Test invalid directory
try:
    analyze_command_structure(Path('/nonexistent/directory'))
    print('ERROR: Should have raised CommandAnalysisError for invalid directory')
except CommandAnalysisError as e:
    print(f'✓ Invalid directory handled: {type(e).__name__}')

# Test invalid file
try:
    identify_singleton_usage(Path('/nonexistent/file.py'))
    print('ERROR: Should have raised CommandAnalysisError for invalid file')
except CommandAnalysisError as e:
    print(f'✓ Invalid file handled: {type(e).__name__}')

print('Error handling validation complete')
")

echo "Result:"
echo "$ERROR_HANDLING_TEST"

if echo "$ERROR_HANDLING_TEST" | grep -q "Invalid directory handled" && \
   echo "$ERROR_HANDLING_TEST" | grep -q "Invalid file handled"; then
    echo "Status: PASS - Error handling works correctly"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL - Error handling not working properly"
fi
echo ""

# Verification phase
echo "Verifying results..."
echo "Checking migration requirements documentation exists..."
if [[ -f "phases/analysis/command_migration_requirements.md" ]]; then
    REQUIREMENT_LINES=$(wc -l < "phases/analysis/command_migration_requirements.md")
    echo "✓ Migration requirements documentation created ($REQUIREMENT_LINES lines)"
else
    echo "✗ Migration requirements documentation missing"
fi

echo "Checking command analysis utility exists..."
if [[ -f "spec_cli/utils/command_analysis.py" ]]; then
    UTILITY_LINES=$(wc -l < "spec_cli/utils/command_analysis.py")
    echo "✓ Command analysis utility created ($UTILITY_LINES lines)"
else
    echo "✗ Command analysis utility missing"
fi

echo "Verification complete"
echo

# Performance validation
echo "Performance validation..."
echo "Measuring CLI analysis response time..."
ANALYSIS_TIME=$(time (python -c "
from spec_cli.utils.command_analysis import analyze_command_structure
from pathlib import Path
result = analyze_command_structure(Path('spec_cli/cli'))
print(f'Analyzed {result.file_count} files with {len(result.singleton_usage)} patterns')
" 2>&1) 2>&1 | grep real | awk '{print $2}')

echo "Analysis completed in: $ANALYSIS_TIME"
echo "Performance validation complete"
echo

# Cleanup phase
echo "Cleaning up..."
# No cleanup needed for this analysis test
echo "Cleanup complete"
echo

echo ""
echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Command analysis feature working correctly"
    echo ""
    echo "Key Achievements:"
    echo "  ✓ CLI structure analysis identifies 30+ files and 10+ commands"
    echo "  ✓ Singleton pattern detection finds 40+ usage patterns"
    echo "  ✓ init.py analysis detects SpecGitRepository direct instantiation"
    echo "  ✓ status.py analysis detects factory function calls"
    echo "  ✓ Click command detection identifies decorators and functions"
    echo "  ✓ Migration requirements provide actionable guidance for P2.3b/P2.3c"
    echo "  ✓ Error handling gracefully manages invalid inputs"
    echo ""
    echo "Ready for P2.3b (init command migration) and P2.3c (status command migration)"
    exit 0
else
    echo "SOME TESTS FAILED - Command analysis feature needs investigation"
    echo ""
    echo "Failed tests need attention before proceeding to P2.3b and P2.3c"
    exit 1
fi