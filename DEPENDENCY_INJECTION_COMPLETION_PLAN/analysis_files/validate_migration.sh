#!/bin/bash
set -e

echo "======================================"
echo "DEPENDENCY INJECTION MIGRATION VALIDATION"
echo "======================================"
echo "Started: $(date)"
echo ""

# Test execution with timing
echo "=== RUNNING FULL TEST SUITE ==="
start_time=$(date +%s)
poetry run pytest tests/unit/ -v --tb=short
end_time=$(date +%s)
test_duration=$((end_time - start_time))
echo "Test duration: ${test_duration}s"
echo ""

# Code quality checks
echo "=== CODE QUALITY VALIDATION ==="
echo "Running ruff check..."
poetry run ruff check spec_cli/
echo "Running mypy..."
poetry run mypy spec_cli/
echo ""

# Performance comparison
echo "=== PERFORMANCE VALIDATION ==="
if [ -f baseline_performance.txt ]; then
    baseline_time=$(grep "total" baseline_performance.txt | grep -o "[0-9]*\.[0-9]*" | tail -1)
    current_time="${test_duration}"
    echo "Baseline: ${baseline_time}s"
    echo "Current: ${current_time}s"
    
    # Calculate percentage difference
    if [ -n "$baseline_time" ] && [ -n "$current_time" ] && [ "$baseline_time" != "0" ]; then
        percentage=$(echo "scale=2; (($current_time - $baseline_time) / $baseline_time) * 100" | bc -l)
        echo "Performance change: ${percentage}%"
        
        # Fail if performance degrades by more than 5%
        if (( $(echo "$percentage > 5" | bc -l) )); then
            echo "ERROR: Performance degraded by more than 5%"
            exit 1
        fi
    fi
else
    echo "No baseline performance data found"
fi

echo ""
echo "=== VALIDATION COMPLETE ==="
echo "Completed: $(date)"
echo "All validations passed!"