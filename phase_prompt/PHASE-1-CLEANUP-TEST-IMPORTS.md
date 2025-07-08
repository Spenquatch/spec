# Phase 1 Cleanup: Test Import Remediation Agent Directive

This protocol governs the systematic cleanup of test file imports that reference removed facade functions from Phase 1 Facade Elimination. Every instruction here is mandatory. Execution must follow the exact sequence, enforce all quality gates, and respect strict complexity, security, and scope boundaries.

You will not skip steps, alter scope, or improvise beyond the test import cleanup definition.

> **If a step fails: fix it. If a rule is unclear: escalate. If test imports remain: it's incomplete.**

---

## **[P0-ABSOLUTE]** EXECUTION RULES

*These rules override everything else. Violating any rule makes the implementation invalid.*

1. **NEVER break existing test functionality** → All tests must continue passing
2. **NEVER modify business logic** → Focus only on test files and imports
3. **NEVER leave broken imports** → All import errors must be resolved
4. **NEVER compromise test coverage** → Maintain or improve test coverage
5. **NEVER exceed McCabe complexity ≤ 7** → Each function max 7 decision points
6. **NEVER modify unrelated test code** → Focus only on facade import cleanup

> **"Test imports cleaned OR not touched - no partial states exist"**

---

## 1. Mission: Clean Up Test Import Technical Debt

### **TARGET FILES (4 CRITICAL + 15 MODERNIZATION)**
**CRITICAL FIXES (Runtime errors):**
- `tests/unit/config/test_loader_integration_config_002.py` - Direct get_settings import/usage
- `tests/unit/utils/test_command_analysis.py` - Direct get_console import/usage  
- `tests/integration/test_test_fixture_analysis.py` - Multiple facade imports/usage
- `tests/integration/utils/test_command_analysis_integration.py` - Direct get_console import/usage

**MODERNIZATION (Mock patches):**
- 15 test files with `@patch("*.get_console")` or `@patch("*.get_settings")` patterns

### **SUCCESS CRITERIA**
- Zero ImportError crashes from removed facade functions
- All test files use modern dependency injection patterns
- Test suite passes with 100% of previous functionality
- No facade function references in active test code
- Test coverage maintained or improved

---

## 2. Pre-Implementation Checklist

### Before Writing Any Code
```bash
# 1. Establish baseline - ALL tests must pass first
poetry run pytest tests/ -v --tb=short

# 2. Identify critical import errors
python -c "
import sys
try:
    from tests.unit.config.test_loader_integration_config_002 import *
    print('✅ Config test imports OK')
except ImportError as e:
    print(f'❌ Config test import error: {e}')
    
try:
    from tests.unit.utils.test_command_analysis import *
    print('✅ Command analysis test imports OK')
except ImportError as e:
    print(f'❌ Command analysis test import error: {e}')
"

# 3. Verify dependency injection fixtures are available
python -c "
from spec_cli.core.context import SpecContext
from spec_cli.cli.decorators import context_injection
print('✅ Dependency injection infrastructure available')
"

# 4. Count facade references in test files
find tests/ -name "*.py" -exec grep -l "get_console\|get_settings" {} \; | wc -l

# 5. Verify test framework availability
python -c "import pytest; from unittest.mock import patch, Mock; print('✅ Test framework ready')"
```

**If ANY baseline check fails:** Stop and escalate - do not proceed with broken foundation.

---

## 3. Implementation Workflow **[MANDATORY SEQUENCE]**

### **WEEK 1: CRITICAL IMPORT FIXES**

#### Step 1: Fix Direct Import Errors (Priority 1)

**File 1: `tests/unit/config/test_loader_integration_config_002.py`**
```python
# BEFORE (Line 17):
from spec_cli.config.settings import get_settings, reset_settings

# AFTER:
from spec_cli.config.settings import reset_settings
# Remove get_settings import

# BEFORE (Lines 126, 152):
settings = get_settings(temp_project_root)

# AFTER (Example pattern):
@pytest.fixture
def mock_settings():
    return Mock(spec=['no_color', 'debug_enabled'])

def test_function(mock_settings):
    # Use mock_settings instead of get_settings()
    pass
```

**File 2: `tests/unit/utils/test_command_analysis.py`**
```python
# BEFORE (Lines 32, 251, 427):
from spec_cli.ui.console import get_console

# AFTER:
# Remove get_console import entirely

# BEFORE (Line 35):
console = get_console()

# AFTER:
@pytest.fixture
def mock_console():
    return Mock(spec=['print', 'print_status'])

def test_function(mock_console):
    # Use mock_console parameter instead
    pass
```

**File 3: `tests/integration/test_test_fixture_analysis.py`**
```python
# BEFORE (Lines 200, 207, 215, 216):
from spec_cli.config.settings import get_settings
from spec_cli.ui.console import get_console, reset_console

# AFTER:
from spec_cli.ui.console import reset_console
# Remove facade function imports

# BEFORE (Line 201+):
settings = get_settings()

# AFTER:
@pytest.fixture
def spec_context():
    return SpecContext.create_for_testing()

def test_function(spec_context):
    settings = spec_context.settings
    console = spec_context.console
```

**File 4: `tests/integration/utils/test_command_analysis_integration.py`**
```python
# BEFORE (Lines 67, 119, 280):
from ...ui.console import get_console

# AFTER:
# Remove get_console import

# BEFORE (Line 75):
console = get_console()

# AFTER:
@pytest.fixture
def spec_context():
    return SpecContext.create_for_testing()

def test_function(spec_context):
    console = spec_context.console
```

#### Step 2: Validate Critical Fixes
```bash
# Test each fixed file individually
poetry run pytest tests/unit/config/test_loader_integration_config_002.py -v
poetry run pytest tests/unit/utils/test_command_analysis.py -v
poetry run pytest tests/integration/test_test_fixture_analysis.py -v
poetry run pytest tests/integration/utils/test_command_analysis_integration.py -v

# Verify no import errors
python -c "
files = [
    'tests.unit.config.test_loader_integration_config_002',
    'tests.unit.utils.test_command_analysis', 
    'tests.integration.test_test_fixture_analysis',
    'tests.integration.utils.test_command_analysis_integration'
]
for f in files:
    try:
        __import__(f)
        print(f'✅ {f} imports successfully')
    except Exception as e:
        print(f'❌ {f} import failed: {e}')
"
```

### **WEEK 2: TEST MODERNIZATION**

#### Step 3: Modernize Mock Patches (Priority 2)

**Pattern 1: Replace Facade Mocks with Context Injection**
```python
# BEFORE:
@patch("spec_cli.ui.console.get_console")
def test_something(mock_get_console):
    mock_get_console.return_value = mock_console
    
# AFTER:
@pytest.fixture
def spec_context():
    context = SpecContext.create_for_testing()
    context.console = Mock(spec=['print', 'print_status'])
    return context

def test_something(spec_context):
    # Test uses spec_context.console directly
```

**Pattern 2: Replace Settings Mocks with Context**
```python
# BEFORE:
@patch("spec_cli.core.some_module.get_settings")
def test_something(mock_get_settings):
    mock_get_settings.return_value = mock_settings
    
# AFTER:
@pytest.fixture
def spec_context():
    context = SpecContext.create_for_testing()
    context.settings = Mock(spec=['debug_enabled', 'no_color'])
    return context

def test_something(spec_context):
    # Test uses spec_context.settings directly
```

**Pattern 3: Update Function Under Test**
```python
# BEFORE:
def function_under_test():
    console = get_console()  # This was removed
    
# AFTER:
def function_under_test(console: Console):
    # Function now accepts console parameter
    
# Test becomes:
def test_function(spec_context):
    result = function_under_test(spec_context.console)
```

#### Step 4: Systematic Modernization of 15 Files

**For each file with mock patches:**

1. **Identify the mock pattern:**
   ```bash
   grep -n "@patch.*get_console\|@patch.*get_settings" [test_file]
   ```

2. **Replace with fixture pattern:**
   ```python
   @pytest.fixture
   def spec_context():
       return SpecContext.create_for_testing()
   ```

3. **Update test method signatures:**
   ```python
   def test_method(spec_context):  # Add spec_context parameter
   ```

4. **Replace facade mocks with context access:**
   ```python
   console = spec_context.console
   settings = spec_context.settings
   ```

5. **Test the individual file:**
   ```bash
   poetry run pytest [test_file] -v
   ```

#### Step 5: Verify Modernization
```bash
# Comprehensive test suite run
poetry run pytest tests/ -v --tb=short

# Verify no facade references in active code
FACADE_REFS=$(find tests/ -name "*.py" -exec grep -l "get_console()\|get_settings()" {} \; | wc -l)
echo "Active facade references in tests: $FACADE_REFS"

# Should be 0 for active calls, only mock patches acceptable
```

---

## 4. Quality Gates **[STRICT ENFORCEMENT]**

### Functional Testing
```bash
# All tests must continue passing
poetry run pytest tests/ -v

# Specific test categories
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v

# No import errors in test discovery
poetry run pytest --collect-only tests/ >/dev/null 2>&1 && echo "✅ Test discovery OK" || echo "❌ Test discovery failed"
```

### Import Validation
```bash
# Verify critical files import successfully
python -c "
critical_files = [
    'tests.unit.config.test_loader_integration_config_002',
    'tests.unit.utils.test_command_analysis',
    'tests.integration.test_test_fixture_analysis', 
    'tests.integration.utils.test_command_analysis_integration'
]
all_passed = True
for module in critical_files:
    try:
        __import__(module)
        print(f'✅ {module}')
    except Exception as e:
        print(f'❌ {module}: {e}')
        all_passed = False
        
if all_passed:
    print('✅ All critical imports successful')
else:
    print('❌ Import failures detected')
    exit(1)
"
```

### Coverage Validation
```bash
# Test coverage must be maintained
poetry run pytest tests/ --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Verify no regressions in coverage
echo "Coverage should be ≥80% and not decrease from baseline"
```

### Code Quality
```bash
# Standard quality gates for test files
poetry run ruff check tests/ --output-format=full
poetry run ruff format tests/
poetry run mypy tests/ || echo "Note: Test files may have type issues - focus on import errors"
```

---

## 5. Completion Checklist

### Before Marking Cleanup Complete
```bash
# MANDATORY VERIFICATION
- [ ] Zero ImportError crashes from facade functions
- [ ] All 4 critical files import successfully  
- [ ] All test files use modern dependency injection patterns
- [ ] Full test suite passes without failures
- [ ] No active facade function calls in test code
- [ ] Test coverage maintained at ≥80%
- [ ] Code quality gates pass
- [ ] No mock patches for removed facade functions
```

### Success Confirmation
**Cleanup is complete when:**
- `python -c "import tests.unit.config.test_loader_integration_config_002"` succeeds
- `python -c "import tests.unit.utils.test_command_analysis"` succeeds  
- `python -c "import tests.integration.test_test_fixture_analysis"` succeeds
- `python -c "import tests.integration.utils.test_command_analysis_integration"` succeeds
- `poetry run pytest tests/ -v` passes 100%
- `find tests/ -name "*.py" -exec grep -c "get_console()\|get_settings()" {} \; | awk '{sum+=$1} END {print sum}'` returns 0 for active calls
- All mock patches use modern dependency injection patterns

---

## 6. Error Handling Protocol

### When Import Fixes Fail
```bash
# 1. Identify the specific import error
python -c "
try:
    import [failing_module]
except ImportError as e:
    print(f'Import error: {e}')
    print(f'Missing: {e.name}')
"

# 2. Check if it's a facade function reference
grep -n "get_console\|get_settings" [failing_file]

# 3. Apply appropriate fix pattern:
# - Direct import: Remove from import statement
# - Direct usage: Replace with fixture parameter
# - Mock patch: Replace with context fixture

# 4. Test the fix
poetry run pytest [failing_file] -v

# 5. Verify no regressions
poetry run pytest tests/ -v --tb=short
```

### Escalation Report Format
```
PHASE 1 CLEANUP TEST IMPORT FAILURE REPORT
Failed Step: [step_number_and_name]
Failing File: [test_file_with_import_error]
Import Pattern: [describe_the_import_issue]
Error Output: [full_error_message]
Fix Attempted: [describe_what_was_tried]
Environment: Python [version], Poetry [version]
Test Results: [output of pytest command]
Coverage Impact: [before/after coverage numbers]
```

---

## 7. File-by-File Remediation Guide

### **Critical Files (Must Fix)**

#### File 1: `test_loader_integration_config_002.py`
```bash
# Issue Analysis
grep -n "get_settings" tests/unit/config/test_loader_integration_config_002.py

# Required Changes:
# - Line 17: Remove get_settings from import
# - Lines 126, 152: Replace get_settings() with fixture

# Fix Pattern:
# Replace get_settings(temp_project_root) with fixture-based settings
```

#### File 2: `test_command_analysis.py`  
```bash
# Issue Analysis
grep -n "get_console" tests/unit/utils/test_command_analysis.py

# Required Changes:
# - Lines 32, 251, 427: Remove get_console imports
# - Line 35: Replace get_console() with fixture

# Fix Pattern:
# Replace get_console() with spec_context.console parameter
```

#### File 3: `test_test_fixture_analysis.py`
```bash
# Issue Analysis  
grep -n "get_settings\|get_console" tests/integration/test_test_fixture_analysis.py

# Required Changes:
# - Multiple import lines: Remove facade function imports
# - Multiple usage lines: Replace with context fixtures

# Fix Pattern:
# Use SpecContext.create_for_testing() fixture
```

#### File 4: `test_command_analysis_integration.py`
```bash
# Issue Analysis
grep -n "get_console" tests/integration/utils/test_command_analysis_integration.py

# Required Changes:
# - Lines 67, 119, 280: Remove get_console imports  
# - Line 75: Replace get_console() call

# Fix Pattern:
# Use dependency injection with spec_context fixture
```

### **Modernization Files (15 files with mock patches)**

**Standard Modernization Pattern:**
```python
# BEFORE:
@patch("some.module.get_console")
def test_something(mock_get_console):
    mock_get_console.return_value = mock_object
    
# AFTER:
@pytest.fixture
def spec_context():
    context = SpecContext.create_for_testing()
    context.console = Mock(spec=['print', 'print_status'])
    return context
    
def test_something(spec_context):
    # Use spec_context.console directly
```

---

## 8. Verification Commands

### Quick Status Check
```bash
# Check critical import status
echo "=== Critical Import Status ==="
for file in \
    "tests.unit.config.test_loader_integration_config_002" \
    "tests.unit.utils.test_command_analysis" \
    "tests.integration.test_test_fixture_analysis" \
    "tests.integration.utils.test_command_analysis_integration"
do
    python -c "import $file; print('✅ $file')" 2>/dev/null || echo "❌ $file"
done

# Check facade references
echo "=== Facade Reference Count ==="
REFS=$(find tests/ -name "*.py" -exec grep -c "get_console()\|get_settings()" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
echo "Total facade calls in tests: $REFS"

# Test suite health
echo "=== Test Suite Health ==="
poetry run pytest tests/ --co -q | grep "test session starts" && echo "✅ Test discovery OK" || echo "❌ Test discovery failed"
```

### Success Verification
```bash
# Final comprehensive check
echo "Facade cleanup complete: $(find tests/ -name "*.py" -exec grep -c "get_console()\|get_settings()" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum+0}') active calls remaining"
poetry run pytest tests/ -v --tb=line | tail -5
```

---

*Remember: This cleanup phase eliminates technical debt from Phase 1 Facade Elimination. All test files must use modern dependency injection patterns. Test functionality must remain identical throughout the cleanup process.*