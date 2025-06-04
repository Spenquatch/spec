Slice 1: Extract ErrorHandler to Utils Layer

  Goal: Move ErrorHandler from core to utils to eliminate
  circular dependencies between config and core layers

  Slice Type: Infrastructure

  Helper Dependencies & Search Evidence:
  - Helper search performed: find spec_cli/utils -name
  "*.py" | grep error
  Found: spec_cli/utils/error_utils.py

  - Existing helper: spec_cli/utils/error_utils.py →
  Contains error formatting utilities
  - New helper to create: None needed (ErrorHandler will
  use existing error_utils)

  Complexity Analysis:
  - Decision points: 6/7 (if/elif chains in report method,
  try/catch in wrapper, reraise logic)
  - Helper calls: 3 (handle_os_error,
  handle_subprocess_error, create_error_context)
  - McCabe validation: Pass (6 ≤ 7, helper calls reduce
  complexity)

  Inputs → Action → Outputs:
  - Inputs: {exception: Exception, operation: str, context:
   Dict[str, Any]}
  - Action:
    a. Move ErrorHandler class from core/error_handler.py
  to utils/error_handler.py
    b. Update imports in config/loader.py and
  config/validation.py
    c. Update all other modules importing from
  core.error_handler
  - Outputs: {clean_architecture: bool} or {error_message:
  str}

  Files to Create/Modify:
  - Move: spec_cli/core/error_handler.py →
  spec_cli/utils/error_handler.py
  - Modify: spec_cli/config/loader.py (update import from
  ..utils.error_handler)
  - Modify: spec_cli/config/validation.py (update import
  from ..utils.error_handler)
  - Test: test_slice_1.py

  Test Requirements:
  - Unit Tests: Test ErrorHandler functionality with new
  import path (100% coverage)
  - Integration Test: Verify config modules can instantiate
   ErrorHandler successfully
  - Idempotent Tests: All imports resolve correctly on
  repeated test runs
  - Mocks/Fixtures: Mock error_utils functions, create test
   exception instances

  Quality Gate Validation:
  - mypy --strict (zero errors for new import paths)
  - ruff check --fix && ruff format
  - pydocstyle (Google-style docstrings)
  - pytest -v --cov=spec_cli --cov-fail-under=90

  Integration Validation:
  End-to-end test: ConfigurationLoader.load_configuration()
   handles file errors using ErrorHandler from utils

  AI Agent Execution Notes:
  - Verify all imports of ErrorHandler are updated across
  codebase
  - Ensure no remaining references to core.error_handler
  exist
  - Test that error handling behavior remains identical
  after move

  ---
  Slice 2: Decouple BatchProcessor from Core Orchestrator

  Goal: Remove dependency from
  file_processing.batch_processor on
  core.workflow_orchestrator to eliminate cross-layer
  coupling

  Slice Type: Component

  Helper Dependencies & Search Evidence:
  - Helper search performed: grep -r "workflow\|orchestrat"
   spec_cli/utils/
  No matches found for workflow orchestration helpers

  - Create helper: spec_cli/utils/workflow_utils.py →
  create_workflow_result(files: List[Path], success: bool)
  -> Dict[str, Any]

  Complexity Analysis:
  - Decision points: 4/7 (error handling in
  _handle_auto_commit, success evaluation, file
  categorization)
  - Helper calls: 2 (create_workflow_result,
  handle_os_error from existing error_utils)
  - McCabe validation: Pass (4 ≤ 7, helper calls simplify
  logic)

  Inputs → Action → Outputs:
  - Inputs: {successful_files: List[Path], auto_commit:
  bool, custom_variables: Dict[str, Any]}
  - Action:
    a. Create workflow_utils.py with workflow result
  creation helper
    b. Replace workflow_orchestrator calls in
  batch_processor with direct git operations
    c. Update auto-commit logic to use simple file
  operations instead of orchestrator
  - Outputs: {workflow_result: Dict[str, Any]} or
  {error_message: str}

  Files to Create/Modify:
  - Create: spec_cli/utils/workflow_utils.py (workflow
  result helpers)
  - Modify: spec_cli/file_processing/batch_processor.py
  (remove orchestrator import, simplify auto-commit)
  - Test: test_slice_2.py

  Test Requirements:
  - Unit Tests: Test BatchProcessor without workflow
  orchestrator dependency (100% coverage)
  - Integration Test: Verify auto-commit functionality
  works with simplified approach
  - Idempotent Tests: Batch processing produces consistent
  results on repeated runs
  - Mocks/Fixtures: Mock git operations, create test file
  processing scenarios

  Quality Gate Validation:
  - mypy --strict (verify no missing imports after
  orchestrator removal)
  - ruff check --fix && ruff format
  - pydocstyle (Google-style docstrings)
  - pytest -v --cov=spec_cli --cov-fail-under=90

  Integration Validation:
  End-to-end test: BatchFileProcessor.process_files() with
  auto_commit=True creates commits without using workflow
  orchestrator

  AI Agent Execution Notes:
  - Ensure auto-commit functionality is preserved but
  simplified
  - Remove all imports of workflow_orchestrator from
  batch_processor
  - Test that batch processing results remain consistent

  ---
  Slice 3: Validate Architecture Dependencies

  Goal: Establish and validate clean architecture
  dependency hierarchy: Utils → Config → Core → CLI

  Slice Type: Integration

  Helper Dependencies & Search Evidence:
  - Helper search performed: grep -r "import.*\.\."
  spec_cli/ | grep -v test
  Found multiple cross-layer imports to validate

  - Existing helper: spec_cli/utils/error_utils.py → Use
  for consistent dependency validation error reporting
  - New helper to create:
  spec_cli/utils/dependency_validator.py →
  validate_import_hierarchy() -> List[str]

  Complexity Analysis:
  - Decision points: 5/7 (layer validation logic, import
  parsing, error categorization)
  - Helper calls: 2 (create_error_context, dependency
  validation helper)
  - McCabe validation: Pass (5 ≤ 7 with helper abstraction)

  Inputs → Action → Outputs:
  - Inputs: {codebase_path: Path, expected_hierarchy:
  List[str]}
  - Action:
    a. Create dependency_validator.py to check import
  hierarchies
    b. Scan all modules for import violations
    c. Generate report of architecture compliance

  - Outputs: {validation_report: Dict[str, Any]} or
  {violations: List[str]}

  Files to Create/Modify:
  - Create: spec_cli/utils/dependency_validator.py
  (architecture validation)
  - Test: test_slice_3.py

  Test Requirements:
  - Unit Tests: Test dependency validation logic with
  various import scenarios (100% coverage)
  - Integration Test: Run validation against current
  codebase after fixes
  - Idempotent Tests: Validation results are consistent
  across multiple runs
  - Mocks/Fixtures: Mock file system for controlled import
  scenarios

  Quality Gate Validation:
  - mypy --strict (clean type checking for validation
  logic)
  - ruff check --fix && ruff format
  - pydocstyle (Google-style docstrings)
  - pytest -v --cov=spec_cli --cov-fail-under=90

  Integration Validation:
  End-to-end test:
  dependency_validator.validate_import_hierarchy() reports
  zero violations after architecture fixes

  AI Agent Execution Notes:
  - Focus on detecting remaining circular dependencies
  - Provide clear reporting of architecture compliance
  - Enable ongoing validation of dependency rules
