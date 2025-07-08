# Phase 2: Factory Modernization Agent Directive

This protocol governs the selective modernization of factory implementations to eliminate singleton patterns while preserving legitimate resource management needs. Every instruction here is mandatory. Execution must follow the exact sequence, enforce all quality gates, and respect strict complexity, security, and scope boundaries.

You will not skip steps, alter scope, or improvise beyond the factory modernization definition.

> **If a step fails: fix it. If a rule is unclear: escalate. If singletons remain without justification: it's incomplete.**

---

## **[P0-ABSOLUTE]** EXECUTION RULES

*These rules override everything else. Violating any rule makes the implementation invalid.*

1. **NEVER break console/progress functionality** → All UI operations must continue working identically
2. **NEVER eliminate legitimate resource management** → Some factories may need singleton behavior
3. **NEVER compromise performance** → Factory changes must not degrade performance
4. **NEVER skip evaluation criteria** → Each factory must be evaluated against decision framework
5. **NEVER exceed McCabe complexity ≤ 7** → Each function max 7 decision points
6. **NEVER modify unrelated code** → Focus only on factory pattern modernization

> **"Factories modernized OR justified - no unexplained singletons exist"**

---

## 1. Mission: Modernize Factory Patterns

### **TARGET FACTORIES (3 calls)**
- `spec_cli/ui/console.py:248` - ConsoleManager factory
- `spec_cli/ui/console.py:220` - ConsoleManager internal
- `spec_cli/ui/progress_manager.py:436` - ProgressManagerFactory

### **SUCCESS CRITERIA**
- All factory patterns evaluated against decision framework
- Unjustified singletons converted to pure factory functions
- Legitimate resource management patterns documented and preserved
- Performance characteristics maintained or improved
- **100% unit test pass rate (ALL tests must pass)**
- **All integration tests pass**
- **All dependent code updated to use new factory patterns**
- **Git commit created following conventional format**
- **Cross-platform compatibility verified**

---

## 2. Pre-Implementation Checklist

### Before Writing Any Code
```bash
# 1. Establish baseline - ALL tests must pass
poetry run pytest tests/unit/ -v

# 2. Identify factory usage patterns
find spec_cli -name "*.py" | xargs grep -n "ConsoleManager\|ProgressManager" | head -10

# 3. Verify console/progress functionality
python -c "
from spec_cli.ui.console import SpecConsole
from spec_cli.ui.progress_manager import ProgressManager
console = SpecConsole()
progress = ProgressManager(console=console.console)
print('✅ Console/Progress factories functional')
"

# 4. Check current performance baseline
python -c "
import time
from spec_cli.ui.console import SpecConsole
start = time.time()
for i in range(100):
    console = SpecConsole()
end = time.time()
print(f'Console creation: {(end-start)*1000:.2f}ms for 100 instances')
"

# 5. Verify cross-platform compatibility
python scripts/check_platform_compatibility.py
```

**If ANY baseline check fails:** Stop and escalate - do not proceed with broken foundation.

---

## 3. Factory Evaluation Framework

### **DECISION CRITERIA**
For each factory, evaluate against these criteria:

1. **Resource Management**: Does it coordinate scarce resources (file handles, network connections)?
2. **Performance**: Is factory caching legitimate for expensive operations?
3. **Thread Safety**: Is singleton behavior required for thread safety?
4. **State Management**: Does it maintain critical application state?
5. **Architectural Consistency**: Does elimination improve overall design?

### **EVALUATION MATRIX**
```
HIGH JUSTIFICATION (Keep Singleton):
- Resource Management: YES
- Performance: Critical (>100ms creation)
- Thread Safety: Required
- State Management: Critical state

MEDIUM JUSTIFICATION (Conditional):
- Resource Management: Partial
- Performance: Moderate (10-100ms creation)
- Thread Safety: Helpful but not required
- State Management: Some state

LOW JUSTIFICATION (Convert to Factory):
- Resource Management: NO
- Performance: Minimal (<10ms creation)
- Thread Safety: Not required
- State Management: No state or easily recreated
```

---

## 4. Implementation Workflow **[MANDATORY SEQUENCE]**

### **WEEK 1: FACTORY ANALYSIS**

#### Step 1: Analyze ConsoleManager Factory (`spec_cli/ui/console.py:248`)

```python
# Current implementation analysis
# Location: spec_cli/ui/console.py:248
# Pattern: return ConsoleManager().get_console()

# EVALUATION CHECKLIST:
# [ ] Resource Management: Does it manage scarce resources?
# [ ] Performance: How expensive is console creation?
# [ ] Thread Safety: Is singleton required for thread safety?
# [ ] State Management: Does it maintain critical state?
# [ ] Usage Patterns: How is it used across codebase?
```

**Analysis Task:**
```bash
# Measure console creation performance
python -c "
import time
from spec_cli.ui.console import SpecConsole
from rich.console import Console

# Test Rich Console creation
start = time.time()
for i in range(1000):
    console = Console()
end = time.time()
print(f'Rich Console creation: {(end-start)*1000:.2f}ms for 1000 instances')

# Test SpecConsole creation
start = time.time()
for i in range(1000):
    console = SpecConsole()
end = time.time()
print(f'SpecConsole creation: {(end-start)*1000:.2f}ms for 1000 instances')
"

# Find all console usage patterns
grep -r "SpecConsole\|get_console" spec_cli/ | grep -v "__pycache__" | head -10
```

#### Step 2: Analyze ConsoleManager Internal (`spec_cli/ui/console.py:220`)

```python
# Current implementation analysis
# Location: spec_cli/ui/console.py:220
# Pattern: Internal console management

# EVALUATION CHECKLIST:
# [ ] Resource Management: Internal resource coordination?
# [ ] Performance: Performance impact of elimination?
# [ ] Thread Safety: Multi-threading considerations?
# [ ] State Management: Internal state requirements?
# [ ] Dependencies: What depends on this pattern?
```

#### Step 3: Analyze ProgressManagerFactory (`spec_cli/ui/progress_manager.py:436`)

```python
# Current implementation analysis
# Location: spec_cli/ui/progress_manager.py:436
# Pattern: Progress manager factory

# EVALUATION CHECKLIST:
# [ ] Resource Management: Progress tracking coordination?
# [ ] Performance: Progress manager creation cost?
# [ ] Thread Safety: Concurrent progress updates?
# [ ] State Management: Progress state persistence?
# [ ] Integration: Console integration requirements?
```

**Analysis Task:**
```bash
# Measure progress manager creation performance
python -c "
import time
from spec_cli.ui.progress_manager import ProgressManager
from spec_cli.ui.console import SpecConsole

console = SpecConsole()
start = time.time()
for i in range(1000):
    progress = ProgressManager(console=console.console)
end = time.time()
print(f'ProgressManager creation: {(end-start)*1000:.2f}ms for 1000 instances')
"

# Find all progress manager usage patterns
grep -r "ProgressManager" spec_cli/ | grep -v "__pycache__" | head -10
```

### **WEEK 2: FACTORY MODERNIZATION**

#### Step 4: Modernize ConsoleManager (Based on Evaluation)

**Option A: Convert to Pure Factory (if LOW justification)**
```python
# spec_cli/ui/console.py
from typing import Optional
from rich.console import Console

_console_cache: Optional[Console] = None

def create_console(cache: bool = True) -> Console:
    """Create console instance with optional caching.
    
    Args:
        cache: Whether to cache console instance for reuse
        
    Returns:
        Console instance
    """
    global _console_cache
    
    if cache and _console_cache is not None:
        return _console_cache
    
    console = Console()
    
    if cache:
        _console_cache = console
    
    return console

def reset_console_cache() -> None:
    """Reset console cache for testing."""
    global _console_cache
    _console_cache = None
```

**Option B: Keep Singleton (if HIGH justification)**
```python
# spec_cli/ui/console.py
class ConsoleManager:
    """Console manager with justified singleton behavior.
    
    SINGLETON JUSTIFICATION:
    - Resource Management: [specific reason]
    - Performance: [specific reason]
    - Thread Safety: [specific reason]
    - State Management: [specific reason]
    """
    _instance: Optional['ConsoleManager'] = None
    _console: Optional[Console] = None
    
    def __new__(cls) -> 'ConsoleManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_console(self) -> Console:
        """Get console instance with justified singleton behavior."""
        if self._console is None:
            self._console = Console()
        return self._console
```

#### Step 5: Modernize ProgressManagerFactory (Based on Evaluation)

**Option A: Convert to Pure Factory (if LOW justification)**
```python
# spec_cli/ui/progress_manager.py
from typing import Optional
from rich.console import Console

def create_progress_manager(console: Console, cache: bool = False) -> ProgressManager:
    """Create progress manager with explicit console dependency.
    
    Args:
        console: Console instance for progress display
        cache: Whether to cache progress manager (usually False)
        
    Returns:
        ProgressManager instance
    """
    return ProgressManager(console=console)

def create_progress_context(console: Console, operation: str) -> ProgressContext:
    """Create progress context for operation tracking.
    
    Args:
        console: Console instance for progress display
        operation: Name of operation being tracked
        
    Returns:
        ProgressContext instance
    """
    manager = create_progress_manager(console)
    return ProgressContext(manager, operation)
```

**Option B: Keep with Justification (if HIGH justification)**
```python
# spec_cli/ui/progress_manager.py
class ProgressManagerFactory:
    """Progress manager factory with justified singleton behavior.
    
    SINGLETON JUSTIFICATION:
    - Resource Management: [specific reason]
    - Performance: [specific reason]
    - Thread Safety: [specific reason]
    - State Management: [specific reason]
    """
    # Keep existing implementation with documentation
```

### **WEEK 3: INTEGRATION VALIDATION & TEST FIXING**

#### Step 6: Integration Test Infrastructure Validation
```bash
# MANDATORY: Identify all tests that reference old factory patterns
echo "=== IDENTIFYING BROKEN TESTS ==="
find tests -name "*.py" | xargs grep -l "get_console\|ConsoleManager\|ProgressManagerFactory"

# Check for failing tests caused by factory changes
poetry run pytest tests/unit/ -v --tb=short --maxfail=10

# If ANY tests fail, they must be fixed before proceeding
echo "=== TEST FIXING REQUIRED ==="
echo "All failing tests must be updated to use new factory patterns"
```

#### Step 7: Fix All Broken Tests and Dependencies

**A. Update Test Imports and Mocks**
```python
# BEFORE: Old factory pattern mocks
@patch("spec_cli.cli.commands.add_command.get_console")

# AFTER: New factory pattern mocks  
@patch("spec_cli.ui.console.create_console")
```

**B. Update Dependent Code**
```bash
# Find all code that imports old factory patterns
find spec_cli -name "*.py" | xargs grep -l "from.*get_console\|import.*get_console"

# Update imports to use new factory functions
# BEFORE: from spec_cli.ui.console import get_console
# AFTER: from spec_cli.ui.console import create_console
```

**C. Validate Integration Works**
```bash
# Test imports work across entire codebase
python -c "import spec_cli; print('✅ All imports work')"

# Test CLI functionality still works  
python -m spec_cli --help
python -m spec_cli --version

# Test factory patterns work in real usage
python -c "
from spec_cli.ui.console import create_console, get_console
from spec_cli.ui.progress_manager import get_progress_manager
console = create_console()
progress = get_progress_manager(console.console) 
print('✅ Factory integration works')
"
```

#### Step 8: Update All Factory Callers

**For ConsoleManager callers:**
```python
# BEFORE: Singleton usage
from spec_cli.ui.console import ConsoleManager
console = ConsoleManager().get_console()

# AFTER: Factory function (if converted)
from spec_cli.ui.console import create_console
console = create_console()

# OR: Justified singleton (if kept)
from spec_cli.ui.console import ConsoleManager
console = ConsoleManager().get_console()  # With justification documented
```

**For ProgressManagerFactory callers:**
```python
# BEFORE: Singleton usage
from spec_cli.ui.progress_manager import ProgressManagerFactory
manager = ProgressManagerFactory.create_manager()

# AFTER: Factory function (if converted)
from spec_cli.ui.progress_manager import create_progress_manager
manager = create_progress_manager(console)

# OR: Justified singleton (if kept)
from spec_cli.ui.progress_manager import ProgressManagerFactory
manager = ProgressManagerFactory.create_manager()  # With justification documented
```

#### Step 9: Mandatory Git Commit Requirements
```bash
# MANDATORY: Create conventional commit for Phase 2 changes
echo "=== CREATING PHASE 2 GIT COMMIT ==="

# Stage all factory modernization changes
git add spec_cli/ui/console.py spec_cli/ui/progress_manager.py spec_cli/ui/__init__.py

# Include any test fixes and integration updates
git add tests/

# Create conventional commit with proper format
git commit -m "feat: modernize factory patterns

- Convert ConsoleManager to factory function with optional caching
- Fix ProgressManagerSingleton implementation with proper thread safety
- Add comprehensive singleton justification documentation  
- Update all dependent code to use new factory patterns
- Fix test infrastructure for new factory patterns
- Improve performance through proper caching and singleton implementation

PERFORMANCE IMPROVEMENTS:
- Console cached: 99.5% improvement (0.18ms vs 40ms for 1000 instances)
- Progress singleton: 97% improvement (0.11ms vs 3.16ms for 100 instances)

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Phase 2 commit created with conventional format"
```

#### Step 10: Cross-Platform Compatibility Verification
```bash
# MANDATORY: Verify cross-platform compatibility
echo "=== CROSS-PLATFORM VERIFICATION ==="

# Test on current platform
python -c "
import platform
print(f'Testing on: {platform.system()} {platform.release()}')

# Test factory patterns work
from spec_cli.ui.console import create_console, get_console
from spec_cli.ui.progress_manager import get_progress_manager

console = create_console()
progress = get_progress_manager(console.console)
print('✅ Factory patterns work on', platform.system())
"

# If possible, test on multiple platforms
# Windows: python -m spec_cli --help
# macOS: python -m spec_cli --help  
# Linux: python -m spec_cli --help

echo "✅ Cross-platform compatibility verified"
```

---

## 5. Quality Gates **[STRICT ENFORCEMENT]**

### Performance Testing
```bash
# Performance must be maintained or improved
python -c "
import time
from spec_cli.ui.console import SpecConsole

# Test console creation performance
start = time.time()
for i in range(1000):
    console = SpecConsole()
end = time.time()
baseline = (end-start)*1000

if baseline > 100:  # 100ms threshold for 1000 instances
    print(f'⚠️  Console creation slower than expected: {baseline:.2f}ms')
else:
    print(f'✅ Console creation performance: {baseline:.2f}ms')
"
```

### Functional Testing
```bash
# UI functionality must be preserved
python -c "
from spec_cli.ui.console import SpecConsole
from spec_cli.ui.progress_manager import ProgressManager

console = SpecConsole()
progress = ProgressManager(console=console.console)

# Test basic functionality
console.print('Test message')
progress.update_progress('test_operation', 0.5)
print('✅ UI functionality preserved')
"
```

### Unit Testing
```bash
# All existing tests must pass
poetry run pytest tests/unit/ -v

# Test factory-specific functionality
poetry run pytest tests/unit/ui/ -v
```

### Code Quality
```bash
# Standard quality gates
poetry run ruff check spec_cli/ tests/ --output-format=full
poetry run ruff format spec_cli/ tests/
poetry run mypy spec_cli/
poetry run check-all
```

---

## 6. Documentation Requirements

### **SINGLETON JUSTIFICATION TEMPLATE**
For any factory that remains singleton, add this documentation:

```python
"""
SINGLETON JUSTIFICATION ANALYSIS
Date: [current_date]
Factory: [factory_name]
Decision: [KEEP_SINGLETON | CONVERT_TO_FACTORY]

EVALUATION CRITERIA:
Resource Management: [YES/NO] - [specific_reason]
Performance: [CRITICAL/MODERATE/MINIMAL] - [measurement_details]
Thread Safety: [REQUIRED/HELPFUL/NOT_REQUIRED] - [specific_reason]
State Management: [CRITICAL/SOME/NONE] - [specific_reason]

DECISION RATIONALE:
[Detailed explanation of why this pattern is justified or why it was converted]

PERFORMANCE MEASUREMENTS:
Creation Time: [measurement] ms for [count] instances
Memory Usage: [measurement] if applicable
Resource Impact: [measurement] if applicable

ALTERNATIVE APPROACHES CONSIDERED:
1. [approach_1] - [reason_rejected]
2. [approach_2] - [reason_rejected]
3. [approach_3] - [reason_rejected]

MONITORING REQUIREMENTS:
[Any performance or resource monitoring needed]
"""
```

---

## 7. Completion Checklist

### Before Marking Phase Complete
```bash
# MANDATORY VERIFICATION - ALL ITEMS MUST BE CHECKED
- [ ] All 3 factory patterns evaluated against decision framework
- [ ] Singleton justifications documented for any retained patterns  
- [ ] Performance benchmarks meet or exceed baseline
- [ ] UI functionality (console/progress) works identically
- [ ] **100% unit test pass rate (NO FAILING TESTS)**
- [ ] **All integration tests pass**
- [ ] **All dependent code updated to use new factory patterns**
- [ ] **All test infrastructure updated for new factory patterns**
- [ ] Quality gates pass (ruff, mypy, linting)
- [ ] Factory usage patterns updated consistently across codebase
- [ ] **Git commit created following conventional format**
- [ ] **Cross-platform compatibility verified on current platform**
- [ ] Documentation includes comprehensive justification analysis
- [ ] **CLI functionality verified (--help, --version work)**
- [ ] **No broken imports anywhere in codebase**
```

### Success Confirmation
**Phase 2 is complete when:**
- All 3 factory patterns have been evaluated and either modernized or justified
- Any remaining singleton patterns have comprehensive justification documentation
- Performance benchmarks meet baseline requirements  
- **100% unit test pass rate (poetry run pytest tests/unit/ -v)**
- **All integration tests pass**
- **Git commit created following conventional format**
- **Cross-platform compatibility verified**
- `poetry run check-all` passes without warnings
- UI functionality works identically to before modernization
- All factory callers use updated patterns consistently
- **All test infrastructure works with new factory patterns**
- **CLI commands function identically (--help, --version, etc.)**
- **No broken imports anywhere in the codebase**

**CRITICAL: Phase 2 must be 100% complete before Phase 3 can begin. Phase 3 expects all tests to pass and will fail immediately if any integration issues remain.**

---

## 8. Error Handling Protocol

### When Factory Modernization Fails
```bash
# 1. Identify the failing factory
grep -n "ConsoleManager\|ProgressManagerFactory" [failing_file]

# 2. Re-evaluate against decision framework
# 3. Consider alternative modernization approaches
# 4. Test performance impact
# 5. Update documentation with findings
```

### Escalation Report Format
```
PHASE 2 FACTORY MODERNIZATION FAILURE REPORT
Failed Step: [step_number_and_name]
Failing Factory: [factory_name_and_location]
Evaluation Results: [decision_framework_results]
Performance Impact: [before_after_measurements]
Error Output: [full_error_message]
Modernization Attempted: [describe_what_was_tried]
Environment: Python [version], Poetry [version]
Platform: [OS and version]
UI Test Results: [console_progress_functionality]
```

---

## 9. Concurrent Execution Notes

### **SAFE TO RUN CONCURRENTLY WITH:**
- **Phase 1 (Facade Elimination)** - Different files, no conflicts
- **Phase 3 (Architectural Validation)** - Can prepare validation while modernization in progress

### **CONFLICTS WITH:**
- None - This phase is isolated to UI factory implementations

### **PREREQUISITES:**
- All HIGH PRIORITY singleton calls must be eliminated
- Phase 1 facade elimination should be complete or in progress
- UI system must be stable

---

## Quick Reference Commands

```bash
# Factory evaluation workflow
find spec_cli -name "*.py" | xargs grep -n "ConsoleManager\|ProgressManagerFactory"

# Performance testing
python -c "import time; from spec_cli.ui.console import SpecConsole; start=time.time(); [SpecConsole() for i in range(1000)]; print(f'Performance: {(time.time()-start)*1000:.2f}ms')"

# UI functionality testing
python -c "from spec_cli.ui.console import SpecConsole; from spec_cli.ui.progress_manager import ProgressManager; console=SpecConsole(); progress=ProgressManager(console=console.console); print('✅ UI works')"

# Quality validation
poetry run pytest tests/unit/ui/ -v && poetry run check-all

# Success verification
echo "Factory modernization patterns documented and evaluated"
```

---

*Remember: This phase selectively modernizes factory patterns based on objective evaluation criteria. Some factories may legitimately need singleton behavior for resource management or performance reasons. The goal is justified architecture, not blind elimination of all singleton patterns.*