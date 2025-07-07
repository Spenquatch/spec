**Slice 3.3: Migration Strategy Development and Planning - REBUILD REQUIRED**

**Goal**: Develop specific elimination strategies for each pattern type and create comprehensive migration plan with effort estimates

**Slice Type**: Component

**🚨 CRITICAL UPDATE - REBUILD REQUIRED:**

**Previous Implementation Issues Identified:**
- **PROBLEM**: Initial implementation created duplicate dataclasses (ClassifiedSingletonPattern, EliminationStrategy) instead of using existing pipeline data structures
- **PROBLEM**: Built standalone migration planning framework instead of integrating with existing Slice 3.2 output
- **PROBLEM**: Ignored existing helpers (migration_utils.py, dependency_analysis.py) and created unnecessary custom logic
- **PROBLEM**: Did not consume PatternAnalysisResult from slice_3_2_pattern_analysis.py as intended

**REBUILD REQUIREMENTS:**
1. **MUST USE** existing ClassifiedSingletonPattern from `slice_3_2_pattern_analysis.py` 
2. **MUST CONSUME** PatternAnalysisResult as input (not create new data structures)
3. **MUST LEVERAGE** existing migration_utils.py helpers for migration logic
4. **MUST FOCUS** on strategy generation only, not comprehensive planning framework
5. **MUST CREATE** only the specified helper: strategy_generator.py

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
# UPDATED: Found existing data structures and helpers
grep -r "ClassifiedSingletonPattern" slice_3_2_pattern_analysis.py
# FOUND: ClassifiedSingletonPattern already defined in Slice 3.2

grep -r "migration_utils" spec_cli/utils/
# FOUND: migration_utils.py with migrate_command_signature, validate_migration_behavior

grep -r "dependency_analysis" spec_cli/utils/
# FOUND: dependency_analysis.py with analyze_current_usage, generate_dependency_report
```

- **EXISTING DATA**: `slice_3_2_pattern_analysis.py` → ClassifiedSingletonPattern, PatternAnalysisResult
- **EXISTING HELPER**: `spec_cli/utils/migration_utils.py` → Migration command utilities
- **EXISTING HELPER**: `spec_cli/utils/dependency_analysis.py` → Dependency analysis utilities  
- **NEW HELPER ONLY**: `spec_cli/utils/migration_planning/strategy_generator.py` → `generate_elimination_strategy(pattern: ClassifiedSingletonPattern) -> dict[str, Any]`

**Complexity Analysis:**

- Decision points: 4/7 (strategy selection, effort estimation) - REDUCED by using existing helpers
- Helper calls: 3 (existing migration utilities, dependency analysis, Slice 3.2 integration)
- McCabe validation: Pass - well within limit by leveraging existing infrastructure

**Inputs → Action → Outputs (CORRECTED):**

- **Inputs**: {pattern_analysis_result: PatternAnalysisResult (from slice_3_2_pattern_analysis.py), project_constraints: Dict[str, Any]}
- **Action**:
  1. Import PatternAnalysisResult from Slice 3.2 output
  2. Generate elimination strategies using migration_utils.py helpers  
  3. Estimate implementation effort based on existing complexity_assessment data
  4. Use dependency_graph from PatternAnalysisResult for ordering
- **Outputs**: {migration_strategies: Dict[str, dict], implementation_order: List[str], effort_estimates: Dict[str, int]}

**Files to Create/Modify (UPDATED):**

- `slice_3_3_strategy_development.py` (REBUILD: simple strategy orchestration using existing pipeline)
- `spec_cli/utils/migration_planning/strategy_generator.py` (NEW: focused strategy generation helper only)
- `test_slice_3_3.py` (REBUILD: test integration with Slice 3.2 output, not standalone framework)

**Test Requirements (UPDATED):**

- **Unit Tests**: Test strategy generation logic integration with existing helpers (100% coverage)
- **Integration Test**: End-to-end strategy generation consuming actual Slice 3.2 PatternAnalysisResult
- **Functionality Script**: Create `functionality_script_slice_3_3_strategy_development.sh` that:
  - **CORRECTED**: Consumes actual PatternAnalysisResult from Slice 3.2 execution
  - **CORRECTED**: Tests strategy generation using existing migration_utils.py helpers
  - **CORRECTED**: Validates effort estimation based on existing complexity_assessment data  
  - **CORRECTED**: Uses actual dependency_graph from Slice 3.2 for ordering validation
  - Uses Docker containers for isolated strategy development execution
  - Tests integration between Slice 3.2 → Slice 3.3 pipeline
  - Verifies strategy generation works with real classified patterns
- **Idempotent Tests**: All tests pass consistently with pipeline integration
- **Mocks/Fixtures**: CORRECTED - Use actual PatternAnalysisResult fixtures, not custom dataclasses

**Functionality Script Requirements:**
Create `functionality_script_slice_3_3_strategy_development.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual strategy development implementation - NO mock objects
- **MANDATORY**: Exercises real strategy generation on actual classified patterns
- **MANDATORY**: Validates actual elimination strategies and effort estimates
- **MANDATORY**: Captures and displays actual migration plan and strategy assignments
- **MANDATORY**: Shows "Expected:" and "Actual:" for each strategy development check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for isolated strategy development execution
- **MANDATORY**: Includes Docker health checks and planning environment setup
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated elimination strategies or fake effort estimates
- Tests actual strategy generation against real classified patterns from Slice 3.2
- Validates strategy appropriateness and effort estimation accuracy
- Includes comprehensive Docker orchestration for planning environment isolation
- Returns proper exit codes and detailed strategy development results

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_3_3_strategy_development.py
poetry run ruff check --fix slice_3_3_strategy_development.py
poetry run ruff format slice_3_3_strategy_development.py
poetry run pydocstyle slice_3_3_strategy_development.py
poetry run bandit -r slice_3_3_strategy_development.py
poetry run pytest test_slice_3_3.py -v --cov=slice_3_3_strategy_development --cov-fail-under=100
```

**Integration Validation:**
Generate complete migration plan for all classified patterns, verify strategies are appropriate and effort estimates enable realistic project planning

**AI Agent Execution Notes (CRITICAL UPDATE):**

**REBUILD APPROACH REQUIRED:**
1. **START BY IMPORTING** existing data structures from slice_3_2_pattern_analysis.py (ClassifiedSingletonPattern, PatternAnalysisResult)
2. **EXAMINE EXISTING HELPERS** in migration_utils.py and dependency_analysis.py to understand available functions
3. **CREATE MINIMAL IMPLEMENTATION** that consumes PatternAnalysisResult and generates simple strategy assignments
4. **AVOID RECREATING** any dataclasses or complex frameworks - focus on strategy logic only
5. **TEST INTEGRATION** with actual Slice 3.2 output, not standalone operation

**EXECUTION SEQUENCE:**
1. Import PatternAnalysisResult from slice_3_2_pattern_analysis.py
2. Create simple strategy_generator.py helper using existing migration utilities  
3. Build minimal slice_3_3_strategy_development.py that orchestrates strategy generation
4. Write tests that consume actual Slice 3.2 output format
5. Validate pipeline integration Slice 3.2 → Slice 3.3

**CRITICAL SUCCESS FACTORS:**
- Uses existing pipeline data structures (no custom dataclasses)
- Leverages migration_utils.py helpers for migration logic
- Consumes PatternAnalysisResult as designed
- Generates strategies, not comprehensive planning frameworks
- Integrates seamlessly with established slice pipeline
