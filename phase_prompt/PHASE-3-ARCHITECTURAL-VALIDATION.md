# Phase 3: Architectural Validation Agent Directive

This protocol governs the comprehensive validation of the completed singleton migration to ensure architectural integrity, performance stability, and complete functionality preservation. Every instruction here is mandatory. Execution must follow the exact sequence, enforce all quality gates, and validate the entire system.

You will not skip steps, accept partial validation, or declare success without comprehensive verification.

> **If a test fails: the migration is incomplete. If performance degrades: the migration is flawed. If functionality breaks: the migration is invalid.**

---

## **[P0-ABSOLUTE]** VALIDATION RULES

*These rules override everything else. Violating any rule makes the migration invalid.*

1. **NEVER accept test failures** → 100% test pass rate required
2. **NEVER accept performance degradation** → Performance must meet or exceed baseline
3. **NEVER accept functionality regression** → All CLI features must work identically
4. **NEVER skip integration validation** → End-to-end scenarios must validate
5. **NEVER accept memory leaks** → Memory usage must be stable
6. **NEVER declare success without documentation** → Architecture decisions must be documented

> **"Migration validated OR migration invalid - no partial success exists"**

---

## 1. Mission: Validate Complete Singleton Migration

### **VALIDATION SCOPE**
- **Functional Validation**: All CLI commands and features work identically
- **Performance Validation**: No regressions in speed or memory usage
- **Integration Validation**: End-to-end workflows function correctly
- **Architecture Validation**: Dependency injection patterns are sound
- **Security Validation**: No security regressions introduced
- **Documentation Validation**: All decisions are properly documented

### **SUCCESS CRITERIA**
- 100% test pass rate
- Performance meets or exceeds baseline
- All CLI functionality preserved
- Memory usage stable
- Integration workflows validated
- Architecture documentation complete

---

## 2. Pre-Validation Checklist

### Before Starting Validation
```bash
# 1. Verify Phase 1 and Phase 2 are complete
echo "=== PHASE COMPLETION VERIFICATION ==="
echo "Phase 1 - Facade Elimination:"
FACADE_CALLS=$(find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import" | grep -v "_original_get_console\|_original_get_settings" | wc -l)
echo "  Remaining facade calls: $FACADE_CALLS"

echo "Phase 2 - Factory Modernization:"
FACTORY_DOCS=$(find spec_cli -name "*.py" | xargs grep -l "SINGLETON JUSTIFICATION" | wc -l)
echo "  Factory justifications documented: $FACTORY_DOCS"

# 2. Establish comprehensive baseline
poetry run pytest tests/unit/ -v --tb=short
poetry run check-all

# 3. Verify system stability
python -m spec_cli --version
python -m spec_cli --help

# 4. Check for any remaining singleton calls
find spec_cli -name "*.py" | xargs grep -n "get_console()\|get_settings()" | grep -v "def get_console\|def get_settings" | grep -v "from.*import"
```

**If ANY baseline check fails:** Stop and escalate - migration is not ready for validation.

---

## 3. Validation Workflow **[MANDATORY SEQUENCE]**

### **WEEK 1: FUNCTIONAL VALIDATION**

#### Step 1: Comprehensive Test Suite Validation
```bash
# Unit test validation
echo "=== UNIT TEST VALIDATION ==="
poetry run pytest tests/unit/ -v --tb=short --maxfail=5

# Integration test validation
echo "=== INTEGRATION TEST VALIDATION ==="
poetry run pytest tests/integration/ -v --tb=short --maxfail=5

# E2E test validation (if exists)
echo "=== E2E TEST VALIDATION ==="
if [ -d "tests/e2e" ]; then
    poetry run pytest tests/e2e/ -v --tb=short --maxfail=5
fi

# Test coverage validation
echo "=== TEST COVERAGE VALIDATION ==="
poetry run pytest tests/ --cov=spec_cli --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

#### Step 2: CLI Command Validation
```bash
# Test all CLI commands comprehensively
echo "=== CLI COMMAND VALIDATION ==="

# Basic command validation
python -m spec_cli --help > /dev/null && echo "✅ Help command works" || echo "❌ Help command failed"
python -m spec_cli --version > /dev/null && echo "✅ Version command works" || echo "❌ Version command failed"

# Command-specific validation
COMMANDS=("init" "status" "add" "commit" "diff" "log" "show" "gen" "regen" "agent-scope")
for cmd in "${COMMANDS[@]}"; do
    python -m spec_cli $cmd --help > /dev/null && echo "✅ $cmd help works" || echo "❌ $cmd help failed"
done
```

#### Step 3: End-to-End Workflow Validation
```bash
# Create temporary test environment
mkdir -p /tmp/spec_validation_test
cd /tmp/spec_validation_test

echo "=== END-TO-END WORKFLOW VALIDATION ==="

# Test complete workflow
echo "Testing complete spec workflow..."

# 1. Initialize repository
python -m spec_cli init && echo "✅ Init successful" || echo "❌ Init failed"

# 2. Create test content
echo "# Test Documentation" > test_doc.md
echo "This is test content for validation." >> test_doc.md

# 3. Add content to spec repository
python -m spec_cli add .specs/test_doc.md && echo "✅ Add successful" || echo "❌ Add failed"

# 4. Check status
python -m spec_cli status && echo "✅ Status successful" || echo "❌ Status failed"

# 5. Commit changes
python -m spec_cli commit -m "Test commit for validation" && echo "✅ Commit successful" || echo "❌ Commit failed"

# 6. View log
python -m spec_cli log && echo "✅ Log successful" || echo "❌ Log failed"

# 7. View diff
python -m spec_cli diff && echo "✅ Diff successful" || echo "❌ Diff failed"

# 8. Show content
python -m spec_cli show .specs/test_doc.md && echo "✅ Show successful" || echo "❌ Show failed"

# Cleanup
cd ..
rm -rf /tmp/spec_validation_test
```

### **WEEK 2: PERFORMANCE VALIDATION**

#### Step 4: Performance Baseline Comparison
```bash
# Performance test script
cat > performance_validation.py << 'EOF'
import time
import psutil
import sys
from pathlib import Path

def measure_performance():
    """Measure performance of key operations."""
    results = {}
    
    # Console creation performance
    start_time = time.time()
    for i in range(1000):
        from spec_cli.ui.console import SpecConsole
        console = SpecConsole()
    results['console_creation_1000'] = (time.time() - start_time) * 1000
    
    # Settings creation performance
    start_time = time.time()
    for i in range(1000):
        from spec_cli.config.settings import SpecSettings
        settings = SpecSettings()
    results['settings_creation_1000'] = (time.time() - start_time) * 1000
    
    # CLI help performance
    start_time = time.time()
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'spec_cli', '--help'], 
                          capture_output=True, text=True)
    results['cli_help_time'] = (time.time() - start_time) * 1000
    
    # Memory usage
    process = psutil.Process()
    results['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024
    
    return results

if __name__ == '__main__':
    results = measure_performance()
    print("=== PERFORMANCE VALIDATION RESULTS ===")
    for key, value in results.items():
        if 'time' in key:
            print(f"{key}: {value:.2f}ms")
        elif 'memory' in key:
            print(f"{key}: {value:.2f}MB")
        else:
            print(f"{key}: {value:.2f}ms")
    
    # Performance thresholds
    thresholds = {
        'console_creation_1000': 100,  # 100ms for 1000 instances
        'settings_creation_1000': 50,  # 50ms for 1000 instances
        'cli_help_time': 1000,         # 1 second for help command
        'memory_usage_mb': 100         # 100MB memory usage
    }
    
    print("\n=== PERFORMANCE THRESHOLD VALIDATION ===")
    all_passed = True
    for key, threshold in thresholds.items():
        if key in results:
            passed = results[key] <= threshold
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{key}: {results[key]:.2f} <= {threshold} {status}")
            if not passed:
                all_passed = False
    
    if all_passed:
        print("\n✅ ALL PERFORMANCE THRESHOLDS PASSED")
    else:
        print("\n❌ SOME PERFORMANCE THRESHOLDS FAILED")
        sys.exit(1)
EOF

python performance_validation.py
```

#### Step 5: Memory Leak Detection
```bash
# Memory leak detection script
cat > memory_leak_detection.py << 'EOF'
import gc
import psutil
import time
from typing import List

def measure_memory_usage() -> float:
    """Measure current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def test_memory_stability():
    """Test memory stability over repeated operations."""
    print("=== MEMORY LEAK DETECTION ===")
    
    # Baseline memory
    gc.collect()
    baseline_memory = measure_memory_usage()
    print(f"Baseline memory: {baseline_memory:.2f}MB")
    
    # Test console creation cycles
    print("Testing console creation cycles...")
    memory_samples = []
    for cycle in range(10):
        for i in range(100):
            from spec_cli.ui.console import SpecConsole
            console = SpecConsole()
            del console
        
        gc.collect()
        memory_usage = measure_memory_usage()
        memory_samples.append(memory_usage)
        print(f"Cycle {cycle + 1}: {memory_usage:.2f}MB")
    
    # Test settings creation cycles
    print("Testing settings creation cycles...")
    for cycle in range(10):
        for i in range(100):
            from spec_cli.config.settings import SpecSettings
            settings = SpecSettings()
            del settings
        
        gc.collect()
        memory_usage = measure_memory_usage()
        memory_samples.append(memory_usage)
        print(f"Settings cycle {cycle + 1}: {memory_usage:.2f}MB")
    
    # Analyze memory trend
    final_memory = measure_memory_usage()
    memory_growth = final_memory - baseline_memory
    
    print(f"\nBaseline: {baseline_memory:.2f}MB")
    print(f"Final: {final_memory:.2f}MB")
    print(f"Growth: {memory_growth:.2f}MB")
    
    # Memory leak threshold: 10MB growth is acceptable
    if memory_growth > 10:
        print("❌ POTENTIAL MEMORY LEAK DETECTED")
        return False
    else:
        print("✅ MEMORY USAGE STABLE")
        return True

if __name__ == '__main__':
    if test_memory_stability():
        print("\n✅ MEMORY LEAK DETECTION PASSED")
    else:
        print("\n❌ MEMORY LEAK DETECTION FAILED")
        exit(1)
EOF

python memory_leak_detection.py
```

### **WEEK 3: INTEGRATION VALIDATION**

#### Step 6: Cross-Platform Validation
```bash
# Cross-platform compatibility validation
echo "=== CROSS-PLATFORM VALIDATION ==="

# Path handling validation
python -c "
from pathlib import Path
import tempfile
import os

# Test cross-platform path handling
temp_dir = Path(tempfile.mkdtemp())
test_file = temp_dir / 'test.txt'
test_file.write_text('test content')

# Test with spec_cli
from spec_cli.file_system.path_resolver import PathResolver
from spec_cli.config.settings import SpecSettings

settings = SpecSettings()
resolver = PathResolver(settings)

# Test path resolution
resolved_path = resolver.resolve_path(str(test_file))
print(f'✅ Path resolution works: {resolved_path}')

# Cleanup
test_file.unlink()
temp_dir.rmdir()
"

# Environment variable handling
python -c "
import os
from spec_cli.config.settings import SpecSettings

# Test environment variable handling
os.environ['SPEC_DEBUG'] = '1'
settings = SpecSettings()
print(f'✅ Environment variable handling works: {settings.debug}')
"
```

#### Step 7: Dependency Injection Validation
```bash
# Dependency injection validation script
cat > dependency_injection_validation.py << 'EOF'
import inspect
from typing import get_type_hints

def validate_dependency_injection():
    """Validate that dependency injection patterns are properly implemented."""
    print("=== DEPENDENCY INJECTION VALIDATION ===")
    
    # Check key classes use dependency injection
    validation_targets = [
        ('spec_cli.cli.commands.generation.prompts', 'GenerationPrompts'),
        ('spec_cli.cli.commands.generation.workflows', 'AddWorkflow'),
        ('spec_cli.ui.theme', 'SpecTheme'),
    ]
    
    for module_name, class_name in validation_targets:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            
            # Check __init__ method signature
            if hasattr(cls, '__init__'):
                sig = inspect.signature(cls.__init__)
                params = list(sig.parameters.values())[1:]  # Skip 'self'
                
                print(f"\n{class_name}.__init__ parameters:")
                for param in params:
                    print(f"  {param.name}: {param.annotation}")
                
                # Check for settings parameter
                has_settings = any(
                    'settings' in param.name.lower() or 
                    'SpecSettings' in str(param.annotation)
                    for param in params
                )
                
                if has_settings:
                    print(f"✅ {class_name} uses dependency injection")
                else:
                    print(f"⚠️  {class_name} may not use dependency injection")
            
        except Exception as e:
            print(f"❌ Error validating {class_name}: {e}")
    
    # Test actual instantiation with dependency injection
    print("\n=== INSTANTIATION VALIDATION ===")
    
    try:
        from spec_cli.config.settings import SpecSettings
        from spec_cli.ui.console import SpecConsole
        
        settings = SpecSettings()
        console = SpecConsole()
        
        # Test GenerationPrompts
        from spec_cli.cli.commands.generation.prompts import GenerationPrompts
        prompts = GenerationPrompts(console, settings)
        print("✅ GenerationPrompts instantiation with DI works")
        
        # Test AddWorkflow
        from spec_cli.cli.commands.generation.workflows import AddWorkflow
        workflow = AddWorkflow(settings=settings)
        print("✅ AddWorkflow instantiation with DI works")
        
        # Test SpecTheme
        from spec_cli.ui.theme import SpecTheme
        theme = SpecTheme.from_settings(settings)
        print("✅ SpecTheme instantiation with DI works")
        
    except Exception as e:
        print(f"❌ Dependency injection validation failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    if validate_dependency_injection():
        print("\n✅ DEPENDENCY INJECTION VALIDATION PASSED")
    else:
        print("\n❌ DEPENDENCY INJECTION VALIDATION FAILED")
        exit(1)
EOF

python dependency_injection_validation.py
```

#### Step 8: Security Validation
```bash
# Security validation
echo "=== SECURITY VALIDATION ==="

# Check for security regressions
poetry run bandit -r spec_cli/ -ll

# Check for hardcoded secrets
poetry run pip-audit

# Validate environment variable usage
python -c "
import os
from spec_cli.config.settings import SpecSettings

# Test that settings still respect environment variables
os.environ['SPEC_DEBUG'] = '1'
settings = SpecSettings()
assert settings.debug == True, 'Environment variable not respected'
print('✅ Environment variable security preserved')

# Test that no hardcoded secrets exist
import spec_cli
import ast
import inspect

# This is a basic check - in production use proper secret scanning
source = inspect.getsource(spec_cli)
if 'sk-' in source or 'api_key' in source.lower():
    print('⚠️  Potential hardcoded secrets detected')
else:
    print('✅ No obvious hardcoded secrets detected')
"
```

### **WEEK 4: DOCUMENTATION VALIDATION**

#### Step 9: Architecture Documentation Validation
```bash
# Validate architecture documentation
echo "=== ARCHITECTURE DOCUMENTATION VALIDATION ==="

# Check for singleton justification documentation
JUSTIFICATION_FILES=$(find spec_cli -name "*.py" | xargs grep -l "SINGLETON JUSTIFICATION" | wc -l)
echo "Files with singleton justifications: $JUSTIFICATION_FILES"

# Check for dependency injection documentation
DI_DOCS=$(find spec_cli -name "*.py" | xargs grep -l "dependency injection\|DI" | wc -l)
echo "Files with DI documentation: $DI_DOCS"

# Validate README or architecture docs exist
if [ -f "README.md" ]; then
    echo "✅ README.md exists"
    grep -i "singleton\|dependency" README.md > /dev/null && echo "✅ Architecture patterns documented in README"
else
    echo "⚠️  README.md missing"
fi

# Check for CHANGELOG updates
if [ -f "CHANGELOG.md" ]; then
    echo "✅ CHANGELOG.md exists"
    grep -i "singleton\|dependency" CHANGELOG.md > /dev/null && echo "✅ Migration documented in CHANGELOG"
else
    echo "⚠️  Consider adding CHANGELOG.md"
fi
```

#### Step 10: Code Quality Final Validation
```bash
# Comprehensive code quality validation
echo "=== FINAL CODE QUALITY VALIDATION ==="

# All quality gates must pass
poetry run check-all

# Specific validations
poetry run ruff check spec_cli/ tests/ --output-format=full
poetry run ruff format --check spec_cli/ tests/
poetry run mypy spec_cli/
poetry run pydocstyle spec_cli/
poetry run bandit -r spec_cli/ -ll
poetry run pip-audit

# Test coverage validation
poetry run pytest tests/ --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

echo "=== FINAL QUALITY GATE RESULTS ==="
if poetry run check-all; then
    echo "✅ ALL QUALITY GATES PASSED"
else
    echo "❌ QUALITY GATES FAILED"
    exit 1
fi
```

---

## 4. Success Metrics Validation

### **MANDATORY SUCCESS CRITERIA**
```bash
# Create final validation report
cat > validation_report.md << 'EOF'
# Singleton Migration Validation Report

## Executive Summary
- **Migration Status**: [COMPLETE/INCOMPLETE]
- **Validation Date**: $(date)
- **Validation Duration**: [X weeks]

## Functional Validation
- **Unit Tests**: [PASS/FAIL] - [X/Y tests passed]
- **Integration Tests**: [PASS/FAIL] - [X/Y tests passed]
- **CLI Commands**: [PASS/FAIL] - [X/Y commands validated]
- **End-to-End Workflows**: [PASS/FAIL] - [X/Y workflows validated]

## Performance Validation
- **Console Creation**: [X.X]ms for 1000 instances (baseline: [Y.Y]ms)
- **Settings Creation**: [X.X]ms for 1000 instances (baseline: [Y.Y]ms)
- **CLI Help Command**: [X.X]ms (baseline: [Y.Y]ms)
- **Memory Usage**: [X.X]MB (baseline: [Y.Y]MB)
- **Memory Leak Detection**: [PASS/FAIL]

## Architecture Validation
- **Facade Elimination**: [COMPLETE/INCOMPLETE] - [X facade calls remaining]
- **Factory Modernization**: [COMPLETE/INCOMPLETE] - [X patterns justified]
- **Dependency Injection**: [IMPLEMENTED/PARTIAL] - [X classes converted]
- **Security**: [PASS/FAIL] - [X issues found]

## Documentation Validation
- **Singleton Justifications**: [X files documented]
- **Architecture Decisions**: [DOCUMENTED/MISSING]
- **Migration Guide**: [COMPLETE/INCOMPLETE]

## Final Recommendation
[APPROVE_MIGRATION/REJECT_MIGRATION/REQUIRES_FIXES]

## Outstanding Issues
[List any remaining issues or recommendations]
EOF

echo "Validation report generated: validation_report.md"
```

---

## 5. Completion Checklist

### Before Declaring Migration Complete
```bash
# MANDATORY VERIFICATION CHECKLIST
- [ ] 100% unit test pass rate
- [ ] 100% integration test pass rate
- [ ] All CLI commands function identically
- [ ] Performance meets or exceeds baseline
- [ ] Memory usage stable (no leaks detected)
- [ ] Cross-platform compatibility verified
- [ ] Security validation passes
- [ ] Dependency injection patterns validated
- [ ] Architecture documentation complete
- [ ] Code quality gates all pass
- [ ] Final validation report generated
```

### Success Confirmation
**Phase 3 is complete when:**
- All validation steps pass without errors
- Performance meets baseline requirements
- `poetry run check-all` passes without warnings
- All CLI functionality works identically to pre-migration state
- Memory usage is stable over time
- Security validation shows no regressions
- Architecture documentation is comprehensive
- Validation report recommends migration approval

---

## 6. Error Handling Protocol

### When Validation Fails
```bash
# 1. Identify the specific failure
# 2. Determine if it's a migration issue or validation issue
# 3. Document the failure with detailed context
# 4. Implement targeted fix
# 5. Re-run validation from appropriate step
```

### Escalation Report Format
```
PHASE 3 ARCHITECTURAL VALIDATION FAILURE REPORT
Failed Step: [step_number_and_name]
Failure Type: [FUNCTIONAL/PERFORMANCE/INTEGRATION/SECURITY]
Test Results: [specific_test_failures]
Performance Impact: [measurement_details]
Error Output: [full_error_message]
Validation Environment: [environment_details]
Reproduction Steps: [exact_steps_to_reproduce]
Migration Status: [phase_1_status/phase_2_status]
Recommended Action: [fix_migration/fix_validation/escalate]
```

---

## 7. Concurrent Execution Notes

### **DEPENDS ON:**
- **Phase 1 (Facade Elimination)** - Must be complete
- **Phase 2 (Factory Modernization)** - Must be complete

### **CONFLICTS WITH:**
- None - This is the final validation phase

### **EXECUTION ORDER:**
- This phase must run AFTER Phase 1 and Phase 2 are complete
- Cannot be started until all singleton migration work is finished

---

## Quick Reference Commands

```bash
# Comprehensive validation workflow
poetry run pytest tests/ -v --tb=short && \
python performance_validation.py && \
python memory_leak_detection.py && \
python dependency_injection_validation.py && \
poetry run check-all

# CLI functionality validation
python -m spec_cli --help && python -m spec_cli --version && python -m spec_cli init --help

# Performance quick check
python -c "import time; from spec_cli.ui.console import SpecConsole; start=time.time(); [SpecConsole() for i in range(1000)]; print(f'Performance: {(time.time()-start)*1000:.2f}ms')"

# Final validation status
echo "Migration validation complete - see validation_report.md for details"
```

---

*Remember: This phase validates the complete singleton migration. Every aspect must be thoroughly tested and validated. No shortcuts or partial validation is acceptable. The migration is either complete and validated, or it is not ready for production use.*