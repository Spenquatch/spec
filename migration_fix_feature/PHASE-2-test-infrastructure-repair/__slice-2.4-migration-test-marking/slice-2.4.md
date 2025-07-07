**Slice 2.4: Migration Test Marking and Core Test Validation**

**Goal**: Mark migration-specific tests with appropriate decorators and validate core functionality test reliability achieves <5% failure rate

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
rg 'def.*mark.*test' spec_cli/utils | head -n 5
# No matches found for mark test

rg 'def.*decorator' spec_cli/utils | head -n 5
# Found: spec_cli/utils/decorator_utils.py
# Found: spec_cli/utils/decorator_analysis.py

rg 'def.*validate.*test' spec_cli/utils | head -n 5
# No matches found for validate test
```

- Existing helper: `spec_cli/utils/decorator_utils.py` → Decorator utilities
- Existing helper: `spec_cli/utils/test_migration_utils.py` → Test migration utilities
- Existing helper: `spec_cli/utils/test_analysis.py` → Test analysis utilities
- New helper to create: `spec_cli/utils/test_helpers/migration_test_marker.py` → `mark_migration_test(test_path: str, reason: str) -> bool`

**Complexity Analysis:**

- Decision points: 5/7 (test type detection, marking strategy selection, validation logic)
- Helper calls: 3 (existing decorator and test analysis helpers)
- McCabe validation: Pass - within limit using existing helpers

**Inputs → Action → Outputs:**

- **Inputs**: {test_files: List[str], categorization_results: Dict[str, TestFailureCategory], core_test_definitions: List[str]}
- **Action**:
  1. Identify migration-specific tests using test analysis helpers
  2. Apply appropriate pytest decorators using decorator utilities
  3. Validate core functionality test reliability meets <5% failure rate
- **Outputs**: {marked_tests: Dict[str, str], core_test_validation: Dict[str, float], overall_reliability_score: float}

**Files to Create/Modify:**

- `slice_2_4_test_marking.py` (test marking implementation)
- `spec_cli/utils/test_helpers/migration_test_marker.py` (marking helper)
- `test_slice_2_4.py` (test marking validation tests)

**Test Requirements:**

- **Unit Tests**: Test marking logic and core test validation (100% coverage)
- **Integration Test**: End-to-end test suite execution with proper marking and reliability validation
- **Functionality Script**: Create `functionality_script_slice_2_4_test_marking.sh` that:
  - Applies marking to actual test files in the codebase
  - Executes full test suite to validate marking effectiveness
  - Measures actual core test reliability and failure rates
  - Uses Docker containers for isolated test execution and measurement
  - Validates <5% failure rate target for core functionality
  - Verifies migration tests are properly separated from core tests
- **Idempotent Tests**: All tests pass consistently with proper marking applied
- **Mocks/Fixtures**: Test file samples, marking configuration, reliability measurement data

**Functionality Script Requirements:**
Create `functionality_script_slice_2_4_test_marking.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual test marking implementation - NO mock objects
- **MANDATORY**: Exercises real test marking and validation logic on actual test files
- **MANDATORY**: Validates actual test suite execution and reliability measurement
- **MANDATORY**: Captures and displays actual test execution results and reliability scores
- **MANDATORY**: Shows "Expected:" and "Actual:" for each reliability check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for isolated pytest execution
- **MANDATORY**: Includes Docker health checks and test environment setup
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated test results or fake reliability scores
- Tests actual test marking against real test files in the codebase
- Validates actual test suite reliability meets <5% failure rate requirement
- Includes comprehensive Docker orchestration for test isolation
- Returns proper exit codes and detailed reliability measurement results

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_2_4_test_marking.py
poetry run ruff check --fix slice_2_4_test_marking.py
poetry run ruff format slice_2_4_test_marking.py
poetry run pydocstyle slice_2_4_test_marking.py
poetry run bandit -r slice_2_4_test_marking.py
poetry run pytest test_slice_2_4.py -v --cov=slice_2_4_test_marking --cov-fail-under=100
```

**Integration Validation:**
Execute complete test suite with marking applied, verify core functionality tests achieve >95% pass rate and migration tests are properly separated

**AI Agent Execution Notes:**
Use existing decorator_utils.py and test_analysis.py helpers to reduce complexity. Focus on achieving reliability target while maintaining clear separation between core and migration tests.