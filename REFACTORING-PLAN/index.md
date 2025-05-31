# Codebase Refactoring Plan

## Overview

This plan refactors the current monolithic `__main__.py` (1340+ lines) into a modular, maintainable, and extensible architecture following industry best practices for AI/ML/CLI pipelines. The refactoring breaks down into 13 focused slices across 5 phases, with no backward compatibility requirements.

## Goals

1. **Modular Architecture**: Clean separation of concerns with single responsibility principle
2. **Testable Design**: Each component easily unit tested with proper dependency injection
3. **Extensible Foundation**: Architecture supports future AI integration and Git hooks
4. **Performance**: Maintain or improve current performance characteristics
5. **Type Safety**: Full type hints and mypy compliance throughout

## Technology Stack

### Core Libraries (Existing)
- **pathlib**: File system operations
- **subprocess**: Git command execution  
- **yaml**: Configuration file parsing
- **pydantic**: Data validation and settings

### New Libraries for Architecture
- **abc**: Abstract base classes for interfaces
- **typing**: Enhanced type hints and protocols
- **dataclasses**: Data structures and configuration
- **functools**: Decorators and utilities
- **contextlib**: Context managers for resource management

### Enhanced User Experience
- **rich**: Terminal styling, colors, and progress bars (replaces emoji usage)
- **click**: Enhanced CLI with better error handling (optional upgrade)

## Phase Breakdown

### [PHASE-1-foundation](./PHASE-1-foundation/) - Core Infrastructure
**Goal**: Establish foundational infrastructure with proper exception handling, logging, and configuration management.

**Slices:**
- [slice-1-exceptions.md](./PHASE-1-foundation/slice-1-exceptions.md) - Custom exception hierarchy
- [slice-2-logging.md](./PHASE-1-foundation/slice-2-logging.md) - Debug logging and timing infrastructure  
- [slice-3-configuration.md](./PHASE-1-foundation/slice-3-configuration.md) - Settings management with terminal styling

**Prerequisites**: None (foundation layer)

### [PHASE-2-filesystem](./PHASE-2-filesystem/) - File System Operations
**Goal**: Extract and organize all file system operations into clean, testable abstractions.

**Slices:**
- [slice-4-path-resolution.md](./PHASE-2-filesystem/slice-4-path-resolution.md) - Path validation and resolution
- [slice-5-file-analysis.md](./PHASE-2-filesystem/slice-5-file-analysis.md) - File type detection and analysis
- [slice-6-directory-management.md](./PHASE-2-filesystem/slice-6-directory-management.md) - Directory operations and ignore patterns

**Prerequisites**: PHASE-1 complete (exceptions, logging, configuration)

### [PHASE-3-templates](./PHASE-3-templates/) - Template System  
**Goal**: Extract template system into shared module for cmd_gen and future git hooks.

**Slices:**
- [slice-7-template-config.md](./PHASE-3-templates/slice-7-template-config.md) - Template configuration and validation
- [slice-8-template-generation.md](./PHASE-3-templates/slice-8-template-generation.md) - Content generation and substitution

**Prerequisites**: PHASE-1 complete, PHASE-2 file operations available

### [PHASE-4-git-core](./PHASE-4-git-core/) - Git and Core Logic
**Goal**: Extract Git operations and core business logic into organized, testable services.

**Slices:**
- [slice-9-git-operations.md](./PHASE-4-git-core/slice-9-git-operations.md) - Git repository interface and operations
- [slice-10-spec-repository.md](./PHASE-4-git-core/slice-10-spec-repository.md) - Main spec operations orchestration  
- [slice-11-file-processing.md](./PHASE-4-git-core/slice-11-file-processing.md) - File processing and conflict resolution

**Prerequisites**: PHASE-1,2,3 complete (all foundational systems available)

### [PHASE-5-interface](./PHASE-5-interface/) - User Interface
**Goal**: Create clean CLI layer with Rich terminal UI and comprehensive error handling.

**Slices:**
- [slice-12-rich-ui.md](./PHASE-5-interface/slice-12-rich-ui.md) - Rich terminal UI system with error handling  
- [slice-13-cli-commands.md](./PHASE-5-interface/slice-13-cli-commands.md) - CLI commands with enhanced error messages

**Prerequisites**: All previous phases complete

## Target Architecture

```
spec_cli/
├── __init__.py              # Public API exports
├── __main__.py              # Thin entry point (~50 lines)
├── cli/                     # Command-line interface layer
├── core/                    # Core business logic  
├── git/                     # Git operations abstraction
├── templates/               # Shared template system
├── file_system/             # File system operations
├── config/                  # Configuration management
├── ui/                      # Rich terminal UI components
├── exceptions.py            # Custom exception hierarchy
├── logging/                 # Logging and debugging
└── utils/                   # Shared utilities
```

## Quality Standards

### Test Coverage Requirements
- **Total Tests Planned**: 180+ comprehensive tests across all slices
- **Coverage Requirement**: Minimum 80% per slice, 85% overall
- **Test Types**: Unit tests with comprehensive edge case coverage

### Performance Requirements  
- Startup time under 200ms (vs current ~150ms)
- Memory usage under 50MB for typical operations
- Directory processing scales linearly with file count
- Module import time minimized through lazy loading

### Architecture Quality
- All modules follow single responsibility principle
- Clean interfaces between all layers with dependency injection
- Comprehensive error handling with user-friendly messages
- Type hints throughout with mypy compliance
- Rich terminal UI replaces all emoji usage

## Success Criteria

- [ ] All 13 slices implemented with 80%+ test coverage
- [ ] Performance meets or exceeds current implementation  
- [ ] Clean architecture enables easy AI and Git hook integration
- [ ] Code maintainability significantly improved
- [ ] Rich terminal UI provides excellent user experience
- [ ] Comprehensive error handling with actionable guidance
- [ ] All existing functionality preserved (CLI commands work identically)

## Execution Notes

- **No Backward Compatibility**: Simplifies refactoring significantly
- **Maintenance Integration**: Terminal styling, error handling, and validation integrated into refactoring
- **Git Command Corrections**: Handled separately after refactoring completion
- **Atomic Slices**: Each slice leaves codebase in working state
- **Progressive Enhancement**: Each phase builds on previous phases