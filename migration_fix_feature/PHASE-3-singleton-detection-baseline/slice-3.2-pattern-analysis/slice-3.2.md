**Slice 3.2: Pattern Analysis and Classification**

**Goal**: Analyze detected singleton patterns to classify by type, complexity, and elimination priority with dependency mapping

**Slice Type**: Component

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
rg 'def.*classify.*pattern' spec_cli/utils | head -n 5
# No matches found for classify pattern

rg 'def.*analyze.*dependency' spec_cli/utils | head -n 5
# Found: spec_cli/utils/dependency_analysis.py

rg 'def.*complexity' spec_cli/utils | head -n 5
# No matches found for complexity
```

- Existing helper: `spec_cli/utils/dependency_analysis.py` → Dependency analysis utilities
- Existing helper: `spec_cli/utils/pattern_analysis.py` → Pattern analysis utilities  
- Existing helper: `spec_cli/utils/singleton_detection.py` → Singleton detection utilities
- New helper to create: `spec_cli/utils/pattern_classification/complexity_analyzer.py` → `analyze_pattern_complexity(pattern: SingletonPattern) -> ComplexityAssessment`

**Complexity Analysis:**

- Decision points: 6/7 (pattern type classification, complexity assessment, dependency mapping)
- Helper calls: 3 (existing dependency analysis, pattern analysis, singleton detection)
- McCabe validation: Pass - within limit using existing analysis helpers

**Inputs → Action → Outputs:**

- **Inputs**: {detected_patterns: List[SingletonPattern], codebase_structure: Dict[str, Any]}
- **Action**:
  1. Classify patterns by type using pattern analysis helpers
  2. Assess complexity using dependency analysis for each pattern
  3. Map dependency relationships between patterns and other components
- **Outputs**: {classified_patterns: List[ClassifiedSingletonPattern], dependency_graph: Dict[str, List[str]], complexity_distribution: Dict[str, int]}

**Files to Create/Modify:**

- `slice_3_2_pattern_analysis.py` (pattern analysis implementation)
- `spec_cli/utils/pattern_classification/complexity_analyzer.py` (complexity analysis helper)
- `test_slice_3_2.py` (pattern analysis tests)

**Test Requirements:**

- **Unit Tests**: Test pattern classification and complexity analysis logic (100% coverage)
- **Integration Test**: End-to-end analysis of real singleton patterns with dependency mapping
- **Functionality Script**: Create `functionality_script_slice_3_2_pattern_analysis.sh` that:
  - Analyzes actual detected singleton patterns from Slice 3.1 output
  - Validates classification accuracy against known pattern types
  - Tests dependency mapping with real codebase dependencies
  - Uses Docker containers for isolated analysis execution
  - Measures analysis performance and accuracy
  - Verifies complexity assessment produces actionable priority rankings
- **Idempotent Tests**: All tests pass consistently with stable analysis results
- **Mocks/Fixtures**: Sample singleton patterns, dependency structures, classification test cases

**Functionality Script Requirements:**
Create `functionality_script_slice_3_2_pattern_analysis.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual pattern analysis implementation - NO mock objects
- **MANDATORY**: Exercises real classification logic on actual singleton patterns
- **MANDATORY**: Validates actual dependency mapping and complexity assessment
- **MANDATORY**: Captures and displays actual analysis results and classifications
- **MANDATORY**: Shows "Expected:" and "Actual:" for each classification check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for isolated analysis execution
- **MANDATORY**: Includes Docker health checks and analysis environment setup
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated pattern classifications or fake complexity scores
- Tests actual analysis system against real singleton patterns detected in Slice 3.1
- Validates classification accuracy and dependency mapping completeness
- Includes comprehensive Docker orchestration for analysis environment isolation
- Returns proper exit codes and detailed pattern analysis results

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_3_2_pattern_analysis.py
poetry run ruff check --fix slice_3_2_pattern_analysis.py
poetry run ruff format slice_3_2_pattern_analysis.py
poetry run pydocstyle slice_3_2_pattern_analysis.py
poetry run bandit -r slice_3_2_pattern_analysis.py
poetry run pytest test_slice_3_2.py -v --cov=slice_3_2_pattern_analysis --cov-fail-under=100
```

**Integration Validation:**
Analyze complete set of detected patterns, verify all patterns classified with accurate complexity assessment and dependency relationships mapped

**AI Agent Execution Notes:**
Use existing dependency_analysis.py and pattern_analysis.py helpers to reduce complexity. Focus on accurate classification over sophisticated complexity metrics.