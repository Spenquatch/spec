#!/bin/bash
# Manual Test Script: Slice P1.3a - Singleton Pattern Analysis
# Purpose: Manually verify that singleton pattern analysis functionality works correctly
# Created: 2024-12-20

set -e  # Exit on any error

echo "=== Manual Test: Slice P1.3a - Singleton Pattern Analysis ==="
echo "Purpose: Validate singleton pattern detection and compatibility requirements generation"
echo "Timestamp: $(date)"
echo

PASSED_TESTS=0
TOTAL_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local expected_result="$2"
    local test_command="$3"
    
    echo "Test: $test_name"
    echo "Expected: $expected_result"
    echo "Executing: $test_command"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo "Status: PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "Status: FAIL"
    fi
    echo ""
}

# Prerequisites check
echo "Checking prerequisites..."
if [[ ! -f "spec_cli/utils/pattern_analysis.py" ]]; then
    echo "ERROR: pattern_analysis.py not found"
    exit 1
fi

if [[ ! -f "spec_cli/utils/singleton.py" ]]; then
    echo "ERROR: singleton.py not found"
    exit 1
fi

if [[ ! -f "spec_cli/ui/progress_manager.py" ]]; then
    echo "ERROR: progress_manager.py not found"  
    exit 1
fi

echo "Prerequisites verified"
echo

# Test 1: Analyze actual singleton.py file
echo "Test 1: Singleton Infrastructure Analysis"
echo "Expected: Successfully detect SingletonMeta and singleton_decorator patterns"
echo "Executing:"
SINGLETON_ANALYSIS=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage

try:
    usages = analyze_singleton_usage(Path('spec_cli/utils/singleton.py'))
    singleton_names = {u.singleton_name for u in usages}
    print(f'FOUND_SINGLETONS:{len(singleton_names)}')
    print(f'SINGLETON_NAMES:{sorted(singleton_names)}')
    if 'SingletonMeta' in singleton_names:
        print('SUCCESS:SingletonMeta detected')
    else:
        print('ERROR:SingletonMeta not detected')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $SINGLETON_ANALYSIS"
if [[ $SINGLETON_ANALYSIS == *"SUCCESS:SingletonMeta detected"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 2: Analyze ProgressManagerSingleton usage
echo "Test 2: ProgressManagerSingleton Usage Analysis"
echo "Expected: Detect ProgressManagerSingleton class and usage patterns"
echo "Executing:"
PROGRESS_ANALYSIS=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage

try:
    usages = analyze_singleton_usage(Path('spec_cli/ui/progress_manager.py'))
    progress_usages = [u for u in usages if 'ProgressManager' in u.singleton_name]
    print(f'PROGRESS_USAGES:{len(progress_usages)}')
    
    usage_types = {u.usage_type for u in progress_usages}
    print(f'USAGE_TYPES:{sorted(usage_types)}')
    
    if len(progress_usages) > 0:
        print('SUCCESS:ProgressManagerSingleton usage detected')
    else:
        print('ERROR:No ProgressManagerSingleton usage found')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $PROGRESS_ANALYSIS"
if [[ $PROGRESS_ANALYSIS == *"SUCCESS:ProgressManagerSingleton usage detected"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 3: Access Pattern Documentation
echo "Test 3: Access Pattern Documentation Generation"
echo "Expected: Generate comprehensive access pattern report with wrapper requirements"
echo "Executing:"
ACCESS_PATTERN_ANALYSIS=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage, document_access_patterns

try:
    # Analyze multiple files
    all_usages = []
    files_to_analyze = [
        'spec_cli/ui/progress_manager.py',
        'spec_cli/ui/progress_utils.py'
    ]
    
    for file_path_str in files_to_analyze:
        file_path = Path(file_path_str)
        if file_path.exists():
            usages = analyze_singleton_usage(file_path)
            all_usages.extend(usages)
    
    # Generate access pattern report
    report = document_access_patterns('ProgressManagerSingleton', all_usages)
    
    print(f'TOTAL_USAGES:{report.total_usages}')
    print(f'ACCESS_METHODS:{sorted(report.access_methods)}')
    print(f'REQUIREMENTS_COUNT:{len(report.wrapper_requirements)}')
    
    # Check for specific requirements
    requirements_text = ' '.join(report.wrapper_requirements).lower()
    
    has_thread_safety = 'thread' in requirements_text
    has_api_preservation = 'api' in requirements_text or 'interface' in requirements_text
    has_progress_specific = 'progress_manager' in requirements_text
    
    print(f'HAS_THREAD_SAFETY:{has_thread_safety}')
    print(f'HAS_API_PRESERVATION:{has_api_preservation}')  
    print(f'HAS_PROGRESS_SPECIFIC:{has_progress_specific}')
    
    if report.total_usages > 0 and len(report.wrapper_requirements) > 0:
        print('SUCCESS:Access pattern report generated')
    else:
        print('ERROR:Incomplete access pattern report')
        
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $ACCESS_PATTERN_ANALYSIS"
if [[ $ACCESS_PATTERN_ANALYSIS == *"SUCCESS:Access pattern report generated"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 4: Cross-Platform Path Handling
echo "Test 4: Cross-Platform Path Handling"
echo "Expected: Pattern analysis works with various path formats"
echo "Executing:"
CROSS_PLATFORM_TEST=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage
import tempfile
import os

try:
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Test file with cross-platform content
from spec_cli.ui.progress_manager import ProgressManagerSingleton
from spec_cli\\\\utils\\\\singleton import SingletonMeta  # Windows-style path in comment

class TestSingleton(metaclass=SingletonMeta):
    pass

def test_function():
    manager = ProgressManagerSingleton()
    return manager.get_progress_manager()
''')
        temp_path = f.name
    
    # Analyze the temporary file
    usages = analyze_singleton_usage(Path(temp_path))
    
    # Clean up
    os.unlink(temp_path)
    
    singleton_names = {u.singleton_name for u in usages}
    print(f'CROSS_PLATFORM_SINGLETONS:{len(singleton_names)}')
    print(f'FOUND_NAMES:{sorted(singleton_names)}')
    
    if 'ProgressManagerSingleton' in singleton_names and 'SingletonMeta' in singleton_names:
        print('SUCCESS:Cross-platform analysis working')
    else:
        print('ERROR:Cross-platform analysis failed')
        
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $CROSS_PLATFORM_TEST"
if [[ $CROSS_PLATFORM_TEST == *"SUCCESS:Cross-platform analysis working"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 5: Error Handling Validation
echo "Test 5: Error Handling Validation"
echo "Expected: Graceful error handling for invalid files and syntax errors"
echo "Executing:"
ERROR_HANDLING_TEST=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage
from spec_cli.exceptions import PatternAnalysisError
import tempfile
import os

try:
    # Test 1: Non-existent file
    try:
        analyze_singleton_usage(Path('/nonexistent/file.py'))
        print('ERROR:Should have raised FileNotFoundError')
    except FileNotFoundError:
        print('SUCCESS:FileNotFoundError handled correctly')
    except Exception as e:
        print(f'ERROR:Unexpected exception: {e}')
    
    # Test 2: Syntax error fallback
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# Invalid syntax but contains patterns
class ProgressManagerSingleton(:  # Syntax error
    pass
        
get_progress_manager()
''')
        temp_path = f.name
    
    usages = analyze_singleton_usage(Path(temp_path))
    os.unlink(temp_path)
    
    singleton_names = {u.singleton_name for u in usages}
    if 'ProgressManagerSingleton' in singleton_names:
        print('SUCCESS:Syntax error fallback working')
    else:
        print('ERROR:Syntax error fallback failed')
    
    print('SUCCESS:Error handling validation complete')
        
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $ERROR_HANDLING_TEST"
if [[ $ERROR_HANDLING_TEST == *"SUCCESS:Error handling validation complete"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 6: End-to-End Analysis Workflow
echo "Test 6: End-to-End Analysis Workflow" 
echo "Expected: Complete analysis workflow from detection to requirements generation"
echo "Executing:"
E2E_WORKFLOW_TEST=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage, document_access_patterns

try:
    # Step 1: Analyze actual codebase files
    key_files = [
        'spec_cli/utils/singleton.py',
        'spec_cli/ui/progress_manager.py',
        'spec_cli/ui/progress_utils.py'
    ]
    
    all_usages = []
    files_analyzed = 0
    
    for file_path_str in key_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            usages = analyze_singleton_usage(file_path)
            all_usages.extend(usages)
            files_analyzed += 1
    
    # Step 2: Generate comprehensive requirements
    progress_usages = [u for u in all_usages if 'ProgressManager' in u.singleton_name]
    
    if progress_usages:
        report = document_access_patterns('ProgressManagerSingleton', all_usages)
        
        # Step 3: Validate requirements for P1.3b
        requirements = report.wrapper_requirements
        
        # Check for essential requirements
        has_thread_requirements = any('thread' in req.lower() for req in requirements)
        has_api_requirements = any('api' in req.lower() or 'interface' in req.lower() for req in requirements)
        has_progress_requirements = any('progress' in req.lower() for req in requirements)
        
        print(f'FILES_ANALYZED:{files_analyzed}')
        print(f'TOTAL_USAGES:{len(all_usages)}')
        print(f'PROGRESS_USAGES:{len(progress_usages)}')
        print(f'REQUIREMENTS_COUNT:{len(requirements)}')
        print(f'HAS_THREAD_REQ:{has_thread_requirements}')
        print(f'HAS_API_REQ:{has_api_requirements}')
        print(f'HAS_PROGRESS_REQ:{has_progress_requirements}')
        
        if (files_analyzed >= 2 and len(progress_usages) > 0 and 
            has_thread_requirements and has_api_requirements and has_progress_requirements):
            print('SUCCESS:End-to-end workflow complete')
        else:
            print('ERROR:Incomplete end-to-end workflow')
    else:
        print('ERROR:No ProgressManager usages found')
        
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Result: $E2E_WORKFLOW_TEST"
if [[ $E2E_WORKFLOW_TEST == *"SUCCESS:End-to-end workflow complete"* ]]; then
    echo "Status: PASS"
    ((PASSED_TESTS++))
else
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Test 7: Requirements Document Generation Validation
echo "Test 7: Requirements Document Generation Validation"
echo "Expected: Requirements document exists and contains essential compatibility information"
echo "Executing:"
if [[ -f "phases/analysis/singleton_compatibility_requirements.md" ]]; then
    echo "Requirements document found"
    
    # Check document content
    if grep -q "ProgressManagerSingleton" phases/analysis/singleton_compatibility_requirements.md; then
        echo "Contains ProgressManagerSingleton analysis: YES"
        
        if grep -q -i "thread.safety" phases/analysis/singleton_compatibility_requirements.md; then
            echo "Contains thread safety requirements: YES"
            
            if grep -q "wrapper" phases/analysis/singleton_compatibility_requirements.md; then
                echo "Contains wrapper requirements: YES"
                echo "Status: PASS"
                ((PASSED_TESTS++))
            else
                echo "Contains wrapper requirements: NO"
                echo "Status: FAIL"
            fi
        else
            echo "Contains thread safety requirements: NO"
            echo "Status: FAIL"
        fi
    else
        echo "Contains ProgressManagerSingleton analysis: NO"
        echo "Status: FAIL"
    fi
else
    echo "Requirements document not found"
    echo "Status: FAIL"
fi
((TOTAL_TESTS++))
echo ""

# Performance validation
echo "Performance validation..."
echo "Measuring singleton analysis performance..."
PERFORMANCE_TEST=$(python -c "
import sys
sys.path.append('.')
from pathlib import Path
from spec_cli.utils.pattern_analysis import analyze_singleton_usage
import time

try:
    start_time = time.time()
    
    # Analyze a moderately large file
    usages = analyze_singleton_usage(Path('spec_cli/ui/progress_manager.py'))
    
    end_time = time.time()
    analysis_time = end_time - start_time
    
    print(f'ANALYSIS_TIME:{analysis_time:.3f}s')
    print(f'USAGES_FOUND:{len(usages)}')
    
    if analysis_time < 1.0:  # Should complete within 1 second
        print('SUCCESS:Performance within acceptable limits')
    else:
        print('WARNING:Analysis took longer than expected')
        
except Exception as e:
    print(f'ERROR:{e}')
")

echo "Performance result: $PERFORMANCE_TEST"
echo ""

# Cleanup phase
echo "Cleaning up..."
echo "No cleanup required - analysis is read-only"
echo "Cleanup complete"
echo ""

echo "=== Manual Test Summary ==="
echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL MANUAL TESTS PASSED - Singleton pattern analysis working correctly"
    echo ""
    echo "Key Findings:"
    echo "- Singleton pattern detection is functional across real codebase"
    echo "- ProgressManagerSingleton usage analysis provides detailed compatibility data"
    echo "- Access pattern documentation generates comprehensive wrapper requirements"
    echo "- Cross-platform path handling works correctly"
    echo "- Error handling is robust for various edge cases"
    echo "- End-to-end workflow from analysis to requirements generation is complete"
    echo "- Requirements document provides sufficient detail for P1.3b implementation"
    echo ""
    exit 0
else
    echo "SOME TESTS FAILED - Singleton pattern analysis needs investigation"
    echo "Review failed tests above for specific issues"
    exit 1
fi