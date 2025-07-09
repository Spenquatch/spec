# Dependency Injection Migration Completion Plan

## Executive Summary

This document outlines a comprehensive plan to complete the singleton to dependency injection migration in the spec-cli codebase. The migration is currently 80% complete with excellent foundations, but requires targeted cleanup to achieve full architectural consistency.

## Current State Assessment

### Successfully Implemented
- SpecContext with proper dependency injection (frozen dataclass)
- CLI context injection decorators (@context_injection)
- Factory methods for CLI and testing environments
- Context bridge for logging integration
- Well-designed testing infrastructure with proper isolation

### Current Metrics
- All 1006 tests passing (100% pass rate)
- No critical linting issues, type checking passes
- Excellent performance (24.46s for full test suite)
- SpecContext properly implemented with DI architecture

### Remaining Issues to Address
1. **SettingsManager** (`spec_cli/config/settings.py:127-177`) - Remove entirely
2. **ConsoleManager** (`spec_cli/ui/console.py:248-291`) - Remove entirely
3. **Module-level caches** (`spec_cli/ui/console.py:294-369`) - Remove/manage properly
4. **ProgressManagerSingleton** (`spec_cli/ui/progress_manager.py:422-533`) - Evaluate necessity
5. **Legacy getter functions** - Remove get_settings(), get_console(), get_progress_manager()

## Implementation Strategy

### Approach: Gradual Migration
- **Risk Level**: Low-Medium (gradual approach with comprehensive testing)
- **Validation Gates**: 5 major checkpoints with rollback capability
- **Success Criteria**: 100% test pass rate maintained, no performance degradation

### Migration Phases Overview

```
PHASE 1: Analysis & Preparation (Days 1-2)
    |
    v
PHASE 2: Decouple SpecContext from Singletons (Days 3-4)
    |
    v
PHASE 3: Remove Singleton Infrastructure (Days 5-7)
    |
    v
PHASE 4: Code Migration & Cleanup (Days 8-10)
    |
    v
PHASE 5: Validation & Documentation (Days 11-12)
```

---

## PHASE 1: Analysis & Preparation

### Duration: Days 1-2

### Day 1: Current State Analysis
**Objective**: Understand current dependencies and create foundation for safe migration

**Tasks**:
1. **Create comprehensive dependency mapping**
   ```bash
   # Find all singleton getter calls
   grep -r "get_settings()" spec_cli/
   grep -r "get_console()" spec_cli/
   grep -r "get_progress_manager()" spec_cli/
   ```

2. **Identify all files with singleton imports**
   ```bash
   grep -r "from.*settings import.*get_settings" spec_cli/
   grep -r "from.*console import.*get_console" spec_cli/
   grep -r "from.*progress_manager import.*get_progress_manager" spec_cli/
   ```

3. **Document current SpecContext factory method dependencies**
   - Analyze `spec_cli/core/context.py` current implementation
   - Map out dependency chain from factory methods to singletons

4. **Analyze ProgressManagerSingleton justification**
   - Review detailed justification in `spec_cli/ui/progress_manager.py:422-533`
   - Determine if singleton pattern is truly necessary
   - Consider dependency injection alternatives

### Day 2: Validation Framework Setup
**Objective**: Establish safety mechanisms for migration

**Tasks**:
1. **Create test validation script**
   ```bash
   # Create validation script
   cat > validate_migration.sh << 'EOF'
   #!/bin/bash
   echo "Running full test suite..."
   poetry run pytest tests/unit/ -v --tb=short
   echo "Running linting..."
   poetry run ruff check spec_cli/
   echo "Running type checking..."
   poetry run mypy spec_cli/
   EOF
   chmod +x validate_migration.sh
   ```

2. **Set up performance monitoring**
   ```bash
   # Baseline performance measurement
   time poetry run pytest tests/unit/ > baseline_performance.txt
   ```

3. **Create rollback procedures**
   - Document git branch strategy for each phase
   - Create backup of critical files before modification
   - Document restoration procedures

4. **Document success criteria**
   - All 1006 tests must pass
   - Performance must not degrade >5% from 24.46s baseline
   - No new linting or type checking errors

### Deliverables
- [ ] Dependency mapping document
- [ ] ProgressManagerSingleton decision (keep/remove)
- [ ] Validation framework ready (validate_migration.sh)
- [ ] Rollback procedures documented
- [ ] Performance baseline established

### Validation Gates
- [ ] All current tests pass
- [ ] Performance baseline established
- [ ] Complete dependency mapping created

---

## PHASE 2: Decouple SpecContext from Singletons

### Duration: Days 3-4

### Day 3: Factory Method Refactoring
**Objective**: Break SpecContext dependency on singleton getters

**Critical Files to Modify**:
- `spec_cli/core/context.py` - Primary target

**Implementation Steps**:

1. **Update imports in context.py**
   ```python
   # BEFORE (current state)
   from ..config.settings import get_settings
   from ..ui.console import get_console
   from ..ui.progress_manager import get_progress_manager
   
   # AFTER (direct imports)
   from ..config.settings import SpecSettings
   from ..ui.console import SpecConsole
   from ..ui.progress_manager import ProgressManager
   ```

2. **Refactor create_for_cli() method**
   ```python
   # BEFORE (current problematic state)
   @classmethod
   def create_for_cli(cls, root_path: Path | None = None) -> "SpecContext":
       return cls(
           settings=get_settings(root_path),
           console=get_console(),
           progress=get_progress_manager(),
       )
   
   # AFTER (direct instantiation)
   @classmethod
   def create_for_cli(cls, root_path: Path | None = None) -> "SpecContext":
       if root_path is None:
           root_path = Path.cwd()
       
       # Create dependencies directly
       settings = SpecSettings(root_path)
       console = SpecConsole(
           width=settings.console_width,
           no_color=not settings.use_color,
           force_terminal=settings.use_color
       )
       progress = ProgressManager(console=console)
       
       return cls(
           settings=settings,
           console=console,
           progress=progress,
       )
   ```

3. **Ensure create_for_testing() remains unchanged**
   - Verify testing factory still uses mocks correctly
   - No changes needed to testing infrastructure

### Day 4: Factory Method Testing & Validation
**Objective**: Ensure refactored factory methods work correctly

**Testing Steps**:

1. **Run full test suite**
   ```bash
   ./validate_migration.sh
   ```

2. **Test CLI commands manually**
   ```bash
   # Test key CLI commands
   poetry run python -m spec_cli.cli.app init --help
   poetry run python -m spec_cli.cli.app status --help
   # Verify no errors in context injection
   ```

3. **Validate factory methods**
   ```python
   # Test script to verify factory behavior
   from spec_cli.core.context import SpecContext
   from pathlib import Path
   
   # Test CLI factory
   cli_context = SpecContext.create_for_cli(Path("/tmp"))
   assert cli_context.settings is not None
   assert cli_context.console is not None
   assert cli_context.progress is not None
   
   # Test testing factory
   test_context = SpecContext.create_for_testing()
   assert test_context.settings is not None
   assert test_context.console is not None
   assert test_context.progress is not None
   ```

4. **Verify context injection decorators**
   - Test that @context_injection still works
   - Ensure CLI commands receive proper context

### Deliverables
- [ ] SpecContext.create_for_cli() refactored
- [ ] Direct dependency instantiation implemented
- [ ] Factory methods tested and validated
- [ ] Context injection decorators verified

### Validation Gates
- [ ] All 1006 tests pass
- [ ] CLI commands receive proper context
- [ ] Factory methods create independent instances
- [ ] No performance degradation

---

## PHASE 3: Remove Singleton Infrastructure

### Duration: Days 5-7

### Day 5: Remove SettingsManager & ConsoleManager
**Objective**: Remove singleton management classes

**Files to Modify**:
- `spec_cli/config/settings.py` (remove lines 127-177)
- `spec_cli/ui/console.py` (remove lines 248-291 and 294-369)

**Implementation Steps**:

1. **Remove SettingsManager class**
   ```python
   # DELETE these lines from spec_cli/config/settings.py:127-177
   class SettingsManager:
       def __init__(self) -> None:
           self._settings_instance: SpecSettings | None = None
           self._console_instance: Console | None = None
       # ... rest of class
   ```

2. **Remove ConsoleManager class**
   ```python
   # DELETE these lines from spec_cli/ui/console.py:248-291
   class ConsoleManager:
       def __init__(self, settings: Any = None) -> None:
           # ... implementation
   ```

3. **Remove module-level cache functions**
   ```python
   # DELETE these lines from spec_cli/ui/console.py:294-369
   _console_cache: SpecConsole | None = None
   
   def create_console(cache: bool = True, ...) -> SpecConsole:
       # ... implementation
   ```

4. **Update any imports referencing these classes**
   ```bash
   # Find and update imports
   grep -r "SettingsManager" spec_cli/
   grep -r "ConsoleManager" spec_cli/
   ```

### Day 6: Handle ProgressManagerSingleton
**Objective**: Address ProgressManagerSingleton based on Phase 1 analysis

**Decision Tree**:
```
ProgressManagerSingleton Analysis
    |
    |-- Singleton Justified?
    |   |-- YES: Keep with updated documentation
    |   |-- NO: Remove and implement DI alternative
    |
    |-- Implementation:
        |-- If Keep: Update documentation, ensure proper integration
        |-- If Remove: Refactor to context-based approach
```

**If Removing ProgressManagerSingleton**:
1. **Refactor ProgressManager instantiation**
   ```python
   # Ensure ProgressManager can be instantiated directly
   # Update constructor to not require singleton pattern
   ```

2. **Update context factory**
   ```python
   # In SpecContext.create_for_cli()
   progress = ProgressManager(console=console)
   ```

**If Keeping ProgressManagerSingleton**:
1. **Document justification clearly**
2. **Ensure it integrates properly with DI system**
3. **Update context factory to use it appropriately**

### Day 7: Remove Legacy Getter Functions
**Objective**: Remove all singleton getter functions

**Functions to Remove**:
- `get_settings()` from `spec_cli/config/settings.py`
- `get_console()` from `spec_cli/ui/console.py`
- `get_progress_manager()` from `spec_cli/ui/progress_manager.py`

**Implementation Steps**:

1. **Remove getter functions**
   ```python
   # DELETE these functions:
   def get_settings(root_path: Path | None = None) -> SpecSettings:
       # ... implementation
   
   def get_console() -> SpecConsole:
       # ... implementation
   
   def get_progress_manager() -> ProgressManager:
       # ... implementation
   ```

2. **Update __init__.py files**
   ```python
   # Remove exports of getter functions
   # Update __all__ lists to remove these functions
   ```

3. **Run validation**
   ```bash
   ./validate_migration.sh
   ```

### Deliverables
- [ ] SettingsManager removed
- [ ] ConsoleManager removed
- [ ] Module-level caches removed
- [ ] ProgressManagerSingleton evaluated and handled
- [ ] Legacy getter functions removed

### Validation Gates
- [ ] All 1006 tests pass
- [ ] No import errors
- [ ] No references to singleton patterns remain

---

## PHASE 4: Code Migration & Cleanup

### Duration: Days 8-10

### Day 8-9: Update All Consumers
**Objective**: Update all remaining code to use SpecContext

**Discovery Process**:
1. **Find all remaining singleton references**
   ```bash
   # Search for any remaining calls to removed functions
   grep -r "get_settings(" spec_cli/
   grep -r "get_console(" spec_cli/
   grep -r "get_progress_manager(" spec_cli/
   ```

2. **Identify files needing refactoring**
   ```bash
   # Find files that import the removed functions
   grep -r "from.*import.*get_settings" spec_cli/
   grep -r "from.*import.*get_console" spec_cli/
   grep -r "from.*import.*get_progress_manager" spec_cli/
   ```

**Refactoring Pattern**:
```python
# BEFORE: Function using singleton getter
def some_function():
    settings = get_settings()
    settings.some_method()

# AFTER: Function accepting context
def some_function(context: SpecContext):
    context.settings.some_method()
```

**Implementation Steps**:

1. **Update function signatures**
   - Add `context: SpecContext` parameter to functions
   - Update type hints appropriately

2. **Update function calls**
   - Replace singleton calls with context access
   - Thread context through call chains

3. **Update all call sites**
   - Pass context to refactored functions
   - Ensure context flows through entire call stack

### Day 10: Final Architectural Cleanup
**Objective**: Ensure complete architectural consistency

**Cleanup Tasks**:

1. **Remove unused imports**
   ```python
   # Clean up any imports that are no longer needed
   # Remove references to deleted singleton classes
   ```

2. **Update type hints**
   ```python
   # Ensure all type hints reference actual classes, not singletons
   # Update return types and parameter types
   ```

3. **Clean up comments and docstrings**
   ```python
   # Remove references to singleton patterns in documentation
   # Update docstrings to reflect new architecture
   ```

4. **Architectural consistency verification**
   ```bash
   # Verify no singleton patterns remain
   grep -r -i "singleton" spec_cli/ --exclude-dir=utils
   # (utils may contain detection tools, which is acceptable)
   ```

### Deliverables
- [ ] All consumers updated to use SpecContext
- [ ] Functions refactored to accept context parameter
- [ ] Call sites updated to pass context
- [ ] Unused imports removed
- [ ] Type hints updated
- [ ] Comments and docstrings cleaned up

### Validation Gates
- [ ] All 1006 tests pass
- [ ] No singleton patterns remain (except documented exceptions)
- [ ] All dependencies flow through SpecContext
- [ ] Performance maintained

---

## PHASE 5: Validation & Documentation

### Duration: Days 11-12

### Day 11: Comprehensive Testing & Validation
**Objective**: Ensure migration completion and stability

**Testing Protocol**:

1. **Full test suite execution**
   ```bash
   # Run tests multiple times to ensure stability
   for i in {1..5}; do
       echo "Test run $i"
       ./validate_migration.sh
   done
   ```

2. **Performance benchmarking**
   ```bash
   # Compare with baseline
   echo "Current performance:"
   time poetry run pytest tests/unit/
   echo "Baseline was: 24.46s"
   # Ensure <5% degradation
   ```

3. **Code quality validation**
   ```bash
   # Comprehensive quality checks
   poetry run ruff check spec_cli/
   poetry run mypy spec_cli/
   poetry run pytest tests/unit/ --cov=spec_cli --cov-report=term-missing
   ```

4. **Architecture consistency verification**
   ```bash
   # Verify singleton removal
   grep -r "class.*Manager" spec_cli/ | grep -v "# OK: Not singleton"
   grep -r "def get_.*(" spec_cli/ | grep -v "# OK: Not singleton getter"
   ```

5. **Integration testing**
   ```bash
   # Test all CLI commands
   poetry run python -m spec_cli.cli.app init --help
   poetry run python -m spec_cli.cli.app status --help
   poetry run python -m spec_cli.cli.app gen --help
   # Verify no errors in context injection
   ```

### Day 12: Documentation & Finalization
**Objective**: Complete migration with proper documentation

**Documentation Tasks**:

1. **Update ARCHITECTURE_IMPROVEMENT.md**
   ```markdown
   # Add completion section
   ## Migration Status: COMPLETED
   
   ### Final State
   - All singleton patterns removed (except documented exceptions)
   - Complete dependency injection through SpecContext
   - All 1006 tests passing
   - Performance maintained
   
   ### Architectural Consistency Achieved
   - No SettingsManager, ConsoleManager, or module-level caches
   - All dependencies flow through SpecContext
   - Factory methods create fresh instances
   ```

2. **Update code comments and docstrings**
   ```python
   # Update any remaining references to singleton patterns
   # Ensure docstrings reflect new architecture
   # Add comments about dependency injection approach
   ```

3. **Create migration summary document**
   ```markdown
   # MIGRATION_SUMMARY.md
   - Components removed: SettingsManager, ConsoleManager, caches
   - Dependencies now flow through SpecContext
   - Benefits: Better testing, no state leakage, clear dependencies
   ```

4. **Final code review**
   - Review all changed files
   - Ensure consistent coding style
   - Verify architectural patterns are properly implemented

### Deliverables
- [ ] Full test suite validated (multiple runs)
- [ ] Performance benchmarking completed
- [ ] Code quality validation passed
- [ ] Architecture consistency verified
- [ ] Integration testing completed
- [ ] ARCHITECTURE_IMPROVEMENT.md updated
- [ ] Migration summary document created
- [ ] Final code review completed

### Validation Gates
- [ ] All 1006 tests pass consistently
- [ ] Performance within 5% of baseline (24.46s)
- [ ] No linting or type checking errors
- [ ] Architecture consistency achieved
- [ ] Documentation updated

---

## Success Metrics

### Quantitative Metrics
- **Test Pass Rate**: 100% (all 1006 tests)
- **Performance**: <5% degradation from 24.46s baseline
- **Code Quality**: Zero linting or type checking errors
- **Architecture**: Zero singleton patterns (except documented exceptions)

### Qualitative Metrics
- **Maintainability**: Clear dependency flow through SpecContext
- **Testability**: Easy to mock dependencies for testing
- **Consistency**: Uniform architectural patterns throughout codebase
- **Documentation**: Complete and accurate architectural documentation

## Risk Assessment and Mitigation

### Low Risk Items
- **SpecContext already implemented**: Foundation is solid
- **Tests comprehensive**: 1006 tests provide good coverage
- **Performance baseline good**: 24.46s allows for some overhead

### Medium Risk Items
- **ProgressManagerSingleton decision**: May require careful evaluation
- **Legacy code updates**: May have hidden dependencies
- **Performance impact**: Object creation overhead possible

### Mitigation Strategies
- **Gradual approach**: Phase-by-phase implementation with validation
- **Rollback procedures**: Documented procedures for each phase
- **Comprehensive testing**: Full test suite after each phase
- **Performance monitoring**: Baseline and continuous monitoring

## Implementation Commands

### Quick Start Commands
```bash
# 1. Set up validation framework
cat > validate_migration.sh << 'EOF'
#!/bin/bash
poetry run pytest tests/unit/ -v --tb=short
poetry run ruff check spec_cli/
poetry run mypy spec_cli/
EOF
chmod +x validate_migration.sh

# 2. Create performance baseline
time poetry run pytest tests/unit/ > baseline_performance.txt

# 3. Create dependency mapping
grep -r "get_settings()" spec_cli/ > dependency_mapping.txt
grep -r "get_console()" spec_cli/ >> dependency_mapping.txt
grep -r "get_progress_manager()" spec_cli/ >> dependency_mapping.txt
```

### Phase Validation Commands
```bash
# After each phase, run:
./validate_migration.sh
git add .
git commit -m "Phase X completed - all tests passing"
```

## Conclusion

This comprehensive plan provides a safe, systematic approach to completing the dependency injection migration. The gradual phase-by-phase implementation ensures minimal risk while achieving complete architectural consistency.

The plan addresses all identified issues:
- Removes all singleton patterns (4 specific areas)
- Ensures complete dependency injection through SpecContext
- Maintains test quality and performance
- Updates documentation to reflect new architecture

Upon completion, the codebase will have clean, maintainable architecture with explicit dependencies and no global state contamination.

---

**Total Duration**: 12 days
**Risk Level**: Low-Medium
**Success Probability**: High (due to existing foundation and comprehensive testing)
**Key Benefit**: Complete architectural consistency with dependency injection