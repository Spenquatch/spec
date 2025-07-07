## Agent Execution Directive

This protocol governs how AI agents must implement vertical slices. Every instruction here is mandatory. Execution must follow the exact sequence, enforce all quality gates, and respect strict complexity, security, and scope boundaries.

You will not skip steps, alter scope, or improvise beyond your slice definition.

> **If a step fails: fix it. If a rule is unclear: escalate. If it's not green: it's broken.**

---

## **[P0-ABSOLUTE]** EXECUTION RULES

*These rules override everything else. Violating any rule makes the implementation invalid.*

1. **NEVER compromise security** → If secure-by-default conflicts with speed, choose security
2. **NEVER use raw pip** → Poetry only, delete venv if pip was used
3. **NEVER ignore P0 rules** → P0 = pipeline-blocking, not suggestions
4. **NEVER exceed McCabe complexity ≤ 7** → Each function max 7 decision points (helper calls don't count)
5. **NEVER commit broken code** → Full test suite must pass before final commit
6. **NEVER modify scope** → Implement exactly what's specified in your slice, nothing more

> **"Build is green OR broken - no yellow states exist"**

---

## 1. Pre-Implementation Checklist

### Before Writing Any Code
```bash
# 1. Establish baseline - ALL tests must pass
poetry run test

# 2. Verify helper dependencies exist
# Check each helper listed in your slice dependencies
ls -la spec_cli/utils/[helper_path]

# 3. Confirm type checking baseline
poetry run type-check

# 4. Check current coverage and quality
poetry run check-all

# 5. Verify cross-platform compatibility
python scripts/check_platform_compatibility.py
```

**If ANY baseline check fails:** Stop and escalate - do not proceed with broken foundation.

---

## 2. Implementation Workflow **[MANDATORY SEQUENCE]**

### Required Execution Sequence **[FOLLOW EXACTLY]**
**Every AI agent executing a slice MUST follow this exact sequence:**

#### Step 1: Preparation & Baseline
1. **Read slice instructions completely** → Understand goal, dependencies, inputs/actions/outputs
2. **Run full test suite** → Establish baseline (all tests must pass before starting)
   ```bash
   poetry run test
   ```
3. **Verify helper dependencies** → Confirm all required helpers exist or note creation needed

#### Step 2: Implementation
4. **Write core implementation code** → Follow slice specifications exactly
   - Create files using naming convention: `slice_<id>_<feature>.py`
   - Support files in appropriate spec_cli/ subdirectories (max depth: 3 levels)
   - Follow slice Inputs → Actions → Outputs exactly
   - Use specified helper functions
   - Add Google-style docstrings
   - Use pathlib.Path for ALL file operations (cross-platform)
   - Use shutil for file operations (never OS-specific commands)

5. **Apply complete type annotations** → All functions, parameters, returns typed

6. **Run type checking** → Must pass with zero errors
   ```bash
   poetry run type-check
   ```

#### Step 3: Test Development
7. **Identify test requirements** → Determine mocks, fixtures, test scenarios for 100% coverage
   - Create test files in tests/ (mirrors spec_cli/ structure 1:1)
   - tests/unit/test_slice_<id>.py for unit tests
   - tests/integration/test_slice_<id>.py for integration tests (if needed)

8. **Write comprehensive tests with typing** → Unit tests + integration test as specified
   - Unit tests for 100% coverage of new code (≤1s total runtime)
   - Integration test as specified in slice (≤30s total runtime)
   - All tests must be idempotent (pass repeatedly)
   - Include mocks/fixtures in tests/fixtures/

9. **Run type checking on tests** → Must pass with zero errors
   ```bash
   poetry run type-check
   ```

10. **Run new tests only** → Verify new tests pass in isolation
    ```bash
    poetry run test tests/unit/test_slice_<id>.py -v
    ```

#### Step 4: Integration & Quality Gates
11. **IF new tests pass** → Run entire test suite
    ```bash
    poetry run test
    ```

12. **IF any tests fail** → Evaluate issue, implement fix, repeat from step 10

13. **Run quality gates in sequence** → All must pass
    ```bash
    # IMPORTANT: Check ALL directories including examples/ and scripts/
    poetry run ruff check spec_cli/ tests/ examples/ scripts/ --output-format=full
    
    # Auto-fix violations where possible
    poetry run ruff check spec_cli/ tests/ examples/ scripts/ --fix
    
    # Apply formatting to ALL directories  
    poetry run ruff format spec_cli/ tests/ examples/ scripts/
    
    # Run comprehensive quality gates
    poetry run check-all
    ```
    
    **Critical Linting Violations to Check:**
    - **E402**: Module level import not at top (use `# noqa: E402` for dynamic imports)
    - **T201**: Print statements found (use logging instead)
    - **Q000**: Single quotes vs double quotes (use double quotes)
    - **W291**: Trailing whitespace (auto-fixed by format)
    - **PLR2004**: Magic numbers in tests (use named constants)
    - **SIM117**: Nested with statements (use single with with multiple contexts)
    
14. **Run integration validation** → Execute scenario specified in slice

15. **IF any quality gate fails** → Fix issue, return to appropriate step, re-validate

#### Step 5: Final Verification
16. **Commit preparation** → Ensure clean working directory, all files staged
    ```bash
    git add [all_your_files]
    git status  # Verify clean working directory
    ```

17. **No git history rewrites allowed** → Use `--fixup` if re-committing

18. **Final test suite run** → All tests must pass before completion
    ```bash
    poetry run test
    ```

19. **Slice completion confirmation** → Verify all deliverables met

### Execution Failure Protocol **[ERROR HANDLING]**
**IF any step fails:**
- **Identify root cause** → Analyze error messages, logs, test failures
- **Implement targeted fix** → Address specific issue without scope creep
- **Re-validate from fix point** → Return to appropriate step in sequence
- **IF 3 consecutive failures at same step** → Escalate with detailed error report including: stack trace, diff output, failed command logs, environment details

---

**Slice 4.2: Implementation Roadmap Development and Strategy Planning**

**Goal**: Create comprehensive migration implementation roadmap with specific strategies for each singleton pattern type and detailed documentation for migration completion

**Slice Type**: Planning Component with Documentation

**Helper Dependencies & Search Evidence:**

Helper search performed:
```bash
rg 'class.*SingletonPattern' spec_cli/utils | head -n 5
# Found: SingletonPattern, SingletonUsage pattern classes

rg 'def.*analyze.*singleton' spec_cli/utils | head -n 5  
# Found: analyze_singleton_usage, pattern analysis functions

rg 'def.*migration.*plan' spec_cli/utils | head -n 5
# No existing migration planning utilities found
```

- Existing helper: `spec_cli/utils/pattern_analysis.py` → Pattern analysis for strategy matching
- Existing helper: `spec_cli/utils/singleton_detection.py` → Pattern detection for baseline review
- Existing helper: `spec_cli/utils/migration_utils.py` → Migration utilities for planning context
- Existing helper: `slice_4_1_readiness_assessment.py` → Readiness assessment data for planning
- New helper to create: `spec_cli/utils/planning/roadmap_generator.py` → `generate_migration_roadmap(baseline_data: dict, readiness_report: ReadinessReport) -> MigrationRoadmap`

**Complexity Analysis:**

- Decision points: 6/7 (strategy selection, phase prioritization, pattern categorization, timeline calculation)
- Helper calls: 4 (pattern analysis, singleton detection, migration utils, readiness assessment)
- McCabe validation: Pass - under limit with focused planning logic

**Inputs → Action → Outputs:**

- **Inputs**: {singleton_baseline: dict, readiness_assessment: ReadinessAssessmentResult, pattern_categories: list, elimination_templates: dict}
- **Action**:
  1. Analyze singleton baseline and pattern categories using existing detection utilities
  2. Generate specific elimination strategies for each pattern type with code examples
  3. Create phase-by-phase implementation roadmap with clear objectives and timelines
  4. Produce comprehensive documentation with templates and implementation guidance
- **Outputs**: {migration_roadmap: MigrationRoadmap, strategy_documentation: dict, implementation_phases: list, code_templates: dict}

**Files to Create/Modify:**

- `slice_4_2_roadmap_development.py` (roadmap development implementation and documentation generation)
- `spec_cli/utils/planning/roadmap_generator.py` (roadmap generation utilities)
- `tests/unit/test_slice_4_2.py` (roadmap development tests)
- `MIGRATION_ROADMAP.md` (comprehensive migration roadmap documentation)
- `SINGLETON_ELIMINATION_STRATEGIES.md` (specific strategies for each pattern type)
- `templates/` directory with elimination code examples

**Test Requirements:**

- **Unit Tests**: Test roadmap generation logic and strategy documentation creation (100% coverage)
- **Integration Test**: End-to-end roadmap development using actual singleton baseline from Phase 3
- **Functionality Script**: Create `functionality_script_slice_4_2_roadmap_development.sh` that:
  - Generates complete migration roadmap using real readiness assessment data
  - Validates strategy appropriateness for different singleton pattern types
  - Tests documentation generation with actual pattern examples
  - Verifies roadmap completeness and implementation guidance quality
  - Uses Docker containers for isolated documentation generation environment
  - Measures roadmap coverage against singleton baseline patterns
  - Confirms all patterns have specific elimination strategies with code examples
- **Idempotent Tests**: All tests pass consistently with stable roadmap generation
- **Mocks/Fixtures**: Singleton baseline samples, readiness reports, strategy templates

**Functionality Script Requirements:**
Create `functionality_script_slice_4_2_roadmap_development.sh` in `tests/functionality/` that:

- **MANDATORY**: Tests REAL functionality only - NO mocking, NO patches, NO unittest.mock usage
- **MANDATORY**: Uses actual roadmap development implementation - NO mock objects
- **MANDATORY**: Exercises real documentation generation on actual singleton baseline data
- **MANDATORY**: Validates actual strategy assignment and implementation guidance
- **MANDATORY**: Captures and displays actual roadmap structure and strategy completeness
- **MANDATORY**: Shows "Expected:" and "Actual:" for each roadmap validation check
- **MANDATORY**: Outputs explicit PASS or FAIL status for each test
- **MANDATORY**: Uses Docker container for isolated documentation generation environment
- **MANDATORY**: Includes Docker health checks and planning environment setup
- **FORBIDDEN**: Any import from unittest.mock, patch, Mock, MagicMock
- **FORBIDDEN**: Simulated roadmap data or fake implementation strategies
- Tests actual roadmap generation against real singleton baseline and readiness assessment
- Validates documentation completeness and strategy implementation guidance
- Includes comprehensive Docker orchestration for documentation generation isolation
- Returns proper exit codes and detailed roadmap development results

**Quality Gate Validation:**
```bash
poetry run mypy --strict slice_4_2_roadmap_development.py
poetry run ruff check --fix slice_4_2_roadmap_development.py
poetry run ruff format slice_4_2_roadmap_development.py
poetry run pydocstyle slice_4_2_roadmap_development.py
poetry run bandit -r slice_4_2_roadmap_development.py
poetry run pytest tests/unit/test_slice_4_2.py -v --cov=slice_4_2_roadmap_development --cov-fail-under=100
```

**Integration Validation:**
Generate complete migration implementation roadmap with specific elimination strategies for all singleton patterns, comprehensive documentation, and clear phase-by-phase implementation guidance

**AI Agent Execution Notes:**
Focus on creating comprehensive migration planning documentation that provides immediate value to the development team. Leverage existing pattern analysis and readiness assessment data to create actionable implementation strategies with specific code examples and clear timelines. The roadmap should serve as the definitive guide for completing singleton elimination across the codebase.