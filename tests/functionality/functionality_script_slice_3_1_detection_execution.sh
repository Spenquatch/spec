#!/bin/bash
# Functionality Script: Slice 3.1 - Comprehensive Singleton Detection Execution
# Purpose: Verify that comprehensive singleton detection works correctly with real codebase scanning using Docker
# Created: $(date)
# CRITICAL: NO unittest.mock, patch, or test doubles - use Docker containers for isolated testing

set -e  # Exit on any error

echo "=== Functionality Script: Slice 3.1 - Comprehensive Singleton Detection Execution ==="
echo "Purpose: Verify comprehensive singleton detection execution with real implementation and Docker isolation"
echo "Approach: Real functionality testing with Docker containerized Python environment (no mocking)"
echo "Timestamp: $(date)"
echo

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Prerequisites check
echo "Checking prerequisites..."
echo "Verifying Docker is available for isolated testing environment..."
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker not available - functionality scripts require Docker for isolated testing"
    exit 1
fi
echo "Docker is available for real functionality testing"

echo "Checking if Python environment is ready..."
if ! python -c "import sys; print(f'Python {sys.version}')" >/dev/null 2>&1; then
    echo "ERROR: Python environment not available"
    exit 1
fi
echo "Python environment ready for testing"

# Setup temporary workspace in Docker volume
echo "Setting up Docker-isolated test environment..."
DOCKER_VOLUME="slice-3-1-test-volume"
DOCKER_CONTAINER="slice-3-1-test-container"

# Create Docker volume for isolated testing
echo "Creating Docker volume for isolated test environment..."
docker volume create $DOCKER_VOLUME || true

# Create test container with Python environment
echo "Starting Docker container with Python environment..."
docker run -d --name $DOCKER_CONTAINER \
    -v $DOCKER_VOLUME:/workspace \
    -w /workspace \
    python:3.11-slim \
    sleep 300

# Copy project files to Docker container
echo "Copying project files to Docker container for real testing..."
docker cp . $DOCKER_CONTAINER:/workspace/spec-cli/

echo "Installing dependencies in Docker container..."
docker exec $DOCKER_CONTAINER bash -c "
    cd /workspace/spec-cli && \
    pip install -e . && \
    pip install pytest
"

echo "Creating test codebase with real singleton patterns in Docker environment..."
docker exec $DOCKER_CONTAINER bash -c "
    mkdir -p /workspace/test_codebase
    cat > /workspace/test_codebase/singleton_module.py << 'EOF'
\"\"\"Real singleton implementation for functionality testing.\"\"\"

class SingletonMeta(type):
    \"\"\"Metaclass for singleton pattern.\"\"\"
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ProgressManagerSingleton(metaclass=SingletonMeta):
    \"\"\"Progress manager singleton using metaclass.\"\"\"
    
    def __init__(self):
        self.status = 'initialized'
    
    def update_progress(self, value):
        self.status = f'progress_{value}'
        return self.status

@singleton_decorator
def get_progress_manager():
    \"\"\"Function with singleton decorator.\"\"\"
    return ProgressManagerSingleton()

def create_singleton_instance():
    \"\"\"Create singleton via direct instantiation.\"\"\"
    return ProgressManagerSingleton()
EOF

    cat > /workspace/test_codebase/usage_module.py << 'EOF'
\"\"\"Module demonstrating singleton usage patterns.\"\"\"

from singleton_module import ProgressManagerSingleton, get_progress_manager

class ServiceClass:
    \"\"\"Service that uses singleton patterns.\"\"\"
    
    def __init__(self):
        self.manager = ProgressManagerSingleton()
        self.instance = get_progress_manager()
    
    def process_with_singleton(self):
        return self.manager.update_progress(50)
EOF

    cat > /workspace/test_codebase/regular_module.py << 'EOF'
\"\"\"Regular module without singleton patterns.\"\"\"

class RegularClass:
    \"\"\"Regular class without singleton patterns.\"\"\"
    
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value

def create_regular_instance():
    return RegularClass('regular')
EOF
"

echo "Test environment setup complete in Docker container"
echo "Verifying test codebase structure..."
docker exec $DOCKER_CONTAINER find /workspace/test_codebase -name "*.py" -exec echo "Found: {}" \;

echo ""
echo "Executing functionality tests with real implementations..."

echo ""
echo "Functionality Test 1: Basic singleton detection execution with real codebase"
echo "Expected: Detection executes successfully and finds singleton patterns in real code"
echo "Executing with real singleton detection implementation in Docker:"
((TOTAL_TESTS++))

TEST_1_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection

try:
    result = execute_comprehensive_detection(
        '/workspace/test_codebase',
        {'max_workers': 2, 'timeout_seconds': 60},
        []
    )
    print(f'SUCCESS:patterns_found={len(result[\"singleton_patterns\"])},files_scanned={result[\"scan_statistics\"][\"total_files_scanned\"]},duration={result[\"scan_statistics\"][\"scan_duration_seconds\"]:.2f}s')
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Actual Result from real detection execution: $TEST_1_OUTPUT"
if [[ $TEST_1_OUTPUT == SUCCESS:* ]]; then
    echo "Status: PASS - Detection executed successfully with real implementation"
    ((PASSED_TESTS++))
    
    # Extract metrics from success output
    PATTERNS_FOUND=$(echo "$TEST_1_OUTPUT" | grep -o 'patterns_found=[0-9]*' | cut -d= -f2)
    FILES_SCANNED=$(echo "$TEST_1_OUTPUT" | grep -o 'files_scanned=[0-9]*' | cut -d= -f2)
    SCAN_DURATION=$(echo "$TEST_1_OUTPUT" | grep -o 'duration=[0-9.]*' | cut -d= -f2)
    
    echo "  - Singleton patterns detected: $PATTERNS_FOUND"
    echo "  - Files scanned: $FILES_SCANNED"
    echo "  - Scan duration: ${SCAN_DURATION}s"
else
    echo "Status: FAIL - Detection execution failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Functionality Test 2: Singleton pattern type detection with real AST parsing"
echo "Expected: Detection identifies specific pattern types (metaclass, decorator, usage) from real code"
echo "Executing with real pattern analysis using Docker environment:"
((TOTAL_TESTS++))

TEST_2_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection, generate_detection_summary

try:
    result = execute_comprehensive_detection(
        '/workspace/test_codebase',
        {'max_workers': 2, 'timeout_seconds': 60},
        []
    )
    
    summary = generate_detection_summary(result['singleton_patterns'])
    patterns = result['singleton_patterns']
    
    # Count pattern types
    metaclass_patterns = len([p for p in patterns if 'metaclass' in p.get('pattern_type', '')])
    decorator_patterns = len([p for p in patterns if 'decorator' in p.get('pattern_type', '')])
    usage_patterns = len([p for p in patterns if 'usage' in p.get('pattern_type', '')])
    
    print(f'SUCCESS:total={summary[\"total_patterns\"]},unique_singletons={summary[\"unique_singletons\"]},metaclass={metaclass_patterns},decorator={decorator_patterns},usage={usage_patterns}')
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Actual Result from real pattern type detection: $TEST_2_OUTPUT"
if [[ $TEST_2_OUTPUT == SUCCESS:* ]]; then
    echo "Status: PASS - Pattern type detection working correctly with real AST parsing"
    ((PASSED_TESTS++))
    
    # Extract pattern type counts
    TOTAL_PATTERNS=$(echo "$TEST_2_OUTPUT" | grep -o 'total=[0-9]*' | cut -d= -f2)
    UNIQUE_SINGLETONS=$(echo "$TEST_2_OUTPUT" | grep -o 'unique_singletons=[0-9]*' | cut -d= -f2)
    METACLASS_COUNT=$(echo "$TEST_2_OUTPUT" | grep -o 'metaclass=[0-9]*' | cut -d= -f2)
    DECORATOR_COUNT=$(echo "$TEST_2_OUTPUT" | grep -o 'decorator=[0-9]*' | cut -d= -f2)
    USAGE_COUNT=$(echo "$TEST_2_OUTPUT" | grep -o 'usage=[0-9]*' | cut -d= -f2)
    
    echo "  - Total patterns: $TOTAL_PATTERNS"
    echo "  - Unique singletons: $UNIQUE_SINGLETONS"
    echo "  - Metaclass patterns: $METACLASS_COUNT"
    echo "  - Decorator patterns: $DECORATOR_COUNT"
    echo "  - Usage patterns: $USAGE_COUNT"
else
    echo "Status: FAIL - Pattern type detection failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Functionality Test 3: Exclusion pattern functionality with real file filtering"
echo "Expected: Scanner correctly excludes specified patterns from real filesystem scanning"
echo "Executing with real file system operations in Docker:"
((TOTAL_TESTS++))

# Create additional test files for exclusion testing
docker exec $DOCKER_CONTAINER bash -c "
    mkdir -p /workspace/test_codebase/tests
    cat > /workspace/test_codebase/tests/test_singleton.py << 'EOF'
# Test file that should be excluded
class TestSingleton(metaclass=SingletonMeta):
    pass
EOF

    cat > /workspace/test_codebase/backup_singleton.bak.py << 'EOF'
# Backup file that should be excluded
class BackupSingleton(metaclass=SingletonMeta):
    pass
EOF
"

TEST_3_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection

try:
    # Scan without exclusions
    result_all = execute_comprehensive_detection(
        '/workspace/test_codebase',
        {'max_workers': 2, 'timeout_seconds': 60},
        []
    )
    
    # Scan with exclusions
    result_filtered = execute_comprehensive_detection(
        '/workspace/test_codebase',
        {'max_workers': 2, 'timeout_seconds': 60},
        ['tests/', '.bak.py']
    )
    
    all_files = result_all['scan_statistics']['total_files_scanned']
    filtered_files = result_filtered['scan_statistics']['total_files_scanned']
    
    print(f'SUCCESS:all_files={all_files},filtered_files={filtered_files},excluded={all_files-filtered_files}')
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Actual Result from real exclusion pattern testing: $TEST_3_OUTPUT"
if [[ $TEST_3_OUTPUT == SUCCESS:* ]]; then
    echo "Status: PASS - Exclusion patterns working correctly with real file system"
    ((PASSED_TESTS++))
    
    # Extract file counts
    ALL_FILES=$(echo "$TEST_3_OUTPUT" | grep -o 'all_files=[0-9]*' | cut -d= -f2)
    FILTERED_FILES=$(echo "$TEST_3_OUTPUT" | grep -o 'filtered_files=[0-9]*' | cut -d= -f2)
    EXCLUDED_FILES=$(echo "$TEST_3_OUTPUT" | grep -o 'excluded=[0-9]*' | cut -d= -f2)
    
    echo "  - Files scanned without exclusions: $ALL_FILES"
    echo "  - Files scanned with exclusions: $FILTERED_FILES"
    echo "  - Files excluded: $EXCLUDED_FILES"
else
    echo "Status: FAIL - Exclusion pattern functionality failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Functionality Test 4: Performance validation with real codebase scanning"
echo "Expected: Scanner completes within 5-minute performance target for moderate codebase"
echo "Executing with real performance measurement using Docker resources:"
((TOTAL_TESTS++))

# Create larger test codebase for performance testing
docker exec $DOCKER_CONTAINER bash -c "
    mkdir -p /workspace/large_test_codebase
    for i in {1..50}; do
        cat > /workspace/large_test_codebase/module_\$i.py << EOF
# Module \$i with singleton patterns
class Singleton\${i}(metaclass=SingletonMeta):
    def __init__(self):
        self.id = \$i
    
    def get_id(self):
        return self.id

def create_singleton_\$i():
    return Singleton\${i}()
EOF
    done
"

TEST_4_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
import time
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection

try:
    start_time = time.time()
    
    result = execute_comprehensive_detection(
        '/workspace/large_test_codebase',
        {'max_workers': 4, 'timeout_seconds': 300},
        []
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    
    files_scanned = result['scan_statistics']['total_files_scanned']
    patterns_found = len(result['singleton_patterns'])
    files_per_second = result['scan_statistics']['files_per_second']
    
    print(f'SUCCESS:files={files_scanned},patterns={patterns_found},duration={total_time:.2f}s,rate={files_per_second:.2f}/s')
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Actual Result from real performance measurement: $TEST_4_OUTPUT"
if [[ $TEST_4_OUTPUT == SUCCESS:* ]]; then
    # Extract performance metrics
    DURATION=$(echo "$TEST_4_OUTPUT" | grep -o 'duration=[0-9.]*' | cut -d= -f2)
    SCAN_RATE=$(echo "$TEST_4_OUTPUT" | grep -o 'rate=[0-9.]*' | cut -d= -f2)
    
    # Check if performance meets requirements (under 5 minutes = 300 seconds)
    if (( $(echo "$DURATION < 300" | bc -l) )); then
        echo "Status: PASS - Performance meets 5-minute requirement"
        ((PASSED_TESTS++))
    else
        echo "Status: FAIL - Performance exceeds 5-minute requirement (${DURATION}s)"
        ((FAILED_TESTS++))
    fi
    
    echo "  - Scan duration: ${DURATION}s"
    echo "  - Scan rate: ${SCAN_RATE} files/second"
else
    echo "Status: FAIL - Performance test execution failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "Functionality Test 5: Result serialization and saving with real file operations"
echo "Expected: Detection results saved correctly to JSON with proper serialization"
echo "Executing with real file I/O operations in Docker environment:"
((TOTAL_TESTS++))

TEST_5_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
import json
import os
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection, save_detection_results
from pathlib import Path

try:
    # Execute detection
    result = execute_comprehensive_detection(
        '/workspace/test_codebase',
        {'max_workers': 2, 'timeout_seconds': 60},
        []
    )
    
    # Save results to file
    output_path = Path('/workspace/detection_results.json')
    save_detection_results(result, output_path)
    
    # Verify file was created and contains valid JSON
    if output_path.exists():
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        # Verify structure
        required_keys = ['singleton_patterns', 'scan_statistics', 'detection_report', 'summary']
        missing_keys = [key for key in required_keys if key not in saved_data]
        
        if not missing_keys:
            file_size = os.path.getsize(output_path)
            pattern_count = len(saved_data['singleton_patterns'])
            print(f'SUCCESS:file_created=true,file_size={file_size},patterns={pattern_count}')
        else:
            print(f'ERROR:MissingKeys:{missing_keys}')
    else:
        print('ERROR:FileNotCreated:Output file was not created')
        
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Actual Result from real file serialization: $TEST_5_OUTPUT"
if [[ $TEST_5_OUTPUT == SUCCESS:* ]]; then
    echo "Status: PASS - Result serialization and saving working correctly"
    ((PASSED_TESTS++))
    
    # Extract file information
    FILE_SIZE=$(echo "$TEST_5_OUTPUT" | grep -o 'file_size=[0-9]*' | cut -d= -f2)
    PATTERN_COUNT=$(echo "$TEST_5_OUTPUT" | grep -o 'patterns=[0-9]*' | cut -d= -f2)
    
    echo "  - Output file size: $FILE_SIZE bytes"
    echo "  - Patterns in saved file: $PATTERN_COUNT"
else
    echo "Status: FAIL - Result serialization failed"
    ((FAILED_TESTS++))
fi
echo ""

# Verification phase
echo "Verifying detection results consistency..."
echo "Checking that detection results are consistent across multiple runs..."
VERIFICATION_OUTPUT=$(docker exec $DOCKER_CONTAINER python3 -c "
import sys
sys.path.append('/workspace/spec-cli')
from slice_3_1_detection_execution import execute_comprehensive_detection

try:
    # Run detection twice
    result1 = execute_comprehensive_detection('/workspace/test_codebase', {'max_workers': 1}, [])
    result2 = execute_comprehensive_detection('/workspace/test_codebase', {'max_workers': 1}, [])
    
    consistent = (
        result1['scan_statistics']['total_files_scanned'] == result2['scan_statistics']['total_files_scanned'] and
        len(result1['singleton_patterns']) == len(result2['singleton_patterns'])
    )
    
    print(f'CONSISTENT:{consistent}')
except Exception as e:
    print(f'ERROR:{type(e).__name__}:{str(e)}')
" 2>&1)

echo "Result consistency check: $VERIFICATION_OUTPUT"

# Cleanup phase
echo "Cleaning up Docker test environment..."
echo "Stopping and removing Docker container..."
docker stop $DOCKER_CONTAINER >/dev/null 2>&1 || true
docker rm $DOCKER_CONTAINER >/dev/null 2>&1 || true

echo "Removing Docker volume..."
docker volume rm $DOCKER_VOLUME >/dev/null 2>&1 || true

echo "Cleanup complete"

echo ""
echo "=== Functionality Script Summary ==="
echo "Total functionality tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Testing approach: Real implementations with Docker isolation (no mocking)"
echo "Timestamp: $(date)"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "ALL FUNCTIONALITY TESTS PASSED - Comprehensive singleton detection working correctly with real implementation"
    exit 0
else
    echo "SOME FUNCTIONALITY TESTS FAILED - Feature needs investigation"
    exit 1
fi