# Command Migration Requirements: CLI Dependency Injection

**Generated**: 2025-07-05  
**Analysis Source**: P2.3a Command Structure Analysis  
**Target Slices**: P2.3b (init), P2.3c (status)

## Executive Summary

Analysis of 31 CLI files revealed 42 singleton usage patterns across 10 commands. Primary migration targets are direct instantiation of `SpecGitRepository` and factory function calls like `get_console()` and `get_spec_repository()`.

## CLI Structure Analysis

### Command Overview
- **Total files analyzed**: 31
- **Commands found**: 10 
- **Click patterns**: 10 (command decorators)
- **Singleton usage patterns**: 42 instances

### Core Commands Identified
1. `init_command` - spec_cli/cli/commands/init.py:16
2. `status_command` - spec_cli/cli/commands/status.py:26  
3. `add_command` - spec_cli/cli/commands/add.py:14
4. `gen_command` - spec_cli/cli/commands/gen.py:31
5. `show_command` - spec_cli/cli/commands/show.py:23

## Singleton Usage Analysis

### Critical Patterns Requiring Migration

#### 1. SpecGitRepository Direct Instantiation
**Pattern**: `SpecGitRepository()`  
**Locations**:
- spec_cli/cli/options.py:138
- spec_cli/cli/utils.py:157  
- spec_cli/cli/utils.py:218
- spec_cli/cli/commands/init.py:24

**Migration Priority**: HIGH - Core repository access

#### 2. Console Factory Functions
**Pattern**: `get_console()`  
**Locations**:
- spec_cli/cli/app.py:103
- spec_cli/cli/commands/show.py:42, 90, 138
- spec_cli/cli/commands/gen_command.py:56
- spec_cli/cli/commands/status.py:34

**Migration Priority**: HIGH - User interface dependency

#### 3. Repository Factory Functions  
**Pattern**: `get_spec_repository()`
**Locations**:
- spec_cli/cli/commands/show.py:54
- spec_cli/cli/commands/status.py:38
- spec_cli/cli/commands/add_command.py:45

**Migration Priority**: HIGH - Repository operations

#### 4. Progress Manager Factory
**Pattern**: `get_progress_manager()`  
**Locations**:
- spec_cli/cli/utils.py:180

**Migration Priority**: MEDIUM - Progress tracking

## Migration Requirements by Command

### init_command (P2.3b Priority)

**Current Singleton Usage**:
```python
# Line 24: Direct instantiation
repo = SpecGitRepository()
```

**Required Dependencies**:
- `SpecGitRepository` instance
- `debug_logger` (already injected via decorators)  
- `echo_status` function (utility dependency)

**Migration Strategy**:
1. Add `repo: SpecGitRepository` parameter to function signature
2. Update `@spec_command()` decorator to provide repository instance  
3. Remove direct instantiation line 24
4. Verify initialization logic works with injected instance

**Test Scenarios**:
- Repository creation and initialization
- Force reinitialize scenario
- Error handling for initialization failures

### status_command (P2.3c Priority)

**Current Singleton Usage**:
```python
# Line 34: Factory function call
console = get_console()
# Line 38: Factory function call  
repo = get_spec_repository()
```

**Required Dependencies**:
- `Console` instance for Rich UI output
- `SpecGitRepository` instance for status queries
- Helper functions: `_get_repository_status`, `_get_git_status_data`

**Migration Strategy**:
1. Add `console: Console` and `repo: SpecGitRepository` to function signature
2. Update `@spec_command()` decorator to provide both instances
3. Remove factory function calls lines 34, 38
4. Verify all status display functions work with injected dependencies

**Test Scenarios**:
- Repository status display
- Health check mode
- Git status integration  
- Processing summary display

## Context Injection Implementation

### Decorator Enhancement Required

The `@spec_command()` decorator needs enhancement to provide dependency injection:

```python
# Current: spec_cli/cli/options.py
@spec_command()
def command_function(debug: bool, verbose: bool): pass

# Target: Enhanced with DI
@spec_command()  
def command_function(
    debug: bool, 
    verbose: bool,
    console: Console,
    repository: SpecGitRepository
): pass
```

### Factory Pattern Migration

Factory functions requiring replacement:
- `get_spec_repository()` -> injected `repository` parameter
- `get_console()` -> injected `console` parameter  
- `get_progress_manager()` -> injected `progress_manager` parameter (if needed)

## Testing Strategy

### Unit Test Requirements
1. **Command Analysis Testing**: Verify analysis correctly identifies patterns
2. **Injection Mock Testing**: Test commands with mocked dependencies  
3. **Integration Testing**: Verify end-to-end functionality post-migration

### Migration Validation
1. **Functionality Preservation**: All existing features work identically
2. **Error Handling**: Error scenarios work with injected dependencies
3. **Performance**: No degradation in command execution time

## Risk Assessment

### High Risk Areas
- **Repository Operations**: Core functionality depends on SpecGitRepository
- **User Interface**: Console output must maintain formatting
- **Error Handling**: Exception paths must work with DI

### Medium Risk Areas  
- **Progress Tracking**: Progress manager integration
- **Debug Logging**: Logging context preservation

### Low Risk Areas
- **Utility Functions**: Most utilities are stateless
- **File Operations**: Path handling functions unaffected

## Implementation Order

### Phase 1: Foundation (P2.3b - init command)
1. Enhance `@spec_command()` decorator for DI
2. Migrate `init_command` as proof of concept
3. Verify initialization workflows  

### Phase 2: Status Operations (P2.3c - status command)  
1. Extend DI support for Console injection
2. Migrate `status_command` with dual dependencies
3. Verify status display functionality

### Phase 3: Remaining Commands (Future slices)
1. Apply patterns to remaining 8 commands
2. Complete singleton elimination
3. Full test suite validation

## Success Criteria

### P2.3b Success Criteria
- `init_command` uses injected `SpecGitRepository`
- No direct instantiation in init command  
- All initialization tests pass
- Error handling preserved

### P2.3c Success Criteria  
- `status_command` uses injected `Console` and `SpecGitRepository`
- No factory function calls in status command
- Status display functionality preserved
- Integration tests pass

### Overall Migration Success
- Zero direct singleton instantiation in target commands
- All existing functionality preserved  
- Test coverage maintained at 90%+
- Performance baseline maintained