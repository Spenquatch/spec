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

**Slice 4.3: Resource Planning and Timeline Development**

**Goal**: Create detailed resource allocation and timeline documentation with critical path analysis and comprehensive project planning guidance for migration completion

**Slice Type**: Planning Documentation Component

**Planning Dependencies:**

Required planning inputs from previous slices:
- `MIGRATION_ROADMAP.md` from Slice 4.2 → Implementation strategy and phase breakdown
- `SINGLETON_ELIMINATION_STRATEGIES.md` from Slice 4.2 → Pattern-specific strategies and effort estimates
- `IMPLEMENTATION_PHASES.md` from Slice 4.2 → Phase timeline and deliverables
- Existing migration utilities documentation for effort estimation reference
- Team capacity and project constraint assumptions

**Planning Analysis:**

- Planning components: 4 (resource allocation, timeline optimization, critical path analysis, project management guidance)
- Documentation deliverables: 3 major planning documents
- Planning validation: Cross-reference with roadmap phases and strategy complexity

**Planning Inputs → Analysis → Outputs:**

- **Planning Inputs**: {implementation_roadmap: MIGRATION_ROADMAP.md, elimination_strategies: SINGLETON_ELIMINATION_STRATEGIES.md, phase_breakdown: IMPLEMENTATION_PHASES.md, team_capacity_assumptions: dict, project_constraints: dict}
- **Analysis**:
  1. Analyze implementation roadmap phases and calculate realistic effort estimates based on strategy complexity
  2. Perform critical path analysis using phase dependencies for timeline optimization  
  3. Generate resource allocation plan with appropriate buffer time for complex migration scenarios
  4. Create comprehensive project planning documentation with timelines and resource requirements
- **Planning Outputs**: {resource_allocation_plan: RESOURCE_ALLOCATION_PLAN.md, migration_timeline: MIGRATION_TIMELINE.md, project_planning_guide: PROJECT_PLANNING_GUIDE.md}

**Documentation Deliverables:**

- `RESOURCE_ALLOCATION_PLAN.md` (detailed resource requirements, skills matrix, and allocation strategy)
- `MIGRATION_TIMELINE.md` (comprehensive timeline with critical path analysis and phase dependencies)
- `PROJECT_PLANNING_GUIDE.md` (project management procedures and guidelines for migration execution)

**Planning Requirements:**

- **Resource Analysis**: Team capacity assessment, skills requirement mapping, allocation optimization
- **Timeline Development**: Critical path analysis, phase dependency mapping, buffer time calculation
- **Project Management**: Process guidelines, communication plans, progress tracking procedures
- **Risk Consideration**: Resource constraints, timeline pressures, capacity limitations

**Planning Validation:**

Ensure planning documentation provides:
- Clear resource allocation with specific roles and responsibilities
- Realistic timeline estimates with proper dependencies and buffers  
- Actionable project management guidance for migration execution
- Alignment with implementation roadmap phases and strategy complexity
- Consideration of real-world project constraints and team limitations

**AI Agent Execution Notes:**
Focus on creating actionable project planning documentation that enables effective resource allocation and timeline management. Use the comprehensive roadmap and strategies from Slice 4.2 as the foundation for realistic effort estimates and resource planning. The planning documents should provide clear guidance for project managers and development teams to execute migration completion efficiently with proper resource allocation and timeline management.