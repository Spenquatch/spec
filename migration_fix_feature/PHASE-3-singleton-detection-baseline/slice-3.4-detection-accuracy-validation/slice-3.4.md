**Slice 3.4: Detection Accuracy Validation and Baseline Finalization**

**Goal**: Validate detection system accuracy at >95% against known patterns and finalize singleton baseline for migration planning

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
rg 'def.*validate.*accuracy' spec_cli/utils | head -n 5
# No matches found for validate accuracy

rg 'def.*baseline' spec_cli/utils | head -n 5
# No matches found for baseline

rg 'def.*validate.*detection' spec_cli/utils | head -n 5
# No matches found for validate detection
```

- Existing helper: `spec_cli/utils/singleton_detection.py` → Singleton detection utilities
- Existing helper: `spec_cli/utils/test_analysis.py` → Test analysis utilities for validation
- Existing helper: `spec_cli/utils/pattern_analysis.py` → Pattern analysis utilities
- New helper to create: `spec_cli/utils/validation/detection_accuracy_validator.py` → `validate_detection_accuracy(detected: List, known: List) -> AccuracyReport`

**Complexity Analysis:**

- Decision points: 5/7 (accuracy calculation, false positive/negative detection, baseline approval)
- Helper calls: 3 (existing singleton detection, test analysis, pattern analysis)
- McCabe validation: Pass - within limit using existing validation helpers

**Inputs → Action → Outputs:**

- **Inputs**: {detected_patterns: List[SingletonPattern], known_patterns: List[str], migration_plan: MigrationPlan}
- **Action**:
  1. Compare detected patterns against known singleton patterns using singleton detection utilities
  2. Calculate accuracy metrics including false positives and false negatives
  3. Finalize singleton baseline for approved migration planning
- **Outputs**: {accuracy_report: AccuracyReport, baseline_status: bool, final_singleton_baseline: SingletonBaseline}

**Files to Create/Modify:**

- `slice_3_4_accuracy_validation.py` (accuracy validation implementation)
- `spec_cli/utils/validation/detection_accuracy_validator.py` (validation helper)
- `test_slice_3_4.py` (accuracy validation tests)

**Test Requirements:**

- **Unit Tests**: Test accuracy calculation and baseline finalization logic (100% coverage)
- **Integration Test**: End-to-end validation of complete detection pipeline accuracy
- **Functionality Script**: Create `functionality_script_slice_3_4_accuracy_validation.sh` that:
  - Validates detection accuracy against actual known singleton patterns in codebase
  - Measures false positive and false negative rates with real detection results
  - Tests baseline finalization process with complete migration planning data
  - Uses Docker containers for isolated validation execution
  - Verifies >95% accuracy requirement is met for planning reliability
  - Validates final baseline completeness and approval readiness
- **Idempotent Tests**: All tests pass consistently with stable accuracy validation
- **Mocks/Fixtures**: Known singleton pattern samples, accuracy calculation test cases, baseline validation scenarios

**Functionality Script Requirements:**
Create `functionality_script_slice_3_4_accuracy_validation.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual accuracy validation implementation - NO mock objects
- **MANDATORY**: Exercises real validation logic on actual detection results and known patterns
- **MANDATORY**: Validates actual accuracy calculations and baseline finalization
- **MANDATORY**: Captures and displays actual accuracy metrics and validation results
- **MANDATORY**: Shows "Expected:" and "Actual:" for each accuracy validation check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for isolated validation execution
- **MANDATORY**: Includes Docker health checks and validation environment setup
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated accuracy scores or fake validation results
- Tests actual validation system against real detection results from Slices 3.1-3.3
- Validates detection accuracy meets >95% requirement for planning reliability
- Includes comprehensive Docker orchestration for validation environment isolation
- Returns proper exit codes and detailed accuracy validation results

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_3_4_accuracy_validation.py
poetry run ruff check --fix slice_3_4_accuracy_validation.py
poetry run ruff format slice_3_4_accuracy_validation.py
poetry run pydocstyle slice_3_4_accuracy_validation.py
poetry run bandit -r slice_3_4_accuracy_validation.py
poetry run pytest test_slice_3_4.py -v --cov=slice_3_4_accuracy_validation --cov-fail-under=100
```

**Integration Validation:**
Validate complete detection pipeline against known singleton patterns, confirm >95% accuracy and approve final baseline for migration planning

**AI Agent Execution Notes:**
Use existing singleton_detection.py and test_analysis.py helpers for validation framework. Focus on accurate measurement over complex validation algorithms.
