# PHASE-4: Git and Core Logic

## Overview

Extracts Git operations and core business logic into organized, testable services. This phase creates the main orchestration layer that coordinates file processing, Git operations, and documentation generation using all the foundational systems built in previous phases.

## Prerequisites

- **PHASE-1 complete**: Exception hierarchy, logging, and configuration systems
- **PHASE-2 complete**: File system operations for path handling and file analysis
- **PHASE-3 complete**: Template system for documentation generation
- **Required modules**: All foundation, file system, and template modules

## Slice Execution Order

Execute slices in the following order due to dependencies:

1. **slice-9-git-operations.md** - Must be first (provides Git interface for other services)
2. **slice-10-spec-repository.md** - Second (orchestrates operations, depends on Git interface)
3. **slice-11-file-processing.md** - Third (depends on spec repository and all previous systems)

## Shared Concepts

- **Git Abstraction**: Clean interface for all Git operations with isolated repository handling
- **Service Orchestration**: Main spec repository service coordinates all operations
- **File Processing Pipeline**: Systematic processing with conflict resolution and batch operations
- **Business Logic Separation**: Core logic separated from CLI and presentation concerns

## Phase Completion Criteria

- [ ] Git operations abstracted with proper error handling and path conversion
- [ ] Spec repository service orchestrates all main operations
- [ ] File processing with conflict resolution and batch support
- [ ] All core business logic extracted from monolithic file
- [ ] Services designed for easy testing and dependency injection
- [ ] All modules have 80%+ test coverage including Git error scenarios
- [ ] Type hints throughout with mypy compliance

## Slice Files

- [slice-9-git-operations.md](./slice-9-git-operations.md) - Git repository interface and operations
- [slice-10-spec-repository.md](./slice-10-spec-repository.md) - Main spec operations orchestration
- [slice-11-file-processing.md](./slice-11-file-processing.md) - File processing with conflict resolution

## Next Phase

Once complete, enables PHASE-5 (user interface) which will create the CLI layer that uses these core services to provide the user-facing commands.