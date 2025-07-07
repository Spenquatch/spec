**Slice 2.1: Test Failure Analysis and Categorization**

**Goal**: Systematically analyze all 263 test failures and categorize them by type and priority to create actionable remediation plan

**Slice Type**: Component

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
rg 'def.*categorize' spec_cli/utils | head -n 5
# No matches found for categorize

rg 'def.*analyze.*test' spec_cli/utils | head -n 5
# Found: spec_cli/utils/test_analysis.py

rg 'def.*failure' spec_cli/utils | head -n 5
# No matches found for failure
```

- Existing helper: `spec_cli/utils/test_analysis.py` → Test analysis utilities
- Existing helper: `spec_cli/utils/test_migration_utils.py` → Test migration utilities
- New helper to create: `spec_cli/utils/test_helpers/test_failure_categorizer.py` → `categorize_test_failure(failure_info: Dict) -> TestFailureCategory`

**Complexity Analysis:**

- Decision points: 5/7 (categorization logic: if/elif chains for failure types)
- Helper calls: 3 (existing test analysis helpers)
- McCabe validation: Pass - within limit using existing helpers

**Inputs → Action → Outputs:**

- **Inputs**: {test_results: Dict[str, Any], failure_logs: List[str]}
- **Action**:
  1. Extract failure information using existing test_analysis helpers
  2. Categorize failures by type (rich_compatibility, missing_function, migration_artifact, real_issue)
  3. Assign priority levels based on failure impact and type
- **Outputs**: {categorization_report: Dict[str, List[TestFailureCategory]], summary_stats: Dict[str, int]}

**Files to Create/Modify:**

- `slice_2_1_test_categorization.py` (main analysis logic)
- `spec_cli/utils/test_helpers/test_failure_categorizer.py` (categorization helper)
- `test_slice_2_1.py` (comprehensive tests)

**Test Requirements:**

- **Unit Tests**: Test categorization logic with sample failure data (100% coverage)
- **Integration Test**: End-to-end analysis of real test failure data
- **Functionality Script**: Create `functionality_script_slice_2_1_test_analysis.sh` that:
  - Runs actual pytest to generate test failures
  - Executes categorization analysis on real test output
  - Validates categorization accuracy against known failure types
  - Uses Docker containers for isolated test execution environment
  - Verifies all 263 failures are properly categorized
  - Tests analysis performance within 2-hour requirement
- **Idempotent Tests**: All tests pass consistently on repeated runs
- **Mocks/Fixtures**: Test failure data fixtures, categorization result templates

**Functionality Script Requirements:**
Create `functionality_script_slice_2_1_test_analysis.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual test_analysis implementation - NO mock objects
- **MANDATORY**: Exercises real categorization logic with actual test failure data
- **MANDATORY**: Validates actual categorization output and statistics
- **MANDATORY**: Captures and displays actual analysis results
- **MANDATORY**: Shows "Expected:" and "Actual:" for each categorization check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for pytest execution isolation
- **MANDATORY**: Includes Docker health checks before running analysis
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated test failure data or categorization results
- Tests actual categorization algorithm against real pytest output
- Validates categorization accuracy and performance requirements
- Includes Docker container startup and teardown for test isolation
- Returns proper exit codes and comprehensive result counting

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_2_1_test_categorization.py
poetry run ruff check --fix slice_2_1_test_categorization.py
poetry run ruff format slice_2_1_test_categorization.py
poetry run pydocstyle slice_2_1_test_categorization.py
poetry run bandit -r slice_2_1_test_categorization.py
poetry run pytest test_slice_2_1.py -v --cov=slice_2_1_test_categorization --cov-fail-under=100
```

**Integration Validation:**
Execute analysis on subset of actual test failures, verify categorization produces actionable results with clear priority assignments

**AI Agent Execution Notes:**
Use existing test_analysis.py helpers to reduce complexity. Focus on categorization accuracy over performance optimization. Ensure all 263 failures are addressed in categorization framework.