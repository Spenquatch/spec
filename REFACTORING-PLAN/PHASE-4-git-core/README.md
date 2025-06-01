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
2. **slice-10a-repo-init.md** - Second (repository initialization and state management)
3. **slice-10b-commit-wrappers.md** - Third (Git commit operations using repo state)
4. **slice-10c-spec-workflow.md** - Fourth (workflow orchestration using Git operations)
5. **slice-11a-change-detection.md** - Fifth (file change detection and caching)
6. **slice-11b-conflict-resolver.md** - Sixth (conflict resolution using change detection)
7. **slice-11c-batch-processor.md** - Seventh (batch processing using conflict resolution)

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
- [slice-10a-repo-init.md](./slice-10a-repo-init.md) - Repository initialization and state management
- [slice-10b-commit-wrappers.md](./slice-10b-commit-wrappers.md) - Git commit wrappers and operations
- [slice-10c-spec-workflow.md](./slice-10c-spec-workflow.md) - High-level spec workflow orchestration
- [slice-11a-change-detection.md](./slice-11a-change-detection.md) - File change detection and caching
- [slice-11b-conflict-resolver.md](./slice-11b-conflict-resolver.md) - Conflict resolution strategies and merge helpers
- [slice-11c-batch-processor.md](./slice-11c-batch-processor.md) - Batch processing and progress events
- [slice-10-spec-repository.md](./slice-10-spec-repository.md) - **[DEPRECATED]** Combined slice split into 10A/10B/10C
- [slice-11-file-processing.md](./slice-11-file-processing.md) - **[DEPRECATED]** Combined slice split into 11A/11B/11C

## Next Phase

Once complete, enables PHASE-5 (user interface) which will create the CLI layer that uses these core services to provide the user-facing commands.