Vertical Slices for Refactoring Large Classes

  Phase Overview

  Decompose SpecWorkflowOrchestrator (641 lines) and BatchProcessor (488
  lines) into focused, single-responsibility components while maintaining
  backward compatibility and test coverage.

  ---
  Slice 1a: Extract WorkflowValidator from SpecWorkflowOrchestrator

  Goal: Extract validation logic into a dedicated WorkflowValidator class

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: ripgrep 'def validate' spec_cli/utils | head
  -n 5
  Found: validate_env_vars, validate_git_command in utils

  - [Existing helper: spec_cli/utils/error_handler.py] → ErrorHandler for
  consistent error wrapping
  - [Existing helper: spec_cli/utils/path_utils.py] → safe_relative_to,
  ensure_path_permissions
  - [New helper to create: spec_cli/core/validators/workflow_validator.py]
  → WorkflowValidator class

  Complexity Analysis:
  - Decision points: 4/7 (if checks for repository state, file existence,
  validation issues)
  - Helper calls: 3 (ErrorHandler.wrap, ensure_path_permissions,
  state_checker methods)
  - McCabe validation: Pass

  Inputs → Action → Outputs:
  - Inputs: {file_path: Path, operation_type: str, settings: SpecSettings}
  - Action:
    a. Check repository health using state_checker
    b. Validate file exists and is readable
    c. Check pre-operation state for the operation type
    d. Return validation result with any issues
  - Outputs: {valid: bool, issues: list[str]} or raises SpecWorkflowError

  Files to Create/Modify:
  - spec_cli/core/validators/workflow_validator.py (new validator class)
  - spec_cli/core/workflow_orchestrator.py (refactor to use validator)
  - tests/unit/core/validators/test_workflow_validator.py (comprehensive
  tests)

  Test Requirements:
  - Unit Tests: Test valid file paths, missing files, repository health
  issues, various operation types
  - Integration Test: Validate complete workflow validation scenario
  - Idempotent Tests: All tests must pass consistently on repeated runs
  - Mocks/Fixtures: Mock RepositoryStateChecker, file system operations

  Quality Gate Validation:
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pytest tests/unit/core/validators/ -v
  --cov=spec_cli.core.validators --cov-fail-under=100

  Integration Validation:
  Generate spec for a file and verify validator is called correctly in the
  workflow

  AI Agent Execution Notes:
  - Create validators subdirectory under core if it doesn't exist
  - Ensure WorkflowValidator uses existing error handling utilities
  - Update SpecWorkflowOrchestrator imports and method calls

  ---
  Slice 1b: Extract WorkflowExecutor from SpecWorkflowOrchestrator

  Goal: Extract workflow execution logic into a dedicated WorkflowExecutor
  class

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: ripgrep 'def.*execute' spec_cli/utils | head
  -n 5
  No execution helpers found in utils

  - [Existing helper: spec_cli/utils/error_handler.py] → ErrorHandler for
  error context
  - [Existing helper: spec_cli/utils/workflow_utils.py] →
  create_workflow_result
  - [New helper to create: spec_cli/core/executors/workflow_executor.py] →
  WorkflowExecutor class

  Complexity Analysis:
  - Decision points: 5/7 (backup check, auto_commit check, error handling
  branches)
  - Helper calls: 2 (create_workflow_result, ErrorHandler methods)
  - McCabe validation: Pass

  Inputs → Action → Outputs:
  - Inputs: {workflow: WorkflowState, file_path: Path, options: dict[str,
  Any]}
  - Action:
    a. Execute generation stage using content_generator
    b. Conditionally execute commit stage if auto_commit
    c. Execute cleanup stage
    d. Return execution result with generated files
  - Outputs: {success: bool, generated_files: dict[str, Path], commit_info:
   dict | None}

  Files to Create/Modify:
  - spec_cli/core/executors/workflow_executor.py (new executor class)
  - spec_cli/core/workflow_orchestrator.py (refactor to use executor)
  - tests/unit/core/executors/test_workflow_executor.py (comprehensive
  tests)

  Test Requirements:
  - Unit Tests: Test successful execution, failed generation, commit
  failures, cleanup
  - Integration Test: Execute complete workflow with all stages
  - Idempotent Tests: Ensure repeated executions produce same results
  - Mocks/Fixtures: Mock ContentGenerator, CommitManager, WorkflowState

  Quality Gate Validation:
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pytest tests/unit/core/executors/ -v
  --cov=spec_cli.core.executors --cov-fail-under=100

  Integration Validation:
  Execute a full workflow and verify all stages complete successfully

  AI Agent Execution Notes:
  - Create executors subdirectory under core if it doesn't exist
  - Ensure proper dependency injection for content_generator and
  commit_manager
  - Maintain workflow state updates throughout execution

  ---
  Slice 1c: Extract WorkflowBackupManager from SpecWorkflowOrchestrator

  Goal: Extract backup and rollback logic into a dedicated manager class

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: ripgrep 'def.*backup' spec_cli/utils | head -n
   5
  No backup helpers found in utils

  - [Existing helper: spec_cli/utils/error_utils.py] → create_error_context
  - [New helper to create: spec_cli/core/managers/backup_manager.py] →
  WorkflowBackupManager class

  Complexity Analysis:
  - Decision points: 3/7 (backup creation check, rollback condition, error
  handling)
  - Helper calls: 1 (create_error_context)
  - McCabe validation: Pass

  Inputs → Action → Outputs:
  - Inputs: {workflow_id: str, commit_manager: SpecCommitManager}
  - Action:
    a. Create backup tag with workflow ID
    b. Store backup info in workflow metadata
    c. Provide rollback capability to backup point
  - Outputs: {backup_tag: str, commit_hash: str} or rollback result

  Files to Create/Modify:
  - spec_cli/core/managers/backup_manager.py (new backup manager class)
  - spec_cli/core/workflow_orchestrator.py (refactor to use backup manager)
  - tests/unit/core/managers/test_backup_manager.py (comprehensive tests)

  Test Requirements:
  - Unit Tests: Test backup creation, tag naming, rollback success/failure
  - Integration Test: Create backup and perform rollback in workflow
  context
  - Idempotent Tests: Ensure backup operations are repeatable
  - Mocks/Fixtures: Mock SpecCommitManager, git operations

  Quality Gate Validation:
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pytest tests/unit/core/managers/ -v
  --cov=spec_cli.core.managers --cov-fail-under=100

  Integration Validation:
  Create a backup, make changes, then rollback and verify restoration

  AI Agent Execution Notes:
  - Create managers subdirectory under core if it doesn't exist
  - Ensure atomic backup operations with proper error handling
  - Store backup metadata for workflow tracking

  ---
  Slice 2a: Extract BatchProgressTracker from BatchFileProcessor

  Goal: Extract progress tracking logic into a dedicated tracker class

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: ripgrep 'class.*Progress' spec_cli | head -n 5
  Found: ProgressReporter, ProgressEvent in
  file_processing/progress_events.py

  - [Existing helper: spec_cli/file_processing/progress_events.py] →
  ProgressReporter, ProgressEvent
  - [New helper to create:
  spec_cli/file_processing/trackers/batch_progress_tracker.py] →
  BatchProgressTracker

  Complexity Analysis:
  - Decision points: 4/7 (progress callback checks, event type selection)
  - Helper calls: 3 (progress_reporter methods)
  - McCabe validation: Pass

  Inputs → Action → Outputs:
  - Inputs: {total_files: int, progress_reporter: ProgressReporter}
  - Action:
    a. Initialize tracking state for batch operation
    b. Track file processing progress with events
    c. Emit appropriate progress events
    d. Provide summary statistics
  - Outputs: Progress events emitted, summary statistics available

  Files to Create/Modify:
  - spec_cli/file_processing/trackers/batch_progress_tracker.py (new
  tracker class)
  - spec_cli/file_processing/batch_processor.py (refactor to use tracker)
  - tests/unit/file_processing/trackers/test_batch_progress_tracker.py
  (tests)

  Test Requirements:
  - Unit Tests: Test progress initialization, event emission, summary
  generation
  - Integration Test: Track complete batch processing with multiple files
  - Idempotent Tests: Ensure consistent tracking across runs
  - Mocks/Fixtures: Mock ProgressReporter, file processing events

  Quality Gate Validation:
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pytest tests/unit/file_processing/trackers/ -v
  --cov=spec_cli.file_processing.trackers --cov-fail-under=100

  Integration Validation:
  Process a batch of files and verify all progress events are emitted
  correctly

  AI Agent Execution Notes:
  - Create trackers subdirectory under file_processing if needed
  - Integrate with existing ProgressReporter infrastructure
  - Maintain backward compatibility with progress callbacks

  ---
  Slice 2b: Extract BatchResultAggregator from BatchFileProcessor

  Goal: Extract result aggregation and summary logic into dedicated class

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: ripgrep 'def.*summary' spec_cli/utils | head
  -n 5
  No summary helpers found in utils

  - [Existing helper: spec_cli/utils/workflow_utils.py] →
  create_workflow_result
  - [New helper to create:
  spec_cli/file_processing/aggregators/result_aggregator.py] →
  BatchResultAggregator

  Complexity Analysis:
  - Decision points: 6/7 (categorizing results, analyzing conflicts, error
  types)
  - Helper calls: 1 (create_workflow_result)
  - McCabe validation: Pass

  Inputs → Action → Outputs:
  - Inputs: {file_results: dict[str, FileProcessingResult]}
  - Action:
    a. Categorize files into successful/failed/skipped
    b. Analyze conflict patterns and resolutions
    c. Classify error types
    d. Generate comprehensive summary
  - Outputs: {summary: dict[str, Any], statistics: dict[str, float]}

  Files to Create/Modify:
  - spec_cli/file_processing/aggregators/result_aggregator.py (new
  aggregator)
  - spec_cli/file_processing/batch_processor.py (refactor to use
  aggregator)
  - tests/unit/file_processing/aggregators/test_result_aggregator.py
  (tests)

  Test Requirements:
  - Unit Tests: Test categorization, conflict analysis, error
  classification
  - Integration Test: Aggregate results from multi-file batch processing
  - Idempotent Tests: Ensure consistent aggregation results
  - Mocks/Fixtures: Create sample FileProcessingResult objects

  Quality Gate Validation:
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pytest tests/unit/file_processing/aggregators/ -v
  --cov=spec_cli.file_processing.aggregators --cov-fail-under=100

  Integration Validation:
  Process files with various outcomes and verify summary accuracy

  AI Agent Execution Notes:
  - Create aggregators subdirectory under file_processing if needed
  - Design flexible aggregation for future metric additions
  - Ensure type safety with result dictionaries

  ---
  Slice 3: Integration and Cleanup

  Goal: Integrate refactored components and clean up original classes

  Slice Type: Integration

  Helper Dependencies & Search Evidence:
  - All components from previous slices
  - [Existing helper: spec_cli/utils/singleton.py] → For potential shared
  state

  Complexity Analysis:
  - Decision points: 2/7 (component initialization, method delegation)
  - Helper calls: 5+ (all new component methods)
  - McCabe validation: Pass (simplified orchestrator methods)

  Inputs → Action → Outputs:
  - Inputs: Same as original classes
  - Action:
    a. Update constructors to initialize new components
    b. Delegate methods to appropriate components
    c. Remove extracted code from original classes
    d. Update all imports and references
  - Outputs: Same public API, cleaner implementation

  Files to Create/Modify:
  - spec_cli/core/workflow_orchestrator.py (final refactored version)
  - spec_cli/file_processing/batch_processor.py (final refactored version)
  - Update all files that import these classes

  Test Requirements:
  - Unit Tests: Ensure all existing tests still pass
  - Integration Test: Full end-to-end workflows work as before
  - Idempotent Tests: No behavior changes from refactoring
  - Mocks/Fixtures: Update mocks to work with new structure

  Quality Gate Validation:
  - poetry run pytest tests/unit/ -v --cov=spec_cli --cov-fail-under=90
  - poetry run mypy --strict
  - poetry run ruff check --fix && poetry run ruff format
  - poetry run pre-commit run --all-files

  Integration Validation:
  Run complete spec generation workflow and batch processing to ensure no
  regressions

  AI Agent Execution Notes:
  - Ensure backward compatibility - no API changes
  - Update documentation strings to reflect new architecture
  - Consider adding deprecation warnings if changing internal APIs
  ⎿  ☒ Analyze SpecWorkflowOrchestrator to identify decomposition slices
     ☒ Analyze BatchProcessor to identify decomposition slices
     ☒ Generate vertical slices for refactoring both classes

⏺ I've generated 6 vertical slices to refactor the large classes:

  1. Slice 1a-1c: Decompose SpecWorkflowOrchestrator into:
    - WorkflowValidator (validation logic)
    - WorkflowExecutor (execution stages)
    - WorkflowBackupManager (backup/rollback)
  2. Slice 2a-2b: Decompose BatchFileProcessor into:
    - BatchProgressTracker (progress tracking)
    - BatchResultAggregator (result aggregation)
  3. Slice 3: Integration slice to wire everything together

  Each slice follows the P0-ABSOLUTE rules:
  - Reuses existing helpers from /src/utils/
  - Keeps complexity under 7 McCabe points
  - Delivers independently testable components
  - Maintains 100% test coverage for new code
  - Uses Poetry-only dependency management
