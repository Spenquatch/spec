# PHASE 3: REMOVE SINGLETON INFRASTRUCTURE - COMPREHENSIVE EXECUTION PROMPT

## MISSION STATEMENT
You are tasked with completing **Phase 3** of the dependency injection migration completion plan. This phase removes the remaining singleton infrastructure classes and legacy getter functions, completing the architectural migration to full dependency injection while preserving the justified ProgressManagerSingleton.

## CRITICAL SUCCESS CRITERIA
- **All 1006 tests must continue to pass** throughout this phase
- **Performance must not degrade** by more than 5% from baseline (~25s)
- **All singleton infrastructure** must be removed (except ProgressManagerSingleton)
- **All legacy getter functions** must be removed
- **No import errors** must occur due to removed dependencies
- **CLI functionality** must remain completely unchanged

---

## P0 ABSOLUTE INSTRUCTIONS - MANDATORY COMPLIANCE

### 🚨 CRITICAL SAFETY REQUIREMENTS

1. **PRESERVE PROGRESSMANAGERSINGLETON** - Based on Phase 1 analysis, this must be kept
2. **MAINTAIN TEST COMPATIBILITY** - All existing tests must continue passing
3. **VALIDATE CONTINUOUSLY** - Run validation after each major removal
4. **BACKUP BEFORE MODIFICATION** - Create backups before changing any files
5. **ROLLBACK ON FAILURE** - Use rollback procedures if any validation fails

### 🔒 GUARDRAILS AND CONSTRAINTS

1. **INCREMENTAL REMOVAL**: Remove one singleton class at a time with validation
2. **DEPENDENCY VERIFICATION**: Ensure no remaining code depends on removed classes
3. **IMPORT CLEANUP**: Update all import statements and __init__.py files
4. **PERFORMANCE MONITORING**: Monitor performance impact continuously
5. **FUNCTIONAL TESTING**: Validate CLI commands work correctly after changes

### ⚠️ FAILURE CONDITIONS - STOP IMMEDIATELY IF:

- Any test fails during validation
- Performance degrades by more than 5%
- CLI commands fail or behave differently
- Import errors occur due to circular dependencies
- Any code still references removed singleton classes
- ProgressManagerSingleton functionality is compromised

---

## PHASE 3 CONTEXT AND BACKGROUND

### Phase 1 & 2 Prerequisites
Before starting Phase 3, ensure previous phases are complete:
- [ ] Phase 1: Complete dependency mapping and ProgressManagerSingleton decision (KEEP)
- [ ] Phase 2: SpecContext factory methods refactored to direct instantiation
- [ ] validate_migration.sh operational and tested
- [ ] rollback_migration.sh tested and verified
- [ ] All 1006 tests passing at baseline performance (~25s)

### Current State Assessment
Based on Phase 1 analysis, the migration is **95% complete** with these remaining cleanup items:

1. **SettingsManager** (`spec_cli/config/settings.py:127-177`) - Remove entirely
2. **ConsoleManager** (`spec_cli/ui/console.py:248-291`) - Remove entirely  
3. **Module-level caches** (`spec_cli/ui/console.py:294-369`) - Remove entirely
4. **ProgressManagerSingleton** - **KEEP** per Phase 1 decision with documentation
5. **Legacy getter functions** - Remove get_settings(), get_console(), get_progress_manager()

### Target Architecture
After Phase 3, the architecture will have:
- ✅ Complete dependency injection through SpecContext
- ✅ No singleton management classes (except ProgressManagerSingleton)
- ✅ No legacy getter functions
- ✅ No module-level caches
- ✅ Clean import structure with no singleton references

---

## DETAILED EXECUTION PLAN

### DAY 5: REMOVE SETTINGSMANAGER & CONSOLEMANAGER

#### Task 5.1: Pre-Removal Validation and Setup
**Objective**: Ensure clean starting state and create safety framework

**Commands to Execute**:
```bash
# 1. Validate current test state
echo "=== PRE-PHASE 3 VALIDATION ==="
./validate_migration.sh | tee phase3_pre_validation.txt

# 2. Create additional backups for Phase 3
echo "=== CREATING PHASE 3 BACKUPS ==="
cp spec_cli/config/settings.py spec_cli/config/settings.py.phase3_backup
cp spec_cli/ui/console.py spec_cli/ui/console.py.phase3_backup
cp spec_cli/ui/progress_manager.py spec_cli/ui/progress_manager.py.phase3_backup

# 3. Document current singleton references
echo "=== DOCUMENTING CURRENT SINGLETON STATE ===" > phase3_removal_log.txt
echo "SettingsManager references:" >> phase3_removal_log.txt
grep -r "SettingsManager" spec_cli/ >> phase3_removal_log.txt
echo "" >> phase3_removal_log.txt

echo "ConsoleManager references:" >> phase3_removal_log.txt
grep -r "ConsoleManager" spec_cli/ >> phase3_removal_log.txt
echo "" >> phase3_removal_log.txt

echo "Module-level cache references:" >> phase3_removal_log.txt
grep -r "_console_cache\|create_console" spec_cli/ >> phase3_removal_log.txt
echo "" >> phase3_removal_log.txt
```

**Expected Outputs**:
- All 1006 tests should pass
- Phase 3 backup files created successfully
- Current singleton state documented

**Validation**:
- [ ] All tests pass (1006/1006)
- [ ] Phase 3 backup files created
- [ ] Singleton references documented

#### Task 5.2: Remove SettingsManager Class
**Objective**: Remove SettingsManager singleton infrastructure from config module

**Commands to Execute**:
```bash
# 1. Identify SettingsManager location and dependencies
echo "=== ANALYZING SETTINGSMANAGER REMOVAL ===" >> phase3_removal_log.txt
echo "Target: spec_cli/config/settings.py lines 127-177" >> phase3_removal_log.txt

# Check for any current imports of SettingsManager
grep -r "from.*settings import.*SettingsManager" spec_cli/ >> phase3_removal_log.txt
grep -r "import.*SettingsManager" spec_cli/ >> phase3_removal_log.txt

# 2. Remove SettingsManager class (lines 127-177)
# Create a temporary file without the SettingsManager class
echo "Creating settings.py without SettingsManager..."
head -126 spec_cli/config/settings.py > temp_settings.py
tail -n +178 spec_cli/config/settings.py >> temp_settings.py
mv temp_settings.py spec_cli/config/settings.py

# 3. Update config/__init__.py to remove SettingsManager export
sed -i.bak '/SettingsManager/d' spec_cli/config/__init__.py

# 4. Validate removal
echo "=== VALIDATING SETTINGSMANAGER REMOVAL ===" >> phase3_removal_log.txt
echo "Checking for remaining SettingsManager references..." >> phase3_removal_log.txt
if grep -r "SettingsManager" spec_cli/ >> phase3_removal_log.txt 2>&1; then
    echo "WARNING: SettingsManager references still found!" >> phase3_removal_log.txt
else
    echo "SUCCESS: No SettingsManager references found" >> phase3_removal_log.txt
fi

# 5. Run validation
./validate_migration.sh | tee settingsmanager_removal_validation.txt
```

**Expected Outputs**:
- SettingsManager class removed from settings.py
- No remaining SettingsManager references in codebase
- All tests continue to pass
- No import errors

**Validation Requirements**:
- [ ] SettingsManager class removed from spec_cli/config/settings.py
- [ ] No remaining SettingsManager references in codebase
- [ ] config/__init__.py updated to remove SettingsManager export
- [ ] All 1006 tests pass
- [ ] No import errors

#### Task 5.3: Remove ConsoleManager Class and Module-Level Caches
**Objective**: Remove ConsoleManager singleton infrastructure and module-level caches

**Commands to Execute**:
```bash
# 1. Identify ConsoleManager and cache locations
echo "=== ANALYZING CONSOLEMANAGER REMOVAL ===" >> phase3_removal_log.txt
echo "Target: spec_cli/ui/console.py lines 248-291 and 294-369" >> phase3_removal_log.txt

# Check for any current imports of ConsoleManager
grep -r "from.*console import.*ConsoleManager" spec_cli/ >> phase3_removal_log.txt
grep -r "import.*ConsoleManager" spec_cli/ >> phase3_removal_log.txt

# Check for module-level cache usage
grep -r "_console_cache\|create_console" spec_cli/ >> phase3_removal_log.txt

# 2. Remove ConsoleManager class (lines 248-291)
# Create a temporary file without ConsoleManager and caches
head -247 spec_cli/ui/console.py > temp_console.py
# Skip lines 248-291 (ConsoleManager class)
tail -n +292 spec_cli/ui/console.py | head -2 >> temp_console.py
# Skip lines 294-369 (module-level caches)
tail -n +370 spec_cli/ui/console.py >> temp_console.py
mv temp_console.py spec_cli/ui/console.py

# 3. Update ui/__init__.py to remove ConsoleManager export
sed -i.bak '/ConsoleManager/d' spec_cli/ui/__init__.py
sed -i.bak '/create_console/d' spec_cli/ui/__init__.py

# 4. Validate removal
echo "=== VALIDATING CONSOLEMANAGER REMOVAL ===" >> phase3_removal_log.txt
echo "Checking for remaining ConsoleManager references..." >> phase3_removal_log.txt
if grep -r "ConsoleManager\|_console_cache\|create_console" spec_cli/ >> phase3_removal_log.txt 2>&1; then
    echo "WARNING: ConsoleManager/cache references still found!" >> phase3_removal_log.txt
else
    echo "SUCCESS: No ConsoleManager/cache references found" >> phase3_removal_log.txt
fi

# 5. Run validation
./validate_migration.sh | tee consolemanager_removal_validation.txt
```

**Expected Outputs**:
- ConsoleManager class removed from console.py
- Module-level cache functions removed
- No remaining ConsoleManager or cache references
- All tests continue to pass

**Validation Requirements**:
- [ ] ConsoleManager class removed from spec_cli/ui/console.py
- [ ] Module-level cache functions removed
- [ ] ui/__init__.py updated to remove ConsoleManager exports
- [ ] All 1006 tests pass
- [ ] No import errors

### DAY 6: HANDLE PROGRESSMANAGERSINGLETON

#### Task 6.1: Document ProgressManagerSingleton Preservation
**Objective**: Properly document the decision to keep ProgressManagerSingleton

**Commands to Execute**:
```bash
# 1. Create architectural decision record
cat > docs/adr/001-retain-progress-manager-singleton.md << 'EOF'
# ADR 001: Retain ProgressManagerSingleton

## Status
Accepted

## Context
During the dependency injection migration analysis (Phase 1), we evaluated whether to remove ProgressManagerSingleton as part of the singleton elimination effort.

## Decision
We will **KEEP** ProgressManagerSingleton for the following reasons:

### Technical Justification
1. **Resource Management**: Progress display coordination across threads requires global state
2. **Thread Safety**: Uses threading.Lock for proper concurrent access management  
3. **Performance**: 3.16ms/100 instances is reasonable overhead for singleton pattern
4. **State Management**: Active operations tracking requires shared state coordination
5. **UI Coordination**: Multiple progress bars would conflict without central coordination

### Analysis Summary
- Resource Management: HIGH - progress display coordination critical
- Performance: MEDIUM - 3.16ms/100 instances acceptable  
- Thread Safety: HIGH - needs coordination across threads
- State Management: HIGH - active operations, progress states, event handlers
- Alternative Solutions: INSUFFICIENT - dependency injection cannot solve same problems

## Consequences
- ProgressManagerSingleton remains as justified exception to DI architecture
- get_progress_manager() function preserved for consistent access
- Clear documentation prevents future refactoring attempts
- Architecture remains 95% dependency injection with one justified singleton

## References
- Phase 1 Analysis: progress_manager_analysis.txt
- Performance measurements: 3.16ms/100 instances
- Thread safety implementation: threading.Lock usage documented
EOF

# 2. Update ProgressManagerSingleton documentation
cat > temp_progress_manager_docs.py << 'EOF'
"""
ARCHITECTURAL DECISION: ProgressManagerSingleton is intentionally preserved.

This singleton is retained after comprehensive analysis (Phase 1) because:
1. Global progress coordination is legitimately required
2. Thread safety across UI components is critical
3. Alternative patterns do not solve the same coordination problems
4. Performance impact is minimal and justified

See: docs/adr/001-retain-progress-manager-singleton.md

This is the ONLY remaining singleton in the codebase and is architecturally justified.
"""
EOF

# Add the documentation to the top of progress_manager.py
cat temp_progress_manager_docs.py > temp_file
cat spec_cli/ui/progress_manager.py >> temp_file
mv temp_file spec_cli/ui/progress_manager.py
rm temp_progress_manager_docs.py

# 3. Validate ProgressManagerSingleton integration
echo "=== VALIDATING PROGRESSMANAGERSINGLETON PRESERVATION ===" >> phase3_removal_log.txt
echo "Confirming ProgressManagerSingleton remains functional..." >> phase3_removal_log.txt
./validate_migration.sh | tee progressmanager_preservation_validation.txt
```

**Expected Outputs**:
- ADR document created explaining decision
- ProgressManagerSingleton properly documented
- All tests continue to pass
- get_progress_manager() function preserved

**Validation Requirements**:
- [ ] ADR 001 created documenting ProgressManagerSingleton decision
- [ ] ProgressManagerSingleton class properly documented
- [ ] get_progress_manager() function preserved and functional
- [ ] All 1006 tests pass

### DAY 7: REMOVE LEGACY GETTER FUNCTIONS

#### Task 7.1: Remove get_settings() and get_console() Functions
**Objective**: Remove legacy singleton getter functions while preserving get_progress_manager()

**Commands to Execute**:
```bash
# 1. Document current getter function locations
echo "=== ANALYZING LEGACY GETTER REMOVAL ===" >> phase3_removal_log.txt
echo "Removing: get_settings() and get_console()" >> phase3_removal_log.txt
echo "Preserving: get_progress_manager() (justified)" >> phase3_removal_log.txt

# Check current usage to ensure none exist
grep -r "get_settings(" spec_cli/ >> phase3_removal_log.txt
grep -r "get_console(" spec_cli/ >> phase3_removal_log.txt

# 2. Remove get_settings() function from settings.py
echo "Removing get_settings() function..."
sed -i.bak '/def get_settings(/,/^$/d' spec_cli/config/settings.py

# 3. Remove get_console() function from console.py  
echo "Removing get_console() function..."
sed -i.bak '/def get_console(/,/^$/d' spec_cli/ui/console.py

# 4. Update __init__.py files to remove getter exports
sed -i.bak '/get_settings/d' spec_cli/config/__init__.py
sed -i.bak '/get_console/d' spec_cli/ui/__init__.py

# 5. Validate removal
echo "=== VALIDATING GETTER FUNCTION REMOVAL ===" >> phase3_removal_log.txt
echo "Checking for remaining get_settings() references..." >> phase3_removal_log.txt
if grep -r "get_settings(" spec_cli/ >> phase3_removal_log.txt 2>&1; then
    echo "ERROR: get_settings() references still found!" >> phase3_removal_log.txt
else
    echo "SUCCESS: No get_settings() references found" >> phase3_removal_log.txt
fi

echo "Checking for remaining get_console() references..." >> phase3_removal_log.txt
if grep -r "get_console(" spec_cli/ >> phase3_removal_log.txt 2>&1; then
    echo "ERROR: get_console() references still found!" >> phase3_removal_log.txt
else
    echo "SUCCESS: No get_console() references found" >> phase3_removal_log.txt
fi

# 6. Confirm get_progress_manager() is preserved
echo "Confirming get_progress_manager() is preserved..." >> phase3_removal_log.txt
if grep -r "get_progress_manager(" spec_cli/ >> phase3_removal_log.txt 2>&1; then
    echo "SUCCESS: get_progress_manager() preserved as intended" >> phase3_removal_log.txt
else
    echo "ERROR: get_progress_manager() accidentally removed!" >> phase3_removal_log.txt
fi

# 7. Run validation
./validate_migration.sh | tee getter_removal_validation.txt
```

**Expected Outputs**:
- get_settings() function removed from settings.py
- get_console() function removed from console.py
- get_progress_manager() function preserved
- __init__.py files updated appropriately
- All tests continue to pass

**Validation Requirements**:
- [ ] get_settings() function removed completely
- [ ] get_console() function removed completely  
- [ ] get_progress_manager() function preserved and functional
- [ ] __init__.py files updated to remove exports
- [ ] All 1006 tests pass

#### Task 7.2: Final Cleanup and Architecture Consistency
**Objective**: Ensure complete architectural consistency and clean final state

**Commands to Execute**:
```bash
# 1. Comprehensive singleton pattern check
echo "=== FINAL ARCHITECTURE CONSISTENCY CHECK ===" >> phase3_removal_log.txt
echo "Scanning for any remaining singleton patterns..." >> phase3_removal_log.txt

# Check for any remaining singleton classes (except ProgressManagerSingleton)
echo "Remaining singleton classes:" >> phase3_removal_log.txt
grep -r "class.*Manager\|class.*Singleton" spec_cli/ | grep -v "ProgressManagerSingleton" >> phase3_removal_log.txt

# Check for any remaining getter functions (except get_progress_manager)
echo "Remaining getter functions:" >> phase3_removal_log.txt
grep -r "def get_.*(" spec_cli/ | grep -v "get_progress_manager\|get_.*_path\|get_.*_config" >> phase3_removal_log.txt

# 2. Clean up any unused imports
echo "Checking for unused imports..." >> phase3_removal_log.txt
grep -r "from.*import.*SettingsManager\|from.*import.*ConsoleManager" spec_cli/ >> phase3_removal_log.txt

# 3. Update any remaining comments referencing removed singletons
find spec_cli/ -name "*.py" -exec sed -i.bak 's/SettingsManager/SpecSettings/g' {} \;
find spec_cli/ -name "*.py" -exec sed -i.bak 's/ConsoleManager/SpecConsole/g' {} \;

# 4. Remove backup files created during editing
find spec_cli/ -name "*.bak" -delete

# 5. Final comprehensive validation
echo "=== FINAL PHASE 3 VALIDATION ===" >> phase3_removal_log.txt
./validate_migration.sh | tee phase3_final_validation.txt

# 6. Generate completion summary
cat > PHASE_3_COMPLETION_SUMMARY.md << 'EOF'
# PHASE 3 COMPLETION SUMMARY

## Removals Completed
- ✅ SettingsManager class removed from spec_cli/config/settings.py
- ✅ ConsoleManager class removed from spec_cli/ui/console.py  
- ✅ Module-level cache functions removed from spec_cli/ui/console.py
- ✅ get_settings() function removed
- ✅ get_console() function removed
- ✅ Updated __init__.py files to remove exports

## Preservations (Justified)
- ✅ ProgressManagerSingleton preserved with comprehensive documentation
- ✅ get_progress_manager() function preserved
- ✅ ADR 001 created documenting architectural decision

## Architecture State
- ✅ 95% dependency injection through SpecContext
- ✅ One justified singleton (ProgressManagerSingleton) with clear documentation
- ✅ No legacy singleton infrastructure remaining
- ✅ Clean import structure with no dangling references

## Validation Results
- Test Pass Rate: 1006/1006 (100%)
- Performance: Within 5% of baseline
- Code Quality: No linting or type checking errors
- Architecture: Consistent DI pattern with one documented exception

## Next Phase
Ready for Phase 4: Code Migration & Cleanup of any remaining singleton calls.
EOF

echo "Phase 3 completed successfully!"
```

**Expected Outputs**:
- No remaining singleton patterns (except ProgressManagerSingleton)
- Clean import structure
- All comments updated appropriately
- PHASE_3_COMPLETION_SUMMARY.md created
- All tests passing with good performance

**Validation Requirements**:
- [ ] No remaining singleton classes (except ProgressManagerSingleton)
- [ ] No remaining getter functions (except get_progress_manager)
- [ ] No unused imports or dangling references
- [ ] All comments updated appropriately
- [ ] All 1006 tests pass
- [ ] Performance within 5% of baseline

---

## EXPECTED DELIVERABLES

### Removal Documentation
1. **phase3_removal_log.txt** - Complete log of all removal operations
2. **PHASE_3_COMPLETION_SUMMARY.md** - Summary of completed removals and preservations
3. **docs/adr/001-retain-progress-manager-singleton.md** - ADR documenting ProgressManagerSingleton decision

### Validation Results
1. **phase3_pre_validation.txt** - Pre-phase validation results
2. **settingsmanager_removal_validation.txt** - SettingsManager removal validation
3. **consolemanager_removal_validation.txt** - ConsoleManager removal validation
4. **progressmanager_preservation_validation.txt** - ProgressManagerSingleton preservation validation
5. **getter_removal_validation.txt** - Getter function removal validation
6. **phase3_final_validation.txt** - Final phase validation results

### Backup Files (Preserved)
1. **spec_cli/config/settings.py.phase3_backup** - Pre-phase 3 settings backup
2. **spec_cli/ui/console.py.phase3_backup** - Pre-phase 3 console backup
3. **spec_cli/ui/progress_manager.py.phase3_backup** - Pre-phase 3 progress manager backup

### Modified Files
1. **spec_cli/config/settings.py** - SettingsManager removed, get_settings() removed
2. **spec_cli/ui/console.py** - ConsoleManager and caches removed, get_console() removed
3. **spec_cli/ui/progress_manager.py** - Enhanced documentation added
4. **spec_cli/config/__init__.py** - Singleton exports removed
5. **spec_cli/ui/__init__.py** - Singleton exports removed

---

## QUALITY ASSURANCE REQUIREMENTS

### Validation Gates
1. **Pre-Removal Validation**: All 1006 tests must pass before starting removals
2. **Incremental Validation**: After each singleton class removal
3. **Preservation Validation**: ProgressManagerSingleton functionality confirmed
4. **Getter Removal Validation**: Legacy getters removed, get_progress_manager preserved
5. **Final Validation**: Complete architecture consistency achieved

### Documentation Standards
1. **Removal Logging**: All removal operations must be documented with evidence
2. **ADR Creation**: ProgressManagerSingleton decision must be formally documented
3. **Architecture Documentation**: Clear explanation of final singleton exception
4. **Validation Recording**: All validation results must be captured

### Safety Requirements
1. **Incremental Approach**: Remove one component at a time with validation
2. **Backup Integrity**: All Phase 3 backup files must be verified
3. **Rollback Capability**: Must be able to restore any removed component
4. **Performance Monitoring**: Must detect any performance degradation

---

## SUCCESS VALIDATION CHECKLIST

### Phase 3 Complete When:
- [ ] All 1006 tests pass consistently
- [ ] Performance within 5% of baseline (~25s)
- [ ] SettingsManager class completely removed
- [ ] ConsoleManager class completely removed
- [ ] Module-level cache functions completely removed
- [ ] get_settings() and get_console() functions completely removed
- [ ] ProgressManagerSingleton preserved with proper documentation
- [ ] get_progress_manager() function preserved and functional
- [ ] ADR 001 created documenting architectural decision
- [ ] All __init__.py files updated appropriately
- [ ] No remaining singleton references (except ProgressManagerSingleton)
- [ ] All validation results documented
- [ ] Phase 3 completion summary created

### Critical Success Metrics:
- **Test Pass Rate**: 1006/1006 (100%)
- **Performance**: ~25s (within 5% of baseline)  
- **Singleton Count**: 1 (ProgressManagerSingleton only, documented)
- **Architecture**: 95% dependency injection with one justified exception
- **Import Cleanliness**: No dangling references to removed components
- **Documentation Quality**: Complete ADR and removal documentation

---

## EMERGENCY PROCEDURES

### If Tests Fail During Removal:
1. **STOP IMMEDIATELY** - Do not proceed with further removals
2. Identify which removal caused the failure
3. Restore from specific backup: `cp spec_cli/path/file.phase3_backup spec_cli/path/file`
4. Run validation: `./validate_migration.sh`
5. Document failure cause and seek assistance

### If Performance Degrades:
1. **STOP IMMEDIATELY** - Do not proceed
2. Check which removal caused degradation
3. Consider if removed component had unexpected performance benefit
4. Restore from backup and re-evaluate removal strategy

### If Import Errors Occur:
1. **STOP IMMEDIATELY** - Import errors indicate dependency issues
2. Check for missed references to removed components
3. Restore from backup: `./rollback_migration.sh`
4. Re-analyze dependencies before attempting removal

### If ProgressManagerSingleton Is Compromised:
1. **STOP IMMEDIATELY** - This component must remain functional
2. Restore progress_manager.py: `cp spec_cli/ui/progress_manager.py.phase3_backup spec_cli/ui/progress_manager.py`
3. Validate restoration: `./validate_migration.sh`
4. Review what accidentally affected ProgressManagerSingleton

---

## PHASE 3 COMPLETION CRITERIA

Phase 3 is complete when ALL of the following are achieved:

1. **Infrastructure Removed**: SettingsManager, ConsoleManager, and module-level caches completely removed
2. **Getters Cleaned**: get_settings() and get_console() removed, get_progress_manager() preserved
3. **Documentation Complete**: ADR 001 created, ProgressManagerSingleton properly documented
4. **Validation Passed**: All 1006 tests pass, performance maintained, no import errors
5. **Architecture Consistent**: 95% dependency injection with one documented singleton exception
6. **Cleanup Complete**: No dangling references, clean import structure

**Next Phase**: Upon successful completion, proceed to Phase 4 with the singleton infrastructure completely removed and only justified singleton patterns remaining.

---

## TECHNICAL REFERENCE

### Target Removal Locations
- **SettingsManager**: `spec_cli/config/settings.py:127-177`
- **ConsoleManager**: `spec_cli/ui/console.py:248-291`  
- **Module-level caches**: `spec_cli/ui/console.py:294-369`
- **get_settings()**: `spec_cli/config/settings.py`
- **get_console()**: `spec_cli/ui/console.py`

### Preservation Locations
- **ProgressManagerSingleton**: `spec_cli/ui/progress_manager.py:422-533` (KEEP)
- **get_progress_manager()**: `spec_cli/ui/progress_manager.py` (KEEP)

### Key Commands
- **Validation**: `./validate_migration.sh`
- **Rollback**: `./rollback_migration.sh`
- **Monitoring**: `./monitor_migration.sh`
- **Singleton Check**: `grep -r "class.*Manager\|class.*Singleton" spec_cli/`
- **Getter Check**: `grep -r "def get_.*(" spec_cli/`

### Critical Metrics
- **Test Count**: 1006 tests total
- **Performance Baseline**: ~25s for full test suite
- **Singleton Target**: Remove 2 manager classes, preserve 1 justified singleton
- **Getter Target**: Remove 2 legacy getters, preserve 1 justified getter

This comprehensive prompt ensures Phase 3 completion with all singleton infrastructure removed while preserving the architecturally justified ProgressManagerSingleton, resulting in a clean dependency injection architecture.